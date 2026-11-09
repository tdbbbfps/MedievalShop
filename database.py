import os
import sqlite3
import pandas as pd
from rag import init_rag_db

DB_FILE = "shop.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if os.path.exists("shop_info.csv"):
        df_info = pd.read_csv("shop_info.csv")
        df_info.to_sql("shop_info", conn, if_exists="replace", index=False)

    if os.path.exists("items.csv"):
        df_items = pd.read_csv("items.csv")
        df_items.to_sql("items", conn, if_exists="replace", index=False)

    
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

    init_rag_db("shop_info.csv")

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
    """查詢物品資訊。"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT item_id, name, category, price, description, stock
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
            "status" : "success",
            "item_id" : row[0],
            "name" : row[1],
            "category" : row[2],
            "price" : float(row[3]),
            "description" : row[4],
            "stock" : int(row[5])
        }
    return {"status": "not_found", "message": f"本店未販售{item_name}"}

def list_items_by_category(category : str = None) -> dict:
    """列出特定分類或所有架上有庫存的道具名稱與價格。"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if category:
        cursor.execute("SELECT item_id, name, price, stock FROM items WHERE category LIKE ? AND stock > 0", (f"%{category.strip()}%",))
    else:
        cursor.execute("SELECT item_id, name, price, stock FROM items WHERE stock > 0")
    rows = cursor.fetchall()
    conn.close()

    items = [{"item_id" : r[0], "name" : r[1], "price" : float(r[2]), "stock" : r[3]} for r in rows]
    return {"status" : "success", "count" : len(items), "items" : items}

def place_order(customer_name : str, item_id : int, quantity : int) -> dict:
    """建立購買訂單。"""
    if quantity <= 0:
        return {"status" : "error", "message" : "訂購數量必須大於0"}

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 1. 查詢道具資訊
    cursor.execute("SELECT name, price, stock FROM items WHERE item_id = ?", (item_id,))
    item = cursor.fetchone()

    if not item:
        conn.close()
        return {"status" : "not_found", "message": f"查無道具編號{item_id}"}

    item_name, price, stock = item
    if stock < quantity:
        conn.close()
        return {"status": "error", "message": f"道具{item_name}庫存不足，目前庫存僅剩 {stock} 件"}

    total_price = float(price * quantity)

    # 2. 扣減庫存
    cursor.execute("UPDATE items SET stock = stock - ? WHERE item_id = ?", (quantity, item_id))

    # 3. 寫入訂單
    cursor.execute(
        """
        INSERT INTO orders (name, item_id, item_name, quantity, total_price, status)
        VALUES (?, ?, ?, ?, ?, 'confirmed')
        """,
        (customer_name.strip(), item_id, item_name, quantity, total_price),
    )
    conn.commit()
    order_id = cursor.lastrowid
    conn.close()

    return {
        "status": "success",
        "order_id": order_id,
        "customer_name": customer_name,
        "item_name": item_name,
        "quantity": quantity,
        "total_price": total_price,
        "order_status": "confirmed"
    }

def query_order(order_id : int) -> dict:
    """查詢指定訂單編號的狀態與購買內容。"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT order_id, name, item_id, item_name, quantity, total_price, status, order_date FROM orders WHERE order_id = ?",
        (order_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "status": "success",
            "order_id": row[0],
            "customer_name": row[1],
            "item_id": row[2],
            "item_name": row[3],
            "quantity": row[4],
            "total_price": float(row[5]),
            "order_status": row[6],
            "order_date": row[7]
        }
    return {"status" : "not_found", "message" : f"查無訂單編號{order_id}"}

def cancel_order(order_id : int) -> dict:
    """取消訂單。"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT item_id, quantity, status FROM orders WHERE order_id = ?", (order_id,))
    order = cursor.fetchone()

    if not order:
        conn.close()
        return {"status" : "not_found", "message" : f"查無訂單編號{order_id}"}

    item_id, quantity, status = order
    if status == "cancelled":
        conn.close()
        return {"status" : "error", "message" : f"訂單編號{order_id}已經取消過了"}

    # 1. 返還庫存
    cursor.execute("UPDATE items SET stock = stock + ? WHERE item_id = ?", (quantity, item_id))
    # 2. 更新狀態
    cursor.execute("UPDATE orders SET status = 'cancelled' WHERE order_id = ?", (order_id,))
    conn.commit()
    conn.close()

    return {"status" : "success", "message" : f"訂單編號{order_id}已成功取消"}