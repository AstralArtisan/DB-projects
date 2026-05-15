# Project3 运行与报告素材说明

## 实验背景

Project3 延续 Project1 的 Olist 电商数据集和 `proj1_3nf` 三范式结构。由于 Project1 的原始表没有库存字段，本实验新增 `product_inventory` 表，把 `products.product_id` 作为外键，并用 `stock_count` 表示某个商品的限量库存。

并发场景定义为：多个用户同时抢购同一个商品。无锁模式下，多个线程可能读取到同一个旧库存，并把各自计算出的新库存写回，导致“丢失修改”。加锁模式下，`SELECT ... FOR UPDATE` 对目标商品库存行加排他锁，线程必须依次完成读改写，最终库存应准确扣减。

## 运行步骤

1. 确认 Project1 数据库已准备好：

```sql
SET search_path TO proj1_3nf, public;
SELECT COUNT(*) FROM products;
```

也可以执行共享检查脚本：

```text
../shared/sql/00_check_proj1_ready.sql
```

如果连接 `localhost:15432` 被拒绝，先启动 Project1 使用的 openGauss 容器，并确认宿主机端口 `15432` 已映射到容器内 `5432`。

2. 在 openGauss / Navicat / psql 中执行：

```sql
\i project3_setup.sql
```

如果使用 Navicat，可以直接打开 `project3_setup.sql` 后执行全文。

3. 安装依赖并启动 Streamlit：

```powershell
pip install -r requirements.txt
streamlit run project3_app.py
```

数据库配置遵循共享环境变量约定，示例见：

```text
../shared/config/db.env.example
```

4. 推荐实验参数：

- 初始库存：100
- 并发线程数：10
- 业务处理延迟：0.10 秒

## 截图清单

报告中建议保留以下截图：

- 实验场景配置：目标商品、初始库存、线程数、延迟。
- 无锁并发测试结果：实际售出数量小于理论应售出数量，并出现“丢失修改”提示。
- 无锁事务日志：多个线程读取到相同旧库存，再写回相同或相近库存。
- 加锁并发测试结果：最终库存等于 `初始库存 - min(初始库存, 线程数)`。
- 加锁事务日志：线程依次获得锁、读取最新库存并写回。

## 报告撰写要点

- 场景描述：基于 Olist 商品表，为商品新增实验库存，模拟多人抢购。
- 问题复现：解释普通 `SELECT` 不会锁定库存行，线程休眠扩大了竞态窗口，旧值写回覆盖了其他事务结果。
- 修正方案：说明 `SELECT ... FOR UPDATE` 在事务内对目标元组加排他锁，后续线程等待前序事务提交后才能读取最新库存。
- 结果分析：对比无锁模式和加锁模式的库存扣减结果，说明悲观锁如何保证一致性。
