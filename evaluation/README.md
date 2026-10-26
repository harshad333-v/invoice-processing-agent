# Evaluation protocol

1. Build a manually labelled set of synthetic or permissioned invoices.
2. Keep a held-out test set that is never used to tune prompts.
3. Report exact field accuracy for vendor, GSTIN, invoice number, date, line items, taxable value, tax breakup, and total.
4. Report zero-edit rate, median/p95 latency, cost per document, and validation catch rate on seeded errors.
5. Report sample size and failure cases; do not invent or extrapolate results.
