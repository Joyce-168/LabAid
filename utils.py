#主要從 main導入路徑

from main import rag_chain # 確保你有 __init__.py 或 main.py 是可引用的模組
import gradio as gr

def format_history(history):
    """Format (user, assistant) message pairs into a text block."""
    formatted_parts = []
    for user, assistant in history:
        if user:
            formatted_parts.append(f"User: {user}")
        if assistant:
            formatted_parts.append(f"Assistant: {assistant}")
    return "\n".join(formatted_parts)


def generate_answer(prompt_text, chat_history_list):
    """
    Combines chat history and user input, then queries the RAG chain.
    """
    # 這裡可以根據需要調整歷史消息的處理方式，例如只傳遞最近的N條消息
    formatted_chat_history = format_history(chat_history_list)
    
    # 組合完整的用戶問題，考慮歷史上下文
    # 確保只有當有歷史消息時才包含它們
    if formatted_chat_history:
        full_question = f"{formatted_chat_history}\nUser: {prompt_text.strip()}"
    else:
        full_question = prompt_text.strip() # 沒有歷史消息時只傳遞當前問題

    print(f"[Debug] Full Question:\n{full_question}\n")

    if not prompt_text.strip():
        return "Please enter a question."

    if len(full_question) > 8000: # 調整長度限制，以適應 LLM 的上下文窗口
        return "The question and chat history are too long. Please shorten them."

    try:
        # LLM 的提示模板應該處理 'question' 變量
        # 你的 prompt 定義是 ("user", "context: {context}\n\nquestion: {question}"),
        # 因此，直接將 full_question 傳遞給 'question' 即可
        result = rag_chain.invoke({"question": full_question})

        if isinstance(result, str):
            return result
        else:
            print(f"Warning: Unexpected return type from rag_chain: {type(result)} - {result}")
            return "Unexpected response format from the AI."
    except Exception as e:
        print(f"[Error] Failed to generate answer: {e}")
        return f"An error occurred while generating the answer: {str(e)}"