import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="清洗 Olist 数据并生成初始大宽表。"
    )
    parser.add_argument(
        "--input-dir",
        default="archive",
        help="输入 CSV 文件所在目录，默认值为 archive。",
    )
    parser.add_argument(
        "--output",
        default="cleaned_flat_table.csv",
        help="输出文件路径，默认值为 cleaned_flat_table.csv。",
    )
    return parser.parse_args()


def load_csv(input_dir: Path, filename: str, usecols: list[str]) -> pd.DataFrame:
    file_path = input_dir / filename
    return pd.read_csv(file_path, usecols=usecols)


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_path = Path(args.output)

    try:
        customers = load_csv(
            input_dir,
            "olist_customers_dataset.csv",
            ["customer_id", "customer_unique_id"],
        )
        orders = load_csv(
            input_dir,
            "olist_orders_dataset.csv",
            [
                "order_id",
                "customer_id",
                "order_purchase_timestamp",
                "order_delivered_customer_date",
                "order_estimated_delivery_date",
            ],
        )
        order_items = load_csv(
            input_dir,
            "olist_order_items_dataset.csv",
            ["order_id", "order_item_id", "product_id", "price", "freight_value"],
        )
        products = load_csv(
            input_dir,
            "olist_products_dataset.csv",
            ["product_id", "product_category_name"],
        )
        reviews = load_csv(
            input_dir,
            "olist_order_reviews_dataset.csv",
            ["review_id", "order_id", "review_score"],
        )
    except FileNotFoundError as exc:
        print(f"[错误] 找不到输入文件：{exc.filename}")
        print(f"[提示] 请检查 --input-dir 路径是否正确：{input_dir}")
        return 1
    except ValueError as exc:
        print(f"[错误] CSV 列读取失败：{exc}")
        print("[提示] 请确认数据集列名与脚本预期一致。")
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"[错误] 读取数据时发生异常：{exc}")
        return 1

    order_rows_before = len(orders)
    product_category_nan_before = int(products["product_category_name"].isna().sum())

    # --- 处理脏数据：时间字段格式统一 ---
    datetime_cols = [
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in datetime_cols:
        orders[col] = pd.to_datetime(orders[col], errors="coerce")

    # --- 处理缺失值：仅保留已送达订单 ---
    delivered_missing_count = int(orders["order_delivered_customer_date"].isna().sum())
    orders = orders.dropna(subset=["order_delivered_customer_date"]).copy()

    # --- 处理缺失值：商品类别缺失填充 ---
    products["product_category_name"] = products["product_category_name"].fillna("Unknown")

    flat_df = (
        orders.merge(customers, on="customer_id", how="inner")
        .merge(order_items, on="order_id", how="inner")
        .merge(products, on="product_id", how="inner")
        .merge(reviews, on="order_id", how="inner")
    )

    # --- 处理缺失值：评价分缺失填充 ---
    review_missing_before_fill = int(flat_df["review_score"].isna().sum())
    flat_df["review_score"] = flat_df["review_score"].fillna(3)

    selected_columns = [
        "order_id",
        "order_item_id",
        "customer_unique_id",
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "product_id",
        "product_category_name",
        "price",
        "freight_value",
        "review_id",
        "review_score",
    ]
    flat_df = flat_df[selected_columns].copy()

    for col in datetime_cols:
        flat_df[col] = flat_df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

    try:
        flat_df.to_csv(output_path, index=False)
    except Exception as exc:  # noqa: BLE001
        print(f"[错误] 导出文件失败：{exc}")
        return 1

    print("=== 数据清洗完成 ===")
    print(f"输入目录: {input_dir}")
    print(f"输出文件: {output_path}")
    print(f"orders 原始行数: {order_rows_before}")
    print(f"orders 丢弃未送达订单行数: {delivered_missing_count}")
    print(f"orders 清洗后行数: {len(orders)}")
    print(f"products 商品类别原始缺失数: {product_category_nan_before}")
    print(f"合并后 review_score 填充前缺失数: {review_missing_before_fill}")
    print(f"最终宽表行数: {len(flat_df)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
