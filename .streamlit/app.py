import gzip
import io
import os
import re
import secrets
import smtplib
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage
import bcrypt
import pandas as pd
import streamlit as st
from supabase import create_client, Client
from streamlit_cookies_controller import CookieController

st.set_page_config(page_title="GovDocs AI — Government Workspace", page_icon="🏛️", layout="wide", initial_sidebar_state="expanded")

CUSTOM_CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{--navy-900:#16324F;--navy-800:#1E3A5F;--navy-700:#2C5282;--canvas:#F7F9FB;--border:#E2E8F0;--border-strong:#CBD5E1;--text:#0F172A;--muted:#64748B;--shadow:0 2px 10px rgba(15,23,42,.05);--shadow-md:0 8px 24px rgba(15,23,42,.08);--shadow-lg:0 18px 45px rgba(15,23,42,.12);}
html,body,[class*="css"]{font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}
body{background:var(--canvas);} .stApp{background:var(--canvas);color:var(--text);}
#MainMenu,footer{visibility:hidden;}
.block-container{padding-top:1.35rem;padding-bottom:3rem;max-width:1500px;}
h1,h2,h3,h4{color:var(--text);font-weight:700;letter-spacing:-.025em;}
section[data-testid="stSidebar"]{background:#FFF !important;border-right:1px solid var(--border) !important;}
section[data-testid="stSidebar"] .stRadio>div{gap:4px;}
section[data-testid="stSidebar"] .stRadio>div>label{border-radius:10px;padding:.62rem .75rem;margin:0;color:#334155;font-weight:500;}
section[data-testid="stSidebar"] .stRadio>div>label:has(div[aria-checked="true"]){background:#EAF2FF;color:var(--navy-800);font-weight:700;}
section[data-testid="stSidebar"] .stRadio>div>label p{color:inherit !important;}
.sidebar-brand{display:flex;align-items:center;gap:10px;padding:.45rem .35rem 1.1rem;border-bottom:1px solid var(--border);margin-bottom:1rem;}
.sidebar-logo{width:38px;height:38px;border-radius:10px;background:var(--navy-800);color:#fff;display:flex;align-items:center;justify-content:center;font-size:20px;}
.sidebar-brand-title{font-size:17px;font-weight:800;color:var(--navy-900);} .sidebar-brand-sub{font-size:10px;color:var(--muted);}
.profile-card{background:#F8FAFC;border:1px solid var(--border);border-radius:12px;padding:12px;margin-bottom:12px;}
.profile-name{font-size:13px;font-weight:700;} .profile-email{font-size:10px;color:var(--muted);margin-top:3px;}
.profile-role{margin-top:9px;display:flex;align-items:center;justify-content:space-between;}
.app-topbar{display:flex;align-items:center;justify-content:space-between;background:#FFF;border:1px solid var(--border);border-radius:14px;padding:13px 18px;margin-bottom:18px;box-shadow:var(--shadow);}
.app-topbar-title{font-size:13px;font-weight:700;color:var(--navy-800);} .app-topbar-sub{font-size:11px;color:var(--muted);margin-top:2px;}
.page-header{margin-bottom:20px;} .page-header h1{margin:0;font-size:27px;} .page-header p{margin:5px 0 0;color:var(--muted);font-size:13px;}
.kpi-card{background:#FFF;border:1px solid var(--border);border-radius:14px;padding:16px;box-shadow:var(--shadow);min-height:112px;}
.kpi-label{color:var(--muted);font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;}
.kpi-value{color:var(--text);font-size:25px;font-weight:800;margin-top:8px;}
.kpi-foot{color:var(--muted);font-size:10px;margin-top:3px;}
.stButton>button{border:1px solid var(--border-strong) !important;background:#FFF !important;color:var(--navy-800) !important;border-radius:9px !important;font-weight:600 !important;min-height:38px;}
.stButton>button[kind="primary"]{background:var(--navy-800) !important;color:#FFF !important;border-color:var(--navy-800) !important;}
.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stSelectbox>div>div,.stDateInput>div>div>input,.stNumberInput>div>div>input{background:#FFF !important;border:1px solid var(--border-strong) !important;border-radius:9px !important;}
.stTabs [data-baseweb="tab-list"]{gap:2px;background:#EEF2F6;padding:3px;border-radius:10px;border:none;}
.stTabs [data-baseweb="tab"]{border-radius:8px;color:#475569;font-weight:600;font-size:12px;}
.stTabs [aria-selected="true"]{background:#FFF !important;color:var(--navy-800) !important;}
.doc-card{background:#FFF;border:1px solid var(--border);border-radius:14px;padding:15px 16px;margin:0 0 9px;box-shadow:var(--shadow);}
.doc-row{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;}
.doc-ref{color:var(--navy-700);background:#EFF6FF;border:1px solid #DBEAFE;border-radius:999px;padding:4px 9px;font-size:10px;font-weight:700;}
.doc-title{font-size:14px;font-weight:700;margin-top:9px;}
.doc-meta{display:flex;flex-wrap:wrap;gap:10px;color:var(--muted);font-size:10px;margin-top:6px;}
.badge{display:inline-flex;padding:4px 9px;border-radius:999px;font-size:10px;font-weight:700;}
.badge-basic{background:#F1F5F9;color:#475569;border:1px solid #E2E8F0;}
.badge-pro{background:#EFF6FF;color:#1D4ED8;border:1px solid #BFDBFE;}
.badge-max{background:#F5F3FF;color:#6D28D9;border:1px solid #DDD6FE;}
.plan-card{background:#FFF;border:1px solid var(--border);border-radius:16px;padding:21px;min-height:380px;position:relative;box-shadow:var(--shadow);}
.plan-card.featured{border:2px solid var(--navy-700);}
.plan-pill{position:absolute;right:18px;top:-12px;background:var(--navy-800);color:#fff;border-radius:999px;padding:5px 10px;font-size:9px;font-weight:800;}
.plan-name{font-size:17px;font-weight:800;} .plan-price{font-size:30px;font-weight:800;margin-top:13px;}
.plan-period{color:var(--muted);font-size:11px;} .plan-description{color:var(--muted);font-size:11px;min-height:34px;margin-top:5px;}
.feature{font-size:11px;color:#475569;margin:10px 0;}
.tapal-card{background:#FFF;border:1px solid var(--border);border-radius:13px;padding:14px;margin-bottom:9px;box-shadow:var(--shadow);}
.tapal-inward{border-left:4px solid var(--navy-700);} .tapal-outward{border-left:4px solid #16A34A;}
.login-shell{min-height:78vh;display:flex;align-items:center;justify-content:center;padding:30px 10px;}
.login-panel{width:min(920px,100%);background:#FFF;border:1px solid var(--border);border-radius:20px;box-shadow:var(--shadow-lg);overflow:hidden;display:grid;grid-template-columns:1fr 1.05fr;}
.login-brand{background:linear-gradient(150deg,#16324F,#2C5282);padding:48px;color:#FFF;display:flex;flex-direction:column;justify-content:center;min-height:510px;}
.login-brand h1{color:#FFF;font-size:32px;margin:12px 0 8px;} .login-brand p{color:rgba(255,255,255,.78);font-size:12px;line-height:1.7;}
.login-mark{width:52px;height:52px;border-radius:14px;background:rgba(255,255,255,.12);display:flex;align-items:center;justify-content:center;font-size:27px;border:1px solid rgba(255,255,255,.18);}
.login-form{padding:38px 40px;} .login-form h2{font-size:22px;margin:0 0 5px;} .login-form .muted{color:var(--muted);font-size:12px;margin-bottom:18px;}
hr{border-color:var(--border) !important;}
@media(max-width:900px){.login-panel{grid-template-columns:1fr;}.login-brand{min-height:auto;padding:28px;}.login-form{padding:28px 22px;}}
@media(max-width:700px){.block-container{padding:12px 10px 30px;}.page-header h1{font-size:22px;}.doc-row{flex-direction:column;}.plan-card{min-height:auto;}.app-topbar{flex-direction:column;align-items:flex-start;gap:8px;}.kpi-card{min-height:auto;}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown("<style>header{visibility:visible !important}#MainMenu{visibility:hidden !important}footer{visibility:hidden !important}[data-testid='stSidebarCollapsedControl'],[data-testid='collapsedControl']{visibility:visible !important}</style>", unsafe_allow_html=True)

DAILY_AI_LIMIT = 20
MAX_UPLOAD_MB = 20
OCR_MAX_PAGES = 40
SESSION_DAYS = 30
COOKIE_NAME = "huddle_session"
OTP_MIN = 10

PROVIDERS = {
    "gemini": ("Google Gemini", "gemini", "gemini-2.0-flash", ""),
    "groq": ("Groq", "openai", "llama-3.3-70b-versatile", "https://api.groq.com/openai/v1"),
    "qwen": ("Alibaba Qwen", "openai", "qwen-plus", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    "openai": ("OpenAI", "openai", "gpt-4o-mini", "https://api.openai.com/v1"),
    "mistral": ("Mistral", "openai", "mistral-small-latest", "https://api.mistral.ai/v1"),
    "custom": ("Custom endpoint", "openai", "", ""),
}

def page_header(title, subtitle=""):
    st.markdown(f'<div class="page-header"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)

def greeting():
    h = datetime.now().hour
    return "Good morning" if h < 12 else ("Good afternoon" if h < 17 else "Good evening")

def tier_badge(tier):
    cls = {"Basic": "badge-basic", "Staff": "badge-basic", "Pro": "badge-pro", "Max": "badge-max", "Admin": "badge-max"}.get(tier, "badge-basic")
    return f'<span class="badge {cls}">{tier}</span>'

def safe_str(v):
    return "" if v is None else str(v)

def email_ok(x):
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', x or ''))

def phone_ok(x):
    return 10 <= len(re.sub(r'\D', '', x or '')) <= 15

def secret(k, d=""):
    try: return st.secrets.get(k, d) or os.getenv(k, d)
    except Exception: return os.getenv(k, d)

def now_utc():
    return datetime.now(timezone.utc)

@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()
cookies = CookieController()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- AUTH ----------------
def hash_password(p): return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()
def check_password(p, h):
    try: return bcrypt.checkpw(p.encode(), h.encode())
    except Exception: return False

def get_user(email):
    res = supabase.table("users").select("*").eq("email", email).execute()
    return res.data[0] if res.data else None

def create_pending_request(name, email, note):
    supabase.table("pending_requests").insert({"name": name, "email": email, "note": note, "requested_at": datetime.utcnow().isoformat(), "status": "pending"}).execute()

def has_access(user_tier, required_tier):
    levels = {"Staff": 1, "Basic": 1, "Pro": 2, "Max": 3, "Admin": 4}
    return levels.get(user_tier, 0) >= levels.get(required_tier, 0)

def create_session_token(email):
    token = secrets.token_urlsafe(32)
    supabase.table("sessions").insert({"token": token, "email": email, "expires_at": (datetime.utcnow() + timedelta(days=SESSION_DAYS)).isoformat()}).execute()
    return token

def get_user_from_token(token):
    if not token: return None
    res = supabase.table("sessions").select("*").eq("token", token).execute()
    if not res.data: return None
    s = res.data[0]
    if s["expires_at"] < datetime.utcnow().isoformat():
        supabase.table("sessions").delete().eq("token", token).execute(); return None
    user = get_user(s["email"])
    if user and user.get("active", True) is False:
        supabase.table("sessions").delete().eq("token", token).execute(); return None
    return user

def read_session_cookie():
    try: return st.context.cookies.get(COOKIE_NAME)
    except Exception:
        try: return cookies.get(COOKIE_NAME)
        except Exception: return None

def clear_session_token(token):
    if token: supabase.table("sessions").delete().eq("token", token).execute()
    try: cookies.remove(COOKIE_NAME)
    except Exception: pass

def try_auto_login():
    if st.session_state.logged_in: return
    user = get_user_from_token(read_session_cookie())
    if user:
        st.session_state.logged_in = True
        st.session_state.user = user

def do_login(u, remember=True):
    st.session_state.logged_in = True
    st.session_state.user = u
    if remember:
        cookies.set(COOKIE_NAME, create_session_token(u["email"]), max_age=SESSION_DAYS * 24 * 3600)
    st.rerun()

# ---------------- OTP ----------------
def otp_send(identifier, channel):
    code = f"{secrets.randbelow(1000000):06d}"
    supabase.table("otp_verifications").insert({
        "identifier": identifier, "channel": channel, "purpose": "signup",
        "code_hash": hash_password(code),
        "expires_at": (now_utc() + timedelta(minutes=OTP_MIN)).isoformat(),
    }).execute()
    if channel == "email":
        host = secret("SMTP_HOST"); port = int(secret("SMTP_PORT", "587"))
        usr = secret("SMTP_USERNAME"); pw = secret("SMTP_PASSWORD")
        sender = secret("SMTP_FROM") or usr
        if not all([host, usr, pw, sender]):
            return False, "Email OTP is not configured yet. Use the Request Access tab or ask admin to add SMTP secrets."
        try:
            m = EmailMessage()
            m["Subject"] = "GovDocs AI verification code"
            m["From"] = sender; m["To"] = identifier
            m.set_content(f"Your verification code is {code}. It expires in {OTP_MIN} minutes.")
            with smtplib.SMTP(host, port, timeout=20) as s:
                s.starttls(); s.login(usr, pw); s.send_message(m)
            return True, ""
        except Exception as e:
            log_error("smtp_otp", repr(e)); return False, str(e)
    sid = secret("TWILIO_ACCOUNT_SID"); tok = secret("TWILIO_AUTH_TOKEN"); frm = secret("TWILIO_FROM_NUMBER")
    if not all([sid, tok, frm]):
        return False, "SMS OTP is not configured yet. Use Email OTP or the Request Access tab."
    try:
        from twilio.rest import Client
        Client(sid, tok).messages.create(body=f"GovDocs AI OTP: {code}. Valid {OTP_MIN} minutes.", from_=frm, to=identifier)
        return True, ""
    except Exception as e:
        log_error("sms_otp", repr(e)); return False, str(e)

def otp_verify(identifier, channel, code):
    try:
        r = supabase.table("otp_verifications").select("*").eq("identifier", identifier).eq("channel", channel).eq("purpose", "signup").eq("verified", False).order("created_at", desc=True).limit(1).execute()
        if not r.data: return False, "Request a new OTP first."
        x = r.data[0]
        if datetime.fromisoformat(str(x["expires_at"]).replace("Z", "+00:00")) < now_utc():
            return False, "OTP expired. Request a new one."
        if int(x.get("attempts", 0)) >= 5:
            return False, "Too many attempts. Request a new OTP."
        supabase.table("otp_verifications").update({"attempts": int(x.get("attempts", 0)) + 1}).eq("id", x["id"]).execute()
        if not check_password(code.strip(), x["code_hash"]):
            return False, "Incorrect OTP."
        supabase.table("otp_verifications").update({"verified": True}).eq("id", x["id"]).execute()
        return True, ""
    except Exception as e:
        log_error("otp_verify", repr(e)); return False, "OTP verification failed."

# ---------------- CACHED DATA ----------------
@st.cache_data(ttl=30)
def fetch_circulars(): return supabase.table("circulars").select("*").execute().data or []
@st.cache_data(ttl=30)
def fetch_templates(): return supabase.table("templates").select("*").execute().data or []
@st.cache_data(ttl=30)
def fetch_tapal(): return supabase.table("tapal_log").select("*").order("tapal_date", desc=True).execute().data or []
@st.cache_data(ttl=30)
def fetch_directory(): return supabase.table("directory").select("*").execute().data or []

# ---------------- SETTINGS / ERRORS ----------------
def get_setting(key, default=""):
    try:
        res = supabase.table("app_settings").select("value").eq("key", key).execute()
        return res.data[0]["value"] if res.data else default
    except Exception: return default

def set_setting(key, value):
    if supabase.table("app_settings").select("key").eq("key", key).execute().data:
        supabase.table("app_settings").update({"value": value}).eq("key", key).execute()
    else:
        supabase.table("app_settings").insert({"key": key, "value": value}).execute()

def log_error(area, message):
    try: supabase.table("error_log").insert({"area": area, "message": str(message)[:2000], "occurred_at": datetime.utcnow().isoformat()}).execute()
    except Exception: pass

# ---------------- AI USAGE ----------------
def log_ai_usage(email):
    today = date.today().isoformat()
    res = supabase.table("ai_usage").select("*").eq("email", email).eq("day", today).execute()
    if res.data:
        row = res.data[0]
        supabase.table("ai_usage").update({"count": row["count"] + 1}).eq("id", row["id"]).execute()
        return row["count"] + 1
    supabase.table("ai_usage").insert({"email": email, "day": today, "count": 1}).execute()
    return 1

def get_ai_usage_today(email):
    res = supabase.table("ai_usage").select("*").eq("email", email).eq("day", date.today().isoformat()).execute()
    return res.data[0]["count"] if res.data else 0

# ----------------
