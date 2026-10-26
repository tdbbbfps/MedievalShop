import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from tools import TOOL_MAPPING, TOOL_SCHEMAS

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "Furen-large")

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
)


def run_agent_turn(user_message: str, chat_history: list, max_steps: int = 5):
    """執行一次 Agent 對話迴圈，返回：(助手回覆內容, 歷程紀錄, 本輪工具軌跡)"""
    messages = [{"role": "system", "content": """你是一家中世紀武器道具店的AI客服助手。請保持親切、專業且具備冒險者世界觀的語調。

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
"""}]

    for role, content in chat_history:
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})

    turn_traces = []
    step_count = 0

    while step_count < max_steps:
        step_count += 1
        response = client.chat.completions.create(
            model=MODEL_NAME, messages=messages, tools=TOOL_SCHEMAS
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            final_text = msg.content or ""
            return final_text, turn_traces

        messages.append(msg)

        for tool_call in msg.tool_calls:
            tool_name = tool_call.function.name
            raw_args = tool_call.function.arguments

            try:
                parsed_args = json.loads(raw_args)
            except Exception:
                parsed_args = {}

            # 工具白名單保護
            if tool_name not in TOOL_MAPPING:
                tool_result = json.dumps(
                    {
                        "status": "error",
                        "message": f"未授權之工具呼叫：{tool_name}",
                    },
                    ensure_ascii=False,
                )
            else:
                try:
                    tool_func = TOOL_MAPPING[tool_name]
                    tool_result = tool_func(**parsed_args)
                except Exception as e:
                    tool_result = json.dumps(
                        {"status": "error", "message": str(e)},
                        ensure_ascii=False,
                    )

            turn_traces.append(
                {
                    "step": step_count,
                    "tool": tool_name,
                    "args": parsed_args,
                    "result": tool_result,
                }
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                }
            )

    return "抱歉，目前處理步驟過多，請稍後再試或直接向店員諮詢。", turn_traces