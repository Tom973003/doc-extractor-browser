import streamlit as st
import fitz  # PyMuPDF
import docx

st.set_page_config(page_title="Document → Important Bits")

st.title("📄 Document → Important Bits")

uploaded_file = st.file_uploader(
    "Upload PDF or Word document",
    type=["pdf", "docx"]
)

def extract_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_docx(file):
    d = docx.Document(file)
    return "\n".join(p.text for p in d.paragraphs)

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        text = extract_pdf(uploaded_file)
    else:
        text = extract_docx(uploaded_file)

    st.subheader("Extracted Text")
    st.text_area("", text, height=400)

    st.download_button(
        "⬇ Download text",
        text,
        file_name="extracted_text.txt"
    )
