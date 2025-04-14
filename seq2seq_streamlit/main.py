import streamlit as st
import pickle
import tensorflow as tf
import numpy as np
import re
import preprocessor as p
from tensorflow.keras.preprocessing.sequence import pad_sequences
import os
from tensorflow.keras import backend as K


# ---------------------------------------- Initial Set-Up & Resources ----------------------------------------
# Attention layer
class AttentionLayer(tf.keras.layers.Layer):
    """
    This class implements Bahdanau attention (https://arxiv.org/pdf/1409.0473.pdf).
    There are three sets of weights introduced: W_a, U_a, and V_a.
    """

    def __init__(self, **kwargs):
        super(AttentionLayer, self).__init__(**kwargs)

    def build(self, input_shape):
        assert isinstance(input_shape, list)
        
        # Create trainable weight variables
        self.W_a = self.add_weight(
            name='W_a',
            shape=tf.TensorShape((input_shape[0][2], input_shape[0][2])),
            initializer='uniform',
            trainable=True
        )
        self.U_a = self.add_weight(
            name='U_a',
            shape=tf.TensorShape((input_shape[1][2], input_shape[0][2])),
            initializer='uniform',
            trainable=True
        )
        self.V_a = self.add_weight(
            name='V_a',
            shape=tf.TensorShape((input_shape[0][2], 1)),
            initializer='uniform',
            trainable=True
        )
        super(AttentionLayer, self).build(input_shape)

    def call(self, inputs, mask=None):
        """
        Inputs: [encoder_output_sequence, decoder_output_sequence]
        Mask: [encoder_mask, decoder_mask]
        """
        assert type(inputs) == list
        encoder_out_seq, decoder_out_seq = inputs

        # Handle masks
        encoder_mask = mask[0] if mask else None
        decoder_mask = mask[1] if mask else None

        def energy_step(inputs, states):
            """Compute energy for a single decoder state."""
            encoder_full_seq = states[-1]

            # S.W_a
            W_a_dot_s = K.dot(encoder_full_seq, self.W_a)

            # h_j.U_a
            U_a_dot_h = K.expand_dims(K.dot(inputs, self.U_a), 1)

            # tanh(S.W_a + h_j.U_a)
            Ws_plus_Uh = K.tanh(W_a_dot_s + U_a_dot_h)

            # softmax(V_a.tanh(S.W_a + h_j.U_a))
            e_i = K.squeeze(K.dot(Ws_plus_Uh, self.V_a), axis=-1)

            # Apply mask
            if encoder_mask is not None:
                e_i *= K.cast(encoder_mask, dtype=K.floatx())

            e_i = K.softmax(e_i, axis=-1)
            return e_i, [e_i]

        def context_step(inputs, states):
            """Compute context vector c_i using e_i."""
            encoder_full_seq = states[-1]

            # c_i = sum(e_i * h_i)
            c_i = K.sum(encoder_full_seq * K.expand_dims(inputs, -1), axis=1)
            return c_i, [c_i]

        # Fake states for RNN step functions
        fake_state_c = K.sum(encoder_out_seq, axis=1)
        fake_state_e = K.sum(encoder_out_seq, axis=2)

        # Compute energy outputs
        _, e_outputs, _ = K.rnn(
            energy_step, decoder_out_seq, [fake_state_e], constants=[encoder_out_seq]
        )

        # Compute context vectors
        _, c_outputs, _ = K.rnn(
            context_step, e_outputs, [fake_state_c], constants=[encoder_out_seq]
        )

        return c_outputs, e_outputs

    def compute_output_shape(self, input_shape):
        """Define the output shapes."""
        return [
            tf.TensorShape((input_shape[1][0], input_shape[1][1], input_shape[1][2])),
            tf.TensorShape((input_shape[1][0], input_shape[1][1], input_shape[0][1]))
        ]

    def compute_mask(self, inputs, mask=None):
        """Preserve the decoder mask for downstream layers."""
        return mask[1], None

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Create absolute paths
tokenizer_path = os.path.join(BASE_DIR, 'model_and_tokenizer', 'tokenizer.pkl')
model_path = os.path.join(BASE_DIR, 'model_and_tokenizer', 'lstm_attention_new.keras')

@st.cache_resource
def load_model_and_tokenizer():
    # Load the pre-trained model and tokenizer
    with open(tokenizer_path, 'rb') as f:
        tokenizer = pickle.load(f)
    model = tf.keras.models.load_model(model_path, custom_objects={'AttentionLayer': AttentionLayer})  
    return model, tokenizer

model, tokenizer = load_model_and_tokenizer()

# Parameters
max_input_len = 400   # Maximum length for article body sequences
max_target_len = 30  # Maximum length for summary sequences
vocab_size = 20000 + 3   # Vocabulary size
embedding_dim = 300   # Embedding dimension
lstm_units = 256      # LSTM units

# Special tokens to be ignored (masked)
mask_tokens = np.array([0, 1, 20001, 20002]) 

# ---------------------------------------- Building The Inference Model ----------------------------------------
# INFERENCE MODELS
# Extract the encoder layers
encoder_inputs = model.get_layer("encoder_input").output
encoder_lstm_layer = model.get_layer("encoder_lstm")  # Get the encoder LSTM layer

# Get encoder outputs and states
encoder_outputs, state_h, state_c = encoder_lstm_layer.output
encoder_states = [state_h, state_c]

# Define encoder inference model
encoder_model = tf.keras.models.Model(inputs=encoder_inputs, outputs=[encoder_outputs, state_h, state_c])

# Define the input layer for encoder outputs (needed for attention)
encoder_outputs_input = tf.keras.layers.Input(shape=(max_input_len, lstm_units), name="encoder_outputs_input")

# Define decoder input layers
decoder_inputs_infer = tf.keras.layers.Input(shape=(1,), name="decoder_inputs_infer")  # Single timestep input
decoder_state_input_h = tf.keras.layers.Input(shape=(lstm_units,), name="decoder_state_input_h")
decoder_state_input_c = tf.keras.layers.Input(shape=(lstm_units,), name="decoder_state_input_c")
decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]

# Retrieve decoder's layers from the trained model
decoder_embedding_layer = model.get_layer("decoder_embedding")  # Get decoder embedding layer
decoder_lstm_layer = model.get_layer("decoder_lstm")  # Get decoder LSTM layer
decoder_dense_layer = model.get_layer("decoder_dense")  # Get output Dense layer

# Apply decoder embeddings
decoder_embedding_infer = decoder_embedding_layer(decoder_inputs_infer)

# Run LSTM with initial state inputs
decoder_lstm_outputs, state_h, state_c = decoder_lstm_layer(
    decoder_embedding_infer, initial_state=decoder_states_inputs
)
decoder_states = [state_h, state_c]

# Attention layer
attention_layer = model.get_layer("attention_layer")
context_vectors, _  = attention_layer([encoder_outputs_input, decoder_lstm_outputs])

# Combine the context vectors with the LSTM outputs
decoder_combined_outputs = tf.keras.layers.Concatenate(axis=-1)([context_vectors, decoder_lstm_outputs])

# Generate output probabilities
decoder_outputs = decoder_dense_layer(decoder_combined_outputs)

# Define inference decoder model
decoder_model = tf.keras.models.Model(
    [decoder_inputs_infer, encoder_outputs_input] + decoder_states_inputs, 
    [decoder_outputs] + decoder_states
)

# [BUG] Disabling the JIT compilation due to .keras model error (because they still)
# Create a function to run inference with XLA compilation
@tf.function(jit_compile=False)
def encoder_xla(input_seq):
    return encoder_model(input_seq, training=False)

@tf.function(jit_compile=False)
def decoder_xla(target_seq):
    return decoder_model(target_seq, training=False)

# ---------------------------------------- Model & Preprocessing Functions ----------------------------------------
# Tweetpreprocessor config
p.set_options(p.OPT.URL, p.OPT.EMOJI, p.OPT.SMILEY)
# Clean text function
def clean_text(text):
    pattern_hashtag = r"#[^\s]+"
    pattern_html_code = r"&[a-zA-Z0-9]+;"
    pattern_noise = "SCROLL TO CONTINUE WITH CONTENT"
    # Removing html escape codes
    text = re.sub(pattern_html_code, "", text)
    # Removing text noises
    text = text.replace(pattern_noise, '')
    # Removing links, emoji, smiley, extra whitespace
    text = p.clean(text)
    # Lowercasing
    text = text.lower()
    return text

# Preprocess text to be fed to the model
def preprocess_input_text(input_text, tokenizer, max_input_len):
    input_text = clean_text(input_text)
    sequence = tokenizer.texts_to_sequences([input_text])
    padded = pad_sequences(sequence, maxlen=max_input_len, padding='post', truncating='post')
    return padded

# Inference function (your original generate_sequence)
def generate_sequence(input_seq, max_target_len=30, start_token_index=20001, end_token_index=20002, is_attention=False):
    # Encode the input sequence to get initial states
    encoder_outputs, state_h, state_c = encoder_xla(input_seq)
    states_value = [state_h, state_c]

    # Initialize target sequence with the start token
    target_seq = np.array([start_token_index]).reshape(1, 1)  # Shape (1, 1) for single token input

    # Initialize an empty list to store the generated tokens
    generated_tokens = []

    for _ in range(max_target_len):
        # Predict the next token and states from the decoder        
        if is_attention:
            output_tokens, h, c = decoder_xla(
                [target_seq, encoder_outputs] + states_value
            )
        else:
            output_tokens, h, c = decoder_xla(
                [target_seq] + states_value
            )

        # Get the token with the highest probability
        sampled_token_index = np.argmax(output_tokens[0, -1, :])
        
        # Exit loop if the end token is generated
        if sampled_token_index == end_token_index:
            break
        
        # Append token
        generated_tokens.append(sampled_token_index)

        # Update the target sequence to the last predicted token
        target_seq = np.array([sampled_token_index]).reshape(1, 1)

        # Update the decoder states with the latest predictions
        states_value = [h, c]

    return np.array(generated_tokens)


# ---------------------------------------- Streamlit Functions ----------------------------------------
# Streamlit UI
st.title("Text Summarization Demo (LSTM Seq2Seq)")
input_text = st.text_area("Enter news article content:")

if st.button("Summarize"):
    if input_text.strip() != "":
        input_seq = preprocess_input_text(input_text, tokenizer, max_input_len)
        generated_tokens = generate_sequence(input_seq, max_target_len=max_target_len, is_attention=True)
        generated_tokens = generated_tokens[~np.isin(generated_tokens, mask_tokens)]
        summary_text = tokenizer.sequences_to_texts([generated_tokens])[0]        
        st.subheader("Generated Summary:")
        st.write(summary_text)
    else:
        st.warning("Please enter some text to summarize.")
