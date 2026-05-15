# Project4 报告要点

## 业务规则与敏感字段

- 业务规则：订单项的运费 `freight_value` 不能高于商品售价 `price`。当插入或更新 `order_items` 时，如果 `freight_value > price`，触发器 `trg_check_order_item_freight` 会在数据库层中断事务。
- 敏感字段：`freight_value`。该字段代表订单项层面的物流费用信息，管理员可见，分析师只能通过脱敏视图查看不含该字段的数据。

## 核心 SQL

- 触发器函数：`check_order_item_freight()`
- 触发器：`trg_check_order_item_freight`
- 脱敏视图：`v_public_order_items`
- 受限用户：`analyst_user`

完整脚本见 `demo_p4_security.sql`。

## 截图清单

1. 管理员角色点击“执行查询请求”，表格中应包含 `freight_value`。
2. 分析师角色点击“执行查询请求”，表格来自 `v_public_order_items`，不包含 `freight_value`。
3. 分析师角色点击“越权访问测试: 强行查询基表”，界面显示数据库权限拒绝错误。
4. 管理员角色保持默认表单值，`price = 100`、`freight_value = 150`，点击插入后界面显示触发器抛出的数据库错误。
5. 管理员角色将 `freight_value` 改为不高于 `price`，点击插入后事务提交成功。

## Python 核心代码说明

`project4_app.py` 使用两套连接配置模拟角色登录：

- 管理员使用 `DB_USER` / `DB_PASSWORD`，直接查询 `order_items`。
- 分析师使用 `ANALYST_DB_USER` / `ANALYST_DB_PASSWORD`，只查询 `v_public_order_items`。
- 录入表单不在 Python 层判断 `freight_value > price`，而是直接执行 `INSERT`，通过捕获 `psycopg2.DatabaseError` 展示数据库内核返回的触发器错误。
