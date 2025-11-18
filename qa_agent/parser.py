import io
import json
from typing import Dict, Any

from bs4 import BeautifulSoup


def _decode_bytes(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except Exception:
        return content.decode("latin-1", errors="ignore")


def parse_document(filename: str, content: bytes) -> Dict[str, Any]:
    """
    Parse a document into text with minimal metadata.
    Supports: .md, .txt, .json, .html, .htm, .pdf (basic text extraction via PyMuPDF if available).
    """
    name = filename.lower()
    parsed = {
        "source_document": filename,
        "ext": name.split(".")[-1] if "." in name else "",
        "text": "",
        "metadata": {},
    }

    ext = parsed["ext"]
    raw_text = _decode_bytes(content)

    if ext in {"md", "txt"}:
        parsed["text"] = raw_text
        return parsed

    if ext in {"json"}:
        try:
            obj = json.loads(raw_text)
            # Flatten a bit for retrieval
            flat_lines = []
            def walk(prefix, v):
                if isinstance(v, dict):
                    for k, vv in v.items():
                        walk(f"{prefix}/{k}" if prefix else str(k), vv)
                elif isinstance(v, list):
                    for i, vv in enumerate(v):
                        walk(f"{prefix}[{i}]", vv)
                else:
                    flat_lines.append(f"{prefix}: {v}")
            walk("", obj)
            parsed["text"] = "\n".join(flat_lines)
        except Exception:
            parsed["text"] = raw_text
        return parsed

    if ext in {"html", "htm"}:
        soup = BeautifulSoup(raw_text, "lxml")
        # Visible text
        text = soup.get_text(" ", strip=True)
        parsed["text"] = text
        # Basic selector metadata for later use
        ids = [e.get("id") for e in soup.find_all(attrs={"id": True})]
        names = [e.get("name") for e in soup.find_all(attrs={"name": True})]
        parsed["metadata"]["html_ids"] = [i for i in ids if i]
        parsed["metadata"]["html_names"] = [n for n in names if n]
        return parsed

    if ext in {"pdf"}:
        try:
            import fitz  # PyMuPDF
            with fitz.open(stream=content, filetype="pdf") as doc:
                texts = []
                for page in doc:
                    texts.append(page.get_text())
                parsed["text"] = "\n".join(texts)
        except Exception:
            parsed["text"] = raw_text
        return parsed

    # Fallback for unknown extensions
    parsed["text"] = raw_text
    return parsed