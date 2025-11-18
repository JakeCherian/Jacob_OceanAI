from typing import List, Dict, Any, Optional
import os

from .parser import parse_document
from .vectorstore import VectorStore


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> List[str]:
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
        if start < 0:
            start = 0
    return chunks


class KnowledgeBase:
    def __init__(self, persist_dir: str = "data/chroma"):
        self.store = VectorStore(persist_dir=persist_dir)
        self._html_content: Optional[str] = None
        self._html_filename: Optional[str] = None

    def build(self, documents: List[Dict[str, Any]], html_document: Optional[Dict[str, Any]] = None):
        """
        documents: list of {filename: str, content: bytes}
        html_document: optional {filename: str, content: bytes}
        """
        chunks_to_add: List[Dict[str, Any]] = []

        if html_document:
            parsed = parse_document(html_document["filename"], html_document["content"])
            self._html_content = parsed["text"] if parsed else None
            self._html_filename = html_document["filename"]
            # Also add HTML text to store for retrieval
            for idx, ch in enumerate(chunk_text(parsed.get("text", ""))):
                chunks_to_add.append({
                    "id": f"html-{idx}",
                    "text": ch,
                    "source_document": html_document["filename"],
                    "chunk_index": idx,
                    "metadata": parsed.get("metadata", {}),
                })

        for doc in documents:
            parsed = parse_document(doc["filename"], doc["content"])
            for idx, ch in enumerate(chunk_text(parsed.get("text", ""))):
                chunks_to_add.append({
                    "id": f"{doc['filename']}-{idx}",
                    "text": ch,
                    "source_document": doc["filename"],
                    "chunk_index": idx,
                    "metadata": parsed.get("metadata", {}),
                })

        if chunks_to_add:
            self.store.add_chunks(chunks_to_add)

    def retrieve(self, query: str, top_k: int = 6) -> List[Dict[str, Any]]:
        return self.store.query(query_text=query, top_k=top_k)

    def get_html(self) -> Optional[str]:
        return self._html_content

    def has_html(self) -> bool:
        return self._html_content is not None