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
from langchain_core.documents import Document # 確保導入 Document 類型

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
    raise ValueError("TOGETHER_API_KEY environment variable not set. Please set it in your .env file.")

# --- LLM Setup ---
llm = ChatTogether(
    model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", # 或您選擇的其他 Together AI 模型
    temperature=0.3,
    api_key=together_api_key
)
print("LLM (Together AI) Instantiation succeeded.")

# --- Retriever Setup ---
embeddings_model_name = "togethercomputer/m2-bert-80M-2k-retrieval" # 必須與 setup_knowledge_base.py 中使用的模型一致

retriever_embeddings = TogetherEmbeddings(
    model=embeddings_model_name,
    api_key=together_api_key
)

# Instantiate ChromaDB client and load the collection
try:
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
    print(f"Error setting up ChromaDB retriever: {e}")
    print("Please ensure you have run 'python setup_knowledge_base.py' to create and populate the vector database.")
    # Fallback or raise error if critical for app function
    retriever = None # Or handle more gracefully

# --- Prompt Template Setup ---
answer_prompt = """
You are a professional HPLC instrument troubleshooting expert who specializes in helping junior researchers and students.
Your task is to answer the user's troubleshooting questions in detail and clearly based on the HPLC instrument knowledge provided below.
If there is no direct answer in the knowledge, please provide the most reasonable speculative suggestions based on your expert judgment, or ask further clarifying questions.
Please ensure that your answers are logically clear, easy to understand, and directly address the user's questions.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", answer_prompt),
    ("user", "context: {context}\n\nquestion: {question}"),
])
print("Prompt Template build success.")

# --- RAG Chain Construction ---
def format_docs(docs):
    # Ensure docs are indeed Document objects or have a page_content attribute
    return "\n\n".join(doc.page_content for doc in docs if hasattr(doc, 'page_content'))

if retriever: # Only build the chain if retriever was successfully initialized
    document_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    print("RAG LangChain assemble success.")
else:
    rag_chain = None # Set to None if retriever failed to initialize
    print("RAG LangChain could not be assembled due to retriever initialization failure.")


# --- Main execution for testing (optional, for direct script run) ---
if __name__ == "__main__":
    print("--- Running main.py for direct test ---")
    if rag_chain:
        # Example queries for testing
        question_1 = "What are the steps for instrument calibration?"
        print(f"\n--- Executing query: {question_1} ---")
        response_1 = rag_chain.invoke(question_1)
        print("\nLLM's Answer:")
        print(response_1)

        print("\n--- Executing another query ---")
        question_2 = "How do I troubleshoot common equipment malfunctions?"
        response_2 = rag_chain.invoke(question_2)
        print("\nLLM's Answer:")
        print(response_2)

        print("\n--- Executing a query that might not have an answer ---")
        question_3 = "How to make Tiramisu cake?"
        response_3 = rag_chain.invoke(question_3)
        print("\nLLM's Answer:")
        print(response_3)
    else:
        print("RAG chain is not available. Please ensure 'setup_knowledge_base.py' has been run successfully.")