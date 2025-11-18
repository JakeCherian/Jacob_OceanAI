from typing import List, Dict, Any

from .knowledge_base import KnowledgeBase
from .llm import LLMProvider


SYSTEM_PROMPT_TESTS = (
    "You are a QA Test Case generation agent. "
    "Respond with structured test plans grounded strictly in provided context. "
    "Include clear citations to source documents. Output as JSON or a Markdown table."
)


def _format_context(chunks: List[Dict[str, Any]]) -> str:
    lines = []
    for i, ch in enumerate(chunks):
        meta = ch.get("metadata", {})
        src = meta.get("source_document", "unknown")
        lines.append(f"[Source: {src}] {ch['text']}")
    return "\n\n".join(lines)


def generate_test_cases(query: str, kb: KnowledgeBase, llm: LLMProvider) -> str:
    retrieved = kb.retrieve(query, top_k=8)
    context = _format_context(retrieved)
    prompt = (
        f"User Request: {query}\n\n"
        f"Context (strictly ground tests here, cite sources):\n{context}\n\n"
        "Return comprehensive positive and negative test cases."
    )
    out = llm.generate(prompt, system=SYSTEM_PROMPT_TESTS)
    return out