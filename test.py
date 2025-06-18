from langchain_together import TogetherEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

emb = TogetherEmbeddings(
    model="togethercomputer/m2-bert-80M-32k-retrieval",
    api_key=os.getenv("TOGETHER_API_KEY")
)
print(emb.embed_documents(["Hello world"]))


print("Key:", os.getenv("TOGETHER_API_KEY")[:5] + "..." if os.getenv("TOGETHER_API_KEY") else None)
