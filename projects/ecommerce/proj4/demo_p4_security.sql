/*
 * Project4：Olist 数据库安全与完整性实验初始化脚本
 *
 * 前置条件：
 * 1. 已完成 Project1 的 schema3.sql 与 migrate_to_3nf.sql。
 * 2. proj1_3nf.order_items 与 proj1_3nf.products 中已有数据。
 *
 * 实验规则：
 * - 完整性红线：订单项运费 freight_value 不能高于商品售价 price。
 * - 敏感字段：freight_value 对分析师隐藏，只允许管理员查看。
 */

SET search_path TO proj1_3nf, public;

-- ========================================================
-- 模块 A: 完整性控制 (拦截运费异常的订单项)
-- ========================================================

DROP TRIGGER IF EXISTS trg_check_order_item_freight ON order_items;
DROP FUNCTION IF EXISTS check_order_item_freight();

CREATE OR REPLACE FUNCTION check_order_item_freight() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.freight_value > NEW.price THEN
        RAISE EXCEPTION '数据完整性拦截：订单项运费 % 不能高于商品售价 %',
            NEW.freight_value,
            NEW.price;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_order_item_freight
BEFORE INSERT OR UPDATE ON order_items
FOR EACH ROW EXECUTE PROCEDURE check_order_item_freight();

-- ========================================================
-- 模块 B: 安全性控制 (脱敏视图与分析师权限)
-- ========================================================

DROP VIEW IF EXISTS v_public_order_items;

CREATE OR REPLACE VIEW v_public_order_items AS
SELECT
    oi.order_id,
    oi.order_item_id,
    oi.product_id,
    p.product_category_name,
    oi.price
FROM order_items oi
JOIN products p
    ON oi.product_id = p.product_id;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'analyst_user') THEN
        REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA proj1_3nf FROM analyst_user;
        REVOKE USAGE ON SCHEMA proj1_3nf FROM analyst_user;
    END IF;
END $$;

DROP USER IF EXISTS analyst_user;
CREATE USER analyst_user WITH PASSWORD 'Analyst@123';

GRANT USAGE ON SCHEMA proj1_3nf TO analyst_user;
REVOKE ALL PRIVILEGES ON order_items FROM analyst_user;
GRANT SELECT ON v_public_order_items TO analyst_user;
ALTER USER analyst_user SET search_path TO "$user", proj1_3nf, public;

-- ========================================================
-- 模块 C: 初始化验证
-- ========================================================

SELECT
    'trigger_ready' AS check_name,
    tgname AS object_name
FROM pg_trigger
WHERE tgname = 'trg_check_order_item_freight';

SELECT *
FROM v_public_order_items
LIMIT 1;
