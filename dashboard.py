import streamlit as st
import sys
import os
import zipfile
import json

sys.path.append(".")
from parser.code_parser import parse_repository
from scanners.security_scanner import scan_repository, get_severity_summary
from embeddings.embedding_engine import embed_code_chunks, search_code
from app.ai_reviewer import review_function, explain_code, suggest_refactor

st.set_page_config(
    page_title="CodeMind AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .stApp {
        background: linear-gradient(135deg, #0a0a0f 0%, #0d1117 50%, #0a0e1a 100%);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 100%) !important;
        border-right: 1px solid #30363d !important;
    }

    section[data-testid="stSidebar"] * {
        color: #e6edf3 !important;
    }

    .main-hero {
        text-align: center;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, rgba(88,166,255,0.08) 0%, rgba(138,43,226,0.08) 50%, rgba(0,255,136,0.05) 100%);
        border: 1px solid rgba(88,166,255,0.15);
        border-radius: 20px;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }

    .main-hero::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle at 30% 50%, rgba(88,166,255,0.05) 0%, transparent 60%),
                    radial-gradient(circle at 70% 50%, rgba(138,43,226,0.05) 0%, transparent 60%);
        pointer-events: none;
    }

    .hero-badge {
        display: inline-block;
        background: linear-gradient(90deg, rgba(88,166,255,0.2), rgba(138,43,226,0.2));
        border: 1px solid rgba(88,166,255,0.3);
        border-radius: 50px;
        padding: 4px 16px;
        font-size: 0.75rem;
        color: #58a6ff !important;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }

    .hero-title {
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #58a6ff 0%, #a855f7 50%, #00ff88 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0.5rem 0;
        line-height: 1.2;
    }

    .hero-subtitle {
        color: #8b949e !important;
        font-size: 1.1rem;
        margin-top: 0.5rem;
        font-weight: 300;
    }

    .metric-card {
        background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
        border: 1px solid #30363d;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, #58a6ff, #a855f7);
    }

    .metric-number {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #58a6ff, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .metric-label {
        color: #8b949e;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.25rem;
    }

    .feature-card {
        background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
        border: 1px solid #30363d;
        border-radius: 16px;
        padding: 1.5rem;
        height: 100%;
        transition: border-color 0.3s ease;
    }

    .feature-card:hover {
        border-color: #58a6ff;
    }

    .feature-icon {
        font-size: 2rem;
        margin-bottom: 0.75rem;
    }

    .feature-title {
        color: #e6edf3 !important;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .feature-desc {
        color: #8b949e !important;
        font-size: 0.85rem;
        line-height: 1.5;
    }

    .severity-high {
        background: linear-gradient(135deg, rgba(255,75,75,0.15), rgba(255,75,75,0.05));
        border: 1px solid rgba(255,75,75,0.3);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }

    .severity-medium {
        background: linear-gradient(135deg, rgba(255,165,0,0.15), rgba(255,165,0,0.05));
        border: 1px solid rgba(255,165,0,0.3);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }

    .severity-low {
        background: linear-gradient(135deg, rgba(0,204,136,0.15), rgba(0,204,136,0.05));
        border: 1px solid rgba(0,204,136,0.3);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }

    .section-header {
        color: #e6edf3 !important;
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .tag {
        display: inline-block;
        background: rgba(88,166,255,0.1);
        border: 1px solid rgba(88,166,255,0.2);
        border-radius: 6px;
        padding: 2px 10px;
        font-size: 0.75rem;
        color: #58a6ff !important;
        font-family: 'JetBrains Mono', monospace;
    }

    .tag-green {
        background: rgba(0,255,136,0.1);
        border-color: rgba(0,255,136,0.2);
        color: #00ff88 !important;
    }

    .tag-purple {
        background: rgba(168,85,247,0.1);
        border-color: rgba(168,85,247,0.2);
        color: #a855f7 !important;
    }

    .pipeline-step {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .step-number {
        background: linear-gradient(135deg, #58a6ff, #a855f7);
        border-radius: 50%;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.85rem;
        color: white !important;
        flex-shrink: 0;
    }

    .search-result {
        background: linear-gradient(135deg, #161b22, #1c2128);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        border-left: 3px solid #58a6ff;
    }

    .similarity-bar {
        height: 4px;
        border-radius: 2px;
        background: linear-gradient(90deg, #58a6ff, #a855f7);
        margin-top: 0.5rem;
    }

    div[data-testid="stExpander"] {
        background: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 12px !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #58a6ff, #a855f7) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 500 !important;
        transition: opacity 0.2s !important;
    }

    .stButton > button:hover {
        opacity: 0.85 !important;
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        color: #e6edf3 !important;
    }

    .stFileUploader {
        background: #161b22 !important;
        border: 2px dashed #30363d !important;
        border-radius: 12px !important;
    }

    div[data-testid="stChatMessage"] {
        background: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 12px !important;
        margin-bottom: 0.75rem !important;
    }

    .stSpinner > div {
        border-top-color: #58a6ff !important;
    }

    p, li, span, label { color: #8b949e !important; }
    h1, h2, h3, h4 { color: #e6edf3 !important; }

    .stRadio > label { color: #e6edf3 !important; }
    div[role="radiogroup"] label { color: #8b949e !important; }

    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0d1117; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #58a6ff; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────
if "parsed_files" not in st.session_state:
    st.session_state.parsed_files = []
if "security_issues" not in st.session_state:
    st.session_state.security_issues = []
if "repo_name" not in st.session_state:
    st.session_state.repo_name = ""
if "repo_path" not in st.session_state:
    st.session_state.repo_path = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 1rem 0;'>
        <div style='font-size:2.5rem;'>🧠</div>
        <div style='font-size:1.3rem; font-weight:700;
             background: linear-gradient(135deg, #58a6ff, #a855f7);
             -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            CodeMind AI
        </div>
        <div style='color:#8b949e; font-size:0.75rem; margin-top:0.25rem;'>
            AI Code Review Platform
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#30363d; margin:0.5rem 0;'>", unsafe_allow_html=True)

    page = st.radio("", [
        "🏠  Home",
        "📁  Upload Repository",
        "🔍  Code Analysis",
        "🔒  Security Scanner",
        "🔎  Semantic Search",
        "🤖  AI Chat",
    ], label_visibility="collapsed")

    st.markdown("<hr style='border-color:#30363d; margin:1rem 0;'>", unsafe_allow_html=True)

    if st.session_state.repo_name:
        st.markdown(f"""
        <div style='background:#1c2128; border:1px solid #30363d;
             border-radius:10px; padding:0.75rem; margin-bottom:1rem;'>
            <div style='color:#8b949e; font-size:0.7rem; text-transform:uppercase;
                 letter-spacing:1px;'>Active Repository</div>
            <div style='color:#58a6ff; font-weight:600; font-size:0.9rem;
                 margin-top:0.25rem;'>📦 {st.session_state.repo_name}</div>
            <div style='color:#8b949e; font-size:0.75rem; margin-top:0.25rem;'>
                {sum(len(f["functions"]) for f in st.session_state.parsed_files)} functions •
                {len(st.session_state.security_issues)} issues
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style='color:#8b949e; font-size:0.75rem;'>
        <div style='margin-bottom:0.4rem;'>⚡ Powered by</div>
        <span style='background:rgba(88,166,255,0.1); border:1px solid rgba(88,166,255,0.2);
              border-radius:4px; padding:2px 8px; font-size:0.7rem; color:#58a6ff;
              margin-right:4px;'>Tree-sitter</span>
        <span style='background:rgba(168,85,247,0.1); border:1px solid rgba(168,85,247,0.2);
              border-radius:4px; padding:2px 8px; font-size:0.7rem; color:#a855f7;
              margin-right:4px;'>ChromaDB</span>
        <span style='background:rgba(0,255,136,0.1); border:1px solid rgba(0,255,136,0.2);
              border-radius:4px; padding:2px 8px; font-size:0.7rem; color:#00ff88;'>Bandit</span>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════════════════════════
if page == "🏠  Home":
    st.markdown("""
    <div class='main-hero'>
        <div class='hero-badge'>✦ AI-Powered Developer Platform</div>
        <div class='hero-title'>CodeMind AI</div>
        <div class='hero-subtitle'>
            Intelligent code review, security scanning, and semantic search<br>
            for modern development teams
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-number'>AST</div>
            <div class='metric-label'>Code Parsing</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-number'>RAG</div>
            <div class='metric-label'>AI Architecture</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-number'>384</div>
            <div class='metric-label'>Vector Dimensions</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-number'>3</div>
            <div class='metric-label'>Languages Supported</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>🔍</div>
            <div class='feature-title'>Deep Code Analysis</div>
            <div class='feature-desc'>Tree-sitter AST parser extracts every function,
            class and import with precise line numbers</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>🔒</div>
            <div class='feature-title'>Security Scanning</div>
            <div class='feature-desc'>Bandit-powered vulnerability detection catches
            SQL injection, hardcoded secrets and unsafe functions</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>🧠</div>
            <div class='feature-title'>Semantic Search</div>
            <div class='feature-desc'>Find code by meaning using 384-dimensional
            vector embeddings — not just keyword matching</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>⚡ How It Works</div>", unsafe_allow_html=True)

    steps = [
        ("1", "📁 Upload Repository", "Upload any ZIP file — Python, JavaScript or TypeScript"),
        ("2", "🔬 Parse Source Code", "Tree-sitter builds an AST and extracts all code structures"),
        ("3", "🔒 Security Scan", "Bandit scans every file for vulnerabilities automatically"),
        ("4", "🧠 Generate Embeddings", "Sentence-transformers converts code to 384D vectors"),
        ("5", "🤖 AI Review", "LLM analyzes functions and provides actionable suggestions"),
    ]
    for num, title, desc in steps:
        st.markdown(f"""
        <div class='pipeline-step'>
            <div class='step-number'>{num}</div>
            <div>
                <div style='color:#e6edf3; font-weight:500; font-size:0.9rem;'>{title}</div>
                <div style='color:#8b949e; font-size:0.8rem;'>{desc}</div>
            </div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# UPLOAD
# ══════════════════════════════════════════════════════════════════
elif page == "📁  Upload Repository":
    st.markdown("<div class='section-header'>📁 Upload Repository</div>", unsafe_allow_html=True)
    st.markdown("<p>Upload a ZIP file of your project to begin analysis</p>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Drop your ZIP file here",
        type=["zip"],
        help="Zip your project folder and upload it here"
    )

    if uploaded_file:
        repo_name = uploaded_file.name.replace(".zip", "")
        col1, col2 = st.columns([3,1])
        with col1:
            st.markdown(f"""
            <div style='background:#161b22; border:1px solid #30363d; border-radius:10px;
                 padding:1rem; margin-bottom:1rem;'>
                <span style='color:#00ff88;'>✓</span>
                <span style='color:#e6edf3; font-weight:500;'> {uploaded_file.name}</span>
                <span style='color:#8b949e; font-size:0.85rem;'>
                    — {uploaded_file.size/1024:.1f} KB
                </span>
            </div>
            """, unsafe_allow_html=True)

        if st.button("🚀 Start Analysis", type="primary"):
            extract_path = os.path.join("uploads", repo_name)
            os.makedirs(extract_path, exist_ok=True)

            with zipfile.ZipFile(uploaded_file, "r") as zip_ref:
                zip_ref.extractall(extract_path)

            progress = st.progress(0)
            status = st.empty()

            status.markdown("🔬 **Parsing source code...**")
            progress.progress(25)
            parsed = parse_repository(extract_path)
            st.session_state.parsed_files = parsed
            st.session_state.repo_name = repo_name
            st.session_state.repo_path = extract_path

            status.markdown("🔒 **Running security scan...**")
            progress.progress(50)
            issues = scan_repository(extract_path)
            st.session_state.security_issues = issues

            status.markdown("🧠 **Generating AI embeddings...**")
            progress.progress(75)
            embed_code_chunks(parsed, repo_name)

            progress.progress(100)
            status.markdown("✅ **Analysis complete!**")

            total_functions = sum(len(f["functions"]) for f in parsed)
            total_classes = sum(len(f["classes"]) for f in parsed)
            summary = get_severity_summary(issues)

            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""<div class='metric-card'>
                    <div class='metric-number'>{len(parsed)}</div>
                    <div class='metric-label'>Files</div></div>""",
                    unsafe_allow_html=True)
            with col2:
                st.markdown(f"""<div class='metric-card'>
                    <div class='metric-number'>{total_functions}</div>
                    <div class='metric-label'>Functions</div></div>""",
                    unsafe_allow_html=True)
            with col3:
                st.markdown(f"""<div class='metric-card'>
                    <div class='metric-number'>{total_classes}</div>
                    <div class='metric-label'>Classes</div></div>""",
                    unsafe_allow_html=True)
            with col4:
                st.markdown(f"""<div class='metric-card'>
                    <div class='metric-number'>{len(issues)}</div>
                    <div class='metric-label'>Issues Found</div></div>""",
                    unsafe_allow_html=True)
            st.balloons()

# ══════════════════════════════════════════════════════════════════
# CODE ANALYSIS
# ══════════════════════════════════════════════════════════════════
elif page == "🔍  Code Analysis":
    st.markdown("<div class='section-header'>🔍 Code Analysis</div>", unsafe_allow_html=True)

    if not st.session_state.parsed_files:
        st.markdown("""
        <div style='text-align:center; padding:3rem; background:#161b22;
             border:1px dashed #30363d; border-radius:16px;'>
            <div style='font-size:3rem;'>📁</div>
            <div style='color:#e6edf3; font-size:1.1rem; margin-top:1rem;'>
                No repository uploaded yet
            </div>
            <div style='color:#8b949e; margin-top:0.5rem;'>
                Go to Upload Repository to get started
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        parsed = st.session_state.parsed_files
        total_functions = sum(len(f["functions"]) for f in parsed)
        total_classes = sum(len(f["classes"]) for f in parsed)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""<div class='metric-card'>
                <div class='metric-number'>{len(parsed)}</div>
                <div class='metric-label'>Files Parsed</div></div>""",
                unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class='metric-card'>
                <div class='metric-number'>{total_functions}</div>
                <div class='metric-label'>Functions</div></div>""",
                unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div class='metric-card'>
                <div class='metric-number'>{total_classes}</div>
                <div class='metric-label'>Classes</div></div>""",
                unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        for file_result in parsed:
            fname = os.path.basename(file_result["file"])
            with st.expander(f"📄 {fname} — {len(file_result['functions'])} functions, {len(file_result['classes'])} classes"):
                for func in file_result["functions"]:
                    st.markdown(f"""
                    <div style='display:flex; align-items:center; gap:0.5rem; margin-bottom:0.5rem;'>
                        <span class='tag'>⚙ {func['name']}</span>
                        <span style='color:#8b949e; font-size:0.75rem;'>
                            Lines {func['start_line']}–{func['end_line']}
                        </span>
                    </div>""", unsafe_allow_html=True)
                    st.code(func["code"], language="python")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"🤖 Review", key=f"r_{fname}_{func['name']}"):
                            with st.spinner("Getting AI review..."):
                                review = review_function(func["name"], func["code"])
                            st.markdown(review)
                    with col2:
                        if st.button(f"💡 Explain", key=f"e_{fname}_{func['name']}"):
                            with st.spinner("Explaining..."):
                                explanation = explain_code(func["code"])
                            st.markdown(explanation)
                    with col3:
                        if st.button(f"♻️ Refactor", key=f"rf_{fname}_{func['name']}"):
                            with st.spinner("Refactoring..."):
                                refactor = suggest_refactor(func["name"], func["code"])
                            st.markdown(refactor)

# ══════════════════════════════════════════════════════════════════
# SECURITY
# ══════════════════════════════════════════════════════════════════
elif page == "🔒  Security Scanner":
    st.markdown("<div class='section-header'>🔒 Security Scanner</div>", unsafe_allow_html=True)

    if not st.session_state.repo_name:
        st.markdown("""
        <div style='text-align:center; padding:3rem; background:#161b22;
             border:1px dashed #30363d; border-radius:16px;'>
            <div style='font-size:3rem;'>🔒</div>
            <div style='color:#e6edf3; font-size:1.1rem; margin-top:1rem;'>
                No repository uploaded yet
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        issues = st.session_state.security_issues
        summary = get_severity_summary(issues)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""<div class='metric-card' style='border-top:2px solid #ff4b4b;'>
                <div class='metric-number' style='color:#ff4b4b !important;
                     -webkit-text-fill-color:#ff4b4b !important;'>{summary['HIGH']}</div>
                <div class='metric-label'>High Severity</div></div>""",
                unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class='metric-card' style='border-top:2px solid #ffa500;'>
                <div class='metric-number' style='color:#ffa500 !important;
                     -webkit-text-fill-color:#ffa500 !important;'>{summary['MEDIUM']}</div>
                <div class='metric-label'>Medium Severity</div></div>""",
                unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div class='metric-card' style='border-top:2px solid #00cc88;'>
                <div class='metric-number' style='color:#00cc88 !important;
                     -webkit-text-fill-color:#00cc88 !important;'>{summary['LOW']}</div>
                <div class='metric-label'>Low Severity</div></div>""",
                unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if not issues:
            st.markdown("""
            <div style='text-align:center; padding:2rem; background:rgba(0,255,136,0.05);
                 border:1px solid rgba(0,255,136,0.2); border-radius:16px;'>
                <div style='font-size:2rem;'>✅</div>
                <div style='color:#00ff88; font-size:1.1rem; margin-top:0.5rem;'>
                    No security issues found!
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            for issue in issues:
                sev = issue["severity"]
                cls = f"severity-{sev.lower()}"
                icon = "🔴" if sev == "HIGH" else "🟡" if sev == "MEDIUM" else "🟢"
                with st.expander(f"{icon} {sev} — {issue['issue'][:70]}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**File:** `{issue['file']}`")
                        st.markdown(f"**Line:** {issue['line']}")
                    with col2:
                        st.markdown(f"**Severity:** {sev}")
                        st.markdown(f"**Confidence:** {issue.get('confidence', 'N/A')}")
                    st.markdown(f"**Issue:** {issue['issue']}")
                    if issue.get("code"):
                        st.code(issue["code"], language="python")

# ══════════════════════════════════════════════════════════════════
# SEMANTIC SEARCH
# ══════════════════════════════════════════════════════════════════
elif page == "🔎  Semantic Search":
    st.markdown("<div class='section-header'>🔎 Semantic Code Search</div>", unsafe_allow_html=True)
    st.markdown("<p>Search your codebase by <strong style='color:#58a6ff;'>meaning</strong> — not just keywords</p>", unsafe_allow_html=True)

    if not st.session_state.repo_name:
        st.markdown("""
        <div style='text-align:center; padding:3rem; background:#161b22;
             border:1px dashed #30363d; border-radius:16px;'>
            <div style='font-size:3rem;'>🔎</div>
            <div style='color:#e6edf3; font-size:1.1rem; margin-top:1rem;'>
                Upload a repository first to enable semantic search
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([4, 1])
        with col1:
            query = st.text_input("", placeholder="e.g. function that adds numbers, error handling, database connection...")
        with col2:
            top_k = st.selectbox("Results", [3, 5, 10], index=0)

        if st.button("🔍 Search", type="primary") and query:
            with st.spinner("Searching vector database..."):
                results = search_code(query, st.session_state.repo_name, top_k)

            if results:
                st.markdown(f"<br><div style='color:#8b949e; font-size:0.85rem;'>Found {len(results)} results for: <span style='color:#58a6ff;'>{query}</span></div><br>", unsafe_allow_html=True)
                for i, result in enumerate(results):
                    meta = result["metadata"]
                    sim = result["similarity"]
                    bar_width = int(sim * 100)
                    st.markdown(f"""
                    <div class='search-result'>
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <div>
                                <span class='tag'>⚙ {meta['name']}</span>
                                <span class='tag-purple' style='margin-left:0.5rem;'>{meta['type']}</span>
                            </div>
                            <span style='color:#58a6ff; font-weight:600;'>{sim:.0%} match</span>
                        </div>
                        <div class='similarity-bar' style='width:{bar_width}%;'></div>
                        <div style='color:#8b949e; font-size:0.8rem; margin-top:0.5rem;'>
                            📄 {meta['file']} · Lines {meta['start_line']}–{meta['end_line']}
                        </div>
                    </div>""", unsafe_allow_html=True)
                    st.code(result["code"], language="python")
            else:
                st.info("No results found. Try a different search query.")

# ══════════════════════════════════════════════════════════════════
# AI CHAT
# ══════════════════════════════════════════════════════════════════
elif page == "🤖  AI Chat":
    st.markdown("<div class='section-header'>🤖 AI Coding Assistant</div>", unsafe_allow_html=True)
    st.markdown("<p>Ask anything about your code or programming in general</p>", unsafe_allow_html=True)

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask a coding question..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                from app.ai_reviewer import ask_ai
                response = ask_ai(
                    prompt,
                    "You are CodeMind AI, an expert coding assistant. Give helpful, practical answers."
                )
            st.markdown(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})