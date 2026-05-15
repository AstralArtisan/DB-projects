/*
 * Project3：商品库存并发控制实验初始化脚本
 *
 * 前置条件：
 * 1. 已完成 Project1 的 schema3.sql 与 migrate_to_3nf.sql。
 * 2. proj1_3nf.products 表中已有商品数据。
 */

SET search_path TO proj1_3nf, public;

CREATE TABLE IF NOT EXISTS product_inventory (
    product_id VARCHAR(32) PRIMARY KEY,
    stock_count INTEGER NOT NULL CHECK (stock_count >= 0),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_product_inventory_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
);

/*
 * 可选：为前 5 个商品初始化实验库存。
 * Streamlit 应用每次实验前也会为当前选中的商品重置库存。
 */
INSERT INTO product_inventory (product_id, stock_count)
SELECT
    p.product_id,
    100 AS stock_count
FROM products p
WHERE NOT EXISTS (
    SELECT 1
    FROM product_inventory pi
    WHERE pi.product_id = p.product_id
)
ORDER BY p.product_id
LIMIT 5;

SELECT
    pi.product_id,
    p.product_category_name,
    pi.stock_count,
    pi.updated_at
FROM product_inventory pi
JOIN products p
    ON pi.product_id = p.product_id
ORDER BY pi.product_id
LIMIT 20;
