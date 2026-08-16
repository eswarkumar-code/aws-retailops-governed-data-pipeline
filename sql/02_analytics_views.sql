CREATE OR REPLACE VIEW retailops_governed.current_validated_transactions AS
SELECT *
FROM (
    SELECT
        v.*,
        ROW_NUMBER() OVER (
            PARTITION BY transaction_id
            ORDER BY from_iso8601_timestamp(processed_at) DESC, source_key DESC
        ) AS record_rank
    FROM retailops_governed.validated_transactions v
    WHERE validation_status = 'VALID'
)
WHERE record_rank = 1;

CREATE OR REPLACE VIEW retailops_governed.pipeline_batch_quality AS
WITH valid AS (
    SELECT source_key, COUNT(*) AS valid_records
    FROM retailops_governed.validated_transactions
    GROUP BY source_key
), invalid AS (
    SELECT source_key, COUNT(*) AS invalid_records
    FROM retailops_governed.quarantined_transactions
    GROUP BY source_key
)
SELECT
    COALESCE(v.source_key, i.source_key) AS source_key,
    COALESCE(valid_records, 0) AS valid_records,
    COALESCE(invalid_records, 0) AS invalid_records,
    COALESCE(valid_records, 0) + COALESCE(invalid_records, 0) AS total_records,
    ROUND(
        100.0 * COALESCE(valid_records, 0)
        / NULLIF(COALESCE(valid_records, 0) + COALESCE(invalid_records, 0), 0),
        2
    ) AS acceptance_rate_percent
FROM valid v
FULL OUTER JOIN invalid i ON v.source_key = i.source_key;

CREATE OR REPLACE VIEW retailops_governed.category_performance AS
SELECT
    category,
    COUNT(*) AS transactions,
    SUM(quantity) AS units_sold,
    ROUND(SUM(gross_amount), 2) AS gross_sales,
    ROUND(SUM(discount_amount), 2) AS discounts,
    ROUND(SUM(net_amount), 2) AS net_sales,
    ROUND(100.0 * SUM(discount_amount) / NULLIF(SUM(gross_amount), 0), 2)
        AS discount_rate_percent
FROM retailops_governed.current_validated_transactions
GROUP BY category;

CREATE OR REPLACE VIEW retailops_governed.validation_failure_taxonomy AS
SELECT
    validation_error,
    COUNT(*) AS occurrences,
    COUNT(DISTINCT source_key) AS affected_batches
FROM retailops_governed.quarantined_transactions
CROSS JOIN UNNEST(validation_errors) AS t(validation_error)
GROUP BY validation_error;

