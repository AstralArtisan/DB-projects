import os
import threading
import time
from datetime import datetime

import pandas as pd
import psycopg2
from psycopg2 import extensions
import streamlit as st

# ==============================================================================
# 模块 1：实验场景与数据库配置
# ==============================================================================
SCHEMA = os.getenv("DB_SCHEMA", "proj1_3nf")
INVENTORY_TABLE = "product_inventory"

SCENARIO_CONFIG = {
    "APP_TITLE": "Project3：Olist 商品库存并发控制实验",
    "ITEM_NAME": "商品库存",
    "UNIT": "件",
    "ACTION_NAME": "抢购",
}

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "ecommerce_db"),
    "user": os.getenv("DB_USER", "gaussdb"),
    "password": os.getenv("DB_PASSWORD", "MyGauss@123"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "15432"),
}


def append_log(log_list, log_lock, message):
    """线程安全地追加实验日志。"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    with log_lock:
        log_list.append(f"{timestamp} {message}")


def get_conn():
    """创建数据库连接，并进入 proj1 的 3NF schema。"""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_session(
        isolation_level=extensions.ISOLATION_LEVEL_READ_COMMITTED,
        autocommit=False,
    )
    with conn.cursor() as cur:
        cur.execute(f"SET search_path TO {SCHEMA}, public;")
    conn.commit()
    return conn


def ensure_inventory_table():
    """确保 Project3 使用的商品库存实验表存在。"""
    sql = f"""
        CREATE TABLE IF NOT EXISTS {INVENTORY_TABLE} (
            product_id VARCHAR(32) PRIMARY KEY,
            stock_count INTEGER NOT NULL CHECK (stock_count >= 0),
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_product_inventory_product
                FOREIGN KEY (product_id)
                REFERENCES products(product_id)
        );
    """
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        return True, "实验库存表已就绪"
    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"实验库存表初始化失败：{e}"
    finally:
        if conn:
            conn.close()


def load_product_options(limit=200):
    """读取可用于并发实验的商品列表。"""
    sql = f"""
        SELECT
            p.product_id,
            p.product_category_name,
            pi.stock_count
        FROM products p
        LEFT JOIN {INVENTORY_TABLE} pi
            ON p.product_id = pi.product_id
        ORDER BY
            CASE WHEN pi.product_id IS NULL THEN 1 ELSE 0 END,
            p.product_category_name,
            p.product_id
        LIMIT %s;
    """
    conn = None
    try:
        conn = get_conn()
        return pd.read_sql(sql, conn, params=(limit,))
    finally:
        if conn:
            conn.close()


def product_label(product_row):
    stock = product_row["stock_count"]
    stock_text = "未初始化" if pd.isna(stock) else f"{int(stock)} 件"
    category = product_row["product_category_name"] or "Unknown"
    return f"{product_row['product_id']} | {category} | 当前库存：{stock_text}"


def init_inventory(product_id, initial_count):
    """重置目标商品库存，确保每次实验可重复。"""
    insert_sql = f"""
        INSERT INTO {INVENTORY_TABLE} (product_id, stock_count)
        SELECT %s, %s
        WHERE EXISTS (
            SELECT 1 FROM products WHERE product_id = %s
        )
          AND NOT EXISTS (
            SELECT 1 FROM {INVENTORY_TABLE} WHERE product_id = %s
        );
    """
    update_sql = f"""
        UPDATE {INVENTORY_TABLE}
        SET stock_count = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE product_id = %s;
    """
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(insert_sql, (product_id, initial_count, product_id, product_id))
            cur.execute(update_sql, (initial_count, product_id))
            if cur.rowcount == 0:
                conn.rollback()
                return False, f"未找到商品 {product_id}，请先确认 proj1.products 已导入"
        conn.commit()
        return True, f"已将商品 {product_id} 库存重置为 {initial_count}"
    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"库存初始化失败：{e}"
    finally:
        if conn:
            conn.close()


def get_real_stock(product_id):
    """读取数据库中的实际库存值，作为一致性验证真值。"""
    sql = f"""
        SELECT stock_count
        FROM {INVENTORY_TABLE}
        WHERE product_id = %s;
    """
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, (product_id,))
            row = cur.fetchone()
            return row[0] if row else None
    except psycopg2.Error as e:
        st.error(f"读取库存失败：{e}")
        return None
    finally:
        if conn:
            conn.close()


# ==============================================================================
# 模块 2：并发事务处理逻辑
# ==============================================================================
def concurrency_worker(thread_name, product_id, delay_time, use_lock, log_list, log_lock):
    """
    模拟一个并发用户的抢购事务。

    无锁路径保留普通 SELECT + 应用层休眠 + 按旧值写回，用于复现丢失修改。
    加锁路径使用 SELECT ... FOR UPDATE，让目标商品库存行在事务内被排他锁保护。
    """
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            if use_lock:
                append_log(log_list, log_lock, f"[{thread_name}] 等待获取商品行排他锁")
                select_sql = f"""
                    SELECT stock_count
                    FROM {INVENTORY_TABLE}
                    WHERE product_id = %s
                    FOR UPDATE;
                """
            else:
                select_sql = f"""
                    SELECT stock_count
                    FROM {INVENTORY_TABLE}
                    WHERE product_id = %s;
                """

            cur.execute(select_sql, (product_id,))
            row = cur.fetchone()
            if not row:
                conn.rollback()
                append_log(log_list, log_lock, f"[{thread_name}] 目标商品库存记录不存在，事务回滚")
                return

            current_stock = row[0]
            mode_text = "加锁读取" if use_lock else "无锁读取"
            append_log(log_list, log_lock, f"[{thread_name}] {mode_text}库存={current_stock}")

            time.sleep(delay_time)

            if current_stock <= 0:
                conn.rollback()
                append_log(log_list, log_lock, f"[{thread_name}] 库存不足，事务回滚")
                return

            new_stock = current_stock - 1
            update_sql = f"""
                UPDATE {INVENTORY_TABLE}
                SET stock_count = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE product_id = %s;
            """
            cur.execute(update_sql, (new_stock, product_id))
            conn.commit()
            append_log(log_list, log_lock, f"[{thread_name}] {SCENARIO_CONFIG['ACTION_NAME']}成功，写回库存={new_stock}")
    except Exception as e:
        if conn:
            conn.rollback()
        append_log(log_list, log_lock, f"[{thread_name}] 数据库异常，事务回滚：{e}")
    finally:
        if conn:
            conn.close()


def run_experiment(product_id, product_category, initial_stock, thread_count, delay_time, use_lock):
    """编排一次并发实验：重置库存、启动线程、监控库存、输出结果。"""
    reset_ok, reset_msg = init_inventory(product_id, initial_stock)
    if not reset_ok:
        st.error(reset_msg)
        return

    st.info(reset_msg)
    logs = []
    log_lock = threading.Lock()
    threads = []

    stock_placeholder = st.empty()
    stock_placeholder.metric("数据库实际库存", f"{initial_stock} {SCENARIO_CONFIG['UNIT']}")

    for i in range(thread_count):
        thread = threading.Thread(
            target=concurrency_worker,
            args=(f"User-{i + 1}", product_id, delay_time, use_lock, logs, log_lock),
        )
        threads.append(thread)
        thread.start()

    with st.spinner(f"正在模拟 {thread_count} 个并发事务..."):
        while any(thread.is_alive() for thread in threads):
            current_stock = get_real_stock(product_id)
            if current_stock is not None:
                stock_placeholder.metric("数据库实际库存", f"{current_stock} {SCENARIO_CONFIG['UNIT']}")
            time.sleep(0.1)

    for thread in threads:
        thread.join()

    final_stock = get_real_stock(product_id)
    if final_stock is None:
        st.error("实验结束后未能读取最终库存")
        return

    expected_sold = min(initial_stock, thread_count)
    expected_stock = initial_stock - expected_sold
    actual_sold = initial_stock - final_stock

    stock_placeholder.metric("数据库实际库存", f"{final_stock} {SCENARIO_CONFIG['UNIT']}")

    c1, c2, c3 = st.columns(3)
    c1.metric("理论应售出", f"{expected_sold} {SCENARIO_CONFIG['UNIT']}")
    c2.metric("实际售出", f"{actual_sold} {SCENARIO_CONFIG['UNIT']}")
    c3.metric("预期剩余库存", f"{expected_stock} {SCENARIO_CONFIG['UNIT']}")

    st.text_area("事务执行日志", "\n".join(logs), height=320)

    if use_lock:
        if final_stock == expected_stock:
            st.success(
                f"加锁测试通过：{product_category} 商品库存从 {initial_stock} 正确扣减到 {final_stock}。"
            )
        else:
            st.error(
                f"加锁测试失败：预期库存 {expected_stock}，实际库存 {final_stock}。请检查事务边界和锁语句。"
            )
    else:
        if final_stock > expected_stock:
            st.error(
                f"观测到丢失修改：预期库存应为 {expected_stock}，实际库存为 {final_stock}，"
                f"说明部分线程基于旧库存写回并覆盖了其他事务结果。"
            )
        elif final_stock == expected_stock:
            st.warning(
                "本次无锁测试没有观测到丢失修改。可增大业务处理延迟或线程数后重试。"
            )
        else:
            st.warning(
                f"实际库存 {final_stock} 低于预期 {expected_stock}，请检查是否有其他会话同时修改了实验表。"
            )


# ==============================================================================
# 模块 3：Streamlit 实验控制台
# ==============================================================================
st.set_page_config(page_title="Project3 并发控制实验", layout="wide")
st.title(SCENARIO_CONFIG["APP_TITLE"])

table_ok, table_msg = ensure_inventory_table()
if not table_ok:
    st.error(table_msg)
    st.stop()

try:
    product_options = load_product_options()
except Exception as e:
    st.error(f"无法读取 proj1 商品数据：{e}")
    st.stop()

if product_options.empty:
    st.error("proj1_3nf.products 中没有可用商品。请先完成 proj1 的 3NF 数据导入。")
    st.stop()

st.sidebar.header("实验参数")
selected_index = st.sidebar.selectbox(
    "目标商品",
    product_options.index,
    format_func=lambda idx: product_label(product_options.loc[idx]),
)
selected_product = product_options.loc[selected_index]
selected_product_id = selected_product["product_id"]
selected_category = selected_product["product_category_name"] or "Unknown"

initial_stock = st.sidebar.number_input(
    "初始库存",
    min_value=1,
    max_value=10000,
    value=100,
    step=1,
)
thread_count = st.sidebar.slider("并发线程数", 2, 50, 10)
delay_time = st.sidebar.slider("业务处理延迟（秒）", 0.0, 1.0, 0.1, 0.05)

current_stock = get_real_stock(selected_product_id)

top_left, top_mid, top_right = st.columns(3)
top_left.metric("目标商品类别", selected_category)
top_mid.metric(
    "当前库存",
    "未初始化" if current_stock is None else f"{current_stock} {SCENARIO_CONFIG['UNIT']}",
)
top_right.metric("线程数 / 延迟", f"{thread_count} / {delay_time:.2f}s")

st.caption(f"目标商品 ID：`{selected_product_id}` | 实验表：`{SCHEMA}.{INVENTORY_TABLE}`")
st.divider()

left, right = st.columns(2)

with left:
    st.subheader("场景 A：无锁并发测试")
    st.caption("普通 SELECT 读取旧库存，休眠后按旧值写回，用于复现丢失修改。")
    if st.button("启动无锁测试", use_container_width=True):
        run_experiment(
            selected_product_id,
            selected_category,
            initial_stock,
            thread_count,
            delay_time,
            use_lock=False,
        )

with right:
    st.subheader("场景 B：排他锁并发测试")
    st.caption("使用 SELECT ... FOR UPDATE 锁定库存行，验证事务串行化后的正确结果。")
    if st.button("启动加锁测试", type="primary", use_container_width=True):
        run_experiment(
            selected_product_id,
            selected_category,
            initial_stock,
            thread_count,
            delay_time,
            use_lock=True,
        )
