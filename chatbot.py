import os
import time
from typing import Dict, List, Optional

import gradio as gr
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Configure Gemini AI
model = None
if not GOOGLE_API_KEY:
    print(" ERROR: GOOGLE_API_KEY not found in .env file")
    print(" Please create a .env file and add your API key:")
    print("   GOOGLE_API_KEY=your_actual_api_key_here")
    print(
        " Get your API key from: https://aistudio.google.com/app/apikey"
    )
else:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # First, list all available models
        print("\n Checking available models...")
        available_models = []
        
        # Prioritize models with best free tier quotas
        preferred_models = [
            "gemini-flash-latest",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-pro-latest"
        ]
        
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
                    print(f"    Found: {m.name}")
        except Exception as list_error:
            print(f"    Could not list models: {list_error}")
        
        # Try preferred models first (best quotas for free tier)
        model = None
        print("\n Selecting best model for free tier...")
        
        for pref_model in preferred_models:
            matching = [
                m for m in available_models 
                if pref_model in m.lower()
            ]
            if matching:
                try:
                    model = genai.GenerativeModel(matching[0])
                    print(f" Successfully initialized: {matching[0]}")
                    break
                except Exception as model_error:
                    print(f" Failed {matching[0]}: {model_error}")
                    continue
        
        # Fallback: try any flash model (better quotas than pro)
        if not model:
            print("\n Trying fallback flash models...")
            flash_models = [
                m for m in available_models 
                if 'flash' in m.lower() and 'exp' not in m.lower()
            ]
            for flash_model in flash_models:
                try:
                    model = genai.GenerativeModel(flash_model)
                    print(f" Using fallback: {flash_model}")
                    break
                except Exception:
                    continue
        else:
            # Last resort: try standard model names directly
            print("\n No models found, trying direct initialization...")
            model_names = [
                "gemini-flash-latest",
                "gemini-2.5-flash",
                "gemini-2.0-flash",
                "gemini-pro"
            ]
            
            model = None
            for model_name in model_names:
                try:
                    model = genai.GenerativeModel(model_name)
                    print(f" Initialized with: {model_name}")
                    break
                except Exception:
                    print(f"    Failed: {model_name}")
                    continue
            
            if not model:
                raise Exception(
                    "No compatible model found. "
                    "Your API key may have exhausted its quota. "
                    "Please wait or get a new API key."
                )
                
    except Exception as init_error:
        print(f"\n Error initializing Gemini model: {init_error}")
        print("\n Troubleshooting steps:")
        print("   1. Verify API key at: "
              "https://aistudio.google.com/app/apikey")
        print("   2. Check internet connection")
        print("   3. Update library: "
              "pip install --upgrade google-generativeai")
        model = None


CSS = """
/* Dark Theme Styles */
.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont,
                  sans-serif !important;
    background-color: #0f172a !important;
}

/* Sidebar Styles */
.sidebar-column {
    background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%)
                !important;
    padding: 1.5rem !important;
    min-height: 100vh !important;
    border-right: 1px solid #334155 !important;
}

/* Chat Container */
.chat-column {
    background-color: #0f172a !important;
    min-height: 100vh !important;
}

/* New Chat Button */
.new-chat-btn {
    width: 100% !important;
    background: linear-gradient(135deg, #10b981 0%, #059669 100%)
                !important;
    color: white !important;
    border: none !important;
    padding: 0.875rem !important;
    border-radius: 0.75rem !important;
    font-weight: 600 !important;
    margin-bottom: 1.5rem !important;
    box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.3) !important;
    transition: all 0.3s ease !important;
}

.new-chat-btn:hover {
    background: linear-gradient(135deg, #059669 0%, #047857 100%)
                !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 8px -1px rgba(16, 185, 129, 0.4) !important;
}

/* History Buttons */
.history-btn {
    width: 100% !important;
    background-color: transparent !important;
    color: #94a3b8 !important;
    border: 1px solid #334155 !important;
    padding: 0.75rem !important;
    text-align: left !important;
    border-radius: 0.5rem !important;
    margin-bottom: 0.5rem !important;
    transition: all 0.2s ease !important;
    font-size: 0.875rem !important;
}

.history-btn:hover {
    background-color: #1e293b !important;
    color: white !important;
    border-color: #10b981 !important;
    transform: translateX(4px) !important;
}

/* Delete Buttons */
.delete-btn {
    background-color: #7f1d1d !important;
    color: white !important;
    border: none !important;
    padding: 0.5rem 0.75rem !important;
    border-radius: 0.5rem !important;
    font-size: 0.875rem !important;
    margin-top: 0.25rem !important;
    transition: all 0.2s ease !important;
}

.delete-btn:hover {
    background-color: #991b1b !important;
    transform: scale(1.05) !important;
}

/* Prompt Cards */
.prompt-card {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%)
                !important;
    border: 1px solid #475569 !important;
    padding: 1.5rem !important;
    border-radius: 1rem !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    height: 100% !important;
}

.prompt-card:hover {
    border-color: #10b981 !important;
    transform: translateY(-4px) !important;
    box-shadow: 0 10px 20px rgba(16, 185, 129, 0.2) !important;
}

/* Input Area */
.input-container {
    background: linear-gradient(180deg, transparent 0%, #0f172a 50%)
                 !important;
    padding: 1.5rem !important;
    border-top: 1px solid #334155 !important;
}

/* Welcome Section */
.welcome-section {
    text-align: center !important;
    padding: 3rem 2rem !important;
}

.welcome-title {
    font-size: 2.5rem !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%)
                !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    margin-bottom: 1rem !important;
}

.welcome-subtitle {
    font-size: 1.125rem !important;
    color: #94a3b8 !important;
    margin-bottom: 3rem !important;
}

/* Chatbot Styling */
.message.user {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%)
                !important;
    color: white !important;
    border-radius: 1rem 1rem 0.25rem 1rem !important;
    padding: 1rem 1.25rem !important;
    box-shadow: 0 4px 6px rgba(16, 185, 129, 0.2) !important;
}

.message.bot {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%)
                !important;
    color: #e2e8f0 !important;
    border-radius: 1rem 1rem 1rem 0.25rem !important;
    padding: 1rem 1.25rem !important;
    border: 1px solid #475569 !important;
}

/* Loading Animation */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%     { opacity: 0.5; }
}

.loading {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite !important;
    color: #10b981 !important;
}

/* Error Message */
.error-message {
    background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%)
                !important;
    color: #fecaca !important;
    padding: 1rem !important;
    border-radius: 0.75rem !important;
    border: 1px solid #dc2626 !important;
    margin: 1rem 0 !important;
}

/* Scrollbar Styling */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #1e293b;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: #475569;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #64748b;
}

/* Section Divider */
.section-divider {
    height: 1px;
    background: linear-gradient(
        90deg,
        transparent 0%,
        #334155 50%,
        transparent 100%
    );
    margin: 1.5rem 0;
}
"""


def convert_history_for_api(history: List[Dict]) -> List[Dict]:
    """Convert chat history to Gemini API format."""
    api_history: List[Dict] = []
    for msg in history:
        content = msg.get("content") or ""
        role = (
            "model"
            if msg.get("role") == "assistant"
            else msg.get("role")
        )
        api_history.append(
            {"role": role, "parts": [{"text": content}]}
        )
    return api_history


def chat_response_stream(history: List[Dict]):
    """Stream response from Gemini model."""
    print(f" Processing message (history: {len(history)} messages)")

    if not history or len(history) < 2:
        print(" Insufficient history")
        return

    user_message = history[-2].get("content", "")
    print(f" User: {user_message[:50]}...")

    if not model:
        error_msg = (
            " Error: Model not initialized. "
            "Please check your API key in the .env file."
        )
        print(error_msg)
        history[-1]["content"] = error_msg
        yield history
        return

    if len(user_message) > 10000:
        error_msg = (
            " Error: Message too long. "
            "Please keep messages under 10,000 characters."
        )
        history[-1]["content"] = error_msg
        yield history
        return

    try:
        api_history = convert_history_for_api(history[:-2])

        # Start chat session
        session = model.start_chat(history=api_history)

        # Send message and stream response
        response = session.send_message(user_message, stream=True)

        full_response = ""
        for chunk in response:
            if hasattr(chunk, "text"):
                full_response += chunk.text
                history[-1]["content"] = full_response
                yield history

        print(f" Response completed ({len(full_response)} chars)")

    except Exception as e:
        error_msg = (
            f" API Error: {str(e)}\n\n"
            "Please check:\n"
            "• Your internet connection\n"
            "• API key validity\n"
            "• Rate limits"
        )
        print(f" Exception: {e}")
        history[-1]["content"] = error_msg
        yield history


def handle_user_message(message: str, history: Optional[List[Dict]]):
    """Process user message and add to chat history."""
    print(" New message received")

    if not message or not message.strip():
        print(" Empty message")
        return history if history else []

    if history is None:
        history = []

    history.append({"role": "user", "content": message.strip()})
    history.append({"role": "assistant", "content": "🤔 Thinking..."})

    print(f" History updated: {len(history)} messages")
    return history


def show_chat_and_clear_textbox(chatbot_history: List[Dict]):
    """
    Show chat interface and clear input textbox.

    This function is used in a .then(...) chain that expects
    three outputs: (initial_view_update, chatbot_update, msg_update)
    """
    initial_view_update = gr.update(visible=False)
    chatbot_update = gr.update(visible=True, value=chatbot_history)
    msg_update = gr.update(value="", interactive=True)
    return initial_view_update, chatbot_update, msg_update


def save_and_clear_session(
    current_history: List[Dict], all_history: List[Dict]
):
    """Save current chat and start new session."""
    print(" Starting new chat")

    if current_history and len(current_history) > 0:
        # Create title from first user message
        title = "New Chat"
        for msg in current_history:
            if msg.get("role") == "user" and msg.get("content"):
                first = msg["content"].strip()
                title = first[:50]
                if len(first) > 50:
                    title += "..."
                break

        # Check duplicates
        is_duplicate = any(
            chat["history"] == current_history for chat in all_history
        )

        if not is_duplicate:
            all_history.insert(
                0,
                {
                    "title": title,
                    "history": current_history.copy(),
                    "timestamp": time.time(),
                },
            )

            # Keep only last 20 chats
            if len(all_history) > 20:
                all_history = all_history[:20]

    # Update history buttons with delete buttons
    history_updates: List[gr.Update] = []
    for i in range(10):
        if i < len(all_history):
            history_updates.append(
                gr.update(value=all_history[i]["title"], visible=True)
            )
            history_updates.append(gr.update(visible=True))
        else:
            history_updates.append(gr.update(visible=False))
            history_updates.append(gr.update(visible=False))

    return (
        all_history,
        gr.update(value=[], visible=False),
        gr.update(visible=True),
        *history_updates,
    )


def load_chat_history(
    current_history: List[Dict], all_history: List[Dict], index: int
):
    """Load selected chat history."""
    print(f" Loading chat at index: {index}")

    if index < 0 or index >= len(all_history):
        print(f" Invalid index: {index}")
        return all_history, gr.update(), gr.update()

    # Save current chat if not empty and not already saved
    if current_history and len(current_history) > 0:
        is_saved = any(
            chat["history"] == current_history for chat in all_history
        )
        if not is_saved:
            title = "New Chat"
            for msg in current_history:
                if msg.get("role") == "user" and msg.get("content"):
                    first = msg["content"].strip()
                    title = first[:50]
                    if len(first) > 50:
                        title += "..."
                    break

            all_history.insert(
                0,
                {
                    "title": title,
                    "history": current_history.copy(),
                    "timestamp": time.time(),
                },
            )

            # Adjust index after insertion
            index += 1

            if len(all_history) > 20:
                all_history = all_history[:20]

    if index < len(all_history):
        chat_to_load = all_history[index]
        return (
            all_history,
            gr.update(value=chat_to_load["history"], visible=True),
            gr.update(visible=False),
        )

    return all_history, gr.update(), gr.update()


def delete_chat_history(
    all_history: List[Dict], index: int, current_history: List[Dict]
):
    """Delete a specific chat from history."""
    print(f" Deleting chat at index: {index}")

    chatbot_update = gr.update()
    initial_view_update = gr.update()

    if 0 <= index < len(all_history):
        deleted_chat = all_history.pop(index)
        print(f" Deleted: {deleted_chat['title']}")

        if current_history and current_history == deleted_chat["history"]:
            chatbot_update = gr.update(value=[], visible=False)
            initial_view_update = gr.update(visible=True)

    # Update all history buttons
    history_updates: List[gr.Update] = []
    for i in range(10):
        if i < len(all_history):
            history_updates.append(
                gr.update(value=all_history[i]["title"], visible=True)
            )
            history_updates.append(gr.update(visible=True))
        else:
            history_updates.append(gr.update(visible=False))
            history_updates.append(gr.update(visible=False))

    return (
        all_history,
        chatbot_update,
        initial_view_update,
        *history_updates,
    )


def clear_all_history(
    all_history: List[Dict], current_history: List[Dict]
):
    """Clear all chat history."""
    print(" Clearing all chat history")

    all_history.clear()

    history_updates: List[gr.Update] = []
    for _ in range(10):
        history_updates.append(gr.update(visible=False))
        history_updates.append(gr.update(visible=False))

    return (
        all_history,
        gr.update(value=[], visible=False),
        gr.update(visible=True),
        *history_updates,
    )


# Create Gradio Interface
with gr.Blocks(
    css=CSS, theme=gr.themes.Soft(), title="Manansh Chatbot"
) as demo:
    all_chats = gr.State([])

    with gr.Row():
        # Sidebar
        with gr.Column(
            scale=1, elem_classes="sidebar-column", min_width=280
        ):
            gr.Markdown("# Manansh Chatbot")
            gr.Markdown("### Your AI Assistant")

            new_chat_btn = gr.Button(
                " New Chat", elem_classes="new-chat-btn", size="lg"
            )

            gr.HTML('<div class="section-divider"></div>')
            gr.Markdown("###  Chat History")

            # Create 10 pairs of history button + delete button
            history_buttons = []
            delete_buttons = []
            for _ in range(10):
                with gr.Row():
                    hist_btn = gr.Button(
                        visible=False,
                        elem_classes="history-btn",
                        scale=4,
                    )
                    del_btn = gr.Button(
                        "",
                        visible=False,
                        elem_classes="delete-btn",
                        scale=1,
                        size="sm",
                    )
                    history_buttons.append(hist_btn)
                    delete_buttons.append(del_btn)

            gr.HTML('<div class="section-divider"></div>')
            clear_all_btn = gr.Button(
                " Clear All History",
                elem_classes="delete-btn",
                size="sm",
            )

            gr.Markdown("---")
            gr.Markdown("** Powered by Manansh**")
            gr.Markdown("*Fast • Smart • Reliable*")

        # Main Chat Area
        with gr.Column(scale=4, elem_classes="chat-column"):
            # Initial Welcome View
            with gr.Column(
                visible=True, elem_classes="welcome-section"
            ) as initial_view:
                gr.HTML(
                    '<h1 class="welcome-title">'
                    " Welcome to Manansh Chat"
                    "</h1>"
                )
                gr.HTML(
                    '<p class="welcome-subtitle">'
                    "Choose a prompt below or start typing "
                    "your own message"
                    "</p>"
                )

                with gr.Row():
                    prompt1 = gr.Button(
                        " Explain quantum computing\nin simple terms",
                        elem_classes="prompt-card",
                        size="lg",
                    )
                    prompt2 = gr.Button(
                        " Creative ideas for a\n"
                        "10 year old's birthday",
                        elem_classes="prompt-card",
                        size="lg",
                    )

                with gr.Row():
                    prompt3 = gr.Button(
                        " How to make an HTTP\n"
                        "request in JavaScript?",
                        elem_classes="prompt-card",
                        size="lg",
                    )
                    prompt4 = gr.Button(
                        " Write a poem about\n"
                        "artificial intelligence",
                        elem_classes="prompt-card",
                        size="lg",
                    )

            # Chatbot
            chatbot = gr.Chatbot(
                type="messages",
                avatar_images=(
                    "https://api.dicebear.com/7.x/avataaars/svg"
                    "?seed=User",
                    "https://api.dicebear.com/7.x/bottts/svg?seed=Gemini",
                ),
                visible=False,
                height=650,
                show_copy_button=True,
                placeholder=" Your conversation will appear here...",
                render_markdown=True,
            )

            # Input Area
            with gr.Row(elem_classes="input-container"):
                msg = gr.Textbox(
                    show_label=False,
                    placeholder=(
                        " Type your message here... "
                        "(Press Enter to send)"
                    ),
                    lines=2,
                    max_lines=6,
                    scale=9,
                )
                send_btn = gr.Button(
                    "➤", scale=1, variant="primary", size="lg"
                )

    # Event Handlers

    # Text input submission
    msg_submit = (
        msg.submit(
            handle_user_message, [msg, chatbot], [chatbot], queue=False
        )
        .then(
            show_chat_and_clear_textbox,
            [chatbot],
            [initial_view, chatbot, msg],
        )
        .then(chat_response_stream, [chatbot], [chatbot])
    )

    # Send button click
    send_click = (
        send_btn.click(
            handle_user_message, [msg, chatbot], [chatbot], queue=False
        )
        .then(
            show_chat_and_clear_textbox,
            [chatbot],
            [initial_view, chatbot, msg],
        )
        .then(chat_response_stream, [chatbot], [chatbot])
    )

    # New chat button
    all_history_components = []
    for i in range(10):
        all_history_components.append(history_buttons[i])
        all_history_components.append(delete_buttons[i])

    new_chat_btn.click(
        save_and_clear_session,
        [chatbot, all_chats],
        [all_chats, chatbot, initial_view] + all_history_components,
    )

    # History load buttons
    for i, btn in enumerate(history_buttons):
        btn.click(
            load_chat_history,
            inputs=[chatbot, all_chats, gr.State(i)],
            outputs=[all_chats, chatbot, initial_view],
        )

    # Delete buttons for individual chats
    for i, del_btn in enumerate(delete_buttons):
        del_btn.click(
            delete_chat_history,
            inputs=[all_chats, gr.State(i), chatbot],
            outputs=[
                all_chats,
                chatbot,
                initial_view,
            ]
            + all_history_components,
        )

    # Clear all history button
    clear_all_btn.click(
        clear_all_history,
        inputs=[all_chats, chatbot],
        outputs=[all_chats, chatbot, initial_view]
        + all_history_components,
    )

    # Prompt card buttons
    prompts = [
        ("Explain quantum computing in simple terms", prompt1),
        (
            "Got any creative ideas for a 10 year old's birthday?",
            prompt2,
        ),
        ("How do I make an HTTP request in JavaScript?", prompt3),
        ("Write a poem about artificial intelligence", prompt4),
    ]

    for prompt_text, prompt_btn in prompts:
        (
            prompt_btn.click(
                handle_user_message,
                [gr.State(prompt_text), chatbot],
                [chatbot],
                queue=False,
            )
            .then(
                show_chat_and_clear_textbox,
                [chatbot],
                [initial_view, chatbot, msg],
            )
            .then(chat_response_stream, [chatbot], [chatbot])
        )


if __name__ == "__main__":
    print("=" * 60)
    print(" Starting Gemini Chat AI Application...")
    print("=" * 60)

    if not model:
        print("\n  WARNING: Model not initialized!")
        print(" Please ensure your .env file contains:")
        print("   GOOGLE_API_KEY=your_actual_api_key")
        print("\n Get your API key from:")
        print("   https://aistudio.google.com/app/apikey")
    else:
        print("\n Model initialized successfully!")
        print("🤖 Using: Gemini Pro")

    print("\n Features enabled:")
    print("   • Real-time streaming responses")
    print("   • Chat history management")
    print("   • Individual chat deletion")
    print("   • Clear all history")
    print("   • Markdown rendering")
    print("   • Copy response button")

    print("\n Opening in browser...")
    print(" Debug mode: Enabled")
    print("=" * 60)

    demo.queue().launch(
        debug=True,
        show_error=True,
        inbrowser=True,
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
    )

