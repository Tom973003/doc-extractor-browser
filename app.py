import streamlit as st
from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from PIL import Image
import io
import re

st.set_page_config(page_title="RFQ DOCX Extractor", layout="wide")

st.title("📄 RFQ Document Extractor (DOCX)")
st.caption("Reliable text + image extraction from Word documents")

uploaded = st.file_uploader("Upload RFQ (.docx only)", type=["docx"])

# ---------- HELPERS ----------

def clean(text):
    return re.sub(r"\s+", " ", text).strip()

def extract_text(doc):
    paragraphs = []
    for p in doc.paragraphs:
        if p.text.strip():
            paragraphs.append(p.text.strip())
    return "\n".join(paragraphs)

def extract_fields(text):
    patterns = {
        "Project title": r"(Project Title|Emergency Maintenance Fault Repair)(.*)",
        "Description of work": r"Brief Description of Works:(.*?)(Date Created:|$)",
        "RFQ close": r"(RFQ Close|Close Date)[:\s]*(.*)",
        "Proposed start date": r"(Proposed Start Date)[:\s]*(.*)",
        "Proposed completion date": r"(Proposed Completion Date)[:\s]*(.*)",
        "Site location": r"(Site Location)[:\s]*(.*)",
        "LRD": r"\bLRD\b[:\s]*(.*)",
        "Inc": r"\bINC\b[:\s]*(.*)",
        "Tas": r"\bTAS\b[:\s]*(.*)",
        "Practical work": r"(Practical Work)[:\s]*(.*)",
    }

    results = {}
    for field, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        results[field] = clean(match.group(2)) if match else "Not found"
    return results

def extract_images(doc):
    images = []
    for rel in doc.part.rels.values():
        if rel.reltype == RT.IMAGE:
            img_bytes = rel.target_part.blob
            image = Image.open(io.BytesIO(img_bytes))
            images.append((rel.target_ref, image, img_bytes))
    return images

# ---------- MAIN ----------

if uploaded:
    doc = Document(uploaded)

    full_text = extract_text(doc)
    fields = extract_fields(full_text)
    images = extract_images(doc)

    st.divider()

    st.header("🧾 Extracted Fields")
    for k, v in fields.items():
        st.text_area(k, v, height=80)

    st.divider()

    st.header("🖼️ Extracted Images")

    if images:
        cols = st.columns(3)
        for i, (name, img, raw) in enumerate(images):
            with cols[i % 3]:
                st.image(img, caption=f"Image {i+1}", use_container_width=True)
                st.download_button(
                    label="⬇️ Download",
                    data=raw,
                    file_name=f"image_{i+1}.png",
                    mime="image/png"
                )
    else:
        st.info("No images found in this document.")

    st.divider()

    with st.expander("📄 Full Extracted Text"):
        st.text(full_text)
