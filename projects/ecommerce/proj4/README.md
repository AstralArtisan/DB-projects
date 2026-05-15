# Project4：数据库安全与完整性

本项目属于 Olist 电商数据库专题，基于 Project1 产出的 `ecommerce_db.proj1_3nf` 完成触发器、视图和权限控制实验。

## 实验设计

- 完整性红线：在 `order_items` 上禁止录入或更新 `freight_value > price` 的订单项，防止出现“运费高于商品售价”的异常订单明细。
- 敏感字段：`freight_value` 视为物流成本/费用敏感信息，管理员可直接查看，普通分析师只能通过脱敏视图访问。
- 脱敏视图：`v_public_order_items` 保留 `order_id`、`order_item_id`、`product_id`、`product_category_name`、`price`，不暴露 `freight_value`。
- 受限用户：`analyst_user` 只能查询 `v_public_order_items`，直接查询 `order_items` 应被数据库权限机制拒绝。

## 前置条件

运行 Project4 前，先完成 Project1 的 3NF 数据导入，并用共享检查脚本确认：

```text
../shared/sql/00_check_proj1_ready.sql
```

共享数据库配置示例见：

```text
../shared/config/db.env.example
```

## 运行

1. 执行 Project4 初始化 SQL，创建触发器、脱敏视图和分析师用户：

```powershell
gsql -d ecommerce_db -U gaussdb -p 15432 -f demo_p4_security.sql
```

如使用 PostgreSQL 客户端，也可按本机环境改用 `psql` 执行同一脚本。

2. 安装依赖并启动 Streamlit：

```powershell
pip install -r requirements.txt
streamlit run project4_app.py
```

3. 在侧边栏切换“管理员 (Admin)”和“分析师 (Analyst)”角色，分别验证基表查询、视图脱敏和越权访问拦截。

## 提交材料提示

更多报告截图与代码说明见 `REPORT_NOTES.md`。
