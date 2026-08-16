import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "src" / "lambda_function.py"
SPEC = importlib.util.spec_from_file_location("lambda_function", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def valid_record():
    return {
        "transaction_id": "TXN-1",
        "store_id": "STORE-1",
        "transaction_timestamp": "2026-08-14T08:05:12Z",
        "product_id": "SKU-1",
        "category": "Beverages",
        "quantity": 2,
        "unit_price": 3.49,
        "discount_amount": 0.50,
        "payment_method": "CARD",
        "loyalty_member_id": None,
    }


def test_valid_record_has_no_errors():
    assert MODULE.validate(valid_record()) == []


def test_schema_drift_is_rejected():
    record = valid_record() | {"customer_email": "synthetic@example.test"}
    assert "Unexpected fields detected: customer_email" in MODULE.validate(record)


def test_invalid_quantity_and_payment_are_rejected():
    record = valid_record() | {"quantity": -2, "payment_method": "CRYPTO"}
    errors = MODULE.validate(record)
    assert "quantity must be an integer between 1 and 100" in errors
    assert "payment_method must be CARD, CASH, or MOBILE_WALLET" in errors


def test_enrichment_calculates_amounts():
    enriched = MODULE.enrich(valid_record(), "raw/batch.jsonl", "2026-08-15T00:00:00Z")
    assert enriched["gross_amount"] == 6.98
    assert enriched["net_amount"] == 6.48
    assert enriched["validation_status"] == "VALID"

