import streamlit.components.v1 as components
import gzip
import html
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

def esc(v):
    """HTML-escape a value before interpolating it into an unsafe_allow_html=True
    markdown block. Any field a user can type (name, subject, remarks, title...)
    must go through this, not safe_str(), when it ends up in raw HTML — otherwise
    it's a stored-XSS hole. Do NOT use this for URLs/hrefs (it would break them)."""
    return html.escape(safe_str(v))

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
    if st.session_state.logged_in:
        return
    token = read_session_cookie()
    user = get_user_from_token(token)
    if user:
        st.session_state.logged_in = True
        st.session_state.user = user
        st.session_state["session_token"] = token

def do_login(u, remember=True):
    st.session_state.logged_in = True
    st.session_state.user = u
    if remember:
        st.session_state["session_token"] = create_session_token(u["email"])
    st.rerun()
    def persist_session_cookie():
    token = st.session_state.get("session_token")
    if not token:
        return
    import streamlit.components.v1 as components
    components.html(
        "<script>document.cookie='huddle_session=" + token
        + "; max-age=2592000; path=/; SameSite=Lax';</script>",
        height=0, width=0,
    )

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
            return False, "Email OTP is not configured yet. Use Request Access or ask admin to add SMTP secrets."
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

@st.cache_data(ttl=30)
def fetch_circulars(): return supabase.table("circulars").select("*").execute().data or []
@st.cache_data(ttl=30)
def fetch_templates(): return supabase.table("templates").select("*").execute().data or []
@st.cache_data(ttl=30)
def fetch_tapal(): return supabase.table("tapal_log").select("*").order("tapal_date", desc=True).execute().data or []
@st.cache_data(ttl=30)
def fetch_directory(): return supabase.table("directory").select("*").execute().data or []

@st.cache_data(ttl=30)
def _fetch_all_settings():
    try:
        res = supabase.table("app_settings").select("key,value").execute()
        return {r["key"]: r["value"] for r in (res.data or [])}
    except Exception:
        return {}

def get_setting(key, default=""):
    return _fetch_all_settings().get(key, default)

def set_setting(key, value):
    if supabase.table("app_settings").select("key").eq("key", key).execute().data:
        supabase.table("app_settings").update({"value": value}).eq("key", key).execute()
    else:
        supabase.table("app_settings").insert({"key": key, "value": value}).execute()
    _fetch_all_settings.clear()  # invalidate cache so the new value is picked up immediately

DEFAULT_DEPARTMENTS = "Establishment;Accounts;Enforcement;Licensing;Registration;Correspondence / Tapal"
DEFAULT_OFFICES = "DTC Office, Visakhapatnam;RTA Office, Visakhapatnam"

def get_org_list(setting_key, default_csv):
    raw = get_setting(setting_key, default_csv)
    items = [x.strip() for x in raw.split(";") if x.strip()]
    return items or [x.strip() for x in default_csv.split(";")]

def log_error(area, message):
    try: supabase.table("error_log").insert({"area": area, "message": str(message)[:2000], "occurred_at": datetime.utcnow().isoformat()}).execute()
    except Exception: pass

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

@st.cache_resource
def get_r2_client():
    import boto3
    return boto3.client("s3", endpoint_url=f"https://{st.secrets['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
                        aws_access_key_id=st.secrets["R2_ACCESS_KEY_ID"], aws_secret_access_key=st.secrets["R2_SECRET_ACCESS_KEY"], region_name="auto")

def upload_to_r2(file_bytes, object_name):
    s3 = get_r2_client()
    s3.put_object(
        Bucket=st.secrets.get("R2_BUCKET_NAME", "circulars"),
        Key=object_name,
        Body=file_bytes,
        ContentType="application/gzip" if object_name.endswith(".gz") else "application/pdf",
    )
    pub_url = st.secrets.get("R2_PUBLIC_URL", "")
    return f"{pub_url.rstrip('/')}/{object_name}" if pub_url else object_name

def compress_for_r2(file_bytes):
    return gzip.compress(optimize_pdf(file_bytes), compresslevel=6)

def fetch_and_decompress(url):
    import urllib.request
    with urllib.request.urlopen(url) as r:
        data = r.read()
    try: return gzip.decompress(data)
    except Exception: return data

def extract_pdf_text(file_bytes):
    import fitz, pytesseract
    from PIL import Image, ImageEnhance, ImageOps
    try: doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        log_error("pdf_open", str(e)); return "", False
    all_text, used_ocr, ocr_done = [], False, 0
    for pn, page in enumerate(doc):
        try: page_text = page.get_text().strip()
        except Exception: page_text = ""
        if len(page_text) > 40:
            all_text.append(page_text)
        else:
            if ocr_done >= OCR_MAX_PAGES:
                all_text.append(f"[Page {pn+1}: scanned — OCR limit reached]"); continue
            try:
                pix = page.get_pixmap(dpi=200)
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                img = ImageOps.autocontrast(img.convert("L"))
                img = ImageEnhance.Sharpness(img).enhance(2.0)
                all_text.append(pytesseract.image_to_string(img, config="--psm 6").strip())
                used_ocr = True; ocr_done += 1
            except Exception as e:
                log_error("pdf_ocr", f"page {pn+1}: {e}"); all_text.append(f"[Page {pn+1}: OCR failed]")
    doc.close()
    return "\n".join(all_text).strip(), used_ocr

def optimize_pdf(file_bytes):
    import fitz
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf"); buf = io.BytesIO()
        doc.save(buf, garbage=3, deflate=True); doc.close()
        out = buf.getvalue()
        return out if len(out) < len(file_bytes) else file_bytes
    except Exception as e:
        log_error("pdf_optimize", str(e)); return file_bytes

def chunk_text(text, size=1200):
    text = text.strip()
    return [text[i:i+size].strip() for i in range(0, len(text), size) if text[i:i+size].strip()] if text else []

def index_circular_for_ai(circular_id, text):
    try:
        supabase.table("circular_chunks").delete().eq("circular_id", circular_id).execute()
        chunks = chunk_text(text)
        if not chunks:
            supabase.table("circulars").update({"ai_indexed": False}).eq("id", circular_id).execute(); return 0
        rows = [{"circular_id": circular_id, "chunk_no": i, "content": ch} for i, ch in enumerate(chunks)]
        supabase.table("circular_chunks").insert(rows).execute()  # single batched insert instead of N round-trips
        supabase.table("circulars").update({"ai_indexed": True}).eq("id", circular_id).execute()
        return len(chunks)
    except Exception as e:
        log_error("ai_indexing", str(e)); return 0

def search_uploaded_circulars(question, limit=4):
    try:
        res = supabase.rpc("search_circular_chunks", {"q": question, "limit_count": limit}).execute()
        return res.data or []
    except Exception as e:
        log_error("ai_search", str(e)); return []

def _call_one(p, key, model, ep, prompt, context):
    name, kind, dm, de = PROVIDERS.get(p, PROVIDERS["gemini"])
    if not key: return None, f"{name}: no API key"
    try:
        if kind == "gemini":
            try:
                from google import genai
                from google.genai import types
                c = genai.Client(api_key=key)
                r = c.models.generate_content(model=model, contents=prompt, config=types.GenerateContentConfig(system_instruction=context, temperature=0.15))
                return r.text, None
            except ImportError:
                import google.generativeai as g2
                g2.configure(api_key=key)
                return g2.GenerativeModel(model).generate_content(f"{context}\n\nQuestion: {prompt}").text, None
        from openai import OpenAI
        c = OpenAI(api_key=key, base_url=(ep or de).rstrip("/"))
        r = c.chat.completions.create(model=model, messages=[{"role": "system", "content": context}, {"role": "user", "content": prompt}], temperature=0.15)
        return r.choices[0].message.content, None
    except Exception as e:
        return None, f"{name} error: {e}"

def ai_call(prompt, context):
    primary = get_setting("ai_provider", "gemini")
    order = [primary] + [p for p in PROVIDERS if p != primary]
    last = None
    for p in order:
        key = get_setting(f"{p}_api_key") or secret(f"{p.upper()}_API_KEY")
        if not key:
            last = f"{PROVIDERS[p][0]}: no API key"; continue
        model = get_setting(f"{p}_model", PROVIDERS[p][2]) or PROVIDERS[p][2]
        ep = get_setting(f"{p}_endpoint", PROVIDERS[p][3]) or PROVIDERS[p][3]
        r, e = _call_one(p, key, model, ep, prompt, context)
        if r is not None: return r, None
        last = e; log_error("ai_" + p, e)
    return None, last or "No AI provider configured."

def hide_cloud_chrome():
    # 1. Internal CSS (hides elements inside the app iframe)
    st.markdown(
        """
        <style>
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        header {visibility: hidden !important; height: 0 !important;}
        [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
        [data-testid="stDecoration"] {visibility: hidden !important;}
        [data-testid="stStatusWidget"] {visibility: hidden !important; display: none !important;}
        [data-testid="stAppDeployButton"] {display: none !important;}
        .viewerBadge_container__1QSob, .viewerBadge_link__1S137, .stAppDeployButton {display: none !important;}
        /* Keep sidebar collapse arrow visible */
        [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"] {visibility: visible !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    # 2. JavaScript to reach into the parent frame (Streamlit Community Cloud wrapper)
    hide_js = """
    <script>
    (function() {
        function cleanChrome() {
            try {
                var p = window.parent.document;
                // Target the top-right toolbar, status widget, deploy button, badges, and profile avatar
                var selectors = [
                    '[data-testid="stToolbar"]',
                    '[data-testid="stStatusWidget"]',
                    '[data-testid="stAppDeployButton"]',
                    '[class*="viewerBadge"]',
                    '[class*="UserMenu"]',
                    '[class*="Toolbar"]',
                    '[class*="DeployButton"]',
                    '[class*="Profile"]'
                ];
                selectors.forEach(function(sel) {
                    var els = p.querySelectorAll(sel);
                    els.forEach(function(el) { 
                        el.style.display = 'none'; 
                        el.style.visibility = 'hidden';
                    });
                });
            } catch (e) {
                // Fail silently if cross-origin restrictions apply
            }
        }
        // Run multiple times to catch elements that load asynchronously after the app renders
        setTimeout(cleanChrome, 500);
        setTimeout(cleanChrome, 1500);
        setTimeout(cleanChrome, 3000);
        setTimeout(cleanChrome, 6000);
    })();
    </script>
    """
    components.html(hide_js, height=0, width=0)

def show_full_chrome():
    """Admin-only: keep Streamlit's native header/toolbar visible so admins
    can still reach Deploy/Rerun/Settings/'Manage app' for debugging."""
    st.markdown(
        """
        <style>
        #MainMenu{visibility:visible !important;}
        footer{visibility:hidden !important;}
        header{visibility:visible !important;}
        [data-testid="stToolbar"]{visibility:visible !important; display:flex !important;}
        [data-testid="stStatusWidget"]{visibility:visible !important; display:flex !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )

def show_login():
    st.markdown("""
    <div class="login-shell"><div class="login-panel">
      <div class="login-brand"><div class="login-mark">🏛️</div><h1>GovDocs AI</h1>
        <p>AI-powered government document workspace for circulars, G.O.s, Tapal, templates and internal rules assistance.</p>
        <div style="margin-top:25px;font-size:11px;color:rgba(255,255,255,.72);line-height:1.8;"><b style="color:#fff;">Instant staff accounts</b><br>Verify your email with OTP · Basic is free forever · Pro/Max by admin approval</div>
      </div>
      <div class="login-form"><h2>Welcome</h2><div class="muted">Sign in, or create your account in 60 seconds.</div></div>
    </div></div>""", unsafe_allow_html=True)
    _, c2, _ = st.columns([1, 1.35, 1])
    with c2:
        tab_login, tab_signup, tab_request = st.tabs(["Sign In", "Create Account", "Request Access"])
        with tab_login:
            email = st.text_input("Email", key="login_email", placeholder="name@department.gov")
            password = st.text_input("Password", type="password", key="login_pass")
            remember = st.checkbox("Remember me", value=True)
            if st.button("Sign In →", use_container_width=True, type="primary"):
                user = get_user(email.strip().lower())
                if user and user.get("active", True) is False:
                    st.error("This account has been deactivated. Contact your administrator.")
                elif user and check_password(password, user["password_hash"]):
                    do_login(user, remember)
                else:
                    st.error("Invalid email or password.")
        with tab_signup:
            st.caption("Verify your email, set a password — instant **Basic** account.")
            n = st.text_input("Full Name *")
            dept_opts = get_org_list("departments", DEFAULT_DEPARTMENTS) + ["Other (type below)"]
            dept_choice = st.selectbox("Department / Section *", dept_opts)
            dept = st.text_input("Enter department") if dept_choice.startswith("Other") else dept_choice
            off_opts = get_org_list("offices", DEFAULT_OFFICES) + ["Other (type below)"]
            off_choice = st.selectbox("Office *", off_opts)
            off = st.text_input("Enter office name") if off_choice.startswith("Other") else off_choice
            dsg = st.text_input("Designation *")
            emp_id = st.text_input("Employee ID (optional)")
            ph = st.text_input("Phone Number (optional)")
            em = st.text_input("Email *")
            channel = "email"
            ident = em.strip().lower()
            if st.button("Send OTP →", use_container_width=True):
                if not (n.strip() and off.strip() and dept.strip() and dsg.strip() and email_ok(em)):
                    st.warning("Fill all required fields correctly.")
                elif ph.strip() and not phone_ok(ph):
                    st.warning("Phone number looks invalid — leave it blank or fix it.")
                elif get_user(em.strip().lower()):
                    st.warning("This email already has an account — use Sign In.")
                else:
                    ok, err = otp_send(ident, channel)
                    if ok:
                        st.success(f"OTP sent to {ident}.")
                    else:
                        st.error(err)
            code = st.text_input("Enter 6-digit OTP", max_chars=6)
            if st.button("Verify OTP", use_container_width=True):
                ok, err = otp_verify(ident, channel, code)
                st.session_state["otp_ok"] = ok
                st.session_state["otp_ident"] = ident
                if ok:
                    st.success("Verified ✓ Now set your password below.")
                else:
                    st.error(err)
            pw = st.text_input("Create Password *", type="password")
            pw2 = st.text_input("Confirm Password *", type="password")
            if st.button("Create Account →", use_container_width=True, type="primary"):
                if not st.session_state.get("otp_ok") or st.session_state.get("otp_ident") != ident:
                    st.warning("Verify the OTP first.")
                elif len(pw) < 8 or pw != pw2:
                    st.warning("Password must be 8+ characters and match.")
                else:
                    payload = {"email": em.strip().lower(), "name": n.strip(), "password_hash": hash_password(pw), "tier": "Basic", "active": True,
                               "office_name": off.strip(), "department": dept.strip(), "designation": dsg.strip(),
                               "employee_id": emp_id.strip() or None, "phone": ph.strip(),
                               "email_verified": channel == "email", "phone_verified": channel == "phone"}
                    try:
                        supabase.table("users").insert(payload).execute()
                    except Exception:
                        supabase.table("users").insert({"email": em.strip().lower(), "name": n.strip(), "password_hash": hash_password(pw), "tier": "Basic", "active": True, "office_name": off.strip(), "designation": dsg.strip()}).execute()
                    st.session_state["otp_ok"] = False
                    st.session_state["show_welcome"] = True
                    do_login(get_user(em.strip().lower()))
        with tab_request:
            st.info("For Pro/Max or special roles. An administrator reviews every request.")
            rn = st.text_input("Full Name", key="req_name")
            re_ = st.text_input("Email", key="req_email")
            rr = st.text_input("Role / Designation", key="req_role")
            rd = st.text_input("Department / Office", key="req_department")
            rnote = st.text_area("Additional note", key="req_note", height=90)
            if st.button("Submit Request →", use_container_width=True, type="primary"):
                if rn.strip() and re_.strip():
                    create_pending_request(rn.strip(), re_.strip().lower(), f"Role: {rr.strip()} | Dept: {rd.strip()} | {rnote.strip()}")
                    st.success("Request submitted. The administrator will contact you after review.")
                else:
                    st.warning("Please enter your name and email.")

def render_sidebar(user):
    with st.sidebar:
        st.markdown('<div class="sidebar-brand"><div class="sidebar-logo">🏛️</div><div><div class="sidebar-brand-title">GovDocs AI</div><div class="sidebar-brand-sub">Government Workspace</div></div></div>', unsafe_allow_html=True)
        office = safe_str(user.get("office_name"))
        desig = safe_str(user.get("designation"))
        extra = f"<div class='profile-email'>{esc(office)} · {esc(desig)}</div>" if (office or desig) else ""
        st.markdown(f'<div class="profile-card"><div class="profile-name">{esc(user.get("name"))}</div><div class="profile-email">{esc(user.get("email"))}</div>{extra}<div class="profile-role"><span style="font-size:10px;color:#64748B;">Access tier</span>{tier_badge(user.get("tier","Staff"))}</div></div>', unsafe_allow_html=True)
        options = [
            "🏠 Dashboard", "📢 Circulars & G.O.s", "🤖 AI Rules Assistant",
            "📝 Templates", "✉️ Tapal Register", "📮 Dispatch Labels",
            "📞 Staff Directory", "💳 Plans & Billing",
        ]
        if user.get("tier") == "Admin":
            options.append("⚙️ Admin Command Center")
        menu = st.radio("Navigation", options, label_visibility="collapsed")
        if st.button("🚪 Logout", use_container_width=True):
                       clear_session_token(read_session_cookie())
            st.session_state.pop("session_token", None)
            st.session_state.logged_in = False; st.session_state.user = None; st.session_state.messages = []
            st.rerun()
    return menu

def topbar(user):
    st.markdown(
        f'<div class="app-topbar"><div><div class="app-topbar-title">Government Document & Rules Workspace</div>'
        f'<div class="app-topbar-sub">Internal · {safe_str(user.get("office_name")) or "GovDocs AI"}</div></div>'
        f'<div style="text-align:right;"><div class="app-topbar-title">{date.today().strftime("%d %b %Y")}</div>'
        f'<div class="app-topbar-sub">{esc(user.get("name"))} · {esc(user.get("tier","Staff"))}</div></div></div>',
        unsafe_allow_html=True,
    )

def show_ai(user):
    page_header("AI Rules Assistant", "Ask about leave, TA/DA, service rules and indexed office circulars.")
    used = get_ai_usage_today(user["email"])
    engine = get_setting("ai_provider", "gemini")
    engine_name = PROVIDERS.get(engine, PROVIDERS["gemini"])[0]
    admin_provider = engine.lower()
    default_idx = ["gemini", "groq", "qwen"].index(admin_provider) if admin_provider in ["gemini", "groq", "qwen"] else 0
    with st.container(border=True):
        c1, c2, c3 = st.columns([1.1, 1.9, 1])
        with c1:
            provider = st.selectbox("Model", ["Gemini", "Groq", "Qwen"], index=default_idx, key="ai_provider_ui")
        with c2:
            custom_key = st.text_input("Custom API key (optional)", type="password", placeholder="Power-user key; leave blank for system key")
        with c3:
            st.markdown(f"<div style='padding-top:29px;text-align:right;color:#64748B;font-size:11px;'>AI queries used: <b>{used}/{DAILY_AI_LIMIT}</b><br>Admin engine: {engine_name}</div>", unsafe_allow_html=True)
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
    smalltalk = user_input.strip().lower().rstrip("!., ") in {
        "hi", "hello", "hey", "namaste", "good morning", "good afternoon",
        "good evening", "thanks", "thank you", "ok", "okay", "test",
    }
    with st.chat_message("assistant"):
        sources = [] if smalltalk else search_uploaded_circulars(user_input, limit=4)
        base_rules = (
            "You are an internal staff knowledge assistant for a state transport department office. "
            "BEHAVIOUR RULES: "
            "(1) If the user's message is only a greeting or small talk (hi, hello, good morning, thanks, ok), reply with a warm 1-2 line greeting and suggest 2-3 example questions they can ask. Do NOT say 'Not found in the uploaded circulars' for greetings. "
            "(2) Keep answers concise (about 150 words max) unless the user asks for detail. "
            "(3) Never invent G.O. or circular numbers. "
            "(4) End rule-answers with one line reminding the user to confirm against the current G.O. or establishment section. "
        )
        if sources:
            source_text = ""
            for i, s in enumerate(sources, 1):
                source_text += f"\n--- Source {i}: {s.get('ref_id')} — {s.get('title')} ---\n{s.get('content','')}\n"
            sys_context = base_rules + (
                "Use the OFFICE CIRCULAR EXCERPTS below as your PRIMARY source. "
                "If the answer is in the excerpts, answer from them and quote the reference number. "
                "If the answer is NOT in the excerpts, say 'Not found in the uploaded circulars' and then give brief general guidance.\n\n"
                f"OFFICE CIRCULAR EXCERPTS:\n{source_text}"
            )
        else:
            sys_context = base_rules + (
                "No uploaded circulars matched this question. If the user asked a genuine rules or procedure question, "
                "start your answer with 'Not found in the uploaded circulars.' and then give brief general guidance "
                "using known Indian state civil-service concepts."
            )
        with st.spinner("Checking indexed documents and rules..."):
            reply, err = ai_call(user_input, sys_context) if not custom_key.strip() else _call_one(provider_code, custom_key.strip(), get_setting(f"{provider_code}_model", PROVIDERS.get(provider_code, PROVIDERS["gemini"])[2]), get_setting(f"{provider_code}_endpoint", PROVIDERS.get(provider_code, PROVIDERS["gemini"])[3]), user_input, sys_context)
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
            elif not smalltalk:
                st.caption("No matching uploaded circulars — answer is based on general guidance.")
            st.session_state.messages.append({"role": "assistant", "content": reply})
            log_ai_usage(user["email"])

def show_home(user):
    page_header(f"{greeting()}, {safe_str(user.get('name')).split(' ')[0] or 'there'} 👋", "Here's what's happening in your workspace today.")
    circulars = fetch_circulars()
    tapal = fetch_tapal()
    this_month = date.today().strftime("%Y-%m")
    tapal_this_month = [r for r in tapal if safe_str(r.get("tapal_date")).startswith(this_month)]
    used = get_ai_usage_today(user["email"])
    a, b, c, d = st.columns(4)
    with a:
        st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Circulars & G.O.s</div><div class='kpi-value'>{len(circulars)}</div><div class='kpi-foot'>Total published</div></div>", unsafe_allow_html=True)
    with b:
        st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Tapal this month</div><div class='kpi-value'>{len(tapal_this_month)}</div><div class='kpi-foot'>{len(tapal)} total logged</div></div>", unsafe_allow_html=True)
    with c:
        st.markdown(f"<div class='kpi-card'><div class='kpi-label'>AI queries today</div><div class='kpi-value'>{used}/{DAILY_AI_LIMIT}</div><div class='kpi-foot'>Resets daily</div></div>", unsafe_allow_html=True)
    with d:
        st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Your access tier</div><div class='kpi-value' style='font-size:20px;'>{tier_badge(user.get('tier','Staff'))}</div></div>", unsafe_allow_html=True)
    st.divider()
    st.subheader("📢 Recently published")
    recent = sorted(circulars, key=lambda r: safe_str(r.get("uploaded_at")), reverse=True)[:5]
    if not recent:
        st.info("No circulars published yet.")
    else:
        for c_ in recent:
            allowed = has_access(user.get("tier", "Staff"), c_.get("tier", "Basic"))
            st.markdown(
                f'<div class="doc-card"><div class="doc-row"><span class="doc-ref">{esc(c_.get("ref_id"))}</span>{tier_badge(c_.get("tier","Basic"))}</div>'
                f'<div class="doc-title">{esc(c_.get("title"))}</div>'
                f'<div class="doc-meta">🗂️ {esc(c_.get("category"))} · 📅 {esc(c_.get("doc_date"))}</div></div>',
                unsafe_allow_html=True,
            )
            if allowed and c_.get("link"):
                st.markdown(f"[📥 Open document]({safe_str(c_.get('link'))})")
            elif not allowed:
                st.caption(f"🔒 Requires {safe_str(c_.get('tier'))} access or higher")

def show_circulars(user):
    page_header("Circulars & G.O.s", "Browse published circulars, G.O.s and notifications.")
    rows = fetch_circulars()
    a, b, c = st.columns([2, 1, 1])
    with a:
        search = st.text_input("Search", placeholder="Search title, reference number or category...", label_visibility="collapsed")
    with b:
        types = ["All"] + sorted({safe_str(r.get("doc_type")) for r in rows if r.get("doc_type")})
        tfilter = st.selectbox("Type", types, label_visibility="collapsed")
    with c:
        cats = ["All"] + sorted({safe_str(r.get("category")) for r in rows if r.get("category")})
        cfilter = st.selectbox("Category", cats, label_visibility="collapsed")
    if search:
        s = search.lower()
        rows = [r for r in rows if s in safe_str(r.get("title")).lower() or s in safe_str(r.get("ref_id")).lower() or s in safe_str(r.get("category")).lower()]
    if tfilter != "All":
        rows = [r for r in rows if r.get("doc_type") == tfilter]
    if cfilter != "All":
        rows = [r for r in rows if r.get("category") == cfilter]
    rows = sorted(rows, key=lambda r: safe_str(r.get("doc_date")), reverse=True)
    st.caption(f"{len(rows)} document(s)")
    if not rows:
        st.info("No circulars match your filters.")
        return
    for r in rows:
        allowed = has_access(user.get("tier", "Staff"), r.get("tier", "Basic"))
        sup = f" · Supersedes {esc(r.get('supersedes'))}" if r.get("supersedes") else ""
        st.markdown(
            f'<div class="doc-card"><div class="doc-row"><span class="doc-ref">{esc(r.get("ref_id"))}</span>{tier_badge(r.get("tier","Basic"))}</div>'
            f'<div class="doc-title">{esc(r.get("title"))}</div>'
            f'<div class="doc-meta">🗂️ {esc(r.get("category"))} · 📅 {esc(r.get("doc_date"))}{sup}</div></div>',
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns([1, 5])
        with col1:
            if allowed and r.get("link"):
                st.markdown(f"[📥 Open]({safe_str(r.get('link'))})")
            elif not allowed:
                st.warning(f"🔒 Requires {safe_str(r.get('tier'))} access or higher")

def show_templates(user):
    page_header("Drafts & Templates", "Pre-approved office formats, organized by access tier.")
    rows = fetch_templates()
    if not rows:
        st.info("No templates available yet. Ask an administrator to publish one."); return
    for t in rows:
        tier = t.get("tier", "Basic")
        allowed = has_access(user.get("tier", "Staff"), tier)
        st.markdown(f'<div class="doc-card"><div class="doc-row"><span class="doc-ref">Template</span>{tier_badge(tier)}</div><div class="doc-title">{esc(t.get("title"))}</div><div class="doc-meta">📝 {esc(t.get("description") or "No description")}</div></div>', unsafe_allow_html=True)
        if allowed and t.get("link"): st.markdown(f"[📥 Download Template]({safe_str(t.get('link'))})")
        elif not allowed: st.warning(f"🔒 Requires {tier} access or higher")

def show_tapal(user):
    page_header("Tapal Workspace", "Log, browse and report inward/outward correspondence.")
    t1, t2, t3 = st.tabs(["➕ New Entry", "📋 Browse", "📊 Monthly Report"])
    with t1:
        with st.form("tapal_form", clear_on_submit=True):
            a, b = st.columns(2)
            with a:
                direction = st.selectbox("Direction", ["Inward", "Outward"])
                tdate = st.date_input("Date", value=date.today(), max_value=date.today())
                from_to = st.text_input("From / To *")
            with b:
                subject = st.text_input("Subject *")
                file_ref = st.text_input("File / Reference No.")
                remarks = st.text_area("Remarks", height=85)
            if st.form_submit_button("Save Entry", type="primary", use_container_width=True):
                if not from_to.strip() or not subject.strip(): st.warning("From/To and Subject are required.")
                else:
                    supabase.table("tapal_log").insert({"direction": direction, "tapal_date": tdate.isoformat(), "from_to": from_to.strip(), "subject": subject.strip(), "file_ref": file_ref.strip() or None, "remarks": remarks.strip() or None, "entered_by": user["email"], "entered_at": datetime.utcnow().isoformat()}).execute()
                    fetch_tapal.clear(); st.success("Entry saved.")
    with t2:
        rows = fetch_tapal()
        a, b = st.columns([3, 1])
        with a: search = st.text_input("Search Tapal", placeholder="Search name, subject or reference...", label_visibility="collapsed")
        with b: dfilter = st.selectbox("Direction", ["All", "Inward", "Outward"], label_visibility="collapsed")
        if search: rows = [r for r in rows if search.lower() in str(r).lower()]
        if dfilter != "All": rows = [r for r in rows if r.get("direction") == dfilter]
        st.caption(f"{len(rows)} record(s)")
        for r in rows:
            inward = r.get("direction") == "Inward"
            cls = "tapal-inward" if inward else "tapal-outward"
            icon = "📥" if inward else "📤"
            ref_txt = " · Ref: " + esc(r.get("file_ref")) if r.get("file_ref") else ""
            remarks_txt = ""
            if r.get("remarks"):
                remarks_txt = '<br><span style="font-size:10px;color:#64748B;">📝 ' + esc(r.get("remarks")) + "</span>"
            card_html = (
                '<div class="tapal-card ' + cls + '">'
                '<div style="font-weight:700;font-size:13px;">' + icon + " " + esc(r.get("subject")) + "</div>"
                '<div style="font-size:10px;color:#64748B;margin-top:5px;">'
                + esc(r.get("from_to")) + " · " + esc(r.get("tapal_date")) + ref_txt
                + "</div>" + remarks_txt + "</div>"
            )
            st.markdown(card_html, unsafe_allow_html=True)
    with t3:
        today = date.today()
        a, b = st.columns(2)
        with a: rm = st.selectbox("Month", list(range(1, 13)), index=today.month - 1, format_func=lambda m: date(2000, m, 1).strftime("%B"))
        with b: ry = st.number_input("Year", min_value=2020, max_value=2100, value=today.year)
        start = date(int(ry), rm, 1)
        end = date(int(ry) + (1 if rm == 12 else 0), rm % 12 + 1, 1)
        res = supabase.table("tapal_log").select("*").gte("tapal_date", start.isoformat()).lt("tapal_date", end.isoformat()).order("tapal_date").execute()
        df = pd.DataFrame(res.data or [])
        if df.empty: st.info(f"No entries for {start.strftime('%B %Y')}.")
        else:
            a, b, c = st.columns(3)
            a.metric("Inward", int((df["direction"] == "Inward").sum())); b.metric("Outward", int((df["direction"] == "Outward").sum())); c.metric("Total", len(df))
            cols = [c_ for c_ in ["tapal_date", "direction", "from_to", "subject", "file_ref", "remarks"] if c_ in df.columns]
            st.dataframe(df[cols], use_container_width=True, hide_index=True)
            st.download_button("📥 Download CSV", df.to_csv(index=False).encode(), f"tapal_report_{start:%Y_%m}.csv", "text/csv")

def show_dispatch(user):
    page_header("Dispatch Label Generator", "Extract an address from a scan/photo and generate print-ready labels.")
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
                if img.width < 1500: img = img.resize((1500, int(img.height * 1500 / img.width)))
                img = img.point(lambda p: 255 if p > 150 else 0)
                st.text_area("2 · Review extracted address", value=pytesseract.image_to_string(img, config="--psm 6").strip(), height=100, key="ocr_extracted")
                with st.expander("Preview processed image"): st.image(img, use_container_width=True)
            except Exception as e:
                st.warning(f"OCR unavailable or failed: {e}")
        address_text = st.text_area("3 · Final address *", value=st.session_state.get("ocr_extracted", ""), height=130)
        a, b, c = st.columns(3)
        with a: font_size = st.slider("Font size (pt)", 14, 36, 22)
        with b: env = st.selectbox("Envelope", ["Long Cover (approx 10 x 4.5 in)", "C5 (229 x 162 mm)", "DL (220 x 110 mm)", "Custom"])
        with c: copies = st.number_input("Copies", 1, 100, 1)
        presets = {"Long Cover (approx 10 x 4.5 in)": (254, 114), "C5 (229 x 162 mm)": (229, 162), "DL (220 x 110 mm)": (220, 110)}
        if env == "Custom":
            x, y = st.columns(2)
            w = x.number_input("Width (mm)", 50, 400, 220); h = y.number_input("Height (mm)", 50, 400, 110)
        else: w, h = presets[env]
        if st.button("🖨️ Generate Label PDF", type="primary", use_container_width=True):
            if not address_text.strip(): st.warning("Please enter an address."); return
            try:
                from reportlab.lib.units import mm
                from reportlab.pdfgen import canvas
                buf = io.BytesIO()
                c = canvas.Canvas(buf, pagesize=(w * mm, h * mm))
                lines = [ln for ln in address_text.strip().split("\n") if ln.strip()]
                lh = font_size * 1.4
                for _ in range(int(copies)):
                    c.setFont("Helvetica-Bold", font_size)
                    y = (h * mm + len(lines) * lh) / 2 - lh
                    for ln in lines:
                        c.drawString(10 * mm, y, ln); y -= lh
                    c.showPage()
                c.save(); buf.seek(0)
                supabase.table("dispatch_log").insert({"address_text": address_text.strip(), "copies": int(copies), "generated_by": user["email"], "generated_at": datetime.utcnow().isoformat()}).execute()
                st.success(f"Generated {copies} label(s).")
                st.download_button("📥 Download Label PDF", buf, "dispatch_labels.pdf", "application/pdf")
            except Exception as e:
                st.error(f"Couldn't generate the PDF: {e}")

def show_directory(user):
    page_header("Staff Directory", "Find contacts across departments and roles.")
    df = pd.DataFrame(fetch_directory())
    search = st.text_input("Search directory", placeholder="Search name, division, role or office...")
    if search and not df.empty:
        df = df[df.apply(lambda r: search.lower() in " ".join(map(str, r.values)).lower(), axis=1)]
    if df.empty: st.info("No staff records found."); return
    st.dataframe(df, use_container_width=True, hide_index=True)

def request_upgrade(u, tier):
    ex = supabase.table("access_requests").select("id").eq("email", u["email"]).eq("requested_tier", tier).eq("status", "pending").execute()
    if ex.data:
        st.info("You already have a pending request for this plan.")
    else:
        supabase.table("access_requests").insert({"user_id": u.get("id"), "email": u["email"], "requested_tier": tier, "status": "pending"}).execute()
        st.success("Request sent to admin for approval.")

def show_billing(user):
    page_header("Plans & Billing", "Choose the workspace level that matches your needs.")
    cycle = st.radio("Billing cycle", ["Monthly", "Yearly"], horizontal=True, label_visibility="collapsed")
    yearly = cycle == "Yearly"
    pro_p = int(get_setting("pro_yearly" if yearly else "pro_monthly", "3588" if yearly else "299"))
    max_p = int(get_setting("max_yearly" if yearly else "max_monthly", "9588" if yearly else "799"))
    per = "year" if yearly else "month"
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="plan-card"><div class="plan-name">Basic</div><div class="plan-price">₹0 <span class="plan-period">/ month</span></div><div class="plan-description">Essential tools for everyday office work.</div><div class="feature">✓ Standard circular reference</div><div class="feature">✓ Tapal register</div><div class="feature">✓ Directory access</div><div class="feature">✓ Daily rate-limited AI queries</div></div>', unsafe_allow_html=True)
        st.button("Current plan" if user.get("tier") in ("Basic", "Staff") else "Get Started", disabled=True, use_container_width=True, key="basic_plan")
    with c2:
        st.markdown(f'<div class="plan-card featured"><div class="plan-pill">MOST POPULAR</div><div class="plan-name">Pro</div><div class="plan-price">₹{pro_p:,} <span class="plan-period">/ {per}</span></div><div class="plan-description">For professionals that need faster access.</div><div class="feature">✓ Everything in Basic</div><div class="feature">✓ Priority AI access</div><div class="feature">✓ Template downloads</div><div class="feature">✓ Pro-grade circulars</div></div>', unsafe_allow_html=True)
        if user.get("tier") in ("Basic", "Staff"):
            if st.button("Request Pro Access", type="primary", use_container_width=True, key="pro_plan"):
                request_upgrade(user, "Pro"); st.rerun()
        else:
            st.button("Current plan", disabled=True, use_container_width=True, key="pro_cur")
    with c3:
        st.markdown(f'<div class="plan-card"><div class="plan-name" style="color:#6D28D9;">Max</div><div class="plan-price">₹{max_p:,} <span class="plan-period">/ {per}</span></div><div class="plan-description">Full workspace power for advanced use.</div><div class="feature">✓ Everything in Pro</div><div class="feature">✓ Unlimited archives</div><div class="feature">✓ Priority queue routing</div><div class="feature">✓ Priority support</div></div>', unsafe_allow_html=True)
        if user.get("tier") in ("Basic", "Staff", "Pro"):
            if st.button("Request Max Access", type="primary", use_container_width=True, key="max_plan"):
                request_upgrade(user, "Max"); st.rerun()
        else:
            st.button("Current plan", disabled=True, use_container_width=True, key="max_cur")

def show_admin(user):
    if user.get("tier") != "Admin":
        st.error("Admin access required."); return
    page_header("Admin Command Center", "Manage users, publish documents, configure AI and monitor health.")
    section = st.radio("Admin section", ["👥 Users", "🏢 Org Settings", "📢 Document Publisher", "🔧 AI & Gateway Settings", "🩺 Health & Diagnostics"], horizontal=True, label_visibility="collapsed")
    if section == "👥 Users":
        st.subheader("Pending access requests")
        res = supabase.table("pending_requests").select("*").eq("status", "pending").execute()
        if res.data:
            for r in res.data:
                with st.container(border=True):
                    st.markdown(f"**{safe_str(r.get('name'))}** · {safe_str(r.get('email'))}")
                    st.caption(safe_str(r.get("note")))
                    a, b, c = st.columns([1.2, .8, .7])
                    with a: pw = st.text_input("Set password", key=f"pw_{r['id']}", type="password")
                    with b: tr = st.selectbox("Tier", ["Staff", "Pro", "Max", "Admin"], key=f"tier_{r['id']}")
                    with c:
                        if st.button("Approve", key=f"appr_{r['id']}", type="primary"):
                            if pw:
                                supabase.table("users").insert({"email": r["email"], "name": r["name"], "password_hash": hash_password(pw), "tier": tr, "active": True}).execute()
                                supabase.table("pending_requests").update({"status": "approved"}).eq("id", r["id"]).execute()
                                st.success("Approved."); st.rerun()
                            else: st.warning("Set a password first.")
        else: st.caption("No pending requests.")
        st.subheader("Pro/Max upgrade requests")
        ups = supabase.table("access_requests").select("*").eq("status", "pending").execute()
        if ups.data:
            for r in ups.data:
                with st.container(border=True):
                    st.markdown(f"**{safe_str(r.get('email'))}** requests **{safe_str(r.get('requested_tier'))}")
                    a, b = st.columns(2)
                    with a:
                        if st.button("Approve", key=f"up_ok_{r['id']}", type="primary"):
                            supabase.table("users").update({"tier": r["requested_tier"]}).eq("email", r["email"]).execute()
                            supabase.table("access_requests").update({"status": "approved", "reviewed_by": user["email"], "reviewed_at": datetime.utcnow().isoformat()}).eq("id", r["id"]).execute()
                            st.success("Upgraded."); st.rerun()
                    with b:
                        if st.button("Reject", key=f"up_no_{r['id']}"):
                            supabase.table("access_requests").update({"status": "rejected", "reviewed_by": user["email"], "reviewed_at": datetime.utcnow().isoformat()}).eq("id", r["id"]).execute()
                            st.rerun()
        else: st.caption("No upgrade requests.")
        st.divider(); st.subheader("Create user directly")
        with st.form("create_user_form", clear_on_submit=True):
            a, b = st.columns(2)
            with a:
                cn = st.text_input("Full Name"); ce = st.text_input("Email")
            with b:
                cp = st.text_input("Password", type="password"); cr = st.selectbox("Tier", ["Staff", "Pro", "Max", "Admin"])
            if st.form_submit_button("+ Create Account", type="primary", use_container_width=True):
                if not (cn.strip() and ce.strip() and cp): st.warning("Name, email and password are required.")
                elif supabase.table("users").select("id").eq("email", ce.strip().lower()).execute().data: st.warning("Email already exists.")
                else:
                    supabase.table("users").insert({"email": ce.strip().lower(), "name": cn.strip(), "password_hash": hash_password(cp), "tier": cr, "active": True}).execute()
                    st.success("Account created."); st.rerun()
        st.divider(); st.subheader("User roster")
        all_users = supabase.table("users").select("*").execute().data or []
        us = st.text_input("Search users", placeholder="Name or email...")
        if us: all_users = [u for u in all_users if us.lower() in safe_str(u.get("name")).lower() or us.lower() in safe_str(u.get("email")).lower()]
        for u in all_users:
            active = u.get("active", True)
            with st.container(border=True):
                a, b, c, d = st.columns([2.2, 1, 1.1, 1])
                with a:
                    st.markdown(f"{'🟢' if active else '🔴'} **{safe_str(u.get('name'))}**")
                    st.caption(safe_str(u.get("email")))
                with b: st.markdown(tier_badge(u.get("tier", "Staff")), unsafe_allow_html=True)
                with c:
                    npw = st.text_input("New password", key=f"rpw_{u['id']}", type="password", label_visibility="collapsed", placeholder="New password")
                    if st.button("Reset", key=f"rst_{u['id']}"):
                        if npw: supabase.table("users").update({"password_hash": hash_password(npw)}).eq("id", u["id"]).execute(); st.success("Reset.")
                        else: st.warning("Enter a password.")
                with d:
                    if st.button("Deactivate" if active else "Activate", key=f"tgl_{u['id']}"):
                        supabase.table("users").update({"active": not active}).eq("id", u["id"]).execute()
                        if active: supabase.table("sessions").delete().eq("email", u["email"]).execute()
                        st.rerun()
                e, f = st.columns([1.1, 1])
                tiers = ["Staff", "Basic", "Pro", "Max", "Admin"]
                cur_tier = u.get("tier", "Staff")
                with e:
                    new_tier = st.selectbox("Change plan", tiers, index=tiers.index(cur_tier) if cur_tier in tiers else 0, key=f"plan_{u['id']}", label_visibility="collapsed")
                with f:
                    if st.button("Change Plan", key=f"chg_{u['id']}", disabled=(new_tier == cur_tier)):
                        supabase.table("users").update({"tier": new_tier}).eq("id", u["id"]).execute()
                        st.success(f"{safe_str(u.get('name'))} moved to {new_tier}."); st.rerun()
    elif section == "🏢 Org Settings":
        st.subheader("Departments")
        st.caption("Shown as dropdown choices on the signup form — one per line.")
        cur_depts = "\n".join(get_org_list("departments", DEFAULT_DEPARTMENTS))
        depts_in = st.text_area("Departments", value=cur_depts, height=110, label_visibility="collapsed")
        st.subheader("Offices")
        st.caption("One per line (commas are fine within a name, e.g. 'DTC Office, Visakhapatnam').")
        cur_offs = "\n".join(get_org_list("offices", DEFAULT_OFFICES))
        offs_in = st.text_area("Offices", value=cur_offs, height=110, label_visibility="collapsed")
        if st.button("Save Org Settings", type="primary"):
            set_setting("departments", ";".join(x.strip() for x in depts_in.splitlines() if x.strip()))
            set_setting("offices", ";".join(x.strip() for x in offs_in.splitlines() if x.strip()))
            st.success("Saved. New signups will see the updated lists.")
    elif section == "📢 Document Publisher":
        st.subheader("Publish new circular / G.O.")
        source = st.radio("Document source", ["Upload PDF", "Paste a link"], horizontal=True)
        with st.form("add_go_form"):
            a, b = st.columns(2)
            with a:
                dt = st.selectbox("Type", ["G.O.", "Memo", "U.O.", "Circular", "Notification", "Office Order", "Letter"])
                rn = st.text_input("Reference Number *", placeholder="e.g. Ms.No.102")
                dd = st.date_input("Document Date *", value=date.today(), max_value=date.today())
            with b:
                tt = st.text_input("Title / Subject *")
                cat = st.selectbox("Category", ["Finance / HR", "Operations", "Confidential", "Executive"])
                tier = st.selectbox("Minimum Tier", ["Basic", "Pro", "Max"])
            sup_ = st.text_input("Supersedes / Amends")
            up = st.file_uploader("PDF file (max 20 MB)", type=["pdf"]) if source == "Upload PDF" else None
            lk = st.text_input("External PDF / Drive URL") if source == "Paste a link" else ""
            if st.form_submit_button("Publish Document", type="primary", use_container_width=True):
                ref_id = f"{dt} {rn}".strip()
                errs = []
                if not rn.strip(): errs.append("Reference number is required.")
                if not tt.strip(): errs.append("Title is required.")
                if supabase.table("circulars").select("id").eq("ref_id", ref_id).execute().data: errs.append(f"'{ref_id}' already exists.")
                if source == "Upload PDF" and up is None: errs.append("Choose a PDF.")
                if source == "Paste a link" and not lk.strip(): errs.append("Paste a document link.")
                if errs:
                    for e in errs: st.warning(e)
                else:
                    final_link = lk.strip(); text = ""; ocr = False
                    if source == "Upload PDF":
                        fb = up.read()
                        if len(fb) / 1048576 > MAX_UPLOAD_MB: st.error("File too large."); return
                        safe_name = f"{dt.replace('.','').replace(' ','_')}_{rn.strip().replace(' ','_').replace('/','-')}_{dd.isoformat()}.pdf"
                        with st.spinner("Reading PDF (OCR if scanned)..."): text, ocr = extract_pdf_text(fb)
                        with st.spinner("Compressing and uploading to R2..."):
                            try: final_link = upload_to_r2(compress_for_r2(fb), safe_name + ".gz")
                            except Exception as e:
                                log_error("r2_upload", str(e)); st.error(f"Upload failed: {e}"); final_link = None
                    if final_link:
                        ins = supabase.table("circulars").insert({"ref_id": ref_id, "doc_type": dt, "ref_number": rn.strip(), "doc_date": dd.isoformat(), "title": tt.strip(), "category": cat, "year": dd.year, "tier": tier, "link": final_link, "supersedes": sup_.strip() or None, "uploaded_by": user["email"], "uploaded_at": datetime.utcnow().isoformat()}).execute()
                        n = index_circular_for_ai(ins.data[0]["id"], text) if text else 0
                        st.success(f"Published: {ref_id} · AI blocks: {n}" + (" · OCR used" if ocr else ""))
                        fetch_circulars.clear(); st.rerun()
    elif section == "🔧 AI & Gateway Settings":
        st.subheader("AI provider configuration")
        cur = get_setting("ai_provider", "gemini")
        prov = st.selectbox("Active provider", list(PROVIDERS.keys()), index=list(PROVIDERS.keys()).index(cur) if cur in PROVIDERS else 0, format_func=lambda x: PROVIDERS[x][0])
        name, kind, dm, de = PROVIDERS[prov]
        k = st.text_input(f"{name} API Key", value=get_setting(f"{prov}_api_key"), type="password")
        m = st.text_input("Model", value=get_setting(f"{prov}_model", dm))
        ep = st.text_input("Base URL", value=get_setting(f"{prov}_endpoint", de), disabled=(kind == "gemini"))
        if st.button("Save Gateway", type="primary"):
            set_setting("ai_provider", prov); set_setting(f"{prov}_api_key", k.strip()); set_setting(f"{prov}_model", m.strip()); set_setting(f"{prov}_endpoint", ep.strip())
            st.success("Saved. All users now use this engine by default.")
        if st.button("🧪 Test provider"):
            r, e = _call_one(prov, k.strip(), m.strip(), ep.strip(), "Reply exactly: AI gateway connection OK", "You are a connection test.")
            st.error(e) if e else st.success(r)
        st.divider(); st.subheader("Subscription pricing (₹)")
        a, b = st.columns(2)
        with a:
            pm = st.number_input("Pro Monthly", 0, 100000, int(get_setting("pro_monthly", "299")))
            py_ = st.number_input("Pro Yearly", 0, 1000000, int(get_setting("pro_yearly", "3588")))
        with b:
            mm = st.number_input("Max Monthly", 0, 100000, int(get_setting("max_monthly", "799")))
            my_ = st.number_input("Max Yearly", 0, 1000000, int(get_setting("max_yearly", "9588")))
        if st.button("Save Pricing", type="primary"):
            for kk, vv in [("pro_monthly", pm), ("pro_yearly", py_), ("max_monthly", mm), ("max_yearly", my_)]: set_setting(kk, str(int(vv)))
            st.success("Pricing saved.")
    elif section == "🩺 Health & Diagnostics":
        st.subheader("System health")
        n_users = supabase.table("users").select("id", count="exact", head=True).execute().count or 0
        n_circ = supabase.table("circulars").select("id", count="exact", head=True).execute().count or 0
        prov = get_setting("ai_provider", "gemini")
        key_ok = bool(get_setting(f"{prov}_api_key") or secret(f"{prov.upper()}_API_KEY"))
        a, b, c, d = st.columns(4)
        a.markdown(f"<div class='kpi-card'><div class='kpi-label'>Total users</div><div class='kpi-value'>{n_users}</div></div>", unsafe_allow_html=True)
        b.markdown(f"<div class='kpi-card'><div class='kpi-label'>Circulars</div><div class='kpi-value'>{n_circ}</div></div>", unsafe_allow_html=True)
        c.markdown(f"<div class='kpi-card'><div class='kpi-label'>AI engine</div><div class='kpi-value' style='font-size:20px;'>{PROVIDERS.get(prov, PROVIDERS['gemini'])[0]}</div></div>", unsafe_allow_html=True)
        d.markdown(f"<div class='kpi-card'><div class='kpi-label'>Status</div><div class='kpi-value' style='font-size:20px;color:{'#15803D' if key_ok else '#B91C1C'};'>{'Healthy' if key_ok else 'Attention'}</div></div>", unsafe_allow_html=True)
        st.divider(); st.subheader("Recent errors")
        errs = supabase.table("error_log").select("*").order("occurred_at", desc=True).limit(30).execute().data or []
        if not errs: st.success("No errors logged. Everything is running clean.")
        else:
            for e in errs:
                with st.container(border=True):
                    st.markdown(f"**{safe_str(e.get('area'))}** · {safe_str(e.get('occurred_at'))}")
                    st.code(safe_str(e.get("message")), language=None)
            if st.button("🗑️ Clear Error Log"):
                supabase.table("error_log").delete().in_("id", [e["id"] for e in errs]).execute()
                st.rerun()

def show_welcome(user):
    hide_cloud_chrome()
    st.markdown('<div class="login-shell">', unsafe_allow_html=True)
    _, c2, _ = st.columns([1, 1.2, 1])
    with c2:
        with st.container(border=True):
            st.markdown("### Welcome to Staff Huddle 👋")
            st.caption("Your account is ready.")
            st.markdown(
                f"| | |\n|---|---|\n"
                f"| Account | 🟢 Active |\n"
                f"| Plan | 🟢 {esc(user.get('tier','Basic'))} — Free |\n"
                f"| Email | 🟢 Verified |\n"
                f"| Office | {esc(user.get('office_name') or '—')} |\n"
                f"| Department | {esc(user.get('department') or '—')} |\n"
            )
            if st.button("Enter Staff Workspace →", type="primary", use_container_width=True):
                st.session_state["show_welcome"] = False
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- ROUTER ----------------
try_auto_login()
if not st.session_state.logged_in:
    hide_cloud_chrome()
    show_login()
else:
    user = st.session_state.user
    if user.get("tier") == "Admin":
        show_full_chrome()
    else:
        hide_cloud_chrome()
    if st.session_state.get("show_welcome"):
        show_welcome(user)
        st.stop()
    menu = render_sidebar(user)
     persist_session_cookie()
    topbar(user)
    if menu == "🏠 Dashboard": show_home(user)
    elif menu == "📢 Circulars & G.O.s": show_circulars(user)
    elif menu == "🤖 AI Rules Assistant": show_ai(user)
    elif menu == "📝 Templates": show_templates(user)
    elif menu == "✉️ Tapal Register": show_tapal(user)
    elif menu == "📮 Dispatch Labels": show_dispatch(user)
    elif menu == "📞 Staff Directory": show_directory(user)
    elif menu == "💳 Plans & Billing": show_billing(user)
    elif menu == "⚙️ Admin Command Center": show_admin(user)
