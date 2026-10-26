import gradio as gr
from database import init_db
from agent import run_agent_turn

# 啟動時自動初始化 SQLite
init_db()


def chat_handler(user_input, history, raw_trace_history):
    if not user_input.strip():
        return "", history, raw_trace_history, ""

    if history is None:
        history = []
    if raw_trace_history is None:
        raw_trace_history = []

    # 轉為純文字對話清單傳給 agent.py (若 agent 內部需要舊格式相容)
    agent_history = [
        (msg["role"], msg["content"]) for msg in history
    ]

    # 執行 Agent 邏輯
    bot_reply, turn_traces = run_agent_turn(user_input, agent_history)

    # Gradio messages 格式
    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": bot_reply})

    # 整理格式化 Tool Trace 面板
    trace_text_block = ""
    if turn_traces:
        for t in turn_traces:
            trace_text_block += f"【步驟 {t['step']}】調用工具：`{t['tool']}`\n"
            trace_text_block += f"- 參數：`{t['args']}`\n"
            trace_text_block += f"- 結果：`{t['result']}`\n\n"
    else:
        trace_text_block = "（本輪未調用任何工具，直接由模型回答）\n"

    raw_trace_history.append(
        f"### 顧客提問：{user_input}\n{trace_text_block}---\n"
    )
    full_trace_display = "\n".join(raw_trace_history)

    return "", history, raw_trace_history, full_trace_display


custom_css = """
#trace-box textarea { font-family: monospace; font-size: 13px; }
"""

with gr.Blocks(title="中世紀道具商店AI助手") as demo:
    gr.Markdown("## 中世紀道具商店客服助手")
    gr.Markdown(
        "沒錯，中世紀的道具商店必須引入目前最流行的大語言模型AI助手。"
    )

    history_state = gr.State([])
    trace_state = gr.State([])

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(label="對話歷程", height=480)
            msg_input = gr.Textbox(
                placeholder="輸入您的詢問",
                label="發送訊息",
            )
            with gr.Row():
                submit_btn = gr.Button("傳送", variant="primary")
                clear_btn = gr.Button("清空對話")

            gr.Examples(
                examples=[
                    "請問初級生命藥水一瓶多少金幣?現在有現貨嗎?",
                    "我想買3瓶初級生命藥水和1把鐵製長劍，我是銀級冒險者，送到王都城內需要多少錢?",
                    "我現在有2500元，買得起幾瓶高級生命藥水?",
                    "你們有賣能治癒斷臂的神級生命藥水嗎?",
                    "請問酒店在哪裡?",
                    "老闆你單身嗎?",
                    "秘銀太刀有現貨嗎?",
                    "什麼時候有營業?"
                ],
                inputs=msg_input,
            )

        with gr.Column(scale=2):
            trace_display = gr.Markdown(
                label="工具調用紀錄",
                value="*尚無工具調用紀錄。當Agent調用工具時，歷程將顯示在此處。*",
            )

    submit_btn.click(
        chat_handler,
        inputs=[msg_input, history_state, trace_state],
        outputs=[msg_input, chatbot, trace_state, trace_display],
    )
    msg_input.submit(
        chat_handler,
        inputs=[msg_input, history_state, trace_state],
        outputs=[msg_input, chatbot, trace_state, trace_display],
    )

    def clear_all():
        return [], [], "*紀錄已清空。*"

    clear_btn.click(
        clear_all, outputs=[chatbot, history_state, trace_display]
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, css=custom_css)