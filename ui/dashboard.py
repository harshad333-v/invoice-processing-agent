import io, json
import streamlit as st
from PIL import Image
from app.extraction.extractor import extract_invoice
from app.validators.run import validate_invoice
from app.exports.csv_export import invoice_to_csv

st.set_page_config(page_title="Invoice Processing Agent", page_icon="🧾", layout="wide")
st.title("🧾 AI Invoice Processing Agent")
st.caption("Extract → validate → human review → export. Always verify before accounting use.")
upload = st.file_uploader("Upload invoice image", type=["png","jpg","jpeg","webp"])
if upload:
    left, right = st.columns([1,1])
    with left:
        st.image(upload, caption="Uploaded invoice", use_container_width=True)
    if st.button("Extract and validate", type="primary"):
        try:
            with st.spinner("Extracting invoice fields…"):
                invoice = extract_invoice(upload.getvalue(), upload.type or "image/png")
            issues = validate_invoice(invoice)
            st.session_state["invoice_json"] = invoice.model_dump(mode="json")
            st.session_state["issues"] = [i.model_dump() for i in issues]
        except Exception as exc:
            st.error(f"Processing failed: {exc}")
    if "invoice_json" in st.session_state:
        with right:
            st.subheader("Extracted fields — review before approval")
            edited = st.text_area("Edit invoice JSON", json.dumps(st.session_state["invoice_json"], indent=2), height=430)
            try:
                from app.schemas import Invoice
                invoice = Invoice.model_validate_json(edited)
                issues = validate_invoice(invoice)
                if issues:
                    st.warning("Validation issues found")
                    for issue in issues: st.write(f"**{issue.code}** — {issue.message}")
                else: st.success("No configured validation issues. Human approval is still required.")
                approved = st.checkbox("I reviewed and approve this invoice")
                if approved:
                    st.download_button("Download approved CSV", invoice_to_csv(invoice), "invoice.csv", "text/csv")
                    st.download_button("Download approved JSON", invoice.model_dump_json(indent=2), "invoice.json", "application/json")
            except Exception as exc:
                st.error(f"Invalid invoice JSON: {exc}")
