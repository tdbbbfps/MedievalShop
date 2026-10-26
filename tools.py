import json
from database import query_shop_info, query_item


def get_shop_info(topic: str) -> str:
    """查詢商店政策、營業時間、折扣規範等。"""
    result = query_shop_info(topic)
    return json.dumps(result, ensure_ascii=False)


def get_item_info(name: str) -> str:
    """查詢商品價格、是否在庫及詳細說明。"""
    result = query_item(name)
    return json.dumps(result, ensure_ascii=False)


def calculate_order_cost(
    items: list, discount_type: str = "none", need_delivery_outside: bool = False
) -> str:
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
    "calculate_order_cost": calculate_order_cost,
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
            "description": "查詢裝備、道具或服務的詳細規格、庫存狀態與單價。注意：若顧客是要計算購買多樣物品的總金額、折扣或結帳，請勿使用此工具，應改用`calculate_order_cost`。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "商品或服務名稱，例如：鐵製長劍、初級生命藥水、常規武器保養",
                    }
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_order_cost",
            "description": "核心算帳工具，計算顧客購買一項或多項商品時的總金額。本工具會自動從資料庫查詢各品項單價並執行乘法加總、折扣扣除與運費計算。凡是詢問「總共多少錢」、「打折後多少」、「加上運費多少」均必須呼叫此工具。",
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
                        "description": "購買品項與數量清單",
                    },
                    "discount_type": {
                        "type": "string",
                        "enum": ["none", "silver", "gold"],
                        "description": "會員折扣類型：none (原價), silver (銀級9折), gold (金級8折)",
                    },
                    "need_delivery_outside": {
                        "type": "boolean",
                        "description": "是否需要城外配送（城外需加 50 金幣護送費，城內則免費）",
                    },
                },
                "required": ["items"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_to_clerk",
            "description": "當資料庫查無特定物品、顧客要求自訂訂製、投訴或要求主管介入時使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "轉接給店主王小明的原因說明",
                    }
                },
                "required": ["reason"],
            },
        },
    },
]