# Proj1：数据的捕获与构建

## Step1：领域选择与目标定义

### 领域选择

**选定领域：** 电商交易

**领域说明：** 选取真实的电商平台交易数据。该领域数据维度丰富，包含时间戳、地理位置、价格、评分等多种数据类型。

**关键实体集：** 至少包含 4 个核心实体，符合复杂性要求：

1. **Customer（客户）**：包含客户ID、所在城市、州等。
2. **Product（商品）**：包含商品ID、类别、尺寸、重量等。
3. **Order（订单）**：包含订单ID、购买时间、物流状态、预计送达时间等。
4. **Seller（卖家）**：包含卖家ID、所在地等。

### 数据源调研

**数据来源：** Kaggle开源数据集 - Brazilian E-Commerce Public Dataset by Olist

**数据源链接：** `https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce`

**数据规模与维度：**

- **规模：** 包含超过 90,000 条真实的匿名交易记录。
- **维度：** 数据以多张 CSV 表格形式提供，天然需要进行外键关联。包含数值型（价格、运费、长宽高）、日期型（下单时间、发货时间、送达时间）以及文本型（商品类目、用户评价）。

数据源文件的关系如下：

![image-20260309205319226](C:\Users\OMEN\AppData\Roaming\Typora\typora-user-images\image-20260309205319226.png)

### 提出分析目标

1. 物流时效与客户满意度关联分析：分析 2017-2018 年已送达订单中，实际送达时间晚于预计送达时间的订单，其订单级平均评分是否比按时送达订单低 1 分以上？

   - 【动词】：分析
   - 【具体指标】：订单级平均评分
   - 【比较/条件】：实际送达时间晚于预计送达时间的订单，对比按时送达订单，评分差异是否超过 1 分
   - 【时间范围/细分领域】：2017-2018 年已送达电商订单

2. 品类消费与复购行为差异分析：对比 2017-2018 年购买过家居家装类商品的客户与购买过美妆个护类商品的客户，其平均订单总金额与复购率是否存在明显差异？

   - 【动词】：对比
   - 【具体指标】：平均订单总金额、复购率
   - 【比较/条件】：家居家装类客户对比美妆个护类客户
   - 【时间范围/细分领域】：2017-2018 年电商客户消费行为
   - 【补充】：在数据中，家居家装类包括 `moveis_decoracao`、`moveis_quarto`、`moveis_sala`、`cama_mesa_banho`、`utilidades_domesticas`、`eletrodomesticos`；美妆个护类包括 `beleza_saude`、`perfumaria`。复购率定义为统计期内下单数大于等于 2 的客户占比

3. 季度运费成本趋势分析：侦测 2017 年已送达订单中，第四季度订单的平均运费占订单商品总价比例是否比前三个季度更高。
   - 【动词】：侦测
   - 【具体指标】：平均运费占订单商品总价比例
   - 【比较/条件】：第四季度订单对比前三个季度订单
   - 【时间范围/细分领域】：2017 年已送达电商订单

## Step2：数据获取与初始入库

### 数据获取

**数据来源：** Kaggle 开源数据集 Brazilian E-Commerce Public Dataset by Olist。原始数据以 8 张 CSV 表格形式提供，本项目使用其中 5 张：

| 文件名 | 说明 | 主要字段 |
|--------|------|----------|
| `olist_customers_dataset.csv` | 客户表 | customer_id, customer_unique_id |
| `olist_orders_dataset.csv` | 订单表 | order_id, customer_id, 购买/送达/预计送达时间戳 |
| `olist_order_items_dataset.csv` | 订单明细表 | order_id, order_item_id, product_id, price, freight_value |
| `olist_products_dataset.csv` | 商品表 | product_id, product_category_name |
| `olist_order_reviews_dataset.csv` | 评价表 | review_id, order_id, review_score |

**数据规模：** 原始订单记录约 99,441 条，订单明细约 112,000 条，商品约 32,000 种，客户约 96,000 位。

### 数据清洗

清洗工作由 Python 脚本 `clean_flat_table.py` 完成，使用 pandas 库进行数据处理。脚本的核心流程如下：

**1. 数据合并流程**

脚本从 `archive/` 目录读取上述 5 个 CSV 文件，仅选取分析所需的列，然后通过 inner join 逐步合并：

```
customers ──(customer_id)──> orders ──(order_id)──> order_items ──(product_id)──> products
                                        │
                                        └──(order_id)──> reviews
```

合并后得到一张包含所有维度的大宽表，每行代表一个订单明细与评价的组合。

**2. 缺失值处理策略**

| 字段 | 处理方式 | 理由 |
|------|---------|------|
| `order_delivered_customer_date` | 丢弃该行（删除未送达订单） | 三个分析目标均依赖已送达订单的时间数据，未送达订单无法参与物流时效分析 |
| `product_category_name` | 填充为 `'Unknown'` | 保留交易记录完整性，避免因类别缺失而丢失价格、运费等有效数据 |
| `review_score` | 填充为 3（中位值） | 评分 1-5 分，3 为中间值，减少对均值的极端拉偏 |

**3. 脏数据处理**

三个时间戳字段（`order_purchase_timestamp`、`order_delivered_customer_date`、`order_estimated_delivery_date`）通过 `pd.to_datetime(errors='coerce')` 统一解析，输出时格式化为 `%Y-%m-%d %H:%M:%S`，确保时间格式一致。

**4. 清洗结果统计**

| 指标 | 数值 |
|------|------|
| 原始订单数 | 99,441 |
| 丢弃未送达订单数 | 2,965 |
| 清洗后订单数 | 96,476 |
| 商品类别原始缺失数 | 610 |
| 最终宽表行数 | 110,012 |
| 最终宽表列数 | 12 |

最终宽表 `cleaned_flat_table.csv` 包含以下 12 列：`order_id`、`order_item_id`、`customer_unique_id`、`order_purchase_timestamp`、`order_delivered_customer_date`、`order_estimated_delivery_date`、`product_id`、`product_category_name`、`price`、`freight_value`、`review_id`、`review_score`。

> 行数（110,012）大于订单明细数，原因是部分订单存在多条评价记录，合并后保留了每条评价与对应订单明细的组合。每行通过 `(order_id, order_item_id, review_id)` 唯一标识。

**5. 运行方式**

```bash
python clean_flat_table.py --input-dir archive --output cleaned_flat_table.csv
```

### 初始数据库实现

#### openGauss 部署

采用 Docker Desktop 部署 openGauss 官方镜像（`opengauss/opengauss:latest`），从 Docker Hub 直接拉取。容器启动命令如下：

```bash
docker run \
  --env=GS_PASSWORD=MyGauss@123 \
  --volume=E:\Docker\OpenGauss:/var/lib/opengauss \
  -p 15432:5432 \
  -d opengauss/opengauss:latest
```

关键配置说明：
- **端口映射**：宿主机 `15432` → 容器内 `5432`，外部通过 `localhost:15432` 连接。
- **数据持久化**：通过 `-v` 将宿主机 `E:\Docker\OpenGauss` 挂载到容器内 `/var/lib/opengauss`，数据库文件持久化存储。
- **数据库超级用户**：`omm`（openGauss 默认），通过 `GS_PASSWORD` 环境变量设置初始密码。

#### 初始表结构设计

本阶段采用非规范化的大宽表方案，将清洗后的所有数据存入单张表中，对应 DDL 脚本为 `schema.sql`：

```sql
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
```

**完整性约束设计说明：**

- **主键**：`id SERIAL`，自增整数代理主键，索引高效，适合过渡性宽表。
- **UNIQUE**：`(order_id, order_item_id, review_id)` 组合唯一约束，保证记录无重复。一个订单可包含多个商品项，一个订单可有多条评价，三者联合唯一标识每条记录。
- **NOT NULL**：所有列均设为 NOT NULL，因清洗脚本已处理所有缺失值。
- **DEFAULT**：`product_category_name` 默认 `'Unknown'`，`review_score` 默认 3，与清洗逻辑保持一致。
- **CHECK**：`price >= 0` 和 `freight_value >= 0`（金额不为负）；`order_item_id > 0`（项号从 1 开始）；`review_score BETWEEN 1 AND 5`（评分范围限制）。

#### 导入 Navicat 

![image-20260410000643389](C:\Users\OMEN\AppData\Roaming\Typora\typora-user-images\image-20260410000643389.png)

### 基础查询验证

连接 Navicat，执行以下 SQL 语句验证数据正确入库：

**查询 1：验证总行数**

```sql
SELECT COUNT(*) AS total_rows FROM cleaned_flat_table;
```

> <img src="C:\Users\OMEN\AppData\Roaming\Typora\typora-user-images\image-20260409234438145.png" alt="image-20260409234438145" style="zoom:67%;" />

**查询 2：验证主键唯一性**

```sql
SELECT order_id, order_item_id, review_id, COUNT(*)
FROM cleaned_flat_table
GROUP BY order_id, order_item_id, review_id
HAVING COUNT(*) > 1;
```

> <img src="C:\Users\OMEN\AppData\Roaming\Typora\typora-user-images\image-20260409235103790.png" alt="image-20260409235103790" style="zoom: 67%;" />

**查询 3：验证约束字段范围**

```sql
SELECT
    MIN(price)        AS min_price,
    MAX(price)        AS max_price,
    MIN(freight_value) AS min_freight,
    MAX(freight_value) AS max_freight,
    MIN(review_score)  AS min_score,
    MAX(review_score)  AS max_score
FROM cleaned_flat_table;
```

> <img src="C:\Users\OMEN\AppData\Roaming\Typora\typora-user-images\image-20260409235143876.png" alt="image-20260409235143876" style="zoom:67%;" />

**查询 4：抽样查看数据**

```sql
SELECT
    order_id,
    order_item_id,
    customer_unique_id,
    product_category_name,
    price,
    freight_value,
    review_score,
    order_purchase_timestamp
FROM cleaned_flat_table
ORDER BY order_purchase_timestamp DESC
LIMIT 10;
```

> ![image-20260409235256991](C:\Users\OMEN\AppData\Roaming\Typora\typora-user-images\image-20260409235256991.png)

## Step3：数据库规范化与数据可视化

### 函数依赖分析与规范化

#### 宽表结构回顾

阶段二的 `cleaned_flat_table` 包含 13 列（含代理主键 `id`），业务候选键为 `(order_id, order_item_id, review_id)`。以下分析基于该候选键。

#### 函数依赖集

| 编号 | 函数依赖 | 类型 |
|------|---------|------|
| FD1 | `order_id` → `customer_unique_id, order_purchase_timestamp, order_delivered_customer_date, order_estimated_delivery_date` | 部分依赖（候选键的真子集决定非主属性） |
| FD2 | `(order_id, order_item_id)` → `product_id, price, freight_value` | 部分依赖（候选键的真子集决定非主属性） |
| FD3 | `product_id` → `product_category_name` | 传递依赖（通过 order_items → product_id → product_category_name） |
| FD4 | `(review_id, order_id)` → `review_score` | 部分依赖（候选键的真子集决定非主属性） |

#### 冗余与异常分析

宽表存在以下问题：

1. **数据冗余**：
   - 同一客户的 `customer_unique_id` 在其所有订单明细行中重复出现
   - 同一订单的时间戳字段在该订单的每个明细×评价行中重复
   - 同一商品的 `product_category_name` 在每次出现时重复存储

2. **插入异常**：无法单独添加一个新客户或新商品，必须伴随完整的订单明细和评价记录

3. **删除异常**：删除某商品的最后一条订单明细，会导致该商品的类别信息丢失

4. **更新异常**：修改某商品的类别名称，需要更新所有包含该商品的行，部分更新会导致数据不一致

### 概念设计

#### E-R 图

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

### 逻辑结构设计与规范化

#### E-R 图转关系模式

将 E-R 图中的 5 个实体直接转换为 5 个关系模式：

- **customers**(<u>customer_unique_id</u>)
- **orders**(<u>order_id</u>, *customer_unique_id*, order_purchase_timestamp, order_delivered_customer_date, order_estimated_delivery_date)
- **products**(<u>product_id</u>, product_category_name)
- **order_items**(<u><i>order_id</i>, order_item_id</u>, *product_id*, price, freight_value)
- **order_reviews**(<u>review_id, <i>order_id</i></u>, review_score)

其中下划线标注主键，斜体为外键。

#### 3NF 分解过程

从宽表 R(<u>order_id, order_item_id, review_id</u>, customer_unique_id, order_purchase_timestamp, order_delivered_customer_date, order_estimated_delivery_date, product_id, product_category_name, price, freight_value, review_score) 出发：

**第一步：消除部分依赖（达到 2NF）**

- FD1：`order_id → customer_unique_id, 时间戳×3`，候选键的真子集决定非主属性 → 拆出 **orders** 表
- FD2：`(order_id, order_item_id) → product_id, price, freight_value`，候选键的真子集决定非主属性 → 拆出 **order_items** 表
- FD4：`(review_id, order_id) → review_score`，候选键的真子集决定非主属性 → 拆出 **order_reviews** 表

**第二步：消除传递依赖（达到 3NF）**

- FD3：在 order_items 中，`product_id → product_category_name` 构成传递依赖（order_items 的主键 → product_id → product_category_name） → 拆出 **products** 表
- 同时提取 **customers** 表作为 orders 外键的参照实体

**分解结果**：5 张表均满足 3NF，每个非主属性完全依赖于主键且不存在传递依赖。

#### 参照完整性

| 外键 | 所在表 | 参照表 |
|------|--------|--------|
| orders.customer_unique_id | orders | customers |
| order_items.order_id | order_items | orders |
| order_items.product_id | order_items | products |
| order_reviews.order_id | order_reviews | orders |

### 架构迁移

#### 3NF 建表脚本

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

#### 数据迁移

迁移脚本 `migrate_to_3nf.sql` 通过 `CREATE TEMP VIEW` 引用阶段二宽表，使用 `SELECT DISTINCT` 逐表提取数据：

| 目标表 | 迁移行数 | 说明 |
|--------|---------|------|
| customers | 92,753 | DISTINCT customer_unique_id |
| products | 32,070 | DISTINCT product_id + category |
| orders | 95,830 | DISTINCT order_id + 时间戳 |
| order_items | 109,369 | DISTINCT (order_id, order_item_id) + price/freight |
| order_reviews | 96,359 | DISTINCT (review_id, order_id) + score |

#### 迁移验证

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

 expected_customers | actual_customers | expected_orders | actual_orders | expected_products | actual_products | expecte
d_order_items | actual_order_items | expected_reviews | actual_reviews
--------------------+------------------+-----------------+---------------+-------------------+-----------------+--------
--------------+--------------------+------------------+----------------
              92753 |            92753 |           95830 |         95830 |             32070 |           32070 |
       109369 |             109369 |            96359 |          96359
(1 row)
```



### 数据可视化

使用 Streamlit 框架构建数据分析看板（`project1_app.py`），通过 psycopg2 连接 openGauss 数据库，实时从 3NF 表中查询数据。

#### 核心指标概览

使用 `st.metric` 组件展示三个核心指标：

| 指标 | SQL | 数据来源 |
|------|-----|---------|
| 总订单数 | `COUNT(*) FROM orders` | orders 表 |
| 总客户数 | `COUNT(*) FROM customers` | customers 表 |
| 平均评分 | `AVG(review_score) FROM order_reviews` | order_reviews 表 |

#### 分析目标 1：物流时效与客户满意度

将订单按实际送达时间是否晚于预计送达时间分为"逾期送达"和"准时送达"两组，计算各组的平均评分，以柱状图展示对比。

#### 分析目标 2：品类消费与复购行为差异

筛选家居家装类（`moveis_decoracao` 等 6 个类别）和美妆个护类（`beleza_saude`、`perfumaria`）客户，分别计算平均订单金额和复购率（下单 ≥ 2 次的客户占比），以并排柱状图展示。

#### 分析目标 3：2017 年季度运费成本趋势

计算 2017 年各季度订单的平均运费占商品价格比例，以柱状图展示 Q1-Q4 的趋势变化。

#### 原始数据抽样

通过 4 表 JOIN（orders + order_items + products + order_reviews）展示前 50 条规范化后的数据样本。

**运行方式：**

```bash
streamlit run project1_app.py
```

#### 结果展示

![image-20260413194247846](C:\Users\OMEN\AppData\Roaming\Typora\typora-user-images\image-20260413194247846.png)

![image-20260413194303562](C:\Users\OMEN\AppData\Roaming\Typora\typora-user-images\image-20260413194303562.png)

![image-20260413194314439](C:\Users\OMEN\AppData\Roaming\Typora\typora-user-images\image-20260413194314439.png)

![image-20260413194323528](C:\Users\OMEN\AppData\Roaming\Typora\typora-user-images\image-20260413194323528.png)



