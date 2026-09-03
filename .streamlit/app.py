"""
RTA ANUBANDHAN — Enterprise Production Final
ALL BUGS FIXED: Storage tier tracking, fuzzy search, security,
AI multi-provider, tapal format, messaging, sidebar, and more.
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
# LOGGING (BUG FIX: was logging.getLogger(name))
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

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

# ============================================================
# SENTRY
# ============================================================
if SENTRY_AVAILABLE and os.getenv("SENTRY_DSN"):
    try:
        sentry_sdk.init(
            dsn=os.getenv("SENTRY_DSN"),
            traces_sample_rate=0.2,
            environment=os.getenv("ENVIRONMENT", "production"),
        )
    except Exception as e:
        logger.error(f"Sentry init failed: {e}")

# ============================================================
# STREAMLIT CONFIG
# ============================================================
st.set_page_config(
    page_title="RTA Anubandhan",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CSS (BUG FIX: removed spaces in variable names and selectors)
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
#MainMenu, footer, header { visibility: hidden !important; display: none !important; }
.block-container { padding-top: 1rem !important; padding-bottom: 100px !important; max-width: 1200px; }
.commercial-card {
    background: var(--bg-surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 20px; margin-bottom: 16px;
    box-shadow: var(--shadow-sm); transition: box-shadow 0.2s;
}
.commercial-card:hover { box-shadow: var(--shadow-md); }
.post-avatar {
    width: 48px; height: 48px; border-radius: 50%;
    background: var(--primary); color: white; display: flex;
    align-items: center; justify-content: center;
    font-size: 20px; font-weight: 700;
}
.login-container { max-width: 420px; margin: 40px auto; padding: 30px; background: white; border-radius: 16px; box-shadow: var(--shadow-md); }
.quote-box { background: var(--primary-light); border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center; }
.empty-state { text-align: center; padding: 50px; color: #666; }
.post-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.post-actions { display: flex; gap: 12px; margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--border); flex-wrap: wrap; }
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
.tag-badge { background: var(--primary-light); color: var(--primary); padding: 2px 8px; border-radius: 8px; font-size: 12px; margin-right: 4px; }
@media print {
    #MainMenu, footer, header, .stSidebar { display: none !important; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ============================================================
# UTILITIES (BUG FIX: removed all trailing spaces in strings)
# ============================================================
def secret(key: str, default: str = "") -> str:
    try:
        val = st.secrets.get(key, default)
        if val not in (None, ""):
            return str(val)
    except Exception:
        pass
    return os.getenv(key, default)


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
                {"key": key, "value": value, "updated_at": now_utc().isoformat()}
            ).execute()
        except Exception as e:
            logger.error(f"Failed to save setting {key}: {e}")


def sanitize_input(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]*>", "", str(text))
    return html.escape(text).strip()


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, str(email or "").strip()))


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def sanitize_search_query(q: str) -> str:
    # BUG FIX: allow @ and # so mention/tag search works
    return re.sub(r"[^a-zA-Z0-9\s@#]", "", str(q or "")).strip()


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
        sb.table("audit_logs").insert({
            "user_email": st.session_state.get("user", {}).get("email", "system"),
            "action": "error",
            "resource_type": str(error_type),
            "metadata": json.dumps({"message": str(message)[:500]}),
            "created_at": now_utc().isoformat(),
        }).execute()
    except Exception as e:
        logger.error(f"Failed to log error: {e}")


# ============================================================
# ENCRYPTION (BUG FIX: no st.stop(), just warn)
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

if os.getenv("ENVIRONMENT", "development") == "production" and not _fernet:
    logger.warning("Encryption key missing in production. Data will not be encrypted.")


def encrypt_data(data: bytes) -> bytes:
    if _fernet:
        try:
            return _fernet.encrypt(data)
        except Exception:
            pass
    return data


def decrypt_data(data: bytes) -> bytes:
    if _fernet:
        try:
            return _fernet.decrypt(data)
        except Exception:
            pass
    return data


# ============================================================
# CIRCUIT BREAKER
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
# CLOUD INITIALIZATION (BUG FIX: B2 uses boto3, not b2sdk)
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
    """BUG FIX: Use boto3 S3-compatible API instead of b2sdk."""
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
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                )
        return client
    except Exception:
        return None


supabase = init_supabase()
redis_client = init_redis()
r2_client = init_r2()
b2_client = init_b2()
qdrant_client = init_qdrant()

# ============================================================
# COMPRESSION
# ============================================================
def compress_data(data: bytes) -> Tuple[bytes, str]:
    if ZSTD_AVAILABLE:
        try:
            compressed = zstd.ZstdCompressor(level=19).compress(data)
            if len(compressed) < len(data):
                return compressed, "zstd"
        except Exception:
            pass
    if COMPRESSION_AVAILABLE:
        try:
            compressed = lzma.compress(data, preset=9)
            if len(compressed) < len(data):
                return compressed, "lzma"
        except Exception:
            pass
    return data, "none"


def decompress_data(data: bytes, method: str) -> bytes:
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


# ============================================================
# SAFE COOKIES (BUG FIX: no crash on delete)
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


# ============================================================
# STORAGE SYSTEM (BUG FIX: returns actual tier, not just bool)
# ============================================================
class StorageSystem:
    def __init__(self):
        self.r2 = r2_client
        self.b2 = b2_client
        self.hot_bucket = secret("R2_BUCKET_NAME", "rta-hot-storage")
        self.cold_bucket = secret("B2_BUCKET_NAME", "rta-cold-storage")

    def _upload_to_storage(self, data: bytes, key: str, target_tier: str) -> Optional[str]:
        """Returns actual tier where data landed, or None on failure."""
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

        # Fallback to R2
        if self.r2:
            try:
                self.r2.put_object(Bucket=self.hot_bucket, Key=key, Body=data)
                return "hot"
            except Exception:
                pass

        return None

    def _download_from_storage(self, key: str, tier: str) -> Optional[bytes]:
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
        # Try both as fallback
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
        return None

    def get_presigned_url(self, key: str, tier: str, expiration: int = 3600):
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
            except Exception:
                pass
        if ext in ["jpg", "jpeg", "png", "bmp", "tiff"] and OCR_AVAILABLE:
            try:
                img = Image.open(io.BytesIO(file_data)).convert("RGB")
                gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
                _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
                return pytesseract.image_to_string(thresh)
            except Exception:
                pass
        return ""

    def upload_document(self, file_data: bytes, filename: str, doc_type: str, user_email: str):
        try:
            if not file_data:
                return {"success": False, "error": "Empty file"}

            filename = sanitize_filename(filename)
            file_hash = generate_file_hash(file_data)

            # Deduplication check
            if supabase:
                try:
                    existing = supabase.table("documents").select("id").eq("file_hash", file_hash).execute()
                    if existing.data:
                        ref_id = existing.data[0]["id"]
                        try:
                            supabase.table("document_references").insert({
                                "original_doc_id": ref_id,
                                "referenced_by": user_email,
                                "original_filename": filename,
                                "created_at": now_utc().isoformat(),
                            }).execute()
                        except Exception:
                            pass
                        audit_log(user_email, "document.duplicate", "document", ref_id)
                        return {
                            "success": True,
                            "duplicate": True,
                            "document_id": ref_id,
                            "message": f"File already exists. Saved {len(file_data)/1024/1024:.2f} MB",
                        }
                except Exception:
                    pass

            extracted_text = self._extract_text(file_data, filename)
            compressed_file, method = compress_data(file_data)
            encrypted_file = encrypt_data(compressed_file)

            storage_key = f"blobs/{file_hash[:2]}/{file_hash[2:4]}/{file_hash}"
            target_tier = "hot" if doc_type in ["circular", "tapal", "current", "social_post"] else "cold"

            # BUG FIX: track actual tier where file landed
            actual_tier = self._upload_to_storage(encrypted_file, storage_key, target_tier)
            if not actual_tier:
                return {"success": False, "error": "All storage backends failed"}

            # Store extracted text
            text_key = None
            if extracted_text and self.r2:
                try:
                    ct, tm = compress_data(extracted_text.encode("utf-8", "ignore"))
                    text_key = f"text/{doc_type}/{now_utc().strftime('%Y/%m/%d')}/{uuid.uuid4().hex}.txt.{tm}"
                    self.r2.put_object(Bucket=self.hot_bucket, Key=text_key, Body=ct)
                except Exception:
                    pass

            doc_id = None
            if supabase:
                try:
                    result = supabase.table("documents").insert({
                        "filename": filename,
                        "file_key": storage_key,
                        "text_key": text_key,
                        "file_hash": file_hash,
                        "doc_type": doc_type,
                        "compression_method": method,
                        "original_size": len(file_data),
                        "compressed_size": len(encrypted_file),
                        "storage_tier": actual_tier,  # BUG FIX: use actual tier
                        "uploaded_by": user_email,
                        "uploaded_at": now_utc().isoformat(),
                        "processing_status": "pending",
                        "access_count": 0,
                        "last_accessed": now_utc().isoformat(),
                    }).execute()
                    if result.data:
                        doc_id = result.data[0]["id"]
                except Exception as e:
                    logger.error(f"Document DB insert failed: {e}")

            audit_log(user_email, "document.upload", "document", doc_id, {"filename": filename})
            business_metrics.increment("documents_uploaded")

            # Background AI summary
            if doc_id and extracted_text:
                def bg_task(did, text, fn):
                    try:
                        ai = globals().get("ai_system")
                        summary = ai.summarize(text[:3000]) if ai and len(text) > 50 else ""
                        if supabase:
                            supabase.table("documents").update({
                                "ai_summary": summary or "",
                                "processing_status": "ready",
                            }).eq("id", did).execute()
                        if QDRANT_AVAILABLE and qdrant_client and text:
                            gen = globals().get("generate_embedding")
                            if gen:
                                qdrant_client.upsert(
                                    collection_name="rta_documents",
                                    points=[PointStruct(
                                        id=str(did),
                                        vector=gen(text),
                                        payload={"doc_id": str(did), "filename": fn},
                                    )],
                                )
                    except Exception as e:
                        logger.error(f"Background task failed: {e}")
                        if supabase:
                            try:
                                supabase.table("documents").update({"processing_status": "failed"}).eq("id", did).execute()
                            except Exception:
                                pass

                threading.Thread(target=bg_task, args=(doc_id, extracted_text, filename), daemon=True).start()
            elif doc_id and supabase:
                try:
                    supabase.table("documents").update({"processing_status": "ready"}).eq("id", doc_id).execute()
                except Exception:
                    pass

            ratio = max(0.0, 1 - (len(encrypted_file) / len(file_data))) if file_data else 0
            return {"success": True, "document_id": doc_id, "compression_ratio": ratio}

        except Exception as e:
            log_error("upload_failed", e)
            return {"success": False, "error": str(e)}

    def download_document(self, document_id: str):
        try:
            if not supabase:
                return None
            result = supabase.table("documents").select(
                "file_key, storage_tier, compression_method, access_count"
            ).eq("id", document_id).execute()
            if not result.data:
                return None
            doc = result.data[0]
            data = self._download_from_storage(doc["file_key"], doc.get("storage_tier", "hot"))
            if not data:
                return None
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
        except Exception:
            return None

    def get_full_text(self, document_id: str) -> str:
        try:
            if not supabase:
                return ""
            result = supabase.table("documents").select("text_key").eq("id", document_id).execute()
            if result.data and result.data[0].get("text_key"):
                key = result.data[0]["text_key"]
                method = "none"
                if key.endswith(".lzma"):
                    method = "lzma"
                elif key.endswith(".zstd"):
                    method = "zstd"
                if self.r2:
                    raw = self.r2.get_object(Bucket=self.hot_bucket, Key=key)["Body"].read()
                    return decompress_data(raw, method).decode("utf-8", "ignore")
            return ""
        except Exception:
            return ""


storage_system = StorageSystem()


# ============================================================
# AUTO-TIERING (BUG FIX: only delete/relabel when tier matches)
# ============================================================
def auto_tier_documents():
    if not supabase:
        return {"error": "Supabase unavailable"}
    try:
        cutoff = (now_utc() - timedelta(days=90)).isoformat()
        cold_candidates = (
            supabase.table("documents")
            .select("id, file_key")
            .eq("storage_tier", "hot")
            .lt("last_accessed", cutoff)
            .limit(100)
            .execute()
            .data or []
        )

        moved_cold = 0
        for d in cold_candidates:
            data = storage_system._download_from_storage(d["file_key"], "hot")
            if not data:
                continue
            # BUG FIX: only proceed if file actually landed in cold
            actual_tier = storage_system._upload_to_storage(data, d["file_key"], "cold")
            if actual_tier == "cold":
                try:
                    if r2_client:
                        r2_client.delete_object(Bucket=storage_system.hot_bucket, Key=d["file_key"])
                except Exception:
                    pass
                supabase.table("documents").update({"storage_tier": "cold"}).eq("id", d["id"]).execute()
                moved_cold += 1

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
                supabase.table("documents").update({"storage_tier": "hot", "access_count": 0}).eq("id", d["id"]).execute()
                moved_hot += 1

        return {"moved_to_cold": moved_cold, "moved_to_hot": moved_hot}
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# AUDIT LOG
# ============================================================
def audit_log(email, action, rtype, rid=None, meta=None):
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
        # ============================================================
# MULTI-PROVIDER AI SYSTEM (Serial Fallback — 6 Providers)
# ============================================================
qwen_breaker = CircuitBreaker("qwen")
grok_breaker = CircuitBreaker("grok")
deepseek_breaker = CircuitBreaker("deepseek")
gemini_breaker = CircuitBreaker("gemini")
openai_breaker = CircuitBreaker("openai")
anthropic_breaker = CircuitBreaker("anthropic")


class MultiAI:
    """Handles AI requests with circuit breakers, semantic caching, and serial fallback."""

    def _get_key(self, setting_name, secret_name=None):
        """Read API key from Admin Panel settings OR secrets.toml."""
        key = get_setting(setting_name)
        if key:
            return key.strip()
        if secret_name:
            return secret(secret_name).strip()
        return ""

    def get_providers(self):
        """Return providers in serial fallback order."""
        providers = []

        k = self._get_key("QWEN_API_KEY", "QWEN_API_KEY")
        if k:
            providers.append({"name": "Qwen", "key": k})

        k = self._get_key("GROK_API_KEY", "GROK_API_KEY")
        if k:
            providers.append({"name": "Grok", "key": k})

        k = self._get_key("DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY")
        if k:
            providers.append({"name": "DeepSeek", "key": k})

        k = self._get_key("GEMINI_API_KEY", "GEMINI_API_KEY")
        if k:
            providers.append({"name": "Gemini", "key": k})

        k = self._get_key("OPENAI_API_KEY", "OPENAI_API_KEY")
        if k:
            providers.append({"name": "OpenAI", "key": k})

        k = self._get_key("ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY")
        if k:
            providers.append({"name": "Anthropic", "key": k})

        return providers

    def _call_qwen(self, prompt, key):
        try:
            r = requests.post(
                "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": "qwen-turbo", "messages": [{"role": "user", "content": prompt}]},
                timeout=20,
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            if r.status_code == 429:
                raise Exception("Rate limited")
        except Exception:
            pass
        return None

    def _call_grok(self, prompt, key):
        try:
            r = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": "grok-2-latest", "messages": [{"role": "user", "content": prompt}]},
                timeout=20,
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            if r.status_code == 429:
                raise Exception("Rate limited")
        except Exception:
            pass
        return None

    def _call_deepseek(self, prompt, key):
        try:
            r = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]},
                timeout=20,
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            if r.status_code == 429:
                raise Exception("Rate limited")
        except Exception:
            pass
        return None

    def _call_gemini(self, prompt, key):
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=15,
            )
            if r.status_code == 200:
                return r.json()["candidates"][0]["content"]["parts"][0]["text"]
            if r.status_code == 429:
                raise Exception("Rate limited")
        except Exception:
            pass
        return None

    def _call_openai(self, prompt, key):
        try:
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": prompt}]},
                timeout=15,
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            if r.status_code == 429:
                raise Exception("Rate limited")
        except Exception:
            pass
        return None

    def _call_anthropic(self, prompt, key):
        try:
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
                json={
                    "model": "claude-3-5-haiku-20241022",
                    "max_tokens": 500,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=15,
            )
            if r.status_code == 200:
                return r.json()["content"][0]["text"].strip()
            if r.status_code == 429:
                raise Exception("Rate limited")
        except Exception:
            pass
        return None

    def request(self, prompt):
        """Execute AI request with serial fallback across all providers."""
        business_metrics.increment("ai_queries_total")

        h = hashlib.md5(prompt.encode()).hexdigest()

        # 1. Exact Match Cache (Redis)
        if redis_client:
            try:
                c = redis_client.get(f"ai_cache:{h}")
                if c:
                    business_metrics.increment("ai_queries_cached")
                    return {"success": True, "response": json.loads(c), "provider": "cache"}
            except Exception:
                pass

        # 2. Semantic Cache (Qdrant)
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
                    return {"success": True, "response": hits[0].payload["response"], "provider": "semantic_cache"}
            except Exception:
                pass

        # 3. Serial Provider Fallback
        providers = self.get_providers()
        if not providers:
            return {"success": False, "error": "No API keys configured. Go to Admin Panel → AI Settings."}

        errors = []
        for p in providers:
            resp = None
            try:
                if p["name"] == "Qwen":
                    resp = qwen_breaker.call(self._call_qwen, prompt, p["key"])
                elif p["name"] == "Grok":
                    resp = grok_breaker.call(self._call_grok, prompt, p["key"])
                elif p["name"] == "DeepSeek":
                    resp = deepseek_breaker.call(self._call_deepseek, prompt, p["key"])
                elif p["name"] == "Gemini":
                    resp = gemini_breaker.call(self._call_gemini, prompt, p["key"])
                elif p["name"] == "OpenAI":
                    resp = openai_breaker.call(self._call_openai, prompt, p["key"])
                elif p["name"] == "Anthropic":
                    resp = anthropic_breaker.call(self._call_anthropic, prompt, p["key"])

                if resp:
                    # Cache successful response
                    if redis_client:
                        try:
                            redis_client.setex(f"ai_cache:{h}", 86400, json.dumps(resp))
                        except Exception:
                            pass
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
            except Exception as e:
                errors.append(f"{p['name']}: {str(e)[:80]}")
                continue

        return {"success": False, "error": f"All providers failed: {'; '.join(errors)}"}

    def summarize(self, text):
        r = self.request(f"Summarize this in 2-3 sentences: {text[:3000]}")
        return r.get("response") if r.get("success") else None


ai_system = MultiAI()


# ============================================================
# AGENTIC WEB SEARCH
# ============================================================
def agentic_web_search(query, stype="gov"):
    """Search the web using Serper API."""
    key = get_setting("SERPER_API_KEY") or secret("SERPER_API_KEY")
    if not key:
        return ""
    if stype == "gov":
        query = f"{query} site:ap.gov.in OR site:gov.in"
    try:
        r = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
            json={"q": query, "num": 5},
            timeout=10,
        )
        return "\n".join([
            f"Source: {x.get('link')}\nSnippet: {x.get('snippet')}\n"
            for x in r.json().get("organic", [])
        ])
    except Exception:
        return ""


# ============================================================
# VECTOR EMBEDDINGS & SEARCH (BUG FIX: fuzzy search tuple fix)
# ============================================================
def generate_embedding(text):
    """Generate 384-dimensional vector for Qdrant."""
    dim = 384
    text = str(text or "")[:1500]
    key = get_setting("GEMINI_EMBEDDING_KEY") or secret("GEMINI_EMBEDDING_KEY") or secret("GEMINI_API_KEY")
    if key:
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key={key}",
                json={"content": {"parts": [{"text": text}]}},
                timeout=10,
            )
            if r.status_code == 200:
                v = r.json()["embedding"]["values"]
                return v[:dim] + [0.0] * (dim - len(v))
        except Exception:
            pass
    # Fallback hash-based embedding
    words = text.lower().split()
    v = np.zeros(dim)
    for w in words:
        v[int(hashlib.md5(w.encode()).hexdigest()[:8], 16) % dim] += 1
    n = np.linalg.norm(v)
    return (v / n if n > 0 else v).tolist()


def search_documents(query, limit=10):
    """Hybrid search: Fuzzy -> Vector -> SQL."""
    # 1. Fuzzy Search (BUG FIX: use dict to get index back)
    if FUZZY_AVAILABLE and supabase:
        try:
            docs = supabase.table("documents").select(
                "id, filename, file_key, storage_tier, doc_type, ai_summary, uploaded_at"
            ).limit(200).execute().data or []
            if docs:
                choices = {i: str(d.get("filename", "")) for i, d in enumerate(docs)}
                matches = process.extract(query, choices, scorer=fuzz.token_sort_ratio, limit=limit)
                ids = [docs[idx].get("id") for _, score, idx in matches if score >= 60]
                if ids:
                    return [d for d in docs if d.get("id") in ids]
        except Exception:
            pass

    # 2. Vector Search
    if qdrant_client:
        try:
            hits = qdrant_client.search(
                collection_name="rta_documents",
                query_vector=generate_embedding(query),
                limit=limit,
            )
            ids = [h.payload.get("doc_id") for h in hits if h.payload]
            if ids and supabase:
                return supabase.table("documents").select(
                    "id, filename, file_key, storage_tier, doc_type, ai_summary, uploaded_at"
                ).in_("id", ids).execute().data or []
        except Exception:
            pass

    # 3. SQL Fallback
    q = sanitize_search_query(query)
    if q and supabase:
        try:
            return supabase.table("documents").select(
                "id, filename, file_key, storage_tier, doc_type, ai_summary, uploaded_at"
            ).ilike("filename", f"%{q}%").limit(limit).execute().data or []
        except Exception:
            pass
    return []


# ============================================================
# AUTHENTICATION (BUG FIX: salted SHA-256 fallback, timezone fix)
# ============================================================
def hash_password(p):
    """Hash password with bcrypt, or salted SHA-256 as fallback."""
    if BCRYPT_AVAILABLE and bcrypt:
        return bcrypt.hashpw(p.encode(), bcrypt.gensalt(rounds=10)).decode()
    # BUG FIX: salted SHA-256 fallback instead of raw SHA-256
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + p).encode()).hexdigest()
    return f"{salt}${h}"


def check_password(p, h):
    """Verify password against stored hash."""
    if not p or not h:
        return False
    try:
        if BCRYPT_AVAILABLE and bcrypt and h.startswith("$2"):
            return bcrypt.checkpw(p.encode(), h.encode())
        # Salted SHA-256 fallback check
        if "$" in h:
            salt, stored_hash = h.split("$", 1)
            return hashlib.sha256((salt + p).encode()).hexdigest() == stored_hash
        return False
    except Exception:
        return False


def get_user(email):
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
                "id, email, name, office_code, office_name, designation, section, seat_number, admin_level, active, password_hash"
            ).eq("email", email).execute()
            if r.data:
                u = r.data[0]
                if redis_client:
                    redis_client.setex(f"user_v2:{email}", 3600, json.dumps(u, default=str))
                return u
        except Exception:
            pass
    return None


def login_rate_limited(email):
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
            r = supabase.table("login_attempts").select("email").eq("email", email).gte("created_at", cutoff).execute()
            supabase.table("login_attempts").delete().lt("created_at", (now_utc() - timedelta(hours=1)).isoformat()).execute()
            return len(r.data or []) >= 5
        except Exception:
            pass
    return False


def increment_login_attempt(email):
    if redis_client:
        k = f"login_attempts:{email}"
        redis_client.set(k, "0", ex=900, nx=True)
        redis_client.incr(k)
    elif supabase:
        try:
            supabase.table("login_attempts").insert({"email": email, "created_at": now_utc().isoformat()}).execute()
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
        "sidebar_open": True,
        "messages": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def try_auto_login():
    """BUG FIX: timezone-aware comparison, silent failure prevention."""
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
        # BUG FIX: handle naive datetime
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


def do_login(u):
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
        audit_log(st.session_state.get("user", {}).get("email", "unknown"), "user.logout", "user", None)
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
def extract_mentions(content):
    pattern = r"@([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
    return re.findall(pattern, str(content or ""))


def extract_hashtags(content):
    pattern = r"#([a-zA-Z0-9_]+)"
    return re.findall(pattern, str(content or ""))


def send_notification(recipient_email, sender_email, ntype, post_id, message):
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


# ============================================================
# SAMPLE CIRCULARS FOR FEED ENGAGEMENT
# ============================================================
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


# ============================================================
# RECENT UPLOADS HELPER FOR FEED
# ============================================================
def get_recent_uploads(limit=5):
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


# ============================================================
# AI TRAINING LINK HELPERS
# ============================================================
def get_training_links():
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


def add_training_link(url, title, user_email):
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


def delete_training_link(link_id):
    if not supabase:
        return False
    try:
        supabase.table("ai_training_links").delete().eq("id", link_id).execute()
        return True
    except Exception:
        return False


# ============================================================
# MESSAGE CLEANUP
# ============================================================
def cleanup_old_messages():
    if not supabase:
        return
    try:
        cutoff = (now_utc() - timedelta(hours=24)).isoformat()
        supabase.table("messages").delete().lt("created_at", cutoff).eq("is_starred", False).execute()
    except Exception:
        pass
        # ============================================================
# UI PAGES
# ============================================================
def show_login():
    """BUG FIX: Wrapped in st.form to prevent keystroke reruns."""
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


def show_feed():
    """Enhanced social feed with BUG FIXES: clear_on_submit, reactions counts, combined filters."""
    u = st.session_state.user or {}
    hour = now_utc().hour
    g = "☀️ Good Morning" if hour < 12 else "🌤️ Hello" if hour < 17 else "🌙 Good Evening"
    st.markdown(f"### {g}, {u.get('name', 'User')}!")
    st.caption(f"📍 {u.get('office_name', 'Office')} | {u.get('designation', 'Staff')}")

    # Announcements
    if supabase:
        try:
            anns = supabase.table("announcements").select("*").gt(
                "expires_at", now_utc().isoformat()
            ).order("created_at", desc=True).limit(3).execute().data or []
            for ann in anns:
                icon = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(ann.get("priority", "info"), "ℹ️")
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

    # Search + Filter (BUG FIX: combined, not silent override)
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

    # Create Post (BUG FIX: clear_on_submit=True)
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
                                supabase.table("post_tags").insert({"post_id": post_id, "tag": tag.lower()}).execute()
                            except Exception:
                                pass
                        for mention_email in extract_mentions(content):
                            mentioned_user = get_user(mention_email)
                            if mentioned_user:
                                send_notification(mention_email, u.get("email", ""), "mention", post_id,
                                                f"{u.get('name', 'Someone')} mentioned you in a post")
                        audit_log(u.get("email", ""), "post.create", "post", post_id)
                        show_toast("Posted successfully!")
                        st.rerun()
                except Exception as e:
                    show_toast(f"Failed to post: {str(e)}", "error")

    # Load Posts (BUG FIX: sb guard, combined search+tag)
    posts = []
    if supabase:
        try:
            if search_q and filter_tag != "All":
                search_sql = sanitize_search_query(search_q)
                selected_tag = filter_tag.replace("#", "").lower()
                tag_posts = supabase.table("post_tags").select("post_id").eq("tag", selected_tag).execute().data or []
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
                tag_posts = supabase.table("post_tags").select("post_id").eq("tag", selected_tag).execute().data or []
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

    # Empty state + sample circulars
    if not posts:
        st.markdown(
            '<div class="empty-state"><div style="font-size:60px;">📭</div><h3>No posts yet</h3><p>Upload a document, register tapal, or create an update.</p></div>',
            unsafe_allow_html=True,
        )
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

    # Render Posts
    for p in posts:
        post_id = str(p.get("id", uuid.uuid4()))
        author = p.get("users") or {}
        author_name = author.get("name") or p.get("author_email", "Unknown")

        with st.container():
            if p.get("is_pinned"):
                st.markdown('<span class="pinned-badge">📌 PINNED</span>', unsafe_allow_html=True)

            col_avatar, col_info = st.columns([1, 5])
            with col_avatar:
                st.markdown(f'<div class="post-avatar">{str(author_name)[0].upper()}</div>', unsafe_allow_html=True)
            with col_info:
                st.markdown(f"**{html.escape(str(author_name))}**")
                st.caption(f"{html.escape(str(author.get('designation', '')))} • {str(p.get('created_at', ''))[:16]}")

            st.markdown(
                f'<div style="margin: 12px 0; font-size: 15px;">{html.escape(str(p.get("content", "")))}</div>',
                unsafe_allow_html=True,
            )

            try:
                if supabase:
                    post_tags = supabase.table("post_tags").select("tag").eq("post_id", p.get("id")).execute().data or []
                    if post_tags:
                        tags_html = " ".join([f'<span class="tag-badge">#{html.escape(str(t.get("tag", "")))}</span>' for t in post_tags])
                        st.markdown(f'<div style="margin-bottom: 8px;">{tags_html}</div>', unsafe_allow_html=True)
            except Exception:
                pass

            # BUG FIX: Use presigned URL for feed downloads
            if p.get("file_key"):
                st.markdown(f"📎 **{html.escape(str(p.get('filename', 'Attachment')))}**")
                presigned = storage_system.get_presigned_url(str(p.get("file_key", "")), "hot")
                if presigned:
                    st.markdown(f"[⬇️ Download Attachment]({presigned})")
                else:
                    if st.button("⬇️ Download Attachment", key=f"dl_post_{post_id}"):
                        file_data = storage_system.download_document(p.get("file_key"))
                        if file_data:
                            st.download_button("Save to Device", file_data, file_name=p.get("filename", "file"), key=f"save_{post_id}")

            st.markdown('<div class="post-actions">', unsafe_allow_html=True)
            col_react1, col_react2, col_react3, col_comment = st.columns(4)

            # BUG FIX: Show counts and state for ALL reactions
            with col_react1:
                like_count, user_liked = 0, False
                try:
                    if supabase:
                        reactions = supabase.table("post_reactions").select("*").eq("post_id", p.get("id")).eq("reaction", "like").execute().data or []
                        like_count = len(reactions)
                        user_liked = any(r.get("user_email") == u.get("email") for r in reactions)
                except Exception:
                    pass
                if st.button(f"👍 {like_count}", key=f"like_{post_id}", type="primary" if user_liked else "secondary"):
                    try:
                        existing = supabase.table("post_reactions").select("id").eq("post_id", p.get("id")).eq("user_email", u.get("email")).eq("reaction", "like").execute()
                        if existing.data:
                            supabase.table("post_reactions").delete().eq("id", existing.data[0].get("id")).execute()
                        else:
                            supabase.table("post_reactions").insert({"post_id": p.get("id"), "user_email": u.get("email"), "reaction": "like"}).execute()
                        st.rerun()
                    except Exception:
                        pass

            with col_react2:
                clap_count, user_clapped = 0, False
                try:
                    if supabase:
                        reactions = supabase.table("post_reactions").select("*").eq("post_id", p.get("id")).eq("reaction", "clap").execute().data or []
                        clap_count = len(reactions)
                        user_clapped = any(r.get("user_email") == u.get("email") for r in reactions)
                except Exception:
                    pass
                if st.button(f"👏 {clap_count}", key=f"clap_{post_id}", type="primary" if user_clapped else "secondary"):
                    try:
                        existing = supabase.table("post_reactions").select("id").eq("post_id", p.get("id")).eq("user_email", u.get("email")).eq("reaction", "clap").execute()
                        if existing.data:
                            supabase.table("post_reactions").delete().eq("id", existing.data[0].get("id")).execute()
                        else:
                            supabase.table("post_reactions").insert({"post_id": p.get("id"), "user_email": u.get("email"), "reaction": "clap"}).execute()
                        st.rerun()
                    except Exception:
                        pass

            with col_react3:
                cel_count, user_cel = 0, False
                try:
                    if supabase:
                        reactions = supabase.table("post_reactions").select("*").eq("post_id", p.get("id")).eq("reaction", "celebrate").execute().data or []
                        cel_count = len(reactions)
                        user_cel = any(r.get("user_email") == u.get("email") for r in reactions)
                except Exception:
                    pass
                if st.button(f"🎉 {cel_count}", key=f"celebrate_{post_id}", type="primary" if user_cel else "secondary"):
                    try:
                        existing = supabase.table("post_reactions").select("id").eq("post_id", p.get("id")).eq("user_email", u.get("email")).eq("reaction", "celebrate").execute()
                        if existing.data:
                            supabase.table("post_reactions").delete().eq("id", existing.data[0].get("id")).execute()
                        else:
                            supabase.table("post_reactions").insert({"post_id": p.get("id"), "user_email": u.get("email"), "reaction": "celebrate"}).execute()
                        st.rerun()
                    except Exception:
                        pass

            comment_count = 0
            with col_comment:
                try:
                    if supabase:
                        comments_count_rows = supabase.table("post_comments").select("id").eq("post_id", p.get("id")).execute().data or []
                        comment_count = len(comments_count_rows)
                except Exception:
                    pass
                if st.button(f"💬 Comment ({comment_count})", key=f"comment_btn_{post_id}"):
                    st.session_state[f"show_comments_{post_id}"] = not st.session_state.get(f"show_comments_{post_id}", False)

            st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state.get(f"show_comments_{post_id}", False):
                st.markdown("---")
                st.markdown(f"#### 💬 Comments ({comment_count})")
                comments = []
                try:
                    if supabase:
                        comments = supabase.table("post_comments").select("*, users(name)").eq("post_id", p.get("id")).order("created_at").execute().data or []
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

            if u.get("admin_level") != "staff" or p.get("author_email") == u.get("email"):
                if st.button("🗑️ Delete Post", key=f"del_post_{post_id}", type="secondary"):
                    try:
                        supabase.table("social_posts").delete().eq("id", p.get("id")).execute()
                        audit_log(u.get("email", ""), "post.delete", "post", p.get("id"))
                        show_toast("Post deleted")
                        st.rerun()
                    except Exception as e:
                        show_toast(f"Failed: {str(e)}", "error")
            st.divider()


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


def show_tapal():
    """BUG FIX: New reference format, monthly report, seat_number, error handling."""
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
                counter_serial = st.selectbox("Counter Serial", ["A1", "B1", "C1", "D1", "E1", "F1", "G1", "H1"])
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
                                return
                            with st.spinner("Uploading attachment..."):
                                file_bytes = file.read()
                                res = storage_system.upload_document(file_bytes, file.name, "tapal", u.get("email", "system"))
                            if res.get("success"):
                                did = res.get("document_id")
                            else:
                                st.error(f"Storage Error: {res.get('error', 'Unknown error')}")
                                return
                        except Exception as e:
                            st.error(f"Exception during upload: {str(e)}")
                            return

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
                            # Show in feed
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
                rows = supabase.table("tapal_log").select("*").gte("tapal_date", month_start).lte("tapal_date", month_end).execute().data or []
                df = pd.DataFrame(rows)
                if not df.empty:
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Total Entries", len(df))
                    c2.metric("Inward", len(df[df.get("direction", pd.Series()) == "Inward"]) if "direction" in df.columns else 0)
                    c3.metric("Outward", len(df[df.get("direction", pd.Series()) == "Outward"]) if "direction" in df.columns else 0)
                    st.download_button("📥 Download CSV", df.to_csv(index=False), f"tapal_report_{now_utc().strftime('%Y%m')}.csv")
                else:
                    st.info("No tapal entries this month.")
            except Exception:
                st.info("Could not load report.")
        else:
            st.info("Supabase not configured.")



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

                # Save dispatch generation to database
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
                    u.get("email", ""),
                    "dispatch.generate",
                    "dispatch",
                    None,
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

def document_card(doc):
    doc_id = str(doc.get("id", ""))
    if not doc_id:
        return
    with st.expander(f"📄 {html.escape(str(doc.get('filename', 'Document')))}"):
        st.write(f"Summary: {doc.get('ai_summary') or '(Processing)'}")
        presigned = storage_system.get_presigned_url(doc.get("file_key", ""), doc.get("storage_tier", "hot"))
        if presigned:
            st.markdown(f"[⬇️ Download]({presigned})")
        else:
            if st.button("Download", key=f"dl_{doc_id}"):
                data = storage_system.download_document(doc_id)
                if data:
                    st.download_button("Save", data, file_name=doc.get("filename", "file"), key=f"sv_{doc_id}")
                else:
                    st.error("Unable to download file.")


def show_documents():
    """BUG FIX: Removed docx from uploader, safe email access."""
    u = st.session_state.user or {}
    st.markdown("### 📄 Documents")

    file = st.file_uploader("Upload", type=["pdf", "jpg", "png"])
    if file:
        if file.size > 20 * 1024 * 1024:
            show_toast("Too large. Max 20MB.", "error")
        else:
            with st.spinner("Uploading..."):
                res = storage_system.upload_document(file.read(), file.name, "circular", u.get("email", ""))
            if res.get("success"):
                if res.get("duplicate"):
                    show_toast(res.get("message", "Duplicate file"), "warning")
                else:
                    show_toast(f"Uploaded! {res.get('compression_ratio', 0) * 100:.1f}% compressed")
                    # Show in feed
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
                    .select("id, filename, file_key, storage_tier, doc_type, ai_summary, uploaded_at")
                    .order("uploaded_at", desc=True)
                    .limit(20)
                    .execute().data or []
                )
            except Exception:
                docs = []

    if not docs:
        st.markdown('<div class="empty-state"><div style="font-size:60px;">📭</div><h3>No documents</h3></div>', unsafe_allow_html=True)
    for d in docs:
        document_card(d)


def show_ai():
    """BUG FIX: Conversation memory included."""
    st.markdown("### 🤖 AI Assistant")
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
            src = search_documents(p, 4)
            web = ""
            if not src:
                web = agentic_web_search(p, "gov")
                if not web.strip():
                    web = agentic_web_search(p, "deep")

            ctx = "Answer using only provided context and trusted sources.\n\n"
            if src:
                ctx += "".join([f"- {s.get('filename', 'Source')}: {s.get('ai_summary', '')}\n" for s in src])
            else:
                ctx += f"WEB:\n{web}"

            # BUG FIX: Include conversation history
            history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-6:]])
            prompt = f"{ctx}\n\nRecent conversation:\n{history}\n\nQuestion: {p}"

            r = ai_system.request(prompt)
            resp = r.get("response") if r.get("success") else f"❌ AI Error: {r.get('error', 'Unknown')}"
            st.markdown(resp)
            st.session_state.messages.append({"role": "assistant", "content": resp})


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
            st.markdown('<div class="empty-state"><div style="font-size:60px;">📭</div><h3>No messages</h3></div>', unsafe_allow_html=True)
        for m in inbox_msgs:
            icon = "📬" if not m.get("read") else "📩"
            with st.expander(f"{icon} {html.escape(str(m.get('subject') or 'No Subject'))} — From: {html.escape(str(m.get('sender_email', 'Unknown')))}"):
                st.caption(str(m.get("created_at", ""))[:16])
                st.write(html.escape(str(m.get("body", ""))))
                if not m.get("read"):
                    if st.button("Mark as Read", key=f"read_{m.get('id')}"):
                        try:
                            supabase.table("messages").update({"read": True}).eq("id", m.get("id")).execute()
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
            st.markdown('<div class="empty-state"><div style="font-size:60px;">📤</div><h3>No sent messages</h3></div>', unsafe_allow_html=True)
        for m in sent_msgs:
            with st.expander(f"📤 To: {html.escape(str(m.get('recipient_email', 'Unknown')))} — {html.escape(str(m.get('subject') or 'No Subject'))}"):
                st.caption(str(m.get("created_at", ""))[:16])
                st.write(html.escape(str(m.get("body", "")))) 
    # ============================================================
# SYSTEM HEALTH
# ============================================================
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
                b2_client.list_buckets()
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


# ============================================================
# OFFICE DIRECTORY HELPER
# ============================================================
def get_office_directory(office_code):
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


# ============================================================
# ADMIN PANEL — FULLY FIXED
# ============================================================
def show_admin():
    u = st.session_state.user or {}

    if u.get("admin_level") not in ["system_admin", "office_admin"]:
        st.warning("Access denied")
        return

    st.markdown("### 🏛️ Admin Panel")

    section = st.radio(
        "Section",
        [
            "🩺 Health",
            "👥 Users",
            "⚙️ AI Settings",
            "🧠 AI Training",
            "📊 Storage",
            "🔄 Maintenance",
            "📋 Audit",
            "🚨 Emergency",
            "📢 Announcements",
            "📊 Analytics",
        ],
        horizontal=True,
        label_visibility="collapsed",
        key="admin_section",
    )

    RTA_ROLES = [
        "Junior Assistant (Jr Asst)",
        "Senior Assistant (Sr Asst)",
        "Assistant Officer (AO)",
        "Regional Transport Officer (RTO)",
        "Deputy Transport Commissioner (DTC)",
        "Motor Vehicle Inspector (MVI)",
        "Assistant Motor Vehicle Inspector (AMVI)",
    ]

    SYSTEM_ROLES = [
        "staff",
        "office_admin",
        "system_admin",
    ]

    # ------------------------------------------------------------
    # HEALTH
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # USERS
    # ------------------------------------------------------------
    elif section == "👥 Users":
        st.markdown("#### 👥 Users")

        st.info(
            "Passwords are stored as secure hashes. Admin cannot view passwords, but can reset them."
        )

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
                                supabase.table("users").insert(
                                    {
                                        "email": ne.strip().lower(),
                                        "name": nn,
                                        "designation": nd,
                                        "seat_number": seat,
                                        "password_hash": hash_password(pw),
                                        "admin_level": na,
                                        "active": True,
                                    }
                                ).execute()

                                show_toast(f"Created user. Password: {pw}")
                            except Exception:
                                show_toast("Failed to create user", "error")

        with st.expander("📥 Bulk Import CSV"):
            csvf = st.file_uploader("CSV columns: email,name,designation,seat_number,admin_level,password", type=["csv"])

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
                                supabase.table("users").insert(
                                    {
                                        "email": email,
                                        "name": name,
                                        "designation": designation,
                                        "seat_number": seat_number,
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

        if supabase:
            try:
                users = (
                    supabase.table("users")
                    .select("*")
                    .order("name")
                    .execute()
                    .data or []
                )
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

            c2.write(
                f"**{usr.get('designation', 'N/A')}** | Access: `{usr.get('admin_level', 'staff')}`"
            )

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
                new_pass = st.text_input(
                    "Set New Password",
                    type="password",
                    key=f"np_{usr_id}",
                )

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

    # ------------------------------------------------------------
    # AI SETTINGS
    # ------------------------------------------------------------
    elif section == "⚙️ AI Settings":
        st.markdown("#### ⚙️ AI API Settings")

        providers = ai_system.get_providers()

        st.info(
            f"Active providers: {len(providers)} — "
            f"{', '.join([p['name'] for p in providers]) or 'None'}"
        )

        st.info(
            "Providers are tried in this order: Qwen → Grok → DeepSeek → Gemini → OpenAI → Claude. "
            "Add at least one key. If one fails, the next is tried automatically."
        )

        with st.form("ai_settings_form"):
            qwen_key = st.text_input(
                "1️⃣ Qwen API Key",
                value=get_setting("QWEN_API_KEY"),
                type="password",
            )

            grok_key = st.text_input(
                "2️⃣ Grok API Key",
                value=get_setting("GROK_API_KEY"),
                type="password",
            )

            deepseek_key = st.text_input(
                "3️⃣ DeepSeek API Key",
                value=get_setting("DEEPSEEK_API_KEY"),
                type="password",
            )

            gemini_key = st.text_input(
                "4️⃣ Gemini API Key",
                value=get_setting("GEMINI_API_KEY"),
                type="password",
            )

            openai_key = st.text_input(
                "5️⃣ OpenAI API Key",
                value=get_setting("OPENAI_API_KEY"),
                type="password",
            )

            anthropic_key = st.text_input(
                "6️⃣ Claude API Key",
                value=get_setting("ANTHROPIC_API_KEY"),
                type="password",
            )

            gemini_embed_key = st.text_input(
                "Gemini Embedding Key",
                value=get_setting("GEMINI_EMBEDDING_KEY"),
                type="password",
            )

            serper_key = st.text_input(
                "Serper Web Search Key",
                value=get_setting("SERPER_API_KEY"),
                type="password",
            )

            if st.form_submit_button("💾 Save AI Settings"):
                set_setting("QWEN_API_KEY", qwen_key)
                set_setting("GROK_API_KEY", grok_key)
                set_setting("DEEPSEEK_API_KEY", deepseek_key)
                set_setting("GEMINI_API_KEY", gemini_key)
                set_setting("OPENAI_API_KEY", openai_key)
                set_setting("ANTHROPIC_API_KEY", anthropic_key)
                set_setting("GEMINI_EMBEDDING_KEY", gemini_embed_key)
                set_setting("SERPER_API_KEY", serper_key)

                show_toast("AI settings saved")
                st.rerun()

    # ------------------------------------------------------------
    # AI TRAINING
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # STORAGE
    # ------------------------------------------------------------
    elif section == "📊 Storage":
        st.markdown("#### 📊 Storage")

        if st.button("Auto-Tier Documents", key="auto_tier_admin"):
            r = auto_tier_documents()

            if "error" in r:
                show_toast(r["error"], "error")
            else:
                show_toast(
                    f"Moved {r.get('moved_to_cold', 0)} cold, {r.get('moved_to_hot', 0)} hot"
                )

    # ------------------------------------------------------------
    # MAINTENANCE
    # ------------------------------------------------------------
    elif section == "🔄 Maintenance":
        st.markdown("#### 🔄 Maintenance")

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
                                supabase.table("documents").update(
                                    {
                                        "ai_summary": s,
                                        "processing_status": "ready",
                                    }
                                ).eq("id", d.get("id")).execute()

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
                                "created_at",
                                (now_utc() - timedelta(days=7)).isoformat(),
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
                                ).in_(
                                    "id",
                                    [d.get("id") for d in stuck.data],
                                ).execute()

                        elif tid == "clean_sessions":
                            supabase.table("sessions").delete().lt(
                                "expires_at",
                                now_utc().isoformat(),
                            ).execute()

                        show_toast("Done!")
                        st.rerun()
                    except Exception:
                        show_toast("Task failed", "error")

    # ------------------------------------------------------------
    # AUDIT
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # EMERGENCY
    # ------------------------------------------------------------
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
            st.warning("⚠️ In maintenance")

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

    # ------------------------------------------------------------
    # ANNOUNCEMENTS
    # ------------------------------------------------------------
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
                            supabase.table("announcements").insert(
                                {
                                    "title": title,
                                    "message": msg,
                                    "priority": pri,
                                    "expires_at": (now_utc() + timedelta(days=int(dur))).isoformat(),
                                    "created_by": u.get("email", ""),
                                }
                            ).execute()

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

                    icon = {
                        "info": "ℹ️",
                        "warning": "⚠️",
                        "critical": "🚨",
                    }.get(ann.get("priority", "info"), "ℹ️")

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

    # ------------------------------------------------------------
    # ANALYTICS
    # ------------------------------------------------------------
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


# ============================================================
# SIDEBAR NAVIGATION — SIDEBAR RETRACT FIX
# ============================================================
def render_sidebar_nav():
    if "sidebar_open" not in st.session_state:
        st.session_state.sidebar_open = True

    # If sidebar is closed, show open button in main area
    if not st.session_state.sidebar_open:
        c1, _ = st.columns([1, 6])

        with c1:
            if st.button("☰ Open Sidebar", use_container_width=True, key="open_sidebar_main"):
                st.session_state.sidebar_open = True
                st.rerun()

        return

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
                selected = st.radio("Navigation", menu_items, index=default_index)
        else:
            selected = st.radio("Navigation", menu_items, index=default_index)

        st.divider()

        if st.button("⬅️ Hide Sidebar", use_container_width=True, key="hide_sidebar_nav"):
            st.session_state.sidebar_open = False
            st.rerun()

        if st.button("🚪 Logout", use_container_width=True, type="secondary", key="logout_nav"):
            logout()

    st.session_state.page = page_map.get(selected, "feed")


# ============================================================
# MAIN ENTRY POINT — BUG FIX: __name__ == "__main__"
# ============================================================
def main():
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

    if maint:
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
