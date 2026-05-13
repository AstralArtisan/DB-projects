# Proj1：数据的捕获与构建

## Step2：数据获取与初始入库

### 数据获取

**数据来源：** Kaggle 开源数据集 Brazilian E-Commerce Public Dataset by Olist。原始数据以 8 张 CSV 表格形式提供，本项目使用其中 5 张：

| 文件名                            | 说明       | 主要字段                                                  |
| --------------------------------- | ---------- | --------------------------------------------------------- |
| `olist_customers_dataset.csv`     | 客户表     | customer_id, customer_unique_id                           |
| `olist_orders_dataset.csv`        | 订单表     | order_id, customer_id, 购买/送达/预计送达时间戳           |
| `olist_order_items_dataset.csv`   | 订单明细表 | order_id, order_item_id, product_id, price, freight_value |
| `olist_products_dataset.csv`      | 商品表     | product_id, product_category_name                         |
| `olist_order_reviews_dataset.csv` | 评价表     | review_id, order_id, review_score                         |

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

| 字段                            | 处理方式                   | 理由                                                         |
| ------------------------------- | -------------------------- | ------------------------------------------------------------ |
| `order_delivered_customer_date` | 丢弃该行（删除未送达订单） | 三个分析目标均依赖已送达订单的时间数据，未送达订单无法参与物流时效分析 |
| `product_category_name`         | 填充为 `'Unknown'`         | 保留交易记录完整性，避免因类别缺失而丢失价格、运费等有效数据 |
| `review_score`                  | 填充为 3（中位值）         | 评分 1-5 分，3 为中间值，减少对均值的极端拉偏                |

**3. 脏数据处理**

三个时间戳字段（`order_purchase_timestamp`、`order_delivered_customer_date`、`order_estimated_delivery_date`）通过 `pd.to_datetime(errors='coerce')` 统一解析，输出时格式化为 `%Y-%m-%d %H:%M:%S`，确保时间格式一致。

**4. 清洗结果统计**

| 指标               | 数值    |
| ------------------ | ------- |
| 原始订单数         | 99,441  |
| 丢弃未送达订单数   | 2,965   |
| 清洗后订单数       | 96,476  |
| 商品类别原始缺失数 | 610     |
| 最终宽表行数       | 110,012 |
| 最终宽表列数       | 12      |

最终宽表 `cleaned_flat_table.csv` 包含以下 13 列：`id`、`order_id`、`order_item_id`、`customer_unique_id`、`order_purchase_timestamp`、`order_delivered_customer_date`、`order_estimated_delivery_date`、`product_id`、`product_category_name`、`price`、`freight_value`、`review_id`、`review_score`。

> 行数（110,012）大于订单明细数，原因是部分订单存在多条评价记录，合并后保留了每条评价与对应订单明细的组合。每行通过 `(order_id, order_item_id, review_id)` 唯一标识。

**5. 运行方式**

```bash
python clean_flat_table.py --input-dir archive --output cleaned_flat_table.csv
```

### 初始数据库实现

#### openGauss 部署

采用 Docker Desktop 部署 openGauss 官方镜像。容器启动命令如下：

```bash
docker run \
  --env=GS_PASSWORD=MyGauss@123 \
  --volume=E:\Docker\OpenGauss:/var/lib/opengauss \
  -p 15432:5432 \
  -d opengauss/opengauss:latest
```

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

![image-20260410000633958](C:\Users\OMEN\AppData\Roaming\Typora\typora-user-images\image-20260410000633958.png)

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



