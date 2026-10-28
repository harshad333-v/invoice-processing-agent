import hashlib
import json
import sys
from pathlib import Path

# Ensure the repository root is importable when Streamlit runs this file directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from app.schemas import Invoice
from app.agent.graph import process_invoice
from app.validators.run import validate_invoice
from app.validators.duplicates import invoice_fingerprint, find_duplicate_candidates
from app.retrieval.vendor_match import suggest_vendor
from app.agent.risk import score_invoice_risk
from app.exports.csv_export import invoice_to_csv
from app.exports.tally_xml import invoice_to_tally_xml
from app.database.models import init_db, SessionLocal, InvoiceRecord, AuditRecord

st.set_page_config(page_title="Invoice Processing Agent", page_icon="🧾", layout="wide")
st.title("🧾 AI Invoice Processing Agent")
st.caption("Extract → validate → risk triage → human review → approve → export. Verify all financial data before accounting use.")
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
            raw = upload.getvalue()
            if len(raw) > 15 * 1024 * 1024:
                st.error("Upload exceeds the 15 MiB limit.")
                st.stop()
            with st.spinner("Preparing document and extracting fields…"):
                result = process_invoice(raw, upload.name)
                invoice = result["invoice"]
                issues = result.get("issues", [])
                risk = score_invoice_risk(invoice, issues)
            st.session_state["workflow_status"] = result.get("status", "needs_review")
            st.session_state["attempts"] = result.get("attempts", 1)
            st.session_state["raw_model_output"] = result.get("raw_model_output", invoice.model_dump_json())
            st.session_state["invoice_json"] = invoice.model_dump(mode="json")
            st.session_state["issues"] = [i.model_dump() for i in issues]
            st.session_state["risk"] = risk
            st.session_state["source_filename"] = upload.name
            st.session_state["source_sha256"] = hashlib.sha256(raw).hexdigest()
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
            with SessionLocal() as db:
                prior_records = db.query(InvoiceRecord).order_by(InvoiceRecord.id.desc()).limit(500).all()
            prior_invoices = []
            known_vendors = set()
            for prior_record in prior_records:
                try:
                    prior_invoice = Invoice.model_validate_json(prior_record.invoice_json)
                    prior_invoices.append(prior_invoice)
                    if prior_invoice.vendor_name.strip():
                        known_vendors.add(prior_invoice.vendor_name.strip())
                except Exception:
                    continue
            duplicates = find_duplicate_candidates(invoice, prior_invoices)
            vendor_suggestion = suggest_vendor(invoice, sorted(known_vendors))
            risk = score_invoice_risk(invoice, issues, duplicates)
            st.session_state["current_issues"] = [i.model_dump() for i in issues]
            st.session_state["current_invoice_json"] = invoice.model_dump(mode="json")
            if issues:
                st.warning("Review the validation findings below.")
                for issue in issues:
                    (st.error if issue.severity == "error" else st.warning)(f"{issue.code}: {issue.message}")
            else:
                st.success("No configured validation issues found. Human approval is still required.")
            st.metric("Review risk score (heuristic)", f"{risk['score']}/100")
            st.caption(f"Risk tier: {risk['tier']}. This is a triage score, not a fraud probability.")
            if vendor_suggestion and vendor_suggestion.get("suggestion"):
                st.info(f"Historical vendor-name suggestion: {vendor_suggestion['vendor_name']} (lexical similarity {vendor_suggestion['similarity']:.0%}). Verify before changing.")
            if duplicates:
                st.warning(f"Potential exact duplicate match(es): {len(duplicates)}. Check saved invoice history before approving.")
                st.json(duplicates)
            blockers = [i for i in issues if i.severity == "error"]
            if blockers:
                st.info("Resolve blocking issues before the app records this invoice as approved.")
            if st.button("Save correction and approve", disabled=bool(blockers)):
                fingerprint = invoice_fingerprint(invoice)
                with SessionLocal() as db:
                    duplicate = db.query(InvoiceRecord).filter(InvoiceRecord.fingerprint == fingerprint).first()
                    if duplicate:
                        st.error(f"Possible exact duplicate of saved record #{duplicate.id}; approval was not saved.")
                    else:
                        record = InvoiceRecord(
                            source_filename=st.session_state.get("source_filename", "invoice"),
                            source_sha256=st.session_state.get("source_sha256", ""),
                            fingerprint=fingerprint,
                            invoice_json=invoice.model_dump_json(),
                            issues_json=json.dumps([i.model_dump() for i in issues]),
                            risk_json=json.dumps(risk),
                            status="approved", approved=True,
                            correction_json=edited,
                        )
                        record.audit_events.append(AuditRecord(action="approved", actor="human_reviewer",
                                                               details_json=json.dumps({"risk_score": risk["score"]})))
                        db.add(record)
                        db.commit()
                        st.session_state["approved_invoice_json"] = invoice.model_dump(mode="json")
                        st.success("Correction saved and approval recorded.")
        except Exception as exc:
            st.error(f"Invoice JSON is invalid: {exc}")
    with right:
        st.subheader("Workflow")
        st.write("Status:", st.session_state.get("workflow_status", "needs_review"))
        st.write("Extraction attempts:", st.session_state.get("attempts", 1))
        st.subheader("Structured output")
        st.json(st.session_state["invoice_json"])
        with st.expander("Raw model output"):
            st.code(st.session_state.get("raw_model_output", ""), language="json")
        st.caption("Extracted data can be wrong. Compare it with the source document before approval.")
        if "approved_invoice_json" in st.session_state:
            approved = Invoice.model_validate(st.session_state["approved_invoice_json"])
            st.download_button("Download approved CSV", invoice_to_csv(approved), "approved_invoice.csv", "text/csv")
            st.download_button("Download Tally XML (verify before import)", invoice_to_tally_xml(approved), "invoice.xml", "application/xml")

st.divider()
st.subheader("Recent saved invoices")
try:
    with SessionLocal() as db:
        records = db.query(InvoiceRecord).order_by(InvoiceRecord.id.desc()).limit(20).all()
        if records:
            st.dataframe([{"ID": r.id, "Vendor": Invoice.model_validate_json(r.invoice_json).vendor_name,
                           "Invoice": Invoice.model_validate_json(r.invoice_json).invoice_number,
                           "Total": str(Invoice.model_validate_json(r.invoice_json).total),
                           "Status": r.status, "Approved": r.approved, "Risk": json.loads(r.risk_json or "{}").get("tier", "unknown")}
                          for r in records], use_container_width=True)
        else:
            st.caption("No invoices have been saved yet.")
except Exception as exc:
    st.warning(f"Could not load invoice history: {exc}")
