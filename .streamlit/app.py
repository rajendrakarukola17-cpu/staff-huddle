"""
GovDocs AI — Professional Government Workspace
Refactored for security, performance, and mobile-first UX
"""
import io
import secrets as pysecrets
from datetime import date, datetime, timedelta
from typing import Optional
import bcrypt
import pandas as pd
import streamlit as st
from supabase import create_client, Client
from streamlit_cookies_controller import CookieController

# ============================================================
# CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="GovDocs AI — Government Workspace",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Constants
DAILY_AI_LIMIT = 20
MAX_UPLOAD_MB = 20
OCR_MAX_PAGES = 40
SESSION_DAYS = 30
COOKIE_NAME = "huddle_session"

# ============================================================
# PROFESSIONAL DESIGN SYSTEM (Mobile-First)
# ============================================================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --navy-900: #16324F;
    --navy-800: #1E3A5F;
    --navy-700: #2C5282;
    --blue: #2563EB;
    --blue-soft: #EFF6FF;
    --indigo: #6366F1;
    --green: #16A34A;
    --green-soft: #F0FDF4;
    --purple: #7C3AED;
    --canvas: #F7F9FB;
    --surface: #FFFFFF;
    --border: #E2E8F0;
    --border-strong: #CBD5E1;
    --text: #0F172A;
    --muted: #64748B;
    --danger: #DC2626;
    --shadow: 0 2px 10px rgba(15,23,42,.05);
    --shadow-md: 0 8px 24px rgba(15,23,42,.08);
    --shadow-lg: 0 18px 45px rgba(15,23,42,.12);
    --radius-lg: 16px;
    --radius-md: 12px;
    --radius-sm: 9px;
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

body { background: var(--canvas); }
.stApp { background: var(--canvas); color: var(--text); }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.35rem; padding-bottom: 3rem; max-width: 1500px; }
h1, h2, h3, h4 { color: var(--text); font-weight: 700; letter-spacing: -0.025em; }
p, label, .stMarkdown { color: var(--text); }
::selection { background: #DBEAFE; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div:first-child { padding: 1rem .8rem; }
section[data-testid="stSidebar"] .stRadio > div { gap: 4px; }
section[data-testid="stSidebar"] .stRadio > div > label {
    border-radius: 10px;
    padding: .62rem .75rem;
    margin: 0;
    color: #334155;
    font-weight: 500;
    transition: .15s ease;
}
section[data-testid="stSidebar"] .stRadio > div > label:hover { background: #F1F5F9; }
section[data-testid="stSidebar"] .stRadio > div > label:has(div[aria-checked="true"]) {
    background: #EAF2FF;
    color: var(--navy-800);
    font-weight: 700;
}
section[data-testid="stSidebar"] .stRadio > div > label p { color: inherit !important; }

.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: .45rem .35rem 1.1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1rem;
}
.sidebar-logo {
    width: 38px;
    height: 38px;
    border-radius: 10px;
    background: var(--navy-800);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
}
.sidebar-brand-title { font-size: 17px; font-weight: 800; color: var(--navy-900); line-height: 1.1; }
.sidebar-brand-sub { font-size: 10px; color: var(--muted); margin-top: 3px; }

.profile-card {
    background: #F8FAFC;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 12px;
}
.profile-name { font-size: 13px; font-weight: 700; color: var(--text); }
.profile-email { font-size: 10px; color: var(--muted); margin-top: 3px; overflow: hidden; text-overflow: ellipsis; }

/* Header */
.app-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #FFFFFF;
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 13px 18px;
    margin-bottom: 18px;
    box-shadow: var(--shadow);
}
.app-topbar-title { font-size: 13px; font-weight: 700; color: var(--navy-800); }
.app-topbar-sub { font-size: 11px; color: var(--muted); margin-top: 2px; }

.page-header { margin-bottom: 20px; }
.page-header h1 { margin: 0; font-size: 27px; }
.page-header p { margin: 5px 0 0; color: var(--muted); font-size: 13px; }

/* Cards */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 18px;
    box-shadow: var(--shadow);
    transition: .2s ease;
}
.card:hover { box-shadow: var(--shadow-md); }

.kpi-card {
    background: #FFFFFF;
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 16px;
    box-shadow: var(--shadow);
    min-height: 112px;
}
.kpi-label { color: var(--muted); font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .5px; }
.kpi-value { color: var(--text); font-size: 25px; font-weight: 800; margin-top: 8px; }
.kpi-foot { color: var(--muted); font-size: 10px; margin-top: 3px; }

/* Buttons */
.stButton > button {
    border: 1px solid var(--border-strong) !important;
    background: #FFFFFF !important;
    color: var(--navy-800) !important;
    border-radius: 9px !important;
    font-weight: 600 !important;
    min-height: 38px;
    transition: .15s ease;
}
.stButton > button:hover { border-color: #94A3B8 !important; box-shadow: var(--shadow); }
.stButton > button[kind="primary"] {
    background: var(--navy-800) !important;
    color: #FFFFFF !important;
    border-color: var(--navy-800) !important;
}
.stButton > button[kind="primary"]:hover { background: var(--navy-700) !important; }

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div,
.stDateInput > div > div > input,
.stNumberInput > div > div > input {
    background: #FFFFFF !important;
    border: 1px solid var(--border-strong) !important;
    border-radius: 9px !important;
    color: var(--text) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #60A5FA !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,.10) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    background: #EEF2F6;
    padding: 3px;
    border-radius: 10px;
    border: none;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #475569;
    font-weight: 600;
    font-size: 12px;
}
.stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    color: var(--navy-800) !important;
    box-shadow: 0 1px 4px rgba(15,23,42,.08);
}

/* Document cards */
.doc-card {
    background: #FFFFFF;
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 15px 16px;
    margin: 0 0 9px;
    box-shadow: var(--shadow);
    transition: .2s ease;
}
.doc-card:hover { border-color: #CBD5E1; box-shadow: var(--shadow-md); }
.doc-row { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
.doc-ref { color: var(--navy-700); background: #EFF6FF; border: 1px solid #DBEAFE; border-radius: 999px; padding: 4px 9px; font-size: 10px; font-weight: 700; }
.doc-title { font-size: 14px; font-weight: 700; color: var(--text); margin-top: 9px; }
.doc-meta { display: flex; flex-wrap: wrap; gap: 10px; color: var(--muted); font-size: 10px; margin-top: 6px; }

.badge { display: inline-flex; align-items: center; gap: 4px; padding: 4px 9px; border-radius: 999px; font-size: 10px; font-weight: 700; }
.badge-basic { background: #F1F5F9; color: #475569; border: 1px solid #E2E8F0; }
.badge-pro { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
.badge-max { background: #F5F3FF; color: #6D28D9; border: 1px solid #DDD6FE; }

/* Chat */
div[data-testid="stChatMessage"] {
    border: 1px solid var(--border);
    border-radius: 13px;
    margin-bottom: 10px;
    background: #FFFFFF;
}
div[data-testid="stChatInput"] > div {
    border: 1px solid var(--border-strong) !important;
    border-radius: 13px !important;
    background: #FFFFFF !important;
}

/* Tapal */
.tapal-card {
    background: #FFFFFF;
    border: 1px solid var(--border);
    border-radius: 13px;
    padding: 14px;
    margin-bottom: 9px;
    box-shadow: var(--shadow);
}
.tapal-inward { border-left: 4px solid var(--navy-700); }
.tapal-outward { border-left: 4px solid #16A34A; }

/* Login */
.login-shell {
    min-height: 78vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 30px 10px;
}
.login-panel {
    width: min(920px, 100%);
    background: #FFFFFF;
    border: 1px solid var(--border);
    border-radius: 20px;
    box-shadow: var(--shadow-lg);
    overflow: hidden;
    display: grid;
    grid-template-columns: 1fr 1.05fr;
}
.login-brand {
    background: linear-gradient(150deg, #16324F, #2C5282);
    padding: 48px;
    color: #FFFFFF;
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-height: 510px;
}
.login-brand h1 { color: #FFFFFF; font-size: 32px; margin: 12px 0 8px; }
.login-brand p { color: rgba(255,255,255,.78); font-size: 12px; line-height: 1.7; }
.login-mark { width: 52px; height: 52px; border-radius: 14px; background: rgba(255,255,255,.12); display: flex; align-items: center; justify-content: center; font-size: 27px; border: 1px solid rgba(255,255,255,.18); }
.login-form { padding: 38px 40px; }
.login-form h2 { font-size: 22px; margin: 0 0 5px; }
.login-form .muted { color: var(--muted); font-size: 12px; margin-bottom: 18px; }

/* Mobile Responsive */
@media(max-width: 900px) {
    .login-panel { grid-template-columns: 1fr; }
    .login-brand { min-height: auto; padding: 28px; }
    .login-brand p { margin-bottom: 0; }
    .login-form { padding: 28px 22px; }
}

@media(max-width: 700px) {
    .block-container { padding: 12px 10px 30px; }
    .page-header h1 { font-size: 22px; }
    .doc-row { flex-direction: column; }
    .doc-meta { gap: 6px; }
    .app-topbar { flex-direction: column; align-items: flex-start; gap: 8px; }
    .kpi-card { min-height: auto; }
    section[data-testid="stSidebar"] .stRadio > div > label { padding: .5rem .6rem; font-size: 13px; }
}

@media(max-width: 500px) {
    .page-header h1 { font-size: 20px; }
    .kpi-value { font-size: 20px; }
    .doc-title { font-size: 13px; }
}

hr { border-color: var(--border) !important; }
[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def page_header(title: str, subtitle: str = ""):
    st.markdown(
        f'<div class="page-header"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )

def greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"

def tier_badge(tier: str) -> str:
    cls = {"Basic": "badge-basic", "Staff": "badge-basic", "Pro": "badge-pro", "Max": "badge-max", "Admin": "badge-max"}.get(tier, "badge-basic")
    return f'<span class="badge {cls}">{tier}</span>'

def safe_str(value) -> str:
    return "" if value is None else str(value)

# ============================================================
# SUPABASE CONNECTION (with connection pooling)
# ============================================================
@st.cache_resource
def get_supabase() -> Client:
    """Cached Supabase client - reuses connection across sessions"""
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()
cookies = CookieController()

# ============================================================
# SESSION STATE
# ============================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# ============================================================
# AUTH HELPERS
# ============================================================
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def check_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def get_user(email: str):
    res = supabase.table("users").select("*").eq("email", email).execute()
    return res.data[0] if res.data else None

def create_pending_request(name: str, email: str, note: str):
    supabase.table("pending_requests").insert({
        "name": name, "email": email, "note": note,
        "requested_at": datetime.utcnow().isoformat(), "status": "pending",
    }).execute()

def has_access(user_tier: str, required_tier: str) -> bool:
    levels = {"Staff": 1, "Basic": 1, "Pro": 2, "Max": 3, "Admin": 4}
    return levels.get(user_tier, 0) >= levels.get(required_tier, 0)

# ============================================================
# CACHED DATA FETCHES (30s TTL for performance)
# ============================================================
@st.cache_data(ttl=30)
def fetch_circulars():
    return supabase.table("circulars").select("*").execute().data or []

@st.cache_data(ttl=30)
def fetch_templates():
    return supabase.table("templates").select("*").execute().data or []

@st.cache_data(ttl=30)
def fetch_tapal():
    return supabase.table("tapal_log").select("*").order("tapal_date", desc=True).execute().data or []

@st.cache_data(ttl=30)
def fetch_directory():
    return supabase.table("directory").select("*").execute().data or []

# ============================================================
# AI USAGE TRACKING
# ============================================================
def log_ai_usage(email: str):
    today = date.today().isoformat()
    res = supabase.table("ai_usage").select("*").eq("email", email).eq("day", today).execute()
    if res.data:
        row = res.data[0]
        supabase.table("ai_usage").update({"count": row["count"] + 1}).eq("id", row["id"]).execute()
        return row["count"] + 1
    supabase.table("ai_usage").insert({"email": email, "day": today, "count": 1}).execute()
    return 1

def get_ai_usage_today(email: str) -> int:
    today = date.today().isoformat()
    res = supabase.table("ai_usage").select("*").eq("email", email).eq("day", today).execute()
    return res.data[0]["count"] if res.data else 0

# ============================================================
# SETTINGS & ERROR LOGGING
# ============================================================
def get_setting(key: str, default: str = "") -> str:
    try:
        res = supabase.table("app_settings").select("value").eq("key", key).execute()
        return res.data[0]["value"] if res.data else default
    except Exception:
        return default

def set_setting(key: str, value: str):
    existing = supabase.table("app_settings").select("key").eq("key", key).execute()
    if existing.data:
        supabase.table("app_settings").update({"value": value}).eq("key", key).execute()
    else:
        supabase.table("app_settings").insert({"key": key, "value": value}).execute()

def log_error(area: str, message: str):
    try:
        supabase.table("error_log").insert({
            "area": area,
            "message": str(message)[:2000],
            "occurred_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception:
        pass

# ============================================================
# AI PROVIDERS (Gemini, Groq, Qwen)
# ============================================================
def ask_ai(user_prompt: str, sys_context: str, provider_override: Optional[str] = None, api_key_override: Optional[str] = None):
    """Unified AI interface supporting Gemini, Groq, and Qwen"""
    provider = (provider_override or get_setting("ai_provider", "gemini")).lower()
    
    if provider == "groq":
        api_key = api_key_override or get_setting("groq_api_key") or st.secrets.get("GROQ_API_KEY", "")
        model_id = get_setting("groq_model", "llama-3.1-8b-instant")
        if not api_key:
            return None, "No Groq API key set. Add one in Admin Panel → Settings."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
            response = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "system", "content": sys_context}, {"role": "user", "content": user_prompt}],
            )
            return response.choices[0].message.content, None
        except Exception as e:
            return None, f"Groq error: {e}"
    
    elif provider == "qwen":
        api_key = api_key_override or get_setting("qwen_api_key") or st.secrets.get("QWEN_API_KEY", "")
        model_id = get_setting("qwen_model", "qwen-plus")
        base_url = get_setting("qwen_base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        if not api_key:
            return None, "No Qwen API key set. Add one in Admin Panel → Settings."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url)
            response = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "system", "content": sys_context}, {"role": "user", "content": user_prompt}],
            )
            return response.choices[0].message.content, None
        except Exception as e:
            return None, f"Qwen error: {e}"
    
    else:  # gemini (default)
        api_key = api_key_override or get_setting("gemini_api_key") or st.secrets.get("GEMINI_API_KEY", "")
        model_id = get_setting("gemini_model", "gemini-1.5-flash")
        if not api_key:
            return None, "No Gemini API key set. Add one in Admin Panel → Settings."
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_id)
            response = model.generate_content(f"{sys_context}\n\nQuestion: {user_prompt}")
            return response.text, None
        except Exception as e:
            return None, f"Gemini error: {e}"

# ============================================================
# SESSION MANAGEMENT
# ============================================================
def create_session_token(email: str) -> str:
    token = pysecrets.token_urlsafe(32)
    expires_at = (datetime.utcnow() + timedelta(days=SESSION_DAYS)).isoformat()
    supabase.table("sessions").insert({"token": token, "email": email, "expires_at": expires_at}).execute()
    return token

def get_user_from_token(token: str):
    if not token:
        return None
    res = supabase.table("sessions").select("*").eq("token", token).execute()
    if not res.data:
        return None
    session = res.data[0]
    if session["expires_at"] < datetime.utcnow().isoformat():
        supabase.table("sessions").delete().eq("token", token).execute()
        return None
    user = get_user(session["email"])
    if user and user.get("active", True) is False:
        supabase.table("sessions").delete().eq("token", token).execute()
        return None
    return user

def clear_session_token(token: str):
    if token:
        supabase.table("sessions").delete().eq("token", token).execute()
    try:
        cookies.remove(COOKIE_NAME)
    except Exception:
        pass

def try_auto_login():
    if st.session_state.logged_in:
        return
    try:
        user = get_user_from_token(cookies.get(COOKIE_NAME))
    except Exception:
        user = None
    if user:
        st.session_state.logged_in = True
        st.session_state.user = user

# ============================================================
# R2 STORAGE & OCR (for PDF processing)
# ============================================================
@st.cache_resource
def get_r2_client():
    import boto3
    return boto3.client(
        "s3",
        endpoint_url=f"https://{st.secrets['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=st.secrets["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )

def upload_to_r2(file_bytes: bytes, object_name: str) -> str:
    s3 = get_r2_client()
    s3.put_object(
        Bucket=st.secrets["R2_BUCKET_NAME"],
        Key=object_name,
        Body=file_bytes,
        ContentType="application/pdf",
    )
    return f"{st.secrets['R2_PUBLIC_URL'].rstrip('/')}/{object_name}"

def extract_pdf_text(file_bytes: bytes):
    import fitz
    import pytesseract
    from PIL import Image, ImageEnhance, ImageOps
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        log_error("pdf_open", str(e))
        return "", False
    
    all_text, used_ocr, ocr_done = [], False, 0
    for page_num, page in enumerate(doc):
        try:
            page_text = page.get_text().strip()
        except Exception:
            page_text = ""
        
        if len(page_text) > 40:
            all_text.append(page_text)
        else:
            if ocr_done >= OCR_MAX_PAGES:
                all_text.append(f"[Page {page_num + 1}: scanned — OCR limit reached]")
                continue
            try:
                pix = page.get_pixmap(dpi=200)
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                img = ImageOps.autocontrast(img.convert("L"))
                img = ImageEnhance.Sharpness(img).enhance(2.0)
                page_text = pytesseract.image_to_string(img, config="--psm 6").strip()
                all_text.append(page_text)
                used_ocr = True
                ocr_done += 1
            except Exception as e:
                log_error("pdf_ocr", f"page {page_num + 1}: {e}")
                all_text.append(f"[Page {page_num + 1}: OCR failed]")
    
    doc.close()
    return "\n".join(all_text).strip(), used_ocr

def optimize_pdf(file_bytes: bytes) -> bytes:
    import fitz
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        buf = io.BytesIO()
        doc.save(buf, garbage=3, deflate=True)
        doc.close()
        out = buf.getvalue()
        return out if len(out) < len(file_bytes) else file_bytes
    except Exception as e:
        log_error("pdf_optimize", str(e))
        return file_bytes

def chunk_text(text: str, chunk_size: int = 1200):
    text = text.strip()
    if not text:
        return []
    return [text[i:i + chunk_size].strip() for i in range(0, len(text), chunk_size) if text[i:i + chunk_size].strip()]

def index_circular_for_ai(circular_id: str, text: str) -> int:
    try:
        supabase.table("circular_chunks").delete().eq("circular_id", circular_id).execute()
        chunks = chunk_text(text)
        if not chunks:
            supabase.table("circulars").update({"ai_indexed": False}).eq("id", circular_id).execute()
            return 0
        for i, ch in enumerate(chunks):
            supabase.table("circular_chunks").insert({
                "circular_id": circular_id,
                "chunk_no": i,
                "content": ch,
            }).execute()
        supabase.table("circulars").update({"ai_indexed": True}).eq("id", circular_id).execute()
        return len(chunks)
    except Exception as e:
        log_error("ai_indexing", str(e))
        return 0

def search_uploaded_circulars(question: str, limit: int = 4):
    try:
        # Try optimized function first, fall back to basic search
        try:
            res = supabase.rpc("search_circular_chunks_optimized", {"q": question, "limit_count": limit}).execute()
        except Exception:
            res = supabase.rpc("search_circular_chunks", {"q": question, "limit_count": limit}).execute()
        return res.data or []
    except Exception as e:
        log_error("ai_search", str(e))
        return []

# Continue in next part due to size...
