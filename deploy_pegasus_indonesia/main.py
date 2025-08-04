# 1) Import necessary libraries
import streamlit as st
import numpy as np
import re
import nltk
import time
import tensorflow as tf
import pandas as pd
import trafilatura
import json
import re

from nltk.tokenize import sent_tokenize
from transformers import TFPegasusForConditionalGeneration, PegasusTokenizerFast, PegasusConfig
from newsplease import NewsPlease

# 2) Initial set-up & loading resources
@st.cache_resource
def load_model(model_name):
    model = TFPegasusForConditionalGeneration.from_pretrained(model_name)
    return model

@st.cache_resource
def load_tokenizers(regular_tokenizer_name, informative_tokenizer_name):
    regular_tokenizer = PegasusTokenizerFast.from_pretrained(regular_tokenizer_name)
    informative_tokenizer = PegasusTokenizerFast.from_pretrained(informative_tokenizer_name)
    return regular_tokenizer, informative_tokenizer

my_model_names = {
    "Regular Canon": "arthd24/pegasus_regular_canon_tpuv4-16",
    "Regular Canon Tuned": "arthd24/pegasus_regular_canon_tuned_tpuv4-16",
    "Regular Xtreme": "arthd24/pegasus_regular_xtreme_tpuv4-16",
    "Regular Xtreme Tuned": "arthd24/pegasus_regular_xtreme_tuned_tpuv4-16",
    "Informative Canon": "arthd24/pegasus_informative_canon_tpuv4-16",
    "Informative Canon Tuned": "arthd24/pegasus_informative_canon_tuned_tpuv4-16",
    "Informative Xtreme": "arthd24/pegasus_informative_xtreme_tpuv4-16",
    "Informative Xtreme Tuned": "arthd24/pegasus_informative_xtreme_tuned_tpuv4-16"
}
regular_models = ["Regular Canon", "Regular Canon Tuned", "Regular Xtreme", "Regular Xtreme Tuned"]
informative_models = ["Informative Canon", "Informative Canon Tuned", "Informative Xtreme", "Informative Xtreme Tuned"]
max_input_len = 512
models = [load_model(model) for model in my_model_names.values()] 
regular_tokenizer, informative_tokenizer = load_tokenizers(my_model_names["Regular Canon"], my_model_names["Informative Canon"])
# xla_generate = [tf.function(model.generate, jit_compile=True, reduce_retracing=True) for model in models]
st.set_page_config(layout="wide")

# 3) Preprocessing functions
# Text cleaning function
def text_cleaning(input_string):
    # Lowercasing
    lowercase = input_string.lower()

    # Removing links & replacing html codes
    remove_link = re.sub(r'(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w\.-]*)', '', lowercase).replace("&amp;","&")

    # Remove accented letters
    remove_accented = cleaned_text = re.sub(r'[^\x00-\x7F]', ' ', remove_link)

    # Remove content inside parentheses
    remove_parentheses = re.sub("([\(\|]).*?([\)\|])", "\g<1>\g<2>", remove_accented)

    # Replace symbols other than dot and commas with an empty space
    remove_punc = re.sub(r"[^a-z\d.,\s]+",' ', remove_parentheses)

    # Remove irrelevant dot (e.g. dot around numbers, etc.)
    remove_num_dot = re.sub(r"(?<=\d)\.|\.(?=\d)|(?<=#)\.","", remove_punc)

    # Remove extra whitespace
    remove_extra_whitespace =  re.sub(r'^\s*|\s\s*', ' ', remove_num_dot).strip()

    return remove_extra_whitespace

# Informative input preprocessing function
def format_input(title, keyphrase, article):
    parsed_keyphrases = [item.strip() for item in keyphrase.split(",") if item.strip()]

    # Join the keyphrases with <sep> token
    keyphrase_str = " <sep> ".join(parsed_keyphrases)

    # Construct the formatted text with special tokens
    formatted_text = (
        f"<TITLE> {title} "
        f"<KEYPHRASES> {keyphrase_str} "
        f"<ARTICLE> {article}"
    )
    return formatted_text

# Post-process summary output function
def post_process(summary):
    summary = summary.strip()
    summary = ' '.join(sentence.capitalize() for sentence in sent_tokenize(summary)) 
    summary = re.sub(r"\.{2,}", ".", summary)
    if not summary.endswith("."):
        summary += "."
    return summary

# 4) Streamlit UI
# === Sidebar Section ====
with st.sidebar:
    st.write("Generation Kwargs")
    preset_option = st.selectbox(
        "Pilih tipe preset:",
        ("Performance (Greedy)", "Quality (Beam Search)", "Creative (Random Sampling)", "Balanced (Beam & Random Sampling)")
    )
    if preset_option == "Performance (Greedy)":
        default_no_repeat_ngram = 2
        default_do_sample = 0
        default_num_beam = 1
        default_top_p = 1.0
    elif preset_option == "Quality (Beam Search)":
        default_no_repeat_ngram = 2
        default_do_sample = 0
        default_num_beam = 2
        default_top_p = 1.0
    elif preset_option == "Creative (Random Sampling)":
        default_no_repeat_ngram = 0
        default_do_sample = 1
        default_num_beam = 1
        default_top_p = 0.90  
    else:
        default_no_repeat_ngram = 2
        default_do_sample = 1
        default_num_beam = 2
        default_top_p = 0.90               
    min_len = st.slider("Min Length", 10, 30, 20)
    max_len = st.slider("Max Length", 30, 70, 50)
    no_repeat_ngram = st.slider("No Repeat Ngram", 0, 4, default_no_repeat_ngram)
    num_beam = st.slider("Num Beams", 1, 4, default_num_beam)
    top_p = st.slider("Top P", 0.0, 1.0,  default_top_p, 0.01)
    do_sample = st.radio(
        "Do Sample",
        [False, True],
        index=default_do_sample,
        horizontal=True
    )
    generation_kwargs = {
        "min_length": min_len,
        "max_length": max_len,
        "do_sample": do_sample,
        "num_beams": num_beam,
        "top_p": top_p,          
        "no_repeat_ngram_size": no_repeat_ngram
    }

# ==== Main Section ======
st.header('Demo Peringkas Teks', divider="rainbow")

input_option = st.selectbox(
    "Pilih tipe input:",
    ("Konten artikel berita", "Link artikel berita")
)

if input_option == "Konten artikel berita":
    title_text = st.text_input("Masukan judul artikel:", placeholder="Contoh: Khawatir Ada Gempa Susulan, Pasien RSUD Sumedang Dievakuasi ke Tenda Darurat")
    keyphrases_text = st.text_input("Masukan kata-kunci artikel:", placeholder="Contoh: Gempa Sumedang, RSUD Sumedang, Gempa, Gempa Bumi")
    body_text = st.text_area("Masukan badan artikel:", height="content", placeholder="Contoh: jpnn.com, SUMEDANG - Pasien RSUD Kabupaten Sumedang dievakuasi keluar rumah sakit pasca-gempa bumi. Mereka ditempatkan dia tenda darurat milik BPBD Kabupaten Garut. Kepala Pelaksana BPBD Kabupaten Garut Aah Anwar Saefuloh mengatakan sejumlah personel BPBD Garut diturunkan untuk memasang tenda darurat berikut lampu penerangan yang disiapkan bagi pasien RSUD Sumedang.")
else:
    article_link = st.text_input("Masukan URL artikel:", placeholder="Contoh: https://www.jpnn.com/news/didimax-dukung-investasi-aman-lewat-edukasi-trading-forex")
    if article_link:
        downloaded_content = trafilatura.fetch_url(article_link)
        body_text = NewsPlease.from_url(article_link).maintext

        # Extract the data as a JSON string
        json_output = trafilatura.extract(
            downloaded_content,
            output_format='json',
            with_metadata=True
        )

        if json_output:
            # Parse the JSON string into a Python dictionary
            article_data = json.loads(json_output)
            keyphrases_text = article_data.get('tags')
            title_text = article_data.get('title')
            st.subheader("Konten Berita:")
            st.write("**Judul:**", title_text)
            st.write("**Kata kunci:**", keyphrases_text)
            st.write("**Badan artikel:**", body_text)        
        else:
            st.warning("Tidak dapat mengekstrak artikel dari URL yang diberikan/URL kosong.")    

summary_text_list = []

if st.button("Summarize"):
    if body_text.strip() != "" and title_text.strip() != "" and keyphrases_text.strip() != "":
        cleaned_title = text_cleaning(title_text)
        cleaned_body = text_cleaning(body_text)
        cleaned_keyphrase = text_cleaning(keyphrases_text)        
        informative_text = format_input(cleaned_title, cleaned_keyphrase, cleaned_body)
        regular_inputs = regular_tokenizer(cleaned_body, return_tensors="tf", max_length=max_input_len, padding="max_length", truncation=True)
        informative_inputs = informative_tokenizer(informative_text, return_tensors="tf", max_length=max_input_len, padding="max_length", truncation=True)
        progress_bar = st.progress(0, text="Membangkitkan ringkasan...")
        start_time = time.perf_counter() 
        for i in range(8):
            if i < 4:
                # Regular Models
                generated_tokens = models[i].generate(
                    input_ids=regular_inputs["input_ids"],
                    attention_mask=regular_inputs["attention_mask"],
                    **generation_kwargs
                )
                summary_text = regular_tokenizer.decode(
                    generated_tokens[0],
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=True
                )
                summary_text_list.append(summary_text)                
            else:
                # Informative Models
                generated_tokens = models[i].generate(
                    input_ids=informative_inputs["input_ids"],
                    attention_mask=informative_inputs["attention_mask"],
                    **generation_kwargs
                )                
                summary_text = informative_tokenizer.decode(
                    generated_tokens[0],
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=True
                )
                summary_text_list.append(summary_text)
            progress_bar.progress(i * 0.125, text=f"Ringkasan dibangkitkan: ({i}/8)")
        progress_bar.empty()
        summary_text_list = [post_process(sum) for sum in summary_text_list]
        st.subheader("Hasil Ringkasan:")
        elapsed_time = time.perf_counter() - start_time
        st.write(f"**Time taken**: {elapsed_time:2f}s") 
        df_summary = pd.DataFrame(
            {
                "**Model**": my_model_names.keys(),
                "**Prediksi Ringkasan**": summary_text_list
            },
        ) 
        st.table(
            df_summary
        )
    elif title_text.strip() == "":
        st.warning("Tolong masukkan judul artikel.")        
    elif keyphrases_text.strip() == "":
        st.warning("Tolong masukkan kata-kunci artikel.")
    else:
        st.warning("Tolong masukkan badan artikel.")

st.divider()
st.caption("Copyright (c) Artha D. 2025")


