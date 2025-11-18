# Autonomous QA Agent for Test Case and Script Generation

An intelligent QA agent that builds a testing knowledge base from project documentation and a target `checkout.html`, generates grounded test cases (JSON/Markdown), and converts selected test cases into runnable Python Selenium scripts.

## Features
- Upload support documents (MD/TXT/JSON/PDF) and target `checkout.html`
- Build a knowledge base with text chunking, embeddings, and vector search (ChromaDB)
- RAG-based agent generates structured test cases grounded strictly in provided docs
- Select a test case to generate a runnable Selenium Python script with real selectors
- Backend implemented with FastAPI; Streamlit UI for simple workflows

## Tech Stack
- UI: Streamlit
- Backend: FastAPI (optional local-mode used by Streamlit for preview)
- Vector DB: ChromaDB with SentenceTransformers (`all-MiniLM-L6-v2`)
- Parsers: BeautifulSoup4 (HTML), builtin readers (MD/TXT/JSON), PyMuPDF (PDF)
- LLM: Pluggable (Ollama via HTTP). Fallback template mode when no LLM configured.

## Project Structure
```
assets/
  checkout.html
backend/
  app.py
docs/
  product_specs.md
  ui_ux_guide.txt
  api_endpoints.json
qa_agent/
  __init__.py
  knowledge_base.py
  parser.py
  vectorstore.py
  llm.py
  agent.py
  script_generator.py
ui/
  streamlit_app.py
requirements.txt
README.md
```

## Setup
- Python: 3.10+ recommended

### 1) Create virtual environment (Windows PowerShell)
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2) Optional: Configure LLM provider
- Ollama: install Ollama and ensure a model is available (e.g., `llama3`, `qwen2.5`) and server is running on `http://localhost:11434`.
- If no LLM is available, the app falls back to a deterministic template generator.

## Running

### Streamlit UI (recommended for demo)
```
streamlit run ui/streamlit_app.py
```

### FastAPI Backend (optional)
```
uvicorn backend.app:app --reload --port 8000
```

## Usage
1. Open the Streamlit app.
2. Upload 3–5 support documents (or use the included examples).
3. Upload or paste the provided `checkout.html` (or use the included example).
4. Click "Build Knowledge Base" to ingest documents and HTML.
5. In the Agent section, enter a request (e.g., "Generate all positive and negative test cases for the discount code feature.")
6. Review generated test cases with clear grounding references.
7. Select a test case and click "Generate Selenium Script" to download a runnable Python script.

## Included Support Documents
- `product_specs.md`
  - Contains feature rules (e.g., SAVE15 applies 15% discount, shipping costs)
- `ui_ux_guide.txt`
  - Provides UI/UX guidelines (colors, validation behavior)
- `api_endpoints.json`
  - Example endpoints for coupon and order submission

## Notes
- All test reasoning is grounded strictly in the provided documents. The agent includes document citations for each test case.
- The generated Selenium scripts use IDs and selectors present in the provided `checkout.html`.
- If you use your own `checkout.html`, ensure elements have stable attributes (IDs/names) for reliable selectors.
