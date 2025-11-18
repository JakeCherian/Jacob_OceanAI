from typing import List, Dict, Any
import os

import chromadb
from chromadb.utils import embedding_functions


class VectorStore:
    def __init__(self, persist_dir: str = "data/chroma", collection_name: str = "knowledgebase"):
        os.makedirs(persist_dir, exist_ok=True)
        # Sanitize name to meet Chroma index naming rules (lowercase alphanumerics, start with letter)
        safe_name = ''.join(ch for ch in collection_name.lower() if ch.isalnum())
        if not safe_name or not safe_name[0].isalpha():
            safe_name = f"kb{safe_name or 'default'}"
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=safe_name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            ),
        )

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        ids = []
        docs = []
        metadatas = []
        for i, ch in enumerate(chunks):
            ids.append(ch.get("id", f"chunk-{len(self.collection)-i}-{i}"))
            docs.append(ch["text"])
            metadatas.append({
                "source_document": ch.get("source_document", "unknown"),
                "chunk_index": ch.get("chunk_index", i),
                **(ch.get("metadata", {})),
            })
        if ids:
            self.collection.add(ids=ids, documents=docs, metadatas=metadatas)

    def query(self, query_text: str, top_k: int = 6) -> List[Dict[str, Any]]:
        res = self.collection.query(query_texts=[query_text], n_results=top_k)
        results = []
        if res and "documents" in res:
            docs = res["documents"][0]
            metas = res["metadatas"][0]
            for d, m in zip(docs, metas):
                results.append({"text": d, "metadata": m})
        return results