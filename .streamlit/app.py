import streamlit as st
import pandas as pd
import bcrypt
import secrets as pysecrets
import io
from datetime import datetime, date, timedelta
from supabase import create_client, Client
from streamlit_cookies_controller import CookieController

# ============================================================
# RTA VIZAG STAFF HUDDLE
# Free internal staff tool — NOT an official department system.
# Circulars reference, AI rules assistant, templates, directory.
# ============================================================

st.set_page_config(
    page_title="RTA Vizag Staff Huddle",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- PROFESSIONAL THEME ---
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.app-header {
    background: linear-gradient(135deg, #1E3A5F 0%, #2C5282 100%);
    padding: 1.75rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    color: white;
}
.app-header h1 { color: white; margin: 0; font-size: 1.7rem; font-weight: 700; }
.app-header p { color: #CBD9E8; margin: 0.25rem 0 0 0; font-size: 0.95rem; }

h1, h2, h3 { color: #1E3A5F; font-weight: 700; }

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 10px !important;
    border: 1px solid #E2E8F0 !important;
}

.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    border: none;
}
.stButton > button[kind="primary"] { background-color: #1E3A5F; }
.stButton > button[kind="primary"]:hover { background-color: #2C5282; }

section[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    border-right: 1px solid #E2E8F0;
}

div[data-testid="stMetric"] {
    background-color: white;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 1rem;
}

div[data-testid="stAlert"] { border-radius: 8px; }
div[data-baseweb="notification"] { border-radius: 8px; }

div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: 0 4px 16px rgba(30, 58, 95, 0.10);
    transform: translateY(-1px);
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
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


# --- SUPABASE CONNECTION ---
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


supabase = get_supabase()
cookies = CookieController()
COOKIE_NAME = "huddle_session"
SESSION_DAYS = 30

# --- SESSION STATE ---
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
    if res.data:
        return res.data[0]
    return None


def create_pending_request(name: str, email: str, note: str):
    supabase.table("pending_requests").insert({
        "name": name,
        "email": email,
        "note": note,
        "requested_at": datetime.utcnow().isoformat(),
        "status": "pending",
    }).execute()


def has_access(user_tier: str, required_tier: str) -> bool:
    levels = {"Basic": 1, "Pro": 2, "Max": 3, "Admin": 4}
    return levels.get(user_tier, 0) >= levels.get(required_tier, 0)


# ============================================================
# CACHED DATA FETCHES
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
    else:
        supabase.table("ai_usage").insert({"email": email, "day": today, "count": 1}).execute()
        return 1


def get_ai_usage_today(email: str) -> int:
    today = date.today().isoformat()
    res = supabase.table("ai_usage").select("*").eq("email", email).eq("day", today).execute()
    return res.data[0]["count"] if res.data else 0


DAILY_AI_LIMIT = 20


# ============================================================
# ADMIN-CONFIGURABLE SETTINGS
# ============================================================
def get_setting(key: str, default: str = "") -> str:
    res = supabase.table("app_settings").select("value").eq("key", key).execute()
    if res.data:
        return res.data[0]["value"]
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
            "area": area, "message": str(message)[:2000],
            "occurred_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception:
        pass


# ============================================================
# CLOUDFLARE R2 STORAGE + AI "BRAIN"
# PDFs stored in R2 (10GB free). Extracted text stored in Supabase
# (circular_chunks) so the AI can search it.
# ============================================================
OCR_MAX_PAGES = 40  # cap on pages we'll OCR, to keep uploads from timing out


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
    """Upload a file to Cloudflare R2 and return its public URL."""
    s3 = get_r2_client()
    s3.put_object(
        Bucket=st.secrets["R2_BUCKET_NAME"],
        Key=object_name,
        Body=file_bytes,
        ContentType="application/pdf",
    )
    base = st.secrets["R2_PUBLIC_URL"].rstrip("/")
    return f"{base}/{object_name}"


def extract_pdf_text(file_bytes: bytes):
    """Extract text from a PDF. Uses the embedded text layer for typed pages;
    falls back to OCR for scanned pages. Returns (full_text, used_ocr)."""
    import fitz  # PyMuPDF
    import pytesseract
    from PIL import Image, ImageOps, ImageEnhance
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        log_error("pdf_open", str(e))
        return "", False

    all_text = []
    used_ocr = False
    ocr_done = 0
    for page_num, page in enumerate(doc):
        try:
            page_text = page.get_text().strip()
        except Exception:
            page_text = ""
        if len(page_text) > 40:
            all_text.append(page_text)
        else:
            if ocr_done >= OCR_MAX_PAGES:
                all_text.append(f"[Page {page_num + 1}: scanned — OCR page limit reached, not extracted]")
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
    """Losslessly shrink the PDF before storing it in R2. Returns the original
    if it fails or if the result isn't actually smaller."""
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
    return [text[i:i + chunk_size].strip()
            for i in range(0, len(text), chunk_size)
            if text[i:i + chunk_size].strip()]


def index_circular_for_ai(circular_id: str, text: str) -> int:
    """Store a circular's extracted text in Supabase as searchable chunks.
    Returns the number of chunks stored (0 = nothing indexable)."""
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
    """Search the AI brain (circular_chunks) for text matching the question."""
    try:
        res = supabase.rpc("search_circular_chunks", {"q": question, "limit_count": limit}).execute()
        return res.data or []
    except Exception as e:
        log_error("ai_search", str(e))
        return []


def ask_ai(user_prompt: str, sys_context: str):
    """Routes to whichever AI provider the admin configured in Settings."""
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
                messages=[
                    {"role": "system", "content": sys_context},
                    {"role": "user", "content": user_prompt},
                ],
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
    supabase.table("sessions").insert({
        "token": token, "email": email, "expires_at": expires_at
    }).execute()
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
    token = cookies.get(COOKIE_NAME)
    user = get_user_from_token(token)
    if user:
        st.session_state.logged_in = True
        st.session_state.user = user


# ============================================================
# LOGIN / REQUEST ACCESS SCREEN
# ============================================================
def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            <div style="text-align:center; padding: 2rem 1rem 1rem 1rem;">
            <div style="font-size: 2.8rem;">🧭</div>
            <h1 style="color:#1E3A5F; margin-bottom:0.2rem;">RTA Vizag Staff Huddle</h1>
            <p style="color:#5A6B7B; font-size:0.95rem; max-width:420px; margin:0 auto;">
            Circulars reference, AI rules assistant & office tools for internal staff use.
            <br><span style="font-size:0.8rem; color:#8A99A8;">Unofficial internal tool — not an official department system.</span>
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        tab_login, tab_request = st.tabs(["🔐 Sign In", "🙋 Request Access"])
        with tab_login:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Sign In", use_container_width=True, type="primary"):
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
            st.info(
                "This is a free tool for internal staff use. Fill this in and the admin will "
                "set up your login manually — no payment, no self-service signup."
            )
            req_name = st.text_input("Full Name")
            req_email = st.text_input("Your Email")
            req_note = st.text_area("Which office / role are you in?", height=80)
            if st.button("Submit Request"):
                if req_name and req_email:
                    create_pending_request(req_name, req_email.strip().lower(), req_note)
                    st.success("Request submitted. The admin will contact you once access is set up.")
                else:
                    st.warning("Please fill in your name and email.")


# ============================================================
# MAIN DASHBOARD
# ============================================================
def show_dashboard():
    user = st.session_state.user
    user_tier = user["tier"]

    with st.sidebar:
        st.markdown(f"### 👤 {user['name']}")
        st.caption(f"**Email:** {user['email']}")
        badge = {"Basic": "🟢", "Pro": "🔵", "Max": "🟣", "Admin": "🔴"}.get(user_tier, "⚪")
        st.markdown(f"**Tier:** {badge} `{user_tier}`")
        st.divider()
        menu = st.radio(
            "Navigation",
            ["🏠 Home", "📢 Circulars & G.O.s", "🤖 AI Rules Assistant", "📝 Templates", "✉️ Tapal Register",
             "📮 Dispatch Labels", "📞 Staff Directory", "⚙️ Admin Panel"],
        )
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            clear_session_token(cookies.get(COOKIE_NAME))
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.messages = []
            st.rerun()

    # --- HOME ---
    if menu == "🏠 Home":
        page_header(f"{greeting()}, {user['name'].split()[0]} 👋", "Here's a quick look at what's available.")
        circ_count = len(fetch_circulars())
        this_month_start = date.today().replace(day=1).isoformat()
        tapal_count = len([r for r in fetch_tapal() if r["tapal_date"] >= this_month_start])
        ai_used_today = get_ai_usage_today(user["email"])
        c1, c2, c3 = st.columns(3)
        c1.metric("Circulars on file", circ_count)
        c2.metric("Tapal entries this month", tapal_count)
        c3.metric("AI queries used today", f"{ai_used_today}/{DAILY_AI_LIMIT}" if ai_used_today is not None else "—")
        st.markdown("#### Quick links")
        q1, q2, q3, q4 = st.columns(4)
        with q1:
            with st.container(border=True):
                st.markdown("**📢 Circulars**")
                st.caption("Search G.O.s, Memos & Circulars")
        with q2:
            with st.container(border=True):
                st.markdown("**🤖 AI Assistant**")
                st.caption("Ask a quick rules question")
        with q3:
            with st.container(border=True):
                st.markdown("**✉️ Tapal**")
                st.caption("Log inward/outward correspondence")
        with q4:
            with st.container(border=True):
                st.markdown("**📮 Dispatch**")
                st.caption("Print-ready address labels")
        st.caption("Use the sidebar to navigate to any of these.")

    # --- CIRCULARS ---
    elif menu == "📢 Circulars & G.O.s":
        page_header("📢 Circulars, G.O.s & Memos", "Search and access departmental documents.")
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input("🔍 Search title or number...")
        with col2:
            category_filter = st.selectbox("Category", ["All", "Finance / HR", "Operations", "Confidential", "Executive"])
        rows = fetch_circulars()
        if category_filter != "All":
            rows = [r for r in rows if r["category"] == category_filter]
        if search_query:
            q = search_query.lower()
            rows = [r for r in rows if q in r["title"].lower() or q in r["ref_id"].lower()]
        st.markdown(f"Showing **{len(rows)}** records:")
        for item in rows:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(f"**{item['ref_id']}: {item['title']}**")
                    st.caption(f"Category: `{item['category']}` | Year: `{item['year']}` | Required Tier: `{item['tier']}`")
                with c2:
                    if has_access(user_tier, item["tier"]):
                        st.markdown(f"[📥 Open]({item['link']})")
                    else:
                        st.warning(f"🔒 {item['tier']}+")
                with c3:
                    st.success("✅") if has_access(user_tier, item["tier"]) else st.error("❌")

    # --- AI ASSISTANT ---
    elif menu == "🤖 AI Rules Assistant":
        page_header("🤖 Rules & Procedure Assistant", "Ask about leave, TA/DA, or service rules.")
        used = get_ai_usage_today(user["email"])
        st.caption(f"Queries used today: {used}/{DAILY_AI_LIMIT}")
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
                # Search the uploaded circulars (the AI brain) FIRST
                sources = search_uploaded_circulars(user_input, limit=4)

                if sources:
                    source_text = ""
                    for i, s in enumerate(sources, 1):
                        source_text += f"\n--- Source {i}: {s['ref_id']} — {s['title']} ---\n{s['content']}\n"
                    sys_context = (
                        "You are an internal staff knowledge assistant for a state transport department office. "
                        "Use the OFFICE CIRCULAR EXCERPTS below as your PRIMARY source.\n"
                        "If the answer is in the excerpts, answer from them and quote the reference number.\n"
                        "If the answer is NOT in the excerpts, say 'Not found in the uploaded circulars' and then "
                        "give brief general guidance.\n"
                        "Never invent G.O. or circular numbers. Be concise. Always tell the user to confirm against "
                        "the current G.O. or the establishment section before relying on this for official use.\n\n"
                        f"OFFICE CIRCULAR EXCERPTS:\n{source_text}"
                    )
                else:
                    sys_context = (
                        "You are an internal staff knowledge assistant for a state transport department office. "
                        "No uploaded circulars matched this question. Start your answer with "
                        "'Not found in the uploaded circulars.' Then answer using general knowledge of Indian state "
                        "civil service rules, Fundamental Rules (FR), Leave Rules, and TA/DA norms. Do not invent "
                        "G.O. numbers. Always tell the user to confirm against the current G.O. or the establishment section."
                    )

                with st.spinner("Checking the rules for you..."):
                    bot_reply, err = ask_ai(user_input, sys_context)
                if err:
                    log_error("ai_assistant", err)
                    st.error(
                        "Couldn't reach the AI engine right now. The admin can check "
                        "Admin Panel → System Health for the exact error."
                    )
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
        for t in rows:
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{t['title']}**")
                    st.caption(f"{t['description']} • Tier: `{t['tier']}`")
                with c2:
                    if has_access(user_tier, t["tier"]):
                        st.markdown(f"[📥 Open]({t['link']})" if t.get("link") else "Available")
                    else:
                        st.warning(f"🔒 {t['tier']}+")

    # --- TAPAL REGISTER ---
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
                if st.form_submit_button("Save Entry"):
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
                        st.success("Entry saved.")
                        fetch_tapal.clear()
        with tab_view:
            rows = fetch_tapal()
            if rows:
                search = st.text_input("🔍 Search from/to, subject, or file ref...")
                if search:
                    q = search.lower()
                    rows = [r for r in rows if q in str(r).lower()]
                if not rows:
                    st.info("No matches. Try a broader term.")
                else:
                    for r in rows:
                        with st.container(border=True):
                            dir_icon = "📥" if r["direction"] == "Inward" else "📤"
                            st.markdown(f"{dir_icon} **{r['subject']}**")
                            st.caption(f"{r['from_to']} · {r['tapal_date']}" + (f" · Ref: {r['file_ref']}" if r.get('file_ref') else ""))
                            if r.get("remarks"):
                                st.caption(f"📝 {r['remarks']}")
            else:
                st.info("No tapal entries yet. Add one from the 'New Entry' tab above.")
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
                inward_count = (df["direction"] == "Inward").sum()
                outward_count = (df["direction"] == "Outward").sum()
                c1, c2, c3 = st.columns(3)
                c1.metric("Inward", int(inward_count))
                c2.metric("Outward", int(outward_count))
                c3.metric("Total", len(df))
                st.dataframe(
                    df[["tapal_date", "direction", "from_to", "subject", "file_ref", "remarks"]],
                    use_container_width=True, hide_index=True,
                )
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    f"📥 Download {start.strftime('%B %Y')} Report (CSV)",
                    data=csv,
                    file_name=f"tapal_report_{start.strftime('%Y_%m')}.csv",
                    mime="text/csv",
                )

    # --- DISPATCH LABELS ---
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
                st.text_area(
                    "Step 2 — Check the extracted address",
                    value=extracted.strip(), height=100, key="ocr_extracted",
                )
                with st.expander("See the processed image OCR actually read"):
                    st.image(img, use_container_width=True)
            except Exception as e:
                st.warning(f"OCR unavailable or failed ({e}). Please type the address manually below.")
        address_text = st.text_area(
            "Step 3 — Confirm final address for the label *",
            value=st.session_state.get("ocr_extracted", ""),
            height=120,
            placeholder="Name\nDesignation / Office\nAddress line 1\nCity - PIN",
        )
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
                        "address_text": address_text.strip(),
                        "copies": int(copies),
                        "generated_by": user["email"],
                        "generated_at": datetime.utcnow().isoformat(),
                    }).execute()
                    st.success(f"Generated {copies} label(s).")
                    st.download_button(
                        "📥 Download Label PDF",
                        data=buf,
                        file_name="dispatch_labels.pdf",
                        mime="application/pdf",
                    )
                except Exception as e:
                    st.error(f"Couldn't generate the PDF: {e}")

    # --- DIRECTORY ---
    elif menu == "📞 Staff Directory":
        page_header("📞 Staff Directory", "Find contact details across the office.")
        df = pd.DataFrame(fetch_directory())
        search_staff = st.text_input("🔍 Search name, division, or role...")
        if search_staff and not df.empty:
            mask = df.apply(lambda r: search_staff.lower() in r.astype(str).str.lower().values, axis=1)
            df = df[mask]
        st.dataframe(df, use_container_width=True, hide_index=True)

    # --- ADMIN PANEL ---
    elif menu == "⚙️ Admin Panel":
        if user_tier != "Admin":
            st.error("⛔ Admin access required.")
        else:
            page_header("⚙️ Admin Panel", "Manage users, circulars, access, and settings.")
            admin_section = st.radio(
                "Section", ["👥 Users", "📢 Circulars", "🔧 Settings", "🩺 System Health"],
                horizontal=True, label_visibility="collapsed",
            )
            st.divider()
            if admin_section == "👥 Users":
                st.subheader("Pending Access Requests")
                res = supabase.table("pending_requests").select("*").eq("status", "pending").execute()
                for r in res.data or []:
                    with st.container(border=True):
                        st.markdown(f"**{r['name']}** — {r['email']}")
                        st.caption(r.get("note", ""))
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            approve_pass = st.text_input("Set password", key=f"pw_{r['id']}", type="password")
                        with c2:
                            approve_tier = st.selectbox("Role", ["Staff", "Admin"], key=f"tier_{r['id']}")
                        with c3:
                            if st.button("Approve", key=f"appr_{r['id']}"):
                                if approve_pass:
                                    supabase.table("users").insert({
                                        "email": r["email"],
                                        "name": r["name"],
                                        "password_hash": hash_password(approve_pass),
                                        "tier": approve_tier,
                                    }).execute()
                                    supabase.table("pending_requests").update({"status": "approved"}).eq("id", r["id"]).execute()
                                    st.success(f"Approved {r['email']}")
                                    st.rerun()
                                else:
                                    st.warning("Set a password first.")
                if not (res.data or []):
                    st.caption("No pending requests.")
                st.divider()
                st.subheader("Create User Directly")
                with st.form("create_user_form", clear_on_submit=True):
                    cu_name = st.text_input("Full Name")
                    cu_email = st.text_input("Email")
                    cu_pass = st.text_input("Password", type="password")
                    cu_role = st.selectbox("Role", ["Staff", "Admin"])
                    if st.form_submit_button("Create Account"):
                        if not (cu_name.strip() and cu_email.strip() and cu_pass):
                            st.warning("Name, email, and password are all required.")
                        else:
                            existing = supabase.table("users").select("id").eq("email", cu_email.strip().lower()).execute()
                            if existing.data:
                                st.warning("A user with this email already exists.")
                            else:
                                supabase.table("users").insert({
                                    "email": cu_email.strip().lower(),
                                    "name": cu_name.strip(),
                                    "password_hash": hash_password(cu_pass),
                                    "tier": cu_role,
                                }).execute()
                                st.success(f"Account created for {cu_email.strip().lower()}")
                                st.rerun()
                st.divider()
                st.subheader("Manage Existing Users")
                users_res = supabase.table("users").select("*").neq("tier", "Admin").execute()
                all_users = users_res.data or []
                if not all_users:
                    st.caption("No non-admin users yet.")
                for u in all_users:
                    is_active = u.get("active", True)
                    with st.container(border=True):
                        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                        with c1:
                            status_dot = "🟢" if is_active else "🔴"
                            st.markdown(f"{status_dot} **{u['name']}** — {u['email']}")
                            st.caption(f"Role: {u['tier']}")
                        with c2:
                            new_pw = st.text_input("New password", key=f"resetpw_{u['id']}", type="password", label_visibility="collapsed", placeholder="New password")
                        with c3:
                            if st.button("Reset Password", key=f"reset_{u['id']}"):
                                if new_pw:
                                    supabase.table("users").update(
                                        {"password_hash": hash_password(new_pw)}
                                    ).eq("id", u["id"]).execute()
                                    st.success(f"Password reset for {u['email']}")
                                else:
                                    st.warning("Type a new password first.")
                        with c4:
                            toggle_label = "Deactivate" if is_active else "Activate"
                            if is_active:
                                if st.button(toggle_label, key=f"toggle_{u['id']}"):
                                    st.session_state[f"confirm_deactivate_{u['id']}"] = True
                                if st.session_state.get(f"confirm_deactivate_{u['id']}"):
                                    with st.container(border=True):
                                        st.warning(f"Revoke access for **{u['name']}**? They'll be logged out immediately.")
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
                st.subheader("Publish New Circular")
                source_choice = st.radio(
                    "Document source", ["Upload PDF", "Paste a link"], horizontal=True, key="doc_source"
                )
                MAX_UPLOAD_MB = 20
                with st.form("add_go_form"):
                    doc_type = st.selectbox(
                        "Document Type",
                        ["G.O.", "Memo", "U.O.", "Circular", "Notification", "Office Order", "Letter"],
                    )
                    ref_number = st.text_input("Reference Number *", placeholder="e.g. Ms.No.102 / 4521/2024")
                    doc_date = st.date_input("Document Date *", value=date.today(), max_value=date.today())
                    title = st.text_input("Title / Subject *")
                    category = st.selectbox("Category", ["Finance / HR", "Operations", "Confidential", "Executive"])
                    tier = st.selectbox("Minimum Tier", ["Basic", "Pro", "Max"])
                    supersedes = st.text_input(
                        "Supersedes / Amends (optional)",
                        placeholder="Reference number of the earlier document this replaces or amends, if any",
                    )
                    uploaded_file = None
                    link = ""
                    if source_choice == "Upload PDF":
                        uploaded_file = st.file_uploader("PDF file (max 20MB)", type=["pdf"])
                    else:
                        link = st.text_input("Link (Drive/PDF URL)")
                    if st.form_submit_button("Publish"):
                        ref_id = f"{doc_type} {ref_number}".strip()
                        errors = []
                        if not ref_number.strip():
                            errors.append("Reference number is required.")
                        if not title.strip():
                            errors.append("Title is required.")
                        if doc_date > date.today():
                            errors.append("Document date cannot be in the future.")
                        dup = supabase.table("circulars").select("id").eq("ref_id", ref_id).execute()
                        if dup.data:
                            errors.append(f"A document with reference '{ref_id}' already exists.")
                        if source_choice == "Upload PDF" and uploaded_file is None:
                            errors.append("Please choose a PDF file.")
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
                                    st.error(f"File is {size_mb:.1f}MB — max allowed is {MAX_UPLOAD_MB}MB.")
                                    final_link = None
                                else:
                                    safe_ref = ref_number.strip().replace(" ", "_").replace("/", "-")
                                    safe_name = f"{doc_type.replace('.', '').replace(' ', '')}_{safe_ref}_{doc_date.isoformat()}.pdf"
                                    with st.spinner("Reading the PDF for the AI (OCR if scanned)..."):
                                        extracted_text, used_ocr = extract_pdf_text(file_bytes)
                                    with st.spinner("Optimising & uploading to cloud storage..."):
                                        try:
                                            optimized = optimize_pdf(file_bytes)
                                            final_link = upload_to_r2(optimized, safe_name)
                                        except Exception as e:
                                            st.error(f"Upload failed: {e}")
                                            log_error("r2_upload", str(e))
                                            final_link = None
                            if final_link:
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
                                n_chunks = 0
                                if source_choice == "Upload PDF" and extracted_text:
                                    n_chunks = index_circular_for_ai(new_id, extracted_text)
                                msg = f"Published: {ref_id}"
                                if source_choice == "Upload PDF":
                                    if n_chunks > 0:
                                        ocr_note = " (used OCR for scanned pages)" if used_ocr else ""
                                        msg += f" — AI can now read it ({n_chunks} text blocks){ocr_note}."
                                    else:
                                        msg += " — but no readable text was found, so the AI can't search this one yet."
                                st.success(msg)
                                fetch_circulars.clear()
                                st.rerun()

            elif admin_section == "🔧 Settings":
                st.subheader("AI Provider")
                st.caption("Change the AI engine or update an API key without touching any code or redeploying.")
                current_provider = get_setting("ai_provider", "gemini")
                provider_choice = st.selectbox(
                    "Active provider", ["gemini", "groq"],
                    index=["gemini", "groq"].index(current_provider) if current_provider in ["gemini", "groq"] else 0,
                )
                if provider_choice == "gemini":
                    gk = st.text_input("Gemini API key", value=get_setting("gemini_api_key"), type="password",
                                        help="From aistudio.google.com — should start with AIzaSy...")
                    gm = st.text_input("Gemini model", value=get_setting("gemini_model", "gemini-1.5-flash"))
                    if st.button("Save Gemini Settings", type="primary"):
                        set_setting("ai_provider", "gemini")
                        set_setting("gemini_api_key", gk.strip())
                        set_setting("gemini_model", gm.strip())
                        st.success("Saved. Takes effect on the next AI question — no restart needed.")
                else:
                    gk = st.text_input("Groq API key", value=get_setting("groq_api_key"), type="password",
                                        help="Free key from console.groq.com")
                    gm = st.text_input(
                        "Groq model ID", value=get_setting("groq_model", "llama-3.1-8b-instant"),
                        help="Examples: llama-3.1-8b-instant, qwen/qwen3-32b — check console.groq.com/docs/models.",
                    )
                    if st.button("Save Groq Settings", type="primary"):
                        set_setting("ai_provider", "groq")
                        set_setting("groq_api_key", gk.strip())
                        set_setting("groq_model", gm.strip())
                        st.success("Saved. Takes effect on the next AI question — no restart needed.")
                st.divider()
                st.subheader("Daily AI Query Limit")
                st.caption(f"Currently fixed at {DAILY_AI_LIMIT} per user per day in code.")

            elif admin_section == "🩺 System Health":
                st.subheader("System Health")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Total Users", len(supabase.table("users").select("id").execute().data or []))
                with c2:
                    st.metric("Total Circulars", len(supabase.table("circulars").select("id").execute().data or []))
                with c3:
                    provider = get_setting("ai_provider", "gemini")
                    key_set = bool(get_setting(f"{provider}_api_key") or st.secrets.get(f"{provider.upper()}_API_KEY", ""))
                    st.metric("AI Engine", provider.title(), "Key set ✅" if key_set else "No key ❌")
                st.divider()
                st.subheader("Recent Errors")
                st.caption("Failures from any part of the app land here automatically.")
                err_res = supabase.table("error_log").select("*").order("occurred_at", desc=True).limit(30).execute()
                errors = err_res.data or []
                if not errors:
                    st.success("No errors logged. Everything's running clean.")
                else:
                    for e in errors:
                        with st.container(border=True):
                            st.markdown(f"**{e['area']}** — {e['occurred_at']}")
                            st.code(e['message'], language=None)
                    if st.button("Clear Error Log"):
                        for e in errors:
                            supabase.table("error_log").delete().eq("id", e["id"]).execute()
                        st.rerun()


# ============================================================
# ROUTER
# ============================================================
try_auto_login()

if not st.session_state.logged_in:
    show_login()
else:
    show_dashboard()
