import io
import secrets as pysecrets
from datetime import date, datetime, timedelta

import bcrypt
import pandas as pd
import streamlit as st
from supabase import create_client, Client
from streamlit_cookies_controller import CookieController

# ============================================================
# GOVDOCS AI — STREAMLIT REDESIGN
# Professional Government SaaS UI
# Backend logic preserved: Supabase + R2 + OCR + AI + sessions
# ============================================================

st.set_page_config(
    page_title="GovDocs AI — Government Workspace",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# DESIGN SYSTEM
# ============================================================
CUSTOM_CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --navy-900:#16324F;
  --navy-800:#1E3A5F;
  --navy-700:#2C5282;
  --blue:#2563EB;
  --blue-soft:#EFF6FF;
  --indigo:#6366F1;
  --indigo-soft:#EEF2FF;
  --green:#16A34A;
  --green-soft:#F0FDF4;
  --purple:#7C3AED;
  --purple-soft:#F5F3FF;
  --canvas:#F7F9FB;
  --surface:#FFFFFF;
  --border:#E2E8F0;
  --border-strong:#CBD5E1;
  --text:#0F172A;
  --muted:#64748B;
  --muted-2:#94A3B8;
  --danger:#DC2626;
  --warning:#D97706;
  --shadow:0 2px 10px rgba(15,23,42,.05);
  --shadow-md:0 8px 24px rgba(15,23,42,.08);
  --shadow-lg:0 18px 45px rgba(15,23,42,.12);
  --radius-lg:16px;
  --radius-md:12px;
  --radius-sm:9px;
}

html, body, [class*="css"] {
  font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
}
body { background:var(--canvas); }
.stApp {
  background:var(--canvas);
  color:var(--text);
}
#MainMenu, footer, header { visibility:hidden; }
.block-container { padding-top:1.35rem; padding-bottom:3rem; max-width:1500px; }
h1,h2,h3,h4 { color:var(--text); font-weight:700; letter-spacing:-.025em; }
p, label, .stMarkdown { color:var(--text); }
::selection { background:#DBEAFE; }

/* Sidebar */
section[data-testid="stSidebar"] {
  background:#FFFFFF !important;
  border-right:1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div:first-child { padding:1rem .8rem; }
section[data-testid="stSidebar"] .stRadio > div { gap:4px; }
section[data-testid="stSidebar"] .stRadio > div > label {
  border-radius:10px;
  padding:.62rem .75rem;
  margin:0;
  color:#334155;
  font-weight:500;
  transition:.15s ease;
}
section[data-testid="stSidebar"] .stRadio > div > label:hover { background:#F1F5F9; }
section[data-testid="stSidebar"] .stRadio > div > label:has(div[aria-checked="true"]) {
  background:#EAF2FF;
  color:var(--navy-800);
  font-weight:700;
}
section[data-testid="stSidebar"] .stRadio > div > label p { color:inherit !important; }

.sidebar-brand {
  display:flex; align-items:center; gap:10px;
  padding:.45rem .35rem 1.1rem;
  border-bottom:1px solid var(--border);
  margin-bottom:1rem;
}
.sidebar-logo {
  width:38px;height:38px;border-radius:10px;
  background:var(--navy-800);color:white;
  display:flex;align-items:center;justify-content:center;
  font-size:20px;
}
.sidebar-brand-title { font-size:17px;font-weight:800;color:var(--navy-900);line-height:1.1; }
.sidebar-brand-sub { font-size:10px;color:var(--muted);margin-top:3px; }

.profile-card {
  background:#F8FAFC;
  border:1px solid var(--border);
  border-radius:12px;
  padding:12px;
  margin-bottom:12px;
}
.profile-name { font-size:13px;font-weight:700;color:var(--text); }
.profile-email { font-size:10px;color:var(--muted);margin-top:3px;overflow:hidden;text-overflow:ellipsis; }
.profile-role { margin-top:9px;display:flex;align-items:center;justify-content:space-between; }

/* Header */
.app-topbar {
  display:flex;align-items:center;justify-content:space-between;
  background:#FFFFFF;border:1px solid var(--border);
  border-radius:14px;padding:13px 18px;margin-bottom:18px;
  box-shadow:var(--shadow);
}
.app-topbar-title { font-size:13px;font-weight:700;color:var(--navy-800); }
.app-topbar-sub { font-size:11px;color:var(--muted);margin-top:2px; }

.page-header {
  margin-bottom:20px;
}
.page-header h1 { margin:0;font-size:27px; }
.page-header p { margin:5px 0 0;color:var(--muted);font-size:13px; }

/* Cards */
.card {
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:var(--radius-lg);
  padding:18px;
  box-shadow:var(--shadow);
}
.card:hover { box-shadow:var(--shadow-md); }
.card-tight { padding:14px; }

.kpi-card {
  background:#FFFFFF;border:1px solid var(--border);border-radius:14px;
  padding:16px;box-shadow:var(--shadow);min-height:112px;
}
.kpi-label { color:var(--muted);font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.5px; }
.kpi-value { color:var(--text);font-size:25px;font-weight:800;margin-top:8px; }
.kpi-foot { color:var(--muted);font-size:10px;margin-top:3px; }

/* Buttons */
.stButton > button {
  border:1px solid var(--border-strong) !important;
  background:#FFFFFF !important;
  color:var(--navy-800) !important;
  border-radius:9px !important;
  font-weight:600 !important;
  min-height:38px;
  transition:.15s ease;
}
.stButton > button:hover { border-color:#94A3B8 !important; box-shadow:var(--shadow); }
.stButton > button[kind="primary"] {
  background:var(--navy-800) !important;
  color:#FFFFFF !important;
  border-color:var(--navy-800) !important;
}
.stButton > button[kind="primary"]:hover { background:var(--navy-700) !important; }

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div,
.stDateInput > div > div > input,
.stNumberInput > div > div > input {
  background:#FFFFFF !important;
  border:1px solid var(--border-strong) !important;
  border-radius:9px !important;
  color:var(--text) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color:#60A5FA !important;
  box-shadow:0 0 0 3px rgba(37,99,235,.10) !important;
}
[data-baseweb="select"] > div { border-color:var(--border-strong) !important;border-radius:9px !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  gap:2px;background:#EEF2F6;padding:3px;border-radius:10px;border:none;
}
.stTabs [data-baseweb="tab"] {
  border-radius:8px;color:#475569;font-weight:600;font-size:12px;
}
.stTabs [aria-selected="true"] {
  background:#FFFFFF !important;color:var(--navy-800) !important;
  box-shadow:0 1px 4px rgba(15,23,42,.08);
}

/* Document cards */
.doc-card {
  background:#FFFFFF;border:1px solid var(--border);border-radius:14px;
  padding:15px 16px;margin:0 0 9px;box-shadow:var(--shadow);
}
.doc-card:hover { border-color:#CBD5E1;box-shadow:var(--shadow-md); }
.doc-row { display:flex;justify-content:space-between;gap:12px;align-items:flex-start; }
.doc-ref { color:var(--navy-700);background:#EFF6FF;border:1px solid #DBEAFE;border-radius:999px;padding:4px 9px;font-size:10px;font-weight:700; }
.doc-title { font-size:14px;font-weight:700;color:var(--text);margin-top:9px; }
.doc-meta { display:flex;flex-wrap:wrap;gap:10px;color:var(--muted);font-size:10px;margin-top:6px; }
.badge { display:inline-flex;align-items:center;gap:4px;padding:4px 9px;border-radius:999px;font-size:10px;font-weight:700; }
.badge-basic { background:#F1F5F9;color:#475569;border:1px solid #E2E8F0; }
.badge-pro { background:#EFF6FF;color:#1D4ED8;border:1px solid #BFDBFE; }
.badge-max { background:#F5F3FF;color:#6D28D9;border:1px solid #DDD6FE; }
.badge-success { background:#F0FDF4;color:#15803D;border:1px solid #BBF7D0; }
.badge-danger { background:#FEF2F2;color:#B91C1C;border:1px solid #FECACA; }

/* Billing */
.plan-card {
  background:#FFFFFF;border:1px solid var(--border);border-radius:16px;
  padding:21px;min-height:405px;position:relative;box-shadow:var(--shadow);
}
.plan-card.featured { border:2px solid var(--navy-700);box-shadow:0 12px 32px rgba(44,82,130,.13); }
.plan-card.max { border-color:#C4B5FD; }
.plan-pill {
  position:absolute;right:18px;top:-12px;background:var(--navy-800);color:#fff;
  border-radius:999px;padding:5px 10px;font-size:9px;font-weight:800;
}
.plan-name { font-size:17px;font-weight:800; }
.plan-price { font-size:30px;font-weight:800;margin-top:13px; }
.plan-period { color:var(--muted);font-size:11px; }
.plan-description { color:var(--muted);font-size:11px;min-height:34px;margin-top:5px; }
.feature { font-size:11px;color:#475569;margin:10px 0; }
.feature::first-letter { color:var(--green); }

/* Chat */
div[data-testid="stChatMessage"] {
  border:1px solid var(--border);border-radius:13px;margin-bottom:10px;
  background:#FFFFFF;
}
div[data-testid="stChatInput"] > div {
  border:1px solid var(--border-strong) !important;
  border-radius:13px !important;background:#FFFFFF !important;
}
.ai-control {
  background:#FFFFFF;border:1px solid var(--border);border-radius:12px;padding:13px;margin-bottom:14px;
}

/* Tapal */
.tapal-card {
  background:#FFFFFF;border:1px solid var(--border);border-radius:13px;
  padding:14px;margin-bottom:9px;box-shadow:var(--shadow);
}
.tapal-inward { border-left:4px solid var(--navy-700); }
.tapal-outward { border-left:4px solid #16A34A; }

/* Admin */
.admin-tab-card { background:#FFFFFF;border:1px solid var(--border);border-radius:14px;padding:18px; }
.status-dot { width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:5px; }
.status-good { background:#22C55E; }
.status-bad { background:#EF4444; }

/* Login */
.login-shell {
  min-height:78vh;display:flex;align-items:center;justify-content:center;
  padding:30px 10px;
}
.login-panel {
  width:min(920px,100%);background:#FFFFFF;border:1px solid var(--border);
  border-radius:20px;box-shadow:var(--shadow-lg);overflow:hidden;display:grid;grid-template-columns:1fr 1.05fr;
}
.login-brand {
  background:linear-gradient(150deg,#16324F,#2C5282);padding:48px;color:#FFFFFF;
  display:flex;flex-direction:column;justify-content:center;min-height:510px;
}
.login-brand h1 { color:#FFFFFF;font-size:32px;margin:12px 0 8px; }
.login-brand p { color:rgba(255,255,255,.78);font-size:12px;line-height:1.7; }
.login-mark { width:52px;height:52px;border-radius:14px;background:rgba(255,255,255,.12);display:flex;align-items:center;justify-content:center;font-size:27px;border:1px solid rgba(255,255,255,.18); }
.login-form { padding:38px 40px; }
.login-form h2 { font-size:22px;margin:0 0 5px; }
.login-form .muted { color:var(--muted);font-size:12px;margin-bottom:18px; }
@media(max-width:900px){
  .login-panel { grid-template-columns:1fr; }
  .login-brand { min-height:auto;padding:28px; }
  .login-brand p { margin-bottom:0; }
  .login-form { padding:28px 22px; }
}

/* Mobile */
@media(max-width:700px){
  .block-container { padding:12px 10px 30px; }
  .page-header h1 { font-size:22px; }
  .doc-row { flex-direction:column; }
  .doc-meta { gap:6px; }
  .plan-card { min-height:auto; }
}

hr { border-color:var(--border) !important; }
[data-testid="stDataFrame"] { border:1px solid var(--border);border-radius:10px;overflow:hidden; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ============================================================
# HELPERS
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
# SUPABASE / COOKIES
# ============================================================
@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


supabase = get_supabase()
cookies = CookieController()
COOKIE_NAME = "huddle_session"
SESSION_DAYS = 30

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []

DAILY_AI_LIMIT = 20
MAX_UPLOAD_MB = 20
OCR_MAX_PAGES = 40

# ============================================================
# AUTH
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
# CACHED DATA
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
# SETTINGS / ERRORS
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
# AI / R2 / OCR
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
        res = supabase.rpc("search_circular_chunks", {"q": question, "limit_count": limit}).execute()
        return res.data or []
    except Exception as e:
        log_error("ai_search", str(e))
        return []


def ask_ai(user_prompt: str, sys_context: str, provider_override: str | None = None, api_key_override: str | None = None):
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
                messages=[
                    {"role": "system", "content": sys_context},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content, None
        except Exception as e:
            return None, f"Groq error: {e}"

    if provider == "qwen":
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
                messages=[
                    {"role": "system", "content": sys_context},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content, None
        except Exception as e:
            return None, f"Qwen error: {e}"

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
# AI USAGE
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
# LOGIN PAGE
# ============================================================
def show_login():
    st.markdown(
        """
        <div class="login-shell">
          <div class="login-panel">
            <div class="login-brand">
              <div class="login-mark">🏛️</div>
              <h1>GovDocs AI</h1>
              <p>AI-powered government document workspace for circulars, G.O.s, Tapal, templates and internal rules assistance.</p>
              <div style="margin-top:25px;font-size:11px;color:rgba(255,255,255,.72);line-height:1.8;">
                <b style="color:#fff;">Designed for staff workflows</b><br>
                Search records faster · Read documents with AI · Keep office correspondence organized
              </div>
            </div>
            <div class="login-form">
              <h2>Welcome back</h2>
              <div class="muted">Sign in with your authorized staff account.</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1.35, 1])
    with col2:
        tab_login, tab_request = st.tabs(["Sign In", "Request Access"])
        with tab_login:
            email = st.text_input("Email", key="login_email", placeholder="name@department.gov")
            password = st.text_input("Password", type="password", key="login_pass")
            remember = st.checkbox("Remember me", value=True)
            if st.button("Sign In →", use_container_width=True, type="primary"):
                user = get_user(email.strip().lower())
                if user and user.get("active", True) is False:
                    st.error("This account has been deactivated. Contact your administrator.")
                elif user and check_password(password, user["password_hash"]):
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    if remember:
                        token = create_session_token(user["email"])
                        cookies.set(COOKIE_NAME, token, max_age=SESSION_DAYS * 24 * 3600)
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
            st.caption("Secure access for authorized personnel only.")

        with tab_request:
            st.info("New staff and NGO volunteers can submit an access request. An administrator creates the account.")
            req_name = st.text_input("Full Name", key="req_name")
            req_email = st.text_input("Email", key="req_email")
            req_role = st.text_input("Role / Designation", key="req_role")
            req_department = st.text_input("Department / NGO", key="req_department")
            req_note = st.text_area("Additional note", key="req_note", height=90)
            if st.button("Submit Request →", use_container_width=True, type="primary"):
                if req_name.strip() and req_email.strip():
                    note = f"Role: {req_role.strip()} | Department: {req_department.strip()} | {req_note.strip()}"
                    create_pending_request(req_name.strip(), req_email.strip().lower(), note)
                    st.success("Request submitted. The administrator will contact you after review.")
                else:
                    st.warning("Please enter your name and email.")


# ============================================================
# SIDEBAR
# ============================================================
def render_sidebar(user):
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
              <div class="sidebar-logo">🏛️</div>
              <div><div class="sidebar-brand-title">GovDocs AI</div><div class="sidebar-brand-sub">Government Workspace</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="profile-card">
              <div class="profile-name">{safe_str(user.get('name'))}</div>
              <div class="profile-email">{safe_str(user.get('email'))}</div>
              <div class="profile-role"><span style="font-size:10px;color:#64748B;">Access tier</span>{tier_badge(user.get('tier','Staff'))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        options = [
            "🏠 Dashboard", "📢 Circulars & G.O.s", "🤖 AI Rules Assistant",
            "📝 Templates", "✉️ Tapal Register", "📮 Dispatch Labels",
            "📞 Staff Directory", "💳 Plans & Billing", "⚙️ Admin Command Center",
        ]
        menu = st.radio("Navigation", options, label_visibility="collapsed")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            clear_session_token(cookies.get(COOKIE_NAME))
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.messages = []
            st.rerun()
    return menu


# ============================================================
# TOPBAR
# ============================================================
def topbar(user):
    tier = user.get("tier", "Staff")
    st.markdown(
        f"""
        <div class="app-topbar">
          <div><div class="app-topbar-title">Government Document & Rules Workspace</div><div class="app-topbar-sub">Internal productivity tools · Always verify official rules before action</div></div>
          <div style="display:flex;align-items:center;gap:8px;font-size:11px;color:#64748B;">{tier_badge(tier)} <span>{safe_str(user.get('name'))}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# DASHBOARD
# ============================================================
def show_home(user):
    page_header(f"{greeting()}, {user['name'].split()[0]} 👋", "Here's your workspace overview.")
    circ_count = len(fetch_circulars())
    this_month_start = date.today().replace(day=1).isoformat()
    tapal_count = len([r for r in fetch_tapal() if safe_str(r.get("tapal_date")) >= this_month_start])
    ai_used = get_ai_usage_today(user["email"])

    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        ("Circulars on file", circ_count, "Indexed and available records"),
        ("Tapal this month", tapal_count, "Inward + outward entries"),
        ("AI queries today", f"{ai_used}/{DAILY_AI_LIMIT}", "Daily usage allowance"),
        ("Access tier", user.get("tier", "Staff"), "Current workspace level"),
    ]
    for col, (label, value, foot) in zip((c1, c2, c3, c4), metrics):
        with col:
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>{label}</div><div class='kpi-value'>{value}</div><div class='kpi-foot'>{foot}</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    left, right = st.columns([1.55, 1])
    with left:
        st.markdown("### Quick access")
        items = [
            ("📢", "Circulars & G.O.s", "Search references, subjects and departments."),
            ("🤖", "AI Rules Assistant", "Ask questions against your indexed circulars."),
            ("✉️", "Tapal Register", "Log and browse inward/outward correspondence."),
            ("📝", "Templates", "Access approved office formats."),
        ]
        for icon, title, desc in items:
            st.markdown(f"<div class='doc-card'><div class='doc-title'>{icon} {title}</div><div class='doc-meta'>{desc}</div></div>", unsafe_allow_html=True)
    with right:
        st.markdown("### Workspace notes")
        with st.container(border=True):
            st.markdown("**AI answers are decision support, not official orders.**")
            st.caption("Confirm current G.O.s, circulars and establishment instructions before taking official action.")
            st.markdown("**Document access**")
            st.caption("Pro and Max records are protected by your account tier.")
            st.markdown("**System storage**")
            st.caption("Documents can be stored in Cloudflare R2 and indexed for internal AI search.")


# ============================================================
# CIRCULARS
# ============================================================
def show_circulars(user):
    page_header("Circulars, G.O.s & Memos", "Search departmental documents using reference number, subject, category or year.")
    c1, c2, c3 = st.columns([2.8, 1.1, 1])
    with c1:
        query = st.text_input("Search documents", placeholder="Search by G.O. number, title, subject or keyword...", label_visibility="collapsed")
    with c2:
        category = st.selectbox("Category", ["All", "Finance / HR", "Operations", "Confidential", "Executive"], label_visibility="collapsed")
    with c3:
        year_filter = st.selectbox("Year", ["All"] + [str(y) for y in sorted({r.get("year") for r in fetch_circulars() if r.get("year")}, reverse=True)], label_visibility="collapsed")

    rows = fetch_circulars()
    if category != "All":
        rows = [r for r in rows if r.get("category") == category]
    if year_filter != "All":
        rows = [r for r in rows if safe_str(r.get("year")) == year_filter]
    if query.strip():
        q = query.lower().strip()
        rows = [r for r in rows if q in safe_str(r.get("title")).lower() or q in safe_str(r.get("ref_id")).lower() or q in safe_str(r.get("category")).lower()]

    st.caption(f"{len(rows)} document(s) found")
    if not rows:
        st.info("No documents match your filters.")
        return

    for item in rows:
        tier = item.get("tier", "Basic")
        allowed = has_access(user.get("tier", "Staff"), tier)
        lock = "" if allowed else "🔒 "
        action_label = "📥 Open Document" if allowed else f"Upgrade to {tier}"
        st.markdown(
            f"""
            <div class="doc-card">
              <div class="doc-row">
                <span class="doc-ref">{safe_str(item.get('ref_id'))}</span>
                {tier_badge(tier)}
              </div>
              <div class="doc-title">{lock}{safe_str(item.get('title'))}</div>
              <div class="doc-meta"><span>📅 {safe_str(item.get('doc_date'))}</span><span>📁 {safe_str(item.get('category'))}</span><span>📆 {safe_str(item.get('year'))}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if allowed:
            st.markdown(f"[📥 Open Document]({safe_str(item.get('link'))})")
        else:
            if st.button(f"🔒 {action_label}", key=f"upgrade_circ_{item.get('id')}"):
                st.session_state["billing_hint"] = tier
                st.info(f"This document requires {tier} access. Open Plans & Billing from the sidebar to upgrade.")


# ============================================================
# AI ASSISTANT
# ============================================================
def show_ai(user):
    page_header("AI Rules Assistant", "Ask about leave, TA/DA, service rules and indexed office circulars.")
    used = get_ai_usage_today(user["email"])

    with st.container(border=True):
        c1, c2, c3 = st.columns([1.1, 1.9, 1])
        with c1:
            provider = st.selectbox("Model", ["Gemini", "Groq", "Qwen"], key="ai_provider_ui")
        with c2:
            custom_key = st.text_input("Custom API key (optional)", type="password", placeholder="Power-user key; leave blank for system key")
        with c3:
            st.markdown(f"<div style='padding-top:29px;text-align:right;color:#64748B;font-size:11px;'>AI queries used: <b>{used}/{DAILY_AI_LIMIT}</b></div>", unsafe_allow_html=True)

    if st.session_state.messages:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])
    else:
        with st.container(border=True):
            st.markdown("**Try asking:**")
            st.markdown("- What are the rules for earned leave?\n- Which circular covers the latest TA/DA revision?\n- What documents are required for this process?")

    if used >= DAILY_AI_LIMIT:
        st.warning("Daily AI limit reached. Try again tomorrow or ask an administrator about your plan limit.")
        return

    user_input = st.chat_input("Ask about rules, circulars, policies or office procedures...")
    if not user_input:
        return

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    provider_code = provider.lower()
    with st.chat_message("assistant"):
        sources = search_uploaded_circulars(user_input, limit=4)
        if sources:
            source_text = ""
            for i, s in enumerate(sources, 1):
                source_text += f"\n--- Source {i}: {s.get('ref_id')} — {s.get('title')} ---\n{s.get('content','')}\n"
            sys_context = (
                "You are an internal staff knowledge assistant for a state transport department office. "
                "Use the OFFICE CIRCULAR EXCERPTS below as your PRIMARY source. "
                "If the answer is in the excerpts, answer from them and quote the reference number. "
                "If the answer is NOT in the excerpts, say 'Not found in the uploaded circulars' and then give brief general guidance. "
                "Never invent G.O. or circular numbers. Be concise. Always tell the user to confirm against the current G.O. or establishment section.\n\n"
                f"OFFICE CIRCULAR EXCERPTS:\n{source_text}"
            )
        else:
            sys_context = (
                "You are an internal staff knowledge assistant for a state transport department office. "
                "No uploaded circulars matched this question. Start your answer with 'Not found in the uploaded circulars.' "
                "Then provide brief general guidance using known Indian state civil-service concepts. Do not invent G.O. numbers. "
                "Always tell the user to confirm against the current G.O. or establishment section."
            )

        with st.spinner("Checking indexed documents and rules..."):
            reply, err = ask_ai(user_input, sys_context, provider_override=provider_code, api_key_override=custom_key.strip() or None)
        if err:
            log_error("ai_assistant", err)
            st.error("Couldn't reach the AI engine right now.")
            st.caption("An administrator can inspect Admin Command Center → Health & Diagnostics for the exact error.")
        else:
            st.markdown(reply)
            if sources:
                st.markdown("**📄 Matched circulars**")
                for s in sources:
                    st.caption(f"• {s.get('ref_id')} — {s.get('title')}")
            else:
                st.caption("No matching uploaded circulars — answer is based on general guidance.")
            st.session_state.messages.append({"role": "assistant", "content": reply})
            log_ai_usage(user["email"])


# ============================================================
# TEMPLATES
# ============================================================
def show_templates(user):
    page_header("Drafts & Templates", "Pre-approved office formats, organized by access tier.")
    rows = fetch_templates()
    if not rows:
        st.info("No templates are available yet. Ask an administrator to publish one.")
        return
    for t in rows:
        tier = t.get("tier", "Basic")
        allowed = has_access(user.get("tier", "Staff"), tier)
        st.markdown(
            f"""
            <div class="doc-card">
              <div class="doc-row"><span class="doc-ref">Template</span>{tier_badge(tier)}</div>
              <div class="doc-title">{safe_str(t.get('title'))}</div>
              <div class="doc-meta">📝 {safe_str(t.get('description') or 'No description')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if allowed and t.get("link"):
            st.markdown(f"[📥 Download Template]({safe_str(t.get('link'))})")
        elif not allowed:
            st.warning(f"🔒 Requires {tier} access or higher")


# ============================================================
# TAPAL
# ============================================================
def show_tapal(user):
    page_header("Tapal Workspace", "Log, browse and report inward/outward correspondence.")
    tab_add, tab_view, tab_report = st.tabs(["➕ New Entry", "📋 Browse", "📊 Monthly Report"])

    with tab_add:
        with st.container(border=True):
            with st.form("tapal_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    direction = st.selectbox("Direction", ["Inward", "Outward"])
                    tapal_date = st.date_input("Date", value=date.today(), max_value=date.today())
                    from_to = st.text_input("From / To *", placeholder="Sender for Inward, recipient for Outward")
                with c2:
                    subject = st.text_input("Subject *")
                    file_ref = st.text_input("File / Reference No.")
                    remarks = st.text_area("Remarks", height=85)
                if st.form_submit_button("Save Entry", type="primary", use_container_width=True):
                    if not from_to.strip() or not subject.strip():
                        st.warning("From/To and Subject are required.")
                    else:
                        supabase.table("tapal_log").insert({
                            "direction": direction,
                            "tapal_date": tapal_date.isoformat(),
                            "from_to": from_to.strip(),
                            "subject": subject.strip(),
                            "file_ref": file_ref.strip() or None,
                            "remarks": remarks.strip() or None,
                            "entered_by": user["email"],
                            "entered_at": datetime.utcnow().isoformat(),
                        }).execute()
                        fetch_tapal.clear()
                        st.success("Entry saved successfully.")

    with tab_view:
        rows = fetch_tapal()
        c1, c2 = st.columns([3, 1])
        with c1:
            search = st.text_input("Search Tapal", placeholder="Search name, subject or reference...", label_visibility="collapsed")
        with c2:
            direction_filter = st.selectbox("Direction", ["All", "Inward", "Outward"], label_visibility="collapsed")
        if search:
            q = search.lower()
            rows = [r for r in rows if q in str(r).lower()]
        if direction_filter != "All":
            rows = [r for r in rows if r.get("direction") == direction_filter]
        st.caption(f"{len(rows)} record(s) found")
        for r in rows:
            inward = r.get("direction") == "Inward"
            cls = "tapal-inward" if inward else "tapal-outward"
            icon = "📥" if inward else "📤"
            ref = f" · Ref: {safe_str(r.get('file_ref'))}" if r.get("file_ref") else ""
            remarks = f"<br><span style='font-size:10px;color:#64748B;'>📝 {safe_str(r.get('remarks'))}</span>" if r.get("remarks") else ""
            st.markdown(
                f"""
                <div class="tapal-card {cls}">
                  <div style="font-weight:700;font-size:13px;">{icon} {safe_str(r.get('subject'))}</div>
                  <div style="font-size:10px;color:#64748B;margin-top:5px;">{safe_str(r.get('from_to'))} · {safe_str(r.get('tapal_date'))}{ref}</div>
                  {remarks}
                </div>
                """,
                unsafe_allow_html=True,
            )

    with tab_report:
        today = date.today()
        c1, c2 = st.columns(2)
        with c1:
            report_month = st.selectbox("Month", list(range(1, 13)), index=today.month - 1, format_func=lambda m: date(2000, m, 1).strftime("%B"))
        with c2:
            report_year = st.number_input("Year", min_value=2020, max_value=2100, value=today.year)
        start = date(report_year, report_month, 1)
        end_month = report_month + 1 if report_month < 12 else 1
        end_year = report_year if report_month < 12 else report_year + 1
        end = date(end_year, end_month, 1)
        res = supabase.table("tapal_log").select("*").gte("tapal_date", start.isoformat()).lt("tapal_date", end.isoformat()).order("tapal_date").execute()
        df = pd.DataFrame(res.data or [])
        if df.empty:
            st.info(f"No Tapal entries for {start.strftime('%B %Y')}.")
        else:
            a, b, c = st.columns(3)
            a.metric("Inward", int((df["direction"] == "Inward").sum()))
            b.metric("Outward", int((df["direction"] == "Outward").sum()))
            c.metric("Total", len(df))
            cols = [c for c in ["tapal_date", "direction", "from_to", "subject", "file_ref", "remarks"] if c in df.columns]
            st.dataframe(df[cols], use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download CSV Report", csv, f"tapal_report_{start:%Y_%m}.csv", "text/csv")


# ============================================================
# DISPATCH
# ============================================================
def show_dispatch(user):
    page_header("Dispatch Label Generator", "Extract an address from a scan/photo and generate print-ready envelope labels.")
    with st.container(border=True):
        st.markdown("**1 · Upload address image**")
        photo = st.file_uploader("Photo or scan", type=["png", "jpg", "jpeg"])
        if photo is not None:
            try:
                import pytesseract
                from PIL import Image, ImageEnhance, ImageOps
                img = Image.open(photo)
                img = ImageOps.exif_transpose(img).convert("L")
                img = ImageOps.autocontrast(img)
                img = ImageEnhance.Sharpness(img).enhance(2.0)
                if img.width < 1500:
                    scale = 1500 / img.width
                    img = img.resize((1500, int(img.height * scale)))
                img = img.point(lambda p: 255 if p > 150 else 0)
                extracted = pytesseract.image_to_string(img, config="--psm 6").strip()
                st.text_area("2 · Review extracted address", value=extracted, height=100, key="ocr_extracted")
                with st.expander("Preview processed image"):
                    st.image(img, use_container_width=True)
            except Exception as e:
                st.warning(f"OCR unavailable or failed: {e}")

        address_text = st.text_area("3 · Final address *", value=st.session_state.get("ocr_extracted", ""), height=130, placeholder="Name\nDesignation / Office\nAddress\nCity - PIN")
        c1, c2, c3 = st.columns(3)
        with c1:
            font_size = st.slider("Font size (pt)", 14, 36, 22)
        with c2:
            envelope_choice = st.selectbox("Envelope size", ["Long Cover (approx 10 x 4.5 in)", "C5 (229 x 162 mm)", "DL (220 x 110 mm)", "Custom"])
        with c3:
            copies = st.number_input("Copies", min_value=1, max_value=100, value=1)
        presets = {"Long Cover (approx 10 x 4.5 in)": (254, 114), "C5 (229 x 162 mm)": (229, 162), "DL (220 x 110 mm)": (220, 110)}
        if envelope_choice == "Custom":
            a, b = st.columns(2)
            width_mm = a.number_input("Width (mm)", 50, 400, 220)
            height_mm = b.number_input("Height (mm)", 50, 400, 110)
        else:
            width_mm, height_mm = presets[envelope_choice]
        if st.button("🖨️ Generate Label PDF", type="primary", use_container_width=True):
            if not address_text.strip():
                st.warning("Please enter an address.")
                return
            try:
                from reportlab.lib.units import mm
                from reportlab.pdfgen import canvas
                buf = io.BytesIO()
                page_w, page_h = width_mm * mm, height_mm * mm
                c = canvas.Canvas(buf, pagesize=(page_w, page_h))
                lines = [ln for ln in address_text.strip().split("\n") if ln.strip()]
                line_height = font_size * 1.4
                for _ in range(int(copies)):
                    c.setFont("Helvetica-Bold", font_size)
                    block_height = len(lines) * line_height
                    y = (page_h + block_height) / 2 - line_height
                    for ln in lines:
                        c.drawString(10 * mm, y, ln)
                        y -= line_height
                    c.showPage()
                c.save()
                buf.seek(0)
                supabase.table("dispatch_log").insert({
                    "address_text": address_text.strip(), "copies": int(copies),
                    "generated_by": user["email"], "generated_at": datetime.utcnow().isoformat(),
                }).execute()
                st.success(f"Generated {copies} label(s).")
                st.download_button("📥 Download Label PDF", buf, "dispatch_labels.pdf", "application/pdf")
            except Exception as e:
                st.error(f"Couldn't generate the PDF: {e}")


# ============================================================
# DIRECTORY
# ============================================================
def show_directory(user):
    page_header("Staff Directory", "Find contacts across departments and roles.")
    df = pd.DataFrame(fetch_directory())
    search = st.text_input("Search directory", placeholder="Search name, division, role or office...")
    if search and not df.empty:
        q = search.lower()
        df = df[df.apply(lambda r: q in " ".join(map(str, r.values)).lower(), axis=1)]
    if df.empty:
        st.info("No staff records found.")
        return
    st.dataframe(df, use_container_width=True, hide_index=True)


# ============================================================
# BILLING
# ============================================================
def show_billing(user):
    page_header("Plans & Billing", "Choose the workspace level that matches your document and AI needs.")
    cycle = st.radio("Billing cycle", ["Monthly", "Yearly"], horizontal=True, index=0, label_visibility="collapsed")
    yearly = cycle == "Yearly"

    pro_price = "₹3,588" if yearly else "₹299"
    max_price = "₹9,588" if yearly else "₹799"
    pro_period = "year" if yearly else "month"
    max_period = "year" if yearly else "month"

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div class="plan-card">
              <div class="plan-name">Basic</div>
              <div class="plan-price">₹0 <span class="plan-period">/ month</span></div>
              <div class="plan-description">Essential tools for everyday office work.</div>
              <div class="feature">✓ Standard circular reference</div><div class="feature">✓ Tapal register</div><div class="feature">✓ Directory access</div><div class="feature">✓ Daily rate-limited AI queries</div><div class="feature">✓ Core office tools</div>
            </div>
            """, unsafe_allow_html=True)
        st.button("Current plan" if user.get("tier") in ("Basic", "Staff") else "Get Started", disabled=True, use_container_width=True, key="basic_plan")
    with c2:
        st.markdown(
            f"""
            <div class="plan-card featured">
              <div class="plan-pill">MOST POPULAR</div>
              <div class="plan-name">Pro</div>
              <div class="plan-price">{pro_price} <span class="plan-period">/ {pro_period}</span></div>
              <div class="plan-description">For professionals and teams that need faster access.</div>
              <div class="feature">✓ Everything in Basic</div><div class="feature">✓ Priority AI access</div><div class="feature">✓ Template downloads</div><div class="feature">✓ Pro-grade circulars</div><div class="feature">✓ Advanced search & filters</div>
            </div>
            """, unsafe_allow_html=True)
        if st.button("Subscribe to Pro", type="primary", use_container_width=True, key="pro_plan"):
            st.session_state.checkout_plan = "Pro"
            st.session_state.checkout_cycle = cycle
            st.rerun()
    with c3:
        st.markdown(
            f"""
            <div class="plan-card max">
              <div class="plan-name" style="color:#6D28D9;">Max</div>
              <div class="plan-price">{max_price} <span class="plan-period">/ {max_period}</span></div>
              <div class="plan-description">Full workspace power for advanced administrative use.</div>
              <div class="feature">✓ Everything in Pro</div><div class="feature">✓ Unlimited document archives</div><div class="feature">✓ Priority queue routing</div><div class="feature">✓ Advanced administrative tools</div><div class="feature">✓ Priority support</div>
            </div>
            """, unsafe_allow_html=True)
        if st.button("Subscribe to Max", type="primary", use_container_width=True, key="max_plan"):
            st.session_state.checkout_plan = "Max"
            st.session_state.checkout_cycle = cycle
            st.rerun()

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    a, b, c = st.columns(3)
    a.markdown("<div class='card'><b>🔒 Secure checkout</b><br><span style='font-size:11px;color:#64748B;'>Use your approved payment provider. Never share card or UPI credentials with staff.</span></div>", unsafe_allow_html=True)
    b.markdown("<div class='card'><b>↻ Cancel anytime</b><br><span style='font-size:11px;color:#64748B;'>Subscription controls can be managed by the billing administrator.</span></div>", unsafe_allow_html=True)
    c.markdown("<div class='card'><b>🧾 Billing records</b><br><span style='font-size:11px;color:#64748B;'>Keep invoices and payment references for office accounting.</span></div>", unsafe_allow_html=True)

    if st.session_state.get("checkout_plan"):
        plan = st.session_state.checkout_plan
        checkout_cycle = st.session_state.get("checkout_cycle", "Monthly")
        with st.expander("🔐 Secure Checkout", expanded=True):
            amount = pro_price if plan == "Pro" and checkout_cycle == cycle else max_price
            st.markdown(f"### Complete your {plan} subscription")
            st.caption(f"Plan: {plan} · Billing: {checkout_cycle} · Display amount: {amount}")
            method = st.radio("Payment method", ["UPI", "Card", "Netbanking"], horizontal=True)
            st.info(f"Checkout method selected: {method}. Connect your production payment gateway here before accepting real payments.")
            x, y = st.columns(2)
            if x.button("Continue to secure payment", type="primary", use_container_width=True):
                st.success("Checkout UI is ready. Add your payment gateway's hosted checkout/API here to process the mandate securely.")
            if y.button("Close checkout", use_container_width=True):
                st.session_state.checkout_plan = None
                st.rerun()


# ============================================================
# ADMIN
# ============================================================
def show_admin(user):
    if user.get("tier") != "Admin":
        st.error("Admin access required.")
        return
    page_header("Admin Command Center", "Manage users, publish documents, configure AI and monitor system health.")
    section = st.radio("Admin section", ["👥 Users", "📢 Document Publisher", "🔧 AI & Gateway Settings", "🩺 Health & Diagnostics"], horizontal=True, label_visibility="collapsed")
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    if section == "👥 Users":
        st.subheader("Pending access requests")
        res = supabase.table("pending_requests").select("*").eq("status", "pending").execute()
        if res.data:
            for r in res.data:
                with st.container(border=True):
                    st.markdown(f"**{safe_str(r.get('name'))}** · {safe_str(r.get('email'))}")
                    st.caption(safe_str(r.get("note")))
                    c1, c2, c3 = st.columns([1.2, .8, .7])
                    with c1:
                        approve_pass = st.text_input("Set password", key=f"pw_{r['id']}", type="password")
                    with c2:
                        approve_tier = st.selectbox("Tier", ["Staff", "Pro", "Max", "Admin"], key=f"tier_{r['id']}")
                    with c3:
                        if st.button("Approve", key=f"appr_{r['id']}", type="primary"):
                            if approve_pass:
                                try:
                                    supabase.table("users").insert({"email": r["email"], "name": r["name"], "password_hash": hash_password(approve_pass), "tier": approve_tier, "active": True}).execute()
                                    supabase.table("pending_requests").update({"status": "approved"}).eq("id", r["id"]).execute()
                                    st.success("Request approved.")
                                    st.rerun()
                                except Exception as e:
                                    log_error("user_approval", str(e))
                                    st.error("Could not create the account. Check the error log.")
                            else:
                                st.warning("Set a password first.")
        else:
            st.caption("No pending requests.")

        st.divider()
        st.subheader("Create user directly")
        with st.container(border=True):
            with st.form("create_user_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    cu_name = st.text_input("Full Name")
                    cu_email = st.text_input("Email")
                    cu_department = st.text_input("Department")
                with c2:
                    cu_pass = st.text_input("Password", type="password")
                    cu_role = st.selectbox("Tier", ["Staff", "Pro", "Max", "Admin"])
                if st.form_submit_button("+ Create Account", type="primary", use_container_width=True):
                    if not (cu_name.strip() and cu_email.strip() and cu_pass):
                        st.warning("Name, email and password are required.")
                    else:
                        existing = supabase.table("users").select("id").eq("email", cu_email.strip().lower()).execute()
                        if existing.data:
                            st.warning("A user with this email already exists.")
                        else:
                            payload = {"email": cu_email.strip().lower(), "name": cu_name.strip(), "password_hash": hash_password(cu_pass), "tier": cu_role, "active": True}
                            # Only include department if your table supports it.
                            try:
                                payload["department"] = cu_department.strip() or None
                                supabase.table("users").insert(payload).execute()
                            except Exception:
                                payload.pop("department", None)
                                supabase.table("users").insert(payload).execute()
                            st.success("Account created.")
                            st.rerun()

        st.divider()
        st.subheader("User roster")
        all_users = supabase.table("users").select("*").execute().data or []
        search = st.text_input("Search users", placeholder="Name or email...")
        if search:
            q = search.lower()
            all_users = [u for u in all_users if q in safe_str(u.get("name")).lower() or q in safe_str(u.get("email")).lower()]
        for u in all_users:
            is_active = u.get("active", True)
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2.2, 1, 1.1, 1])
                with c1:
                    dot = "🟢" if is_active else "🔴"
                    st.markdown(f"{dot} **{safe_str(u.get('name'))}**")
                    st.caption(f"{safe_str(u.get('email'))} · {safe_str(u.get('department') or 'Department not set')}")
                with c2:
                    st.markdown(tier_badge(u.get("tier", "Staff")), unsafe_allow_html=True)
                with c3:
                    new_pw = st.text_input("New password", key=f"resetpw_{u['id']}", type="password", label_visibility="collapsed", placeholder="New password")
                    if st.button("Reset", key=f"reset_{u['id']}"):
                        if new_pw:
                            supabase.table("users").update({"password_hash": hash_password(new_pw)}).eq("id", u["id"]).execute()
                            st.success("Password reset.")
                        else:
                            st.warning("Enter a password.")
                with c4:
                    label = "Deactivate" if is_active else "Activate"
                    if st.button(label, key=f"toggle_{u['id']}"):
                        supabase.table("users").update({"active": not is_active}).eq("id", u["id"]).execute()
                        if is_active:
                            supabase.table("sessions").delete().eq("email", u["email"]).execute()
                        st.rerun()

    elif section == "📢 Document Publisher":
        st.subheader("Publish new circular / G.O.")
        source_choice = st.radio("Document source", ["Upload PDF", "Paste a link"], horizontal=True)
        with st.container(border=True):
            with st.form("add_go_form"):
                c1, c2 = st.columns(2)
                with c1:
                    doc_type = st.selectbox("Document Type", ["G.O.", "Memo", "U.O.", "Circular", "Notification", "Office Order", "Letter"])
                    ref_number = st.text_input("Reference Number *", placeholder="e.g. Ms.No.102")
                    doc_date = st.date_input("Document Date *", value=date.today(), max_value=date.today())
                with c2:
                    title = st.text_input("Title / Subject *")
                    category = st.selectbox("Category", ["Finance / HR", "Operations", "Confidential", "Executive"])
                    tier = st.selectbox("Minimum Tier", ["Basic", "Pro", "Max"])
                supersedes = st.text_input("Supersedes / Amends")
                uploaded_file = None
                link = ""
                if source_choice == "Upload PDF":
                    uploaded_file = st.file_uploader("PDF file (max 20 MB)", type=["pdf"])
                else:
                    link = st.text_input("External PDF / Drive URL")
                if st.form_submit_button("Publish Document", type="primary", use_container_width=True):
                    ref_id = f"{doc_type} {ref_number}".strip()
                    errors = []
                    if not ref_number.strip(): errors.append("Reference number is required.")
                    if not title.strip(): errors.append("Title is required.")
                    if supabase.table("circulars").select("id").eq("ref_id", ref_id).execute().data: errors.append(f"'{ref_id}' already exists.")
                    if source_choice == "Upload PDF" and uploaded_file is None: errors.append("Choose a PDF.")
                    if source_choice == "Paste a link" and not link.strip(): errors.append("Paste a document link.")
                    if errors:
                        for e in errors: st.warning(e)
                    else:
                        final_link = link.strip()
                        extracted_text = ""
                        used_ocr = False
                        if source_choice == "Upload PDF":
                            file_bytes = uploaded_file.read()
                            size_mb = len(file_bytes) / (1024 * 1024)
                            if size_mb > MAX_UPLOAD_MB:
                                st.error(f"File too large ({size_mb:.1f} MB). Maximum is {MAX_UPLOAD_MB} MB.")
                                return
                            safe_ref = ref_number.strip().replace(" ", "_").replace("/", "-")
                            safe_name = f"{doc_type.replace('.', '').replace(' ', '')}_{safe_ref}_{doc_date.isoformat()}.pdf"
                            with st.spinner("Reading PDF and running OCR if needed..."):
                                extracted_text, used_ocr = extract_pdf_text(file_bytes)
                            with st.spinner("Optimising and uploading to R2..."):
                                try:
                                    final_link = upload_to_r2(optimize_pdf(file_bytes), safe_name)
                                except Exception as e:
                                    log_error("r2_upload", str(e))
                                    st.error(f"Upload failed: {e}")
                                    final_link = None
                        if final_link:
                            try:
                                insert_res = supabase.table("circulars").insert({
                                    "ref_id": ref_id,
                                    "doc_type": doc_type,
                                    "ref_number": ref_number.strip(),
                                    "doc_date": doc_date.isoformat(),
                                    "title": title.strip(),
                                    "category": category,
                                    "year": doc_date.year,
                                    "tier": tier,
                                    "link": final_link,
                                    "supersedes": supersedes.strip() or None,
                                    "uploaded_by": user["email"],
                                    "uploaded_at": datetime.utcnow().isoformat(),
                                }).execute()
                                new_id = insert_res.data[0]["id"]
                                chunks = index_circular_for_ai(new_id, extracted_text) if extracted_text else 0
                                msg = f"Published: {ref_id}"
                                if source_choice == "Upload PDF":
                                    msg += f" · AI blocks: {chunks}"
                                    if used_ocr: msg += " · OCR used"
                                st.success(msg)
                                fetch_circulars.clear()
                                st.rerun()
                            except Exception as e:
                                log_error("circular_publish", str(e))
                                st.error(f"Could not publish document: {e}")

    elif section == "🔧 AI & Gateway Settings":
        st.subheader("AI provider configuration")
        current_provider = get_setting("ai_provider", "gemini")
        provider = st.selectbox("Active provider", ["gemini", "groq", "qwen"], index=["gemini", "groq", "qwen"].index(current_provider) if current_provider in ["gemini", "groq", "qwen"] else 0)
        if provider == "gemini":
            key = st.text_input("Gemini API Key", value=get_setting("gemini_api_key"), type="password")
            model = st.text_input("Gemini Model", value=get_setting("gemini_model", "gemini-1.5-flash"))
            if st.button("Save Gemini Settings", type="primary"):
                set_setting("ai_provider", "gemini"); set_setting("gemini_api_key", key.strip()); set_setting("gemini_model", model.strip()); st.success("Gemini settings saved.")
        elif provider == "groq":
            key = st.text_input("Groq API Key", value=get_setting("groq_api_key"), type="password")
            model = st.text_input("Groq Model", value=get_setting("groq_model", "llama-3.1-8b-instant"))
            if st.button("Save Groq Settings", type="primary"):
                set_setting("ai_provider", "groq"); set_setting("groq_api_key", key.strip()); set_setting("groq_model", model.strip()); st.success("Groq settings saved.")
        else:
            key = st.text_input("Qwen API Key", value=get_setting("qwen_api_key"), type="password")
            model = st.text_input("Qwen Model", value=get_setting("qwen_model", "qwen-plus"))
            base = st.text_input("Qwen OpenAI-compatible Base URL", value=get_setting("qwen_base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1"))
            if st.button("Save Qwen Settings", type="primary"):
                set_setting("ai_provider", "qwen"); set_setting("qwen_api_key", key.strip()); set_setting("qwen_model", model.strip()); set_setting("qwen_base_url", base.strip()); st.success("Qwen settings saved.")

        st.divider()
        st.subheader("Subscription pricing")
        c1, c2 = st.columns(2)
        with c1:
            pro_monthly = st.number_input("Pro Monthly (₹)", min_value=0, value=int(get_setting("pro_monthly", "299")))
            pro_yearly = st.number_input("Pro Yearly (₹)", min_value=0, value=int(get_setting("pro_yearly", "3588")))
        with c2:
            max_monthly = st.number_input("Max Monthly (₹)", min_value=0, value=int(get_setting("max_monthly", "799")))
            max_yearly = st.number_input("Max Yearly (₹)", min_value=0, value=int(get_setting("max_yearly", "9588")))
        if st.button("Save Pricing", type="primary"):
            for k, v in [("pro_monthly", pro_monthly), ("pro_yearly", pro_yearly), ("max_monthly", max_monthly), ("max_yearly", max_yearly)]: set_setting(k, str(v))
            st.success("Pricing saved.")
        st.caption("For production payments, connect a hosted checkout/payment provider rather than collecting payment credentials directly in Streamlit.")

    elif section == "🩺 Health & Diagnostics":
        st.subheader("System health")
        users = supabase.table("users").select("id").execute().data or []
        circulars = supabase.table("circulars").select("id").execute().data or []
        provider = get_setting("ai_provider", "gemini")
        key_set = bool(get_setting(f"{provider}_api_key") or st.secrets.get(f"{provider.upper()}_API_KEY", ""))
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='kpi-card'><div class='kpi-label'>Total users</div><div class='kpi-value'>{len(users)}</div><div class='kpi-foot'>Active workspace accounts</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='kpi-card'><div class='kpi-label'>Circulars indexed</div><div class='kpi-value'>{len(circulars)}</div><div class='kpi-foot'>Document records</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='kpi-card'><div class='kpi-label'>AI engine</div><div class='kpi-value' style='font-size:20px;'>{provider.title()}</div><div class='kpi-foot'>{'Key configured' if key_set else 'No key configured'}</div></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='kpi-card'><div class='kpi-label'>Status</div><div class='kpi-value' style='font-size:20px;color:{'#15803D' if key_set else '#B91C1C'};'>{'Healthy' if key_set else 'Attention'}</div><div class='kpi-foot'>Configuration check</div></div>", unsafe_allow_html=True)
        st.divider()
        st.subheader("Recent errors")
        errors = supabase.table("error_log").select("*").order("occurred_at", desc=True).limit(30).execute().data or []
        if not errors:
            st.success("No errors logged. Everything is running clean.")
        else:
            for e in errors:
                with st.container(border=True):
                    st.markdown(f"**{safe_str(e.get('area'))}** · {safe_str(e.get('occurred_at'))}")
                    st.code(safe_str(e.get("message")), language=None)
            if st.button("🗑️ Clear Error Log"):
                for e in errors:
                    supabase.table("error_log").delete().eq("id", e["id"]).execute()
                st.rerun()


# ============================================================
# MAIN ROUTER
# ============================================================
try_auto_login()

if not st.session_state.logged_in:
    show_login()
else:
    user = st.session_state.user
    menu = render_sidebar(user)
    topbar(user)

    if menu == "🏠 Dashboard":
        show_home(user)
    elif menu == "📢 Circulars & G.O.s":
        show_circulars(user)
    elif menu == "🤖 AI Rules Assistant":
        show_ai(user)
    elif menu == "📝 Templates":
        show_templates(user)
    elif menu == "✉️ Tapal Register":
        show_tapal(user)
    elif menu == "📮 Dispatch Labels":
        show_dispatch(user)
    elif menu == "📞 Staff Directory":
        show_directory(user)
    elif menu == "💳 Plans & Billing":
        show_billing(user)
    elif menu == "⚙️ Admin Command Center":
        show_admin(user)
