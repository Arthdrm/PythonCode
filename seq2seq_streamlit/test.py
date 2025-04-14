import streamlit as st

import os
# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Create absolute paths
tokenizer_path = os.path.join(BASE_DIR, 'model_and_tokenizer', 'tokenizer.pkl')
model_path = os.path.join(BASE_DIR, 'model_and_tokenizer', 'lstm_attention_new.keras')

st.write(BASE_DIR)
st.write(tokenizer_path)
st.write(model_path)