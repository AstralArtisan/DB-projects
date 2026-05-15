# Step3：数据库规范化与数据可视化

## 函数依赖分析与规范化

### 宽表结构回顾

阶段二的 `cleaned_flat_table` 包含 13 列（含代理主键 `id`），业务候选键为 `(order_id, order_item_id, review_id)`。以下分析基于该候选键。

### 函数依赖集

| 编号 | 函数依赖 | 类型 |
|------|---------|------|
| FD1 | `order_id` → `customer_unique_id, order_purchase_timestamp, order_delivered_customer_date, order_estimated_delivery_date` | 部分依赖（候选键的真子集决定非主属性） |
| FD2 | `(order_id, order_item_id)` → `product_id, price, freight_value` | 部分依赖（候选键的真子集决定非主属性） |
| FD3 | `product_id` → `product_category_name` | 传递依赖（通过 order_items → product_id → product_category_name） |
| FD4 | `(review_id, order_id)` → `review_score` | 部分依赖（候选键的真子集决定非主属性） |

### 冗余与异常分析

宽表存在以下问题：

1. **数据冗余**：
   - 同一客户的 `customer_unique_id` 在其所有订单明细行中重复出现
   - 同一订单的时间戳字段在该订单的每个明细×评价行中重复
   - 同一商品的 `product_category_name` 在每次出现时重复存储

2. **插入异常**：无法单独添加一个新客户或新商品，必须伴随完整的订单明细和评价记录

3. **删除异常**：删除某商品的最后一条订单明细，会导致该商品的类别信息丢失

4. **更新异常**：修改某商品的类别名称，需要更新所有包含该商品的行，部分更新会导致数据不一致

## 概念设计

### E-R 图

根据分析目标和数据特征，识别出 5 个实体及其联系：

**实体与属性：**

| 实体 | 主键 | 其他属性 |
|------|------|---------|
| Customer | customer_unique_id | — |
| Order | order_id | order_purchase_timestamp, order_delivered_customer_date, order_estimated_delivery_date |
| OrderItem | (order_id, order_item_id) | price, freight_value |
| Product | product_id | product_category_name |
| OrderReview | (review_id, order_id) | review_score |

**联系与类型：**

| 联系 | 类型 | 说明 |
|------|------|------|
| Customer → Order | 1:N | 一个客户可下多个订单 |
| Order → OrderItem | 1:N | 一个订单包含多个商品项 |
| Product → OrderItem | 1:N | 一个商品可出现在多个订单项中 |
| Order → OrderReview | 1:N | 一个订单可有多条评价 |

E-R图：

![er](E:\课程\数据库\课程proj\proj1\er.png)

## 逻辑结构设计与规范化

### E-R 图转关系模式

将 E-R 图中的 5 个实体直接转换为 5 个关系模式：

- **customers**(<u>customer_unique_id</u>)
- **orders**(<u>order_id</u>, *customer_unique_id*, order_purchase_timestamp, order_delivered_customer_date, order_estimated_delivery_date)
- **products**(<u>product_id</u>, product_category_name)
- **order_items**(<u><i>order_id</i>, order_item_id</u>, *product_id*, price, freight_value)
- **order_reviews**(<u>review_id, <i>order_id</i></u>, review_score)

其中下划线标注主键，斜体为外键。

### 3NF 分解过程

从宽表 R(<u>order_id, order_item_id, review_id</u>, customer_unique_id, order_purchase_timestamp, order_delivered_customer_date, order_estimated_delivery_date, product_id, product_category_name, price, freight_value, review_score) 出发：

**第一步：消除部分依赖（达到 2NF）**

- FD1：`order_id → customer_unique_id, 时间戳×3`，候选键的真子集决定非主属性 → 拆出 **orders** 表
- FD2：`(order_id, order_item_id) → product_id, price, freight_value`，候选键的真子集决定非主属性 → 拆出 **order_items** 表
- FD4：`(review_id, order_id) → review_score`，候选键的真子集决定非主属性 → 拆出 **order_reviews** 表

**第二步：消除传递依赖（达到 3NF）**

- FD3：在 order_items 中，`product_id → product_category_name` 构成传递依赖（order_items 的主键 → product_id → product_category_name） → 拆出 **products** 表
- 同时提取 **customers** 表作为 orders 外键的参照实体

**分解结果**：5 张表均满足 3NF，每个非主属性完全依赖于主键且不存在传递依赖。

### 参照完整性

| 外键 | 所在表 | 参照表 |
|------|--------|--------|
| orders.customer_unique_id | orders | customers |
| order_items.order_id | order_items | orders |
| order_items.product_id | order_items | products |
| order_reviews.order_id | order_reviews | orders |

## 架构迁移

### 3NF 建表脚本

对应 DDL 脚本为 `schema3.sql`，在 `proj1_3nf` schema 下创建 5 张规范化表：

```sql
CREATE SCHEMA IF NOT EXISTS proj1_3nf;

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
    FOREIGN KEY (customer_unique_id) REFERENCES customers(customer_unique_id)
);

CREATE TABLE order_items (
    order_id VARCHAR(32) NOT NULL,
    order_item_id INTEGER NOT NULL CHECK (order_item_id > 0),
    product_id VARCHAR(32) NOT NULL,
    price NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    freight_value NUMERIC(10,2) NOT NULL CHECK (freight_value >= 0),
    PRIMARY KEY (order_id, order_item_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE order_reviews (
    review_id VARCHAR(32) NOT NULL,
    order_id VARCHAR(32) NOT NULL,
    review_score SMALLINT NOT NULL CHECK (review_score BETWEEN 1 AND 5),
    PRIMARY KEY (review_id, order_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);
```

### 数据迁移

迁移脚本 `migrate_to_3nf.sql` 通过 `CREATE TEMP VIEW` 引用阶段二宽表，使用 `SELECT DISTINCT` 逐表提取数据：

| 目标表 | 迁移行数 | 说明 |
|--------|---------|------|
| customers | 92,753 | DISTINCT customer_unique_id |
| products | 32,070 | DISTINCT product_id + category |
| orders | 95,830 | DISTINCT order_id + 时间戳 |
| order_items | 109,369 | DISTINCT (order_id, order_item_id) + price/freight |
| order_reviews | 96,359 | DISTINCT (review_id, order_id) + score |

### 迁移验证

执行 `validate_3nf.sql` 验证结果：

- 所有主键重复检查：**0**（无重复）
- 所有外键孤儿检查：**0**（无孤儿记录）
- 源宽表与目标表的粒度校验：**全部匹配**

```bash
DROP VIEW
CREATE VIEW
  table_name   | row_count
---------------+-----------
 customers     |     92753
 products      |     32070
 orders        |     95830
 order_items   |    109369
 order_reviews |     96359
(5 rows)

 duplicated_customer_keys
--------------------------
                        0
(1 row)

 duplicated_product_keys
-------------------------
                       0
(1 row)

 duplicated_order_keys
-----------------------
                     0
(1 row)

 duplicated_order_item_keys
----------------------------
                          0
(1 row)

 duplicated_review_keys
------------------------
                      0
(1 row)

 orphan_orders
---------------
             0
(1 row)

 orphan_order_items_by_order
-----------------------------
                           0
(1 row)

 orphan_order_items_by_product
-------------------------------
                             0
(1 row)

 orphan_reviews
----------------
              0
(1 row)

 expected_customers | actual_customers | expected_orders | actual_orders | expected_products | actual_products | expected_order_items | actual_order_items | expected_reviews | actual_reviews
--------------------+------------------+-----------------+---------------+-------------------+-----------------+----------------------+--------------------+------------------+----------------
              92753 |            92753 |           95830 |         95830 |             32070 |           32070 |               109369 |             109369 |            96359 |          96359
(1 row)
```

## 数据可视化

使用 Streamlit 框架构建数据分析看板（`project1_app.py`），通过 psycopg2 连接 openGauss 数据库，实时从 3NF 表中查询数据。

### 核心指标概览

使用 `st.metric` 组件展示三个核心指标：

| 指标 | SQL | 数据来源 |
|------|-----|---------|
| 总订单数 | `COUNT(*) FROM orders` | orders 表 |
| 总客户数 | `COUNT(*) FROM customers` | customers 表 |
| 平均评分 | `AVG(review_score) FROM order_reviews` | order_reviews 表 |

### 分析目标 1：物流时效与客户满意度

将订单按实际送达时间是否晚于预计送达时间分为"逾期送达"和"准时送达"两组，计算各组的平均评分，以柱状图展示对比。

### 分析目标 2：品类消费与复购行为差异

筛选家居家装类（`moveis_decoracao` 等 6 个类别）和美妆个护类（`beleza_saude`、`perfumaria`）客户，分别计算平均订单金额和复购率（下单 ≥ 2 次的客户占比），以并排柱状图展示。

### 分析目标 3：2017 年季度运费成本趋势

计算 2017 年各季度订单的平均运费占商品价格比例，以柱状图展示 Q1-Q4 的趋势变化。

### 原始数据抽样

通过 4 表 JOIN（orders + order_items + products + order_reviews）展示前 50 条规范化后的数据样本。

**运行方式：**

```bash
streamlit run project1_app.py
```

### 结果展示

![image-20260413194247846](C:\Users\OMEN\AppData\Roaming\Typora\typora-user-images\image-20260413194247846.png)

![image-20260413194303562](C:\Users\OMEN\AppData\Roaming\Typora\typora-user-images\image-20260413194303562.png)

![image-20260413194314439](C:\Users\OMEN\AppData\Roaming\Typora\typora-user-images\image-20260413194314439.png)

![image-20260413194323528](C:\Users\OMEN\AppData\Roaming\Typora\typora-user-images\image-20260413194323528.png)
