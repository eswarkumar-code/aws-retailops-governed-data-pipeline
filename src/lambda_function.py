import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import PurePosixPath
from urllib.parse import unquote_plus

import boto3


LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)
S3 = boto3.client("s3")

REQUIRED_FIELDS = {
    "transaction_id",
    "store_id",
    "transaction_timestamp",
    "product_id",
    "category",
    "quantity",
    "unit_price",
    "discount_amount",
    "payment_method",
    "loyalty_member_id",
}
ALLOWED_PAYMENT_METHODS = {"CARD", "CASH", "MOBILE_WALLET"}


def validate(record):
    errors = []
    missing = sorted(REQUIRED_FIELDS - record.keys())
    if missing:
        errors.append(f"Missing required fields: {', '.join(missing)}")

    unexpected = sorted(record.keys() - REQUIRED_FIELDS)
    if unexpected:
        errors.append(f"Unexpected fields detected: {', '.join(unexpected)}")

    if not isinstance(record.get("transaction_id"), str) or not record.get(
        "transaction_id", ""
    ).strip():
        errors.append("transaction_id must be a non-empty string")

    quantity = record.get("quantity")
    if not isinstance(quantity, int) or isinstance(quantity, bool) or not 1 <= quantity <= 100:
        errors.append("quantity must be an integer between 1 and 100")

    if record.get("payment_method") not in ALLOWED_PAYMENT_METHODS:
        errors.append("payment_method must be CARD, CASH, or MOBILE_WALLET")

    for field in ("unit_price", "discount_amount"):
        value = record.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
            errors.append(f"{field} must be a non-negative number")

    return errors


def enrich(record, source_key, processed_at):
    quantity = Decimal(str(record["quantity"]))
    unit_price = Decimal(str(record["unit_price"]))
    discount = Decimal(str(record["discount_amount"]))
    gross = quantity * unit_price

    return {
        **record,
        "gross_amount": float(gross.quantize(Decimal("0.01"))),
        "net_amount": float((gross - discount).quantize(Decimal("0.01"))),
        "source_key": source_key,
        "processed_at": processed_at,
        "validation_status": "VALID",
    }


def jsonl_bytes(records):
    if not records:
        return b""
    return ("\n".join(json.dumps(record, separators=(",", ":")) for record in records) + "\n").encode()


def process_object(bucket, key):
    response = S3.get_object(Bucket=bucket, Key=key)
    text = response["Body"].read().decode("utf-8")
    processed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    valid_records = []
    invalid_records = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            errors = validate(record)
        except json.JSONDecodeError as exc:
            record = {"raw_line": line}
            errors = [f"Malformed JSON: {exc.msg}"]

        if errors:
            invalid_records.append(
                {
                    "line_number": line_number,
                    "source_key": key,
                    "quarantined_at": processed_at,
                    "validation_status": "INVALID",
                    "validation_errors": errors,
                    "record": record,
                }
            )
        else:
            valid_records.append(enrich(record, key, processed_at))

    stem = PurePosixPath(key).stem
    S3.put_object(
        Bucket=bucket,
        Key=f"processed/{stem}_validated.jsonl",
        Body=jsonl_bytes(valid_records),
        ContentType="application/x-ndjson",
    )
    S3.put_object(
        Bucket=bucket,
        Key=f"quarantine/{stem}_rejected.jsonl",
        Body=jsonl_bytes(invalid_records),
        ContentType="application/x-ndjson",
    )

    summary = {
        "event": "transaction_batch_processed",
        "source_key": key,
        "valid_records": len(valid_records),
        "invalid_records": len(invalid_records),
    }
    LOGGER.info(json.dumps(summary))
    return {k: v for k, v in summary.items() if k != "event"}


def lambda_handler(event, context):
    results = []
    for event_record in event.get("Records", []):
        bucket = event_record["s3"]["bucket"]["name"]
        key = unquote_plus(event_record["s3"]["object"]["key"])
        if key.startswith("raw/") and key.endswith(".jsonl"):
            results.append(process_object(bucket, key))

    return {"statusCode": 200, "results": results}

