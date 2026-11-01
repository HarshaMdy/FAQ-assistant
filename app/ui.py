# app/ui.py
"""
Phase 8: User Interface Layer
Interactive Web UI for the HDFC Mutual Fund FAQ Assistant.
Features:
  - Welcome banner & persistent disclaimer: "Facts-only. No investment advice."
  - 3 clickable example questions
  - Sourced citations and "Last updated" timestamps
  - Safe guardrail refusal handling
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.orchestrator import ask

DISCLAIMER_TEXT = "Facts-only. No investment advice."

EXAMPLE_QUESTIONS = [
    "What is the expense ratio of HDFC Large Cap Fund?",
    "What is the lock-in period for HDFC ELSS Tax Saver Fund?",
    "What is the minimum SIP for HDFC Mid Cap Fund?",
    "What is the exit load for HDFC Flexi Cap Fund?",
    "What is the benchmark index for HDFC Large Cap?",
    "Should I invest in HDFC Mid Cap?",  # Test refusal
]


def format_bot_response(result: dict) -> str:
    """Format orchestrator response into clean Markdown with citation."""
    if result["status"] == "refused":
        return f"**Notice:**\n{result['answer']}"

    lines = [result["answer"]]

    if result.get("source_url"):
        lines.append(f"\n**Official Source:** [{result['source_url']}]({result['source_url']})")

    if result.get("last_updated"):
        lines.append(f"\n*Last updated from sources: {result['last_updated']}*")

    return "\n".join(lines)


def chat_handler(message: str, history: list):
    """Gradio chat response generator."""
    if not message or not message.strip():
        return history

    response_data = ask(message)
    reply_md = format_bot_response(response_data)
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply_md})
    return history


def launch_gradio():
    """Launch Gradio Blocks UI."""
    import gradio as gr

    custom_css = """
    .disclaimer-banner {
        background-color: #f0f4f8;
        border-left: 4px solid #1a73e8;
        padding: 10px 14px;
        margin: 10px 0;
        border-radius: 4px;
        font-size: 0.9em;
    }
    """

    with gr.Blocks(title="HDFC MF FAQ Assistant", theme=gr.themes.Soft(), css=custom_css) as demo:
        gr.Markdown("# HDFC Mutual Fund FAQ Assistant")
        gr.Markdown(
            "Welcome! Ask factual questions about HDFC Mutual Fund schemes. "
            "Answers are sourced strictly from official Groww public pages."
        )

        gr.HTML(f"""
        <div class="disclaimer-banner">
            <strong>Disclaimer:</strong> {DISCLAIMER_TEXT} This assistant does not give portfolio advice or compute returns.
        </div>
        """)

        chatbot = gr.Chatbot(
            label="Scheme FAQ Chat",
            type="messages",
            height=420,
        )

        with gr.Row():
            msg_input = gr.Textbox(
                placeholder="Ask about expense ratio, exit load, minimum SIP, lock-in, benchmark...",
                label="Your Question",
                scale=8,
            )
            submit_btn = gr.Button("Ask", variant="primary", scale=1)
            clear_btn = gr.Button("Clear", scale=1)

        gr.Markdown("### Example Questions (Click to test):")
        gr.Examples(
            examples=EXAMPLE_QUESTIONS,
            inputs=msg_input,
        )

        gr.Markdown(f"---\n*{DISCLAIMER_TEXT}*")

        def user_submit(user_msg, chat_hist):
            if not user_msg.strip():
                return "", chat_hist
            chat_hist = chat_hist or []
            new_hist = chat_handler(user_msg, chat_hist)
            return "", new_hist

        submit_btn.click(user_submit, [msg_input, chatbot], [msg_input, chatbot])
        msg_input.submit(user_submit, [msg_input, chatbot], [msg_input, chatbot])
        clear_btn.click(lambda: [], outputs=[chatbot])

    return demo


if __name__ == "__main__":
    demo = launch_gradio()
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
