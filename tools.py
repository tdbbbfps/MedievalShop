import json
from database import (
    query_shop_info,
    query_item,
    list_items_by_category,
    place_order as db_place_order,
    query_order as db_query_order,
    cancel_order as db_cancel_order,
)

def get_shop_info(topic : str) -> str:
    """查詢商店政策、營業時間、折扣規範等。"""
    result = query_shop_info(topic)
    return json.dumps(result, ensure_ascii=False)


def get_item_info(name : str) -> str:
    """查詢商品詳細資訊。"""
    result = query_item(name)
    return json.dumps(result, ensure_ascii=False)

def list_shop_items(category: str = None) -> str:
    """瀏覽架上現有商品清單。"""
    result = list_items_by_category(category)
    return json.dumps(result, ensure_ascii=False)

def calculate_order_cost(items : list, discount_type : str = "none", need_delivery_outside : bool = False) -> str:
    """由代碼執行精確訂單計算，嚴禁讓模型心算。"""
    total = 0.0
    details = []

    for item in items:
        name = item.get("name", "")
        qty = int(item.get("quantity", 1))
        info = query_item(name)

        if info["status"] == "not_found":
            return json.dumps(
                {
                    "status": "error",
                    "message": f"品項「{name}」不存在，無法計算總價",
                },
                ensure_ascii=False,
            )

        subtotal = info["price"] * qty
        total += subtotal
        details.append(
            {
                "name": info["name"],
                "unit_price": info["price"],
                "quantity": qty,
                "subtotal": subtotal,
            }
        )

    discount_rate = 1.0
    if discount_type.lower() == "silver":
        discount_rate = 0.9
    elif discount_type.lower() == "gold":
        discount_rate = 0.8

    discounted_total = total * discount_rate
    delivery_fee = 50.0 if need_delivery_outside else 0.0
    final_amount = discounted_total + delivery_fee

    return json.dumps(
        {
            "status": "success",
            "item_subtotals": details,
            "raw_total": round(total, 2),
            "discount_applied": discount_type,
            "discount_multiplier": discount_rate,
            "delivery_fee": delivery_fee,
            "final_amount": round(final_amount, 2),
        },
        ensure_ascii=False,
    )

def place_order(customer_name: str, item_id: int, quantity: int) -> str:
    """建立購買訂單。"""
    result = db_place_order(customer_name, item_id, quantity)
    return json.dumps(result, ensure_ascii=False)


def query_order(order_id: int) -> str:
    """依訂單編號查詢訂單狀態與購買品項。"""
    result = db_query_order(order_id)
    return json.dumps(result, ensure_ascii=False)


def cancel_order(order_id: int) -> str:
    """取消已建立的訂單。"""
    result = db_cancel_order(order_id)
    return json.dumps(result, ensure_ascii=False)

def transfer_to_clerk(reason: str) -> str:
    """遇到客訴、資料庫查無資訊或非標準需求時轉交店主。"""
    return json.dumps(
        {
            "status": "transferred",
            "assigned_agent": "店主兼鍛造大師王小明",
            "reason": reason,
            "message": "已為您轉接本店鍛造大師王小明，請稍候。",
        },
        ensure_ascii=False,
    )


TOOL_MAPPING = {
    "get_shop_info": get_shop_info,
    "get_item_info": get_item_info,
    "list_shop_items": list_shop_items,
    "calculate_order_cost": calculate_order_cost,
    "place_order": place_order,
    "query_order": query_order,
    "cancel_order": cancel_order,
    "transfer_to_clerk": transfer_to_clerk,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_shop_info",
            "description": "查詢商店相關規則與資訊。支援主題：opening_hours, location, accepted_currency, repair_service, return_policy, guild_discount, delivery, custom_order。",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "欲查詢的主題關鍵字，必須為上述 8 個主題之一",
                    }
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_item_info",
            "description": "查詢單一裝備、道具的詳細規格、剩餘庫存與單價。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "商品名稱，例如：鐵製長劍、鐵製長槍",
                    }
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_shop_items",
            "description": "瀏覽商店目前有庫存販售的商品列表。可依照類別篩選或查看全部。",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "欲瀏覽的分類（選填），如：武器、防具、藥水。若未提供則列出所有商品。",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_order_cost",
            "description": "核心算帳工具，僅用於顧客下單前的報價與試算。凡是詢問「總共多少錢」、「打折後多少」、「加上運費多少」均必須呼叫此工具，禁止模型心算。",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "quantity": {"type": "integer"},
                            },
                            "required": ["name", "quantity"],
                        },
                        "description": "欲試算的品項名稱與數量清單",
                    },
                    "discount_type": {
                        "type": "string",
                        "enum": ["none", "silver", "gold"],
                        "description": "冒險者公會徽章/會員折扣：none (原價), silver (銀級9折), gold (金級8折)",
                    },
                    "need_delivery_outside": {
                        "type": "boolean",
                        "description": "是否需要城外護送配送（加收 50 金幣）",
                    },
                },
                "required": ["items"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "place_order",
            "description": "正式為顧客建立購買訂單並扣減倉庫庫存。請在確認顧客名稱、商品 ID 與數量後再呼叫。",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "冒險者姓名",
                    },
                    "item_id": {
                        "type": "integer",
                        "description": "商品 ID（可由 get_item_info 獲得）",
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "購買數量（必須大於 0）",
                    },
                },
                "required": ["customer_name", "item_id", "quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_order",
            "description": "透過訂單編號（整數）查詢該筆訂單的購買明細、狀態與總金額。",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "訂單編號，例如 1",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_order",
            "description": "取消指定的訂單編號，並自動將商品數量退回庫存。",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "欲取消的訂單編號",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_to_clerk",
            "description": "遇到客訴、資料庫查無特定物品、顧客要求客製特殊武器或要求店長介入時使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "轉接原因說明",
                    }
                },
                "required": ["reason"],
            },
        },
    },
]