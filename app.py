import streamlit as st
import fitz
import re
import io
import zipfile
from PIL import Image

st.set_page_config(page_title="RFQ Document Extractor", layout="wide")

st.title("📄 RFQ Document Extractor")
st.write("Upload an RFQ PDF to extract structured fields and attachments.")

uploaded_file = st.file_uploader("Upload RFQ PDF", type=["pdf"])

# ---------------- FIELD PATTERNS ----------------
FIELD_PATTERNS = {
    "Project Title": r"^(Emergency.*|Project Title.*|.+Repair)",
    "Description of Work": r"Description of Works?:?(.*?)(?:\n\n|$)",
    "RFQ Close": r"RFQ Close:? *(.*)",
    "Proposed Start Date": r"Proposed Start Date:? *(.*)",
    "Proposed Completion Date": r"Proposed Completion Date:? *(.*)",
    "Site Location": r"(P\d[-–]\d.*|Site Location:? *(.*))",
    "LRD": r"\bLRD\b[: ]*(Yes|No|Y|N)?",
    "Inc": r"\bInc\b[: ]*(Yes|No|Y|N)?",
    "Tas": r"\bTas\b[: ]*(Yes|No|Y|N)?",
    "Practical Work": r"Practical Work:? *(.*)",
}

# ---------------- PDF EXTRACTION ----------------
def extract_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    images = []

    for page_index, page in enumerate(doc):
        text += page.get_text() + "\n"

        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base = doc.extract_image(xref)
            images.append({
                "page": page_index + 1,
                "index": img_index + 1,
                "bytes": base["image"],
                "ext": base["ext"]
            })

    return text, images

def extract_fields(text):
    results = {}
    for field, pattern in FIELD_PATTERNS.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        results[field] = match.group(1).strip() if match and match.group(1) else "—"
    return results

# ---------------- MAIN ----------------
if uploaded_file:
    with st.spinner("Extracting RFQ details…"):
        raw_text, images = extract_pdf(uploaded_file.read())
        fields = extract_fields(raw_text)

    # -------- STRUCTURED FIELDS --------
    st.subheader("📋 Extracted RFQ Fields")

    for k, v in fields.items():
        st.markdown(f"**{k}:** {v}")

    # -------- ATTACHMENTS --------
    st.subheader("📎 Attachments")
    st.write(f"Attached Photos: **{len(images)} found**")

    # -------- IMAGE PREVIEW --------
    if images:
        st.subheader("🖼️ Attached Photos")
        cols = st.columns(3)

        for i, img in enumerate(images):
            image = Image.open(io.BytesIO(img["bytes"]))
            cols[i % 3].image(
                image,
                caption=f"Page {img['page']} – Image {img['index']}",
                use_container_width=True
            )
    else:
        st.info("No images found in document.")

    # -------- IMAGE DOWNLOAD --------
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for img in images:
            name = f"page_{img['page']}_image_{img['index']}.{img['ext']}"
            zipf.writestr(name, img["bytes"])

    st.download_button(
        "⬇️ Download Attached Photos (ZIP)",
        data=zip_buffer.getvalue(),
        file_name="attached_photos.zip",
        mime="application/zip"
    )

    # -------- RAW TEXT --------
    with st.expander("📄 Full Extracted Text (Debug View)"):
        st.text(raw_text)
