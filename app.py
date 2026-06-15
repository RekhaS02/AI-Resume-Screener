import os
import json
import re
from io import BytesIO
from dotenv import load_dotenv
import streamlit as st
import pdfplumber
import docx
from google import genai as genai_client
from google.genai import types as genai_types

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Resume Screener",
    page_icon="📄",
    layout="wide",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background: #f0f2f6; }
[data-testid="stSidebar"] { background: #1a1f2e; }

/* ── Sidebar styles ── */
.sidebar-header {
    padding: 1.5rem 0 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 1.5rem;
}
.sidebar-header h1 {
    color: #ffffff;
    font-size: 1.3rem;
    font-weight: 700;
    margin: 0;
}
.sidebar-header p {
    color: rgba(255,255,255,0.45);
    font-size: 0.78rem;
    margin: 4px 0 0;
}
.sidebar-label {
    color: rgba(255,255,255,0.5);
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 1.25rem 0 0.4rem;
}
[data-testid="stSidebar"] .stTextInput input {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #fff !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] .stTextInput input::placeholder { color: rgba(255,255,255,0.25) !important; }
[data-testid="stSidebar"] .stTextInput input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.2) !important;
}
[data-testid="stSidebar"] .stFileUploader {
    background: rgba(255,255,255,0.04) !important;
    border: 1.5px dashed rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
}
[data-testid="stSidebar"] label { color: rgba(255,255,255,0.7) !important; }
[data-testid="stSidebar"] .stTextArea textarea {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #fff !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
}
[data-testid="stSidebar"] .stTextArea textarea::placeholder { color: rgba(255,255,255,0.25) !important; }
[data-testid="stSidebar"] .stButton button {
    background: #6366f1 !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 0.65rem 1rem !important;
    width: 100% !important;
    margin-top: 0.75rem !important;
    transition: background 0.2s !important;
}
[data-testid="stSidebar"] .stButton button:hover { background: #4f46e5 !important; }
.key-status {
    font-size: 0.78rem;
    color: #6ee7b7;
    margin-top: 4px;
    display: flex;
    align-items: center;
    gap: 5px;
}

/* ── Main area cards ── */
.welcome-card {
    background: white;
    border-radius: 16px;
    padding: 3rem 2.5rem;
    text-align: center;
    border: 1px solid #e2e8f0;
    margin-top: 2rem;
}
.welcome-card h2 { font-size: 1.6rem; font-weight: 700; color: #0f172a; margin-bottom: 0.5rem; }
.welcome-card p  { color: #64748b; font-size: 0.95rem; max-width: 480px; margin: 0 auto; }
.step-row {
    display: flex;
    gap: 1.5rem;
    margin-top: 2rem;
    justify-content: center;
    flex-wrap: wrap;
}
.step-chip {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 99px;
    padding: 8px 16px;
    font-size: 0.83rem;
    color: #475569;
    font-weight: 500;
}
.step-num {
    width: 22px; height: 22px;
    background: #6366f1;
    color: white;
    border-radius: 50%;
    font-size: 0.72rem;
    font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}

/* ── Score hero ── */
.score-hero {
    background: linear-gradient(135deg, #1a1f2e 0%, #2d3450 100%);
    border-radius: 20px;
    padding: 2rem 2.5rem;
    display: flex;
    align-items: center;
    gap: 2rem;
    margin-bottom: 1.25rem;
    flex-wrap: wrap;
}
.score-circle {
    width: 110px; height: 110px;
    border-radius: 50%;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    flex-shrink: 0;
    border: 5px solid rgba(255,255,255,0.1);
    position: relative;
}
.score-num  { font-size: 2.4rem; font-weight: 800; line-height: 1; color: #fff; }
.score-sub  { font-size: 0.65rem; color: rgba(255,255,255,0.45); margin-top: 2px; }
.score-meta h2  { font-size: 1.3rem; font-weight: 700; color: #fff; margin: 0 0 4px; }
.score-meta p   { font-size: 0.88rem; color: rgba(255,255,255,0.6); margin: 0 0 12px; }
.verdict-pill {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 6px 16px; border-radius: 99px;
    font-size: 0.82rem; font-weight: 600;
}

/* ── Result cards ── */
.result-card {
    background: white;
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    border: 1px solid #e2e8f0;
    margin-bottom: 1rem;
    height: 100%;
}
.card-title {
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 1rem;
    display: flex; align-items: center; gap: 6px;
}
.bar-row { margin-bottom: 10px; }
.bar-label-row {
    display: flex; justify-content: space-between;
    font-size: 0.84rem; color: #475569; margin-bottom: 4px;
}
.bar-track {
    background: #f1f5f9; border-radius: 99px;
    height: 7px; overflow: hidden;
}
.bar-fill { height: 100%; border-radius: 99px; }

/* ── Skill chips ── */
.chip-wrap { display: flex; flex-wrap: wrap; gap: 6px; }
.chip {
    padding: 4px 11px; border-radius: 99px;
    font-size: 0.79rem; font-weight: 500;
}
.chip-green  { background: #dcfce7; color: #166534; }
.chip-yellow { background: #fef9c3; color: #854d0e; }
.chip-red    { background: #fee2e2; color: #991b1b; }

/* ── Suggestions ── */
.sug-item {
    display: flex; gap: 10px; align-items: flex-start;
    padding: 10px 0; border-bottom: 1px solid #f1f5f9;
    font-size: 0.88rem; color: #374151; line-height: 1.55;
}
.sug-item:last-child { border-bottom: none; }
.sug-dot {
    width: 22px; height: 22px; border-radius: 50%;
    background: #ede9fe; color: #6d28d9;
    font-size: 0.72rem; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; margin-top: 1px;
}

/* ── Misc ── */
.stSuccess { border-radius: 10px !important; }
[data-testid="stCaption"] { color: rgba(255,255,255,0.4) !important; }
.stSpinner > div { color: #6366f1 !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n".join(text_parts)

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = docx.Document(BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

def extract_resume_text(uploaded_file) -> str:
    file_bytes = uploaded_file.read()
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif name.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    elif name.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="replace")
    return ""

def score_color(s: int) -> str:
    return "#16a34a" if s >= 75 else "#d97706" if s >= 50 else "#dc2626"

def call_gemini(api_key: str, resume_text: str, jd: str) -> dict:
    client = genai_client.Client(api_key=api_key)

    prompt = f"""You are an expert ATS system and career coach. Analyze the resume against the job description.

RESUME:
{resume_text}

JOB DESCRIPTION:
{jd}

Return ONLY a raw JSON object with NO markdown, NO code fences, NO extra text before or after.
The JSON must have exactly these keys:
{{
  "overall_score": <integer 0-100>,
  "summary": "<5-7 word title>",
  "one_liner": "<one sentence strength or gap>",
  "skills_score": <integer 0-100>,
  "experience_score": <integer 0-100>,
  "keyword_score": <integer 0-100>,
  "education_score": <integer 0-100>,
  "matched_skills": ["<skill>"],
  "partial_skills": ["<skill>"],
  "missing_skills": ["<skill>"],
  "suggestions": ["<tip 1>","<tip 2>","<tip 3>","<tip 4>"]
}}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=8192,
        ),
    )

    raw = response.text if response.text else ""
    st.session_state["_raw"] = raw

    if not raw.strip():
        raise ValueError("Gemini returned an empty response. This may be a safety filter or quota issue.")

    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()

    start = cleaned.find("{")
    end   = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON found. Raw response: {raw[:300]}")

    return json.loads(cleaned[start:end+1])


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <h1>📄 Resume Screener</h1>
        <p>Powered by Google Gemini</p>
    </div>
    """, unsafe_allow_html=True)

    env_key = os.getenv("GEMINI_API_KEY", "")
    st.markdown('<div class="sidebar-label">API Key</div>', unsafe_allow_html=True)
    api_key = st.text_input(
        "key", value=env_key, type="password",
        placeholder="AIza...", label_visibility="collapsed"
    )
    if env_key:
        st.markdown('<div class="key-status">✓ Loaded from .env</div>', unsafe_allow_html=True)
    else:
        st.caption("Get free key → aistudio.google.com/apikey")

    st.markdown('<div class="sidebar-label">Resume</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "resume", type=["pdf","docx","txt"], label_visibility="collapsed"
    )

    resume_text = ""
    if uploaded_file:
        with st.spinner("Reading..."):
            resume_text = extract_resume_text(uploaded_file)
        if resume_text:
            st.success(f"✓ {uploaded_file.name}  ·  {len(resume_text.split())} words")
        else:
            st.error("Could not extract text from this file.")

    st.markdown('<div class="sidebar-label">Job Description</div>', unsafe_allow_html=True)
    job_desc = st.text_area(
        "jd", height=200, label_visibility="collapsed",
        placeholder="Paste the full job description here..."
    )

    analyze = st.button("🔍  Analyze Match", use_container_width=True)


# ── Main area ──────────────────────────────────────────────────────────────────
if not analyze:
    st.markdown("""
    <div class="welcome-card">
        <h2>AI Resume Screener</h2>
        <p>Upload your resume and paste a job description to get an instant match score,
           skill gap analysis, and actionable improvement tips — all powered by Gemini.</p>
        <div class="step-row">
            <div class="step-chip"><div class="step-num">1</div> Enter your API key</div>
            <div class="step-chip"><div class="step-num">2</div> Upload your resume</div>
            <div class="step-chip"><div class="step-num">3</div> Paste job description</div>
            <div class="step-chip"><div class="step-num">4</div> Click Analyze Match</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    # Validation
    if not api_key:
        st.error("⚠️ Please enter your Gemini API key in the sidebar.")
        st.stop()
    if not resume_text:
        st.error("⚠️ Please upload your resume in the sidebar.")
        st.stop()
    if not job_desc.strip():
        st.error("⚠️ Please paste the job description in the sidebar.")
        st.stop()

    with st.spinner("Gemini is analyzing your resume..."):
        try:
            result = call_gemini(api_key, resume_text, job_desc)
        except json.JSONDecodeError as e:
            st.error(f"JSON parse error: {e}")
            raw = st.session_state.get("_raw", "")
            st.text_area("Raw Gemini response (debug)", value=raw, height=200)
            st.stop()
        except Exception as e:
            msg = str(e)
            if "API_KEY_INVALID" in msg or "api key" in msg.lower():
                st.error("❌ Invalid API key.")
            elif "quota" in msg.lower() or "429" in msg:
                st.error("❌ Quota exceeded. Wait a minute and try again.")
            else:
                st.error(f"❌ {msg}")
            raw = st.session_state.get("_raw", "")
            if raw:
                st.text_area("Raw Gemini response (debug)", value=raw, height=150)
            st.stop()

    score  = int(result.get("overall_score", 0))
    color  = score_color(score)
    if score >= 75:
        v_label, v_bg, v_fg = "Strong fit",   "#dcfce7", "#166534"
    elif score >= 50:
        v_label, v_bg, v_fg = "Possible fit", "#fef9c3", "#854d0e"
    else:
        v_label, v_bg, v_fg = "Weak fit",     "#fee2e2", "#991b1b"

    # ── Score hero ──
    st.markdown(f"""
    <div class="score-hero">
        <div class="score-circle" style="border-color:{color}40; background:{color}18;">
            <div class="score-num" style="color:{color};">{score}</div>
            <div class="score-sub">out of 100</div>
        </div>
        <div class="score-meta">
            <h2>{result.get("summary","Analysis complete")}</h2>
            <p>{result.get("one_liner","")}</p>
            <span class="verdict-pill" style="background:{v_bg};color:{v_fg};">
                {"✅" if score>=75 else "⚠️" if score>=50 else "❌"} {v_label}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Score breakdown + Skills row ──
    col_a, col_b = st.columns([1.1, 1])

    with col_a:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title" style="color:#6366f1;">📊 Score Breakdown</div>', unsafe_allow_html=True)
        dims = [
            ("Skills alignment",     result.get("skills_score",     0)),
            ("Experience relevance", result.get("experience_score", 0)),
            ("Keyword coverage",     result.get("keyword_score",    0)),
            ("Education fit",        result.get("education_score",  0)),
        ]
        for label, val in dims:
            c = score_color(int(val))
            st.markdown(f"""
            <div class="bar-row">
                <div class="bar-label-row">
                    <span>{label}</span>
                    <span style="font-weight:600;color:{c};">{int(val)}%</span>
                </div>
                <div class="bar-track">
                    <div class="bar-fill" style="width:{val}%;background:{c};"></div>
                </div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        matched  = result.get("matched_skills",  [])
        partial  = result.get("partial_skills",  [])
        missing  = result.get("missing_skills",  [])

        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title" style="color:#16a34a;">✅ Skills You Have</div>', unsafe_allow_html=True)
        if matched:
            chips = "".join(f'<span class="chip chip-green">{s}</span>' for s in matched)
            st.markdown(f'<div class="chip-wrap">{chips}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#94a3b8;font-size:0.83rem;">None found</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title" style="color:#d97706;">⚠️ Partial Match</div>', unsafe_allow_html=True)
        if partial:
            chips = "".join(f'<span class="chip chip-yellow">{s}</span>' for s in partial)
            st.markdown(f'<div class="chip-wrap">{chips}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#94a3b8;font-size:0.83rem;">None</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title" style="color:#dc2626;">❌ Missing Skills</div>', unsafe_allow_html=True)
        if missing:
            chips = "".join(f'<span class="chip chip-red">{s}</span>' for s in missing)
            st.markdown(f'<div class="chip-wrap">{chips}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#94a3b8;font-size:0.83rem;">None — great fit!</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Suggestions ──
    suggestions = result.get("suggestions", [])
    if suggestions:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title" style="color:#7c3aed;">💡 How to Improve Your Resume</div>', unsafe_allow_html=True)
        items = "".join(
            f'<div class="sug-item"><div class="sug-dot">{i+1}</div><span>{s}</span></div>'
            for i, s in enumerate(suggestions)
        )
        st.markdown(items, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)