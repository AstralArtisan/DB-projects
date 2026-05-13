/*
 * 3NF 结构验证脚本。
 * 运行前请保证：
 * 1. schema3.sql 和 migrate_to_3nf.sql 已执行完成。
 * 2. cleaned_flat_table 仍可在当前会话访问。
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

-- 行数概览
SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL
SELECT 'order_reviews', COUNT(*) FROM order_reviews;

-- 主键重复检查，结果应全部为 0
SELECT COUNT(*) AS duplicated_customer_keys
FROM (
    SELECT customer_unique_id
    FROM customers
    GROUP BY customer_unique_id
    HAVING COUNT(*) > 1
) t;

SELECT COUNT(*) AS duplicated_product_keys
FROM (
    SELECT product_id
    FROM products
    GROUP BY product_id
    HAVING COUNT(*) > 1
) t;

SELECT COUNT(*) AS duplicated_order_keys
FROM (
    SELECT order_id
    FROM orders
    GROUP BY order_id
    HAVING COUNT(*) > 1
) t;

SELECT COUNT(*) AS duplicated_order_item_keys
FROM (
    SELECT order_id, order_item_id
    FROM order_items
    GROUP BY order_id, order_item_id
    HAVING COUNT(*) > 1
) t;

SELECT COUNT(*) AS duplicated_review_keys
FROM (
    SELECT review_id, order_id
    FROM order_reviews
    GROUP BY review_id, order_id
    HAVING COUNT(*) > 1
) t;

-- 外键检查，结果应全部为 0
SELECT COUNT(*) AS orphan_orders
FROM orders o
LEFT JOIN customers c
    ON o.customer_unique_id = c.customer_unique_id
WHERE c.customer_unique_id IS NULL;

SELECT COUNT(*) AS orphan_order_items_by_order
FROM order_items oi
LEFT JOIN orders o
    ON oi.order_id = o.order_id
WHERE o.order_id IS NULL;

SELECT COUNT(*) AS orphan_order_items_by_product
FROM order_items oi
LEFT JOIN products p
    ON oi.product_id = p.product_id
WHERE p.product_id IS NULL;

SELECT COUNT(*) AS orphan_reviews
FROM order_reviews r
LEFT JOIN orders o
    ON r.order_id = o.order_id
WHERE o.order_id IS NULL;

-- 迁移结果与源宽表的粒度校验
SELECT
    (SELECT COUNT(DISTINCT customer_unique_id) FROM source_cleaned_flat_table)
        AS expected_customers,
    (SELECT COUNT(*) FROM customers) AS actual_customers,
    (SELECT COUNT(DISTINCT order_id) FROM source_cleaned_flat_table)
        AS expected_orders,
    (SELECT COUNT(*) FROM orders) AS actual_orders,
    (SELECT COUNT(DISTINCT product_id) FROM source_cleaned_flat_table)
        AS expected_products,
    (SELECT COUNT(*) FROM products) AS actual_products,
    (
        SELECT COUNT(*)
        FROM (
            SELECT DISTINCT order_id, order_item_id, product_id, price, freight_value
            FROM source_cleaned_flat_table
        ) s
    ) AS expected_order_items,
    (SELECT COUNT(*) FROM order_items) AS actual_order_items,
    (SELECT COUNT(DISTINCT (review_id, order_id)) FROM source_cleaned_flat_table)
        AS expected_reviews,
    (SELECT COUNT(*) FROM order_reviews) AS actual_reviews;
