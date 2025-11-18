import os
import json
import io
import streamlit as st

from qa_agent.knowledge_base import KnowledgeBase
from qa_agent.llm import LLMProvider
from qa_agent.agent import generate_test_cases
from qa_agent.script_generator import generate_selenium_script


st.set_page_config(page_title="Autonomous QA Agent", layout="wide")
st.title("Autonomous QA Agent for Test Case and Script Generation")

if "kb" not in st.session_state:
    # Lazy-init KB to avoid startup failures before dependencies are installed
    st.session_state.kb = None
if "llm" not in st.session_state:
    st.session_state.llm = LLMProvider()
if "built" not in st.session_state:
    st.session_state.built = False
if "last_tests" not in st.session_state:
    st.session_state.last_tests = ""
if "html_text" not in st.session_state:
    st.session_state.html_text = None


with st.sidebar:
    st.header("Assets")
    st.markdown("Use included assets or upload your own.")
    here = os.path.dirname(os.path.dirname(__file__))
    default_html_path = os.path.join(here, "assets", "checkout.html")
    st.text_input("Default checkout.html path", value=default_html_path, disabled=True)

st.subheader("Phase 1: Knowledge Base Ingestion")
col1, col2 = st.columns(2)
with col1:
    uploaded_docs = st.file_uploader("Upload support documents (MD/TXT/JSON/PDF)", type=["md","txt","json","pdf"], accept_multiple_files=True)
    use_example_docs = st.checkbox("Use included example docs", value=True)
with col2:
    uploaded_html = st.file_uploader("Upload checkout.html", type=["html","htm"], accept_multiple_files=False)
    use_example_html = st.checkbox("Use included checkout.html", value=True)

if st.button("Build Knowledge Base"):
    docs = []
    if use_example_docs:
        docs_dir = os.path.join(here, "docs")
        for name in ["product_specs.md", "ui_ux_guide.txt", "api_endpoints.json"]:
            p = os.path.join(docs_dir, name)
            with open(p, "rb") as f:
                docs.append({"filename": name, "content": f.read()})
    for f in uploaded_docs or []:
        docs.append({"filename": f.name, "content": f.getvalue()})

    html_doc = None
    if use_example_html and os.path.exists(default_html_path):
        with open(default_html_path, "rb") as f:
            html_doc = {"filename": "checkout.html", "content": f.read()}
    elif uploaded_html is not None:
        html_doc = {"filename": uploaded_html.name, "content": uploaded_html.getvalue()}

    # Initialize KB on demand
    if st.session_state.kb is None:
        st.session_state.kb = KnowledgeBase()
    st.session_state.kb.build(docs, html_document=html_doc)
    if html_doc:
        # store visible text for script gen context
        st.session_state.html_text = html_doc["content"].decode("utf-8", errors="ignore")
    st.session_state.built = True
    st.success("Knowledge Base Built")

st.divider()
st.subheader("Phase 2: Test Case Generation Agent")
query = st.text_area("Agent prompt", value="Generate all positive and negative test cases for the discount code feature.")

if st.button("Generate Test Cases"):
    if not st.session_state.built:
        st.warning("Build the Knowledge Base first.")
    else:
        if st.session_state.kb is None:
            st.warning("Build the Knowledge Base first.")
        else:
            out = generate_test_cases(query, st.session_state.kb, st.session_state.llm)
            st.session_state.last_tests = out
            st.markdown(out)

if st.session_state.last_tests:
    st.divider()
    st.subheader("Phase 3: Selenium Script Generation Agent")
    st.caption("Paste a single test case in JSON or select one by index if output is a Markdown table.")
    test_case_input = st.text_area("Selected Test Case (JSON)", height=200, placeholder='{"Test_ID": "TC-001", "Feature": "Discount Code", "Test_Scenario": "Apply a valid discount code \"SAVE15\".", "Expected_Result": "Total price is reduced by 15%.", "Grounded_In": "product_specs.md"}')

    if st.button("Generate Selenium Script"):
        try:
            tc = json.loads(test_case_input)
        except Exception:
            st.error("Please provide a valid JSON test case.")
            tc = None
        if tc is not None:
            html_text = st.session_state.html_text or ((st.session_state.kb.get_html() if st.session_state.kb else "") or "")
            code = generate_selenium_script(tc, html_text, st.session_state.kb, st.session_state.llm)
            st.code(code, language="python")
            st.download_button("Download Script", data=code, file_name=f"{tc.get('Test_ID','test')}.py")