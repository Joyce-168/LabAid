#主要從 main導入路徑
from main import rag_chain  # 確保你有 __init__.py 或 main.py 是可引用的模組
import gradio as gr

def format_history(history):
    """
    Format chat history from Gradio's new messages format
    [{'role': 'user', 'content': '...'}, {'role': 'assistant', 'content': '...'}]
    into a plain text block for the LLM.
    """
    formatted_parts = []
    for message in history:
        if message['role'] == 'user':
            formatted_parts.append(f"User: {message['content']}")
        elif message['role'] == 'assistant':
            formatted_parts.append(f"Assistant: {message['content']}")
    return "\n".join(formatted_parts)


def generate_answer(prompt_text, chat_history_list):
    """
    Combines chat history and user input, then queries the RAG chain.
    """
    # chat_history_list 現在是 Gradio 提供的新的字典列表格式
    formatted_chat_history = format_history(chat_history_list)
    
    # 組合完整的用戶問題，考慮歷史上下文
    # 確保只有當有歷史消息時才包含它們
    if formatted_chat_history:
        # 將歷史和當前問題組合成一個連貫的輸入，給到 LLM 的 question 部分
        # 這裡不應該加 "Assistant:"，因為這是用戶在問，不是模型要回答的開始
        full_question = f"{formatted_chat_history}\nUser: {prompt_text.strip()}"
    else:
        full_question = prompt_text.strip() # 沒有歷史消息時只傳遞當前問題

    print(f"[Debug] Full Question:\n{full_question}\n")

    if not prompt_text.strip():
        return "Please enter a question."

    # 調整長度限制，以適應 LLM 的上下文窗口，並給檢索結果留空間
    # 10000 字符可能過大，建議根據 Together AI 模型實際輸入限制調整，
    # 尤其是當上下文(context)也很大時。可以調低到 4000-6000 字符。
    if len(full_question) > 6000: 
        return "The question and chat history are too long. Please shorten them."

    try:
        # 檢查 rag_chain 是否已成功初始化
        if rag_chain is None:
            return "AI system not initialized. Please ensure 'python setup_knowledge_base.py' ran successfully and check your API key."

        # rag_chain.invoke({"question": full_question}) 傳遞給 LLM
        # 預期 rag_chain 返回的是字符串
        result = rag_chain.invoke(full_question) # rag_chain 現在直接接受一個 string

        if isinstance(result, str):
            return result
        else:
            print(f"Warning: Unexpected return type from rag_chain: {type(result)} - {result}")
            return "Unexpected response format from the AI."
    except Exception as e:
        print(f"[Error] Failed to generate answer: {e}")
        # 更詳細的錯誤提示給用戶
        return f"An error occurred while generating the answer: {str(e)}\n\nPlease check your API key, model availability, or the setup of your knowledge base."