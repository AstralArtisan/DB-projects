# 数据库课程项目仓库

本仓库集中管理数据库课程四次 project。当前采用一个 Git 仓库、按主题聚合的布局：

```text
projects/
  ecommerce/
    shared/
    proj1/
    proj3/
    proj4/
  simpledb/
    proj2/
```

## 项目关系

- `projects/ecommerce/proj1/`：Olist 电商数据捕获、清洗、建模、3NF 入库和基础分析看板。
- `projects/ecommerce/proj3/`：复用 `proj1` 产出的 `ecommerce_db.proj1_3nf`，完成事务管理与并发控制实验。
- `projects/ecommerce/proj4/`：复用 `proj1` 的电商数据库背景，完成完整性、安全性、视图和权限控制实验。
- `projects/simpledb/proj2/`：SimpleDB 查询执行与优化实验，和 Olist 电商线相互独立。

## 推荐运行顺序

1. 先完成 `projects/ecommerce/proj1/` 的数据清洗、建表和 3NF 迁移。
2. 用 `projects/ecommerce/shared/sql/00_check_proj1_ready.sql` 检查共享数据库是否就绪。
3. 再运行 `projects/ecommerce/proj3/` 或 `projects/ecommerce/proj4/`。
4. `projects/simpledb/proj2/` 可独立运行。

## 共享配置

电商线共用数据库配置约定见：

```text
projects/ecommerce/shared/config/db.env.example
```

各 Streamlit app 默认仍可直接运行；需要换数据库、端口或密码时，优先通过环境变量覆盖。
