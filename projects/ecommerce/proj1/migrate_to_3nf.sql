/*
 * 将阶段二宽表 cleaned_flat_table 迁移到 3NF 结构。
 *
 * 前置条件：
 * 1. 已执行 schema3.sql。
 * 2. cleaned_flat_table 已导入数据库（public schema）。
 */

SET search_path TO proj1_3nf, public;

DROP VIEW IF EXISTS source_cleaned_flat_table;
CREATE TEMP VIEW source_cleaned_flat_table AS
SELECT
    order_id,
    order_item_id,
    customer_unique_id,
    order_purchase_timestamp,
    order_delivered_customer_date,
    order_estimated_delivery_date,
    product_id,
    product_category_name,
    price,
    freight_value,
    review_id,
    review_score
FROM cleaned_flat_table;

TRUNCATE TABLE
    order_reviews,
    order_items,
    orders,
    products,
    customers;

INSERT INTO customers (customer_unique_id)
SELECT DISTINCT customer_unique_id
FROM source_cleaned_flat_table;

INSERT INTO products (product_id, product_category_name)
SELECT DISTINCT
    product_id,
    product_category_name
FROM source_cleaned_flat_table;

INSERT INTO orders (
    order_id,
    customer_unique_id,
    order_purchase_timestamp,
    order_delivered_customer_date,
    order_estimated_delivery_date
)
SELECT DISTINCT
    order_id,
    customer_unique_id,
    order_purchase_timestamp,
    order_delivered_customer_date,
    order_estimated_delivery_date
FROM source_cleaned_flat_table;

INSERT INTO order_items (
    order_id,
    order_item_id,
    product_id,
    price,
    freight_value
)
SELECT DISTINCT
    order_id,
    order_item_id,
    product_id,
    price,
    freight_value
FROM source_cleaned_flat_table;

INSERT INTO order_reviews (
    review_id,
    order_id,
    review_score
)
SELECT DISTINCT
    review_id,
    order_id,
    review_score::SMALLINT
FROM source_cleaned_flat_table;
