import streamlit as st
import pandas as pd
import bcrypt
import secrets as pysecrets
import io
from datetime import datetime, date, timedelta
from supabase import create_client, Client
from streamlit_cookies_controller import CookieController

# ============================================================
# RTA VIZAG STAFF HUDDLE — APPLE GLASS BUILD (final UI push)
# ============================================================

st.set_page_config(
    page_title="RTA Vizag Staff Huddle",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root{
  --glass: rgba(255,255,255,0.55);
  --glass-strong: rgba(255,255,255,0.75);
  --glass-dark: rgba(20,26,42,0.72);
  --hairline: rgba(255,255,255,0.65);
  --hairline-dark: rgba(255,255,255,0.14);
  --blur: blur(24px) saturate(180%);
  --navy-900:#1E3A5F;
  --navy-700:#2C5282;
  --blue:#0A84FF;
  --text:#1D1D1F;
  --muted:#6E6E73;
  --r-lg:24px; --r-md:18px; --r-sm:12px;
  --shadow: 0 8px 32px rgba(31,38,135,0.10);
  --shadow-lg: 0 20px 50px rgba(0,0,0,0.18);
}

html,body{ background:#F5F5F7; }
html,body,[class*="css"]{ font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; }

/* Apple-style mesh wallpaper behind all glass */
.stApp{
  background:
    radial-gradient(1100px 700px at 92% -10%, rgba(10,132,255,0.16), transparent 60%),
    radial-gradient(900px 650px at -10% 25%, rgba(44,82,130,0.15), transparent 60%),
    radial-gradient(1000px 700px at 50% 115%, rgba(94,92,230,0.10), transparent 60%),
    #F5F5F7;
  background-attachment: fixed;
}

#MainMenu,footer,header{visibility:hidden}
h1,h2,h3{color:var(--text);font-weight:700;letter-spacing:-0.022em}
::selection{background:rgba(10,132,255,0.25)}
::-webkit-scrollbar{width:8px;height:8px}
::-webkit-scrollbar-thumb{background:rgba(0,0,0,0.18);border-radius:8px}
::-webkit-scrollbar-track{background:transparent}

/* ---------- APPLE PILL BUTTONS ---------- */
.stButton > button{
  border-radius:980px !important;
  background:var(--glass-strong);
  backdrop-filter:blur(12px) saturate(160%);
  -webkit-backdrop-filter:blur(12px) saturate(160%);
  border:1px solid rgba(0,0,0,0.06);
  color:var(--navy-700);
  font-weight:600;
  transition:all .18s ease;
}
.stButton > button:hover{ background:#fff; box-shadow:0 4px 14px rgba(0,0,0,0.10); }
.stButton > button:active{ transform:scale(0.98); }
.stButton > button[kind="primary"]{
  background:linear-gradient(180deg,var(--navy-700),var(--navy-900)) !important;
  color:#fff !important; border:none !important;
  box-shadow:0 6px 18px rgba(30,58,95,0.35);
}
.stButton > button[kind="primary"]:hover{ filter:brightness(1.12); }

/* ---------- FROSTED SIDEBAR ---------- */
section[data-testid="stSidebar"]{
  background:rgba(255,255,255,0.42) !important;
  backdrop-filter:var(--blur);
  -webkit-backdrop-filter:var(--blur);
  border-right:1px solid var(--hairline) !important;
}
section[data-testid="stSidebar"] div[role="radio"]{display:none}
section[data-testid="stSidebar"] .stRadio > div > label{
  padding:.65rem 1rem;border-radius:var(--r-sm);margin-bottom:3px;
  font-weight:500;color:var(--text);transition:all .18s ease;
}
section[data-testid="stSidebar"] .stRadio > div > label:hover{background:rgba(255,255,255,0.55)}
section[data-testid="stSidebar"] .stRadio > div > label:has(div[aria-checked="true"]){
  background:var(--glass-dark);
  backdrop-filter:blur(16px) saturate(160%);
  color:#fff; box-shadow:0 6px 18px rgba(0,0,0,0.22);
}
section[data-testid="stSidebar"] .stRadio > div > label p{color:inherit}

.user-profile-card{
  background:var(--glass-dark);
  backdrop-filter:var(--blur);
  -webkit-backdrop-filter:var(--blur);
  border:1px solid var(--hairline-dark);
  border-radius:var(--r-lg);
  padding:1.25rem; margin-bottom:1rem; color:#fff;
  box-shadow:var(--shadow-lg);
}
.user-profile-card h3{color:#fff !important;margin:0 0 .25rem 0;font-size:1rem}
.user-profile-card p{color:rgba(255,255,255,.75) !important;margin:0;font-size:.8rem}
.user-profile-card .doc-tier{background:rgba(255,255,255,.16) !important;color:#fff !important}

/* ---------- GLASS CARDS (everything floats) ---------- */
div[data-testid="stVerticalBlockBorderWrapper"]{
  background:var(--glass) !important;
  backdrop-filter:var(--blur);
  -webkit-backdrop-filter:var(--blur);
  border:1px solid var(--hairline) !important;
  border-radius:var(--r-lg) !important;
  box-shadow:var(--shadow);
  transition:transform .2s ease, box-shadow .2s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover{
  transform:translateY(-2px);
  box-shadow:0 14px 40px rgba(31,38,135,0.16);
}

/* ---------- GLASS INPUTS ---------- */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div,
.stDateInput > div > div > input{
  background:rgba(255,255,255,0.65) !important;
  backdrop-filter:blur(10px);
  border:1px solid rgba(0,0,0,0.08) !important;
  border-radius:var(--r-sm) !important;
  transition:all .18s ease;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus{
  border-color:var(--blue) !important;
  box-shadow:0 0 0 4px rgba(10,132,255,0.15) !important;
  background:#fff !important;
}

/* ---------- GLASS METRICS ---------- */
div[data-testid="stMetric"]{
  background:var(--glass);
  backdrop-filter:var(--blur);
  border:1px solid var(--hairline);
  border-radius:var(--r-md);
  padding:1.25rem; box-shadow:var(--shadow);
}

/* ---------- APPLE SEGMENTED CONTROL TABS ---------- */
.stTabs [data-baseweb="tab-list"]{
  background:rgba(120,120,128,0.14);
  border-radius:var(--r-sm); padding:2px; gap:2px; border:none;
}
.stTabs [data-baseweb="tab"]{border-radius:10px;color:var(--text);font-weight:500}
.stTabs [aria-selected="true"]{
  background:rgba(255,255,255,0.92) !important;
  color:var(--text) !important; border-radius:10px !important;
  box-shadow:0 2px 8px rgba(0,0,0,0.12);
}

/* ---------- ALERTS / CHAT ---------- */
div[data-testid="stAlert"]{
  backdrop-filter:blur(14px); border-radius:var(--r-md) !important;
  border:1px solid var(--hairline) !important;
}
div[data-testid="stChatMessage"]{border-radius:var(--r-md)}

/* ---------- DARK-GLASS HERO HEADER ---------- */
.app-header{
  background:var(--glass-dark);
  backdrop-filter:var(--blur);
  -webkit-backdrop-filter:var(--blur);
  border:1px solid var(--hairline-dark);
  border-radius:var(--r-lg);
  padding:2rem 2.25rem; margin-bottom:1.75rem; color:#fff;
  box-shadow:var(--shadow-lg);
}
.app-header h1{color:#fff;margin:0;font-size:1.75rem;font-weight:700}
.app-header p{color:rgba(255,255,255,.7);margin:.35rem 0 0 0;font-size:.95rem}

/* ---------- KPI GLASS TILES ---------- */
.kpi-card{
  background:var(--glass);
  backdrop-filter:var(--blur);
  -webkit-backdrop-filter:var(--blur);
  border:1px solid var(--hairline);
  border-radius:var(--r-lg);
  padding:1.4rem; box-shadow:var(--shadow);
}
.kpi-label{font-size:12px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;margin-bottom:.5rem}
.kpi-value{font-size:1.9rem;font-weight:800;color:var(--text);letter-spacing:-0.02em}

/* ---------- DOCUMENT CARDS ---------- */
.doc-card{
  background:var(--glass);
  backdrop-filter:var(--blur);
  -webkit-backdrop-filter:var(--blur);
  border:1px solid var(--hairline);
  border-radius:var(--r-lg);
  padding:1.3rem; margin-bottom:.6rem; box-shadow:var(--shadow);
}
.doc-card-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:.6rem}
.doc-ref{font-size:11px;font-weight:600;color:var(--navy-700);background:rgba(44,82,130,0.10);padding:5px 12px;border-radius:999px}
.doc-tier{font-size:11px;font-weight:600;padding:5px 12px;border-radius:999px;backdrop-filter:blur(8px)}
.doc-tier.basic{background:rgba(16,185,129,0.14);color:#0B8A5C}
.doc-tier.pro{background:rgba(10,132,255,0.14);color:var(--blue)}
.doc-tier.max{background:rgba(94,92,230,0.14);color:#5E5CE6}
.doc-title{font-weight:700;font-size:1rem;color:var(--text);margin-bottom:.4rem;letter-spacing:-0.01em}
.doc-meta{display:flex;gap:1rem;font-size:12px;color:var(--muted)}

/* ---------- TAPAL CARDS ---------- */
.tapal-card{
  background:var(--glass);
  backdrop-filter:var(--blur);
  border:1px solid var(--hairline);
  border-radius:var(--r-md);
  padding:1rem 1.25rem; margin-bottom:.75rem; box-shadow:var(--shadow);
}
.tapal-card.inward{border-left:4px solid var(--navy-700)}
.tapal-card.outward{border-left:4px solid #34C759}

/* ---------- GLASS LOGIN OVER WALLPAPER ---------- */
.login-container{
  min-height:72vh;
  display:flex;align-items:center;justify-content:center;
  background:
    radial-gradient(900px 600px at 80% 15%, rgba(10,132,255,0.35), transparent 60%),
    radial-gradient(800px 550px at 12% 85%, rgba(94,92,230,0.30), transparent 60%),
    radial-gradient(700px 500px at 55% 55%, rgba(44,82,130,0.35), transparent 65%),
    linear-gradient(160deg,#0B1524,#101B33 55%,#14264A);
  border-radius:var(--r-lg);
  position:relative;overflow:hidden;padding:3rem 1rem;
}
.login-card{
  position:relative;z-index:10;
  background:rgba(255,255,255,0.10);
  backdrop-filter:blur(30px) saturate(180%);
  -webkit-backdrop-filter:blur(30px) saturate(180%);
  border:1px solid rgba(255,255,255,0.22);
  border-radius:28px;
  padding:2.5rem; width:100%; max-width:440px; text-align:center;
  box-shadow:0 30px 70px rgba(0,0,0,0.45);
}
.login-card h1{color:#fff !important;margin:.5rem 0}
.login-card p{color:rgba(255,255,255,0.72) !important;font-size:.9rem}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = ""):
    sub_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f"<div class='app-header'><h1>{title}</h1>{sub_html}</div>",
        unsafe_allow_html=True,
    )


def greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    return "Good evening"


def tier_badge(tier: str) -> str:
    colors = {"Basic": "basic", "Staff": "basic", "Pro": "pro", "Max": "max", "Admin": "max"}
    return f'<span class="doc-tier {colors.get(tier, "basic")}">{tier}</span>'


# --- SUPABASE CONNECTION ---
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
# CACHED FETCHES
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


DAILY_AI_LIMIT = 20
MAX_UPLOAD_MB = 20


# ============================================================
# SETTINGS + ERROR LOG
# ============================================================
def get_setting(key: str, default: str = "") -> str:
    res = supabase.table("app_settings").select("value").eq("key", key).execute()
    return res.data[0]["value"] if res.data else default


def set_setting(key: str, value: str):
    existing = supabase.table("app_settings").select("key").eq("key", key).execute()
    if existing.data:
        supabase.table("app_settings").update({"value": value}).eq("key", key).execute()
    else:
        supabase.table("app_settings").insert({"key": key, "value": value}).execute()


def log_error(area: str, message: str):
    try:
        supabase.table("error_log").insert({
            "area": area, "message": str(message)[:2000],
            "occurred_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception:
        pass


# ============================================================
# CLOUDFLARE R2 + AI BRAIN
# ============================================================
OCR_MAX_PAGES = 40


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
        Bucket=st.secrets["R2_BUCKET_NAME"], Key=object_name,
        Body=file_bytes, ContentType="application/pdf",
    )
    return f"{st.secrets['R2_PUBLIC_URL'].rstrip('/')}/{object_name}"


def extract_pdf_text(file_bytes: bytes):
    import fitz
    import pytesseract
    from PIL import Image, ImageOps, ImageEnhance
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
                img = img.convert("L")
                img = ImageOps.autocontrast(img)
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
                "circular_id": circular_id, "chunk_no": i, "content": ch,
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


def ask_ai(user_prompt: str, sys_context: str):
    provider = get_setting("ai_provider", "gemini")
    if provider == "groq":
        api_key = get_setting("groq_api_key") or st.secrets.get("GROQ_API_KEY", "")
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
    else:
        api_key = get_setting("gemini_api_key") or st.secrets.get("GEMINI_API_KEY", "")
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
# PERSISTENT LOGIN
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
    cookies.remove(COOKIE_NAME)


def try_auto_login():
    if st.session_state.logged_in:
        return
    user = get_user_from_token(cookies.get(COOKIE_NAME))
    if user:
        st.session_state.logged_in = True
        st.session_state.user = user


# ============================================================
# LOGIN SCREEN (glass over wallpaper)
# ============================================================
def show_login():
    st.markdown(
        """
        <div class="login-container">
            <div class="login-card">
                <div style="font-size:3rem;">🧭</div>
                <h1>RTA Vizag Staff Huddle</h1>
                <p>Circulars reference, AI rules assistant & office tools for internal staff use.<br>
                <span style="font-size:0.75rem; opacity:0.7;">Unofficial internal tool — not an official department system.</span></p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_request = st.tabs(["🔐 Sign In", "🙋 Request Access"])
        with tab_login:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Sign In →", use_container_width=True, type="primary"):
                user = get_user(email.strip().lower())
                if user and user.get("active", True) is False:
                    st.error("This account has been deactivated. Contact your admin.")
                elif user and check_password(password, user["password_hash"]):
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    token = create_session_token(user["email"])
                    cookies.set(COOKIE_NAME, token, max_age=SESSION_DAYS * 24 * 3600)
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
        with tab_request:
            st.info("Free internal tool. Submit your details — the admin sets up your login manually.")
            req_name = st.text_input("Full Name")
            req_email = st.text_input("Your Email")
            req_note = st.text_area("Which office / role are you in?", height=80)
            if st.button("Submit Request →", use_container_width=True, type="primary"):
                if req_name and req_email:
                    create_pending_request(req_name, req_email.strip().lower(), req_note)
                    st.success("✓ Request submitted! The admin will contact you once access is set up.")
                else:
                    st.warning("Please fill in your name and email.")


# ============================================================
# MAIN DASHBOARD
# ============================================================
def show_dashboard():
    user = st.session_state.user
    user_tier = user["tier"]

    with st.sidebar:
        st.markdown(
            f"""
            <div class="user-profile-card">
                <h3>👤 {user['name']}</h3>
                <p>{user['email']}</p>
                <p style="margin-top:0.5rem;">{tier_badge(user_tier)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        menu = st.radio(
            "Navigation",
            ["🏠 Home", "📢 Circulars & G.O.s", "🤖 AI Rules Assistant", "📝 Templates", "✉️ Tapal Register",
             "📮 Dispatch Labels", "📞 Staff Directory", "⚙️ Admin Panel"],
            label_visibility="collapsed",
        )
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            clear_session_token(cookies.get(COOKIE_NAME))
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.messages = []
            st.rerun()

    # --- HOME ---
    if menu == "🏠 Home":
        page_header(f"{greeting()}, {user['name'].split()[0]} 👋", "Here's your workspace overview.")
        circ_count = len(fetch_circulars())
        this_month_start = date.today().replace(day=1).isoformat()
        tapal_count = len([r for r in fetch_tapal() if r["tapal_date"] >= this_month_start])
        ai_used_today = get_ai_usage_today(user["email"])
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Circulars on File</div><div class='kpi-value'>{circ_count}</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Tapal This Month</div><div class='kpi-value'>{tapal_count}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='kpi-card'><div class='kpi-label'>AI Queries Today</div><div class='kpi-value'>{ai_used_today}/{DAILY_AI_LIMIT}</div></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Quick Access")
        q1, q2, q3, q4 = st.columns(4)
        for col, icon, name, desc in [
            (q1, "📢", "Circulars", "Search G.O.s, Memos & Circulars"),
            (q2, "🤖", "AI Assistant", "Ask about rules & procedures"),
            (q3, "✉️", "Tapal", "Log inward/outward correspondence"),
            (q4, "📮", "Dispatch", "Print-ready address labels"),
        ]:
            with col:
                st.markdown(
                    f"<div class='doc-card'><div class='doc-title'>{icon} {name}</div><div class='doc-meta'>{desc}</div></div>",
                    unsafe_allow_html=True,
                )

    # --- CIRCULARS ---
    elif menu == "📢 Circulars & G.O.s":
        page_header("📢 Circulars, G.O.s & Memos", "Search and access departmental documents.")
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input("🔍 Search", placeholder="Search by title, number, or keyword...")
        with col2:
            category_filter = st.selectbox("Category", ["All", "Finance / HR", "Operations", "Confidential", "Executive"])
        rows = fetch_circulars()
        if category_filter != "All":
            rows = [r for r in rows if r["category"] == category_filter]
        if search_query:
            q = search_query.lower()
            rows = [r for r in rows if q in r["title"].lower() or q in r["ref_id"].lower()]
        st.caption(f"Showing **{len(rows)}** documents")
        for item in rows:
            allowed = has_access(user_tier, item["tier"])
            st.markdown(
                f"""
                <div class="doc-card">
                    <div class="doc-card-header">
                        <span class="doc-ref">{item['ref_id']}</span>
                        {tier_badge(item['tier'])}
                    </div>
                    <div class="doc-title">{item['title']}</div>
                    <div class="doc-meta"><span>📅 {item['doc_date']}</span><span>📁 {item['category']}</span><span>📆 {item['year']}</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if allowed:
                st.markdown(f"[📥 Open Document]({item['link']})")
            else:
                st.warning(f"🔒 Requires {item['tier']} access or higher")

    # --- AI ASSISTANT ---
    elif menu == "🤖 AI Rules Assistant":
        page_header("🤖 Rules & Procedure Assistant", "Ask about leave, TA/DA, or service rules — it checks your uploaded circulars first.")
        used = get_ai_usage_today(user["email"])
        st.markdown(f"<div class='kpi-card' style='margin-bottom:1rem;'><div class='kpi-label'>Queries Used Today</div><div class='kpi-value'>{used} / {DAILY_AI_LIMIT}</div></div>", unsafe_allow_html=True)
        for m in st.session_state.messages:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])
        if used >= DAILY_AI_LIMIT:
            st.info("Daily limit reached. Try again tomorrow, or ask the admin to raise your limit.")
        elif user_input := st.chat_input("E.g., Can I take CCL if I worked on a holiday?"):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
            with st.chat_message("assistant"):
                sources = search_uploaded_circulars(user_input, limit=4)
                if sources:
                    source_text = ""
                    for i, s in enumerate(sources, 1):
                        source_text += f"\n--- Source {i}: {s['ref_id']} — {s['title']} ---\n{s['content']}\n"
                    sys_context = (
                        "You are an internal staff knowledge assistant for a state transport department office. "
                        "Use the OFFICE CIRCULAR EXCERPTS below as your PRIMARY source.\n"
                        "If the answer is in the excerpts, answer from them and quote the reference number.\n"
                        "If the answer is NOT in the excerpts, say 'Not found in the uploaded circulars' and then give brief general guidance.\n"
                        "Never invent G.O. or circular numbers. Be concise. Always tell the user to confirm against "
                        "the current G.O. or the establishment section before relying on this for official use.\n\n"
                        f"OFFICE CIRCULAR EXCERPTS:\n{source_text}"
                    )
                else:
                    sys_context = (
                        "You are an internal staff knowledge assistant for a state transport department office. "
                        "No uploaded circulars matched this question. Start your answer with 'Not found in the uploaded circulars.' "
                        "Then answer using general knowledge of Indian state civil service rules, Fundamental Rules (FR), "
                        "Leave Rules, and TA/DA norms. Do not invent G.O. numbers. Always tell the user to confirm against "
                        "the current G.O. or the establishment section."
                    )
                with st.spinner("Checking the rules for you..."):
                    bot_reply, err = ask_ai(user_input, sys_context)
                if err:
                    log_error("ai_assistant", err)
                    st.error("Couldn't reach the AI engine right now. The admin can check Admin Panel → System Health for the exact error.")
                else:
                    st.markdown(bot_reply)
                    if sources:
                        st.markdown("**📄 Matched circulars:**")
                        for s in sources:
                            st.caption(f"• {s['ref_id']} — {s['title']}")
                    else:
                        st.caption("No matching uploaded circulars — answer is from general knowledge.")
                    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                    log_ai_usage(user["email"])

    # --- TEMPLATES ---
    elif menu == "📝 Templates":
        page_header("📝 Drafts & Templates", "Pre-approved formats, ready to use.")
        rows = fetch_templates()
        if not rows:
            st.info("No templates available yet. Ask your admin to add some.")
        for t in rows:
            st.markdown(
                f"""
                <div class="doc-card">
                    <div class="doc-card-header"><span class="doc-ref">Template</span>{tier_badge(t['tier'])}</div>
                    <div class="doc-title">{t['title']}</div>
                    <div class="doc-meta"><span>📝 {t.get('description') or 'No description'}</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if has_access(user_tier, t["tier"]) and t.get("link"):
                st.markdown(f"[📥 Download Template]({t['link']})")
            elif not has_access(user_tier, t["tier"]):
                st.warning(f"🔒 Requires {t['tier']} access or higher")

    # --- TAPAL ---
    elif menu == "✉️ Tapal Register":
        page_header("✉️ Tapal / Correspondence Register", "Log and report inward/outward correspondence.")
        tab_add, tab_view, tab_report = st.tabs(["➕ New Entry", "📋 Browse", "📊 Monthly Report"])
        with tab_add:
            with st.form("tapal_form", clear_on_submit=True):
                direction = st.selectbox("Direction", ["Inward", "Outward"])
                tapal_date = st.date_input("Date", value=date.today(), max_value=date.today())
                from_to = st.text_input("From / To *", placeholder="Sender for Inward, Recipient for Outward")
                subject = st.text_input("Subject *")
                file_ref = st.text_input("File / Reference No. (optional)")
                remarks = st.text_area("Remarks (optional)", height=70)
                if st.form_submit_button("Save Entry", type="primary"):
                    if not from_to.strip() or not subject.strip():
                        st.warning("From/To and Subject are required.")
                    else:
                        supabase.table("tapal_log").insert({
                            "direction": direction, "tapal_date": tapal_date.isoformat(),
                            "from_to": from_to.strip(), "subject": subject.strip(),
                            "file_ref": file_ref.strip() or None, "remarks": remarks.strip() or None,
                            "entered_by": user["email"], "entered_at": datetime.utcnow().isoformat(),
                        }).execute()
                        st.success("✓ Entry saved.")
                        fetch_tapal.clear()
        with tab_view:
            rows = fetch_tapal()
            if rows:
                search = st.text_input("🔍 Search", placeholder="Search by name, subject, or reference...")
                if search:
                    q = search.lower()
                    rows = [r for r in rows if q in str(r).lower()]
                for r in rows:
                    dir_class = "inward" if r["direction"] == "Inward" else "outward"
                    dir_icon = "📥" if r["direction"] == "Inward" else "📤"
                    st.markdown(
                        f"""
                        <div class="tapal-card {dir_class}">
                            <strong>{dir_icon} {r['subject']}</strong><br>
                            <small style="color:var(--muted);">{r['from_to']} · {r['tapal_date']}{f" · Ref: {r['file_ref']}" if r.get('file_ref') else ""}</small>
                            {f"<br><small>📝 {r['remarks']}</small>" if r.get('remarks') else ""}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No tapal entries yet. Add one from the 'New Entry' tab.")
        with tab_report:
            today = date.today()
            col1, col2 = st.columns(2)
            with col1:
                report_month = st.selectbox("Month", list(range(1, 13)), index=today.month - 1,
                                            format_func=lambda m: date(2000, m, 1).strftime("%B"))
            with col2:
                report_year = st.number_input("Year", min_value=2020, max_value=2030, value=today.year)
            start = date(report_year, report_month, 1)
            end_month = report_month + 1 if report_month < 12 else 1
            end_year = report_year if report_month < 12 else report_year + 1
            end = date(end_year, end_month, 1)
            res = supabase.table("tapal_log").select("*") \
                .gte("tapal_date", start.isoformat()).lt("tapal_date", end.isoformat()) \
                .order("tapal_date").execute()
            df = pd.DataFrame(res.data or [])
            if df.empty:
                st.info(f"No tapal entries for {start.strftime('%B %Y')}.")
            else:
                c1, c2, c3 = st.columns(3)
                c1.metric("Inward", int((df["direction"] == "Inward").sum()))
                c2.metric("Outward", int((df["direction"] == "Outward").sum()))
                c3.metric("Total", len(df))
                st.dataframe(df[["tapal_date", "direction", "from_to", "subject", "file_ref", "remarks"]],
                             use_container_width=True, hide_index=True)
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(f"📥 Download {start.strftime('%B %Y')} Report (CSV)", data=csv,
                                   file_name=f"tapal_report_{start.strftime('%Y_%m')}.csv", mime="text/csv")

    # --- DISPATCH ---
    elif menu == "📮 Dispatch Labels":
        page_header("📮 Dispatch Label Generator", "Print-ready address labels, no handwriting needed.")
        st.markdown("**Step 1 — Upload the existing letter's address**")
        photo = st.file_uploader("Upload a photo or scan of the address", type=["png", "jpg", "jpeg"])
        if photo is not None:
            try:
                import pytesseract
                from PIL import Image, ImageOps, ImageEnhance
                img = Image.open(photo)
                img = ImageOps.exif_transpose(img)
                img = img.convert("L")
                img = ImageOps.autocontrast(img)
                img = ImageEnhance.Sharpness(img).enhance(2.0)
                if img.width < 1500:
                    scale = 1500 / img.width
                    img = img.resize((1500, int(img.height * scale)))
                img = img.point(lambda p: 255 if p > 150 else 0)
                extracted = pytesseract.image_to_string(img, config="--psm 6")
                st.text_area("Step 2 — Check the extracted address", value=extracted.strip(), height=100, key="ocr_extracted")
                with st.expander("See the processed image OCR actually read"):
                    st.image(img, use_container_width=True)
            except Exception as e:
                st.warning(f"OCR unavailable or failed ({e}). Please type the address manually below.")
        address_text = st.text_area("Step 3 — Confirm final address for the label *",
                                    value=st.session_state.get("ocr_extracted", ""), height=120,
                                    placeholder="Name\nDesignation / Office\nAddress line 1\nCity - PIN")
        font_size = st.slider("Font size (pt)", min_value=14, max_value=36, value=22)
        st.markdown("**Step 4 — Envelope & copies**")
        envelope_presets = {
            "Long Cover (approx 10 x 4.5 in)": (254, 114),
            "C5 (229 x 162 mm)": (229, 162),
            "DL (220 x 110 mm)": (220, 110),
            "Custom": None,
        }
        col1, col2 = st.columns(2)
        with col1:
            envelope_choice = st.selectbox("Envelope size", list(envelope_presets.keys()))
        with col2:
            copies = st.number_input("Number of copies", min_value=1, max_value=100, value=1)
        if envelope_choice == "Custom":
            c1, c2 = st.columns(2)
            with c1:
                width_mm = st.number_input("Width (mm)", min_value=50, max_value=400, value=220)
            with c2:
                height_mm = st.number_input("Height (mm)", min_value=50, max_value=400, value=110)
        else:
            width_mm, height_mm = envelope_presets[envelope_choice]
        if st.button("🖨️ Generate Label PDF", type="primary"):
            if not address_text.strip():
                st.warning("Please enter an address.")
            else:
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
                        x = 10 * mm
                        for ln in lines:
                            c.drawString(x, y, ln)
                            y -= line_height
                        c.showPage()
                    c.save()
                    buf.seek(0)
                    supabase.table("dispatch_log").insert({
                        "address_text": address_text.strip(), "copies": int(copies),
                        "generated_by": user["email"], "generated_at": datetime.utcnow().isoformat(),
                    }).execute()
                    st.success(f"✓ Generated {copies} label(s).")
                    st.download_button("📥 Download Label PDF", data=buf, file_name="dispatch_labels.pdf", mime="application/pdf")
                except Exception as e:
                    st.error(f"Couldn't generate the PDF: {e}")

    # --- DIRECTORY ---
    elif menu == "📞 Staff Directory":
        page_header("📞 Staff Directory", "Find contact details across the office.")
        df = pd.DataFrame(fetch_directory())
        search_staff = st.text_input("🔍 Search", placeholder="Search by name, division, or role...")
        if search_staff and not df.empty:
            mask = df.apply(lambda r: search_staff.lower() in r.astype(str).str.lower().values, axis=1)
            df = df[mask]
        if df.empty:
            st.info("No staff records found.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)

    # --- ADMIN ---
    elif menu == "⚙️ Admin Panel":
        if user_tier != "Admin":
            st.error("⛔ Admin access required.")
            return
        page_header("⚙️ Admin Command Center", "Manage users, documents, and system settings.")
        admin_section = st.radio("Section", ["👥 Users", "📢 Circulars", "🔧 Settings", "🩺 System Health"],
                                 horizontal=True, label_visibility="collapsed")
        st.markdown("---")

        if admin_section == "👥 Users":
            st.subheader("📋 Pending Access Requests")
            res = supabase.table("pending_requests").select("*").eq("status", "pending").execute()
            if res.data:
                for r in res.data:
                    with st.container(border=True):
                        st.markdown(f"**{r['name']}** — {r['email']}")
                        st.caption(r.get("note", ""))
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            approve_pass = st.text_input("Set password", key=f"pw_{r['id']}", type="password")
                        with c2:
                            approve_tier = st.selectbox("Role", ["Staff", "Admin"], key=f"tier_{r['id']}")
                        with c3:
                            if st.button("✓ Approve", key=f"appr_{r['id']}", type="primary"):
                                if approve_pass:
                                    supabase.table("users").insert({
                                        "email": r["email"], "name": r["name"],
                                        "password_hash": hash_password(approve_pass), "tier": approve_tier,
                                    }).execute()
                                    supabase.table("pending_requests").update({"status": "approved"}).eq("id", r["id"]).execute()
                                    st.success(f"✓ Approved {r['email']}")
                                    st.rerun()
                                else:
                                    st.warning("Set a password first.")
            else:
                st.caption("No pending requests.")
            st.markdown("---")
            st.subheader("➕ Create User Directly")
            with st.form("create_user_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    cu_name = st.text_input("Full Name")
                    cu_email = st.text_input("Email")
                with c2:
                    cu_pass = st.text_input("Password", type="password")
                    cu_role = st.selectbox("Role", ["Staff", "Admin"])
                if st.form_submit_button("Create Account", type="primary"):
                    if not (cu_name.strip() and cu_email.strip() and cu_pass):
                        st.warning("All fields are required.")
                    else:
                        existing = supabase.table("users").select("id").eq("email", cu_email.strip().lower()).execute()
                        if existing.data:
                            st.warning("A user with this email already exists.")
                        else:
                            supabase.table("users").insert({
                                "email": cu_email.strip().lower(), "name": cu_name.strip(),
                                "password_hash": hash_password(cu_pass), "tier": cu_role,
                            }).execute()
                            st.success(f"✓ Account created for {cu_email.strip().lower()}")
                            st.rerun()
            st.markdown("---")
            st.subheader("👥 User Roster")
            all_users = supabase.table("users").select("*").neq("tier", "Admin").execute().data or []
            if not all_users:
                st.caption("No non-admin users yet.")
            for u in all_users:
                is_active = u.get("active", True)
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                    with c1:
                        dot = "🟢" if is_active else "🔴"
                        st.markdown(f"{dot} **{u['name']}** — {u['email']}")
                        st.caption(f"Role: {u['tier']}")
                    with c2:
                        new_pw = st.text_input("New password", key=f"resetpw_{u['id']}", type="password",
                                               label_visibility="collapsed", placeholder="New password")
                    with c3:
                        if st.button("🔑 Reset", key=f"reset_{u['id']}"):
                            if new_pw:
                                supabase.table("users").update({"password_hash": hash_password(new_pw)}).eq("id", u["id"]).execute()
                                st.success("✓ Password reset")
                            else:
                                st.warning("Enter a new password.")
                    with c4:
                        toggle_label = "Deactivate" if is_active else "Activate"
                        if is_active:
                            if st.button(toggle_label, key=f"toggle_{u['id']}"):
                                st.session_state[f"confirm_deactivate_{u['id']}"] = True
                            if st.session_state.get(f"confirm_deactivate_{u['id']}"):
                                st.warning(f"Revoke access for **{u['name']}**?")
                                cc1, cc2 = st.columns(2)
                                if cc1.button("Yes, deactivate", key=f"confirm_yes_{u['id']}", type="primary"):
                                    supabase.table("users").update({"active": False}).eq("id", u["id"]).execute()
                                    supabase.table("sessions").delete().eq("email", u["email"]).execute()
                                    st.session_state[f"confirm_deactivate_{u['id']}"] = False
                                    st.rerun()
                                if cc2.button("Cancel", key=f"confirm_no_{u['id']}"):
                                    st.session_state[f"confirm_deactivate_{u['id']}"] = False
                                    st.rerun()
                        else:
                            if st.button(toggle_label, key=f"toggle_{u['id']}"):
                                supabase.table("users").update({"active": True}).eq("id", u["id"]).execute()
                                st.rerun()

        elif admin_section == "📢 Circulars":
            st.subheader("📤 Publish New Circular")
            source_choice = st.radio("Document source", ["Upload PDF", "Paste a link"], horizontal=True, key="doc_source")
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
                supersedes = st.text_input("Supersedes / Amends (optional)")
                uploaded_file = None
                link = ""
                if source_choice == "Upload PDF":
                    uploaded_file = st.file_uploader("PDF file (max 20MB)", type=["pdf"])
                else:
                    link = st.text_input("Link (Drive/PDF URL)")
                if st.form_submit_button("Publish Circular", type="primary"):
                    ref_id = f"{doc_type} {ref_number}".strip()
                    errors = []
                    if not ref_number.strip():
                        errors.append("Reference number is required.")
                    if not title.strip():
                        errors.append("Title is required.")
                    if doc_date > date.today():
                        errors.append("Date cannot be in the future.")
                    if supabase.table("circulars").select("id").eq("ref_id", ref_id).execute().data:
                        errors.append(f"'{ref_id}' already exists.")
                    if source_choice == "Upload PDF" and uploaded_file is None:
                        errors.append("Please choose a PDF.")
                    if source_choice == "Paste a link" and not link.strip():
                        errors.append("Please paste a link.")
                    if errors:
                        for e in errors:
                            st.warning(e)
                    else:
                        final_link = link
                        extracted_text = ""
                        used_ocr = False
                        if source_choice == "Upload PDF":
                            file_bytes = uploaded_file.read()
                            size_mb = len(file_bytes) / (1024 * 1024)
                            if size_mb > MAX_UPLOAD_MB:
                                st.error(f"File too large ({size_mb:.1f}MB). Max {MAX_UPLOAD_MB}MB.")
                                final_link = None
                            else:
                                safe_ref = ref_number.strip().replace(" ", "_").replace("/", "-")
                                safe_name = f"{doc_type.replace('.', '').replace(' ', '')}_{safe_ref}_{doc_date.isoformat()}.pdf"
                                with st.spinner("Reading the PDF for the AI (OCR if scanned)..."):
                                    extracted_text, used_ocr = extract_pdf_text(file_bytes)
                                with st.spinner("Optimising & uploading to cloud storage..."):
                                    try:
                                        final_link = upload_to_r2(optimize_pdf(file_bytes), safe_name)
                                    except Exception as e:
                                        st.error(f"Upload failed: {e}")
                                        log_error("r2_upload", str(e))
                                        final_link = None
                        if final_link:
                            insert_res = supabase.table("circulars").insert({
                                "ref_id": ref_id, "doc_type": doc_type, "ref_number": ref_number.strip(),
                                "doc_date": doc_date.isoformat(), "title": title.strip(), "category": category,
                                "year": doc_date.year, "tier": tier, "link": final_link,
                                "supersedes": supersedes.strip() or None, "uploaded_by": user["email"],
                                "uploaded_at": datetime.utcnow().isoformat(),
                            }).execute()
                            new_id = insert_res.data[0]["id"]
                            n_chunks = index_circular_for_ai(new_id, extracted_text) if (source_choice == "Upload PDF" and extracted_text) else 0
                            msg = f"✓ Published: {ref_id}"
                            if source_choice == "Upload PDF":
                                if n_chunks > 0:
                                    ocr_note = " (used OCR for scanned pages)" if used_ocr else ""
                                    msg += f" — AI can now read it ({n_chunks} text blocks){ocr_note}."
                                else:
                                    msg += " — but no readable text found, so the AI can't search this one yet."
                            st.success(msg)
                            fetch_circulars.clear()
                            st.rerun()

        elif admin_section == "🔧 Settings":
            st.subheader("🤖 AI Provider Configuration")
            st.caption("Change the AI engine or update API keys without redeploying.")
            current_provider = get_setting("ai_provider", "gemini")
            provider_choice = st.selectbox("Active provider", ["gemini", "groq"],
                                           index=["gemini", "groq"].index(current_provider) if current_provider in ["gemini", "groq"] else 0)
            if provider_choice == "gemini":
                gk = st.text_input("Gemini API Key", value=get_setting("gemini_api_key"), type="password",
                                   help="From aistudio.google.com — should start with AIzaSy...")
                gm = st.text_input("Gemini Model", value=get_setting("gemini_model", "gemini-1.5-flash"))
                if st.button("💾 Save Gemini Settings", type="primary"):
                    set_setting("ai_provider", "gemini")
                    set_setting("gemini_api_key", gk.strip())
                    set_setting("gemini_model", gm.strip())
                    st.success("✓ Saved. Takes effect on the next AI question.")
            else:
                gk = st.text_input("Groq API Key", value=get_setting("groq_api_key"), type="password")
                gm = st.text_input("Groq Model ID", value=get_setting("groq_model", "llama-3.1-8b-instant"))
                if st.button("💾 Save Groq Settings", type="primary"):
                    set_setting("ai_provider", "groq")
                    set_setting("groq_api_key", gk.strip())
                    set_setting("groq_model", gm.strip())
                    st.success("✓ Saved. Takes effect on the next AI question.")

        elif admin_section == "🩺 System Health":
            st.subheader("🩺 System Health")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Total Users", len(supabase.table("users").select("id").execute().data or []))
            with c2:
                st.metric("Total Circulars", len(supabase.table("circulars").select("id").execute().data or []))
            with c3:
                provider = get_setting("ai_provider", "gemini")
                key_set = bool(get_setting(f"{provider}_api_key") or st.secrets.get(f"{provider.upper()}_API_KEY", ""))
                st.metric("AI Engine", provider.title(), "Key set ✅" if key_set else "No key ❌")
            st.markdown("---")
            st.subheader("🐛 Recent Errors")
            errors = supabase.table("error_log").select("*").order("occurred_at", desc=True).limit(30).execute().data or []
            if not errors:
                st.success("✓ No errors logged. Everything's running clean.")
            else:
                for e in errors:
                    with st.container(border=True):
                        st.markdown(f"**{e['area']}** — {e['occurred_at']}")
                        st.code(e["message"], language=None)
                if st.button("🗑️ Clear Error Log"):
                    for e in errors:
                        supabase.table("error_log").delete().eq("id", e["id"]).execute()
                    st.rerun()


# ============================================================
try_auto_login()
if not st.session_state.logged_in:
    show_login()
else:
    show_dashboard()
