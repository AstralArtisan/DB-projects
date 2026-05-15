import os

import pandas as pd
import psycopg2
from psycopg2 import sql as pg_sql
import streamlit as st


# ==============================================================================
# 模块 1：数据库连接配置与角色定义
# ==============================================================================
ADMIN_ROLE = "管理员 (Admin)"
ANALYST_ROLE = "分析师 (Analyst)"

SCHEMA = os.getenv("DB_SCHEMA", "proj1_3nf")
BASE_TABLE = "order_items"
PUBLIC_VIEW = "v_public_order_items"
SENSITIVE_COL = "freight_value"

ADMIN_CONFIG = {
    "dbname": os.getenv("DB_NAME", "ecommerce_db"),
    "user": os.getenv("DB_USER", "gaussdb"),
    "password": os.getenv("DB_PASSWORD", "MyGauss@123"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "15432"),
}

ANALYST_CONFIG = {
    "dbname": os.getenv("DB_NAME", "ecommerce_db"),
    "user": os.getenv("ANALYST_DB_USER", "analyst_user"),
    "password": os.getenv("ANALYST_DB_PASSWORD", "Analyst@123"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "15432"),
}

ADMIN_QUERY = """
    SELECT
        oi.order_id,
        oi.order_item_id,
        oi.product_id,
        p.product_category_name,
        oi.price,
        oi.freight_value
    FROM order_items oi
    JOIN products p
        ON oi.product_id = p.product_id
    ORDER BY oi.order_id DESC, oi.order_item_id DESC
    LIMIT 200;
"""

ANALYST_QUERY = """
    SELECT *
    FROM v_public_order_items
    ORDER BY order_id DESC, order_item_id DESC
    LIMIT 200;
"""


# ==============================================================================
# 模块 2：数据库访问工具
# ==============================================================================
def get_connection(role_name):
    """根据当前会话身份建立数据库连接，并进入 Project1 的 3NF schema。"""
    config = ADMIN_CONFIG if role_name == ADMIN_ROLE else ANALYST_CONFIG
    conn = psycopg2.connect(**config)
    with conn.cursor() as cur:
        cur.execute(
            pg_sql.SQL("SET search_path TO {}, public;").format(
                pg_sql.Identifier(SCHEMA)
            )
        )
    return conn


def format_database_error(error):
    """优先展示数据库内核返回的原始错误文本。"""
    return getattr(error, "pgerror", None) or str(error)


def run_dataframe_query(role_name, query):
    conn = None
    try:
        conn = get_connection(role_name)
        return pd.read_sql(query, conn)
    finally:
        if conn:
            conn.close()


def load_insert_defaults():
    """
    为录入表单读取一组满足外键约束的默认订单与商品。
    新的 order_item_id 取该订单已有最大序号 + 1，避免默认值撞主键。
    """
    sql = """
        SELECT
            oi.order_id,
            COALESCE(MAX(same_order.order_item_id), 0) + 1 AS next_order_item_id,
            oi.product_id,
            p.product_category_name
        FROM order_items oi
        JOIN order_items same_order
            ON same_order.order_id = oi.order_id
        JOIN products p
            ON p.product_id = oi.product_id
        GROUP BY
            oi.order_id,
            oi.product_id,
            p.product_category_name
        ORDER BY oi.order_id, oi.product_id
        LIMIT 1;
    """
    conn = None
    try:
        conn = get_connection(ADMIN_ROLE)
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchone()
    finally:
        if conn:
            conn.close()


# ==============================================================================
# 模块 3：安全与完整性实验控制台
# ==============================================================================
st.set_page_config(page_title="Project4：安全与完整性", layout="wide")
st.title("Project4：Olist 数据库安全性与完整性控制实验")

st.sidebar.header("身份验证模拟")
role = st.sidebar.radio("请选择登录角色:", [ADMIN_ROLE, ANALYST_ROLE])
st.info(f"当前会话身份：**{role}**")

st.caption(
    "业务红线：订单项运费 `freight_value` 不能高于商品售价 `price`；"
    "敏感字段：`freight_value` 只允许管理员查看。"
)

# ========================================================
# 模块 A: 自主存取控制 (Security & DAC)
# ========================================================
st.subheader("1. 数据安全性与视图机制测试")

col1, col2 = st.columns([3, 1])
with col1:
    if st.button("执行查询请求", use_container_width=True):
        try:
            if role == ADMIN_ROLE:
                query = ADMIN_QUERY
                st.caption(f"执行 SQL: SELECT ... FROM {BASE_TABLE} (物理基表)")
            else:
                query = ANALYST_QUERY
                st.caption(f"执行 SQL: SELECT * FROM {PUBLIC_VIEW} (脱敏视图)")

            df = run_dataframe_query(role, query)
            st.dataframe(df, use_container_width=True)

            if SENSITIVE_COL in df.columns:
                st.warning(f"当前权限可见敏感属性 [{SENSITIVE_COL}]")
            else:
                st.success(f"安全验证通过：敏感属性 [{SENSITIVE_COL}] 已被视图机制屏蔽")
        except Exception as e:
            st.error(f"查询异常:\n{format_database_error(e)}")

if role == ANALYST_ROLE:
    with col2:
        st.write("")
        st.write("")
        if st.button("越权访问测试: 强行查询基表", use_container_width=True):
            conn = None
            try:
                conn = get_connection(role)
                pd.read_sql(f"SELECT * FROM {BASE_TABLE} LIMIT 1;", conn)
                st.warning("异常：分析师直接查询基表成功，请检查权限脚本是否已执行。")
            except Exception as e:
                st.error(
                    "访问控制生效！数据库内核拒绝了该请求:\n"
                    f"{format_database_error(e)}"
                )
            finally:
                if conn:
                    conn.close()

st.divider()

# ========================================================
# 模块 B: 语义完整性约束 (Semantic Integrity)
# ========================================================
st.subheader("2. 业务规则完整性与触发器测试")

if role == ANALYST_ROLE:
    st.warning("权限限制：当前角色不具备数据录入 (INSERT) 权限")
else:
    st.write("管理员录入订单项时，Python 不做业务拦截，违规数据由数据库触发器中断。")

    try:
        defaults = load_insert_defaults()
    except Exception as e:
        st.error(f"无法读取默认订单项，请先确认 Project1 数据已导入:\n{format_database_error(e)}")
        defaults = None

    if not defaults:
        st.error("order_items 中没有可用数据，无法构造满足外键约束的录入样本。")
    else:
        default_order_id, default_item_id, default_product_id, default_category = defaults

        with st.form("data_entry_form"):
            c1, c2 = st.columns(2)
            order_id = c1.text_input("订单 ID (order_id)", default_order_id)
            product_id = c2.text_input("商品 ID (product_id)", default_product_id)

            c3, c4, c5 = st.columns(3)
            order_item_id = c3.number_input(
                "订单项序号 (order_item_id)",
                min_value=1,
                value=int(default_item_id),
                step=1,
            )
            price = c4.number_input("商品售价 price", min_value=0.0, value=100.0, step=1.0)
            freight_value = c5.number_input(
                "运费 freight_value",
                min_value=0.0,
                value=150.0,
                step=1.0,
            )

            st.caption(f"默认商品类别：{default_category}")
            submitted = st.form_submit_button("执行插入事务 (INSERT)")

        if submitted:
            conn = None
            try:
                conn = get_connection(role)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO order_items (
                            order_id,
                            order_item_id,
                            product_id,
                            price,
                            freight_value
                        )
                        VALUES (%s, %s, %s, %s, %s);
                        """,
                        (
                            order_id,
                            int(order_item_id),
                            product_id,
                            price,
                            freight_value,
                        ),
                    )
                conn.commit()
                st.success("事务提交成功：数据符合完整性约束。")
            except psycopg2.DatabaseError as e:
                if conn:
                    conn.rollback()
                st.error(
                    "事务被中断 (触发器或约束拦截):\n"
                    f"{format_database_error(e)}"
                )
            finally:
                if conn:
                    conn.close()
