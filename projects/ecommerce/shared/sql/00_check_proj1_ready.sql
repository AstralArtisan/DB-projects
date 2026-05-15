/*
 * Check whether Project1's shared Olist schema is ready for Project3/Project4.
 *
 * Expected setup:
 *   database: ecommerce_db
 *   schema:   proj1_3nf
 */

SET search_path TO proj1_3nf, public;

SELECT
    'customers' AS table_name,
    COUNT(*) AS row_count
FROM customers
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL
SELECT 'order_reviews', COUNT(*) FROM order_reviews
ORDER BY table_name;

SELECT
    CASE
        WHEN
            (SELECT COUNT(*) FROM products) > 0
            AND (SELECT COUNT(*) FROM orders) > 0
            AND (SELECT COUNT(*) FROM order_items) > 0
            AND (SELECT COUNT(*) FROM order_reviews) > 0
        THEN 'proj1_3nf is ready'
        ELSE 'proj1_3nf is missing required data'
    END AS readiness_status;
