#main.py 負責構建 RAG 鏈。

import os
import chromadb
from dotenv import load_dotenv

from langchain_together import TogetherEmbeddings, ChatTogether
from langchain.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
db_directory = "database"
db_path = os.path.join(db_directory, "processed_documents.db")
vector_db_dir = "vector_db_chroma"
collection_name = "my_instrument_manual_chunks"

# Ensure TOGETHER_API_KEY is set
together_api_key = os.getenv("TOGETHER_API_KEY")
if not together_api_key:
    # 更好的錯誤處理：直接拋出異常，應用啟動就會失敗，避免後續問題
    raise ValueError("TOGETHER_API_KEY environment variable not set. Please set it in your .env file.")

# --- LLM Setup ---
try:
    llm = ChatTogether(
        model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", # 或您選擇的其他 Together AI 模型
        temperature=0.3,
        api_key=together_api_key
    )
    print("LLM (Together AI) Instantiation succeeded.")
except Exception as e:
    llm = None
    print(f"Error instantiating LLM: {e}")
    print("Please check your TOGETHER_API_KEY and model name.")

# --- Retriever Setup ---
embeddings_model_name = "togethercomputer/m2-bert-80M-2k-retrieval" # 必須與 setup_knowledge_base.py 中使用的模型一致

try:
    retriever_embeddings = TogetherEmbeddings(
        model=embeddings_model_name,
        api_key=together_api_key
    )

    # Instantiate ChromaDB client and load the collection
    client = chromadb.PersistentClient(path=vector_db_dir)
    vectorstore = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=retriever_embeddings # 用於將查詢嵌入
    )
    # Check if the collection is empty, if so, warn the user to run setup_knowledge_base.py
    if vectorstore._collection.count() == 0:
        print(f"Warning: ChromaDB collection '{collection_name}' is empty. Please run 'python setup_knowledge_base.py' to populate the knowledge base.")
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    print(f"Retriever (ChromaDB) Instantiation succeeded, retrieving {retriever.search_kwargs['k']} chunks.")

except Exception as e:
    retriever = None
    print(f"Error setting up ChromaDB retriever: {e}")
    print("Please ensure you have run 'python setup_knowledge_base.py' to create and populate the vector database.")

# --- Prompt Template Setup ---
answer_prompt = """
You are a professional HPLC instrument troubleshooting expert who specializes in helping junior researchers and students.
Your task is to answer the user's troubleshooting questions in detail and clearly based on the HPLC instrument knowledge provided below.
If there is no direct answer in the knowledge, please provide the most reasonable speculative suggestions based on your expert judgment, or ask further clarifying questions.
Please ensure that your answers are logically clear, easy to understand, and directly address the user's questions.
"""

# --- RAG Chain Construction ---
rag_chain = None # 預設為 None
if llm and retriever: # Only build the chain if both LLM and retriever were successfully initialized
    try:
        # format_docs 函數用於將檢索到的 LangChain Document 對象轉換為字符串
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs if hasattr(doc, 'page_content'))

        # 新的 RAG 鏈結構:
        # 1. 接收一個問題 (str)
        # 2. 將問題傳遞給檢索器 (retriever)，獲取相關文檔
        # 3. 將文檔格式化 (format_docs)
        # 4. 將格式化後的文檔作為 context，原始問題作為 question，填充到 ChatPromptTemplate
        # 5. 將填充後的 prompt 傳遞給 LLM
        # 6. 使用 StrOutputParser() 將 LLM 輸出解析為字符串

        # 修改 Prompt Template
        prompt = ChatPromptTemplate.from_messages([
            ("system", answer_prompt),
            ("user", "Context: {context}\n\nQuestion: {question}"),
        ])
        print("Prompt Template build success.")

        rag_chain = (
            {
                "context": retriever | format_docs,
                "question": RunnablePassthrough() # 這裡將接收到的輸入直接作為 'question' 傳遞
            }
            | prompt
            | llm
            | StrOutputParser()
        )
        print("RAG LangChain assemble success.")
    except Exception as e:
        rag_chain = None
        print(f"Error assembling RAG LangChain: {e}")
        print("Please check previous setup steps for LLM and Retriever.")
else:
    print("RAG LangChain could not be assembled due to LLM or Retriever initialization failure.")

# --- Main execution for testing (optional, for direct script run) ---
if __name__ == "__main__":
    print("--- Running main.py for direct test ---")
    if rag_chain:
        # Example queries for testing
        question_1 = "What are the steps for instrument calibration?"
        print(f"\n--- Executing query: {question_1} ---")
        response_1 = rag_chain.invoke(question_1) # 直接傳遞字符串給 invoke
        print("\nLLM's Answer:")
        print(response_1)

        print("\n--- Executing another query ---")
        question_2 = "How do I troubleshoot common equipment malfunctions?"
        response_2 = rag_chain.invoke(question_2) # 直接傳遞字符串給 invoke
        print("\nLLM's Answer:")
        print(response_2)

        print("\n--- Executing a query that might not have an answer ---")
        question_3 = "How to make Tiramisu cake?"
        response_3 = rag_chain.invoke(question_3) # 直接傳遞字符串給 invoke
        print("\nLLM's Answer:")
        print(response_3)
    else:
        print("RAG chain is not available for testing. Please ensure 'setup_knowledge_base.py' has been run successfully and check API key/model setup in main.py.")