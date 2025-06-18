#這個文件將負責所有的數據準備工作。在運行 app.py 之前，你需要先執行這個文件一次。
import re
import os
import sqlite3
import datetime
import chromadb

from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from together import Together
from langchain_together import TogetherEmbeddings
from chromadb.utils import embedding_functions
from langchain_core.documents import Document


def extract_text_from_pdf(pdf_path):
    """
    Extract all text content from PDF files.
    """
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text += page.extract_text() + "\n"  # 提取每頁文字並換行
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return text

def clean_text_content(text):
    """
    Remove irrelevant content, such as copyright information, legal notices, and long blank spaces.
    """
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s+\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'Copyright © \d{4} [^\n]*\. All Rights Reserved\.', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Confidential and Proprietary Information[^\n]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Disclaimer:[^.]*\.', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def standardize_text_format(text):
    """
    Try to organize everything into clear paragraphs.
    """
    text = re.sub(r'([a-zA-Z])-(\n)([a-zA-Z])', r'\1\3', text)
    text = re.sub(r'([.?!])\s*([A-Z])', r'\1  \2', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'([^\n])\n([^\n])', r'\1 \2', text)
    text = re.sub(r'\n{2,}', '\n\n', text)
    return text

def create_database_table(db_path):
    """
    Create a SQLite database and define the table structure.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_filename TEXT NOT NULL UNIQUE, -- Add UNIQUE constraint
            source_type TEXT,
            processed_text TEXT NOT NULL,
            processed_date TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print(f"SQLite table 'documents' ensured in {db_path}")

def create_chunks_table(db_path):
    """
    Create a table to store the segmented text blocks.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            chunk_content TEXT NOT NULL,
            chunk_length INTEGER,
            created_at TEXT,
            UNIQUE(document_id, chunk_index), -- Ensure chunks are unique per document
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    ''')
    conn.commit()
    conn.close()
    print(f"SQLite table 'chunks' ensured in {db_path}")

def insert_document_data(db_path, original_filename, source_type, processed_text, processed_date):
    """
    Insert the processed file data into the database.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # 檢查是否已存在相同的原始文件
    cursor.execute("SELECT id FROM documents WHERE original_filename = ?", (original_filename,))
    existing_doc = cursor.fetchone()
    if existing_doc:
        print(f"Document '{original_filename}' already exists in DB (ID: {existing_doc[0]}). Skipping insertion.")
        conn.close()
        return existing_doc[0]
    else:
        cursor.execute('''
            INSERT INTO documents (original_filename, source_type, processed_text, processed_date)
            VALUES (?, ?, ?, ?)
        ''', (original_filename, source_type, processed_text, processed_date))
        conn.commit()
        doc_id = cursor.lastrowid
        conn.close()
        print(f"Document '{original_filename}' saved to database: {db_path} with ID: {doc_id}")
        return doc_id

def get_document_text_from_db(db_path, document_id=None, limit=None):
    """
    Reads the processed text contents of one or more files from a SQLite database.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        query = "SELECT id, processed_text FROM documents"
        params = []
        if document_id:
            query += " WHERE id = ?"
            params.append(document_id)
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        cursor.execute(query, params)
        if document_id:
            row = cursor.fetchone()
            if row:
                return {'id': row[0], 'processed_text': row[1]}
            return None
        else:
            return [{'id': row[0], 'processed_text': row[1]} for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Error reading from SQLite database: {e}")
        return []
    finally:
        if conn:
            conn.close()

def chunk_text(text, chunk_size=500, chunk_overlap=100): # Adjusted chunk size and overlap for potentially smaller chunks
    """
    Splits the text using RecursiveCharacterTextSplitter.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        add_start_index=True
    )
    chunks = text_splitter.create_documents([text])
    return [chunk.page_content for chunk in chunks]

def insert_chunks_to_db(db_path, document_id, chunks):
    """
    Inserts all text blocks from the specified file into the database.
    Checks if chunks for this document_id already exist and skips if found.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    current_time = datetime.datetime.now().isoformat()

    # Check if chunks for this document_id already exist
    cursor.execute("SELECT COUNT(*) FROM chunks WHERE document_id = ?", (document_id,))
    if cursor.fetchone()[0] > 0:
        print(f"Chunks for document ID {document_id} already exist. Skipping chunk insertion.")
        conn.close()
        return

    data_to_insert = []
    for i, chunk in enumerate(chunks):
        data_to_insert.append((document_id, i, chunk, len(chunk), current_time))

    cursor.executemany('''
        INSERT INTO chunks (document_id, chunk_index, chunk_content, chunk_length, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', data_to_insert)
    conn.commit()
    conn.close()
    print(f"Saved {len(chunks)} chunks into the database for file ID {document_id}.")

def generate_embeddings(texts, model_name="togethercomputer/m2-bert-80M-32k-retrieval"):
    """
    Generates text embeddings using Together AI's embedding model.
    """
    try:
        embeddings_model = TogetherEmbeddings(
            model=model_name,
            api_key=os.getenv("TOGETHER_API_KEY")
        )
        vectors = embeddings_model.embed_documents(texts)
        print(f"Successfully generated embeddings for {len(texts)} text chunks using {model_name}.")
        return vectors
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return []

def get_chunks_from_db_for_embedding(db_path):
    """
    Reads all split text chunks from the SQLite database, including their IDs.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, document_id, chunk_index, chunk_content FROM chunks ORDER BY document_id, chunk_index")
        rows = cursor.fetchall()
        return [{'id': row[0], 'source_document_id': row[1], 'chunk_index': row[2], 'text': row[3]} for row in rows]
    except sqlite3.Error as e:
        print(f"Error reading chunks from SQLite database: {e}")
        return []
    finally:
        if conn:
            conn.close()

def load_chunks_to_vector_db(chunks_data, db_path="vector_db_chroma", collection_name="document_chunks", embeddings_model_name="togethercomputer/m2-bert-80M-32k-retrieval"):
    """
    Loads text chunks and their embeddings into a ChromaDB vector database.
    This function will now ADD chunks if they are new (based on their IDs).
    """
    try:
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_or_create_collection(name=collection_name)

        # Check existing IDs in ChromaDB to avoid adding duplicates
        existing_chroma_ids = set()
        if collection.count() > 0:
            # Fetching all existing IDs can be slow for very large collections.
            # A more efficient approach for very large databases might involve
            # querying a batch of IDs or checking after insertion.
            # For now, this is simpler for demonstration.
            try:
                all_ids_in_chroma = collection.get(ids=collection.get()['ids'])['ids']
                existing_chroma_ids = set(all_ids_in_chroma)
            except Exception as e:
                print(f"Warning: Could not retrieve all existing IDs from ChromaDB. May attempt to add duplicates. Error: {e}")


        ids_to_add = []
        documents_to_add = []
        embeddings_to_add = []
        metadatas_to_add = []

        for item in chunks_data:
            chunk_id_str = str(item['id'])
            if chunk_id_str not in existing_chroma_ids:
                ids_to_add.append(chunk_id_str)
                documents_to_add.append(item['text'])
                embeddings_to_add.append(item['embedding'])
                metadatas_to_add.append({"source_document_id": item.get('source_document_id', 'unknown'),
                                        "chunk_index": item.get('chunk_index', None)})
            else:
                print(f"Chunk ID {chunk_id_str} already exists in ChromaDB. Skipping.")

        if ids_to_add:
            collection.add(
                embeddings=embeddings_to_add,
                documents=documents_to_add,
                metadatas=metadatas_to_add,
                ids=ids_to_add
            )
            print(f"Successfully added {len(ids_to_add)} new text chunks into ChromaDB collection '{collection_name}'.")
        else:
            print(f"No new chunks to add to ChromaDB collection '{collection_name}'.")

    except Exception as e:
        print(f"Error loading data into ChromaDB: {e}")


if __name__ == "__main__":
    # Define the directory containing your PDF files
    pdf_input_directory = "input" # Ensure this directory exists and contains your PDFs
    db_directory = "database"
    db_path = os.path.join(db_directory, "processed_documents.db")
    vector_db_dir = "vector_db_chroma"
    collection_name = "my_instrument_manual_chunks"
    embeddings_model_name = "togethercomputer/m2-bert-80M-32k-retrieval" # 確保與 main.py 中使用的一致

    # Create necessary directories
    os.makedirs(db_directory, exist_ok=True)
    os.makedirs(vector_db_dir, exist_ok=True)

    print("--- Starting knowledge base setup ---")

    # 1. 確保 SQLite 表格存在
    create_database_table(db_path)
    create_chunks_table(db_path)

    # 2. 遍歷指定目錄下的所有 PDF 文件
    pdf_files = [f for f in os.listdir(pdf_input_directory) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print(f"No PDF files found in '{pdf_input_directory}'. Please place your PDF documents there.")
    
    for pdf_filename in pdf_files:
        pdf_full_path = os.path.join(pdf_input_directory, pdf_filename)
        print(f"\n--- Processing PDF: {pdf_full_path} ---")

        # 檢查文件是否已在 documents 表中處理過
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM documents WHERE original_filename = ?", (pdf_filename,))
        existing_doc_id = cursor.fetchone()
        conn.close()

        if existing_doc_id:
            doc_id = existing_doc_id[0]
            print(f"Document '{pdf_filename}' already in 'documents' table with ID: {doc_id}. Skipping PDF extraction and text processing.")
            # Still process chunks if they aren't in 'chunks' table or ChromaDB
        else:
            pdf_content = extract_text_from_pdf(pdf_full_path)
            if pdf_content:
                cleaned_text = clean_text_content(pdf_content)
                final_processed_text = standardize_text_format(cleaned_text)
                current_date = datetime.date.today().isoformat()
                doc_id = insert_document_data(db_path, pdf_filename, "PDF", final_processed_text, current_date)
            else:
                print(f"No content extracted from {pdf_full_path}. Skipping document insertion for this PDF.")
                continue # Move to the next PDF if no content

        # 如果 doc_id 存在（無論是新插入還是已存在的），則進行分塊和嵌入處理
        if doc_id is not None:
            # 從 SQLite documents 表讀取並分塊，存儲到 SQLite chunks 表
            document_from_db = get_document_text_from_db(db_path, document_id=doc_id)
            if document_from_db:
                full_text = document_from_db['processed_text']
                print(f"--- Chunking document ID {doc_id} ('{pdf_filename}') ---")
                chunks = chunk_text(full_text, chunk_size=500, chunk_overlap=100) # Re-evaluate chunk_size
                if chunks:
                    insert_chunks_to_db(db_path, doc_id, chunks)
                else:
                    print(f"Document ID {doc_id} unable to split any chunks.")
            else:
                print(f"Could not retrieve processed text for document ID {doc_id}.")

    # 3. 從 SQLite chunks 表讀取所有塊並生成嵌入，載入到 ChromaDB
    # 我們需要重新從 DB 獲取所有 chunks，因為可能有多個 PDF 的 chunks
    chunks_from_db_for_embedding = get_chunks_from_db_for_embedding(db_path)

    if chunks_from_db_for_embedding:
        # Filter out chunks that already have an embedding in ChromaDB if checking was efficient
        # For simplicity, we'll try to generate embeddings for all chunks retrieved from SQLite
        # and let load_chunks_to_vector_db handle duplicates in ChromaDB.
        texts_to_embed = [item['text'] for item in chunks_from_db_for_embedding]
        print(f"\n--- Generating embeddings for {len(texts_to_embed)} total chunks ---")
        text_embeddings = generate_embeddings(texts_to_embed, model_name=embeddings_model_name)

        if text_embeddings:
            data_for_vector_db = []
            for i, chunk_data in enumerate(chunks_from_db_for_embedding):
                if i < len(text_embeddings):
                    chunk_data['embedding'] = text_embeddings[i]
                    data_for_vector_db.append(chunk_data)
                else:
                    print(f"Warning: Missing embedding for chunk {chunk_data['id']}. Skipping this chunk for ChromaDB.")

            print(f"--- Loading/Updating {len(data_for_vector_db)} chunks into ChromaDB ---")
            load_chunks_to_vector_db(data_for_vector_db, db_path=vector_db_dir, collection_name=collection_name, embeddings_model_name=embeddings_model_name)
        else:
            print("No embeddings generated. Skipping ChromaDB loading.")
    else:
        print("No text chunks read from the database for embedding and loading into ChromaDB.")

    print("\n--- Knowledge base setup complete ---")