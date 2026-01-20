import streamlit as st
from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from PIL import Image
import io
import re

st.set_page_config(page_title="RFQ DOCX Extractor", layout="wide")
st.title("📄 RFQ DOCX Extractor")
st.caption("Accurate extraction from DOCX RFQs (tables + images supported)")

uploaded = st.file_uploader("Upload RFQ (.docx only)", type=["docx"])

# ---------------- HELPERS ----------------

def clean(text):
    return re.sub(r"\s+", " ", text).strip()

def extract_paragraph_text(doc):
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

def extract_table_text(doc):
    rows = []
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                rows.append(" | ".join(cells))
    return "\n".join(rows)

def extract_full_text(doc):
    return extract_paragraph_text(doc) + "\n" + extract_table_text(doc)

def safe_group(match):
    if not match:
        return "Not found"
    return clean(match.group(match.lastindex))

def extract_fields(text):
    patterns = {
        "Project title": r"(Project Title|Emergency Maintenance Fault Repair)\s*(.*)",
        "Description of work": r"Brief Description of Works[:\s]*(.*?)(Date Created|$)",
        "RFQ close": r"(RFQ Close|Close Date|RFQ Closing)[:\s|]*(.*)",
        "Proposed start date": r"(Proposed Start Date|Start Date)[:\s|]*(.*)",
        "Proposed completion date": r"(Proposed Completion Date|Completion Date)[:\s|]*(.*)",
        "Site location": r"(Site Location)[:\s|]*(.*)",
        "LRD": r"\bLRD\b[:\s|]*(.*)",
        "Inc": r"\bINC\b[:\s|]*(.*)",
        "Tas": r"\bTAS\b[:\s|]*(.*)",
        "Practical work": r"(Practical Work)[:\s|]*(.*)",
    }

    results = {}
    for field, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        results[field] = safe_group(match)
    return results

def extract_images(doc):
    images = []
    for rel in doc.part.rels.values():
        if rel.reltype == RT.IMAGE:
            blob = rel.target_part.blob
            try:
                img = Image.open(io.BytesIO(blob))
                images.append((img, blob))
            except:
                pass
    return images

# ---------------- MAIN ----------------

if uploaded:
    doc = Document(uploaded)

    full_text = extract_full_text(doc)
    fields = extract_fields(full_text)
    images = extract_images(doc)

    st.divider()
    st.header("🧾 Extracted RFQ Fields")

    for k, v in fields.items():
        st.text_area(k, v, height=90)

    st.divider()
    st.header("🖼️ Extracted Images")

    if images:
        cols = st.columns(3)
        for i, (img, raw) in enumerate(images):
            with cols[i % 3]:
                st.image(img, caption=f"Image {i+1}", use_container_width=True)
                st.download_button(
                    "⬇️ Download image",
                    data=raw,
                    file_name=f"rfq_image_{i+1}.png",
                    mime="image/png"
                )
    else:
        st.info("No extractable images found in this document.")

    st.divider()
    with st.expander("📄 Full extracted text (debug view)"):
        st.text(full_text)
