from __future__ import annotations

import os
from pathlib import Path
from typing import List

from langchain_core.documents import Document

CATEGORY_KEYWORDS = {
    "cefr": "cefr",
    "grammar": "grammar",
    "interview": "interview",
    "vocabulary": "vocabulary",
    "email": "email",
    "errors": "errors",
}


def infer_file_category(filename: str) -> str:
    name = filename.lower()
    for keyword, category in CATEGORY_KEYWORDS.items():
        if keyword in name:
            return category
    return "unknown"


def load_documents(folder_path: str) -> List[Document]:
    folder = Path(folder_path)
    docs: List[Document] = []

    for file_path in folder.rglob("*.md"):
        if not file_path.is_file():
            continue

        source_file = file_path.name
        with file_path.open("r", encoding="utf-8") as fd:
            text = fd.read()

        metadata = {
            "source_file": source_file,
            "full_path": str(file_path.resolve()),
            "file_category": infer_file_category(source_file),
        }

        docs.append(Document(page_content=text, metadata=metadata))

    filenames = [doc.metadata["source_file"] for doc in docs]
    print(f"Loaded {len(docs)} files:")
    for name in filenames:
        print(f"- {name}")
    return docs


if __name__ == "__main__":
    load_documents("knowledge_base")
