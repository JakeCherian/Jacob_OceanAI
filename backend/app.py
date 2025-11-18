from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from qa_agent.knowledge_base import KnowledgeBase
from qa_agent.llm import LLMProvider
from qa_agent.agent import generate_test_cases
from qa_agent.script_generator import generate_selenium_script


app = FastAPI(title="Autonomous QA Agent Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

kb = KnowledgeBase()
llm = LLMProvider()


class DocItem(BaseModel):
    filename: str
    content: str  # base64 or plain text; we will treat as plain text here


class BuildKBRequest(BaseModel):
    documents: List[DocItem]
    html_document: Optional[DocItem] = None


@app.post("/build_kb")
async def build_kb(req: BuildKBRequest):
    docs = [{"filename": d.filename, "content": d.content.encode("utf-8") } for d in req.documents]
    html_doc = None
    if req.html_document:
        html_doc = {"filename": req.html_document.filename, "content": req.html_document.content.encode("utf-8")}
    kb.build(docs, html_document=html_doc)
    return {"status": "ok", "message": "Knowledge Base Built"}


@app.post("/build_kb/upload")
async def build_kb_upload(files: List[UploadFile] = File(default=[]), html: UploadFile | None = File(default=None)):
    docs = []
    for f in files:
        content = await f.read()
        docs.append({"filename": f.filename, "content": content})
    html_doc = None
    if html is not None:
        html_doc = {"filename": html.filename, "content": await html.read()}
    kb.build(docs, html_document=html_doc)
    return {"status": "ok", "message": "Knowledge Base Built"}


class TestCaseRequest(BaseModel):
    query: str


@app.post("/generate_test_cases")
async def api_generate_test_cases(req: TestCaseRequest):
    out = generate_test_cases(req.query, kb, llm)
    return {"status": "ok", "data": out}


class SeleniumScriptRequest(BaseModel):
    test_case: Dict[str, Any]


@app.post("/generate_selenium_script")
async def api_generate_selenium_script(req: SeleniumScriptRequest):
    html_text = kb.get_html() or ""
    code = generate_selenium_script(req.test_case, html_text, kb, llm)
    return {"status": "ok", "code": code}