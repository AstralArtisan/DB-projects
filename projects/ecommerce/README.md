# Olist 电商数据库专题

本目录聚合依赖同一套 Olist 电商数据库背景的 project。

## 目录

- `proj1/`：基础项目，负责原始数据、清洗脚本、schema、3NF 迁移、报告和基础看板。
- `proj3/`：事务管理与并发控制，基于 `proj1_3nf.products` 新增实验库存表。
- `proj4/`：数据库安全与完整性，后续应基于 `proj1_3nf` 完成触发器、视图和权限实验。
- `shared/`：共享配置示例、数据库就绪检查 SQL 和跨 project 说明。

## 依赖关系

`proj3` 和 `proj4` 不直接复用 `proj1/archive/*.csv` 或 `cleaned_flat_table.csv`，而是复用 `proj1` 已经导入 openGauss 的数据库成果：

```text
database: ecommerce_db
schema:   proj1_3nf
```

因此运行 `proj3` / `proj4` 前，必须先完成 `proj1` 的 `schema3.sql` 和 `migrate_to_3nf.sql`。
