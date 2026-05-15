/*
 * 阶段三：3NF 结构（完整保真方案）
 * 说明：
 * 1. 基于阶段二宽表 cleaned_flat_table 迁移。
 * 2. 宽表已包含 review_id，可直接保留逐条评价记录。
 */

CREATE SCHEMA IF NOT EXISTS proj1_3nf;
SET search_path TO proj1_3nf;

DROP TABLE IF EXISTS order_reviews CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_unique_id VARCHAR(32) PRIMARY KEY
);

CREATE TABLE products (
    product_id VARCHAR(32) PRIMARY KEY,
    product_category_name VARCHAR(100) NOT NULL DEFAULT 'Unknown'
);

CREATE TABLE orders (
    order_id VARCHAR(32) PRIMARY KEY,
    customer_unique_id VARCHAR(32) NOT NULL,
    order_purchase_timestamp TIMESTAMP NOT NULL,
    order_delivered_customer_date TIMESTAMP NOT NULL,
    order_estimated_delivery_date TIMESTAMP NOT NULL,
    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_unique_id)
        REFERENCES customers(customer_unique_id)
);

CREATE TABLE order_items (
    order_id VARCHAR(32) NOT NULL,
    order_item_id INTEGER NOT NULL CHECK (order_item_id > 0),
    product_id VARCHAR(32) NOT NULL,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    freight_value NUMERIC(10, 2) NOT NULL CHECK (freight_value >= 0),
    CONSTRAINT pk_order_items PRIMARY KEY (order_id, order_item_id),
    CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id),
    CONSTRAINT fk_order_items_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
);

CREATE TABLE order_reviews (
    review_id VARCHAR(32) NOT NULL,
    order_id VARCHAR(32) NOT NULL,
    review_score SMALLINT NOT NULL CHECK (review_score BETWEEN 1 AND 5),
    CONSTRAINT pk_order_reviews PRIMARY KEY (review_id, order_id),
    CONSTRAINT fk_order_reviews_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id)
);

CREATE INDEX idx_orders_customer_unique_id
    ON orders(customer_unique_id);

CREATE INDEX idx_order_items_product_id
    ON order_items(product_id);

CREATE INDEX idx_order_reviews_order_id
    ON order_reviews(order_id);
