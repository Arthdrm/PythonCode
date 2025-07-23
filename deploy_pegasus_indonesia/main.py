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

from nltk.tokenize import sent_tokenize
from transformers import TFPegasusForConditionalGeneration, PegasusTokenizerFast, PegasusConfig


# 2) Initial set-up & loading resources
@st.cache_resource
def load_model_and_tokenizer(model_name):
    tokenizer = PegasusTokenizerFast.from_pretrained(original_model_name)
    model = TFPegasusForConditionalGeneration.from_pretrained(original_model_name)
    return model, tokenizer

original_model_name = "thonyyy/pegasus_indonesian_base-finetune"
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
max_input_len = 512
model, tokenizer = load_model_and_tokenizer(original_model_name)
xla_generate = tf.function(model.generate, jit_compile=True)
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

# 4) Streamlit UI
# === Sidebar Section ====
with st.sidebar:
    st.write("Sidebar")
    st.text_input("Enter something")

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
    downloaded_content = trafilatura.fetch_url(article_link)

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
        body_text = article_data.get('text')
        title_text = article_data.get('title')
        st.subheader("Konten Berita:")
        st.write("**Judul:**", title_text)
        st.write("**Kata kunci:**", keyphrases_text)
        st.write("**Badan artikel:**", body_text)        
    else:
        st.warning("Tidak dapat mengekstrak artikel dari URL yang diberikan.")    

summary_text_list = []

if st.button("Summarize"):
    if body_text.strip() != "" and title_text.strip() != "" and keyphrases_text.strip() != "":
        cleaned_body = text_cleaning(body_text)
        cleaned_keyphrase = text_cleaning(keyphrases_text)
        cleaned_title = text_cleaning(title_text)
        inputs = tokenizer(cleaned_body, return_tensors="tf")
        progress_bar = st.progress(0, text="Membangkitkan ringkasan...")
        start_time = time.perf_counter()      
        for i in range(8):
            generated_tokens = xla_generate(
                input_ids=inputs["input_ids"],
                max_length=50,
                min_length=20,
                num_beams=1,
                early_stopping=True
            )
            summary_text = tokenizer.decode(
                generated_tokens[0],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )
            summary_text_list.append(summary_text)
            progress_bar.progress(i * 0.125, text=f"Ringkasan dibangkitkan: ({i}/8)")
        progress_bar.empty()
        summary_text_list = [' '.join(sentence.capitalize() for sentence in sent_tokenize(t)) for t in summary_text_list]
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


