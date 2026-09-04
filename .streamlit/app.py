"""
RTA ANUBANDHAN — Enterprise Production Final v2.0
==================================================
COMPLETE DOCUMENT-FIRST AI SYSTEM
✅ Multi-AI with Circuit Breakers + Multi-Account Rotation
✅ Document Upload → Extract → Store → Search → Answer
✅ Hot/Cold Storage Tiering (R2/B2)
✅ Semantic Search (Qdrant) + Keyword + Fuzzy
✅ Redis + Semantic Caching
✅ Maintenance Mode with Admin Bypass
✅ Compression + Encryption
✅ Rate Limiting + Audit Logging
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

# ═══════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# OPTIONAL IMPORTS (Graceful degradation)
# ═══════════════════════════════════════════════════════════
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
    import lzma
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

# ═══════════════════════════════════════════════════════════
# SENTRY (Optional)
# ═══════════════════════════════════════════════════════════
if SENTRY_AVAILABLE and os.getenv("SENTRY_DSN"):
    try:
        sentry_sdk.init(
            dsn=os.getenv("SENTRY_DSN"),
            traces_sample_rate=0.2,
            environment=os.getenv("ENVIRONMENT", "production"),
        )
    except Exception as e:
        logger.error(f"Sentry init failed: {e}")

# ═══════════════════════════════════════════════════════════
# PAGE CONFIG + CSS
# ═══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="RTA Anubandhan",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
    --success: #059669;
    --warning: #D97706;
    --danger: #DC2626;
}
body, .stApp {
    background-color: var(--bg-canvas) !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--text-primary) !important;
}
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
header[data-testid="stHeader"] {
    background: transparent !important;
    height: 2.5rem !important;
}
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    color: var(--primary) !important;
}
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 100px !important;
    max-width: 1200px;
}
.commercial-card {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: var(--shadow-sm);
    transition: box-shadow 0.2s;
}
.commercial-card:hover { box-shadow: var(--shadow-md); }
.post-avatar {
    width: 48px; height: 48px; border-radius: 50%;
    background: var(--primary); color: white; display: flex;
    align-items: center; justify-content: center;
    font-size: 20px; font-weight: 700;
}
.login-container {
    max-width: 420px; margin: 40px auto; padding: 30px;
    background: white; border-radius: 16px; box-shadow: var(--shadow-md);
}
.quote-box {
    background: var(--primary-light); border-radius: 12px;
    padding: 20px; margin: 20px 0; text-align: center;
}
.empty-state { text-align: center; padding: 50px; color: #666; }
.post-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.post-actions {
    display: flex; gap: 12px; margin-top: 16px;
    padding-top: 12px; border-top: 1px solid var(--border); flex-wrap: wrap;
}
.comment-item { padding: 12px; background: var(--bg-canvas); border-radius: 8px; margin-bottom: 8px; }
.pinned-badge {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
    color: white; padding: 4px 12px; border-radius: 12px;
    font-size: 12px; font-weight: 600; display: inline-block; margin-bottom: 8px;
}
.announcement-card {
    background: linear-gradient(135deg, #e8f0fe 0%, #d2e3fc 100%);
    border: 2px solid var(--primary); border-radius: 12px;
    padding: 20px; margin-bottom: 16px;
}
.tag-badge {
    background: var(--primary-light); color: var(--primary);
    padding: 2px 8px; border-radius: 8px; font-size: 12px; margin-right: 4px;
}
.status-badge {
    padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;
}
.status-ready { background: #D1FAE5; color: #065F46; }
.status-processing { background: #FEF3C7; color: #92400E; }
.status-failed { background: #FEE2E2; color: #991B1B; }
@media print {
    #MainMenu, footer, header, .stSidebar { display: none !important; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# CORE UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════

def secret(key: str, default: str = "") -> str:
    """Get secret from Streamlit secrets or environment variables."""
    try:
        val = st.secrets.get(key, default)
        if val not in (None, ""):
            return str(val)
    except Exception:
        pass
    return os.getenv(key, default)


def get_setting(key: str, default: str = "") -> str:
    """Get setting from session state, Supabase, or environment."""
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
            try:
                sb.table("app_settings").insert({
                    "key": key,
                    "value": default,
                    "updated_at": now_utc().isoformat()
                }).execute()
            except Exception:
                pass
    return secret(key, default)


def set_setting(key: str, value: str) -> bool:
    """Save setting to session state and Supabase."""
    st.session_state[f"setting_{key}"] = value
    sb = globals().get("supabase")
    if not sb:
        return False
    try:
        existing = sb.table("app_settings").select("id").eq("key", key).execute()
        if existing.data:
            sb.table("app_settings").update({
                "value": value,
                "updated_at": now_utc().isoformat()
            }).eq("key", key).execute()
        else:
            sb.table("app_settings").insert({
                "key": key,
                "value": value,
                "updated_at": now_utc().isoformat()
            }).execute()
        return True
    except Exception as e:
        logger.error(f"Failed to save setting {key}: {e}")
        st.session_state["_last_setting_error"] = str(e)
        return False


def sanitize_input(text: str) -> str:
    """Remove HTML tags and escape special characters."""
    if not text:
        return ""
    text = re.sub(r"<[^>]*>", "", str(text))
    return html.escape(text).strip()


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, str(email or "").strip()))


def now_utc() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def sanitize_search_query(q: str) -> str:
    """Sanitize search query to prevent injection."""
    return re.sub(r"[^a-zA-Z0-9\s@#]", "", str(q or "")).strip()


def generate_file_hash(file_data: bytes) -> str:
    """Generate SHA-256 hash of file content."""
    if isinstance(file_data, str):
        file_data = file_data.encode("utf-8", "ignore")
    return hashlib.sha256(file_data or b"").hexdigest()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    filename = os.path.basename(str(filename or "file"))
    filename = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)
    parts = filename.split(".")
    if len(parts) > 2:
        filename = parts[0] + "." + parts[-1]
    return filename[:200] or "file"


def show_toast(message: str, type: str = "success"):
    """Show toast notification."""
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
    """Log error to audit_logs table."""
    sb = globals().get("supabase")
    if not sb:
        return
    try:
        sb.table("audit_logs").insert({
            "user_email": st.session_state.get("user", {}).get("email", "system"),
            "action": "error",
            "resource_type": str(error_type),
            "metadata": json.dumps({"message": str(message)[:500]}),
            "created_at": now_utc().isoformat(),
        }).execute()
    except Exception as e:
        logger.error(f"Failed to log error: {e}")


def audit_log(email, action, rtype, rid=None, meta=None):
    """Log audit trail entry."""
    sb = globals().get("supabase")
    if not sb:
        return
    try:
        sb.table("audit_logs").insert({
            "user_email": email,
            "action": action,
            "resource_type": rtype,
            "resource_id": str(rid) if rid else None,
            "metadata": json.dumps(meta or {}),
            "created_at": now_utc().isoformat(),
        }).execute()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
# ENCRYPTION
# ═══════════════════════════════════════════════════════════

def get_fernet():
    """Initialize Fernet encryption from key."""
    if not CRYPTO_AVAILABLE:
        return None
    key = secret("ENCRYPTION_KEY", "")
    if not key:
        return None
    key_bytes = hashlib.sha256(key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(key_bytes))


_fernet = get_fernet()
if os.getenv("ENVIRONMENT", "development") == "production" and not _fernet:
    logger.warning("Encryption key missing in production. Data will not be encrypted.")


def encrypt_data(data: bytes) -> bytes:
    """Encrypt data with Fernet."""
    if _fernet:
        try:
            return _fernet.encrypt(data)
        except Exception:
            pass
    return data


def decrypt_data(data: bytes) -> bytes:
    """Decrypt data with Fernet."""
    if _fernet:
        try:
            return _fernet.decrypt(data)
        except Exception:
            pass
    return data


# ═══════════════════════════════════════════════════════════
# COMPRESSION
# ═══════════════════════════════════════════════════════════

def compress_data(data: bytes) -> Tuple[bytes, str]:
    """Compress data using best available method (zstd > lzma > none)."""
    if ZSTD_AVAILABLE:
        try:
            compressed = zstd.ZstdCompressor(level=12).compress(data)
            if len(compressed) < len(data):
                return compressed, "zstd"
        except Exception as e:
            logger.warning(f"Zstd compression failed: {e}")
    if COMPRESSION_AVAILABLE:
        try:
            compressed = lzma.compress(data, preset=6)
            if len(compressed) < len(data):
                return compressed, "lzma"
        except Exception as e:
            logger.warning(f"LZMA compression failed: {e}")
    return data, "none"


def decompress_data(data: bytes, method: str) -> bytes:
    """Decompress data based on method."""
    if method == "zstd" and ZSTD_AVAILABLE:
        try:
            return zstd.ZstdDecompressor().decompress(data)
        except Exception:
            pass
    elif method == "lzma" and COMPRESSION_AVAILABLE:
        try:
            return lzma.decompress(data)
        except Exception:
            pass
    return data


# ═══════════════════════════════════════════════════════════
# CIRCUIT BREAKER
# ═══════════════════════════════════════════════════════════

class CircuitBreaker:
    """Prevents cascading failures by tracking provider errors."""

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


# ═══════════════════════════════════════════════════════════
# BUSINESS METRICS
# ═══════════════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════════════
# SERVICE INITIALIZATION
# ═══════════════════════════════════════════════════════════

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
    except Exception:
        return None


@st.cache_resource
def init_r2():
    if not BOTO_AVAILABLE:
        return None
    try:
        acc = secret("R2_ACCOUNT_ID")
        ak = secret("R2_ACCESS_KEY_ID")
        sk = secret("R2_SECRET_ACCESS_KEY")
        if not all([acc, ak, sk]):
            return None
        return boto3.client(
            "s3",
            endpoint_url=f"https://{acc}.r2.cloudflarestorage.com",
            aws_access_key_id=ak,
            aws_secret_access_key=sk,
            region_name="auto",
        )
    except Exception:
        return None


@st.cache_resource
def init_b2():
    """B2 Cold Storage via S3-compatible API."""
    if not BOTO_AVAILABLE:
        return None
    try:
        key_id = secret("B2_KEY_ID")
        app_key = secret("B2_APPLICATION_KEY")
        region = secret("B2_REGION", "us-west-002")
        if not key_id or not app_key:
            return None
        return boto3.client(
            "s3",
            endpoint_url=f"https://s3.{region}.backblazeb2.com",
            aws_access_key_id=key_id,
            aws_secret_access_key=app_key,
            region_name=region,
        )
    except Exception:
        return None
@st.cache_resource
def init_storj():
    """Storj decentralized storage via S3-compatible API."""
    if not BOTO_AVAILABLE:
        return None
    try:
        access_key = secret("STORJ_ACCESS_KEY")
        secret_key = secret("STORJ_SECRET_KEY")
        if not access_key or not secret_key:
            return None
        return boto3.client(
            "s3",
            endpoint_url="https://gateway.storjshare.io",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="global",
        )
    except Exception as e:
        logger.warning(f"Storj init failed: {e}")
        return None

@st.cache_resource
def init_minio():
    """MinIO for local processing and caching on VPS."""
    try:
        from minio import Minio
        endpoint = secret("MINIO_ENDPOINT", "localhost:9000")
        access_key = secret("MINIO_ACCESS_KEY", "minioadmin")
        secret_key = secret("MINIO_SECRET_KEY", "minioadmin")
        
        client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False,
        )
        
        bucket_name = secret("MINIO_BUCKET", "processing")
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
        
        return client
    except Exception as e:
        logger.warning(f"MinIO init failed: {e}")
        return None

@st.cache_resource
def init_d1():
    """Cloudflare D1 via HTTP API for edge caching."""
    try:
        account_id = secret("CF_ACCOUNT_ID")
        database_id = secret("D1_DATABASE_ID")
        api_token = secret("CF_API_TOKEN")
        if not all([account_id, database_id, api_token]):
            return None
        
        class D1Client:
            def __init__(self, account_id, database_id, api_token):
                self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{database_id}"
                self.headers = {
                    "Authorization": f"Bearer {api_token}",
                    "Content-Type": "application/json",
                }
            
            def query(self, sql, params=None):
                try:
                    r = requests.post(
                        f"{self.base_url}/query",
                        headers=self.headers,
                        json={"sql": sql, "params": params or []},
                        timeout=10,
                    )
                    if r.status_code == 200:
                        return r.json().get("result", [])
                    return []
                except Exception as e:
                    logger.warning(f"D1 query failed: {e}")
                    return []
            
            def execute(self, sql, params=None):
                return self.query(sql, params)
        
        return D1Client(account_id, database_id, api_token)
    except Exception as e:
        logger.warning(f"D1 init failed: {e}")
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
        for col in ["rta_documents", "ai_semantic_cache"]:
            try:
                client.get_collection(col)
            except Exception:
                client.create_collection(
                    collection_name=col,
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
                )
        return client
    except Exception:
        return None


# Initialize all services
supabase = init_supabase()
redis_client = init_redis()
r2_client = init_r2()
b2_client = init_b2()
qdrant_client = init_qdrant() 
# ═══════════════════════════════════════════════════════════
# ADMIN USER INITIALIZATION
# ═══════════════════════════════════════════════════════════

def ensure_admin_user():
    """
    Ensure admin user exists in Supabase.
    Creates admin from secrets if not present.
    """
    if not supabase:
        logger.warning("Supabase not available for admin initialization")
        return False
    
    try:
        # Get admin credentials from secrets
        admin_email = secret("ADMIN_EMAIL", "")
        admin_password = secret("ADMIN_PASSWORD", "")
        admin_name = secret("ADMIN_NAME", "System Admin")
        admin_designation = secret("ADMIN_DESIGNATION", "System Administrator")
        admin_level = secret("ADMIN_LEVEL", "system_admin")
        admin_office = secret("ADMIN_OFFICE", "Head Office")
        admin_section = secret("ADMIN_SECTION", "IT")
        admin_seat = secret("ADMIN_SEAT", "ADMIN-01")
        
        if not admin_email or not admin_password:
            logger.warning("Admin credentials not configured in secrets")
            return False
        
        # Check if admin exists
        existing = (
            supabase.table("users")
            .select("id, email")
            .eq("email", admin_email.lower().strip())
            .execute()
        )
        
        if existing.data:
            logger.info(f"Admin user already exists: {admin_email}")
            # Update admin password if needed (optional)
            # supabase.table("users").update({
            #     "password_hash": hash_password(admin_password)
            # }).eq("email", admin_email).execute()
            return True
        
        # Create admin user
        result = (
            supabase.table("users")
            .insert({
                "email": admin_email.lower().strip(),
                "name": admin_name,
                "designation": admin_designation,
                "office_name": admin_office,
                "section": admin_section,
                "seat_number": admin_seat,
                "password_hash": hash_password(admin_password),
                "admin_level": admin_level,
                "active": True,
                "created_at": now_utc().isoformat(),
            })
            .execute()
        )
        
        if result.data:
            logger.info(f"Admin user created: {admin_email}")
            
            # Log admin creation
            audit_log(
                admin_email,
                "admin.initialize",
                "user",
                result.data[0].get("id"),
                {"source": "secrets"}
            )
            
            return True
        else:
            logger.error("Failed to create admin user")
            return False
            
    except Exception as e:
        logger.error(f"Admin initialization failed: {e}")
        return False


# ═══════════════════════════════════════════════════════════
# BULK USER INITIALIZATION (Optional)
# ═══════════════════════════════════════════════════════════

def ensure_default_users():
    """
    Create default users from secrets if configured.
    Format: DEFAULT_USERS_JSON in secrets
    """
    default_users = secret("DEFAULT_USERS_JSON", "")
    if not default_users or not supabase:
        return
    
    try:
        import json as json_lib
        users_list = json_lib.loads(default_users)
        
        for user_data in users_list:
            email = user_data.get("email", "").lower().strip()
            name = user_data.get("name", "")
            
            if not email or not name:
                continue
            
            # Check if exists
            existing = (
                supabase.table("users")
                .select("id")
                .eq("email", email)
                .execute()
            )
            
            if existing.data:
                continue
            
            # Create user
            supabase.table("users").insert({
                "email": email,
                "name": name,
                "designation": user_data.get("designation", "Staff"),
                "office_name": user_data.get("office_name", ""),
                "section": user_data.get("section", ""),
                "seat_number": user_data.get("seat_number", ""),
                "password_hash": hash_password(user_data.get("password", "Default@123")),
                "admin_level": user_data.get("admin_level", "staff"),
                "active": True,
                "created_at": now_utc().isoformat(),
            }).execute()
            
            logger.info(f"Created default user: {email}")
            
    except Exception as e:
        logger.error(f"Default users initialization failed: {e}")

# ═══════════════════════════════════════════════════════════
# COOKIE MANAGEMENT
# ═══════════════════════════════════════════════════════════

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
        _raw_cookies = CookieController()
    except Exception:
        _raw_cookies = None

    class SafeCookies:
        def __init__(self, inner):
            self.inner = inner

        def get(self, name):
            try:
                if self.inner and hasattr(self.inner, "get"):
                    val = self.inner.get(name)
                    if val and isinstance(val, str) and len(val) > 5:
                        return val
            except Exception:
                pass
            return None

        def set(self, name, value, max_age=None):
            try:
                if self.inner and hasattr(self.inner, "set"):
                    if max_age:
                        self.inner.set(name, value, max_age=max_age)
                    else:
                        self.inner.set(name, value)
                    return
            except Exception:
                pass
            st.session_state[f"_cookie_{name}"] = value

        def delete(self, name):
            try:
                if self.inner and hasattr(self.inner, "delete"):
                    self.inner.delete(name)
                    return
            except Exception:
                pass
            st.session_state.pop(f"_cookie_{name}", None)

    cookies = SafeCookies(_raw_cookies)
else:
    cookies = DummyCookieController() 
# ═══════════════════════════════════════════════════════════
# MULTI-ACCOUNT KEY HELPER (Used by Embeddings + MultiAI)
# ═══════════════════════════════════════════════════════════

def get_multi_keys(setting_name: str, secret_name: str = "") -> List[str]:
    """
    Supports comma-separated keys for multi-account rotation.
    Admin can paste: "sk-key1, sk-key2, sk-key3" in AI Settings.
    """
    val = get_setting(setting_name)
    if not val and secret_name:
        val = secret(secret_name)
    if not val:
        return []
    return [k.strip() for k in str(val).split(",") if k.strip()]


# ═══════════════════════════════════════════════════════════
# STORAGE SYSTEM (Hot R2 / Cold B2 / Supabase fallback)
# ═══════════════════════════════════════════════════════════

class StorageSystem:
    """
    Tiered storage architecture:
      HOT  (R2)       → Recent/frequently accessed documents
      COLD (B2)       → Archives (>90 days, rarely accessed)
      FALLBACK        → Supabase Storage if R2/B2 unavailable
    """

    def __init__(self):
    self.r2 = r2_client
    self.b2 = b2_client
    self.storj = storj_client
    self.minio = minio_client
    self.d1 = d1_client
    
    self.hot_bucket = secret("R2_BUCKET_NAME", "rta-hot-storage")
    self.cold_bucket = secret("B2_BUCKET_NAME", "rta-cold-storage")
    self.archive_bucket = secret("STORJ_BUCKET_NAME", "rta-archive")
    self.processing_bucket = secret("MINIO_BUCKET", "processing")
    self.fallback_bucket = secret("SUPABASE_BUCKET", "rta-fallback") 
    def backup_document(self, file_data: bytes, key: str, primary_tier: str) -> dict:
    """Create redundant backups across multiple providers."""
    backup_results = {}
    
    if primary_tier != "cold":
        backup_results['b2'] = self._upload_to_storage(file_data, key, "cold")
    
    if primary_tier in ["hot", "cold"]:
        backup_results['storj'] = self._upload_to_storage(file_data, key, "archive")
    
    return backup_results

    # ─── UPLOAD ────────────────────────────────────────────
    def _upload_to_storage(self, data: bytes, key: str, target_tier: str) -> Optional[str]:
    # ARCHIVE TIER → Storj
    if target_tier == "archive" and self.storj:
        try:
            self.storj.put_object(Bucket=self.archive_bucket, Key=key, Body=data)
            return "archive"
        except Exception as e:
            logger.warning(f"Storj archive upload failed: {e}")

    # PROCESSING TIER → MinIO
    if target_tier == "processing" and self.minio:
        try:
            import io as _io
            self.minio.put_object(
                self.processing_bucket,
                key,
                _io.BytesIO(data),
                length=len(data),
            )
            return "processing"
        except Exception as e:
            logger.warning(f"MinIO processing upload failed: {e}")
    
    # ... rest of existing code continues here
    def _upload_to_storage(self, data: bytes, key: str, target_tier: str) -> Optional[str]:
        """Upload to preferred tier with automatic fallback chain."""
        if target_tier == "cold" and self.b2:
            try:
                self.b2.put_object(Bucket=self.cold_bucket, Key=key, Body=data)
                return "cold"
            except Exception as e:
                logger.warning(f"B2 cold upload failed: {e}")

        if target_tier == "hot" and self.r2:
            try:
                self.r2.put_object(Bucket=self.hot_bucket, Key=key, Body=data)
                return "hot"
            except Exception as e:
                logger.warning(f"R2 hot upload failed: {e}")

        # Fallback: try whichever cloud is available
        if self.r2:
            try:
                self.r2.put_object(Bucket=self.hot_bucket, Key=key, Body=data)
                return "hot"
            except Exception:
                pass

        sb = globals().get("supabase")
        if sb:
            try:
                try:
                    sb.storage.from_(self.hot_bucket).upload(
                        key, data, file_options={"upsert": True}
                    )
                except Exception:
                    sb.storage.create_bucket(self.hot_bucket, {"public": False})
                    sb.storage.from_(self.hot_bucket).upload(
                        key, data, file_options={"upsert": True}
                    )
                return "supabase"
            except Exception as e:
                logger.warning(f"Supabase Storage upload failed: {e}")

        return None

    # ─── DOWNLOAD ──────────────────────────────────────────
    def _download_from_storage(self, key: str, tier: str) -> Optional[bytes]:
        """Download from recorded tier with automatic fallback chain."""
        if tier == "hot" and self.r2:
            try:
                return self.r2.get_object(Bucket=self.hot_bucket, Key=key)["Body"].read()
            except Exception:
                pass

        if tier == "cold" and self.b2:
            try:
                return self.b2.get_object(Bucket=self.cold_bucket, Key=key)["Body"].read()
            except Exception:
                pass

        if tier == "supabase":
            sb = globals().get("supabase")
            if sb:
                try:
                    return sb.storage.from_(self.hot_bucket).download(key)
                except Exception:
                    pass

        # Fallback: try all locations
        if self.r2:
            try:
                return self.r2.get_object(Bucket=self.hot_bucket, Key=key)["Body"].read()
            except Exception:
                pass
        if self.b2:
            try:
                return self.b2.get_object(Bucket=self.cold_bucket, Key=key)["Body"].read()
            except Exception:
                pass
        sb = globals().get("supabase")
        if sb:
            try:
                return sb.storage.from_(self.hot_bucket).download(key)
            except Exception:
                pass

        return None
    def _download_from_storage(self, key: str, tier: str) -> Optional[bytes]:
    # Add after existing tier checks:
    
    if tier == "archive" and self.storj:
        try:
            return self.storj.get_object(Bucket=self.archive_bucket, Key=key)["Body"].read()
        except Exception:
            pass
    
    if tier == "processing" and self.minio:
        try:
            response = self.minio.get_object(self.processing_bucket, key)
            return response.read()
        except Exception:
            pass
    
    # Add to fallback chain (after existing B2 fallback):
    if self.storj:
        try:
            return self.storj.get_object(Bucket=self.archive_bucket, Key=key)["Body"].read()
        except Exception:
            pass
    
    if self.minio:
        try:
            response = self.minio.get_object(self.processing_bucket, key)
            return response.read()
        except Exception:
            pass
    
    # ... rest of existing code

    # ─── PRESIGNED URL ─────────────────────────────────────
    def get_presigned_url(self, key: str, tier: str, expiration: int = 3600) -> Optional[str]:
        try:
            if tier == "hot" and self.r2:
                return self.r2.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.hot_bucket, "Key": key},
                    ExpiresIn=expiration,
                )
            if tier == "cold" and self.b2:
                return self.b2.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.cold_bucket, "Key": key},
                    ExpiresIn=expiration,
                )
            if tier == "supabase":
                sb = globals().get("supabase")
                if sb:
                    res = sb.storage.from_(self.hot_bucket).create_signed_url(key, expiration)
                    return res.get("signedURL")
        except Exception:
            pass
        return None

    # ─── TEXT EXTRACTION (PDF + OCR) ───────────────────────
    def _extract_text(self, file_data: bytes, filename: str, page_limit: int = 15) -> str:
        """
        Extract text from PDF/Image.
        page_limit keeps UI responsive — full document is processed in background.
        """
        ext = filename.lower().split(".")[-1] if "." in filename else ""
        text = ""

        if ext == "pdf" and PDF_AVAILABLE:
            try:
                reader = pypdf.PdfReader(io.BytesIO(file_data))
                pages = reader.pages[:page_limit]
                text = "".join([(p.extract_text() or "") + "\n" for p in pages])

                # Scanned PDF → OCR fallback
                if len(text.strip()) < 50 and PDF2IMAGE_AVAILABLE and OCR_AVAILABLE:
                    try:
                        images = convert_from_bytes(file_data, dpi=150, first_page=1, last_page=min(5, len(reader.pages)))
                        for img in images:
                            gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
                            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
                            text += pytesseract.image_to_string(thresh) + "\n"
                    except Exception as e:
                        logger.warning(f"PDF OCR fallback failed: {e}")
            except Exception as e:
                logger.warning(f"PDF extraction failed: {e}")

        elif ext in ["jpg", "jpeg", "png", "bmp", "tiff"] and OCR_AVAILABLE:
            try:
                img = Image.open(io.BytesIO(file_data)).convert("RGB")
                gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
                _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
                text = pytesseract.image_to_string(thresh)
            except Exception as e:
                logger.warning(f"Image OCR failed: {e}")

        return text.strip()

    # ─── UPLOAD DOCUMENT (Document-First Architecture) ─────
    def upload_document(self, file_data: bytes, filename: str, doc_type: str, user_email: str) -> dict:
        """
        DOCUMENT-FIRST FLOW:
        Upload → Extract → Store (R2 + Supabase + Qdrant) → Searchable

        BUG FIX: Text extraction is now SYNCHRONOUS (first 15 pages) so
        search works IMMEDIATELY. AI summary + embeddings run in background.
        """
        try:
            if not file_data:
                return {"success": False, "error": "Empty file"}

            filename = sanitize_filename(filename)
            file_hash = generate_file_hash(file_data)

            # ── Duplicate detection ──
            if supabase:
                try:
                    dup = (
                        supabase.table("documents")
                        .select("id")
                        .eq("file_hash", file_hash)
                        .limit(1)
                        .execute()
                    )
                    if dup.data:
                        return {
                            "success": True,
                            "duplicate": True,
                            "document_id": dup.data[0]["id"],
                            "message": "This file was already uploaded",
                        }
                except Exception:
                    pass

            # ── Compress → Encrypt → Store binary ──
            compressed_file, method = compress_data(file_data)
            encrypted_file = encrypt_data(compressed_file)
            storage_key = f"blobs/{file_hash[:2]}/{file_hash[2:4]}/{file_hash}"

            target_tier = "hot" if doc_type in ["circular", "tapal", "current", "social_post"] else "cold"
            actual_tier = self._upload_to_storage(encrypted_file, storage_key, target_tier) 
            # Create multi-cloud backups for critical documents
backup_tiers = {}
if doc_type in ["circular", "tapal"]:  # Critical documents
    backup_tiers = self.backup_document(encrypted_file, storage_key, actual_tier)

            if not actual_tier:
                return {"success": False, "error": "All storage backends failed"}

            # ── Create database record ──
            doc_id = None
            if supabase:
                try:
                    result = supabase.table("documents").insert({
                        "filename": filename,
                        "file_key": storage_key,
                        "file_hash": file_hash,
                        "doc_type": doc_type,
                        "compression_method": method,
                        "original_size": len(file_data),
                        "compressed_size": len(encrypted_file),
                        "storage_tier": actual_tier,
                        "uploaded_by": user_email,
                        "uploaded_at": now_utc().isoformat(),
                        "access_count": 0,
                        "last_accessed": now_utc().isoformat(),
                        "processing_status": "processing",
                    }).execute()
                    if result.data:
                        doc_id = result.data[0]["id"]
                except Exception as e:
                    logger.error(f"Document DB insert failed: {e}")

            audit_log(user_email, "document.upload", "document", doc_id, {"filename": filename})
            business_metrics.increment("documents_uploaded")

            # ── SYNCHRONOUS text extraction (guarantees search works) ──
            extracted_text = ""
            if doc_id:
                extracted_text = self._extract_text(file_data, filename, page_limit=15)

                if extracted_text:
                    # Store compressed text copy for full-text retrieval
                    text_key = None
                    try:
                        ct, tm = compress_data(extracted_text.encode("utf-8", "ignore"))
                        text_key = f"text/{doc_type}/{now_utc().strftime('%Y/%m/%d')}/{uuid.uuid4().hex}.txt.{tm}"
                        self._upload_to_storage(ct, text_key, "hot")
                    except Exception as e:
                        logger.warning(f"Text storage failed: {e}")

                    # Save to Supabase IMMEDIATELY → search works instantly
                    try:
                        supabase.table("documents").update({
                            "text_key": text_key,
                            "full_text_preview": extracted_text[:50000],
                            "processing_status": "ready",
                        }).eq("id", doc_id).execute()
                    except Exception as e:
                        logger.error(f"Failed to save extracted text: {e}")

                    # ── BACKGROUND: AI summary + Qdrant embedding ──
                    def bg_ai_task(did, text, fn, dtype):
                        try:
                            ai = globals().get("ai_system")
                            if ai and len(text) > 50:
                                summary = ai.summarize(text[:3000])
                                if summary and supabase:
                                    supabase.table("documents").update(
                                        {"ai_summary": summary}
                                    ).eq("id", did).execute()

                            if QDRANT_AVAILABLE and qdrant_client:
                                gen = globals().get("generate_embedding")
                                if gen:
                                    vec = gen(text[:4000])
                                    if any(vec):  # skip zero vectors
                                        qdrant_client.upsert(
                                            collection_name="rta_documents",
                                            points=[PointStruct(
                                                id=str(did),
                                                vector=vec,
                                                payload={"doc_id": str(did), "filename": fn, "doc_type": dtype},
                                            )],
                                        )
                        except Exception as e:
                            logger.error(f"Background AI task failed: {e}")

                    threading.Thread(
                        target=bg_ai_task,
                        args=(doc_id, extracted_text, filename, doc_type),
                        daemon=True,
                    ).start()
                else:
                    # No text extracted (e.g., encrypted PDF) → still mark ready
                    try:
                        supabase.table("documents").update(
                            {"processing_status": "ready"}
                        ).eq("id", doc_id).execute()
                    except Exception:
                        pass

            ratio = max(0.0, 1 - (len(encrypted_file) / len(file_data))) if file_data else 0
            return {"success": True, "document_id": doc_id, "compression_ratio": ratio}

        except Exception as e:
            log_error("upload_failed", e)
            return {"success": False, "error": str(e)}

    # ─── DOWNLOAD DOCUMENT ─────────────────────────────────
    def download_document(self, document_id: str) -> Optional[bytes]:
        """Fetch → Decrypt → Decompress → Original file."""
        try:
            if not supabase:
                return None

            result = (
                supabase.table("documents")
                .select("file_key, storage_tier, compression_method, access_count")
                .eq("id", document_id)
                .execute()
            )
            if not result.data:
                return None

            doc = result.data[0]
            data = self._download_from_storage(doc["file_key"], doc.get("storage_tier", "hot"))
            if not data:
                return None

            # Track access count (used for auto-tiering)
            try:
                count = int(doc.get("access_count", 0) or 0)
                supabase.table("documents").update({
                    "access_count": count + 1,
                    "last_accessed": now_utc().isoformat(),
                }).eq("id", document_id).execute()
            except Exception:
                pass

            business_metrics.increment("documents_downloaded")
            return decompress_data(decrypt_data(data), doc.get("compression_method", "none"))

        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None

    # ─── GET FULL TEXT ─────────────────────────────────────
    def get_full_text(self, document_id: str) -> str:
        """Retrieve full extracted text from text storage."""
        try:
            if not supabase:
                return ""
            result = (
                supabase.table("documents")
                .select("text_key, full_text_preview")
                .eq("id", document_id)
                .execute()
            )
            if not result.data:
                return ""

            row = result.data[0]
            if row.get("text_key"):
                key = row["text_key"]
                method = "none"
                if key.endswith(".lzma"):
                    method = "lzma"
                elif key.endswith(".zstd"):
                    method = "zstd"
                raw = self._download_from_storage(key, "hot")
                if raw:
                    return decompress_data(raw, method).decode("utf-8", "ignore")

            return row.get("full_text_preview") or ""
        except Exception:
            return ""


storage_system = StorageSystem()


# ═══════════════════════════════════════════════════════════
# EMBEDDINGS (Gemini text-embedding-004, 768-dim, multi-key)
# ═══════════════════════════════════════════════════════════

def generate_embedding(text: str) -> list:
    """
    768-dim vector via Gemini text-embedding-004.
    Supports multi-account key rotation for rate limit resilience.
    """
    keys = get_multi_keys("GEMINI_API_KEY", "GEMINI_API_KEY")
    if not keys or not text:
        return [0.0] * 768

    last_err = None
    for key in keys:
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={key}",
                json={
                    "model": "models/text-embedding-004",
                    "content": {"parts": [{"text": text[:2000]}]},
                },
                timeout=15,
            )
            if r.status_code == 200:
                vec = r.json().get("embedding", {}).get("values", [])
                if vec and len(vec) == 768:
                    return vec
            last_err = f"HTTP {r.status_code}: {r.text[:100]}"
        except Exception as e:
            last_err = str(e)
            continue

    logger.warning(f"All embedding keys failed: {last_err}")
    return [0.0] * 768


# ═══════════════════════════════════════════════════════════
# DOCUMENT SEARCH (3-Layer: Keyword → Fuzzy → Semantic)
# ═══════════════════════════════════════════════════════════

def search_documents(query: str, limit: int = 4) -> list:
    """
    Layered search strategy:
      1. Fast keyword match (Supabase SQL)     → instant
      2. Fuzzy match (thefuzz)                 → typo-tolerant
      3. Semantic search (Qdrant vectors)      → meaning-based
    """
    query = sanitize_search_query(query)
    if not query or not supabase:
        return []

    results = []

    # ── Layer 1: Keyword search ──
    try:
        results = (
            supabase.table("documents")
            .select("id, filename, doc_type, ai_summary, full_text_preview, storage_tier, file_key")
            .or_(f"filename.ilike.%{query}%,ai_summary.ilike.%{query}%,full_text_preview.ilike.%{query}%")
            .eq("processing_status", "ready")
            .limit(limit)
            .execute()
            .data or []
        )
    except Exception as e:
        logger.warning(f"Keyword search failed: {e}")

    # ── Layer 2: Fuzzy search ──
    if not results and FUZZY_AVAILABLE:
        try:
            all_docs = (
                supabase.table("documents")
                .select("id, filename, doc_type, ai_summary, full_text_preview, storage_tier, file_key")
                .eq("processing_status", "ready")
                .limit(200)
                .execute()
                .data or []
            )
            choices = {
                d["id"]: f"{d.get('filename', '')} {d.get('ai_summary', '')}"
                for d in all_docs
            }
            if choices:
                matches = process.extract(query, choices, scorer=fuzz.partial_ratio, limit=limit)
                matched_ids = {m[2] for m in matches if m[1] >= 60}
                results = [d for d in all_docs if d["id"] in matched_ids]
        except Exception as e:
            logger.warning(f"Fuzzy search failed: {e}")

    # ── Layer 3: Semantic search ──
    if not results and QDRANT_AVAILABLE and qdrant_client:
        try:
            vec = generate_embedding(query)
            if any(vec):
                hits = qdrant_client.search(
                    collection_name="rta_documents",
                    query_vector=vec,
                    limit=limit,
                    score_threshold=0.55,
                )
                doc_ids = [h.payload.get("doc_id") for h in hits if h.payload.get("doc_id")]
                if doc_ids:
                    results = (
                        supabase.table("documents")
                        .select("id, filename, doc_type, ai_summary, full_text_preview, storage_tier, file_key")
                        .in_("id", doc_ids)
                        .execute()
                        .data or []
                    )
        except Exception as e:
            logger.warning(f"Semantic search failed: {e}")

    return results


# ═══════════════════════════════════════════════════════════
# AUTO-TIERING (Hot ↔ Cold migration)
# ═══════════════════════════════════════════════════════════

def auto_tier_documents() -> dict:
    """Multi-cloud auto-tiering: Hot → Cold → Archive"""
    if not supabase:
        return {"error": "Supabase unavailable"}

    try:
        results = {"moved_to_cold": 0, "moved_to_archive": 0, "moved_to_hot": 0}

        # HOT → COLD (90 days)
        cutoff_90 = (now_utc() - timedelta(days=90)).isoformat()
        cold_candidates = (
            supabase.table("documents")
            .select("id, file_key")
            .eq("storage_tier", "hot")
            .lt("last_accessed", cutoff_90)
            .limit(100)
            .execute()
            .data or []
        )

        for d in cold_candidates:
            data = storage_system._download_from_storage(d["file_key"], "hot")
            if not data:
                continue
            actual_tier = storage_system._upload_to_storage(data, d["file_key"], "cold")
            if actual_tier == "cold":
                try:
                    if r2_client:
                        r2_client.delete_object(Bucket=storage_system.hot_bucket, Key=d["file_key"])
                except Exception:
                    pass
                supabase.table("documents").update({"storage_tier": "cold"}).eq("id", d["id"]).execute()
                results["moved_to_cold"] += 1

        # COLD → ARCHIVE (365 days)
        cutoff_365 = (now_utc() - timedelta(days=365)).isoformat()
        archive_candidates = (
            supabase.table("documents")
            .select("id, file_key")
            .eq("storage_tier", "cold")
            .lt("last_accessed", cutoff_365)
            .limit(50)
            .execute()
            .data or []
        )

        for d in archive_candidates:
            data = storage_system._download_from_storage(d["file_key"], "cold")
            if not data:
                continue
            actual_tier = storage_system._upload_to_storage(data, d["file_key"], "archive")
            if actual_tier == "archive":
                try:
                    if b2_client:
                        b2_client.delete_object(Bucket=storage_system.cold_bucket, Key=d["file_key"])
                except Exception:
                    pass
                supabase.table("documents").update({"storage_tier": "archive"}).eq("id", d["id"]).execute()
                results["moved_to_archive"] += 1

        # Promote to HOT (10+ accesses)
        hot_candidates = (
            supabase.table("documents")
            .select("id, file_key, storage_tier")
            .in_("storage_tier", ["cold", "archive"])
            .gte("access_count", 10)
            .limit(50)
            .execute()
            .data or []
        )

        for d in hot_candidates:
            current_tier = d.get("storage_tier", "cold")
            data = storage_system._download_from_storage(d["file_key"], current_tier)
            if not data:
                continue
            actual_tier = storage_system._upload_to_storage(data, d["file_key"], "hot")
            if actual_tier == "hot":
                try:
                    if current_tier == "cold" and b2_client:
                        b2_client.delete_object(Bucket=storage_system.cold_bucket, Key=d["file_key"])
                    elif current_tier == "archive" and storj_client:
                        storj_client.delete_object(Bucket=storage_system.archive_bucket, Key=d["file_key"])
                except Exception:
                    pass
                supabase.table("documents").update(
                    {"storage_tier": "hot", "access_count": 0}
                ).eq("id", d["id"]).execute()
                results["moved_to_hot"] += 1

        return results

    except Exception as e:
        return {"error": str(e)}
        # ── Promote hot documents from cold storage ──
        hot_candidates = (
            supabase.table("documents")
            .select("id, file_key")
            .eq("storage_tier", "cold")
            .gte("access_count", 10)
            .limit(50)
            .execute()
            .data or []
        )

        moved_hot = 0
        for d in hot_candidates:
            data = storage_system._download_from_storage(d["file_key"], "cold")
            if not data:
                continue
            actual_tier = storage_system._upload_to_storage(data, d["file_key"], "hot")
            if actual_tier == "hot":
                try:
                    if b2_client:
                        b2_client.delete_object(Bucket=storage_system.cold_bucket, Key=d["file_key"])
                except Exception:
                    pass
                supabase.table("documents").update(
                    {"storage_tier": "hot", "access_count": 0}
                ).eq("id", d["id"]).execute()
                moved_hot += 1

        return {"moved_to_cold": moved_cold, "moved_to_hot": moved_hot}

    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════
# DOCUMENT CARD (UI Component)
# ═══════════════════════════════════════════════════════════

def document_card(doc: dict):
    """Render a document row with status badge, summary, and download."""
    doc_id = str(doc.get("id", uuid.uuid4()))
    status = doc.get("processing_status", "ready")
    tier = doc.get("storage_tier", "hot")

    status_class = {
        "ready": "status-ready",
        "processing": "status-processing",
        "failed": "status-failed",
    }.get(status, "status-processing")

    tier_icon = "🔥" if tier == "hot" else "❄️" if tier == "cold" else "☁️"

    st.markdown(f"""
    <div class="commercial-card">
        <div class="post-header">
            <div class="post-avatar">📄</div>
            <div style="flex:1;">
                <b>{html.escape(str(doc.get('filename', 'Document')))}</b><br>
                <small style="color:#666;">
                    {str(doc.get('uploaded_at', ''))[:16]} •
                    {tier_icon} {tier.upper()} storage
                </small>
            </div>
            <span class="status-badge {status_class}">{status.upper()}</span>
        </div>
        {f'<p>{html.escape(str(doc.get("ai_summary", ""))[:200])}</p>' if doc.get('ai_summary') else ''}
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button("⬇️ Download", key=f"dl_{doc_id}"):
            with st.spinner("Decrypting & decompressing..."):
                file_data = storage_system.download_document(doc_id)
                if file_data:
                    st.session_state[f"download_ready_{doc_id}"] = file_data
                    st.rerun()
                else:
                    st.error("Unable to download file.")

    if st.session_state.get(f"download_ready_{doc_id}"):
        st.download_button(
            label="💾 Save to Device",
            data=st.session_state[f"download_ready_{doc_id}"],
            file_name=doc.get("filename", "file"),
            key=f"sv_{doc_id}",
        )

    with c2:
        if doc.get("ai_summary") or doc.get("full_text_preview"):
            with st.expander("👁️ Preview"):
                if doc.get("full_text_preview"):
                    st.text(str(doc["full_text_preview"])[:1000])
                elif doc.get("ai_summary"):
                    st.write(doc["ai_summary"]) 
# ═══════════════════════════════════════════════════════════
# CIRCUIT BREAKERS (One per provider)
# ═══════════════════════════════════════════════════════════

qwen_breaker = CircuitBreaker("qwen", failure_threshold=5, recovery_timeout=60)
groq_breaker = CircuitBreaker("groq", failure_threshold=5, recovery_timeout=60)
deepseek_breaker = CircuitBreaker("deepseek", failure_threshold=5, recovery_timeout=60)
gemini_breaker = CircuitBreaker("gemini", failure_threshold=5, recovery_timeout=60)
openai_breaker = CircuitBreaker("openai", failure_threshold=5, recovery_timeout=60)
anthropic_breaker = CircuitBreaker("anthropic", failure_threshold=5, recovery_timeout=60)


# ═══════════════════════════════════════════════════════════
# MULTI-AI ENGINE (Circuit Breakers + Multi-Account + Fallback)
# ═══════════════════════════════════════════════════════════

class MultiAI:
    """
    Enterprise AI routing engine:
      • Multi-account key rotation (comma-separated keys)
      • Circuit breakers prevent cascading failures
      • Redis cache (exact match) + Qdrant semantic cache (similar queries)
      • Serial fallback across providers by role
      • FIXED MODEL NAMES: gemini-1.5-flash, claude-3-haiku, gpt-4o-mini
    """

    # ─── KEY MANAGEMENT ────────────────────────────────────
    def _get_keys(self, setting_name: str, secret_name: str = "") -> List[str]:
        """
        Supports comma-separated keys for multi-account rotation.
        Admin pastes: "sk-key1, sk-key2, sk-key3" in AI Settings.
        """
        val = get_setting(setting_name)
        if not val and secret_name:
            val = secret(secret_name)
        if not val:
            return []
        return [k.strip() for k in str(val).split(",") if k.strip()]

    def _get_key(self, setting_name: str, secret_name: str = "") -> str:
        """Get first available key (backward compatible)."""
        keys = self._get_keys(setting_name, secret_name)
        return keys[0] if keys else ""

    # ─── PROVIDER ROUTING BY ROLE ──────────────────────────
    def get_providers(self, role: str = "chat") -> List[dict]:
        """
        Route to specialized providers based on task type:
          doc_qa      → DeepSeek (best at document understanding)
          deep_search → Qwen + Groq (fast web analysis)
          summarize   → DeepSeek + Gemini (free, good for Indian languages)
          chat        → Qwen + DeepSeek (general purpose)
        """
        providers = []

        # Fetch all keys with multi-account support
        ds_keys = self._get_keys("DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY")
        qw_keys = self._get_keys("QWEN_API_KEY", "QWEN_API_KEY")
        gm_keys = self._get_keys("GEMINI_API_KEY", "GEMINI_API_KEY")
        oai_keys = self._get_keys("OPENAI_API_KEY", "OPENAI_API_KEY")
        ant_keys = self._get_keys("ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY")
        groq_keys = self._get_keys("GROQ_API_KEY", "GROQ_API_KEY")

        # Primary providers by role
        if role == "doc_qa":
            for k in ds_keys:
                providers.append({"name": "DeepSeek", "key": k})
            for k in qw_keys:
                providers.append({"name": "Qwen", "key": k})
        elif role == "deep_search":
            for k in qw_keys:
                providers.append({"name": "Qwen", "key": k})
            for k in groq_keys:
                providers.append({"name": "Groq", "key": k})
            for k in ds_keys:
                providers.append({"name": "DeepSeek", "key": k})
        elif role == "summarize":
            for k in ds_keys:
                providers.append({"name": "DeepSeek", "key": k})
            for k in gm_keys:
                providers.append({"name": "Gemini", "key": k})
            for k in qw_keys:
                providers.append({"name": "Qwen", "key": k})
        else:  # chat
            for k in qw_keys:
                providers.append({"name": "Qwen", "key": k})
            for k in ds_keys:
                providers.append({"name": "DeepSeek", "key": k})

        # Backup providers (always appended)
        for k in gm_keys:
            providers.append({"name": "Gemini", "key": k})
        for k in groq_keys:
            providers.append({"name": "Groq", "key": k})
        for k in oai_keys:
            providers.append({"name": "OpenAI", "key": k})
        for k in ant_keys:
            providers.append({"name": "Anthropic", "key": k})

        # Deduplicate by provider name (keep first occurrence)
        seen = set()
        final = []
        for p in providers:
            if p["key"] and p["name"] not in seen:
                seen.add(p["name"])
                final.append(p)
        return final

    # ─── PROVIDER CALL METHODS (FIXED MODEL NAMES) ─────────

    def _call_qwen(self, prompt: str, key: str) -> str:
        try:
            r = requests.post(
                "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "qwen-plus",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000,
                },
                timeout=20,
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            raise Exception(f"HTTP {r.status_code}: {r.text[:100]}")
        except Exception as e:
            logger.warning(f"Qwen call failed: {e}")
            raise

    def _call_groq(self, prompt: str, key: str) -> str:
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.1-8b-instant",  # FIX: Higher free-tier limits
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000,
                },
                timeout=20,
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            raise Exception(f"HTTP {r.status_code}: {r.text[:100]}")
        except Exception as e:
            logger.warning(f"Groq call failed: {e}")
            raise

    def _call_deepseek(self, prompt: str, key: str) -> str:
        try:
            r = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000,
                },
                timeout=20,
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            raise Exception(f"HTTP {r.status_code}: {r.text[:100]}")
        except Exception as e:
            logger.warning(f"DeepSeek call failed: {e}")
            raise

    def _call_gemini(self, prompt: str, key: str) -> str:
        try:
            # FIX: gemini-1.5-flash (gemini-2.0-flash doesn't exist on free tier)
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=15,
            )
            if r.status_code == 200:
                return r.json()["candidates"][0]["content"]["parts"][0]["text"]
            raise Exception(f"HTTP {r.status_code}: {r.text[:100]}")
        except Exception as e:
            logger.warning(f"Gemini call failed: {e}")
            raise

    def _call_openai(self, prompt: str, key: str) -> str:
        try:
            # FIX: gpt-4o-mini (gpt-3.5-turbo is deprecated)
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000,
                },
                timeout=15,
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            raise Exception(f"HTTP {r.status_code}: {r.text[:100]}")
        except Exception as e:
            logger.warning(f"OpenAI call failed: {e}")
            raise

    def _call_anthropic(self, prompt: str, key: str) -> str:
        try:
            # FIX: claude-3-haiku-20240307 (claude-3-5-haiku doesn't exist)
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
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
            raise Exception(f"HTTP {r.status_code}: {r.text[:100]}")
        except Exception as e:
            logger.warning(f"Anthropic call failed: {e}")
            raise

    # ─── MAIN REQUEST METHOD ───────────────────────────────
    def request(self, prompt: str, role: str = "chat") -> dict:
        """
        Full request pipeline:
          1. Check Redis cache (exact match)
          2. Check Qdrant semantic cache (similar queries)
          3. Try providers in priority order with circuit breakers
          4. Cache successful responses
        """
        business_metrics.increment("ai_queries_total")
        h = hashlib.md5(f"{role}:{prompt}".encode()).hexdigest()

        # ── Layer 1: Redis exact-match cache ──
        if redis_client:
            try:
                c = redis_client.get(f"ai_cache:{h}")
                if c:
                    business_metrics.increment("ai_queries_cached")
                    return {"success": True, "response": json.loads(c), "provider": "cache"}
            except Exception:
                pass

        # ── Layer 2: Qdrant semantic cache ──
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
                        "response": hits[0].payload["response"],
                        "provider": "semantic_cache",
                    }
            except Exception:
                pass

        # ── Layer 3: Provider fallback chain ──
        providers = self.get_providers(role=role)
        if not providers:
            return {
                "success": False,
                "error": f"No API keys configured for role '{role}'. Go to Admin Panel → AI Settings.",
            }

        errors = []
        for p in providers:
            resp = None
            try:
                if p["name"] == "Qwen":
                    resp = qwen_breaker.call(self._call_qwen, prompt, p["key"])
                elif p["name"] == "Groq":
                    resp = groq_breaker.call(self._call_groq, prompt, p["key"])
                elif p["name"] == "DeepSeek":
                    resp = deepseek_breaker.call(self._call_deepseek, prompt, p["key"])
                elif p["name"] == "Gemini":
                    resp = gemini_breaker.call(self._call_gemini, prompt, p["key"])
                elif p["name"] == "OpenAI":
                    resp = openai_breaker.call(self._call_openai, prompt, p["key"])
                elif p["name"] == "Anthropic":
                    resp = anthropic_breaker.call(self._call_anthropic, prompt, p["key"])

                if resp:
                    # Cache in Redis (24h TTL)
                    if redis_client:
                        try:
                            redis_client.setex(f"ai_cache:{h}", 86400, json.dumps(resp))
                        except Exception:
                            pass

                    # Cache in Qdrant (semantic match for future similar queries)
                    if qdrant_client:
                        try:
                            qdrant_client.upsert(
                                collection_name="ai_semantic_cache",
                                points=[PointStruct(
                                    id=uuid.uuid4().hex,
                                    vector=generate_embedding(prompt),
                                    payload={"query": prompt, "response": resp},
                                )],
                            )
                        except Exception:
                            pass

                    return {"success": True, "response": resp, "provider": p["name"]}
                else:
                    errors.append(f"{p['name']}: returned no response")

            except Exception as e:
                errors.append(f"{p['name']}: {str(e)[:80]}")
                continue

        return {
            "success": False,
            "error": f"All providers failed for role '{role}': {'; '.join(errors)}",
        }

    # ─── SUMMARIZE HELPER ──────────────────────────────────
    def summarize(self, text: str) -> Optional[str]:
        """Generate 2-3 sentence summary of document text."""
        r = self.request(f"Summarize this in 2-3 sentences: {text[:3000]}", role="summarize")
        return r.get("response") if r.get("success") else None


# Initialize the AI engine
ai_system = MultiAI()


# ═══════════════════════════════════════════════════════════
# AGENTIC WEB SEARCH (Serper + DuckDuckGo fallback)
# ═══════════════════════════════════════════════════════════

def agentic_web_search(query: str, stype: str = "gov") -> str:
    """
    Search the web using Serper API (if configured) or DuckDuckGo fallback.
    stype="gov" restricts to government websites.
    """
    key = get_setting("SERPER_API_KEY") or secret("SERPER_API_KEY")

    # ── Try Serper first ──
    if key:
        search_query = query
        if stype == "gov":
            search_query = f"{query} site:ap.gov.in OR site:gov.in"
        try:
            r = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": key, "Content-Type": "application/json"},
                json={"q": search_query, "num": 5},
                timeout=10,
            )
            if r.status_code == 200:
                results = r.json().get("organic", [])
                if results:
                    return "\n".join([
                        f"Source: {x.get('link')}\nSnippet: {x.get('snippet')}\n"
                        for x in results
                    ])
        except Exception as e:
            logger.warning(f"Serper search failed: {e}")

    # ── DuckDuckGo fallback ──
    try:
        ddg_query = query
        if stype == "gov":
            ddg_query = f"{query} site:gov.in"

        r = requests.get(
            "https://lite.duckduckgo.com/lite/",
            params={"q": ddg_query},
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if r.status_code == 200:
            results = []
            links = re.findall(r'<a rel="nofollow" href="([^"]+)"[^>]*>(.*?)</a>', r.text)
            snippets = re.findall(r'<td class="result-snippet">(.*?)</td>', r.text, re.DOTALL)
            for i, (link, title) in enumerate(links[:5]):
                snippet = snippets[i] if i < len(snippets) else ""
                snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                results.append(f"Source: {link}\nSnippet: {snippet[:200]}\n")
            if results:
                return "\n".join(results)
    except Exception as e:
        logger.warning(f"DuckDuckGo search failed: {e}")

    return ""


# ═══════════════════════════════════════════════════════════
# AUTHENTICATION UTILITIES
# ═══════════════════════════════════════════════════════════

def hash_password(p: str) -> str:
    """Hash password with bcrypt, or salted SHA-256 as fallback."""
    if BCRYPT_AVAILABLE and bcrypt:
        return bcrypt.hashpw(p.encode(), bcrypt.gensalt(rounds=10)).decode()
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + p).encode()).hexdigest()
    return f"{salt}${h}"


def check_password(p: str, h: str) -> bool:
    """Verify password against stored hash."""
    if not p or not h:
        return False
    try:
        if BCRYPT_AVAILABLE and bcrypt and h.startswith("$2"):
            return bcrypt.checkpw(p.encode(), h.encode())
        if "$" in h:
            salt, stored_hash = h.split("$", 1)
            return hashlib.sha256((salt + p).encode()).hexdigest() == stored_hash
        return False
    except Exception:
        return False


def get_user(email: str) -> Optional[dict]:
    """Fetch user from Redis cache or Supabase."""
    if redis_client:
        try:
            c = redis_client.get(f"user_v2:{email}")
            if c:
                return json.loads(c)
        except Exception:
            pass

    if supabase:
        try:
            r = supabase.table("users").select(
                "id, email, name, office_code, office_name, designation, "
                "section, seat_number, admin_level, active, password_hash"
            ).eq("email", email).execute()
            if r.data:
                u = r.data[0]
                if redis_client:
                    redis_client.setex(f"user_v2:{email}", 3600, json.dumps(u, default=str))
                return u
        except Exception:
            pass
    return None


def login_rate_limited(email: str) -> bool:
    """Check if user has exceeded 5 login attempts in 15 minutes."""
    if redis_client:
        k = f"login_attempts:{email}"
        try:
            v = redis_client.get(k)
            return int(v) > 5 if v else False
        except Exception:
            return False

    if supabase:
        try:
            cutoff = (now_utc() - timedelta(minutes=15)).isoformat()
            r = (
                supabase.table("login_attempts")
                .select("email")
                .eq("email", email)
                .gte("created_at", cutoff)
                .execute()
            )
            # Cleanup old attempts
            supabase.table("login_attempts").delete().lt(
                "created_at", (now_utc() - timedelta(hours=1)).isoformat()
            ).execute()
            return len(r.data or []) >= 5
        except Exception:
            pass
    return False


def increment_login_attempt(email: str):
    """Track failed login attempt for rate limiting."""
    if redis_client:
        k = f"login_attempts:{email}"
        redis_client.set(k, "0", ex=900, nx=True)
        redis_client.incr(k)
    elif supabase:
        try:
            supabase.table("login_attempts").insert({
                "email": email,
                "created_at": now_utc().isoformat(),
            }).execute()
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
# SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════

COOKIE_NAME = "rta_session"
SESSION_DAYS = 7


def init_session_state():
    """Initialize default session state values."""
    defaults = {
        "user": None,
        "logged_in": False,
        "page": "feed",
        "admin_level": "staff",
        "sidebar_open": True,
        "messages": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def try_auto_login():
    """Attempt auto-login from session cookie."""
    if st.session_state.logged_in:
        return

    try:
        token = cookies.get(COOKIE_NAME)
    except Exception:
        token = None

    if not token or not isinstance(token, str) or len(token) < 10:
        return

    h = hashlib.sha256(token.encode("utf-8")).hexdigest()
    if not supabase:
        return

    try:
        r = supabase.table("sessions").select("*").eq("token_hash", h).execute()
        if not r.data:
            try:
                cookies.delete(COOKIE_NAME)
            except Exception:
                pass
            return

        s = r.data[0]
        expires_raw = s.get("expires_at")
        if not expires_raw:
            return

        expires_at = datetime.fromisoformat(str(expires_raw).replace("Z", "+00:00"))
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at <= now_utc():
            try:
                supabase.table("sessions").delete().eq("token_hash", h).execute()
                cookies.delete(COOKIE_NAME)
            except Exception:
                pass
            return

        email = s.get("email")
        if not email:
            return

        u = get_user(email)
        if u and u.get("active", True):
            st.session_state.logged_in = True
            st.session_state.user = u
            st.session_state.admin_level = u.get("admin_level", "staff")
        else:
            try:
                supabase.table("sessions").delete().eq("token_hash", h).execute()
                cookies.delete(COOKIE_NAME)
            except Exception:
                pass

    except Exception as e:
        logger.error(f"Auto-login failed: {e}")


def do_login(u: dict):
    """Complete login: set session, create token, set cookie."""
    st.session_state.logged_in = True
    st.session_state.user = u
    st.session_state.admin_level = u.get("admin_level", "staff")

    token = secrets.token_urlsafe(32)
    h = hashlib.sha256(token.encode()).hexdigest()

    if supabase:
        try:
            supabase.table("sessions").insert({
                "token_hash": h,
                "email": u.get("email", ""),
                "expires_at": (now_utc() + timedelta(days=SESSION_DAYS)).isoformat(),
            }).execute()
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
    """Clear session, delete token, remove cookie."""
    h = None
    try:
        token = cookies.get(COOKIE_NAME)
        if token:
            h = hashlib.sha256(token.encode()).hexdigest()
    except Exception:
        pass

    if supabase and h:
        try:
            supabase.table("sessions").delete().eq("token_hash", h).execute()
        except Exception:
            pass

    try:
        audit_log(
            st.session_state.get("user", {}).get("email", "unknown"),
            "user.logout", "user", None
        )
    except Exception:
        pass

    st.session_state.clear()
    try:
        cookies.delete(COOKIE_NAME)
    except Exception:
        pass
    st.rerun() 
# ═══════════════════════════════════════════════════════════
# SOCIAL FEED HELPERS
# ═══════════════════════════════════════════════════════════

def extract_mentions(content: str) -> list:
    """Extract @email mentions from post content."""
    pattern = r"@([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
    return re.findall(pattern, str(content or ""))


def extract_hashtags(content: str) -> list:
    """Extract #hashtags from post content."""
    pattern = r"#([a-zA-Z0-9_]+)"
    return re.findall(pattern, str(content or ""))


def send_notification(recipient_email, sender_email, ntype, post_id, message):
    """Insert a notification row for the recipient."""
    if not supabase:
        return
    try:
        supabase.table("notifications").insert({
            "recipient_email": recipient_email,
            "sender_email": sender_email,
            "type": ntype,
            "post_id": str(post_id) if post_id else None,
            "message": message,
            "read": False,
            "created_at": now_utc().isoformat(),
        }).execute()
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")


# ═══════════════════════════════════════════════════════════
# SAMPLE GOVERNMENT CIRCULARS (Demo content for empty installs)
# ═══════════════════════════════════════════════════════════

SAMPLE_CIRCULARS = [
    {
        "id": "sample_1",
        "title": "AP Transport Department - New Vehicle Registration Guidelines",
        "department": "Transport Department, Government of Andhra Pradesh",
        "summary": "Updated guidelines for vehicle registration process effective from 2026. All RTO offices must follow the new digital verification process.",
        "full_text": "The Transport Department of Andhra Pradesh hereby notifies all Regional Transport Officers regarding the updated vehicle registration guidelines. All new registrations must be processed through the digital portal. Physical verification of documents is mandatory for commercial vehicles. The new process includes Aadhaar-based KYC verification, online payment of road tax, and digital issuance of Registration Certificate.",
        "tags": ["registration", "guidelines", "rto"],
        "date": "2026-04-15",
    },
    {
        "id": "sample_2",
        "title": "Motor Vehicle Inspection Schedule - Q2 2026",
        "department": "Office of the Transport Commissioner",
        "summary": "Schedule for mandatory vehicle inspections for Q2 2026. All MVI offices to complete pending inspections before 30th June.",
        "full_text": "All Motor Vehicle Inspectors are hereby directed to complete pending vehicle inspections for Q2 2026 before 30th June 2026. Priority must be given to commercial vehicles, school buses, and tourist vehicles. Inspection certificates must be uploaded to the central portal within 24 hours of inspection.",
        "tags": ["inspection", "mvi", "schedule"],
        "date": "2026-04-20",
    },
    {
        "id": "sample_3",
        "title": "Driving License Renewal - New Automation Process",
        "department": "Transport Department, Government of Andhra Pradesh",
        "summary": "Automated driving license renewal process is now live. Citizens can renew their DL online without visiting RTO office.",
        "full_text": "The Transport Department is pleased to announce the launch of automated driving license renewal system. Citizens whose licenses are due for renewal within 6 months can apply online through the AP Transport portal. The system will automatically verify medical fitness certificates for applicants below 50 years.",
        "tags": ["driving_license", "automation", "renewal"],
        "date": "2026-04-25",
    },
    {
        "id": "sample_4",
        "title": "Road Safety Awareness Campaign - May 2026",
        "department": "Office of the Transport Commissioner",
        "summary": "All RTO offices to conduct road safety awareness programs in schools and colleges during May 2026.",
        "full_text": "As part of the national road safety awareness campaign, all Regional Transport Officers are directed to organize awareness programs in schools and colleges within their jurisdiction during May 2026. Topics must include helmet usage, seatbelt importance, dangers of drunk driving, and pedestrian safety.",
        "tags": ["road_safety", "awareness", "campaign"],
        "date": "2026-04-28",
    },
    {
        "id": "sample_5",
        "title": "Digital Payment Mandate for All Transport Services",
        "department": "Transport Department, Government of Andhra Pradesh",
        "summary": "All transport-related payments must be processed digitally from 1st May 2026. Cash payments will no longer be accepted.",
        "full_text": "In alignment with the Digital India initiative, the Transport Department mandates that all payments for transport services including registration fees, road tax, license fees, and permit charges must be processed through digital payment methods only from 1st May 2026.",
        "tags": ["digital_payment", "mandate", "transport"],
        "date": "2026-05-01",
    },
]


# ═══════════════════════════════════════════════════════════
# FEED DATA HELPERS
# ═══════════════════════════════════════════════════════════

def get_recent_uploads(limit: int = 5) -> list:
    if not supabase:
        return []
    try:
        return (
            supabase.table("documents")
            .select("id, filename, doc_type, ai_summary, uploaded_by, uploaded_at")
            .order("uploaded_at", desc=True)
            .limit(limit)
            .execute()
            .data or []
        )
    except Exception:
        return []


def get_training_links() -> list:
    if not supabase:
        return []
    try:
        res = (
            supabase.table("ai_training_links")
            .select("*")
            .order("created_at", desc=True)
            .limit(30)
            .execute()
        )
        return res.data or []
    except Exception:
        return []


def add_training_link(url, title, user_email) -> bool:
    if not supabase:
        return False
    try:
        existing = get_training_links()
        if len(existing) >= 30:
            return False

        clean_url = str(url or "").strip()
        if not clean_url.startswith("http"):
            clean_url = "https://" + clean_url
        domain = clean_url.split("//")[-1].split("/")[0].replace("www.", "")

        supabase.table("ai_training_links").insert({
            "url": clean_url,
            "title": title or domain,
            "domain": domain,
            "added_by": user_email,
            "created_at": now_utc().isoformat(),
        }).execute()
        return True
    except Exception as e:
        logger.error(f"Failed to add training link: {e}")
        return False


def delete_training_link(link_id) -> bool:
    if not supabase:
        return False
    try:
        supabase.table("ai_training_links").delete().eq("id", link_id).execute()
        return True
    except Exception:
        return False


def cleanup_old_messages():
    """Delete non-starred messages older than 24 hours."""
    if not supabase:
        return
    try:
        cutoff = (now_utc() - timedelta(hours=24)).isoformat()
        supabase.table("messages").delete().lt(
            "created_at", cutoff
        ).eq("is_starred", False).execute()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
# LOGIN PAGE
# ═══════════════════════════════════════════════════════════

def show_login():
    """Login wrapped in st.form to prevent keystroke reruns."""
    quotes = [
        {"text": "Service to the public is service to the nation", "author": "Mahatma Gandhi"},
        {"text": "Together we move Andhra forward", "author": "RTA Mission"},
        {"text": "Every file processed is a citizen served", "author": "RTA Vision"},
    ]
    q = quotes[int(time.time()) % len(quotes)]

    st.markdown(f"""
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
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email").strip().lower()
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                if not email or not password:
                    show_toast("Enter email and password", "warning")
                elif not validate_email(email):
                    show_toast("Invalid email format", "error")
                elif login_rate_limited(email):
                    show_toast("Too many attempts. Try again later.", "error")
                else:
                    u = get_user(email)
                    if u and check_password(password, u.get("password_hash", "")):
                        do_login(u)
                    else:
                        increment_login_attempt(email)
                        show_toast("Invalid credentials", "error")


# ═══════════════════════════════════════════════════════════
# FEED PAGE
# ═══════════════════════════════════════════════════════════

def show_feed():
    """Social feed with announcements, posts, reactions, comments."""
    u = st.session_state.user or {}
    hour = now_utc().hour
    g = "☀️ Good Morning" if hour < 12 else "🌤️ Hello" if hour < 17 else "🌙 Good Evening"

    st.markdown(f"### {g}, {u.get('name', 'User')}!")
    st.caption(f"📍 {u.get('office_name', 'Office')} | {u.get('designation', 'Staff')}")

    # ── Announcements ──
    if supabase:
        try:
            anns = supabase.table("announcements").select("*").gt(
                "expires_at", now_utc().isoformat()
            ).order("created_at", desc=True).limit(3).execute().data or []
            for ann in anns:
                icon = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(
                    ann.get("priority", "info"), "ℹ️"
                )
                st.markdown(f"""
                <div class="announcement-card">
                    <div style="font-size:20px;">{icon}</div>
                    <h3>{html.escape(str(ann.get('title', '')))}</h3>
                    <p>{html.escape(str(ann.get('message', '')))}</p>
                    <small>Expires: {str(ann.get('expires_at', ''))[:10]}</small>
                </div>
                """, unsafe_allow_html=True)
        except Exception:
            pass

    # ── Search + Tag filter ──
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
            if supabase:
                tags = supabase.table("post_tags").select("tag").execute().data or []
                tag_counts = {}
                for t in tags:
                    tag_counts[t.get("tag", "")] = tag_counts.get(t.get("tag", ""), 0) + 1
                top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:5]
                filter_tag = st.selectbox(
                    "Filter by Tag",
                    ["All"] + [f"#{t[0]}" for t in top_tags if t[0]],
                    key="tag_filter",
                )
        except Exception:
            filter_tag = "All"

    # ── Post composer ──
    with st.form("post_form", clear_on_submit=True):
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
            if not supabase:
                show_toast("Supabase not configured", "warning")
            else:
                content_clean = sanitize_input(content)
                post_id = None
                try:
                    result = supabase.table("social_posts").insert({
                        "author_email": u.get("email", ""),
                        "content": content_clean,
                        "post_type": post_type.split()[-1].lower(),
                        "is_pinned": is_pinned,
                        "pinned_by": u.get("email") if is_pinned else None,
                        "created_at": now_utc().isoformat(),
                    }).execute()
                    if result.data:
                        post_id = result.data[0].get("id")

                    if file_upload:
                        file_result = storage_system.upload_document(
                            file_upload.read(), file_upload.name, "social_post", u.get("email", "")
                        )
                        if file_result.get("success"):
                            supabase.table("social_posts").update({
                                "file_key": file_result.get("document_id"),
                                "filename": file_upload.name,
                            }).eq("id", post_id).execute()

                    for tag in extract_hashtags(content):
                        try:
                            supabase.table("post_tags").insert(
                                {"post_id": post_id, "tag": tag.lower()}
                            ).execute()
                        except Exception:
                            pass

                    for mention_email in extract_mentions(content):
                        mentioned_user = get_user(mention_email)
                        if mentioned_user:
                            send_notification(
                                mention_email, u.get("email", ""), "mention", post_id,
                                f"{u.get('name', 'Someone')} mentioned you in a post"
                            )

                    audit_log(u.get("email", ""), "post.create", "post", post_id)
                    show_toast("Posted successfully!")
                    st.rerun()
                except Exception as e:
                    show_toast(f"Failed to post: {str(e)}", "error")

    # ── Fetch posts ──
    posts = []
    if supabase:
        try:
            if search_q and filter_tag != "All":
                search_sql = sanitize_search_query(search_q)
                selected_tag = filter_tag.replace("#", "").lower()
                tag_posts = supabase.table("post_tags").select("post_id").eq(
                    "tag", selected_tag
                ).execute().data or []
                if tag_posts:
                    post_ids = [p.get("post_id") for p in tag_posts if p.get("post_id")]
                    if post_ids:
                        posts = (
                            supabase.table("social_posts")
                            .select("*, users(name, designation)")
                            .in_("id", post_ids)
                            .or_(f"content.ilike.%{search_sql}%,author_email.ilike.%{search_sql}%")
                            .order("is_pinned", desc=True)
                            .order("created_at", desc=True)
                            .limit(50)
                            .execute().data or []
                        )
            elif search_q:
                search_sql = sanitize_search_query(search_q)
                posts = (
                    supabase.table("social_posts")
                    .select("*, users(name, designation)")
                    .or_(f"content.ilike.%{search_sql}%,author_email.ilike.%{search_sql}%")
                    .order("is_pinned", desc=True)
                    .order("created_at", desc=True)
                    .limit(50)
                    .execute().data or []
                )
            elif filter_tag != "All":
                selected_tag = filter_tag.replace("#", "").lower()
                tag_posts = supabase.table("post_tags").select("post_id").eq(
                    "tag", selected_tag
                ).execute().data or []
                if tag_posts:
                    post_ids = [p.get("post_id") for p in tag_posts if p.get("post_id")]
                    if post_ids:
                        posts = (
                            supabase.table("social_posts")
                            .select("*, users(name, designation)")
                            .in_("id", post_ids)
                            .order("is_pinned", desc=True)
                            .order("created_at", desc=True)
                            .execute().data or []
                        )
            else:
                posts = (
                    supabase.table("social_posts")
                    .select("*, users(name, designation)")
                    .order("is_pinned", desc=True)
                    .order("created_at", desc=True)
                    .limit(50)
                    .execute().data or []
                )
        except Exception:
            posts = []

    if not posts:
        st.markdown(
            '<div class="empty-state"><div style="font-size:60px;">📭</div>'
            '<h3>No posts yet</h3><p>Upload a document, register tapal, or create an update.</p></div>',
            unsafe_allow_html=True,
        )

    # ── Recent uploads ──
    recent_uploads = get_recent_uploads(5)
    if recent_uploads:
        st.divider()
        st.markdown("### 📤 Recent Uploads")
        for up in recent_uploads:
            st.markdown(f"""
            <div class="commercial-card">
                <div class="post-header">
                    <div class="post-avatar">📄</div>
                    <div>
                        <b>{html.escape(str(up.get('filename', 'Document')))}</b><br>
                        <small style="color:#666;">Uploaded by {html.escape(str(up.get('uploaded_by', 'Unknown')))} • {str(up.get('uploaded_at', ''))[:16]}</small>
                    </div>
                </div>
                <p>{html.escape(str(up.get('ai_summary') or 'Document uploaded.'))}</p>
            </div>
            """, unsafe_allow_html=True)

    # ── Sample circulars ──
    st.divider()
    st.markdown("### 📋 Latest Government Circulars")
    for circ in SAMPLE_CIRCULARS:
        st.markdown(f"""
        <div class="commercial-card">
            <div class="post-header">
                <div class="post-avatar">🏛️</div>
                <div>
                    <b>{html.escape(circ['department'])}</b><br>
                    <small style="color:#666;">{circ['date']} • Circular</small>
                </div>
            </div>
            <h4>{html.escape(circ['title'])}</h4>
            <p>{html.escape(circ['summary'])}</p>
            <div>{''.join([f'<span class="tag-badge">#{t}</span>' for t in circ['tags']])}</div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("📖 View Full Circular"):
            st.write(circ["full_text"])

    st.divider()

    # ── Render posts ──
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
                st.markdown(f"**{html.escape(str(author_name))}**")
                st.caption(
                    f"{html.escape(str(author.get('designation', '')))} • "
                    f"{str(p.get('created_at', ''))[:16]}"
                )
                st.markdown(
                    f'<div style="margin: 12px 0; font-size: 15px;">'
                    f'{html.escape(str(p.get("content", "")))}</div>',
                    unsafe_allow_html=True,
                )

            try:
                if supabase:
                    post_tags = supabase.table("post_tags").select("tag").eq(
                        "post_id", p.get("id")
                    ).execute().data or []
                    if post_tags:
                        tags_html = " ".join([
                            f'<span class="tag-badge">#{html.escape(str(t.get("tag", "")))}</span>'
                            for t in post_tags
                        ])
                        st.markdown(f'<div style="margin-bottom: 8px;">{tags_html}</div>', unsafe_allow_html=True)
            except Exception:
                pass

            if p.get("file_key"):
                st.markdown(f"📎 **{html.escape(str(p.get('filename', 'Attachment')))}**")
                file_data = storage_system.download_document(str(p.get("file_key")))
                if file_data:
                    st.download_button(
                        "⬇️ Download Attachment", file_data,
                        file_name=p.get("filename", "file"), key=f"dl_post_{post_id}"
                    )

            # ── Actions row ──
            st.markdown('<div class="post-actions">', unsafe_allow_html=True)
            col_react1, col_react2, col_react3, col_comment = st.columns(4)

            for col, reaction, emoji, key_prefix in [
                (col_react1, "like", "👍", "like"),
                (col_react2, "clap", "👏", "clap"),
                (col_react3, "celebrate", "🎉", "celebrate"),
            ]:
                with col:
                    count, user_reacted = 0, False
                    try:
                        if supabase:
                            reactions = supabase.table("post_reactions").select("*").eq(
                                "post_id", p.get("id")
                            ).eq("reaction", reaction).execute().data or []
                            count = len(reactions)
                            user_reacted = any(
                                r.get("user_email") == u.get("email") for r in reactions
                            )
                    except Exception:
                        pass

                    if st.button(
                        f"{emoji} {count}", key=f"{key_prefix}_{post_id}",
                        type="primary" if user_reacted else "secondary"
                    ):
                        try:
                            existing = supabase.table("post_reactions").select("id").eq(
                                "post_id", p.get("id")
                            ).eq("user_email", u.get("email")).eq(
                                "reaction", reaction
                            ).execute()
                            if existing.data:
                                supabase.table("post_reactions").delete().eq(
                                    "id", existing.data[0].get("id")
                                ).execute()
                            else:
                                supabase.table("post_reactions").insert({
                                    "post_id": p.get("id"),
                                    "user_email": u.get("email"),
                                    "reaction": reaction,
                                }).execute()
                            st.rerun()
                        except Exception:
                            pass

            comment_count = 0
            with col_comment:
                try:
                    if supabase:
                        comments_rows = supabase.table("post_comments").select("id").eq(
                            "post_id", p.get("id")
                        ).execute().data or []
                        comment_count = len(comments_rows)
                except Exception:
                    pass
                if st.button(f"💬 Comment ({comment_count})", key=f"comment_btn_{post_id}"):
                    st.session_state[f"show_comments_{post_id}"] = not st.session_state.get(
                        f"show_comments_{post_id}", False
                    )

            st.markdown("</div>", unsafe_allow_html=True)

            # ── Comments section ──
            if st.session_state.get(f"show_comments_{post_id}", False):
                st.markdown("---")
                st.markdown(f"#### 💬 Comments ({comment_count})")
                comments = []
                try:
                    if supabase:
                        comments = supabase.table("post_comments").select(
                            "*, users(name)"
                        ).eq("post_id", p.get("id")).order("created_at").execute().data or []
                except Exception:
                    comments = []

                for c in comments:
                    commenter_name = (c.get("users") or {}).get("name") or c.get("author_email", "Unknown")
                    st.markdown(f"""
                    <div class="comment-item">
                        <div><b>{html.escape(str(commenter_name))}</b></div>
                        <div>{html.escape(str(c.get('content', '')))}</div>
                        <div style="font-size:12px;color:#666;">{str(c.get('created_at', ''))[:16]}</div>
                    </div>
                    """, unsafe_allow_html=True)

                new_comment = st.text_area("Add a comment", key=f"new_comment_{post_id}", height=60)
                if st.button("Post Comment", key=f"post_comment_{post_id}"):
                    if new_comment.strip() and supabase:
                        try:
                            supabase.table("post_comments").insert({
                                "post_id": p.get("id"),
                                "author_email": u.get("email", ""),
                                "content": sanitize_input(new_comment),
                                "created_at": now_utc().isoformat(),
                            }).execute()
                            show_toast("Comment posted!")
                            st.rerun()
                        except Exception as e:
                            show_toast(f"Failed: {str(e)}", "error")

            # ── Delete (author or admin) ──
            if u.get("admin_level") != "staff" or p.get("author_email") == u.get("email"):
                if st.button("🗑️ Delete Post", key=f"del_post_{post_id}", type="secondary"):
                    try:
                        supabase.table("social_posts").delete().eq("id", p.get("id")).execute()
                        audit_log(u.get("email", ""), "post.delete", "post", p.get("id"))
                        show_toast("Post deleted")
                        st.rerun()
                    except Exception as e:
                        show_toast(f"Failed: {str(e)}", "error")


# ═══════════════════════════════════════════════════════════
# WORKSPACE PAGE
# ═══════════════════════════════════════════════════════════

def show_workspace():
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


# ═══════════════════════════════════════════════════════════
# TAPAL PAGE
# ═══════════════════════════════════════════════════════════

def show_tapal():
    """Tapal registration with reference format + monthly report."""
    u = st.session_state.user or {}
    st.markdown("### 📥 Smart Tapal")

    tab1, tab2 = st.tabs(["📝 Register Tapal", "📊 Monthly Report"])

    with tab1:
        with st.form("tapal_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                direction = st.selectbox("Direction", ["Inward", "Outward"])
                d = st.date_input("Date", value=date.today())
            with c2:
                counter_serial = st.selectbox(
                    "Counter Serial",
                    ["A1", "B1", "C1", "D1", "E1", "F1", "G1", "H1"]
                )
                serial_number = st.text_input("Serial Number (up to 8 digits)", max_chars=8)
            with c3:
                ft = st.text_input("From/To")
                pri = st.selectbox("Priority", ["Normal", "Urgent", "Immediate"])
                subj = st.text_input("Subject")

            rno = ""
            if counter_serial and serial_number:
                current_year = now_utc().year
                rno = f"R.NO-{counter_serial}/{serial_number}/{current_year}"
            if rno:
                st.info(f"📋 Reference: {rno}")

            remarks = st.text_area("Remarks", height=80)
            file = st.file_uploader("Attachment (Max 20MB)", type=["pdf", "jpg", "png"])
            submitted = st.form_submit_button("💾 Save Tapal")

            if submitted:
                if not serial_number or not subj:
                    show_toast("Serial Number and Subject are required", "warning")
                elif not serial_number.isdigit():
                    show_toast("Serial Number must be numeric", "error")
                else:
                    did = None
                    if file is not None:
                        try:
                            if file.size > 20 * 1024 * 1024:
                                show_toast("File too large. Max 20MB.", "error")
                                st.stop()
                            with st.spinner("Uploading attachment..."):
                                file_bytes = file.read()
                                res = storage_system.upload_document(
                                    file_bytes, file.name, "tapal", u.get("email", "system")
                                )
                                if res.get("success"):
                                    did = res.get("document_id")
                                else:
                                    st.error(f"Storage Error: {res.get('error', 'Unknown error')}")
                                    st.stop()
                        except Exception as e:
                            st.error(f"Exception during upload: {str(e)}")
                            st.stop()

                    if supabase:
                        try:
                            supabase.table("tapal_log").insert({
                                "r_no": rno,
                                "direction": direction,
                                "tapal_date": d.isoformat(),
                                "section": u.get("section", ""),
                                "designation": u.get("designation", ""),
                                "from_to": ft,
                                "subject": subj,
                                "priority": pri,
                                "remarks": remarks,
                                "document_id": did,
                                "created_by": u.get("email", "system"),
                                "created_at": now_utc().isoformat(),
                            }).execute()
                            try:
                                supabase.table("social_posts").insert({
                                    "author_email": u.get("email", ""),
                                    "content": f"📥 Tapal registered: {rno} - {subj}",
                                    "post_type": "tapal",
                                    "is_pinned": False,
                                    "created_at": now_utc().isoformat(),
                                }).execute()
                            except Exception:
                                pass
                            show_toast("Tapal saved successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Database Error: {str(e)}")
                    else:
                        show_toast("Supabase not configured", "warning")

    with tab2:
        st.markdown("#### 📊 Monthly Tapal Report")
        if supabase:
            try:
                month_start = date(now_utc().year, now_utc().month, 1).isoformat()
                month_end = now_utc().date().isoformat()
                rows = (
                    supabase.table("tapal_log").select("*")
                    .gte("tapal_date", month_start)
                    .lte("tapal_date", month_end)
                    .execute().data or []
                )
                df = pd.DataFrame(rows)
                if not df.empty:
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Total Entries", len(df))
                    c2.metric(
                        "Inward",
                        len(df[df.get("direction", pd.Series()) == "Inward"])
                        if "direction" in df.columns else 0
                    )
                    c3.metric(
                        "Outward",
                        len(df[df.get("direction", pd.Series()) == "Outward"])
                        if "direction" in df.columns else 0
                    )
                    st.download_button(
                        "📥 Download CSV", df.to_csv(index=False),
                        f"tapal_report_{now_utc().strftime('%Y%m')}.csv"
                    )
                else:
                    st.info("No tapal entries this month.")
            except Exception:
                st.info("Could not load report.")
        else:
            st.info("Supabase not configured.")


# ═══════════════════════════════════════════════════════════
# DISPATCH PAGE
# ═══════════════════════════════════════════════════════════

def show_dispatch():
    """Dispatch label generator with validation, audit log, and print support."""
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

        submitted = st.form_submit_button("🖨️ Generate Label")
        if submitted:
            if not seq or not to.strip() or not subj.strip():
                show_toast("Seq No., To, and Subject are required", "warning")
            else:
                safe_to = html.escape(to)
                safe_frm = html.escape(frm)
                safe_subj = html.escape(subj)

                seat = u.get("seat_number")
                if not seat:
                    designation = u.get("designation", "JA") or "JA"
                    seat = str(designation)[:3]

                dno = f"Dispatch/{u.get('section', 'A')}/{seat}/{now_utc().year}/{seq}"

                if supabase:
                    try:
                        supabase.table("dispatch_log").insert({
                            "dispatch_no": dno,
                            "envelope": env,
                            "from_addr": frm,
                            "to_addr": to,
                            "subject": subj,
                            "created_by": u.get("email", ""),
                            "created_at": now_utc().isoformat(),
                        }).execute()
                    except Exception as e:
                        st.error(f"Dispatch log error: {type(e).__name__}: {e}")

                audit_log(
                    u.get("email", ""), "dispatch.generate", "dispatch", None,
                    {"dispatch_no": dno},
                )

                st.session_state.dispatch_ready = True
                st.session_state.dispatch_html = f"""
                <div style="border:2px solid #000;padding:30px;background:white;color:black;font-family:monospace;">
                    <h3 style="margin-top:0;">DISPATCH LABEL</h3>
                    <hr>
                    <b>Dispatch No:</b> {dno}<br>
                    <b>Envelope:</b> {env}<br><br>
                    <b>From:</b><br>
                    {safe_frm}<br><br>
                    <b>To:</b><br>
                    {safe_to}<br><br>
                    <b>Subject:</b> {safe_subj}
                </div>
                """
                show_toast("Label generated!")

    # BUG FIX: Removed orphaned download block that referenced undefined doc_id
    if st.session_state.get("dispatch_ready"):
        st.markdown(st.session_state.get("dispatch_html", ""), unsafe_allow_html=True)
        if st.button("🖨️ Print / Save as PDF"):
            components.html(
                """
                <script>
                window.parent.print();
                </script>
                """,
                height=0,
            )


# ═══════════════════════════════════════════════════════════
# DOCUMENTS PAGE
# ═══════════════════════════════════════════════════════════

def show_documents():
    """Document upload + search using the document_card helper."""
    u = st.session_state.user or {}
    st.markdown("### 📄 Documents")

    file = st.file_uploader("Upload", type=["pdf", "jpg", "png"])
    if file:
        if file.size > 20 * 1024 * 1024:
            show_toast("Too large. Max 20MB.", "error")
        else:
            with st.spinner("Uploading..."):
                res = storage_system.upload_document(
                    file.read(), file.name, "circular", u.get("email", "")
                )
                if res.get("success"):
                    if res.get("duplicate"):
                        show_toast(res.get("message", "Duplicate file"), "warning")
                    else:
                        show_toast(f"Uploaded! {res.get('compression_ratio', 0) * 100:.1f}% compressed")
                    try:
                        if supabase:
                            supabase.table("social_posts").insert({
                                "author_email": u.get("email", ""),
                                "content": f"📄 Uploaded document: {file.name}",
                                "post_type": "document",
                                "is_pinned": False,
                                "file_key": res.get("document_id"),
                                "filename": file.name,
                                "created_at": now_utc().isoformat(),
                            }).execute()
                    except Exception:
                        pass
                else:
                    show_toast(res.get("error", "Upload failed"), "error")

    q = st.text_input("Search")
    docs = []
    if q:
        docs = search_documents(q)
    else:
        if supabase:
            try:
                docs = (
                    supabase.table("documents")
                    .select("id, filename, file_key, storage_tier, doc_type, ai_summary, "
                            "full_text_preview, uploaded_at, processing_status")
                    .order("uploaded_at", desc=True)
                    .limit(20)
                    .execute().data or []
                )
            except Exception:
                docs = []

    if not docs:
        st.markdown(
            '<div class="empty-state"><div style="font-size:60px;">📭</div>'
            '<h3>No documents</h3></div>',
            unsafe_allow_html=True,
        )

    for d in docs:
        document_card(d)


# ═══════════════════════════════════════════════════════════
# MESSAGES PAGE
# ═══════════════════════════════════════════════════════════

def show_messages():
    """Real messaging with Inbox/Sent/Compose."""
    u = st.session_state.user or {}
    st.markdown("### 💬 Messages")

    if not supabase:
        st.warning("Supabase is required for messaging.")
        return

    tab_inbox, tab_sent, tab_compose = st.tabs(["📩 Inbox", "📤 Sent", "✍️ Compose"])

    with tab_compose:
        with st.form("compose_message_form"):
            recipient = st.text_input("To (email)")
            subject = st.text_input("Subject")
            body = st.text_area("Message", height=150)
            if st.form_submit_button("Send"):
                if not recipient or not body:
                    show_toast("Recipient and message are required", "warning")
                elif not validate_email(recipient):
                    show_toast("Invalid recipient email", "error")
                else:
                    try:
                        supabase.table("messages").insert({
                            "sender_email": u.get("email", ""),
                            "recipient_email": recipient.strip().lower(),
                            "subject": subject,
                            "body": sanitize_input(body),
                            "read": False,
                            "is_starred": False,
                            "created_at": now_utc().isoformat(),
                        }).execute()
                        show_toast("Message sent!")
                        st.rerun()
                    except Exception as e:
                        show_toast(f"Failed to send message: {str(e)}", "error")

    with tab_inbox:
        inbox_msgs = []
        try:
            inbox_msgs = (
                supabase.table("messages")
                .select("*")
                .eq("recipient_email", u.get("email", ""))
                .order("created_at", desc=True)
                .limit(50)
                .execute().data or []
            )
        except Exception:
            pass

        if not inbox_msgs:
            st.markdown(
                '<div class="empty-state"><div style="font-size:60px;">📭</div>'
                '<h3>No messages</h3></div>',
                unsafe_allow_html=True,
            )
        for m in inbox_msgs:
            icon = "📬" if not m.get("read") else "📩"
            with st.expander(
                f"{icon} {html.escape(str(m.get('subject') or 'No Subject'))} — "
                f"From: {html.escape(str(m.get('sender_email', 'Unknown')))}"
            ):
                st.caption(str(m.get("created_at", ""))[:16])
                st.write(html.escape(str(m.get("body", ""))))
                if not m.get("read"):
                    if st.button("Mark as Read", key=f"read_{m.get('id')}"):
                        try:
                            supabase.table("messages").update(
                                {"read": True}
                            ).eq("id", m.get("id")).execute()
                            st.rerun()
                        except Exception:
                            pass

    with tab_sent:
        sent_msgs = []
        try:
            sent_msgs = (
                supabase.table("messages")
                .select("*")
                .eq("sender_email", u.get("email", ""))
                .order("created_at", desc=True)
                .limit(50)
                .execute().data or []
            )
        except Exception:
            pass

        if not sent_msgs:
            st.markdown(
                '<div class="empty-state"><div style="font-size:60px;">📤</div>'
                '<h3>No sent messages</h3></div>',
                unsafe_allow_html=True,
            )
        for m in sent_msgs:
            with st.expander(
                f"📤 To: {html.escape(str(m.get('recipient_email', 'Unknown')))} — "
                f"{html.escape(str(m.get('subject') or 'No Subject'))}"
            ):
                st.caption(str(m.get("created_at", ""))[:16])
                st.write(html.escape(str(m.get("body", "")))) 
    # ═══════════════════════════════════════════════════════════
# AI CHAT (Document-First: Search Docs → DeepSeek → Web → Groq)
# ═══════════════════════════════════════════════════════════

def show_ai():
    """
    DOCUMENT-FIRST AI FLOW:
      1. Search Supabase documents first (keyword → fuzzy → semantic)
      2. If found → answer with DeepSeek (doc_qa) + show sources
      3. If not → web search → answer with Groq (deep_search)
    """
    st.markdown("### 🤖 AI Rules Assistant")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # ── Header controls ──
    col_h1, col_h2 = st.columns([4, 1])
    with col_h1:
        st.caption("Ask about leave rules, TA/DA, vehicle registration, or any office circular.")
    with col_h2:
        if st.button("🗑️ Clear Chat", key="clear_ai_chat"):
            st.session_state.messages = []
            st.rerun()

    # ── Chat history ──
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m.get("sources"):
                with st.expander(f"📄 {len(m['sources'])} source document(s)"):
                    for s in m["sources"]:
                        st.markdown(f"- **{s.get('filename', 'Document')}**: {str(s.get('ai_summary', ''))[:150]}")

    # ── Input ──
    if p := st.chat_input("E.g., How many days of Earned Leave can be encashed at retirement?"):
        p_clean = sanitize_input(p)
        st.session_state.messages.append({"role": "user", "content": p_clean})
        with st.chat_message("user"):
            st.markdown(p_clean)

        with st.chat_message("assistant"):
            # ── STEP 1: Search documents FIRST ──
            src = search_documents(p_clean, 4)
            web = ""
            role = "doc_qa"

            if src:
                # ── STEP 2a: Answer from documents using DeepSeek ──
                ctx = (
                    "You are an internal staff knowledge assistant for a state transport "
                    "department office. Answer using ONLY the document context below. "
                    "If it isn't specific enough to answer confidently, ask a short "
                    "clarifying question instead of guessing. Always tell the user to "
                    "confirm exact figures against the current G.O. before official use.\n\n"
                    "DOCUMENT CONTEXT:\n"
                    + "\n".join([
                        f"- {s.get('filename', 'Source')}: {s.get('ai_summary', '') or str(s.get('full_text_preview', ''))[:300]}"
                        for s in src
                    ])
                )
            else:
                # ── STEP 2b: Web search using Groq ──
                role = "deep_search"
                web = agentic_web_search(p_clean, "gov")
                if not web.strip():
                    web = agentic_web_search(p_clean, "deep")
                ctx = (
                    "No matching internal document was found. Answer using ONLY the web "
                    "results below. If they don't answer the question, say so plainly "
                    "instead of guessing.\n\nWEB RESULTS:\n" + web
                )

            history = "\n".join([
                f"{m['role']}: {m['content']}"
                for m in st.session_state.messages[-6:]
            ])
            prompt = f"{ctx}\n\nRecent conversation:\n{history}\n\nQuestion: {p_clean}"

            with st.spinner("Thinking..." if not src else "Checking your documents..."):
                r = ai_system.request(prompt, role=role)

            if r.get("success") and r.get("response"):
                resp = r["response"]
                provider = r.get("provider", "AI")
                st.markdown(resp)
                if provider not in ("cache", "semantic_cache"):
                    st.caption(f"⚡ Answered by: {provider}" + (" • 📄 from your documents" if src else " • 🌐 from web"))
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": resp,
                    "sources": src if src else None,
                })

                # Show source documents with download
                if src:
                    st.markdown("---")
                    st.markdown("**📎 Source Documents:**")
                    for s in src[:3]:
                        document_card(s)
            else:
                error_msg = r.get('error', 'AI service unavailable')
                st.warning(f"⚠️ AI service issue: {error_msg}")

                # ── Graceful fallback ──
                fallback = ""
                if src:
                    fallback = "📄 **Based on your documents, I found:**\n\n"
                    for s in src[:3]:
                        fallback += f"- **{s.get('filename', 'Document')}**: {s.get('ai_summary', 'No summary available')}\n"
                    fallback += "\n*AI summarization is currently unavailable. Please review these documents manually.*"
                elif web.strip():
                    fallback = "🌐 **Web search results found:**\n\n"
                    for line in web.split('\n')[:6]:
                        if line.strip():
                            fallback += f"{line}\n"
                    fallback += "\n*AI analysis is currently unavailable. Please review these sources manually.*"
                else:
                    fallback = (
                        "❓ I couldn't find relevant information in your documents or on the web. "
                        "Please try rephrasing your question or check if AI API keys are configured "
                        "in Admin Panel → AI Settings."
                    )
                st.markdown(fallback)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": fallback,
                    "sources": src if src else None,
                })


# ═══════════════════════════════════════════════════════════
# SYSTEM HEALTH
# ═══════════════════════════════════════════════════════════

def show_system_health():
    st.markdown("### 🩺 System Health Check")
    cols = st.columns(4)

    with cols[0]:
        if supabase:
            try:
                supabase.table("users").select("id").limit(1).execute()
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
                b2_client.head_bucket(Bucket=storage_system.cold_bucket)
                storage_status.append("✅ B2")
            except Exception:
                storage_status.append("❌ B2")
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


def get_office_directory(office_code):
    """Fetch office directory from CF Worker or Supabase fallback."""
    worker_url = secret("CF_WORKER_URL", "")
    if worker_url:
        try:
            resp = requests.get(
                f"{worker_url}/directory",
                params={"office": office_code},
                timeout=2,
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
    try:
        if supabase:
            return (
                supabase.table("users")
                .select("name, designation, section, seat_number")
                .eq("office_code", office_code)
                .execute()
                .data or []
            )
    except Exception:
        pass
    return [] 
    if storj_client:
    try:
        storj_client.head_bucket(Bucket=storage_system.archive_bucket)
        storage_status.append("✅ Storj")
    except Exception:
        storage_status.append("❌ Storj")
if minio_client:
    try:
        minio_client.bucket_exists(storage_system.processing_bucket)
        storage_status.append("✅ MinIO")
    except Exception:
        storage_status.append("❌ MinIO") 
    # Add after Qdrant check
if d1_client:
    try:
        d1_client.query("SELECT 1")
        st.success("✅ Cloudflare D1: Connected")
    except Exception:
        st.error("❌ Cloudflare D1: Down")
else:
    st.warning("⚠️ Cloudflare D1: Not configured")


# ═══════════════════════════════════════════════════════════
# ADMIN PANEL
# ═══════════════════════════════════════════════════════════

RTA_ROLES = [
    "Junior Assistant (Jr Asst)",
    "Senior Assistant (Sr Asst)",
    "Assistant Officer (AO)",
    "Regional Transport Officer (RTO)",
    "Deputy Transport Commissioner (DTC)",
    "Motor Vehicle Inspector (MVI)",
    "Assistant Motor Vehicle Inspector (AMVI)",
]

SYSTEM_ROLES = ["staff", "office_admin", "system_admin"]


def show_admin():
    u = st.session_state.user or {}
    if u.get("admin_level") not in ["system_admin", "office_admin"]:
        st.warning("Access denied")
        return

    st.markdown("### 🏛️ Admin Panel")
    section = st.radio(
        "Section",
        [
            "🩺 Health", "👥 Users", "⚙️ AI Settings", "🧠 AI Training",
            "📊 Storage", "🔄 Maintenance", "📋 Audit", "🚨 Emergency",
            "📢 Announcements", "📊 Analytics",
        ],
        horizontal=True,
        label_visibility="collapsed",
        key="admin_section",
    )

    # ── HEALTH ──
    if section == "🩺 Health":
        st.markdown("#### 🩺 Health")
        if st.button("Check Health", key="health_check_admin"):
            show_system_health()

        st.divider()
        st.markdown("#### 📜 Recent Errors")
        if supabase:
            try:
                errs = (
                    supabase.table("audit_logs")
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

    # ── USERS ──
    elif section == "👥 Users":
        st.markdown("#### 👥 Users")
        st.info("Passwords are stored as secure hashes. Admin cannot view passwords, but can reset them.")

        with st.expander("➕ Add User"):
            with st.form("add_user_form"):
                c1, c2 = st.columns(2)
                with c1:
                    ne = st.text_input("Email")
                    nn = st.text_input("Name")
                    nd = st.selectbox("RTA Designation", RTA_ROLES)
                with c2:
                    seat = st.text_input("Seat Number")
                    na = st.selectbox("System Access Role", SYSTEM_ROLES)
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
                            try:
                                supabase.table("users").insert({
                                    "email": ne.strip().lower(),
                                    "name": nn,
                                    "designation": nd,
                                    "seat_number": seat,
                                    "password_hash": hash_password(pw),
                                    "admin_level": na,
                                    "active": True,
                                }).execute()
                                show_toast(f"Created user. Password: {pw}")
                            except Exception:
                                show_toast("Failed to create user", "error")

        with st.expander("📥 Bulk Import CSV"):
            csvf = st.file_uploader(
                "CSV columns: email,name,designation,seat_number,admin_level,password",
                type=["csv"],
            )
            if csvf and st.button("Import", key="bulk_import_admin"):
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
                        seat_number = csv_str(row, "seat_number")
                        admin_level = csv_str(row, "admin_level") or "staff"
                        password = csv_str(row, "password") or secrets.token_urlsafe(10)
                        if email and name and validate_email(email) and len(password) >= 8:
                            try:
                                supabase.table("users").insert({
                                    "email": email,
                                    "name": name,
                                    "designation": designation,
                                    "seat_number": seat_number,
                                    "password_hash": hash_password(password),
                                    "admin_level": admin_level,
                                    "active": True,
                                }).execute()
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
        if supabase:
            try:
                users = supabase.table("users").select("*").order("name").execute().data or []
            except Exception:
                users = []

        if not users:
            st.info("No users found.")

        for usr in users:
            usr_id = str(usr.get("id") or usr.get("email") or uuid.uuid4())
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(
                f"{'🟢' if usr.get('active', True) else '🔴'} "
                f"**{usr.get('name', 'Unknown')}** ({usr.get('email', '')})"
            )
            c2.write(f"**{usr.get('designation', 'N/A')}** | Access: `{usr.get('admin_level', 'staff')}`")

            if c3.button("🔑 Reset", key=f"rst_{usr_id}"):
                tp = secrets.token_urlsafe(10)
                try:
                    if usr.get("id"):
                        supabase.table("users").update(
                            {"password_hash": hash_password(tp)}
                        ).eq("id", usr.get("id")).execute()
                    else:
                        supabase.table("users").update(
                            {"password_hash": hash_password(tp)}
                        ).eq("email", usr.get("email")).execute()
                    show_toast(f"New password: {tp}")
                except Exception:
                    show_toast("Password reset failed", "error")

            with st.expander(f"⚙️ Manage {usr.get('name', 'User')}"):
                new_pass = st.text_input("Set New Password", type="password", key=f"np_{usr_id}")
                if st.button("Update Password", key=f"up_{usr_id}"):
                    if len(new_pass) < 8:
                        show_toast("Password must be at least 8 characters", "error")
                    else:
                        try:
                            if usr.get("id"):
                                supabase.table("users").update(
                                    {"password_hash": hash_password(new_pass)}
                                ).eq("id", usr.get("id")).execute()
                            else:
                                supabase.table("users").update(
                                    {"password_hash": hash_password(new_pass)}
                                ).eq("email", usr.get("email")).execute()
                            show_toast("Password updated")
                        except Exception:
                            show_toast("Password reset failed", "error")

                if st.button("Toggle Active Status", key=f"tg_{usr_id}"):
                    try:
                        new_active = not usr.get("active", True)
                        if usr.get("id"):
                            supabase.table("users").update(
                                {"active": new_active}
                            ).eq("id", usr.get("id")).execute()
                        else:
                            supabase.table("users").update(
                                {"active": new_active}
                            ).eq("email", usr.get("email")).execute()
                        if redis_client:
                            try:
                                redis_client.delete(f"user_v2:{usr.get('email')}")
                            except Exception:
                                pass
                        st.rerun()
                    except Exception:
                        show_toast("Toggle failed", "error")

    # ── AI SETTINGS (with MULTI-ACCOUNT key support) ──
    elif section == "⚙️ AI Settings":
        st.markdown("#### ⚙️ AI API Settings")
        st.info(
            "🔑 **Add or update your API keys here.** Keys are stored securely in the database. "
            "**Multi-account support:** paste multiple keys separated by commas "
            "(e.g., `sk-key1, sk-key2, sk-key3`) to rotate across accounts and avoid rate limits."
        )

        tab1, tab2, tab3 = st.tabs(["🔑 API Keys", "🧪 Test Connection", "📊 Status"])

        with tab1:
            st.markdown("##### 🔑 Enter Your API Keys")
            with st.form("ai_keys_form"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Primary Providers**")
                    deepseek_key = st.text_input(
                        "DeepSeek API Key(s)",
                        value=get_setting("DEEPSEEK_API_KEY"),
                        type="password",
                        placeholder="sk-... (comma-separate for multiple accounts)",
                        help="Primary for document Q&A. Get free key at platform.deepseek.com",
                    )
                    qwen_key = st.text_input(
                        "Qwen (DashScope) API Key(s)",
                        value=get_setting("QWEN_API_KEY"),
                        type="password",
                        placeholder="sk-... (comma-separate for multiple accounts)",
                        help="Primary for web search. Get free key at dashscope.aliyun.com",
                    )
                with col2:
                    st.markdown("**Backup Providers** (Optional)")
                    openai_key = st.text_input(
                        "OpenAI API Key",
                        value=get_setting("OPENAI_API_KEY"),
                        type="password",
                        placeholder="sk-...",
                        help="Used as backup",
                    )
                    gemini_key = st.text_input(
                        "Google Gemini API Key(s)",
                        value=get_setting("GEMINI_API_KEY"),
                        type="password",
                        placeholder="AIza... (comma-separate for multiple accounts)",
                        help="Used for embeddings + backup. Free tier at makersuite.google.com",
                    )

                col3, col4 = st.columns(2)
                with col3:
                    anthropic_key = st.text_input(
                        "Claude (Anthropic) API Key",
                        value=get_setting("ANTHROPIC_API_KEY"),
                        type="password",
                        placeholder="sk-ant-...",
                        help="Optional backup provider",
                    )
                with col4:
                    groq_key = st.text_input(
                        "Groq API Key(s)",
                        value=get_setting("GROQ_API_KEY"),
                        type="password",
                        placeholder="gsk_... (comma-separate for multiple accounts)",
                        help="Fast free-tier provider for web search analysis",
                    )

                st.divider()
                col5, col6 = st.columns(2)
                with col5:
                    serper_key = st.text_input(
                        "Serper API Key (Web Search)",
                        value=get_setting("SERPER_API_KEY"),
                        type="password",
                        placeholder="Optional - free DuckDuckGo fallback works without this",
                        help="Get free key at serper.dev",
                    )
                with col6:
                    st.text_input(
                        "OpenAI Embedding Key (deprecated — uses Gemini)",
                        value=get_setting("OPENAI_EMBEDDING_KEY"),
                        type="password",
                        disabled=True,
                        help="Embeddings now use Gemini text-embedding-004",
                    )

                submitted = st.form_submit_button("💾 Save All API Keys", use_container_width=True)
                if submitted:
                    saves = {
                        "DEEPSEEK_API_KEY": deepseek_key.strip(),
                        "QWEN_API_KEY": qwen_key.strip(),
                        "OPENAI_API_KEY": openai_key.strip(),
                        "GEMINI_API_KEY": gemini_key.strip(),
                        "ANTHROPIC_API_KEY": anthropic_key.strip(),
                        "GROQ_API_KEY": groq_key.strip(),
                        "SERPER_API_KEY": serper_key.strip(),
                    }
                    failed = [k for k, v in saves.items() if v and not set_setting(k, v)]
                    if failed:
                        err = st.session_state.get("_last_setting_error", "unknown error")
                        show_toast(f"⚠️ Saved locally but FAILED to persist: {', '.join(failed)}", "error")
                    else:
                        show_toast("✅ API keys saved to database — will survive logout")
                    st.rerun()

            with st.expander("🔗 Where to get free API keys?"):
                st.markdown("""
| Provider | Free Tier | Sign Up Link |
|----------|-----------|--------------|
| **DeepSeek** | ✅ Yes | [platform.deepseek.com](https://platform.deepseek.com/) |
| **Qwen (DashScope)** | ✅ Yes (100K tokens) | [dashscope.aliyun.com](https://dashscope.aliyun.com/) |
| **Gemini** | ✅ Yes (60 req/min) | [makersuite.google.com](https://makersuite.google.com/) |
| **Groq** | ✅ Yes | [console.groq.com](https://console.groq.com/) |
| **OpenAI** | ❌ Paid | [platform.openai.com](https://platform.openai.com/) |
| **Claude** | ❌ Paid | [console.anthropic.com](https://console.anthropic.com/) |
""")

        with tab2:
            st.markdown("##### 🧪 Test AI Connection")
            if st.button("🔍 Test All AI Providers", use_container_width=True):
                with st.spinner("Testing AI providers..."):
                    st.markdown("**Provider Configuration:**")
                    for role_label, role_key in [
                        ("💬 Chat", "chat"),
                        ("📄 Document Q&A", "doc_qa"),
                        ("🌐 Deep Search", "deep_search"),
                        ("📝 Summarization", "summarize"),
                    ]:
                        providers = ai_system.get_providers(role=role_key)
                        if providers:
                            st.success(f"✅ {role_label}: {', '.join([p['name'] for p in providers])}")
                        else:
                            st.error(f"❌ {role_label}: No providers configured")

                    st.markdown("**API Call Test:**")
                    with st.spinner("Making test API call..."):
                        test_result = ai_system.request("Reply with exactly: OK", role="chat")
                        if test_result.get("success"):
                            st.success(f"✅ API Call Successful via {test_result.get('provider')}")
                            st.info(f"Response: {str(test_result.get('response', ''))[:100]}")
                        else:
                            st.error(f"❌ API Call Failed: {test_result.get('error', 'Unknown error')}")

        with tab3:
            st.markdown("##### 📊 Current Configuration Status")
            status_data = []
            providers_config = [
                ("DeepSeek", "DEEPSEEK_API_KEY", "Primary - Document Q&A"),
                ("Qwen", "QWEN_API_KEY", "Primary - Web Search"),
                ("Gemini", "GEMINI_API_KEY", "Embeddings + Backup"),
                ("Groq", "GROQ_API_KEY", "Web Search Analysis"),
                ("OpenAI", "OPENAI_API_KEY", "Backup - Chat"),
                ("Anthropic", "ANTHROPIC_API_KEY", "Backup - Optional"),
                ("Serper", "SERPER_API_KEY", "Web Search API"),
            ]
            for provider, setting_key, purpose in providers_config:
                key = get_setting(setting_key)
                key_count = len([k for k in key.split(",") if k.strip()]) if key else 0
                status = f"✅ Configured ({key_count} key{'s' if key_count != 1 else ''})" if key else "❌ Not Configured"
                status_data.append({
                    "Provider": provider,
                    "Purpose": purpose,
                    "Status": status,
                })
            st.dataframe(pd.DataFrame(status_data), use_container_width=True)

            st.divider()
            st.markdown("**System Status:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                if redis_client:
                    try:
                        redis_client.get("health_check")
                        st.success("✅ Redis Cache: Working")
                    except Exception:
                        st.error("❌ Redis Cache: Failed")
                else:
                    st.warning("⚠️ Redis Cache: Not configured")
            with col2:
                if qdrant_client:
                    try:
                        qdrant_client.get_collections()
                        st.success("✅ Vector DB: Working")
                    except Exception:
                        st.error("❌ Vector DB: Failed")
                else:
                    st.warning("⚠️ Vector DB: Not configured")
            with col3:
                if supabase:
                    try:
                        supabase.table("app_settings").select("key").limit(1).execute()
                        st.success("✅ Settings DB: Working")
                    except Exception:
                        st.error("❌ Settings DB: Failed")
                else:
                    st.warning("⚠️ Settings DB: Not configured")

    # ── AI TRAINING ──
    elif section == "🧠 AI Training":
        st.markdown("#### 🧠 AI Training Sources")
        links = get_training_links()
        st.info(f"Trusted Sources: {len(links)}/30")

        if len(links) < 30:
            with st.form("add_training_link_form"):
                url = st.text_input("Website URL", placeholder="https://aptransport.org")
                title = st.text_input("Title (Optional)")
                if st.form_submit_button("➕ Add Trusted Source"):
                    if url:
                        if add_training_link(url, title, u.get("email", "")):
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
                f"**{link.get('title', 'Untitled')}**\n\n"
                f"🔗 {link.get('url', '')}\n\n"
                f"*Domain: `{link.get('domain', '')}`*"
            )
            if c2.button("🗑️ Delete", key=f"del_link_{link.get('id')}"):
                if delete_training_link(link.get("id")):
                    show_toast("Source removed")
                    st.rerun()
                else:
                    show_toast("Delete failed", "error")

    # ── STORAGE ──
    elif section == "📊 Storage":
        st.markdown("#### 📊 Storage")
        if st.button("Auto-Tier Documents", key="auto_tier_admin"):
            r = auto_tier_documents()
            if "error" in r:
                show_toast(r["error"], "error")
            else:
                show_toast(f"Moved {r.get('moved_to_cold', 0)} cold, {r.get('moved_to_hot', 0)} hot")

    # ── MAINTENANCE TASKS ──
    elif section == "🔄 Maintenance":
        st.markdown("#### 🔄 Maintenance Tasks")
        if st.button("Reprocess Failed Documents", key="reprocess_failed_admin"):
            if not supabase:
                show_toast("Supabase not configured", "warning")
            else:
                try:
                    failed = (
                        supabase.table("documents")
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
                                supabase.table("documents").update({
                                    "ai_summary": s,
                                    "processing_status": "ready",
                                }).eq("id", d.get("id")).execute()
                    show_toast(f"Reprocessed {len(failed)}")
                except Exception:
                    show_toast("Reprocess failed", "error")

        st.divider()
        if st.button("Clean Old Messages", key="clean_old_messages_admin"):
            cleanup_old_messages()
            show_toast("Old messages cleaned")

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
            if c2.button("Run", key=f"task_{tid}"):
                if not supabase:
                    show_toast("Supabase not configured", "warning")
                    continue
                with st.spinner("Running..."):
                    try:
                        if tid == "cleanup_login":
                            supabase.table("login_attempts").delete().lt(
                                "created_at", (now_utc() - timedelta(days=7)).isoformat()
                            ).execute()
                        elif tid == "auto_tier":
                            auto_tier_documents()
                        elif tid == "reset_stuck":
                            stuck = (
                                supabase.table("documents")
                                .select("id")
                                .eq("processing_status", "pending")
                                .lt("uploaded_at", (now_utc() - timedelta(hours=1)).isoformat())
                                .execute()
                            )
                            if stuck.data:
                                supabase.table("documents").update(
                                    {"processing_status": "failed"}
                                ).in_("id", [d.get("id") for d in stuck.data]).execute()
                        elif tid == "clean_sessions":
                            supabase.table("sessions").delete().lt(
                                "expires_at", now_utc().isoformat()
                            ).execute()
                        show_toast("Done!")
                        st.rerun()
                    except Exception:
                        show_toast("Task failed", "error")

    # ── AUDIT ──
    elif section == "📋 Audit":
        st.markdown("#### 📋 Audit")
        if supabase:
            try:
                logs = (
                    supabase.table("audit_logs")
                    .select("*")
                    .order("created_at", desc=True)
                    .limit(100)
                    .execute()
                    .data or []
                )
                if not logs:
                    st.info("No audit logs found.")
                for log in logs:
                    st.caption(
                        f"{str(log.get('created_at', ''))[:16]} | "
                        f"{log.get('user_email', '')} | "
                        f"{log.get('action', '')} | "
                        f"{log.get('resource_type', '')}"
                    )
            except Exception:
                st.warning("Could not read audit logs.")
        else:
            st.info("Supabase is not configured.")

    # ── EMERGENCY ──
    elif section == "🚨 Emergency":
        st.markdown("#### 🚨 Emergency")
        maint = False
        if redis_client:
            try:
                val = redis_client.get("maintenance_mode")
                if isinstance(val, bytes):
                    val = val.decode("utf-8", "ignore")
                maint = val == "1"
            except Exception:
                maint = False
        else:
            maint = bool(st.session_state.get("maintenance_mode", False))

        if not maint:
            if st.button("🔧 Enable Maintenance", type="secondary", key="enable_maintenance_admin"):
                if redis_client:
                    try:
                        redis_client.set("maintenance_mode", "1")
                    except Exception:
                        pass
                else:
                    st.session_state["maintenance_mode"] = True
                show_toast("Maintenance ON", "warning")
                st.rerun()
        else:
            st.warning("⚠️ In maintenance mode. Admins can still log in via the maintenance screen.")
            if st.button("✅ Disable Maintenance", key="disable_maintenance_admin"):
                if redis_client:
                    try:
                        redis_client.delete("maintenance_mode")
                    except Exception:
                        pass
                else:
                    st.session_state["maintenance_mode"] = False
                show_toast("Maintenance OFF")
                st.rerun()

        st.divider()
        if st.button("🔒 Force Logout All", type="secondary", key="force_logout_admin"):
            if supabase:
                try:
                    supabase.table("sessions").delete().neq("token_hash", "").execute()
                    show_toast("All sessions deleted", "warning")
                    st.rerun()
                except Exception:
                    show_toast("Could not delete sessions", "error")
            else:
                logout()

        if st.button("🗑️ Clear AI Cache", type="secondary", key="clear_ai_cache_admin"):
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

    # ── ANNOUNCEMENTS ──
    elif section == "📢 Announcements":
        st.markdown("#### 📢 Announcements")
        if not supabase:
            st.info("Supabase is not configured.")
        else:
            with st.form("announcement_form"):
                title = st.text_input("Title")
                msg = st.text_area("Message", height=100)
                pri = st.selectbox("Priority", ["info", "warning", "critical"])
                dur = st.number_input("Days", 1, 30, 7)
                if st.form_submit_button("Broadcast"):
                    if title and msg:
                        try:
                            supabase.table("announcements").insert({
                                "title": title,
                                "message": msg,
                                "priority": pri,
                                "expires_at": (now_utc() + timedelta(days=int(dur))).isoformat(),
                                "created_by": u.get("email", ""),
                            }).execute()
                            show_toast("Posted!")
                            st.rerun()
                        except Exception:
                            show_toast("Failed to post announcement", "error")

            st.divider()
            try:
                anns = (
                    supabase.table("announcements")
                    .select("*")
                    .gt("expires_at", now_utc().isoformat())
                    .order("created_at", desc=True)
                    .execute()
                    .data or []
                )
                for ann in anns:
                    c1, c2 = st.columns([4, 1])
                    icon = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(
                        ann.get("priority", "info"), "ℹ️"
                    )
                    c1.write(f"{icon} **{ann.get('title', '')}**")
                    c1.caption(f"{str(ann.get('message', ''))[:100]}...")
                    if c2.button("🗑️", key=f"dann_{ann.get('id')}"):
                        try:
                            supabase.table("announcements").delete().eq("id", ann.get("id")).execute()
                            st.rerun()
                        except Exception:
                            show_toast("Delete failed", "error")
            except Exception:
                pass

    # ── ANALYTICS ──
    elif section == "📊 Analytics":
        st.markdown("#### 📊 Analytics")
        if not supabase:
            st.info("Supabase is not configured.")
        else:
            try:
                logs = (
                    supabase.table("audit_logs")
                    .select("user_email, action")
                    .gte("created_at", (now_utc() - timedelta(days=30)).isoformat())
                    .execute()
                    .data or []
                )
                if logs:
                    users_list = supabase.table("users").select("email, office_name").execute().data or []
                    em = {x.get("email"): x.get("office_name", "Unknown") for x in users_list}
                    oc = {}
                    for l in logs:
                        o = em.get(l.get("user_email"), "Unknown")
                        oc[o] = oc.get(o, 0) + 1
                    if oc:
                        st.bar_chart(
                            pd.DataFrame([{"Office": k, "Actions": v} for k, v in oc.items()]).set_index("Office")
                        )
                    ac = {}
                    for l in logs:
                        ac[l.get("action")] = ac.get(l.get("action"), 0) + 1
                    st.markdown("##### Top Actions")
                    for a, c in sorted(ac.items(), key=lambda x: -x[1])[:10]:
                        st.write(f"**{a}**: {c}")
                else:
                    st.info("No analytics data found.")
            except Exception:
                st.warning("Analytics unavailable.")


# ═══════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ═══════════════════════════════════════════════════════════

def render_sidebar_nav():
    with st.sidebar:
        u = st.session_state.user or {}
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #0A66C2 0%, #004182 100%); padding: 16px; border-radius: 12px; color: white; margin-bottom: 20px;">
                <div style="font-size: 14px; opacity: 0.9;">Welcome,</div>
                <div style="font-size: 18px; font-weight: 700;">{html.escape(str(u.get('name', 'User')))}</div>
                <div style="font-size: 12px; opacity: 0.8;">🏢 {html.escape(str(u.get('office_name', 'Office')))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        menu_items = ["Feed", "Workspace", "Tapal", "Dispatch", "Documents", "Messages", "AI Assistant"]
        menu_icons = ["house", "briefcase", "envelope-paper", "send", "file-earmark-text", "chat", "robot"]

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
            except ValueError:
                default_index = 0

        selected = None
        if OPTION_MENU_LIB and option_menu:
            try:
                selected = option_menu(
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
                selected = None

        if selected is None:
            selected = st.radio("Navigation", menu_items, index=default_index)

        st.divider()
        if st.button("🚪 Logout", use_container_width=True, type="secondary", key="logout_nav"):
            logout()

        st.session_state.page = page_map.get(selected, "feed")


# ═══════════════════════════════════════════════════════════
# MAIN (with MAINTENANCE ADMIN BYPASS)
# ═══════════════════════════════════════════════════════════

def main():
    """
    BUG FIX: Login check moved BEFORE maintenance check so admins
    are never locked out. Maintenance screen includes a hidden
    Admin/Staff login expander to escape maintenance mode.
    """
   def main():
    # 1. Initialize session state
    init_session_state()
    
    # 2. Ensure admin user exists (first run only)
    if supabase:
        try:
            ensure_admin_user()
            ensure_default_users()  # Optional
        except Exception as e:
            logger.error(f"User initialization failed: {e}")
    
    # 3. Try auto-login
    try_auto_login()

    # 2. Check maintenance status
    maint = False
    if redis_client:
        try:
            val = redis_client.get("maintenance_mode")
            if isinstance(val, bytes):
                val = val.decode("utf-8", "ignore")
            maint = val == "1"
        except Exception:
            maint = False
    else:
        maint = bool(st.session_state.get("maintenance_mode", False))

    # 3. Check if user is an admin
    is_admin = (
        st.session_state.get("logged_in")
        and st.session_state.get("admin_level") in ["system_admin", "office_admin"]
    )

    # 4. Maintenance screen with admin bypass
    if maint and not is_admin:
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
        # Hidden login for admins to escape maintenance mode
        with st.expander("🔒 Admin / Staff Login"):
            show_login()
        return

    # 5. Normal flow for logged-out users
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
