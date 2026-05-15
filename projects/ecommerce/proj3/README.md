# Project3：事务管理与并发控制

本项目复用 Project1 的 Olist 电商数据库成果，在 `proj1_3nf.products` 基础上新增实验库存表，模拟多个用户并发抢购同一商品。

## 前置条件

先完成：

```text
../proj1/schema3.sql
../proj1/migrate_to_3nf.sql
```

再用共享检查脚本确认基础表可用：

```text
../shared/sql/00_check_proj1_ready.sql
```

共享数据库配置示例见：

```text
../shared/config/db.env.example
```

## 运行

```powershell
pip install -r requirements.txt
streamlit run project3_app.py
```

更多截图与报告说明见 `REPORT_NOTES.md`。
