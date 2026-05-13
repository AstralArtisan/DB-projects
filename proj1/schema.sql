DROP TABLE IF EXISTS cleaned_flat_table CASCADE;

CREATE TABLE cleaned_flat_table (
    id                            SERIAL        PRIMARY KEY,
    order_id                      VARCHAR(32)   NOT NULL,
    order_item_id                 INTEGER       NOT NULL CHECK (order_item_id > 0),
    customer_unique_id            VARCHAR(32)   NOT NULL,
    order_purchase_timestamp      TIMESTAMP     NOT NULL,
    order_delivered_customer_date TIMESTAMP     NOT NULL,
    order_estimated_delivery_date TIMESTAMP     NOT NULL,
    product_id                    VARCHAR(32)   NOT NULL,
    product_category_name         VARCHAR(100)  NOT NULL DEFAULT 'Unknown',
    price                         NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    freight_value                 NUMERIC(10,2) NOT NULL CHECK (freight_value >= 0),
    review_id                     VARCHAR(32)   NOT NULL,
    review_score                  INTEGER       NOT NULL DEFAULT 3
                                      CHECK (review_score BETWEEN 1 AND 5),
    UNIQUE (order_id, order_item_id, review_id)
);
