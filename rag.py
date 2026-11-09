import json
import os
import sqlite3
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
DB_FILE = "shop.db"

def get_embedding(text: str) -> list[float]:
    """產生文本的Embedding向量。"""
    text = text.replace("\n", " ").strip()
    response = client.embeddings.create(input=[text], model=EMBEDDING_MODEL)
    return response.data[0].embedding


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """計算兩向量間的餘弦相似度。"""
    vec_a = np.array(a, dtype=float)
    vec_b = np.array(b, dtype=float)
    norm = np.linalg.norm(vec_a) * np.linalg.norm(vec_b)
    if norm == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / norm)


def init_rag_db(csv_file: str = "shop_info.csv"):
    """初始化並建立RAG資料表，讀取CSV並存入Embedding向量。"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS shop_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            content TEXT NOT NULL,
            embedding TEXT NOT NULL
        )
        """
    )
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM shop_rules")
    count = cursor.fetchone()[0]

    if count == 0 and os.path.exists(csv_file):
        print(f"正在為 {csv_file} 生成 Embedding 並寫入 SQLite...")
        df = pd.read_csv(csv_file)

        for _, row in df.iterrows():
            topic = str(row["topic"]).strip()
            content = str(row["content"]).strip()
            text_to_embed = f"【主題：{topic}】{content}"

            # 計算向量並序列化為 JSON 字串存入 SQLite
            emb = get_embedding(text_to_embed)
            cursor.execute(
                "INSERT INTO shop_rules (topic, content, embedding) VALUES (?, ?, ?)",
                (topic, content, json.dumps(emb)),
            )

        conn.commit()
        print("RAG 資料表初始化完成！")

    conn.close()


def retrieve_rules(query: str, top_k: int = 2, threshold: float = 0.3) -> str:
    """根據使用者提問檢索最相關的店規內容。"""
    if not os.path.exists(DB_FILE):
        return "暫無相關規章資料。"

    query_emb = get_embedding(query)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT topic, content, embedding FROM shop_rules")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "暫無相關規章資料。"

    results = []
    for topic, content, emb_str in rows:
        rule_emb = json.loads(emb_str)
        score = cosine_similarity(query_emb, rule_emb)
        if score >= threshold:
            results.append((score, topic, content))

    results.sort(key=lambda x: x[0], reverse=True)
    top_matches = results[:top_k]

    if not top_matches:
        return "未檢索到直接相關的店內規章。"

    retrieved_texts = [f"- 【{topic}】: {content}" for _, topic, content in top_matches]
    return "\n".join(retrieved_texts)