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

    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            total_price REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            order_date TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (item_id) REFERENCES items(item_id) ON DELETE CASCADE
        );
        """
    )
    conn.commit()
    conn.close()

def query_shop_info(topic : str) -> dict:
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

def query_item(item_name : str) -> dict:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT name, category, price, is_available, description, stock
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
            "stock": int(row[5])
        }
    return {"status": "not_found", "message": f"本店未販售「{item_name}」"}

def add_order(name : str, item_id : int, item_name : str, quantity : int, total_price : float, status : str = "pending") -> dict:
    """新增一筆訂單。"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO orders (name, item_id, item_name, quantity, total_price, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name.strip(), item_id, item_name.strip(), quantity, total_price, status),
    )
    conn.commit()
    order_id = cursor.lastrowid
    conn.close()

    return {
        "status": "success",
        "order_id": order_id,
        "name": name,
        "item_id": item_id,
        "item_name": item_name,
        "quantity": quantity,
        "total_price": total_price,
        "order_status": status,
    }

def modify_order(order_id : int, item_id : int = None, item_name : str = None, quantity : int = None, total_price : float = None, status : str = None) -> dict:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    if not cursor.fetchone():
        conn.close()
        return {"status": "not_found", "message": f"未找到訂單編號「{order_id}」"}

    update_fields = []
    update_values = []

    if item_id is not None:
        update_fields.append("item_id = ?")
        update_values.append(item_id)
    if item_name is not None:
        update_fields.append("item_name = ?")
        update_values.append(item_name.strip())
    if quantity is not None:
        update_fields.append("quantity = ?")
        update_values.append(quantity)
    if total_price is not None:
        update_fields.append("total_price = ?")
        update_values.append(total_price)
    if status is not None:
        update_fields.append("status = ?")
        update_values.append(status)

    if not update_fields:
        conn.close()
        return {"status": "error", "message": "未提供任何修改的欄位"}

    update_query = f"UPDATE orders SET {', '.join(update_fields)} WHERE order_id = ?"
    update_values.append(order_id)

    cursor.execute(update_query, tuple(update_values))
    conn.commit()
    conn.close()

    return {"status": "success", "message": f"訂單編號{order_id}已更新"}

def remove_order(order_id : int) -> dict:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    if not cursor.fetchone():
        conn.close()
        return {"status": "not_found", "message": f"未找到訂單編號「{order_id}」"}

    cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
    conn.commit()
    conn.close()

    return {"status": "success", "message": f"訂單編號{order_id}已刪除"}