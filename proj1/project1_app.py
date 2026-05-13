import pandas as pd
import psycopg2
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ==============================================================================
# 数据库连接
# ==============================================================================
DB_CONFIG = {
    "dbname": "ecommerce_db",
    "user": "gaussdb",
    "password": "MyGauss@123",
    "host": "localhost",
    "port": "15432",
}
SCHEMA = "proj1_3nf"


def get_data(sql):
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(f"SET search_path TO {SCHEMA}, public;")
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        st.error(f"SQL 执行错误: {e}")
        return None
    finally:
        if conn:
            conn.close()


# ==============================================================================
# 页面配置
# ==============================================================================
st.set_page_config(page_title="Olist 电商数据分析看板", layout="wide")
st.title("Olist Brazilian E-Commerce 数据分析看板")

# ==============================================================================
# 核心指标
# ==============================================================================
st.header("核心指标概览")

sql_metrics = """
    SELECT
        (SELECT COUNT(*) FROM orders) AS total_orders,
        (SELECT COUNT(*) FROM customers) AS total_customers,
        (SELECT ROUND(AVG(review_score)::NUMERIC, 2) FROM order_reviews) AS avg_score
"""
df_metrics = get_data(sql_metrics)
if df_metrics is not None:
    c1, c2, c3 = st.columns(3)
    c1.metric("总订单数", f"{df_metrics.iloc[0, 0]:,}")
    c2.metric("总客户数", f"{df_metrics.iloc[0, 1]:,}")
    c3.metric("平均评分", f"{df_metrics.iloc[0, 2]:.2f}")

st.divider()

# ==============================================================================
# 分析目标 1：物流时效与客户满意度
# ==============================================================================
st.header("分析目标 1：物流时效与客户满意度")
st.caption("2017-2018 年已送达订单：逾期送达 vs 准时送达的平均评分对比")

sql_goal1 = """
    SELECT
        CASE
            WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
            THEN '逾期送达'
            ELSE '准时送达'
        END AS delivery_status,
        ROUND(AVG(r.review_score)::NUMERIC, 2) AS avg_score,
        COUNT(DISTINCT o.order_id) AS order_count
    FROM orders o
    JOIN order_reviews r ON o.order_id = r.order_id
    WHERE EXTRACT(YEAR FROM o.order_purchase_timestamp) BETWEEN 2017 AND 2018
    GROUP BY delivery_status
"""

df_g1 = get_data(sql_goal1)
if df_g1 is not None:
    colors = ["#e74c3c" if s == "逾期送达" else "#2ecc71" for s in df_g1["delivery_status"]]
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        x=df_g1["delivery_status"],
        y=df_g1["avg_score"],
        marker_color=colors,
        text=df_g1["avg_score"].apply(lambda v: f"{v:.2f}"),
        textposition="outside",
        textfont=dict(size=16, color="#333"),
        hovertemplate="<b>%{x}</b><br>平均评分: %{y:.2f}<br>订单数: %{customdata:,}<extra></extra>",
        customdata=df_g1["order_count"],
    ))
    fig1.update_layout(
        yaxis=dict(title="平均评分", range=[0, 5.5], dtick=1),
        xaxis=dict(title=""),
        height=420,
        margin=dict(t=30, b=40),
    )
    col_chart, col_insight = st.columns([3, 2])
    with col_chart:
        st.plotly_chart(fig1, use_container_width=True)
    with col_insight:
        late = df_g1[df_g1["delivery_status"] == "逾期送达"]
        ontime = df_g1[df_g1["delivery_status"] == "准时送达"]
        if not late.empty and not ontime.empty:
            diff = ontime.iloc[0]["avg_score"] - late.iloc[0]["avg_score"]
            st.metric("评分差值", f"{diff:.2f} 分")
            st.write(f"- 准时送达订单 **{int(ontime.iloc[0]['order_count']):,}** 单，平均评分 **{ontime.iloc[0]['avg_score']:.2f}**")
            st.write(f"- 逾期送达订单 **{int(late.iloc[0]['order_count']):,}** 单，平均评分 **{late.iloc[0]['avg_score']:.2f}**")
            if diff > 1:
                st.success(f"逾期订单评分低 {diff:.2f} 分，超过 1 分阈值，物流时效显著影响满意度。")
            else:
                st.info(f"逾期订单评分低 {diff:.2f} 分，未超过 1 分阈值。")

st.divider()
# ==============================================================================
# 分析目标 2：品类消费与复购行为差异
# ==============================================================================
st.header("分析目标 2：品类消费与复购行为差异")
st.caption("2017-2018 年家居家装类 vs 美妆个护类客户的平均订单金额与复购率")

sql_goal2 = """
    WITH category_customers AS (
        SELECT
            CASE
                WHEN p.product_category_name IN (
                    'moveis_decoracao','moveis_quarto','moveis_sala',
                    'cama_mesa_banho','utilidades_domesticas','eletrodomesticos'
                ) THEN '家居家装'
                WHEN p.product_category_name IN (
                    'beleza_saude','perfumaria'
                ) THEN '美妆个护'
            END AS category_group,
            o.customer_unique_id,
            COUNT(DISTINCT o.order_id) AS order_count,
            SUM(oi.price + oi.freight_value) AS total_amount
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE EXTRACT(YEAR FROM o.order_purchase_timestamp) BETWEEN 2017 AND 2018
          AND p.product_category_name IN (
              'moveis_decoracao','moveis_quarto','moveis_sala',
              'cama_mesa_banho','utilidades_domesticas','eletrodomesticos',
              'beleza_saude','perfumaria'
          )
        GROUP BY category_group, o.customer_unique_id
    )
    SELECT
        category_group,
        ROUND(AVG(total_amount)::NUMERIC, 2) AS avg_amount,
        ROUND(100.0 * SUM(CASE WHEN order_count >= 2 THEN 1 ELSE 0 END) / COUNT(*)::NUMERIC, 2) AS repurchase_rate,
        COUNT(*) AS customer_count
    FROM category_customers
    GROUP BY category_group
"""

df_g2 = get_data(sql_goal2)
if df_g2 is not None:
    col_a, col_b = st.columns(2)
    with col_a:
        fig2a = go.Figure()
        fig2a.add_trace(go.Bar(
            x=df_g2["category_group"],
            y=df_g2["avg_amount"],
            marker_color=["#3498db", "#e67e22"],
            text=df_g2["avg_amount"].apply(lambda v: f"R${v:,.0f}"),
            textposition="outside",
            textfont=dict(size=14),
        ))
        fig2a.update_layout(
            title=dict(text="平均订单金额 (R$)", font=dict(size=15)),
            yaxis=dict(title="金额 (R$)"),
            height=400, margin=dict(t=50, b=40),
        )
        st.plotly_chart(fig2a, use_container_width=True)
    with col_b:
        fig2b = go.Figure()
        fig2b.add_trace(go.Bar(
            x=df_g2["category_group"],
            y=df_g2["repurchase_rate"],
            marker_color=["#3498db", "#e67e22"],
            text=df_g2["repurchase_rate"].apply(lambda v: f"{v:.1f}%"),
            textposition="outside",
            textfont=dict(size=14),
        ))
        fig2b.update_layout(
            title=dict(text="复购率 (%)", font=dict(size=15)),
            yaxis=dict(title="复购率 (%)", range=[0, max(df_g2["repurchase_rate"]) * 1.4]),
            height=400, margin=dict(t=50, b=40),
        )
        st.plotly_chart(fig2b, use_container_width=True)

    st.write(f"- 家居家装类客户 **{int(df_g2[df_g2['category_group']=='家居家装']['customer_count'].values[0]):,}** 人，"
             f"美妆个护类客户 **{int(df_g2[df_g2['category_group']=='美妆个护']['customer_count'].values[0]):,}** 人")

st.divider()
# ==============================================================================
# 分析目标 3：2017 年季度运费成本趋势
# ==============================================================================
st.header("分析目标 3：2017 年季度运费成本趋势")
st.caption("2017 年各季度订单的平均运费占商品价格比例，检验 Q4 是否显著高于前三季度")

sql_goal3 = """
    SELECT
        EXTRACT(QUARTER FROM o.order_purchase_timestamp)::INTEGER AS quarter,
        ROUND(AVG(oi.freight_value / NULLIF(oi.price, 0))::NUMERIC * 100, 2) AS freight_ratio,
        COUNT(*) AS item_count
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE EXTRACT(YEAR FROM o.order_purchase_timestamp) = 2017
      AND oi.price > 0
    GROUP BY quarter
    ORDER BY quarter
"""

df_g3 = get_data(sql_goal3)
if df_g3 is not None:
    df_g3["quarter_label"] = df_g3["quarter"].apply(lambda q: f"Q{q}")
    q4_val = df_g3[df_g3["quarter"] == 4]["freight_ratio"].values
    q123_avg = df_g3[df_g3["quarter"] < 4]["freight_ratio"].mean()
    colors3 = ["#f39c12" if q == 4 else "#95a5a6" for q in df_g3["quarter"]]

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=df_g3["quarter_label"],
        y=df_g3["freight_ratio"],
        marker_color=colors3,
        text=df_g3["freight_ratio"].apply(lambda v: f"{v:.1f}%"),
        textposition="outside",
        textfont=dict(size=14),
        hovertemplate="<b>%{x}</b><br>运费占比: %{y:.2f}%<br>订单项数: %{customdata:,}<extra></extra>",
        customdata=df_g3["item_count"],
    ))
    fig3.add_hline(
        y=q123_avg, line_dash="dash", line_color="#e74c3c", line_width=2,
        annotation_text=f"Q1-Q3 均值: {q123_avg:.1f}%",
        annotation_position="top right",
        annotation_font=dict(color="#e74c3c", size=12),
    )
    fig3.update_layout(
        yaxis=dict(title="平均运费占比 (%)", range=[0, max(df_g3["freight_ratio"]) * 1.3]),
        xaxis=dict(title="季度"),
        height=420, margin=dict(t=30, b=40),
    )

    col_chart3, col_insight3 = st.columns([3, 2])
    with col_chart3:
        st.plotly_chart(fig3, use_container_width=True)
    with col_insight3:
        if len(q4_val) > 0:
            diff3 = q4_val[0] - q123_avg
            st.metric("Q4 运费占比", f"{q4_val[0]:.1f}%", delta=f"{diff3:+.1f}% vs Q1-Q3均值")
            if diff3 > 0:
                st.warning(f"Q4 运费占比高于前三季度均值 {diff3:.1f} 个百分点。")
            else:
                st.info("Q4 运费占比未高于前三季度。")

st.divider()

# ==============================================================================
# 原始数据抽样
# ==============================================================================
st.header("原始数据抽样")
st.caption("3NF 规范化后的数据样本（4 表 JOIN，前 50 行）")

sql_raw = """
    SELECT
        o.order_id,
        o.customer_unique_id,
        o.order_purchase_timestamp,
        oi.order_item_id,
        p.product_category_name,
        oi.price,
        oi.freight_value,
        r.review_score,
        o.order_delivered_customer_date,
        o.order_estimated_delivery_date
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    JOIN order_reviews r ON o.order_id = r.order_id
    LIMIT 50
"""

df_raw = get_data(sql_raw)
if df_raw is not None:
    st.dataframe(df_raw, use_container_width=True)
