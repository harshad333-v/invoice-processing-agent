"""Evaluate field-level extraction accuracy from aligned JSONL files.

Each line in predictions.jsonl and ground_truth.jsonl must be a JSON object using the
same record order and invoice schema field names. This script reports exact-match
accuracy for scalar fields and numeric tolerance for monetary totals. It does not
claim model quality without a representative labeled test set.
"""
import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

FIELDS = ("vendor_name", "gstin", "invoice_number", "invoice_date", "taxable_value",
          "cgst", "sgst", "igst", "total", "currency")
NUMERIC_FIELDS = {"taxable_value", "cgst", "sgst", "igst", "total"}


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_number}: invalid JSON") from exc
    return rows


def field_match(field: str, predicted, expected, tolerance: Decimal) -> bool:
    if field in NUMERIC_FIELDS:
        try:
            return abs(Decimal(str(predicted or 0)) - Decimal(str(expected or 0))) <= tolerance
        except InvalidOperation:
            return False
    return str(predicted or "").strip().casefold() == str(expected or "").strip().casefold()


def evaluate(predictions: list[dict], ground_truth: list[dict], tolerance: Decimal = Decimal("0.01")) -> dict:
    if len(predictions) != len(ground_truth):
        raise ValueError(f"Row count mismatch: predictions={len(predictions)}, ground_truth={len(ground_truth)}")
    if not predictions:
        raise ValueError("No aligned records found")
    result = {"records": len(predictions), "tolerance": str(tolerance), "fields": {}}
    total_correct = total_fields = 0
    for field in FIELDS:
        correct = sum(field_match(field, p.get(field), g.get(field), tolerance)
                      for p, g in zip(predictions, ground_truth))
        result["fields"][field] = {"correct": correct, "total": len(predictions),
                                   "accuracy": round(correct / len(predictions), 4)}
        total_correct += correct
        total_fields += len(predictions)
    result["micro_field_accuracy"] = round(total_correct / total_fields, 4)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument("--tolerance", default="0.01")
    args = parser.parse_args()
    report = evaluate(read_jsonl(args.predictions), read_jsonl(args.ground_truth), Decimal(args.tolerance))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
