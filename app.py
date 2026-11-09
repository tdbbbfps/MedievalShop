import gradio as gr
from agent import OPENING_LINE, run_agent_turn
from database import init_db

init_db()

custom_css = """
#trace-box textarea { font-family: monospace; font-size: 13px; }
"""


def chat_handler(user_input, history, raw_trace_history):
    if not user_input.strip():
        return "", history, raw_trace_history, ""

    if history is None:
        history = []
    if raw_trace_history is None:
        raw_trace_history = []

    bot_reply, updated_history, turn_traces = run_agent_turn(
        user_input, chat_history=history
    )

    history = updated_history

    trace_text_block = ""
    if turn_traces:
        for t in turn_traces:
            trace_text_block += f"【步驟 {t['step']}】調用工具：`{t['tool']}`\n"
            trace_text_block += f"- 參數：`{t['args']}`\n"
            trace_text_block += f"- 結果：`{t['result']}`\n\n"
    else:
        trace_text_block = "（本輪未調用任何工具，直接由模型或 RAG 回答）\n"

    raw_trace_history.append(
        f"### 冒險者提問：{user_input}\n{trace_text_block}---\n"
    )
    full_trace_display = "\n".join(raw_trace_history)

    return "", history, raw_trace_history, full_trace_display


with gr.Blocks(title="中世紀道具商店AI助手") as demo:
    gr.Markdown("## 中世紀道具商店AI助手")
    gr.Markdown(
        "歡迎光臨！本店提供裝備販售、保固諮詢、金額試算與下單服務。"
    )

    initial_history = [{"role": "assistant", "content": OPENING_LINE}]

    history_state = gr.State(initial_history)
    trace_state = gr.State([])

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                value=initial_history,
                label="櫃台對話紀錄",
                height=480,
            )
            msg_input = gr.Textbox(
                placeholder="輸入您的詢問（例如：有賣鐵製長劍嗎？我要下單...）",
                label="發送訊息給學徒",
            )
            with gr.Row():
                submit_btn = gr.Button("傳送", variant="primary")
                clear_btn = gr.Button("清空對話")

            gr.Examples(
                examples=[
                    "請問初級生命藥水一瓶多少金幣？現在有現貨嗎？",
                    "我想買 2 把鐵製長劍，我叫亞瑟，請幫我下單。",
                    "幫我查詢訂單編號 1 號的購買狀態。",
                    "幫我查訂單編號 9999 號。",
                    "售出的武器如果發現瑕疵可以退貨嗎？",
                    "我是金級冒險者，買 3 瓶初級生命藥水送到城外多少錢？",
                    "請問魔王城的弱點是什麼？",
                ],
                inputs=msg_input,
            )

        with gr.Column(scale=2):
            trace_display = gr.Markdown(
                label="工具調用紀錄",
                value="*尚無工具調用紀錄。當 Agent 調用工具時，歷程將顯示在此處。*",
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
        reset_history = [{"role": "assistant", "content": OPENING_LINE}]
        return (
            reset_history,
            reset_history,
            [],
            "*紀錄已清空。*",
        )

    clear_btn.click(
        clear_all,
        outputs=[chatbot, history_state, trace_state, trace_display],
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, css=custom_css)