# Project4：数据库安全与完整性

本项目属于 Olist 电商数据库专题，后续应基于 Project1 产出的 `ecommerce_db.proj1_3nf` 完成触发器、视图和权限控制实验。

## 前置条件

运行 Project4 前，先完成 Project1 的 3NF 数据导入，并用共享检查脚本确认：

```text
../shared/sql/00_check_proj1_ready.sql
```

共享数据库配置示例见：

```text
../shared/config/db.env.example
```

## 当前状态

- `Guide.md`：课程要求。
- `demo_p4_security.sql`：触发器与权限配置参考脚本，目前仍是模板，需要按 Olist 电商业务改造。
- `project4_app.py`：Streamlit 权限与完整性实验模板，数据库连接已改为共享环境变量约定。
