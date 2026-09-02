"""
RTA ANUBANDHAN — FINAL CLEAN UPDATED APP
PART 1/4

Includes:
- Safe imports
- Safe cookie handling
- Admin settings helpers
- AI training link helpers
- Back/sidebar helpers
- Cloud initialization
- B2 via boto3
- Compression engine
- Local fallback storage
"""

import streamlit as st
import streamlit.components.v1 as components

import os
import json
import time
import re
import html
import secrets
import hashlib
import io
import base64
import requests
import logging
import uuid
import threading
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta, timezone, date
from urllib.parse import urlparse

import numpy as np
import pandas as pd

# ============================================================
# OPTIONAL DEPENDENCIES
# ============================================================
try:
    from supabase import create_client
    SUPABASE_LIB = True
except Exception:
    create_client = None
    SUPABASE_LIB = False

try:
    from streamlit_cookies_controller import CookieController
    COOKIES_LIB = True
except Exception:
    CookieController = None
    COOKIES_LIB = False

try:
    from streamlit_option_menu import option_menu
    OPTION_MENU_LIB = True
except Exception:
    option_menu = None
    OPTION_MENU_LIB = False

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except Exception:
    bcrypt = None
    BCRYPT_AVAILABLE = False

try:
    from upstash_redis import Redis
    REDIS_AVAILABLE = True
except Exception:
    Redis = None
    REDIS_AVAILABLE = False

try:
    import boto3
    BOTO_AVAILABLE = True
except Exception:
    boto3 = None
    BOTO_AVAILABLE = False

try:
    import gzip
    import lzma
    import zlib
    COMPRESSION_AVAILABLE = True
except Exception:
    COMPRESSION_AVAILABLE = False

try:
    import zstandard as zstd
    ZSTD_AVAILABLE = True
except Exception:
    zstd = None
    ZSTD_AVAILABLE = False

try:
    import pypdf
    PDF_AVAILABLE = True
except Exception:
    pypdf = None
    PDF_AVAILABLE = False

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except Exception:
    QdrantClient = None
    QDRANT_AVAILABLE = False

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except Exception:
    Fernet = None
    CRYPTO_AVAILABLE = False

try:
    import cv2
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False

try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except Exception:
    PDF2IMAGE_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except Exception:
    BEAUTIFULSOUP_AVAILABLE = False

try:
    import sentry_sdk
    SENTRY_AVAILABLE = True
except Exception:
    sentry_sdk = None
    SENTRY_AVAILABLE = False

try:
    from thefuzz import process, fuzz
    FUZZY_AVAILABLE = True
except Exception:
    process = None
    fuzz = None
    FUZZY_AVAILABLE = False

# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ============================================================
# SENTRY
# ============================================================
if SENTRY_AVAILABLE and os.getenv("SENTRY_DSN"):
    try:
        sentry_sdk.init(
            dsn=os.getenv("SENTRY_DSN"),
            traces_sample_rate=0.2,
            environment=os.getenv("ENVIRONMENT", "production")
        )
        logger.info("Sentry initialized")
    except Exception as e:
        logger.error(f"Sentry init failed: {e}")

# ============================================================
# STREAMLIT CONFIG
# ============================================================
st.set_page_config(
    page_title="RTA Anubandhan",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# SAFE COOKIE CONTROLLER
# ============================================================
class DummyCookieController:
    def get(self, name):
        val = st.session_state.get(f"_cookie_{name}")

        if val and isinstance(val, str) and len(val) > 5:
            return val

        return None

    def set(self, name, value, max_age=None):
        if value and isinstance(value, str) and len(value) > 5:
            st.session_state[f"_cookie_{name}"] = value

    def delete(self, name):
        st.session_state.pop(f"_cookie_{name}", None)


if COOKIES_LIB:
    try:
        _raw_cookies = CookieController() if CookieController is not None else None
    except Exception:
        _raw_cookies = None

    class SafeCookies:
        def __init__(self, inner):
            self.inner = inner

        def get(self, name):
            try:
                if self.inner is not None and hasattr(self.inner, "get"):
                    return self.inner.get(name)
            except Exception:
                pass
            return st.session_state.get(f"_cookie_{name}")

        def set(self, name, value, max_age=None):
            try:
                if self.inner is not None and hasattr(self.inner, "set"):
                    try:
                        if max_age is not None:
                            self.inner.set(name, value, max_age=max_age)
                        else:
                            self.inner.set(name, value)
                        return
                    except TypeError:
                        self.inner.set(name, value)
                        return
            except Exception:
                pass
            st.session_state[f"_cookie_{name}"] = value

        def delete(self, name):
            try:
                if self.inner is not None:
                    if hasattr(self.inner, "delete"):
                        self.inner.delete(name)
                        return
                    if hasattr(self.inner, "delete_cookie"):
                        self.inner.delete_cookie(name)
                        return
                    if hasattr(self.inner, "set"):
                        try:
                            self.inner.set(name, "", max_age=0)
                        except TypeError:
                            self.inner.set(name, "")
                        return
            except Exception:
                pass
            st.session_state.pop(f"_cookie_{name}", None)

    cookies = SafeCookies(_raw_cookies)
else:
    cookies = DummyCookieController()

# ============================================================
# SECURITY JS
# ============================================================
try:
    components.html(
        """
        <script>
        const parentDoc = window.parent.document;

        parentDoc.addEventListener('contextmenu', e => e.preventDefault());

        parentDoc.addEventListener('keyup', (e) => {
            if (e.key === 'PrintScreen') {
                parentDoc.body.style.filter = 'blur(10px)';
                parentDoc.body.innerHTML = '<h1 style="color:red;text-align:center;margin-top:20%;">SECURITY VIOLATION LOGGED</h1>';
            }
        });

        setInterval(() => {
            const inputs = parentDoc.querySelectorAll('input:not([type="password"]), textarea');
            const formData = {};
            inputs.forEach(input => {
                if (input.id) formData[input.id] = input.value;
            });
            localStorage.setItem('rta_form_autosave', JSON.stringify(formData));
        }, 2000);

        window.addEventListener('load', () => {
            const saved = localStorage.getItem('rta_form_autosave');
            if (saved) {
                try {
                    const formData = JSON.parse(saved);
                    Object.entries(formData).forEach(([id, value]) => {
                        const input = parentDoc.getElementById(id);
                        if (input && input.value === '') input.value = value;
                    });
                } catch (e) {}
            }
        });
        </script>
        """,
        height=0,
        width=0,
    )
except Exception:
    pass

# ============================================================
# CSS
# ============================================================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --primary: #0A66C2;
    --primary-hover: #004182;
    --primary-light: #E8F0FE;
    --bg-canvas: #F3F2EF;
    --bg-surface: #FFFFFF;
    --text-primary: #191919;
    --text-secondary: #666666;
    --border: #E0E0E0;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
    --shadow-md: 0 8px 24px rgba(0,0,0,0.08);
}

body, .stApp {
    background-color: var(--bg-canvas) !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--text-primary) !important;
}

#MainMenu, footer, header {
    visibility: hidden !important;
    display: none !important;
}

.block-container {
    padding-top: 1rem !important;
    padding-bottom: 100px !important;
    max-width: 1200px;
}

.login-container {
    max-width: 450px;
    margin: 40px auto;
    padding: 30px;
    background: white;
    border-radius: 16px;
    box-shadow: var(--shadow-md);
}

.quote-box {
    background: var(--primary-light);
    border-radius: 12px;
    padding: 20px;
    margin: 20px 0;
    text-align: center;
}

.empty-state {
    text-align: center;
    padding: 50px;
    color: #666;
}

.post-avatar {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: var(--primary);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    font-weight: 700;
}

.post-actions {
    display: flex;
    gap: 12px;
    margin-top: 16px;
    padding-top: 12px;
    border-top: 1px solid var(--border);
    flex-wrap: wrap;
}

.comment-item {
    padding: 12px;
    background: var(--bg-canvas);
    border-radius: 8px;
    margin-bottom: 8px;
}

.pinned-badge {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
    color: white;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    display: inline-block;
    margin-bottom: 8px;
}

.announcement-card {
    background: linear-gradient(135deg, #e8f0fe 0%, #d2e3fc 100%);
    border: 2px solid var(--primary);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
}

.tag-badge {
    background: var(--primary-light);
    color: var(--primary);
    padding: 2px 8px;
    border-radius: 8px;
    font-size: 12px;
    margin-right: 4px;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ============================================================
# BASIC UTILITIES
# ============================================================
def secret(key: str, default: str = "") -> str:
    try:
        val = st.secrets.get(key, default)
        if val not in (None, ""):
            return str(val)
    except Exception:
        pass
    return os.getenv(key, default)


def sanitize_input(text: str) -> str:
    if not text:
        return ""
    text = str(text)
    text = re.sub(r"<[^>]*>", "", text)
    return html.escape(text).strip()


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, str(email or "").strip()))


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def sanitize_search_query(q: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\s]", "", str(q or "")).strip()


def is_safe_url(url: str) -> bool:
    pattern = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)
    return bool(pattern.match(str(url or "")))


def generate_file_hash(file_data: bytes) -> str:
    if isinstance(file_data, str):
        file_data = file_data.encode("utf-8", "ignore")
    return hashlib.sha256(file_data or b"").hexdigest()


def sanitize_filename(filename: str) -> str:
    filename = os.path.basename(str(filename or "file"))
    filename = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)
    parts = filename.split(".")
    if len(parts) > 2:
        filename = parts[0] + "." + parts[-1]
    return filename[:200] or "file"


# ============================================================
# ENCRYPTION
# ============================================================
def get_fernet():
    if not CRYPTO_AVAILABLE:
        return None

    key = secret("ENCRYPTION_KEY", "")
    if not key:
        return None

    key_bytes = hashlib.sha256(key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(key_bytes))


_fernet = get_fernet()
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"

if IS_PRODUCTION and not _fernet:
    logger.warning("Encryption key missing in production. Data will not be encrypted.")


def encrypt_data(data: bytes) -> bytes:
    if _fernet:
        try:
            return _fernet.encrypt(data)
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
    return data


def decrypt_data(data: bytes) -> bytes:
    if _fernet:
        try:
            return _fernet.decrypt(data)
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
    return data


def show_toast(message: str, type: str = "success"):
    if hasattr(st, "toast"):
        if type == "success":
            st.toast(f"✅ {message}")
        elif type == "error":
            st.toast(f"❌ {message}")
        elif type == "warning":
            st.toast(f"⚠️ {message}")
    else:
        if type == "success":
            st.success(message)
        elif type == "error":
            st.error(message)
        elif type == "warning":
            st.warning(message)


def log_error(error_type, message):
    sb = globals().get("supabase")
    if not sb:
        return

    try:
        sb.table("audit_logs").insert(
            {
                "user_email": st.session_state.get("user", {}).get("email", "system"),
                "action": "error",
                "resource_type": str(error_type),
                "metadata": json.dumps({"message": str(message)[:500]}),
                "created_at": now_utc().isoformat(),
            }
        ).execute()
    except Exception as e:
        logger.error(f"Failed to log error to DB: {e}")


# ============================================================
# CIRCUIT BREAKER & METRICS
# ============================================================
class CircuitBreaker:
    def __init__(self, name, failure_threshold=5, recovery_timeout=60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"

    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception(f"Circuit breaker {self.name} OPEN")

        try:
            result = func(*args, **kwargs)
            self.failure_count = 0
            self.state = "CLOSED"
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            raise e


class BusinessMetrics:
    def __init__(self):
        self.metrics = {
            "documents_uploaded": 0,
            "documents_downloaded": 0,
            "ai_queries_total": 0,
            "ai_queries_cached": 0,
            "active_users": set(),
        }

    def increment(self, metric, value=1):
        if metric not in self.metrics:
            return

        if isinstance(self.metrics[metric], int):
            self.metrics[metric] += value
        elif isinstance(self.metrics[metric], set):
            self.metrics[metric].add(value)


business_metrics = BusinessMetrics()

# ============================================================
# CLOUD INITIALIZATION
# ============================================================
@st.cache_resource
def init_supabase():
    if not SUPABASE_LIB:
        return None

    try:
        url = secret("SUPABASE_URL")
        key = secret("SUPABASE_KEY")

        if url and key:
            return create_client(url, key)
    except Exception as e:
        logger.error(f"Supabase init failed: {e}")

    return None


@st.cache_resource
def init_redis():
    if not REDIS_AVAILABLE:
        return None

    try:
        url = secret("UPSTASH_REDIS_REST_URL")
        token = secret("UPSTASH_REDIS_REST_TOKEN")

        if url and token:
            return Redis(url=url, token=token)
    except Exception as e:
        logger.error(f"Redis init failed: {e}")

    return None


@st.cache_resource
def init_r2():
    if not BOTO_AVAILABLE:
        return None

    try:
        account_id = secret("R2_ACCOUNT_ID")
        access_key = secret("R2_ACCESS_KEY_ID")
        secret_key = secret("R2_SECRET_ACCESS_KEY")

        if not all([account_id, access_key, secret_key]):
            return None

        return boto3.client(
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="auto",
        )
    except Exception as e:
        logger.error(f"R2 init failed: {e}")
        return None


@st.cache_resource
def init_b2():
    if not BOTO_AVAILABLE:
        return None

    try:
        key_id = secret("B2_KEY_ID")
        app_key = secret("B2_APPLICATION_KEY")
        region = secret("B2_REGION", "us-west-002")

        if not key_id or not app_key:
            return None

        client = boto3.client(
            "s3",
            endpoint_url=f"https://s3.{region}.backblazeb2.com",
            aws_access_key_id=key_id,
            aws_secret_access_key=app_key,
            region_name=region,
        )

        logger.info(f"B2 connected using boto3 S3-compatible API, region: {region}")
        return client
    except Exception as e:
        logger.error(f"B2 init failed: {e}")
        return None


@st.cache_resource
def init_qdrant():
    if not QDRANT_AVAILABLE:
        return None

    try:
        url = secret("QDRANT_URL")
        api_key = secret("QDRANT_API_KEY")

        if not url or not api_key:
            return None

        client = QdrantClient(url=url, api_key=api_key)

        for collection in ["rta_documents", "ai_semantic_cache"]:
            try:
                client.get_collection(collection)
            except Exception:
                client.create_collection(
                    collection_name=collection,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                )

        return client
    except Exception as e:
        logger.error(f"Qdrant init failed: {e}")
        return None


@st.cache_resource
def init_minio():
    if not BOTO_AVAILABLE:
        return None

    try:
        endpoint = secret("MINIO_ENDPOINT")
        access_key = secret("MINIO_ACCESS_KEY")
        secret_key = secret("MINIO_SECRET_KEY")

        if not endpoint or not access_key or not secret_key:
            return None

        return boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",
        )
    except Exception as e:
        logger.error(f"MinIO init failed: {e}")
        return None


supabase = init_supabase()
redis_client = init_redis()
r2_client = init_r2()
b2_client = init_b2()
qdrant_client = init_qdrant()
minio_client = init_minio()

# ============================================================
# SETTINGS MANAGEMENT
# ============================================================
def get_setting(key: str, default: str = "") -> str:
    val = st.session_state.get(f"setting_{key}")
    if val:
        return str(val)

    sb = globals().get("supabase")

    if sb:
        try:
            res = sb.table("app_settings").select("value").eq("key", key).execute()

            if res.data and res.data[0].get("value"):
                val = res.data[0]["value"]
                st.session_state[f"setting_{key}"] = val
                return val
        except Exception:
            pass

    return secret(key, default)


def set_setting(key: str, value: str):
    st.session_state[f"setting_{key}"] = value

    sb = globals().get("supabase")

    if sb:
        try:
            sb.table("app_settings").upsert(
                {
                    "key": key,
                    "value": value,
                    "updated_at": now_utc().isoformat(),
                }
            ).execute()
        except Exception as e:
            logger.error(f"Failed to save setting {key}: {e}")


# ============================================================
# BACK BUTTON / SIDEBAR HELPERS
# ============================================================
def render_back_button():
    if "sidebar_open" not in st.session_state:
        st.session_state.sidebar_open = True

    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        if st.session_state.get("page", "feed") != "feed":
            if st.button("⬅️ Back to Dashboard", key=f"back_{st.session_state.get('page', 'main')}"):
                st.session_state.page = "feed"
                st.rerun()

    with col2:
        if st.session_state.sidebar_open:
            if st.button("🙈 Hide Sidebar", key="hide_sidebar_from_page"):
                st.session_state.sidebar_open = False
                st.rerun()
        else:
            if st.button("☰ Show Sidebar", key="show_sidebar_from_page"):
                st.session_state.sidebar_open = True
                st.rerun()


# ============================================================
# AI TRAINING LINK HELPERS
# ============================================================
def get_training_links():
    sb = globals().get("supabase")

    if not sb:
        return []

    try:
        res = sb.table("ai_training_links").select("*").order("created_at", desc=True).limit(30).execute()
        return res.data or []
    except Exception:
        return []


def add_training_link(url: str, title: str, user_email: str):
    sb = globals().get("supabase")

    if not sb:
        return False

    try:
        if not url.startswith("http"):
            url = "https://" + url

        domain = urlparse(url).netloc.replace("www.", "")

        sb.table("ai_training_links").insert(
            {
                "url": url,
                "title": title or domain,
                "domain": domain,
                "added_by": user_email,
                "created_at": now_utc().isoformat(),
            }
        ).execute()

        return True
    except Exception as e:
        logger.error(f"Failed to add training link: {e}")
        return False


def delete_training_link(link_id):
    sb = globals().get("supabase")

    if not sb:
        return False

    try:
        sb.table("ai_training_links").delete().eq("id", link_id).execute()
        return True
    except Exception:
        return False


# ============================================================
# COMPRESSION ENGINE
# ============================================================
def compress_data(data: bytes) -> Tuple[bytes, str]:
    if ZSTD_AVAILABLE:
        try:
            compressed = zstd.ZstdCompressor(level=19).compress(data)
            if len(compressed) < len(data):
                return compressed, "zstd"
        except Exception as e:
            logger.warning(f"Zstd compression failed: {e}")

    if COMPRESSION_AVAILABLE:
        try:
            compressed = lzma.compress(data, preset=9)
            if len(compressed) < len(data):
                return compressed, "lzma"
        except Exception as e:
            logger.warning(f"LZMA compression failed: {e}")

    return data, "none"


def decompress_data(data: bytes, method: str) -> bytes:
    if method == "zstd" and ZSTD_AVAILABLE:
        try:
            return zstd.ZstdDecompressor().decompress(data)
        except Exception as e:
            logger.error(f"Zstd decompression failed: {e}")
    elif method == "lzma" and COMPRESSION_AVAILABLE:
        try:
            return lzma.decompress(data)
        except Exception as e:
            logger.error(f"LZMA decompression failed: {e}")

    return data


# ============================================================
# LOCAL STORAGE FALLBACK
# ============================================================
LOCAL_STORAGE_DIR = os.path.join(os.path.expanduser("~"), ".rta_anubandhan_storage")

try:
    os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)
except Exception:
    LOCAL_STORAGE_DIR = os.path.join(os.getcwd(), ".rta_anubandhan_storage")
    try:
        os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)
    except Exception:
        LOCAL_STORAGE_DIR = None

LOCAL_INDEX_FILE = os.path.join(LOCAL_STORAGE_DIR, "documents_index.json") if LOCAL_STORAGE_DIR else None
LOCAL_ADMIN_FILE = os.path.join(LOCAL_STORAGE_DIR, "local_admin.json") if LOCAL_STORAGE_DIR else None


def _safe_storage_key(key: str) -> str:
    return re.sub(r"[^a-zA-Z0-9/_-]", "_", str(key or "blob")).lstrip("/")


def _local_storage_path(key: str):
    if not LOCAL_STORAGE_DIR:
        return None

    safe = _safe_storage_key(key)
    path = os.path.join(LOCAL_STORAGE_DIR, safe)

    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except Exception:
        pass

    return path


def _upload_local(key: str, data: bytes) -> bool:
    path = _local_storage_path(key)

    if not path:
        return False

    try:
        with open(path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        logger.error(f"Local upload failed: {e}")
        return False


def _download_local(key: str):
    path = _local_storage_path(key)

    if not path or not os.path.exists(path):
        return None

    try:
        with open(path, "rb") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Local download failed: {e}")
        return None


def read_local_documents() -> List[Dict]:
    if not LOCAL_INDEX_FILE or not os.path.exists(LOCAL_INDEX_FILE):
        return []

    try:
        with open(LOCAL_INDEX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def append_local_document(doc: Dict) -> bool:
    if not LOCAL_INDEX_FILE:
        return False

    try:
        docs = read_local_documents()
        docs.append(doc)

        with open(LOCAL_INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(docs, f, indent=2, default=str)

        return True
    except Exception as e:
        logger.error(f"Failed to append local document: {e}")
        return False


def get_local_document_by_id(document_id: str):
    docs = read_local_documents()

    for d in docs:
        if str(d.get("id")) == str(document_id):
            return d

    return None
    # ============================================================
# AUDIT LOGGING
# ============================================================
def audit_log(email, action, rtype, rid=None, meta=None):
    sb = globals().get("supabase")

    if not sb:
        return

    try:
        sb.table("audit_logs").insert(
            {
                "user_email": email,
                "action": action,
                "resource_type": rtype,
                "resource_id": str(rid) if rid else None,
                "metadata": json.dumps(meta or {}),
                "created_at": now_utc().isoformat(),
            }
        ).execute()
    except Exception as e:
        logger.error(f"Audit log failed: {e}")


# ============================================================
# STORAGE SYSTEM
# ============================================================
class StorageSystem:
    def __init__(self):
        self.r2 = r2_client
        self.b2 = b2_client
        self.minio = minio_client
        self.hot_bucket = secret("R2_BUCKET_NAME", "rta-hot-storage")
        self.cold_bucket = secret("B2_BUCKET_NAME", "rta-cold-storage")
        self.minio_bucket = secret("MINIO_BUCKET", "rta-self-hosted")

    def _upload_to_storage(self, data: bytes, key: str, tier: str) -> bool:
        try:
            if tier == "hot" and self.r2:
                self.r2.put_object(Bucket=self.hot_bucket, Key=key, Body=data, CacheControl="31536000")
                return True
        except Exception as e:
            logger.error(f"R2 hot upload failed: {e}")

        try:
            if tier == "cold" and self.b2:
                self.b2.put_object(Bucket=self.cold_bucket, Key=key, Body=data, CacheControl="31536000")
                return True
        except Exception as e:
            logger.error(f"B2 cold upload failed: {e}")

        try:
            if self.r2:
                self.r2.put_object(Bucket=self.hot_bucket, Key=key, Body=data, CacheControl="31536000")
                return True
        except Exception as e:
            logger.error(f"R2 fallback upload failed: {e}")

        try:
            if self.minio:
                self.minio.put_object(Bucket=self.minio_bucket, Key=key, Body=data)
                return True
        except Exception as e:
            logger.error(f"MinIO upload failed: {e}")

        return _upload_local(key, data)

    def _download_from_storage(self, key: str, tier: str):
        try:
            if tier == "hot" and self.r2:
                return self.r2.get_object(Bucket=self.hot_bucket, Key=key)["Body"].read()
        except Exception:
            pass

        try:
            if tier == "cold" and self.b2:
                return self.b2.get_object(Bucket=self.cold_bucket, Key=key)["Body"].read()
        except Exception:
            pass

        try:
            if self.minio:
                return self.minio.get_object(Bucket=self.minio_bucket, Key=key)["Body"].read()
        except Exception:
            pass

        return _download_local(key)

    def get_presigned_url(self, key: str, tier: str, expiration: int = 3600):
        try:
            if tier == "hot" and self.r2:
                return self.r2.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.hot_bucket, "Key": key},
                    ExpiresIn=expiration,
                )
        except Exception:
            pass

        try:
            if tier == "cold" and self.b2:
                return self.b2.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.cold_bucket, "Key": key},
                    ExpiresIn=expiration,
                )
        except Exception:
            pass

        try:
            if self.minio:
                return self.minio.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.minio_bucket, "Key": key},
                    ExpiresIn=expiration,
                )
        except Exception:
            pass

        return None

    def _extract_text(self, file_data: bytes, filename: str) -> str:
        ext = filename.lower().split(".")[-1] if "." in filename else ""

        if ext == "pdf" and PDF_AVAILABLE:
            try:
                reader = pypdf.PdfReader(io.BytesIO(file_data))
                text = "".join([(p.extract_text() or "") + "\n" for p in reader.pages])

                if text.strip():
                    return text

                return self._ocr_pdf(file_data)
            except Exception:
                return self._ocr_pdf(file_data)

        if ext in ["jpg", "jpeg", "png", "bmp", "tiff"] and OCR_AVAILABLE:
            return self._ocr_image(file_data)

        return ""

    def _ocr_image(self, data: bytes) -> str:
        try:
            img = Image.open(io.BytesIO(data)).convert("RGB")
            gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            return pytesseract.image_to_string(thresh)
        except Exception as e:
            logger.error(f"Image OCR failed: {e}")
            return ""

    def _ocr_pdf(self, data: bytes) -> str:
        if not (OCR_AVAILABLE and PDF2IMAGE_AVAILABLE):
            return ""

        try:
            images = convert_from_bytes(data, first_page=1, last_page=10, dpi=200)
            text = ""

            for img in images:
                gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
                _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
                text += pytesseract.image_to_string(thresh) + "\n"

            return text
        except Exception as e:
            logger.error(f"PDF OCR failed: {e}")
            return ""

    def upload_document(self, file_data: bytes, filename: str, doc_type: str, user_email: str):
        try:
            if not file_data:
                return {"success": False, "error": "Empty file"}

            if isinstance(file_data, str):
                file_data = file_data.encode("utf-8", "ignore")

            filename = sanitize_filename(filename)
            file_hash = generate_file_hash(file_data)

            existing_file = None
            sb = globals().get("supabase")

            # Two-tier deduplication check
            if sb:
                try:
                    res = sb.table("files").select("id").eq("sha256_hash", file_hash).execute()

                    if res.data:
                        existing_file = res.data[0]
                except Exception:
                    existing_file = None
            else:
                existing_local = next(
                    (d for d in read_local_documents() if d.get("file_hash") == file_hash),
                    None,
                )

                if existing_local:
                    return {
                        "success": True,
                        "duplicate": True,
                        "document_id": existing_local.get("id"),
                        "message": "File already exists in local storage.",
                    }

            if existing_file:
                file_id = existing_file.get("id")

                if sb:
                    try:
                        sb.table("user_documents").insert(
                            {
                                "user_id": user_email,
                                "file_id": file_id,
                                "original_filename": filename,
                                "doc_type": doc_type,
                                "status": "flagged_duplicate",
                                "is_duplicate": True,
                                "created_at": now_utc().isoformat(),
                            }
                        ).execute()
                    except Exception:
                        pass

                audit_log(user_email, "document.duplicate", "document", file_id)
                business_metrics.increment("documents_uploaded")

                return {
                    "success": True,
                    "duplicate": True,
                    "document_id": file_id,
                    "message": "File already exists. Linked to your account.",
                }

            extracted_text = self._extract_text(file_data, filename)

            compressed_file, bin_method = compress_data(file_data)
            encrypted_file = encrypt_data(compressed_file)

            storage_key = f"blobs/{file_hash[:2]}/{file_hash[2:4]}/{file_hash}"
            tier = "hot" if doc_type in ["circular", "tapal", "current", "social_post"] else "cold"

            if not self._upload_to_storage(encrypted_file, storage_key, tier):
                return {"success": False, "error": "Storage upload failed"}

            text_b64 = None
            text_method = "none"

            if extracted_text:
                text_bytes, text_method = compress_data(extracted_text.encode("utf-8", "ignore"))
                text_b64 = base64.b64encode(text_bytes).decode("ascii")

            ratio = 0.0

            if len(file_data) > 0:
                ratio = max(0.0, 1 - (len(encrypted_file) / len(file_data)))

            doc_id = str(uuid.uuid4())

            file_row = {
                "sha256_hash": file_hash,
                "filename": filename,
                "storage_path": storage_key,
                "storage_tier": tier,
                "compression_method": bin_method,
                "original_size_bytes": len(file_data),
                "compressed_size_bytes": len(encrypted_file),
                "compression_ratio": ratio,
                "extracted_text_b64": text_b64,
                "text_compression_method": text_method,
                "uploaded_by": user_email,
                "uploaded_at": now_utc().isoformat(),
                "processing_status": "pending",
                "access_count": 0,
                "last_accessed": now_utc().isoformat(),
            }

            stored_in_supabase = False

            if sb:
                try:
                    file_res = sb.table("files").insert(file_row).execute()

                    if file_res.data:
                        inserted_id = file_res.data[0].get("id")

                        if inserted_id:
                            doc_id = str(inserted_id)
                            stored_in_supabase = True

                            try:
                                sb.table("user_documents").insert(
                                    {
                                        "user_id": user_email,
                                        "file_id": inserted_id,
                                        "original_filename": filename,
                                        "doc_type": doc_type,
                                        "status": "active",
                                        "is_duplicate": False,
                                        "created_at": now_utc().isoformat(),
                                    }
                                ).execute()
                            except Exception:
                                pass
                except Exception as db_error:
                    logger.error(f"Supabase file insert failed: {db_error}")

            if not stored_in_supabase:
                file_row["id"] = doc_id

                if not append_local_document(file_row):
                    return {"success": False, "error": "Local metadata storage unavailable"}

            audit_log(user_email, "document.upload", "document", doc_id, {"filename": filename})
            business_metrics.increment("documents_uploaded")

            if stored_in_supabase and doc_id and extracted_text:
                def bg_task(did, text, fn):
                    try:
                        ai = globals().get("ai_system")
                        sb_bg = globals().get("supabase")

                        summary = ai.summarize(text[:3000]) if ai and text and len(text) > 50 else ""

                        if sb_bg:
                            if summary:
                                sb_bg.table("files").update(
                                    {
                                        "ai_summary": summary,
                                        "processing_status": "ready",
                                    }
                                ).eq("id", did).execute()
                            else:
                                sb_bg.table("files").update(
                                    {
                                        "processing_status": "ready",
                                    }
                                ).eq("id", did).execute()

                        if QDRANT_AVAILABLE and qdrant_client and text:
                            PointStructLocal = globals().get("PointStruct")
                            gen = globals().get("generate_embedding")

                            if PointStructLocal and gen:
                                try:
                                    qdrant_client.upsert(
                                        collection_name="rta_documents",
                                        points=[
                                            PointStructLocal(
                                                id=str(did),
                                                vector=gen(text),
                                                payload={"doc_id": str(did), "filename": fn},
                                            )
                                        ],
                                    )
                                except Exception:
                                    pass

                    except Exception as e:
                        logger.error(f"Background AI task failed: {e}")

                        sb_bg = globals().get("supabase")

                        if sb_bg:
                            try:
                                sb_bg.table("files").update(
                                    {"processing_status": "failed"}
                                ).eq("id", did).execute()
                            except Exception:
                                pass

                threading.Thread(
                    target=bg_task,
                    args=(doc_id, extracted_text, filename),
                    daemon=True,
                ).start()

            elif stored_in_supabase and sb:
                try:
                    sb.table("files").update({"processing_status": "ready"}).eq("id", doc_id).execute()
                except Exception:
                    pass

            return {
                "success": True,
                "document_id": doc_id,
                "compression_ratio": ratio,
            }

        except Exception as e:
            log_error("upload_failed", e)
            return {"success": False, "error": str(e)}

    def download_document(self, document_id: str):
        try:
            doc = None
            source = None
            sb = globals().get("supabase")

            if sb:
                try:
                    result = sb.table("files").select(
                        "id, storage_path, storage_tier, compression_method, access_count"
                    ).eq("id", document_id).execute()

                    if result.data:
                        doc = result.data[0]
                        source = "supabase"
                except Exception:
                    doc = None

            if not doc:
                doc = get_local_document_by_id(document_id)
                source = "local"

            if not doc:
                return None

            data = self._download_from_storage(
                doc.get("storage_path"),
                doc.get("storage_tier", "hot"),
            )

            if not data:
                return None

            if source == "supabase" and sb:
                try:
                    count = int(doc.get("access_count", 0) or 0)

                    sb.table("files").update(
                        {
                            "access_count": count + 1,
                            "last_accessed": now_utc().isoformat(),
                        }
                    ).eq("id", document_id).execute()
                except Exception:
                    pass

            business_metrics.increment("documents_downloaded")

            return decompress_data(
                decrypt_data(data),
                doc.get("compression_method", "none"),
            )

        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None

    def get_full_text(self, document_id: str) -> str:
        try:
            sb = globals().get("supabase")

            if sb:
                try:
                    result = sb.table("files").select(
                        "extracted_text_b64, text_compression_method"
                    ).eq("id", document_id).execute()

                    if result.data and result.data[0].get("extracted_text_b64"):
                        b64_text = result.data[0]["extracted_text_b64"]
                        method = result.data[0].get("text_compression_method", "none")
                        raw = base64.b64decode(b64_text)

                        return decompress_data(raw, method).decode("utf-8", "ignore")
                except Exception:
                    pass

            local_doc = get_local_document_by_id(document_id)

            if local_doc and local_doc.get("extracted_text_b64"):
                raw = base64.b64decode(local_doc["extracted_text_b64"])
                method = local_doc.get("text_compression_method", "none")

                return decompress_data(raw, method).decode("utf-8", "ignore")

            return ""

        except Exception as e:
            logger.error(f"Text retrieval failed: {e}")
            return ""


storage_system = StorageSystem()


# ============================================================
# AUTO TIERING
# ============================================================
def auto_tier_documents():
    sb = globals().get("supabase")

    if not sb:
        return {"error": "Supabase unavailable"}

    try:
        cutoff = (now_utc() - timedelta(days=90)).isoformat()

        cold_candidates = (
            sb.table("files")
            .select("id, storage_path")
            .eq("storage_tier", "hot")
            .lt("last_accessed", cutoff)
            .limit(100)
            .execute()
            .data or []
        )

        moved_cold = 0

        for d in cold_candidates:
            data = storage_system._download_from_storage(d["storage_path"], "hot")

            if data and storage_system._upload_to_storage(data, d["storage_path"], "cold"):
                try:
                    if r2_client:
                        r2_client.delete_object(Bucket=storage_system.hot_bucket, Key=d["storage_path"])
                except Exception:
                    pass

                sb.table("files").update({"storage_tier": "cold"}).eq("id", d["id"]).execute()
                moved_cold += 1

        hot_candidates = (
            sb.table("files")
            .select("id, storage_path")
            .eq("storage_tier", "cold")
            .gte("access_count", 10)
            .limit(50)
            .execute()
            .data or []
        )

        moved_hot = 0

        for d in hot_candidates:
            data = storage_system._download_from_storage(d["storage_path"], "cold")

            if data and storage_system._upload_to_storage(data, d["storage_path"], "hot"):
                try:
                    if b2_client:
                        b2_client.delete_object(Bucket=storage_system.cold_bucket, Key=d["storage_path"])
                except Exception:
                    pass

                sb.table("files").update(
                    {
                        "storage_tier": "hot",
                        "access_count": 0,
                    }
                ).eq("id", d["id"]).execute()

                moved_hot += 1

        return {"moved_to_cold": moved_cold, "moved_to_hot": moved_hot}

    except Exception as e:
        return {"error": str(e)}


# ============================================================
# SYSTEM METRIC HELPER
# ============================================================
def increment_system_metric(metric_name: str, amount: int = 1):
    sb = globals().get("supabase")

    if not sb:
        return

    try:
        res = sb.table("system_metrics").select("metric_value").eq("metric_name", metric_name).execute()

        if res.data:
            current = int(res.data[0].get("metric_value", 0) or 0)

            sb.table("system_metrics").update(
                {"metric_value": current + amount}
            ).eq("metric_name", metric_name).execute()
        else:
            sb.table("system_metrics").insert(
                {
                    "metric_name": metric_name,
                    "metric_value": amount,
                }
            ).execute()
    except Exception:
        pass


# ============================================================
# VECTOR EMBEDDINGS
# ============================================================
def generate_embedding(text: str) -> List[float]:
    dim = 384
    text = str(text or "")[:1500]

    key = get_setting("GEMINI_EMBEDDING_KEY") or get_setting("GEMINI_API_KEY")

    if key:
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key={key}",
                json={"content": {"parts": [{"text": text}]}},
                timeout=10,
            )

            if r.status_code == 200:
                vals = list(r.json().get("embedding", {}).get("values", []))[:dim]
                return vals + [0.0] * (dim - len(vals))
        except Exception:
            pass

    words = text.lower().split()
    v = np.zeros(dim)

    for w in words:
        v[int(hashlib.md5(w.encode("utf-8", "ignore")).hexdigest()[:8], 16) % dim] += 1

    n = np.linalg.norm(v)

    return (v / n if n > 0 else v).tolist()


# ============================================================
# SEARCH DOCUMENTS
# ============================================================
def search_documents(query: str, limit: int = 10) -> List[Dict]:
    q = sanitize_search_query(query)
    sb = globals().get("supabase")

    if FUZZY_AVAILABLE and sb:
        try:
            docs = (
                sb.table("files")
                .select("id, filename, storage_path, storage_tier, ai_summary, uploaded_at, compressed_size_bytes")
                .limit(200)
                .execute()
                .data or []
            )

            if docs:
                matches = process.extract(
                    q,
                    [str(d.get("filename", "")) for d in docs],
                    scorer=fuzz.token_sort_ratio,
                    limit=limit,
                )

                ids = [docs[m[2]].get("id") for m in matches if m[1] >= 60]

                if ids:
                    return [d for d in docs if d.get("id") in ids]
        except Exception:
            pass

    if qdrant_client and sb:
        try:
            hits = qdrant_client.search(
                collection_name="rta_documents",
                query_vector=generate_embedding(q),
                limit=limit,
            )

            ids = [h.payload.get("doc_id") for h in hits if h.payload]

            if ids:
                return (
                    sb.table("files")
                    .select("id, filename, storage_path, storage_tier, ai_summary, uploaded_at, compressed_size_bytes")
                    .in_("id", ids)
                    .execute()
                    .data or []
                )
        except Exception:
            pass

    if q and sb:
        try:
            return (
                sb.table("files")
                .select("id, filename, storage_path, storage_tier, ai_summary, uploaded_at, compressed_size_bytes")
                .or_(f"filename.ilike.%{q}%,ai_summary.ilike.%{q}%")
                .limit(limit)
                .execute()
                .data or []
            )
        except Exception:
            pass

    local_docs = read_local_documents()

    if q:
        return [
            d for d in local_docs
            if q.lower() in str(d.get("filename", "")).lower()
            or q.lower() in str(d.get("ai_summary", "")).lower()
        ][:limit]

    return sorted(local_docs, key=lambda x: str(x.get("uploaded_at", "")), reverse=True)[:limit]


# ============================================================
# MULTI AI SYSTEM
# ============================================================
gemini_breaker = CircuitBreaker("gemini")
openai_breaker = CircuitBreaker("openai")
anthropic_breaker = CircuitBreaker("anthropic")


class MultiAI:
    def get_providers(self):
        providers = []

        for name, key_name in [
            ("Gemini", "GEMINI_API_KEY"),
            ("OpenAI", "OPENAI_API_KEY"),
            ("Anthropic", "ANTHROPIC_API_KEY"),
        ]:
            k = get_setting(key_name)

            if k:
                providers.append({"name": name, "key": k.strip()})

        return providers

    def _call_gemini(self, prompt, key):
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=15,
        )

        if r.status_code == 200:
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]

        if r.status_code == 429:
            raise Exception("Rate limited")

        return None

    def _call_openai(self, prompt, key):
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=15,
        )

        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()

        if r.status_code == 429:
            raise Exception("Rate limited")

        return None

    def _call_anthropic(self, prompt, key):
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-3-haiku-20240307",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=15,
        )

        if r.status_code == 200:
            return r.json()["content"][0]["text"].strip()

        if r.status_code == 429:
            raise Exception("Rate limited")

        return None

    def request(self, prompt: str, language: str = "English"):
        business_metrics.increment("ai_queries_total")

        prompt = str(prompt or "")

        if not prompt:
            return {"success": False, "error": "Empty prompt"}

        if language and language != "English":
            prompt += f"\n\nIMPORTANT: Respond strictly in {language}."

        h = hashlib.md5(prompt.encode("utf-8", "ignore")).hexdigest()

        if redis_client:
            try:
                c = redis_client.get(f"ai_cache:{h}")

                if isinstance(c, bytes):
                    c = c.decode("utf-8", "ignore")

                if c:
                    business_metrics.increment("ai_queries_cached")

                    return {
                        "success": True,
                        "response": json.loads(c),
                        "provider": "cache",
                    }
            except Exception:
                pass

        if qdrant_client:
            try:
                hits = qdrant_client.search(
                    collection_name="ai_semantic_cache",
                    query_vector=generate_embedding(prompt),
                    limit=1,
                    score_threshold=0.90,
                )

                if hits:
                    business_metrics.increment("ai_queries_cached")

                    return {
                        "success": True,
                        "response": hits[0].payload.get("response"),
                        "provider": "semantic_cache",
                    }
            except Exception:
                pass

        for provider in self.get_providers():
            try:
                resp = None

                if provider["name"] == "Gemini":
                    resp = gemini_breaker.call(self._call_gemini, prompt, provider["key"])
                elif provider["name"] == "OpenAI":
                    resp = openai_breaker.call(self._call_openai, prompt, provider["key"])
                elif provider["name"] == "Anthropic":
                    resp = anthropic_breaker.call(self._call_anthropic, prompt, provider["key"])

                if resp:
                    if redis_client:
                        try:
                            redis_client.setex(f"ai_cache:{h}", 86400, json.dumps(resp))
                        except Exception:
                            pass

                    if qdrant_client:
                        try:
                            PointStructLocal = globals().get("PointStruct")

                            if PointStructLocal:
                                qdrant_client.upsert(
                                    collection_name="ai_semantic_cache",
                                    points=[
                                        PointStructLocal(
                                            id=uuid.uuid4().hex,
                                            vector=generate_embedding(prompt),
                                            payload={"query": prompt, "response": resp},
                                        )
                                    ],
                                )
                        except Exception:
                            pass

                    est_tokens = (len(prompt) + len(str(resp))) // 4

                    increment_system_metric("ai_requests_total", 1)
                    increment_system_metric("ai_tokens_estimated", est_tokens)

                    return {
                        "success": True,
                        "response": resp,
                        "provider": provider["name"],
                    }

            except Exception:
                continue

        return {"success": False, "error": "All providers failed"}

    def summarize(self, text: str):
        r = self.request(f"Summarize: {str(text or '')[:3000]}")
        return r.get("response") if r.get("success") else None


ai_system = MultiAI()


# ============================================================
# AGENTIC WEB SEARCH
# ============================================================
def agentic_web_search(query: str, stype: str = "gov", allowed_domains=None) -> str:
    key = get_setting("SERPER_API_KEY")

    if not key:
        return ""

    query = str(query or "").strip()

    if not query:
        return ""

    if allowed_domains:
        domains = list(dict.fromkeys([d for d in allowed_domains if d]))[:5]

        if domains:
            query += " " + " OR ".join([f"site:{d}" for d in domains])
    elif stype == "gov":
        query = f"{query} site:ap.gov.in OR site:gov.in"

    try:
        r = requests.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": key,
                "Content-Type": "application/json",
            },
            json={"q": query, "num": 5},
            timeout=10,
        )

        return "\n".join(
            [
                f"Source: {x.get('link')}\nSnippet: {x.get('snippet')}\n"
                for x in r.json().get("organic", [])
            ]
        )
    except Exception:
        return ""


# ============================================================
# CASCADING SEARCH
# ============================================================
def cascading_search(query: str, language: str = "English", limit: int = 5) -> List[Dict]:
    q = sanitize_search_query(query)
    results = []

    try:
        docs = search_documents(q, limit)

        for d in docs:
            results.append(
                {
                    "id": d.get("id"),
                    "filename": d.get("filename", "Document"),
                    "ai_summary": d.get("ai_summary") or "",
                    "source": "internal",
                }
            )
    except Exception:
        pass

    training_links = get_training_links()

    if training_links:
        trusted_lines = "\n".join(
            [
                f"- {l.get('title', 'Source')}: {l.get('url', '')}"
                for l in training_links
            ]
        )

        results.append(
            {
                "id": "training_links",
                "filename": "Trusted Sources",
                "ai_summary": trusted_lines,
                "source": "training",
            }
        )

    if len(results) < 2:
        domains = [l.get("domain") for l in training_links if l.get("domain")]

        web = agentic_web_search(q, "gov", allowed_domains=domains)

        if not web.strip():
            web = agentic_web_search(q, "deep")

        if web:
            results.append(
                {
                    "id": "web",
                    "filename": "Government Web Search",
                    "ai_summary": web,
                    "source": "external",
                }
            )

    return results[:limit + 2]


# ============================================================
# AUTHENTICATION
# ============================================================
def hash_password(password: str) -> str:
    password = str(password or "")

    if BCRYPT_AVAILABLE and bcrypt:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=10)).decode("utf-8")

    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def check_password(password: str, password_hash: str) -> bool:
    if not password or not password_hash:
        return False

    password = str(password)
    password_hash = str(password_hash)

    if BCRYPT_AVAILABLE and bcrypt and password_hash.startswith("$2"):
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except Exception:
            return False

    return hashlib.sha256(password.encode("utf-8")).hexdigest() == password_hash


def get_local_admin():
    if not LOCAL_ADMIN_FILE or not os.path.exists(LOCAL_ADMIN_FILE):
        return None

    try:
        with open(LOCAL_ADMIN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

            if isinstance(data, dict) and data.get("email"):
                data.setdefault("active", True)
                data.setdefault("admin_level", "system_admin")
                data.setdefault("name", "System Admin")
                data.setdefault("id", "local-admin")
                return data
    except Exception:
        return None

    return None


def save_local_admin(email: str, name: str, password: str, admin_level: str = "system_admin") -> bool:
    if not LOCAL_ADMIN_FILE:
        return False

    try:
        row = {
            "id": "local-admin",
            "email": str(email or "").strip().lower(),
            "name": str(name or "System Admin").strip(),
            "office_code": "",
            "office_name": "Local Office",
            "designation": "Administrator",
            "section": "",
            "seat_number": "",
            "admin_level": admin_level,
            "active": True,
            "password_hash": hash_password(password),
            "created_at": now_utc().isoformat(),
        }

        with open(LOCAL_ADMIN_FILE, "w", encoding="utf-8") as f:
            json.dump(row, f, indent=2)

        return True
    except Exception as e:
        logger.error(f"Failed to save local admin: {e}")
        return False


def has_any_user() -> bool:
    sb = globals().get("supabase")

    if sb:
        try:
            r = sb.table("users").select("id").limit(1).execute()

            if r.data:
                return True
        except Exception:
            pass

    return get_local_admin() is not None


def create_admin_user(email: str, name: str, password: str, admin_level: str = "system_admin"):
    email = str(email or "").strip().lower()
    name = str(name or "System Admin").strip()

    if not validate_email(email):
        return {"success": False, "error": "Invalid email"}

    if len(password or "") < 8:
        return {"success": False, "error": "Password must be at least 8 characters"}

    user_row = {
        "email": email,
        "name": name,
        "office_code": "",
        "office_name": "Head Office",
        "designation": "System Administrator",
        "section": "",
        "seat_number": "",
        "admin_level": admin_level,
        "active": True,
        "password_hash": hash_password(password),
    }

    sb = globals().get("supabase")

    if sb:
        try:
            r = sb.table("users").insert(user_row).execute()

            if r.data:
                return {"success": True, "backend": "supabase"}
        except Exception as e:
            logger.error(f"Supabase admin creation failed: {e}")

            if not get_local_admin():
                if save_local_admin(email, name, password, admin_level):
                    return {
                        "success": True,
                        "backend": "local",
                        "warning": f"Supabase insert failed. Created local admin instead. Error: {e}",
                    }

            return {"success": False, "error": str(e)}

    if get_local_admin():
        return {"success": False, "error": "Local admin already exists"}

    if save_local_admin(email, name, password, admin_level):
        return {"success": True, "backend": "local"}

    return {"success": False, "error": "Could not create admin"}


def get_user(email: str):
    if not email:
        return None

    email = str(email).strip().lower()

    if redis_client:
        try:
            c = redis_client.get(f"user_v2:{email}")

            if c:
                if isinstance(c, bytes):
                    c = c.decode("utf-8", "ignore")

                return json.loads(c)
        except Exception:
            pass

    sb = globals().get("supabase")

    if sb:
        try:
            r = sb.table("users").select(
                "id, email, name, office_code, office_name, designation, section, seat_number, admin_level, active, password_hash"
            ).eq("email", email).execute()

            if r.data:
                u = r.data[0]

                if redis_client:
                    try:
                        redis_client.setex(f"user_v2:{email}", 3600, json.dumps(u, default=str))
                    except Exception:
                        pass

                return u
        except Exception:
            pass

    local_admin = get_local_admin()

    if local_admin and local_admin.get("email") == email:
        return local_admin

    return None


def login_rate_limited(email: str) -> bool:
    if redis_client:
        try:
            k = f"login_attempts:{email}"
            v = redis_client.get(k)

            return int(v) > 5 if v else False
        except Exception:
            return False

    sb = globals().get("supabase")

    if sb:
        try:
            cutoff = (now_utc() - timedelta(minutes=15)).isoformat()

            r = (
                sb.table("login_attempts")
                .select("email")
                .eq("email", email)
                .gte("created_at", cutoff)
                .limit(10)
                .execute()
            )

            return len(r.data or []) >= 5
        except Exception:
            return False

    return False


def increment_login_attempt(email: str):
    if redis_client:
        try:
            k = f"login_attempts:{email}"

            redis_client.set(k, "0", ex=900, nx=True)
            redis_client.incr(k)
        except Exception:
            pass

        return

    sb = globals().get("supabase")

    if sb:
        try:
            sb.table("login_attempts").insert(
                {
                    "email": email,
                    "created_at": now_utc().isoformat(),
                }
            ).execute()
        except Exception:
            pass


COOKIE_NAME = "rta_session"
SESSION_DAYS = 7


def init_session_state():
    defaults = {
        "user": None,
        "logged_in": False,
        "page": "feed",
        "admin_level": "staff",
        "maintenance_mode": False,
        "sidebar_open": True,
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def try_auto_login():
    if st.session_state.get("logged_in"):
        return

    try:
        token = cookies.get(COOKIE_NAME)
    except Exception:
        token = None

    if not token:
        return

    h = hashlib.sha256(str(token).encode("utf-8")).hexdigest()

    sb = globals().get("supabase")

    if not sb:
        return

    try:
        r = sb.table("sessions").select("*").eq("token_hash", h).execute()

        if not r.data:
            return

        s = r.data[0]
        expires_raw = s.get("expires_at")

        if not expires_raw:
            return

        expires_at = datetime.fromisoformat(str(expires_raw).replace("Z", "+00:00"))

        if expires_at <= now_utc():
            return

        u = get_user(s.get("email"))

        if u and u.get("active", True):
            st.session_state.logged_in = True
            st.session_state.user = u
            st.session_state.admin_level = u.get("admin_level", "staff")
        elif u and not u.get("active", True):
            try:
                sb.table("sessions").delete().eq("token_hash", h).execute()
            except Exception:
                pass

            cookies.delete(COOKIE_NAME)
    except Exception:
        pass


def do_login(u: Dict):
    st.session_state.logged_in = True
    st.session_state.user = u
    st.session_state.admin_level = u.get("admin_level", "staff")

    token = secrets.token_urlsafe(32)
    h = hashlib.sha256(token.encode("utf-8")).hexdigest()

    sb = globals().get("supabase")

    if sb:
        try:
            sb.table("sessions").insert(
                {
                    "token_hash": h,
                    "email": u.get("email"),
                    "expires_at": (now_utc() + timedelta(days=SESSION_DAYS)).isoformat(),
                }
            ).execute()
        except Exception:
            pass

    try:
        cookies.set(COOKIE_NAME, token, max_age=SESSION_DAYS * 24 * 3600)
    except Exception:
        pass

    audit_log(u.get("email", "unknown"), "user.login", "user", None)
    business_metrics.increment("active_users", u.get("email"))

    st.rerun()


def logout():
    h = None

    try:
        token = cookies.get(COOKIE_NAME)

        if token:
            h = hashlib.sha256(str(token).encode("utf-8")).hexdigest()
    except Exception:
        pass

    sb = globals().get("supabase")

    if sb and h:
        try:
            sb.table("sessions").delete().eq("token_hash", h).execute()
        except Exception:
            pass

    email = (st.session_state.get("user") or {}).get("email", "unknown")

    try:
        audit_log(email, "user.logout", "user", None)
    except Exception:
        pass

    st.session_state.clear()

    try:
        cookies.delete(COOKIE_NAME)
    except Exception:
        pass

    st.rerun()


# ============================================================
# SOCIAL FEED HELPERS
# ============================================================
def extract_mentions(content: str):
    pattern = r"@([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
    return re.findall(pattern, str(content or ""))


def extract_hashtags(content: str):
    pattern = r"#([a-zA-Z0-9_]+)"
    return re.findall(pattern, str(content or ""))


def send_notification(recipient_email, sender_email, ntype, post_id, message):
    sb = globals().get("supabase")

    if not sb:
        return

    try:
        sb.table("notifications").insert(
            {
                "recipient_email": recipient_email,
                "sender_email": sender_email,
                "type": ntype,
                "post_id": str(post_id) if post_id else None,
                "message": message,
                "read": False,
                "created_at": now_utc().isoformat(),
            }
        ).execute()
    except Exception as e:
        logger.error(f"Notification failed: {e}")


# ============================================================
# MAINTENANCE HELPERS
# ============================================================
def is_maintenance_mode() -> bool:
    if redis_client:
        try:
            val = redis_client.get("maintenance_mode")

            if isinstance(val, bytes):
                val = val.decode("utf-8", "ignore")

            return val == "1"
        except Exception:
            pass

    return bool(st.session_state.get("maintenance_mode", False))


def set_maintenance_mode(enabled: bool):
    if redis_client:
        try:
            if enabled:
                redis_client.set("maintenance_mode", "1")
            else:
                redis_client.delete("maintenance_mode")
        except Exception:
            pass

    st.session_state["maintenance_mode"] = enabled


def cleanup_old_messages():
    sb = globals().get("supabase")

    if not sb:
        return

    try:
        cutoff = (now_utc() - timedelta(hours=24)).isoformat()

        sb.table("messages").delete().lt(
            "created_at", cutoff
        ).eq(
            "is_starred", False
        ).execute()
    except Exception as e:
        logger.error(f"Message cleanup failed: {e}")


# ============================================================
# MESSAGE COMPRESSION HELPERS
# ============================================================
def pack_message(text: str) -> str:
    comp_bytes, method = compress_data(str(text or "").encode("utf-8", "ignore"))
    b64 = base64.b64encode(comp_bytes).decode("ascii")
    return f"{method}:{b64}"


def unpack_message(payload: str) -> str:
    if not payload:
        return ""

    try:
        if ":" in payload:
            method, b64 = payload.split(":", 1)
            raw = base64.b64decode(b64)

            return decompress_data(raw, method).decode("utf-8", "ignore")

        raw = base64.b64decode(payload)

        return decompress_data(raw, "lzma").decode("utf-8", "ignore")
    except Exception:
        return str(payload)


# ============================================================
# ADMIN BOOTSTRAP
# ============================================================
def bootstrap_env_admin():
    try:
        if has_any_user():
            return

        email = secret("ADMIN_EMAIL", "").strip()
        password = secret("ADMIN_PASSWORD", "")
        name = secret("ADMIN_NAME", "System Admin")

        if email and password:
            create_admin_user(email, name, password, "system_admin")
    except Exception as e:
        logger.error(f"Admin bootstrap failed: {e}") 
# ============================================================
# UI PAGES
# ============================================================
def show_initial_admin_setup():
    st.markdown("### 🔐 First-Time System Admin Setup")
    st.info("No users found. Create a System Admin account to enter the app.")

    with st.form("create_admin_form"):
        name = st.text_input("Admin Name", "System Admin")
        email = st.text_input("Admin Email", "admin@rta.local")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")

        if st.form_submit_button("Create System Admin"):
            if not email or not password:
                show_toast("Email and password are required", "error")
            elif not validate_email(email):
                show_toast("Invalid email format", "error")
            elif len(password) < 8:
                show_toast("Password must be at least 8 characters", "error")
            elif password != confirm:
                show_toast("Passwords do not match", "error")
            else:
                res = create_admin_user(email, name, password, "system_admin")

                if res.get("success"):
                    if res.get("warning"):
                        st.warning(res["warning"])

                    show_toast("System admin created. Please sign in.")
                    st.rerun()
                else:
                    show_toast(res.get("error", "Admin creation failed"), "error")


def show_login():
    if not has_any_user():
        show_initial_admin_setup()
        st.divider()

    quotes = [
        {
            "text": "Service to the public is service to the nation",
            "author": "Mahatma Gandhi",
        },
        {
            "text": "Together we move Andhra forward",
            "author": "RTA Mission",
        },
        {
            "text": "Every file processed is a citizen served",
            "author": "RTA Vision",
        },
    ]

    q = quotes[int(time.time()) % len(quotes)]

    st.markdown(
        f"""
        <div class="login-container">
            <div style="text-align:center;">
                <div style="font-size:50px;">🏛️</div>
                <h1 style="color:#0A66C2;">RTA Anubandhan</h1>
                <p style="color:#666;">Government Workspace Platform</p>
            </div>

            <div class="quote-box">
                <p style="font-style:italic;">"{q['text']}"</p>
                <small>- {q['author']}</small>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([1, 2, 1])

    with c2:
        email = st.text_input("Email", key="login_email").strip().lower()
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Sign In", use_container_width=True):
            if not email or not password:
                show_toast("Enter email and password", "warning")
            elif not validate_email(email):
                show_toast("Invalid email format", "error")
            elif login_rate_limited(email):
                show_toast("Too many attempts. Try again later.", "error")
            else:
                u = get_user(email)

                if u and u.get("active", True) and check_password(password, u.get("password_hash", "")):
                    do_login(u)
                else:
                    increment_login_attempt(email)
                    show_toast("Invalid credentials", "error")


def show_feed():
    u = st.session_state.user or {}

    if not u:
        return

    hour = now_utc().hour
    g = "☀️ Good Morning" if hour < 12 else "🌤️ Hello" if hour < 17 else "🌙 Good Evening"

    st.markdown(f"### {g}, {u.get('name', 'User')}!")
    st.caption(f"📍 {u.get('office_name', 'Office')} | {u.get('designation', 'Staff')}")

    sb = globals().get("supabase")

    # Announcements
    if sb:
        try:
            anns = (
                sb.table("announcements")
                .select("*")
                .gt("expires_at", now_utc().isoformat())
                .order("created_at", desc=True)
                .limit(3)
                .execute()
                .data or []
            )

            for ann in anns:
                icon = {
                    "info": "ℹ️",
                    "warning": "⚠️",
                    "critical": "🚨",
                }.get(ann.get("priority", "info"), "ℹ️")

                st.markdown(
                    f"""
                    <div class="announcement-card">
                        <div style="font-size:20px;">{icon}</div>
                        <h3>{html.escape(str(ann.get('title', '')))}</h3>
                        <p>{html.escape(str(ann.get('message', '')))}</p>
                        <small>Expires: {str(ann.get('expires_at', ''))[:10]}</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        except Exception:
            pass

    # Search and tag filter
    col1, col2 = st.columns([3, 1])

    with col1:
        search_q = st.text_input(
            "🔍 Search posts",
            placeholder="Search by keyword, @mention, or #tag",
            key="feed_search",
        )

    with col2:
        filter_tag = "All"

        try:
            if sb:
                tags = sb.table("post_tags").select("tag").execute().data or []

                tag_counts = {}

                for t in tags:
                    tag_counts[t.get("tag")] = tag_counts.get(t.get("tag"), 0) + 1

                top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:5]

                filter_tag = st.selectbox(
                    "Filter by Tag",
                    ["All"] + [f"#{t[0]}" for t in top_tags if t[0]],
                    key="tag_filter",
                )
        except Exception:
            filter_tag = "All"

    # Create post
    with st.form("post_form", clear_on_submit=False):
        content = st.text_area(
            "What's on your mind?",
            placeholder="Use @email to mention, #tag to categorize",
            height=100,
            key="post_content",
        )

        post_type = st.selectbox(
            "Post Type",
            ["📝 Update", "📢 Announcement", "❓ Question", "🎉 Celebration", "📅 Event"],
            key="post_type",
        )

        col_a1, col_a2 = st.columns(2)

        with col_a1:
            file_upload = st.file_uploader("📎 Attachment", type=["jpg", "png", "pdf"], key="post_file")

        with col_a2:
            is_pinned = st.checkbox("📌 Pin Post", key="post_pin") if u.get("admin_level") != "staff" else False

        submitted = st.form_submit_button("📤 Post")

        if submitted and content.strip():
            if not sb:
                show_toast("Supabase is not configured. Social feed storage is unavailable.", "warning")
            else:
                content_clean = sanitize_input(content)
                post_id = None

                try:
                    result = sb.table("social_posts").insert(
                        {
                            "author_email": u.get("email"),
                            "content": content_clean,
                            "post_type": post_type.split()[-1].lower(),
                            "is_pinned": is_pinned,
                            "pinned_by": u.get("email") if is_pinned else None,
                            "created_at": now_utc().isoformat(),
                        }
                    ).execute()

                    if result.data:
                        post_id = result.data[0].get("id")

                        if file_upload:
                            file_result = storage_system.upload_document(
                                file_upload.read(),
                                file_upload.name,
                                "social_post",
                                u.get("email"),
                            )

                            if file_result.get("success"):
                                sb.table("social_posts").update(
                                    {
                                        "file_key": file_result.get("document_id"),
                                        "filename": file_upload.name,
                                    }
                                ).eq("id", post_id).execute()

                        for tag in extract_hashtags(content):
                            try:
                                sb.table("post_tags").insert(
                                    {
                                        "post_id": post_id,
                                        "tag": tag.lower(),
                                    }
                                ).execute()
                            except Exception:
                                pass

                        for mention_email in extract_mentions(content):
                            mentioned_user = get_user(mention_email)

                            if mentioned_user:
                                send_notification(
                                    mention_email,
                                    u.get("email"),
                                    "mention",
                                    post_id,
                                    f"{u.get('name')} mentioned you in a post",
                                )

                        audit_log(u.get("email"), "post.create", "post", post_id)
                        show_toast("Posted successfully!")
                        st.rerun()

                except Exception as e:
                    show_toast(f"Failed to post: {str(e)}", "error")

    # Load posts
    posts = []

    try:
        if search_q:
            search_sql = sanitize_search_query(search_q)

            posts = (
                sb.table("social_posts")
                .select("*, users(name, designation)")
                .or_(f"content.ilike.%{search_sql}%,author_email.ilike.%{search_sql}%")
                .order("is_pinned", desc=True)
                .order("created_at", desc=True)
                .limit(50)
                .execute()
                .data or []
            )

        elif filter_tag != "All":
            selected_tag = str(filter_tag).replace("#", "").lower()

            tag_posts = (
                sb.table("post_tags")
                .select("post_id")
                .eq("tag", selected_tag)
                .execute()
                .data or []
            )

            if tag_posts:
                post_ids = [p.get("post_id") for p in tag_posts if p.get("post_id")]

                posts = (
                    sb.table("social_posts")
                    .select("*, users(name, designation)")
                    .in_("id", post_ids)
                    .order("is_pinned", desc=True)
                    .order("created_at", desc=True)
                    .execute()
                    .data or []
                )
        else:
            posts = (
                sb.table("social_posts")
                .select("*, users(name, designation)")
                .order("is_pinned", desc=True)
                .order("created_at", desc=True)
                .limit(50)
                .execute()
                .data or []
            )

    except Exception:
        try:
            posts = (
                sb.table("social_posts")
                .select("*")
                .order("is_pinned", desc=True)
                .order("created_at", desc=True)
                .limit(50)
                .execute()
                .data or []
            )
        except Exception:
            posts = []

    if not posts:
        st.markdown(
            '<div class="empty-state"><div style="font-size:60px;">📭</div><h3>No posts yet</h3><p>Be the first to share an update.</p></div>',
            unsafe_allow_html=True,
        )

    # Render posts
    for p in posts:
        post_id = str(p.get("id", uuid.uuid4()))
        author = p.get("users") or {}
        author_name = author.get("name") or p.get("author_email", "Unknown")

        with st.container():
            if p.get("is_pinned"):
                st.markdown('<span class="pinned-badge">📌 PINNED</span>', unsafe_allow_html=True)

            col_avatar, col_info = st.columns([1, 5])

            with col_avatar:
                st.markdown(
                    f'<div class="post-avatar">{str(author_name)[0].upper()}</div>',
                    unsafe_allow_html=True,
                )

            with col_info:
                st.markdown(f"**{author_name}**")
                st.caption(f"{author.get('designation', '')} • {str(p.get('created_at', ''))[:16]}")

            st.markdown(
                f'<div style="margin: 12px 0; font-size: 15px;">{html.escape(str(p.get("content", "")))}</div>',
                unsafe_allow_html=True,
            )

            try:
                if sb:
                    post_tags = (
                        sb.table("post_tags")
                        .select("tag")
                        .eq("post_id", p.get("id"))
                        .execute()
                        .data or []
                    )

                    if post_tags:
                        tags_html = " ".join(
                            [
                                f'<span class="tag-badge">#{html.escape(str(t.get("tag")))}' "</span>"
                                for t in post_tags
                            ]
                        )

                        st.markdown(
                            f'<div style="margin-bottom: 8px;">{tags_html}</div>',
                            unsafe_allow_html=True,
                        )
            except Exception:
                pass

            attachment_doc = p.get("file_key") or p.get("document_id")

            if attachment_doc:
                st.markdown(f"📎 **{p.get('filename', 'Attachment')}**")

                if st.button("⬇️ Download Attachment", key=f"dl_post_{post_id}"):
                    file_data = storage_system.download_document(attachment_doc)

                    if file_data:
                        st.download_button(
                            "Save to Device",
                            file_data,
                            file_name=p.get("filename", "file"),
                            key=f"save_{post_id}",
                        )

            st.markdown('<div class="post-actions">', unsafe_allow_html=True)

            col_react1, col_react2, col_react3, col_comment = st.columns(4)

            with col_react1:
                like_count = 0
                user_liked = False

                try:
                    if sb:
                        reactions = (
                            sb.table("post_reactions")
                            .select("*")
                            .eq("post_id", p.get("id"))
                            .eq("reaction", "like")
                            .execute()
                            .data or []
                        )

                        like_count = len(reactions)
                        user_liked = any(r.get("user_email") == u.get("email") for r in reactions)
                except Exception:
                    pass

                if st.button(
                    f"👍 {like_count}",
                    key=f"like_{post_id}",
                    type="primary" if user_liked else "secondary",
                ):
                    try:
                        if sb:
                            existing = (
                                sb.table("post_reactions")
                                .select("id")
                                .eq("post_id", p.get("id"))
                                .eq("user_email", u.get("email"))
                                .eq("reaction", "like")
                                .execute()
                            )

                            if existing.data:
                                sb.table("post_reactions").delete().eq("id", existing.data[0].get("id")).execute()
                            else:
                                sb.table("post_reactions").insert(
                                    {
                                        "post_id": p.get("id"),
                                        "user_email": u.get("email"),
                                        "reaction": "like",
                                    }
                                ).execute()

                                if p.get("author_email") != u.get("email"):
                                    send_notification(
                                        p.get("author_email"),
                                        u.get("email"),
                                        "reaction",
                                        p.get("id"),
                                        f"{u.get('name')} liked your post",
                                    )

                            st.rerun()
                    except Exception as e:
                        show_toast(f"Failed: {str(e)}", "error")

            with col_react2:
                if st.button("👏 Appreciate", key=f"clap_{post_id}"):
                    try:
                        if sb:
                            existing = (
                                sb.table("post_reactions")
                                .select("id")
                                .eq("post_id", p.get("id"))
                                .eq("user_email", u.get("email"))
                                .eq("reaction", "clap")
                                .execute()
                            )

                            if existing.data:
                                sb.table("post_reactions").delete().eq("id", existing.data[0].get("id")).execute()
                            else:
                                sb.table("post_reactions").insert(
                                    {
                                        "post_id": p.get("id"),
                                        "user_email": u.get("email"),
                                        "reaction": "clap",
                                    }
                                ).execute()

                            st.rerun()
                    except Exception:
                        pass

            with col_react3:
                if st.button("🎉 Celebrate", key=f"celebrate_{post_id}"):
                    try:
                        if sb:
                            existing = (
                                sb.table("post_reactions")
                                .select("id")
                                .eq("post_id", p.get("id"))
                                .eq("user_email", u.get("email"))
                                .eq("reaction", "celebrate")
                                .execute()
                            )

                            if existing.data:
                                sb.table("post_reactions").delete().eq("id", existing.data[0].get("id")).execute()
                            else:
                                sb.table("post_reactions").insert(
                                    {
                                        "post_id": p.get("id"),
                                        "user_email": u.get("email"),
                                        "reaction": "celebrate",
                                    }
                                ).execute()

                            st.rerun()
                    except Exception:
                        pass

            comment_count = 0

            with col_comment:
                try:
                    if sb:
                        comments_count_rows = (
                            sb.table("post_comments")
                            .select("id")
                            .eq("post_id", p.get("id"))
                            .execute()
                            .data or []
                        )

                        comment_count = len(comments_count_rows)
                except Exception:
                    pass

                if st.button(f"💬 Comment ({comment_count})", key=f"comment_btn_{post_id}"):
                    st.session_state[f"show_comments_{post_id}"] = not st.session_state.get(
                        f"show_comments_{post_id}", False
                    )

            st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state.get(f"show_comments_{post_id}", False):
                st.markdown("---")
                st.markdown(f"#### 💬 Comments ({comment_count})")

                comments = []

                try:
                    if sb:
                        try:
                            comments = (
                                sb.table("post_comments")
                                .select("*, users(name)")
                                .eq("post_id", p.get("id"))
                                .order("created_at")
                                .execute()
                                .data or []
                            )
                        except Exception:
                            comments = (
                                sb.table("post_comments")
                                .select("*")
                                .eq("post_id", p.get("id"))
                                .order("created_at")
                                .execute()
                                .data or []
                            )
                except Exception:
                    comments = []

                for c in comments:
                    commenter_name = (c.get("users") or {}).get("name") or c.get("author_email", "Unknown")

                    st.markdown(
                        f"""
                        <div class="comment-item">
                            <div><b>{html.escape(str(commenter_name))}</b></div>
                            <div>{html.escape(str(c.get('content', '')))}</div>
                            <div style="font-size:12px;color:#666;">{str(c.get('created_at', ''))[:16]}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                new_comment = st.text_area(
                    "Add a comment",
                    key=f"new_comment_{post_id}",
                    height=60,
                )

                if st.button("Post Comment", key=f"post_comment_{post_id}"):
                    if new_comment.strip() and sb:
                        try:
                            sb.table("post_comments").insert(
                                {
                                    "post_id": p.get("id"),
                                    "author_email": u.get("email"),
                                    "content": sanitize_input(new_comment),
                                    "created_at": now_utc().isoformat(),
                                }
                            ).execute()

                            if p.get("author_email") != u.get("email"):
                                send_notification(
                                    p.get("author_email"),
                                    u.get("email"),
                                    "reply",
                                    p.get("id"),
                                    f"{u.get('name')} commented on your post",
                                )

                            show_toast("Comment posted!")
                            st.rerun()
                        except Exception as e:
                            show_toast(f"Failed: {str(e)}", "error")

            if u.get("admin_level") != "staff" or p.get("author_email") == u.get("email"):
                if st.button("🗑️ Delete Post", key=f"del_post_{post_id}", type="secondary"):
                    try:
                        if sb:
                            sb.table("social_posts").delete().eq("id", p.get("id")).execute()
                            audit_log(u.get("email"), "post.delete", "post", p.get("id"))
                            show_toast("Post deleted")
                            st.rerun()
                    except Exception as e:
                        show_toast(f"Failed: {str(e)}", "error")

            st.divider()


def show_workspace():
    render_back_button()

    st.markdown("### 🧰 Workspace")

    c = st.columns(4)

    with c[0]:
        if st.button("📥 Tapal"):
            st.session_state.page = "tapal"
            st.rerun()

    with c[1]:
        if st.button("📮 Dispatch"):
            st.session_state.page = "dispatch"
            st.rerun()

    with c[2]:
        if st.button("📄 Docs"):
            st.session_state.page = "documents"
            st.rerun()

    with c[3]:
        if st.button("🤖 AI"):
            st.session_state.page = "ai"
            st.rerun()


def show_tapal():
    render_back_button()

    u = st.session_state.user or {}
    st.markdown("### 📥 Smart Tapal")

    with st.form("tapal_form"):
        c1, c2, c3 = st.columns(3)

        with c1:
            direction = st.selectbox("Direction", ["Inward", "Outward"])
            d = st.date_input("Date", value=date.today())

        with c2:
            seq = st.text_input("Seq No.")
            ft = st.text_input("From/To")

        with c3:
            subj = st.text_input("Subject")
            pri = st.selectbox("Priority", ["Normal", "Urgent", "Immediate"])

        rno = f"R.No/{u.get('section', 'A')}/{u.get('designation', 'JA')}/{now_utc().year}/{seq}" if seq else ""

        if rno:
            st.info(f"📋 Reference: {rno}")

        remarks = st.text_area("Remarks", height=80)
        file = st.file_uploader("Attachment", type=["pdf", "jpg", "png"])

        if st.form_submit_button("💾 Save"):
            if not seq or not subj:
                show_toast("Seq No and Subject are required", "warning")
                return

            did = None

            if file:
                if file.size > 20 * 1024 * 1024:
                    show_toast("File too large. Max 20MB.", "error")
                    return

                with st.spinner("Uploading..."):
                    res = storage_system.upload_document(
                        file.read(),
                        file.name,
                        "tapal",
                        u.get("email"),
                    )

                if res.get("success"):
                    did = res.get("document_id")
                else:
                    show_toast(res.get("error", "Upload failed"), "error")
                    return

            sb = globals().get("supabase")

            if sb:
                try:
                    sb.table("tapal_log").insert(
                        {
                            "r_no": rno,
                            "direction": direction,
                            "tapal_date": d.isoformat(),
                            "section": u.get("section"),
                            "designation": u.get("designation"),
                            "from_to": ft,
                            "subject": subj,
                            "priority": pri,
                            "remarks": remarks,
                            "document_id": did,
                            "created_by": u.get("email"),
                            "created_at": now_utc().isoformat(),
                        }
                    ).execute()

                    show_toast("Saved successfully!")
                    st.rerun()
                except Exception:
                    show_toast("Failed to save tapal record", "error")
            else:
                show_toast("Saved file locally only. Supabase is not configured.", "warning")


def show_dispatch():
    render_back_button()

    u = st.session_state.user or {}
    st.markdown("### 📮 Dispatch")

    with st.form("dispatch_form"):
        c1, c2 = st.columns(2)

        with c1:
            env = st.selectbox("Envelope", ["DL", "C5", "A4"])
            seq = st.text_input("Seq No.")

        with c2:
            frm = st.text_area("From", value="Office of the Transport Commissioner")

        to = st.text_area("To", height=80)
        subj = st.text_input("Subject")

        if st.form_submit_button("🖨️ Generate"):
            safe_to = html.escape(to)
            safe_frm = html.escape(frm)
            safe_subj = html.escape(subj)

            dno = f"Dispatch/{u.get('section', 'A')}/{u.get('designation', 'JA')}/{now_utc().year}/{seq}"

            st.session_state.dispatch_ready = True
            st.session_state.dispatch_html = f"""
            <div style="border:2px solid #000;padding:20px;background:white;color:black;">
                <b>Dispatch No:</b> {dno}<br>
                <b>Envelope:</b> {env}<br>
                <b>From:</b> {safe_frm}<br>
                <b>To:</b><br>{safe_to}<br>
                <b>Subject:</b> {safe_subj}
            </div>
            """

            show_toast("Generated!")

    if st.session_state.get("dispatch_ready"):
        st.markdown(st.session_state.get("dispatch_html", ""), unsafe_allow_html=True)


def document_card(doc: Dict):
    doc_id = str(doc.get("id", ""))

    if not doc_id:
        return

    with st.expander(f"📄 {doc.get('filename', 'Document')}"):
        st.write(f"Summary: {doc.get('ai_summary') or '(Processing)'}")

        try:
            size_bytes = int(doc.get("compressed_size_bytes", 0) or 0)
            st.caption(f"Tier: {doc.get('storage_tier', 'hot')} | Size: {size_bytes / 1024:.1f} KB")
        except Exception:
            pass

        if st.button("Download", key=f"dl_{doc_id}"):
            presigned = storage_system.get_presigned_url(
                doc.get("storage_path", ""),
                doc.get("storage_tier", "hot"),
            )

            if presigned:
                st.markdown(f"[Download]({presigned})")
            else:
                data = storage_system.download_document(doc_id)

                if data:
                    st.download_button(
                        "Save",
                        data,
                        file_name=doc.get("filename", "file"),
                        key=f"sv_{doc_id}",
                    )
                else:
                    st.error("Unable to download file.")


def show_documents():
    render_back_button()

    u = st.session_state.user or {}
    st.markdown("### 📄 Documents")

    file = st.file_uploader("Upload", type=["pdf", "jpg", "png", "doc", "docx"])

    if file:
        if file.size > 20 * 1024 * 1024:
            show_toast("Too large. Max 20MB.", "error")
        else:
            with st.spinner("Uploading..."):
                res = storage_system.upload_document(
                    file.read(),
                    file.name,
                    "circular",
                    u.get("email"),
                )

            if res.get("success"):
                if res.get("duplicate"):
                    show_toast(res.get("message", "Duplicate file"), "warning")
                else:
                    show_toast(f"Uploaded! {res.get('compression_ratio', 0) * 100:.1f}% compressed")
            else:
                show_toast(res.get("error", "Upload failed"), "error")

    q = st.text_input("Search")
    docs = []

    if q:
        docs = search_documents(q)
    else:
        sb = globals().get("supabase")

        if sb:
            try:
                docs = (
                    sb.table("files")
                    .select("id, filename, storage_path, storage_tier, ai_summary, uploaded_at, compressed_size_bytes")
                    .order("uploaded_at", desc=True)
                    .limit(20)
                    .execute()
                    .data or []
                )
            except Exception:
                docs = read_local_documents()[:20]
        else:
            docs = sorted(
                read_local_documents(),
                key=lambda x: str(x.get("uploaded_at", "")),
                reverse=True,
            )[:20]

    if not docs:
        st.markdown(
            '<div class="empty-state"><div style="font-size:60px;">📭</div><h3>No documents</h3></div>',
            unsafe_allow_html=True,
        )

    for d in docs:
        document_card(d)


def show_messages():
    render_back_button()

    u = st.session_state.user or {}
    st.markdown("### 💬 Messages")
    st.caption("Auto-delete after 24h. ⭐ Star to compress and keep forever.")

    sb = globals().get("supabase")

    if not sb:
        st.warning("Supabase is required for messages.")
        return

    with st.form("send_msg"):
        msg = st.text_input("Type a message...")

        if st.form_submit_button("Send"):
            if msg:
                try:
                    sb.table("messages").insert(
                        {
                            "user_id": u.get("email"),
                            "content": sanitize_input(msg),
                            "created_at": now_utc().isoformat(),
                        }
                    ).execute()

                    st.rerun()
                except Exception as e:
                    show_toast(f"Failed to send message: {str(e)}", "error")

    msgs = []

    try:
        msgs = (
            sb.table("messages")
            .select("*")
            .eq("user_id", u.get("email"))
            .order("created_at", desc=True)
            .limit(50)
            .execute()
            .data or []
        )
    except Exception:
        msgs = []

    if not msgs:
        st.info("No messages yet.")

    for m in msgs:
        mid = str(m.get("id", uuid.uuid4()))

        c1, c2, c3 = st.columns([0.5, 8, 1.5])

        with c1:
            star = "⭐" if m.get("is_starred") else "☆"

            if st.button(star, key=f"star_{mid}"):
                try:
                    if m.get("is_starred"):
                        content = unpack_message(m.get("compressed_payload")) if m.get("compressed_payload") else m.get("content", "")

                        sb.table("messages").update(
                            {
                                "is_starred": False,
                                "is_compressed": False,
                                "compressed_payload": None,
                                "content": content,
                            }
                        ).eq("id", m.get("id")).execute()
                    else:
                        payload = pack_message(m.get("content", ""))

                        sb.table("messages").update(
                            {
                                "is_starred": True,
                                "is_compressed": True,
                                "compressed_payload": payload,
                                "content": None,
                            }
                        ).eq("id", m.get("id")).execute()

                    st.rerun()
                except Exception as e:
                    show_toast(f"Failed to update message: {str(e)}", "error")

        with c2:
            if m.get("is_compressed") and m.get("compressed_payload"):
                st.write(unpack_message(m.get("compressed_payload")))
            else:
                st.write(m.get("content", ""))

        with c3:
            st.caption(str(m.get("created_at", ""))[:16]) 
            # ============================================================
# AI ASSISTANT PAGE
# ============================================================
def show_ai():
    render_back_button()

    st.markdown("### 🤖 AI Assistant")

    training_links = get_training_links()

    if training_links:
        st.caption(f"🎓 {len(training_links)} trusted training sources active")

    lang = st.selectbox(
        "Response Language",
        ["English", "Telugu", "Hindi"],
        key="ai_language",
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if p := st.chat_input("Ask..."):
        st.session_state.messages.append({"role": "user", "content": p})

        with st.chat_message("user"):
            st.markdown(p)

        with st.chat_message("assistant"):
            src = cascading_search(p, lang, 5)

            ctx = "Answer using only provided context and trusted sources.\n\n"

            if src:
                ctx += "".join(
                    [
                        f"- {s.get('filename', 'Source')}: {s.get('ai_summary', '')}\n"
                        for s in src
                    ]
                )
            else:
                ctx += "No internal sources found.\n"

            r = ai_system.request(ctx + f"\nQuestion: {p}", lang)

            resp = r.get("response") if r.get("success") else "AI unavailable. Add API keys in Admin Panel -> AI Settings."

            st.markdown(resp)
            st.session_state.messages.append({"role": "assistant", "content": resp})


# ============================================================
# SYSTEM HEALTH
# ============================================================
def show_system_health():
    st.markdown("### 🩺 System Health Check")

    cols = st.columns(4)

    with cols[0]:
        sb = globals().get("supabase")

        if sb:
            try:
                sb.table("users").select("id").limit(1).execute()
                st.success("✅ Supabase: Connected")
            except Exception:
                st.error("❌ Supabase: Down")
        else:
            st.warning("⚠️ Supabase: Not configured")

    with cols[1]:
        if redis_client:
            try:
                if hasattr(redis_client, "ping"):
                    redis_client.ping()
                else:
                    redis_client.get("health_check")

                st.success("✅ Redis: Connected")
            except Exception:
                st.error("❌ Redis: Down")
        else:
            st.warning("⚠️ Redis: Not configured")

    with cols[2]:
        storage_status = []

        if r2_client:
            try:
                r2_client.list_buckets()
                storage_status.append("✅ R2")
            except Exception:
                storage_status.append("❌ R2")

        if b2_client:
            try:
                b2_client.list_buckets()
                storage_status.append("✅ B2")
            except Exception:
                storage_status.append("❌ B2")

        if minio_client:
            try:
                minio_client.list_buckets()
                storage_status.append("✅ MinIO")
            except Exception:
                storage_status.append("❌ MinIO")

        st.info("Storage: " + (" | ".join(storage_status) or "❌ None"))

    with cols[3]:
        try:
            if qdrant_client:
                qdrant_client.get_collections()
                st.success("✅ Qdrant: Connected")
            else:
                st.warning("⚠️ Qdrant: Disabled")
        except Exception:
            st.error("❌ Qdrant: Down")


# ============================================================
# ADMIN PANEL
# ============================================================
def show_admin():
    u = st.session_state.user or {}

    if u.get("admin_level") not in ["system_admin", "office_admin"]:
        st.warning("Access denied")
        return

    render_back_button()

    st.markdown("### 🏛️ Admin Panel")

    section = st.radio(
        "Section",
        [
            "🩺 Health",
            "👥 Users",
            "⚙️ AI Settings",
            "🧠 AI Training",
            "📊 Storage & AI",
            "🔄 Maintenance",
            "📋 Audit",
            "🚨 Emergency",
            "📢 Announcements",
        ],
        horizontal=True,
        label_visibility="collapsed",
        key="admin_section",
    )

    RTA_DESIGNATIONS = [
        "Junior Assistant (Jr Asst)",
        "Senior Assistant (Sr Asst)",
        "Assistant Officer (AO)",
        "Regional Transport Officer (RTO)",
        "Deputy Transport Commissioner (DTC)",
        "Motor Vehicle Inspector (MVI)",
        "Assistant Motor Vehicle Inspector (AMVI)",
    ]

    SYSTEM_ACCESS_ROLES = [
        "staff",
        "office_admin",
        "system_admin",
    ]

    sb = globals().get("supabase")

    # --------------------------------------------------------
    # HEALTH
    # --------------------------------------------------------
    if section == "🩺 Health":
        st.markdown("#### 🩺 Health")

        if st.button("Check Health", key="hcheck"):
            show_system_health()

        st.divider()
        st.markdown("#### 📜 Recent Errors")

        if sb:
            try:
                errs = (
                    sb.table("audit_logs")
                    .select("*")
                    .eq("action", "error")
                    .gte("created_at", (now_utc() - timedelta(hours=24)).isoformat())
                    .order("created_at", desc=True)
                    .limit(20)
                    .execute()
                    .data or []
                )

                if not errs:
                    st.success("No errors in 24h!")

                for e in errs:
                    st.error(f"{e.get('resource_type', 'Unknown')} at {str(e.get('created_at', ''))[:16]}")
                    st.caption(str(e.get("metadata", ""))[:200])
            except Exception:
                st.warning("Could not read audit logs.")
        else:
            st.info("Supabase is not configured.")

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------
    elif section == "👥 Users":
        st.markdown("#### 👥 Users")

        st.info(
            "Passwords are stored as secure hashes. Admin cannot view existing passwords, "
            "but can reset them anytime."
        )

        with st.expander("➕ Add User"):
            with st.form("adduser"):
                ne = st.text_input("Email")
                nn = st.text_input("Name")
                nd = st.selectbox("RTA Designation", RTA_DESIGNATIONS)
                na = st.selectbox("System Access Role", SYSTEM_ACCESS_ROLES)
                npw = st.text_input("Password (leave blank to auto-generate)", type="password")

                if st.form_submit_button("Create"):
                    if not ne or not nn:
                        show_toast("Email and name required", "warning")
                    elif not validate_email(ne):
                        show_toast("Invalid email format", "error")
                    else:
                        pw = npw.strip() or secrets.token_urlsafe(10)

                        if len(pw) < 8:
                            show_toast("Password must be at least 8 characters", "error")
                        else:
                            if sb:
                                try:
                                    sb.table("users").insert(
                                        {
                                            "email": ne.strip().lower(),
                                            "name": nn,
                                            "designation": nd,
                                            "password_hash": hash_password(pw),
                                            "admin_level": na,
                                            "active": True,
                                        }
                                    ).execute()

                                    show_toast(f"Created user. Password: {pw}")
                                except Exception:
                                    show_toast("Failed to create user", "error")
                            else:
                                show_toast("Supabase not configured. Only local admin is available.", "warning")

        with st.expander("📥 Bulk Import CSV"):
            csvf = st.file_uploader("CSV columns: email,name,designation,admin_level,password", type=["csv"])

            if csvf and st.button("Import", key="bimp"):
                if not sb:
                    show_toast("Supabase not configured", "warning")
                else:
                    try:
                        df = pd.read_csv(csvf)
                        created = []

                        def csv_str(row, key):
                            v = row.get(key, "")
                            try:
                                if pd.isna(v):
                                    return ""
                            except Exception:
                                pass
                            return str(v).strip()

                        for _, row in df.iterrows():
                            email = csv_str(row, "email").lower()
                            name = csv_str(row, "name")
                            designation = csv_str(row, "designation") or "Staff"
                            admin_level = csv_str(row, "admin_level") or "staff"
                            password = csv_str(row, "password") or secrets.token_urlsafe(10)

                            if email and name and validate_email(email) and len(password) >= 8:
                                try:
                                    sb.table("users").insert(
                                        {
                                            "email": email,
                                            "name": name,
                                            "designation": designation,
                                            "password_hash": hash_password(password),
                                            "admin_level": admin_level,
                                            "active": True,
                                        }
                                    ).execute()

                                    created.append((email, password))
                                except Exception:
                                    pass

                        if created:
                            st.download_button(
                                "Download Passwords",
                                pd.DataFrame(created, columns=["Email", "Password"]).to_csv(index=False),
                                "passwords.csv",
                            )
                            show_toast(f"Created {len(created)} users")
                        else:
                            show_toast("No users created", "warning")
                    except Exception as e:
                        show_toast(f"Import failed: {e}", "error")

        st.divider()

        users = []

        if sb:
            try:
                users = (
                    sb.table("users")
                    .select("*")
                    .order("name")
                    .execute()
                    .data or []
                )
            except Exception:
                users = []
        else:
            local_admin = get_local_admin()
            users = [local_admin] if local_admin else []

        if not users:
            st.info("No users found.")

        for usr in users:
            usr_id = str(usr.get("id") or usr.get("email") or uuid.uuid4())

            c1, c2 = st.columns([3, 2])

            c1.write(
                f"{'🟢' if usr.get('active', True) else '🔴'} "
                f"**{usr.get('name', 'Unknown')}** ({usr.get('email', '')})"
            )

            c2.write(
                f"**{usr.get('designation', 'N/A')}** | Access: `{usr.get('admin_level', 'staff')}`"
            )

            with st.expander(f"⚙️ Manage {usr.get('name', 'User')}"):
                new_pass = st.text_input(
                    "Set New Password",
                    type="password",
                    key=f"np_{usr_id}",
                )

                if st.button("Update Password", key=f"up_{usr_id}"):
                    if len(new_pass) < 8:
                        show_toast("Password must be at least 8 characters", "error")
                    else:
                        if sb and usr.get("id"):
                            try:
                                sb.table("users").update(
                                    {"password_hash": hash_password(new_pass)}
                                ).eq("id", usr.get("id")).execute()

                                show_toast("Password updated")
                            except Exception:
                                show_toast("Password reset failed", "error")
                        else:
                            if save_local_admin(
                                usr.get("email", ""),
                                usr.get("name", "System Admin"),
                                new_pass,
                                usr.get("admin_level", "system_admin"),
                            ):
                                show_toast("Local admin password updated")
                            else:
                                show_toast("Password reset failed", "error")

                if st.button("Toggle Active Status", key=f"tg_{usr_id}"):
                    if sb and usr.get("id"):
                        try:
                            sb.table("users").update(
                                {"active": not usr.get("active", True)}
                            ).eq("id", usr.get("id")).execute()

                            if redis_client:
                                try:
                                    redis_client.delete(f"user_v2:{usr.get('email')}")
                                except Exception:
                                    pass

                            st.rerun()
                        except Exception:
                            show_toast("Toggle failed", "error")
                    else:
                        show_toast("Local admin toggle is not supported.", "warning")

    # --------------------------------------------------------
    # AI SETTINGS
    # --------------------------------------------------------
    elif section == "⚙️ AI Settings":
        st.markdown("#### ⚙️ AI API Settings")

        st.info(
            "Admin-controlled AI keys. These override secrets.toml and are saved in Supabase app_settings."
        )

        with st.form("ai_settings_form"):
            gemini_key = st.text_input(
                "Gemini API Key",
                value=get_setting("GEMINI_API_KEY"),
                type="password",
            )

            gemini_embed_key = st.text_input(
                "Gemini Embedding Key",
                value=get_setting("GEMINI_EMBEDDING_KEY"),
                type="password",
            )

            openai_key = st.text_input(
                "OpenAI API Key",
                value=get_setting("OPENAI_API_KEY"),
                type="password",
            )

            anthropic_key = st.text_input(
                "Anthropic API Key",
                value=get_setting("ANTHROPIC_API_KEY"),
                type="password",
            )

            serper_key = st.text_input(
                "Serper Web Search Key",
                value=get_setting("SERPER_API_KEY"),
                type="password",
            )

            if st.form_submit_button("💾 Save AI Settings"):
                set_setting("GEMINI_API_KEY", gemini_key)
                set_setting("GEMINI_EMBEDDING_KEY", gemini_embed_key)
                set_setting("OPENAI_API_KEY", openai_key)
                set_setting("ANTHROPIC_API_KEY", anthropic_key)
                set_setting("SERPER_API_KEY", serper_key)

                show_toast("AI settings saved")
                st.rerun()

    # --------------------------------------------------------
    # AI TRAINING LINKS
    # --------------------------------------------------------
    elif section == "🧠 AI Training":
        st.markdown("#### 🧠 AI Training Sources")

        links = get_training_links()

        st.info(f"Trusted Sources: {len(links)}/30")

        if len(links) < 30:
            with st.form("add_link_form"):
                url = st.text_input("Website URL", placeholder="https://aptransport.org")
                title = st.text_input("Title (Optional)")

                if st.form_submit_button("➕ Add Trusted Source"):
                    if url:
                        if add_training_link(url, title, u.get("email")):
                            show_toast("Trusted source added")
                            st.rerun()
                        else:
                            show_toast("Failed to add source", "error")
                    else:
                        show_toast("URL is required", "warning")
        else:
            st.warning("Maximum limit of 30 links reached. Delete an existing link to add a new one.")

        st.divider()

        if not links:
            st.info("No training links added yet.")

        for link in links:
            c1, c2 = st.columns([4, 1])

            c1.markdown(
                f"**{link.get('title', 'Untitled')}**  \n"
                f"🔗 {link.get('url', '')}  \n"
                f"*Domain: `{link.get('domain', '')}`*"
            )

            if c2.button("🗑️ Delete", key=f"del_link_{link.get('id')}"):
                if delete_training_link(link.get("id")):
                    show_toast("Source removed")
                    st.rerun()
                else:
                    show_toast("Delete failed", "error")

    # --------------------------------------------------------
    # STORAGE & AI METRICS
    # --------------------------------------------------------
    elif section == "📊 Storage & AI":
        st.markdown("#### 📊 Storage & AI Metrics")

        if sb:
            try:
                metrics = sb.table("system_metrics").select("*").execute().data or []

                def metric_val(name):
                    return int(
                        next(
                            (m.get("metric_value", 0) for m in metrics if m.get("metric_name") == name),
                            0,
                        )
                        or 0
                    )

                ai_req = metric_val("ai_requests_total")
                ai_tok = metric_val("ai_tokens_estimated")

                files = sb.table("files").select("compressed_size_bytes, storage_tier").execute().data or []

                used = sum(int(f.get("compressed_size_bytes", 0) or 0) for f in files)

                try:
                    quota = int(secret("STORAGE_QUOTA_BYTES", "5000000000"))
                except Exception:
                    quota = 5_000_000_000

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "💾 Storage Used",
                    f"{used / (1024 ** 3):.2f} GB",
                    f"Quota: {quota / (1024 ** 3):.1f} GB",
                )

                c1.progress(min(float(used / quota), 1.0) if quota > 0 else 0.0)

                c2.metric("🤖 AI Requests", f"{ai_req:,}")
                c3.metric("🔑 Estimated AI Tokens", f"{ai_tok:,}")

                hot_count = len([f for f in files if f.get("storage_tier") == "hot"])
                cold_count = len([f for f in files if f.get("storage_tier") == "cold"])

                st.caption(f"Files: {len(files)} | Hot: {hot_count} | Cold: {cold_count}")

            except Exception as e:
                st.error(f"Metrics failed: {e}")
        else:
            st.info("Supabase is not configured.")

    # --------------------------------------------------------
    # MAINTENANCE
    # --------------------------------------------------------
    elif section == "🔄 Maintenance":
        st.markdown("#### 🔄 Maintenance")

        if st.button("Reprocess Failed Documents", key="reproc"):
            if not sb:
                show_toast("Supabase not configured", "warning")
            else:
                try:
                    failed = (
                        sb.table("files")
                        .select("id")
                        .eq("processing_status", "failed")
                        .limit(10)
                        .execute()
                        .data or []
                    )

                    for d in failed:
                        text = storage_system.get_full_text(d.get("id"))

                        if text:
                            s = ai_system.summarize(text[:3000])

                            if s:
                                sb.table("files").update(
                                    {
                                        "ai_summary": s,
                                        "processing_status": "ready",
                                    }
                                ).eq("id", d.get("id")).execute()

                    show_toast(f"Reprocessed {len(failed)}")
                except Exception:
                    show_toast("Reprocess failed", "error")

        st.divider()
        st.markdown("##### ⏰ Scheduled Tasks")

        tasks = [
            ("cleanup_login", "Clean login attempts", "Daily"),
            ("auto_tier", "Auto-tier storage", "Weekly"),
            ("reset_stuck", "Reset stuck processing", "Hourly"),
            ("clean_sessions", "Clean expired sessions", "Daily"),
        ]

        for tid, tname, freq in tasks:
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{tname}** ({freq})")

            if c2.button("Run", key=f"t_{tid}"):
                if not sb:
                    show_toast("Supabase not configured", "warning")
                    continue

                with st.spinner("Running..."):
                    try:
                        if tid == "cleanup_login":
                            sb.table("login_attempts").delete().lt(
                                "created_at",
                                (now_utc() - timedelta(days=7)).isoformat(),
                            ).execute()

                        elif tid == "auto_tier":
                            auto_tier_documents()

                        elif tid == "reset_stuck":
                            stuck = (
                                sb.table("files")
                                .select("id")
                                .eq("processing_status", "pending")
                                .lt("uploaded_at", (now_utc() - timedelta(hours=1)).isoformat())
                                .execute()
                            )

                            if stuck.data:
                                sb.table("files").update(
                                    {"processing_status": "failed"}
                                ).in_(
                                    "id",
                                    [d.get("id") for d in stuck.data],
                                ).execute()

                        elif tid == "clean_sessions":
                            sb.table("sessions").delete().lt(
                                "expires_at",
                                now_utc().isoformat(),
                            ).execute()

                        show_toast("Done!")
                        st.rerun()
                    except Exception:
                        show_toast("Task failed", "error")

    # --------------------------------------------------------
    # AUDIT
    # --------------------------------------------------------
    elif section == "📋 Audit":
        st.markdown("#### 📋 Audit")

        if sb:
            try:
                logs = (
                    sb.table("audit_logs")
                    .select("*")
                    .order("created_at", desc=True)
                    .limit(50)
                    .execute()
                    .data or []
                )

                for log in logs:
                    st.caption(
                        f"{str(log.get('created_at', ''))[:16]} | "
                        f"{log.get('user_email', '')} | "
                        f"{log.get('action', '')}"
                    )
            except Exception:
                st.warning("Could not read audit logs.")
        else:
            st.info("Supabase is not configured.")

    # --------------------------------------------------------
    # EMERGENCY
    # --------------------------------------------------------
    elif section == "🚨 Emergency":
        st.markdown("#### 🚨 Emergency")

        maint = is_maintenance_mode()

        if not maint:
            if st.button("🔧 Enable Maintenance", type="secondary", key="mon"):
                set_maintenance_mode(True)
                show_toast("Maintenance ON", "warning")
                st.rerun()
        else:
            st.warning("⚠️ In maintenance")

            if st.button("✅ Disable Maintenance", key="moff"):
                set_maintenance_mode(False)
                show_toast("Maintenance OFF")
                st.rerun()

        st.divider()

        if st.button("🔒 Force Logout All", type="secondary", key="flog"):
            if sb:
                try:
                    sb.table("sessions").delete().neq("token_hash", "").execute()
                    show_toast("All sessions deleted", "warning")
                    st.rerun()
                except Exception:
                    show_toast("Could not delete sessions", "error")
            else:
                logout()

        if st.button("🗑️ Clear AI Cache", type="secondary", key="ccache"):
            if redis_client:
                try:
                    if hasattr(redis_client, "scan_iter"):
                        keys = redis_client.scan_iter("ai_cache:*")
                    else:
                        keys = redis_client.keys("ai_cache:*")

                    for k in keys:
                        redis_client.delete(k)

                    show_toast("Cache cleared")
                except Exception:
                    show_toast("Could not clear cache", "error")
            else:
                show_toast("Redis not configured", "warning")

    # --------------------------------------------------------
    # ANNOUNCEMENTS
    # --------------------------------------------------------
    elif section == "📢 Announcements":
        st.markdown("#### 📢 Announcements")

        if not sb:
            st.info("Supabase is not configured.")
        else:
            with st.form("ann"):
                title = st.text_input("Title")
                msg = st.text_area("Message", height=100)
                pri = st.selectbox("Priority", ["info", "warning", "critical"])
                dur = st.number_input("Days", 1, 30, 7)

                if st.form_submit_button("Broadcast"):
                    if title and msg:
                        try:
                            sb.table("announcements").insert(
                                {
                                    "title": title,
                                    "message": msg,
                                    "priority": pri,
                                    "expires_at": (now_utc() + timedelta(days=int(dur))).isoformat(),
                                    "created_by": u.get("email"),
                                }
                            ).execute()

                            show_toast("Posted!")
                            st.rerun()
                        except Exception:
                            show_toast("Failed to post announcement", "error")

            st.divider()

            try:
                anns = (
                    sb.table("announcements")
                    .select("*")
                    .gt("expires_at", now_utc().isoformat())
                    .order("created_at", desc=True)
                    .execute()
                    .data or []
                )

                for ann in anns:
                    c1, c2 = st.columns([4, 1])

                    icon = {
                        "info": "ℹ️",
                        "warning": "⚠️",
                        "critical": "🚨",
                    }.get(ann.get("priority", "info"), "ℹ️")

                    c1.write(f"{icon} **{ann.get('title', '')}**")
                    c1.caption(f"{str(ann.get('message', ''))[:100]}...")

                    if c2.button("🗑️", key=f"dann_{ann.get('id')}"):
                        try:
                            sb.table("announcements").delete().eq("id", ann.get("id")).execute()
                            st.rerun()
                        except Exception:
                            show_toast("Delete failed", "error")
            except Exception:
                pass


# ============================================================
# NAVIGATION
# ============================================================
def render_sidebar_nav():
    u = st.session_state.user or {}

    if "sidebar_open" not in st.session_state:
        st.session_state.sidebar_open = True

    # If sidebar is closed, show open button in main page
    if not st.session_state.sidebar_open:
        c1, _ = st.columns([1, 5])

        with c1:
            if st.button("☰ Open Sidebar", use_container_width=True, key="open_sidebar"):
                st.session_state.sidebar_open = True
                st.rerun()

        return

    with st.sidebar:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #0A66C2 0%, #004182 100%); padding: 16px; border-radius: 12px; color: white; margin-bottom: 20px;">
                <div style="font-size: 14px; opacity: 0.9;">Welcome,</div>
                <div style="font-size: 18px; font-weight: 700;">{str(u.get('name', 'User'))}</div>
                <div style="font-size: 12px; opacity: 0.8;">🏢 {str(u.get('office_name', 'Office'))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        menu_items = [
            "Feed",
            "Workspace",
            "Tapal",
            "Dispatch",
            "Documents",
            "Messages",
            "AI Assistant",
        ]

        menu_icons = [
            "house",
            "briefcase",
            "envelope-paper",
            "send",
            "file-earmark-text",
            "chat",
            "robot",
        ]

        if u.get("admin_level") in ["system_admin", "office_admin"]:
            menu_items.append("Admin Panel")
            menu_icons.append("gear")

        page_map = {
            "Feed": "feed",
            "Workspace": "workspace",
            "Tapal": "tapal",
            "Dispatch": "dispatch",
            "Documents": "documents",
            "Messages": "messages",
            "AI Assistant": "ai",
            "Admin Panel": "admin",
        }

        inverse_map = {v: k for k, v in page_map.items()}
        current_page = st.session_state.get("page", "feed")

        default_index = 0

        if current_page in inverse_map:
            try:
                default_index = menu_items.index(inverse_map[current_page])
            except Exception:
                default_index = 0

        selected = menu_items[default_index]

        om = globals().get("option_menu")

        if om is not None:
            try:
                selected = om(
                    "Navigation",
                    menu_items,
                    icons=menu_icons,
                    menu_icon="cast",
                    default_index=default_index,
                    styles={
                        "container": {"padding": "0!important", "background-color": "#fafafa"},
                        "icon": {"color": "#0A66C2", "font-size": "18px"},
                        "nav-link": {
                            "font-size": "15px",
                            "text-align": "left",
                            "margin": "2px 0",
                            "padding": "12px 16px",
                        },
                        "nav-link-selected": {
                            "background-color": "#0A66C2",
                            "color": "white",
                            "font-weight": "600",
                        },
                    },
                )
            except Exception:
                selected = st.radio("Navigation", menu_items, index=default_index)
        else:
            selected = st.radio("Navigation", menu_items, index=default_index)

        st.divider()

        if st.button("⬅️ Close Sidebar", use_container_width=True, key="close_sidebar"):
            st.session_state.sidebar_open = False
            st.rerun()

        logout_func = globals().get("logout")

        if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
            if logout_func:
                logout_func()
            else:
                st.session_state.clear()
                st.rerun()

    st.session_state.page = page_map.get(selected, "feed")


# ============================================================
# MAIN ENTRY POINT
# ============================================================
def main():
    if is_maintenance_mode():
        st.markdown(
            """
            <div style="text-align:center; padding:50px;">
                <h1>🔧 Under Maintenance</h1>
                <p>We're making improvements. Please check back soon.</p>
                <p><small>— RTA Anubandhan Team</small></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    init_session_state()
    bootstrap_env_admin()
    try_auto_login()

    if not st.session_state.logged_in:
        show_login()
        return

    try:
        cleanup_old_messages()
    except Exception:
        pass

    render_sidebar_nav()

    page = st.session_state.get("page", "feed")

    if page == "feed":
        show_feed()
    elif page == "workspace":
        show_workspace()
    elif page == "tapal":
        show_tapal()
    elif page == "dispatch":
        show_dispatch()
    elif page == "documents":
        show_documents()
    elif page == "messages":
        show_messages()
    elif page == "ai":
        show_ai()
    elif page == "admin":
        show_admin()
    else:
        show_feed()


if __name__ == "__main__":
    main()
