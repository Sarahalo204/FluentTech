import os
import sys
from pathlib import Path
from langchain_core.documents import Document
from rag.chunker import chunk_documents
from rag.embedder import build_vector_store

from rag.loader import load_documents

def ingest_data():
    print("[+] Loading documents from knowledge_base...")
    
    project_root = Path(__file__).resolve().parent
    kb_path = project_root / "knowledge_base"
    
    docs = load_documents(str(kb_path))
    if not docs:
        print("[-] No documents found in knowledge base!")
        return
        
    print("[+] Chunking documents...")
    chunks = chunk_documents(docs)
    
    print(f"[+] Embedding chunks and storing in Supabase...")
    build_vector_store(chunks)
    
    print("[+] Ingestion complete successfully!")

if __name__ == "__main__":
    ingest_data()
