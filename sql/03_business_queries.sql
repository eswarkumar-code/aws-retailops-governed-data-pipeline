SELECT
    COUNT(*) AS transactions,
    COUNT(DISTINCT store_id) AS stores,
    SUM(quantity) AS units_sold,
    ROUND(SUM(gross_amount), 2) AS gross_sales,
    ROUND(SUM(discount_amount), 2) AS discounts,
    ROUND(SUM(net_amount), 2) AS net_sales,
    ROUND(AVG(net_amount), 2) AS avg_transaction_value
FROM retailops_governed.current_validated_transactions;

SELECT *
FROM retailops_governed.category_performance
ORDER BY net_sales DESC;

SELECT *
FROM retailops_governed.pipeline_batch_quality
ORDER BY source_key;

SELECT *
FROM retailops_governed.validation_failure_taxonomy
ORDER BY occurrences DESC, validation_error;

