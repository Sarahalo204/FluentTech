import os
import sys
from pathlib import Path
from langchain_core.documents import Document
from rag.chunker import chunk_documents
from rag.embedder import build_vector_store

def ingest_data():
    print("[+] Building vector store with legacy inline knowledge...")
    
    # Legacy documents
    documents = [
        "Past tense rules for regular verbs: Add '-ed' to the base form (e.g., talk -> talked, walk -> walked). For verbs ending in '-e', add '-d' (e.g., like -> liked). For irregular verbs, the past tense form varies (e.g., go -> went, see -> saw, write -> wrote).",
        "Subject-verb agreement rules: Singular subjects require singular verbs (e.g., 'He speaks English', 'The server runs smoothly'), while plural subjects require plural verbs (e.g., 'They speak English', 'The servers run smoothly').",
        "Indefinite articles 'a' vs 'an' rules: Use 'a' before words starting with consonant sounds (e.g., 'a software engineer', 'a cloud database') and 'an' before words starting with vowel sounds (e.g., 'an AI model', 'an API endpoint')."
    ]
    
    docs = []
    sources = ["grammar_past_tense", "grammar_subject_verb", "grammar_articles"]
    
    for i, text in enumerate(documents):
        metadata = {
            "source_file": sources[i] + ".md",
            "file_category": "grammar",
        }
        docs.append(Document(page_content=text, metadata=metadata))
        
    print("[+] Chunking documents...")
    chunks = chunk_documents(docs)
    
    project_root = Path(__file__).resolve().parent
    persist_dir = project_root / "chroma_db"
    
    print(f"[+] Embedding chunks and storing in Chroma at {persist_dir}...")
    build_vector_store(chunks, persist_dir=str(persist_dir))
    
    print("[+] Ingestion complete successfully!")

if __name__ == "__main__":
    ingest_data()
