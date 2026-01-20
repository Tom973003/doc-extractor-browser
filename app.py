import streamlit as st
import fitz  # PyMuPDF
import io
import zipfile
from PIL import Image

st.set_page_config(page_title="Document → Important Bits", layout="wide")

st.title("📄 Document → Important Bits")
st.write("Upload a PDF to extract structured text and images.")

uploaded_file = st.file_uploader(
    "Upload PDF",
    type=["pdf"],
    accept_multiple_files=False
)

def extract_text_and_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    text_blocks = []
    images = []

    for page_number, page in enumerate(doc, start=1):
        # ---- TEXT ----
        text = page.get_text("text")
        if text.strip():
            text_blocks.append(f"### Page {page_number}\n{text}")

        # ---- IMAGES ----
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            images.append({
                "page": page_number,
                "index": img_index,
                "bytes": image_bytes,
                "ext": image_ext
            })

    return text_blocks, images

if uploaded_file:
    pdf_bytes = uploaded_file.read()

    with st.spinner("Extracting content..."):
        text_blocks, images = extract_text_and_images(pdf_bytes)

    # ---------- TEXT OUTPUT ----------
    st.subheader("📝 Extracted Text")
    for block in text_blocks:
        st.markdown(block)

    # ---------- IMAGES ----------
    st.subheader("🖼️ Extracted Images")

    if images:
        cols = st.columns(3)
        for i, img in enumerate(images):
            image = Image.open(io.BytesIO(img["bytes"]))
            cols[i % 3].image(
                image,
                caption=f"Page {img['page']} – Image {img['index'] + 1}",
                use_container_width=True
            )
    else:
        st.info("No images found in this document.")

    # ---------- DOWNLOAD ZIP ----------
    st.subheader("⬇️ Download Images")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for img in images:
            filename = f"page_{img['page']}_image_{img['index'] + 1}.{img['ext']}"
            zip_file.writestr(filename, img["bytes"])

    st.download_button(
        label="Download all images as ZIP",
        data=zip_buffer.getvalue(),
        file_name="extracted_images.zip",
        mime="application/zip"
    )
