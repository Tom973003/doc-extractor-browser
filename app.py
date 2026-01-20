import streamlit as st
import fitz
import re
import io
import zipfile
from PIL import Image

st.set_page_config(page_title="RFQ Extractor", layout="wide")
st.title("📄 RFQ Structured Extractor")

uploaded_file = st.file_uploader("Upload RFQ PDF", type=["pdf"])

# ---------------- HELPERS ----------------

def clean(text):
    if not text:
        return "Not found"
    return re.sub(r"\s+", " ", str(text)).strip()

def extract_fields(text):
    fields = {
        "Project title": r"(Emergency .*? Repair|Emergency Maintenance .*? Repair)",
        "Description of work": r"Brief Description of Works:? (.*?)(?:Date Created|$)",
        "RFQ close": r"RFQ Close:? *(.*)",
        "Proposed start date": r"Proposed Start Date:? *(.*)",
        "Proposed completion date": r"Proposed Completion Date:? *(.*)",
        "Site location": r"(P\d[-–]\d.*?)(?:\n|$)",
        "LRD": r"\bLRD\b[: ]*(Yes|No|Y|N)?",
        "Inc": r"\bInc\b[: ]*(Yes|No|Y|N)?",
        "Tas": r"\bTas\b[: ]*(Yes|No|Y|N)?",
        "Practical work": r"Practical Work:? *(.*)",
    }

    results = {}
    for k, pattern in fields.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        value = match.group(1) if match and match.groups() else None
        results[k] = clean(value)

    return results

def extract_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []

    for page_i, page in enumerate(doc):
        for img in page.get_images(full=True):
            xref = img[0]
            base = doc.extract_image(xref)

            if base["width"] < 300 or base["height"] < 300:
                continue

            images.append({
                "page": page_i + 1,
                "bytes": base["image"],
                "ext": base["ext"]
            })

    return images

# ---------------- MAIN ----------------

if uploaded_file:
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    full_text = ""
    for page in doc:
        full_text += page.get_text()

    fields = extract_fields(full_text)
    images = extract_images(pdf_bytes)

    st.subheader("📋 Extracted RFQ Fields")

    for k, v in fields.items():
        st.markdown(f"**{k}:** {v}")

    st.subheader("📎 Attachments")
    st.write(f"Attached photos found: **{len(images)}**")

    if images:
        st.subheader("🖼️ Attached Photos")
        cols = st.columns(3)

        for i, img in enumerate(images):
            image = Image.open(io.BytesIO(img["bytes"]))
            cols[i % 3].image(
                image,
                caption=f"Photo – Page {img['page']}",
                use_container_width=True
            )

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for i, img in enumerate(images):
                zipf.writestr(
                    f"photo_{i+1}_page_{img['page']}.{img['ext']}",
                    img["bytes"]
                )

        st.download_button(
            "⬇️ Download Attached Photos (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="attached_photos.zip",
            mime="application/zip"
        )
    else:
        st.info("No photographic attachments detected.")
