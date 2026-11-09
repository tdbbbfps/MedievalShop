import time
import os
from openai import OpenAI
from dotenv import load_dotenv
from tools import TOOL_SCHEMAS

load_dotenv()

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

# 10 個測試案例：包含單查、算錢、資訊、轉接與不調用工具
test_cases = [
    {"q": "請問初級生命藥水一瓶多少金幣?現在有現貨嗎?", "expected": ["get_item_info"]},
    {"q": "王都城外荒野可以外送嗎？運費多少？", "expected": ["get_shop_info"]},
    {"q": "我想買3瓶初級生命藥水和1把鐵製長劍，我是銀級冒險者，送到王都城內需要多少錢?", "expected": ["calculate_order_cost"]},
    {"q": "秘銀太刀現在有現貨嗎？", "expected": ["get_item_info"]},
    {"q": "我現在有2500元，買得起幾瓶高級生命藥水?", "expected": ["calculate_order_cost"]},
    {"q": "我想要買100瓶高級魔力藥水，送去王都外距離500公里的城市，要多少錢?", "expected": ["calculate_order_cost"]},
    {"q": "請問酒店在哪裡?", "expected": ["none"]},
    {"q": "我想客製化一把帶有冰霜附魔的屠龍巨劍，該怎麼訂做？", "expected": ["transfer_to_clerk", "get_shop_info"]},
    {"q": "什麼時候有營業?", "expected": ["get_shop_info"]},
    {"q": "老闆你單身嗎?", "expected": ["none"]}
]

def run_single_choice_test(query: str):
    messages = [
        {"role": "system", "content": """你是一家中世紀武器道具店的AI客服助手。請保持親切、專業且具備冒險者世界觀的語調。

【核心運作守則】
1. 接地規則：
   - 你`不`可憑記憶回答任何價格、庫存或店規，所有事實必須源自工具調用結果。
   - 若工具傳回查無資料，請如實告知顧客，嚴禁自行捏造任何數值或庫存狀態。
   - 絕對嚴禁自行心算加總或折抵：所有涉及金額總計、折扣、購買多樣物品的花費計算，必須完全仰賴`calculate_order_cost`工具計算所得的結果作答，嚴禁自行計算！
   
2. 守備範圍 (Scope)：
   - 僅回答與本店業務（武器、防具、道具販售、保養維修、店規運費）相關之事項。
   - 顧客若詢問非本店業務之問題（例如：討伐魔王戰略、別家酒館八卦、歷史政治），請委婉拒絕並引導回本店商品。
   - 若顧客說諸如早安、晚安等無關商店問題的句子，請直接把他趕出店裡。

3. 工具分派 (Routing)：
   - 詢問店規、營業時段、付費幣別、退換政策、會員折扣比例、運送方式 -> 呼叫`get_shop_info`。
   - 詢問單一裝備/道具/服務之價格、庫存可用狀態 -> 呼叫`get_item_info`。
   - 詢問多項商品金額、會員折抵試算、外送費用累加 -> 呼叫`calculate_order_cost`（嚴禁模型自己心算加總）。
   - 資料庫明確查無資訊、客訴、要求高度客製化鍛造 -> 呼叫`transfer_to_clerk`。

4. 語言與格式 (Language & Format)：
   - 一律使用繁體中文回覆。
   - 保持簡潔有力，回答控制在 3 句話以內。
"""},
        {"role": "user", "content": query}
    ]
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto"
        )
        msg = response.choices[0].message
        if msg.tool_calls:
            return [tc.function.name for tc in msg.tool_calls]
        return ["none"]
    except Exception as e:
        return [f"error: {str(e)}"]

print("=" * 60)
print("開始執行 Tool-Choice Test (10 題測試)")
print("=" * 60)

passed = 0
for i, case in enumerate(test_cases, 1):
    q = case["q"]
    expected = case["expected"]
    actual = run_single_choice_test(q)

    is_pass = any(act in expected for act in actual)
    if is_pass:
        passed += 1
        status = "PASS"
    else:
        status = "MISS"
        
    print(f"[{status}] Q{i}: {q}")
    print(f"   預期工具: {expected} | 實際調用: {actual}\n")
    time.sleep(1)

score = (passed / len(test_cases)) * 100
print("=" * 60)
print(f"測試結果：{passed}/{len(test_cases)} 通過 (命中率: {score:.1f}%)")
print("=" * 60)