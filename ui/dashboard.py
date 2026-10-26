import json
import streamlit as st
from app.schemas import Invoice
from app.extraction.extractor import extract_invoice
from app.extraction.preprocess import document_to_image
from app.validators.run import validate_invoice
from app.exports.csv_export import invoice_to_csv
from app.exports.tally_xml import invoice_to_tally_xml
from app.database.models import init_db, SessionLocal, InvoiceRecord

st.set_page_config(page_title="Invoice Processing Agent", page_icon="🧾", layout="wide")
st.title("🧾 AI Invoice Processing Agent")
st.caption("Extract → validate → human review → approve → export. Verify all financial data before accounting use.")
init_db()
with st.sidebar:
    st.subheader("System status")
    st.write("Vision model is configured through .env or Streamlit secrets.")
    st.warning("Use synthetic or permissioned invoices only. Do not upload confidential data to an unapproved API.")
upload = st.file_uploader("Upload invoice PDF or image", type=["pdf", "png", "jpg", "jpeg", "webp"])
if upload:
    if not upload.name.lower().endswith(".pdf"):
        st.image(upload, caption="Uploaded invoice", use_container_width=True)
    if st.button("Extract and validate", type="primary"):
        try:
            with st.spinner("Preparing document and extracting fields…"):
                image_bytes, mime = document_to_image(upload.getvalue(), upload.name)
                invoice = extract_invoice(image_bytes, mime)
                issues = validate_invoice(invoice)
            st.session_state["invoice_json"] = invoice.model_dump(mode="json")
            st.session_state["issues"] = [i.model_dump() for i in issues]
            st.session_state["source_filename"] = upload.name
            st.session_state.pop("approved_invoice_json", None)
        except Exception as exc:
            st.error(f"Processing failed: {exc}")
if "invoice_json" in st.session_state:
    left, right = st.columns([1, 1])
    with left:
        st.subheader("Extracted fields — edit before approval")
        edited = st.text_area("Invoice JSON", json.dumps(st.session_state["invoice_json"], indent=2), height=440)
        try:
            invoice = Invoice.model_validate_json(edited)
            issues = validate_invoice(invoice)
            st.session_state["current_issues"] = [i.model_dump() for i in issues]
            if issues:
                st.warning("Review the validation findings below.")
                for issue in issues:
                    (st.error if issue.severity == "error" else st.warning)(f"{issue.code}: {issue.message}")
            else:
                st.success("No configured validation issues found. Human approval is still required.")
            blockers = [i for i in issues if i.severity == "error"]
            if blockers:
                st.info("Resolve blocking issues before the app records this invoice as approved.")
            if st.button("Save correction and approve", disabled=bool(blockers)):
                with SessionLocal() as db:
                    record = InvoiceRecord(
                        source_filename=st.session_state.get("source_filename", "invoice"),
                        invoice_json=invoice.model_dump_json(),
                        issues_json=json.dumps([i.model_dump() for i in issues]),
                        status="approved",
                        approved=True,
                        correction_json=edited,
                    )
                    db.add(record)
                    db.commit()
                st.session_state["approved_invoice_json"] = invoice.model_dump(mode="json")
                st.success("Correction saved and approval recorded.")
        except Exception as exc:
            st.error(f"Invoice JSON is invalid: {exc}")
    with right:
        st.subheader("Structured output")
        st.json(st.session_state["invoice_json"])
        st.caption("Extracted data can be wrong. Compare it with the source document before approval.")
        if "approved_invoice_json" in st.session_state:
            approved = Invoice.model_validate(st.session_state["approved_invoice_json"])
            st.download_button("Download approved CSV", invoice_to_csv(approved), "approved_invoice.csv", "text/csv")
            st.download_button("Download Tally XML (verify before import)", invoice_to_tally_xml(approved), "invoice.xml", "application/xml")
