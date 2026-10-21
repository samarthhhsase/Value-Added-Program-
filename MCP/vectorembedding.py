from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from loaddocument import chunks

if not chunks:
    raise ValueError("No document chunks were created. Check that the PDFs contain extractable text.")

# 1. Initialize the Ollama embeddings model
embeddings = OllamaEmbeddings(model="qwen3-embedding:0.6b")

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db",
)

print("Vector Database created and persisted locally")
