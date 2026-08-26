import os
import streamlit as st
import httpx
import json

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")

st.set_page_config(
    page_title="Cross-Publication Insight Assistant",
    page_icon="🔍",
    layout="wide",
)

# ---- CSS Overrides ----
st.markdown("""
<style>
    .main { background-color: #0f1117; }
    .stTextInput>div>div>input { border-radius: 8px; }
    .badge { display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; margin-right: 6px; }
    .badge-aggregate { background: #1a3a5c; color: #5aaafa; }
    .badge-retrieve  { background: #1a3d2b; color: #4caf88; }
    .badge-compare   { background: #3a1a3a; color: #cc7fff; }
    .badge-verified  { background: #1a3d2b; color: #4caf88; }
    .badge-partial   { background: #3a3200; color: #f0c040; }
    .badge-unverified{ background: #3d1a1a; color: #f07070; }
    .evidence-card { background: #1a1d27; border-left: 3px solid #5aaafa; padding: 12px; border-radius: 6px; margin: 6px 0; font-size: 13px; font-family: monospace; white-space: pre-wrap; word-break: break-all; }
    .project-card  { background: #1a1d27; border-radius: 8px; padding: 14px 18px; margin: 6px 0; }
</style>
""", unsafe_allow_html=True)

st.title("🔍 Cross-Publication Insight Assistant")
st.caption("Analyze GitHub repos & publications — then ask questions about trends, patterns, and technologies.")

# ---- Helper ----
def api_get(path):
    try:
        r = httpx.get(f"{API_BASE}{path}", timeout=15)
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        return None, str(e)

def api_post(path, body):
    try:
        r = httpx.post(f"{API_BASE}{path}", json=body, timeout=120)
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        return None, str(e)

# ---- Sidebar — Add & Analyze URLs ----
with st.sidebar:
    st.header("📦 Add Projects")
    url_input = st.text_area("GitHub / Publication URLs (one per line)", height=150, placeholder="https://github.com/user/repo")
    if st.button("🚀 Analyze", use_container_width=True):
        urls = [u.strip() for u in url_input.strip().splitlines() if u.strip()]
        if urls:
            with st.spinner("Fetching and indexing…"):
                data, err = api_post("/projects/analyze", {"urls": urls, "source_type": "github"})
            if err:
                st.error(f"API error: {err}")
            else:
                for item in data.get("indexed", []):
                    st.success(f"✅ Indexed: {item['url']} (ID {item['project_id']})")
                for item in data.get("errors", []):
                    st.error(f"❌ {item['url']}: {item['error']}")
        else:
            st.warning("Please enter at least one URL.")

    st.divider()
    st.header("🗂 Indexed Projects")
    projects, err = api_get("/projects")
    if err:
        st.warning(f"Could not load projects: {err}")
    elif projects:
        for p in projects:
            st.markdown(
                f"<div class='project-card'><b>{p['name']}</b><br/>"
                f"<small style='color:#888'>{p['source_url']}</small></div>",
                unsafe_allow_html=True
            )
    else:
        st.info("No projects indexed yet.")

# ---- Main — Query ----
st.divider()
st.subheader("💬 Ask a Question")

example_queries = [
    "What percentage of projects use LangGraph?",
    "Show me projects that use vector databases.",
    "How many projects use RAG?",
    "Which framework is most common?",
    "Which projects use FAISS?",
]

col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input("Your question", placeholder="e.g. What percentage of projects use LangGraph?")
with col2:
    st.markdown("<br/>", unsafe_allow_html=True)
    use_example = st.selectbox("Examples", [""] + example_queries, label_visibility="collapsed")
    if use_example:
        query = use_example

project_id_input = st.text_input("Filter by project IDs (optional, comma-separated)", placeholder="1, 2, 3")

if st.button("🔎 Ask", use_container_width=False, type="primary"):
    if not query:
        st.warning("Please enter a question.")
    else:
        project_ids = None
        if project_id_input.strip():
            try:
                project_ids = [int(x.strip()) for x in project_id_input.split(",") if x.strip()]
            except ValueError:
                st.error("Invalid project IDs — use comma-separated integers.")
                st.stop()

        with st.spinner("Running multi-agent analysis…"):
            body = {"user_query": query}
            if project_ids:
                body["project_ids"] = project_ids
            result, err = api_post("/query", body)

        if err:
            st.error(f"Query failed: {err}")
        else:
            # ---- Answer ----
            st.divider()
            st.subheader("📋 Answer")

            qt = result.get("query_type") or "unknown"
            fc = result.get("fact_check_status") or "unknown"

            badge_class = {"aggregate": "badge-aggregate", "retrieve": "badge-retrieve", "compare": "badge-compare"}.get(qt, "badge-aggregate")
            fc_class    = {"verified": "badge-verified", "partial": "badge-partial",  "unverified": "badge-unverified"}.get(fc, "badge-partial")

            st.markdown(
                f"<span class='badge {badge_class}'>{qt.upper()}</span>"
                f"<span class='badge {fc_class}'>Fact-check: {fc.upper()}</span>",
                unsafe_allow_html=True
            )
            st.markdown(f"> {result.get('answer', 'No answer.')}")
