import os
import sqlite3
import pandas as pd

DB_FILE = "shop.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)

    if os.path.exists("shop_info.csv"):
        df_info = pd.read_csv("shop_info.csv")
        df_info.to_sql("shop_info", conn, if_exists="replace", index=False)

    if os.path.exists("items.csv"):
        df_items = pd.read_csv("items.csv")
        df_items.to_sql("items", conn, if_exists="replace", index=False)

    conn.close()


def query_shop_info(topic: str) -> dict:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT content FROM shop_info WHERE topic = ? LIMIT 1", (topic.strip(),)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"status": "success", "topic": topic, "content": row[0]}
    return {"status": "not_found", "message": f"未找到與「{topic}」相關的店規與資訊"}


def query_item(item_name: str) -> dict:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT name, category, price, is_available, description 
        FROM items 
        WHERE name LIKE ? 
        LIMIT 1
        """,
        (f"%{item_name.strip()}%",),
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "status": "success",
            "name": row[0],
            "category": row[1],
            "price": float(row[2]),
            "is_available": bool(row[3]),
            "description": row[4],
        }
    return {"status": "not_found", "message": f"本店未販售「{item_name}」"}