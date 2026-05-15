# Project1：Olist 电商数据基础

本项目负责 Olist 电商数据的捕获、清洗、宽表入库、3NF 规范化建模和基础分析看板，是 `projects/ecommerce/` 专题的数据库基础。

## 共享关系

Project3 和 Project4 不直接读取本目录中的 CSV，而是复用本项目导入 openGauss 后形成的数据库成果：

```text
database: ecommerce_db
schema:   proj1_3nf
```

共享配置示例见：

```text
../shared/config/db.env.example
```

数据库就绪检查脚本见：

```text
../shared/sql/00_check_proj1_ready.sql
```

## 关键文件

- `archive/`：Olist 原始 CSV 数据。
- `clean_flat_table.py`：清洗并合并原始数据。
- `cleaned_flat_table.csv`：清洗后的宽表数据。
- `schema.sql`：初始宽表结构。
- `schema3.sql`：3NF 表结构。
- `migrate_to_3nf.sql`：从宽表迁移到 3NF schema。
- `project1_app.py`：Olist 数据分析 Streamlit 看板。
