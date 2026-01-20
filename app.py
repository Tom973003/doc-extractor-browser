import streamlit as st
import zipfile
import tempfile
import os
from pathlib import Path
from docx import Document
from PIL import Image
import io

st.set_page_config(page_title="Document → Important Bits", layout="wide")

st.title("📄 Document → Important Bits")
st.write("Upload a Word document to extract text, images, and embedded files.")

uploaded_file = st.file_uploader(
    "Upload DOCX file",
    type=["docx"],
)

if uploaded_file:

    with tempfile.TemporaryDirectory() as tmpdir:
        docx_path = Path(tmpdir) / uploaded_file.name
        docx_path.write_bytes(uploaded_file.read())

        doc = Document(docx_path)

        # ---------------- TEXT ----------------
        st.header("📝 Extracted Text")
        for para in doc.paragraphs:
            if para.text.strip():
                st.write(para.text)

        # ---------------- IMAGES ----------------
        st.header("🖼 Extracted Images")
        image_count = 0

        with zipfile.ZipFile(docx_path) as z:
            for name in z.namelist():
                if name.startswith("word/media/"):
                    image_bytes = z.read(name)
                    image = Image.open(io.BytesIO(image_bytes))
                    st.image(image, caption=name.split("/")[-1], use_container_width=True)
                    image_count += 1

        if image_count == 0:
            st.info("No images found in this document.")

        # ---------------- EMBEDDED FILES ----------------
        st.header("📎 Embedded Files (Downloads)")

        embedded_found = False

        with zipfile.ZipFile(docx_path) as z:
            for name in z.namelist():
                if name.startswith("word/embeddings/"):
                    embedded_found = True
                    file_bytes = z.read(name)
                    filename = Path(name).name

                    st.download_button(
                        label=f"⬇ Download {filename}",
                        data=file_bytes,
                        file_name=filename,
                        mime="application/octet-stream",
                    )

        if not embedded_found:
            st.info("No embedded files found.")
