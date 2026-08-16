CREATE DATABASE IF NOT EXISTS retailops_governed;

CREATE EXTERNAL TABLE IF NOT EXISTS retailops_governed.validated_transactions (
    transaction_id STRING,
    store_id STRING,
    transaction_timestamp STRING,
    product_id STRING,
    category STRING,
    quantity INT,
    unit_price DOUBLE,
    discount_amount DOUBLE,
    payment_method STRING,
    loyalty_member_id STRING,
    gross_amount DOUBLE,
    net_amount DOUBLE,
    source_key STRING,
    processed_at STRING,
    validation_status STRING
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://REPLACE_WITH_BUCKET_NAME/processed/'
TBLPROPERTIES ('classification' = 'json');

CREATE EXTERNAL TABLE IF NOT EXISTS retailops_governed.quarantined_transactions (
    line_number INT,
    source_key STRING,
    quarantined_at STRING,
    validation_status STRING,
    validation_errors ARRAY<STRING>,
    record STRUCT<
        transaction_id:STRING,
        store_id:STRING,
        transaction_timestamp:STRING,
        product_id:STRING,
        category:STRING,
        quantity:INT,
        unit_price:DOUBLE,
        discount_amount:DOUBLE,
        payment_method:STRING,
        loyalty_member_id:STRING,
        customer_email:STRING
    >
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://REPLACE_WITH_BUCKET_NAME/quarantine/'
TBLPROPERTIES ('classification' = 'json');

