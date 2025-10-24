import streamlit as st
import pdfplumber
import spacy
import random
import re

# Load or auto-download spaCy model
@st.cache_resource
def load_spacy_model():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        from spacy.cli import download
        download("en_core_web_sm")
        return spacy.load("en_core_web_sm")

nlp = load_spacy_model()

# --- Extract text safely ---
def extract_text_from_pdf(uploaded_file, max_pages=10):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for i, page in enumerate(pdf.pages[:max_pages]):  # limit to first 10 pages
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

# --- Generate clean, unique questions ---
def generate_questions(text, num_questions=5):
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.split()) > 6]

    if not sentences:
        return ["No valid sentences found for question generation."]

    sampled = random.sample(sentences, min(num_questions, len(sentences)))
    questions = []

    for sentence in sampled:
        sent_doc = nlp(sentence)
        nouns = [t.text for t in sent_doc if t.pos_ in ("NOUN", "PROPN") and len(t.text) > 2]
        if nouns:
            keyword = random.choice(nouns)
            q = re.sub(rf"\b{re.escape(keyword)}\b", "_____", sentence, count=1)
            questions.append(f"Q: {q}\nA: {keyword}")
        else:
            questions.append(f"Q: What is the main idea of this?\nA: {sentence}")
    return questions

# --- Streamlit UI ---
st.set_page_config(page_title="AI Question Generator", layout="centered")
st.title("🧠 AI Question Generator")
st.write("Upload a PDF and get AI-generated fill-in-the-blank style questions automatically.")

uploaded_file = st.file_uploader("📄 Upload PDF", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("Extracting text from PDF..."):
        text = extract_text_from_pdf(uploaded_file)

    if text:
        st.success("✅ Text successfully extracted!")
        st.subheader("📜 Extracted Text Preview:")
        st.text_area(
            "Extracted Text",
            text[:1000] + "..." if len(text) > 1000 else text,
            height=200,
        )

        num_questions = st.slider("Number of Questions", 3, 15, 5)

        if st.button("Generate Questions"):
            with st.spinner("Generating questions..."):
                questions = generate_questions(text, num_questions)
            st.success("🎯 Questions Generated Successfully!")
            for i, q in enumerate(questions, 1):
                st.markdown(f"**{i}.** {q}")
    else:
        st.error("⚠️ Could not extract text from the uploaded PDF (maybe it's scanned or empty).")
else:
    st.info("👆 Please upload a PDF file to begin.")
