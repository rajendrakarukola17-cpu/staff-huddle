"""
RTA ANUBANDHAN — Enterprise Production Final
Core Infrastructure, Cloud Initialization, and Multi-Tier Storage System.
"""

import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
from streamlit_cookies_controller import CookieController
from streamlit_option_menu import option_menu
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
import bcrypt
import logging
import uuid
import threading
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta, timezone, date
import numpy as np
import pandas as pd

# ============================================
# LOGGING CONFIGURATION
# ============================================
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============================================
# OPTIONAL DEPENDENCIES (Graceful Degradation)
# ============================================
try:
    from upstash_redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available - caching disabled")

try:
    import boto3
    BOTO_AVAILABLE = True
except ImportError:
    BOTO_AVAILABLE = False

try:
    import gzip, lzma, zlib
    COMPRESSION_AVAILABLE = True
except ImportError:
    COMPRESSION_AVAILABLE = False

try:
    import zstandard as zstd
    ZSTD_AVAILABLE = True
except ImportError:
    ZSTD_AVAILABLE = False

try:
    import pypdf
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import b2sdk.v2 as b2
    B2_AVAILABLE = True
except ImportError:
    B2_AVAILABLE = False

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

try:
    import cv2
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False

try:
    import sentry_sdk
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

try:
    from thefuzz import process, fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

# ============================================
# SENTRY INITIALIZATION (Fail-safe)
# ============================================
if SENTRY_AVAILABLE and os.getenv("SENTRY_DSN"):
    try:
        sentry_sdk.init(
            dsn=os.getenv("SENTRY_DSN"),
            traces_sample_rate=0.2,
            environment=os.getenv("ENVIRONMENT", "production")
        )
        logger.info("✅ Sentry initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")

# ============================================
# STREAMLIT CONFIGURATION
# ============================================
st.set_page_config(
    page_title="RTA Anubandhan", 
    page_icon="🏛️", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# ============================================
# SECURITY: Anti-Screenshot & Form Autosave JS
# ============================================
components.html("""
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
    inputs.forEach(input => { if (input.id) formData[input.id] = input.value; });
    localStorage.setItem('rta_form_autosave', JSON.stringify(formData));
}, 2000);
window.addEventListener('load', () => {
    const saved = localStorage.getItem('rta_form_autosave');
    if (saved) {
        const formData = JSON.parse(saved);
        Object.entries(formData).forEach(([id, value]) => {
            const input = parentDoc.getElementById(id);
            if (input && input.value === '') input.value = value;
        });
    }
});
</script>
""", height=0, width=0)

# ============================================
# CUSTOM CSS (Enterprise Theme)
# ============================================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root {
    --primary: #0A66C2; --primary-hover: #004182; --primary-light: #E8F0FE;
    --bg-canvas: #F3F2EF; --bg-surface: #FFFFFF;
    --text-primary: #191919; --text-secondary: #666666;
    --border: #E0E0E0; --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
    --shadow-md: 0 8px 24px rgba(0,0,0,0.08);
}
body, .stApp { background-color: var(--bg-canvas) !important; font-family: 'Inter', sans-serif !important; color: var(--text-primary) !important; }
#MainMenu, footer, header { visibility: hidden !important; display: none !important; }
.block-container { padding-top: 1rem !important; padding-bottom: 100px !important; max-width: 1200px; }
.commercial-card { background: var(--bg-surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: var(--shadow-sm); transition: box-shadow 0.2s; }
.commercial-card:hover { box-shadow: var(--shadow-md); }
.post-avatar { width: 48px; height: 48px; border-radius: 50%; background: var(--primary); color: white; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 700; }
.stButton > button { background-color: var(--primary) !important; color: white !important; border: none !important; border-radius: 20px !important; font-weight: 600 !important; width: 100% !important; }
.login-container { max-width: 400px; margin: 50px auto; padding: 30px; background: white; border-radius: 16px; box-shadow: var(--shadow-md); }
.quote-box { background: var(--primary-light); border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center; }
.empty-state { text-align: center; padding: 50px; color: #666; }
.post-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.post-actions { display: flex; gap: 12px; margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--border); flex-wrap: wrap; }
.comment-item { padding: 12px; background: var(--bg-canvas); border-radius: 8px; margin-bottom: 8px; }
.pinned-badge { background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%); color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; display: inline-block; margin-bottom: 8px; }
.announcement-card { background: linear-gradient(135deg, #e8f0fe 0%, #d2e3fc 100%); border: 2px solid var(--primary); border-radius: 12px; padding: 20px; margin-bottom: 16px; }
.tag-badge { background: var(--primary-light); color: var(--primary); padding: 2px 8px; border-radius: 8px; font-size: 12px; margin-right: 4px; }
@media (max-width: 768px) { .block-container { padding: 0.5rem !important; } }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ============================================
# UTILITIES & SECURITY
# ============================================
def secret(key: str, default: str = "") -> str:
    """Fetch secrets from Streamlit secrets.toml or environment variables."""
    try:
        return st.secrets.get(key, default) or os.getenv(key, default)
    except Exception:
        return os.getenv(key, default)

def sanitize_input(text: str) -> str:
    """Strip HTML tags and escape characters to prevent XSS."""
    if not text:
        return ""
    text = re.sub(r'<[^>]*>', '', text)
    return html.escape(text).strip()

def validate_email(email: str) -> bool:
    """Basic email validation regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def now_utc() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)

def sanitize_search_query(q: str) -> str:
    """Remove special characters from search queries."""
    return re.sub(r'[^a-zA-Z0-9\s]', '', q).strip()

def is_safe_url(url: str) -> bool:
    """Basic URL validation."""
    pattern = re.compile(r'^https?://[^\s/$.?#].[^\s]*$', re.IGNORECASE)
    return bool(pattern.match(url))

def generate_file_hash(file_data: bytes) -> str:
    """Generate SHA-256 hash for deduplication."""
    return hashlib.sha256(file_data).hexdigest()

def sanitize_filename(filename: str) -> str:
    """Clean filename for safe storage."""
    filename = os.path.basename(filename)
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    parts = filename.split('.')
    if len(parts) > 2:
        filename = parts[0] + '.' + parts[-1]
    return filename[:200]

def get_fernet():
    """Initialize Fernet encryption."""
    if not CRYPTO_AVAILABLE:
        return None
    key = secret("ENCRYPTION_KEY", "")
    if not key:
        return None
    key_bytes = hashlib.sha256(key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key_bytes))

_fernet = get_fernet()
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"
if IS_PRODUCTION and not _fernet:
    st.error("🚨 System Halted: Encryption key missing in production.")
    st.stop()

def encrypt_data(data: bytes) -> bytes:
    """Encrypt data using Fernet."""
    return _fernet.encrypt(data) if _fernet else data

def decrypt_data(data: bytes) -> bytes:
    """Decrypt data using Fernet."""
    if _fernet:
        try:
            return _fernet.decrypt(data)
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return data
    return data

def show_toast(message: str, type: str = "success"):
    """Show a toast notification."""
    if hasattr(st, 'toast'):
        if type == "success": st.toast(f"✅ {message}")
        elif type == "error": st.toast(f"❌ {message}")
        elif type == "warning": st.toast(f"⚠️ {message}")
    else:
        if type == "success": st.success(message)
        elif type == "error": st.error(message)
        elif type == "warning": st.warning(message)

def log_error(error_type, message):
    """Log critical errors to the audit table."""
    try:
        supabase.table("audit_logs").insert({
            "user_email": st.session_state.get('user', {}).get('email', 'system'),
            "action": "error",
            "resource_type": error_type,
            "metadata": json.dumps({"message": str(message)[:500]}),
            "created_at": now_utc().isoformat()
        }).execute()
    except Exception as e:
        logger.error(f"Failed to log error to DB: {e}")

# ============================================
# CIRCUIT BREAKER & METRICS
# ============================================
class CircuitBreaker:
    """Prevents cascading failures when external APIs are down."""
    def __init__(self, name, failure_threshold=5, recovery_timeout=60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'
    
    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception(f"Circuit breaker {self.name} OPEN")
        try:
            result = func(*args, **kwargs)
            self.failure_count = 0
            self.state = 'CLOSED'
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
            raise

class BusinessMetrics:
    """In-memory metrics tracking for the current session."""
    def __init__(self):
        self.metrics = {
            "documents_uploaded": 0,
            "documents_downloaded": 0,
            "ai_queries_total": 0,
            "ai_queries_cached": 0,
            "active_users": set(),
        }
    
    def increment(self, metric, value=1):
        if metric in self.metrics:
            if isinstance(self.metrics[metric], int):
                self.metrics[metric] += value
            elif isinstance(self.metrics[metric], set):
                self.metrics[metric].add(value)

business_metrics = BusinessMetrics()

# ============================================
# CLOUD INITIALIZATION
# ============================================
@st.cache_resource
def init_supabase():
    try:
        url = secret("SUPABASE_URL")
        key = secret("SUPABASE_KEY")
        if url and key:
            return create_client(url, key, options={
                "postgrest_client_timeout": 30,
                "storage_client_timeout": 30,
                "schema": "public",
                "auto_refresh_token": True,
                "persist_session": True,
                "detect_session_in_url": False,
            })
    except Exception as e:
        logger.error(f"Supabase init failed: {e}")
    return None

@st.cache_resource
def init_redis():
    try:
        if REDIS_AVAILABLE:
            url = secret("UPSTASH_REDIS_REST_URL")
            token = secret("UPSTASH_REDIS_REST_TOKEN")
            if url and token:
                return Redis(url=url, token=token)
    except Exception as e:
        logger.error(f"Redis init failed: {e}")
    return None

@st.cache_resource
def init_r2():
    try:
        if BOTO_AVAILABLE:
            return boto3.client('s3',
                endpoint_url=f"https://{secret('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
                aws_access_key_id=secret("R2_ACCESS_KEY_ID"),
                aws_secret_access_key=secret("R2_SECRET_ACCESS_KEY"),
                region_name='auto')
    except Exception as e:
        logger.error(f"R2 init failed: {e}")
    return None

@st.cache_resource
def init_b2():
    try:
        if B2_AVAILABLE:
            info = b2.InMemoryAccountInfo()
            client = b2.B2Api(info)
            client.authorize_account("production", secret("B2_KEY_ID"), secret("B2_APPLICATION_KEY"))
            return client
    except Exception as e:
        logger.error(f"B2 init failed: {e}")
    return None

@st.cache_resource
def init_qdrant():
    try:
        if QDRANT_AVAILABLE:
            url = secret("QDRANT_URL")
            api_key = secret("QDRANT_API_KEY")
            if url and api_key:
                client = QdrantClient(url=url, api_key=api_key)
                for collection in ["rta_documents", "ai_semantic_cache"]:
                    try:
                        client.get_collection(collection)
                    except Exception:
                        client.create_collection(
                            collection_name=collection,
                            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                        )
                return client
    except Exception as e:
        logger.error(f"Qdrant init failed: {e}")
    return None

@st.cache_resource
def init_minio():
    try:
        if BOTO_AVAILABLE:
            return boto3.client('s3',
                endpoint_url=secret("MINIO_ENDPOINT", "http://localhost:9000"),
                aws_access_key_id=secret("MINIO_ACCESS_KEY"),
                aws_secret_access_key=secret("MINIO_SECRET_KEY"),
                region_name='us-east-1')
    except Exception as e:
        logger.error(f"MinIO init failed: {e}")
    return None

supabase = init_supabase()
redis_client = init_redis()
r2_client = init_r2()
b2_client = init_b2()
qdrant_client = init_qdrant()
minio_client = init_minio()

# ============================================
# COMPRESSION ENGINE
# ============================================
def compress_data(data: bytes) -> Tuple[bytes, str]:
    """Compress data using Zstandard, fallback to LZMA."""
    if ZSTD_AVAILABLE:
        try:
            compressed = zstd.ZstdCompressor(level=19).compress(data)
            if len(compressed) < len(data):
                return compressed, 'zstd'
        except Exception as e:
            logger.warning(f"Zstd compression failed: {e}")
    
    if COMPRESSION_AVAILABLE:
        try:
            compressed = lzma.compress(data, preset=9)
            if len(compressed) < len(data):
                return compressed, 'lzma'
        except Exception as e:
            logger.warning(f"LZMA compression failed: {e}")
            
    return data, 'none'

def decompress_data(data: bytes, method: str) -> bytes:
    """Decompress data based on the method used."""
    if method == 'zstd' and ZSTD_AVAILABLE:
        try:
            return zstd.ZstdDecompressor().decompress(data)
        except Exception as e:
            logger.error(f"Zstd decompression failed: {e}")
    elif method == 'lzma' and COMPRESSION_AVAILABLE:
        try:
            return lzma.decompress(data)
        except Exception as e:
            logger.error(f"LZMA decompression failed: {e}")
    return data

# ============================================
# MULTI-TIER STORAGE SYSTEM
# ============================================
class StorageSystem:
    """Handles encryption, compression, deduplication, and multi-cloud storage."""
    def __init__(self):
        self.r2 = r2_client
        self.b2 = b2_client
        self.minio = minio_client
        self.hot_bucket = secret("R2_BUCKET_NAME", "rta-hot-storage")
        self.cold_bucket = secret("B2_BUCKET_NAME", "rta-cold-storage")
        self.minio_bucket = secret("MINIO_BUCKET", "rta-self-hosted")

    def _upload_to_storage(self, data, key, tier):
        """Upload to R2/B2 by tier, MinIO only as an explicit self-hosted fallback."""
        try:
            if tier == 'hot' and self.r2:
                self.r2.put_object(Bucket=self.hot_bucket, Key=key, Body=data)
                return True
            elif tier == 'cold' and self.b2:
                self.b2.get_bucket_by_name(self.cold_bucket).upload_bytes(data, key)
                return True
            elif self.r2:
                self.r2.put_object(Bucket=self.hot_bucket, Key=key, Body=data)
                return True
            if self.minio:
                try:
                    self.minio.put_object(Bucket=self.minio_bucket, Key=key, Body=data)
                    return True
                except Exception:
                    pass
            return False
        except Exception as e:
            logger.error(f"Storage upload failed: {e}")
            return False

    def _download_from_storage(self, key, tier):
        """Download from R2/B2 by tier, MinIO only as an explicit self-hosted fallback."""
        try:
            if tier == 'hot' and self.r2:
                try:
                    return self.r2.get_object(Bucket=self.hot_bucket, Key=key)['Body'].read()
                except Exception:
                    pass
            elif tier == 'cold' and self.b2:
                try:
                    return self.b2.get_bucket_by_name(self.cold_bucket).download_file_by_name(key).as_bytes()
                except Exception:
                    pass
            if self.minio:
                try:
                    return self.minio.get_object(Bucket=self.minio_bucket, Key=key)['Body'].read()
                except Exception:
                    pass
            return None
        except Exception as e:
            logger.error(f"Storage download failed: {e}")
            return None

    def get_presigned_url(self, key, tier, expiration=3600):
        """Generate secure, time-limited download links."""
        try:
            if tier == 'hot' and self.r2:
                return self.r2.generate_presigned_url('get_object',
                    Params={'Bucket': self.hot_bucket, 'Key': key}, ExpiresIn=expiration)
            elif tier == 'cold' and self.b2:
                bucket = self.b2.get_bucket_by_name(self.cold_bucket)
                token = bucket.get_download_authorization(key, expiration)
                return f"https://f005.backblazeb2.com/file/{self.cold_bucket}/{key}?Authorization={token}"
            return None
        except Exception as e:
            logger.error(f"Presigned URL generation failed: {e}")
            return None

    def upload_document(self, file_data, filename, doc_type, user_email):
        """Master upload function with deduplication and background AI processing."""
        try:
            filename = sanitize_filename(filename)
            file_hash = generate_file_hash(file_data)
            
            # 1. Deduplication Check
            if supabase:
                existing = supabase.table("documents").select("id").eq("file_hash", file_hash).execute()
                if existing.data:
                    ref_id = existing.data[0]['id']
                    supabase.table("document_references").insert({
                        "original_doc_id": ref_id, "referenced_by": user_email,
                        "original_filename": filename, "created_at": now_utc().isoformat()
                    }).execute()
                    audit_log(user_email, "document.duplicate", "document", ref_id)
                    business_metrics.increment("documents_uploaded")
                    return {
                        'success': True, 'duplicate': True, 'document_id': ref_id,
                        'message': f"File exists. Saved {len(file_data)/1024/1024:.2f} MB"
                    }

            # 2. Extract Text & Compress
            extracted_text = self._extract_text(file_data, filename)
            compressed_file, method = compress_data(file_data)
            encrypted_file = encrypt_data(compressed_file)
            
            # 3. Determine Storage Tier
            storage_key = f"blobs/{file_hash[:2]}/{file_hash[2:4]}/{file_hash}"
            tier = 'hot' if doc_type in ['circular', 'tapal', 'current', 'social_post'] else 'cold'

            if not self._upload_to_storage(encrypted_file, storage_key, tier):
                return {'success': False, 'error': 'Storage upload failed'}

            # 4. Store Extracted Text
            text_key = None
            if extracted_text:
                ct, tm = compress_data(extracted_text.encode())
                text_key = f"text/{doc_type}/{now_utc().strftime('%Y/%m/%d')}/{uuid.uuid4().hex}.txt.{tm}"
                if self.r2:
                    self.r2.put_object(Bucket=self.hot_bucket, Key=text_key, Body=ct)

            # 5. Save Metadata to Supabase
            doc_id = None
            if supabase:
                result = supabase.table("documents").insert({
                    "filename": filename, "file_key": storage_key, "text_key": text_key,
                    "file_hash": file_hash, "doc_type": doc_type, "compression_method": method,
                    "original_size": len(file_data), "compressed_size": len(encrypted_file),
                    "storage_tier": tier, "uploaded_by": user_email,
                    "uploaded_at": now_utc().isoformat(), "processing_status": "pending",
                    "access_count": 0, "last_accessed": now_utc().isoformat()
                }).execute()
                if result.data:
                    doc_id = result.data[0]['id']

            audit_log(user_email, "document.upload", "document", doc_id, {"filename": filename})
            business_metrics.increment("documents_uploaded")

            # 6. Fire-and-Forget Background AI Task
            def bg_task(did, text, fn):
                try:
                    summary = ai_system.summarize(text[:3000]) if text and len(text) > 50 else ""
                    if supabase and summary:
                        supabase.table("documents").update({
                            "ai_summary": summary, "processing_status": "ready"
                        }).eq("id", did).execute()
                    if text and qdrant_client and did:
                        qdrant_client.upsert(collection_name="rta_documents", points=[PointStruct(
                            id=did, vector=generate_embedding(text), payload={"doc_id": did, "filename": fn}
                        )])
                except Exception as e:
                    logger.error(f"Background AI task failed: {e}")
                    if supabase:
                        supabase.table("documents").update({"processing_status": "failed"}).eq("id", did).execute()

            if doc_id and extracted_text:
                threading.Thread(target=bg_task, args=(doc_id, extracted_text, filename), daemon=True).start()
            elif doc_id and supabase:
                supabase.table("documents").update({"processing_status": "ready"}).eq("id", doc_id).execute()

            return {
                'success': True, 'document_id': doc_id,
                'compression_ratio': 1 - (len(encrypted_file)/len(file_data))
            }
        except Exception as e:
            log_error("upload_failed", e)
            return {'success': False, 'error': str(e)}

    def _extract_text(self, file_data, filename):
        """Extract text from PDFs and Images."""
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if ext == 'pdf' and PDF_AVAILABLE:
            try:
                reader = pypdf.PdfReader(io.BytesIO(file_data))
                text = "".join([(p.extract_text() or "") + "\n" for p in reader.pages])
                if text.strip():
                    return text
                return self._ocr_pdf(file_data)
            except Exception:
                return self._ocr_pdf(file_data)
        elif ext in ['jpg', 'jpeg', 'png', 'bmp', 'tiff'] and OCR_AVAILABLE:
            return self._ocr_image(file_data)
        return ""

    def _ocr_image(self, data):
        """OCR for image files."""
        try:
            img = Image.open(io.BytesIO(data)).convert('RGB')
            gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            return pytesseract.image_to_string(thresh)
        except Exception as e:
            logger.error(f"Image OCR failed: {e}")
            return ""

    def _ocr_pdf(self, data):
        """OCR for scanned PDFs (limited to 10 pages to prevent OOM)."""
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

    def download_document(self, document_id):
        """Download, decrypt, and decompress a document."""
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
            
            # Track access for auto-tiering
            try:
                count = doc.get("access_count", 0) or 0
                supabase.table("documents").update({
                    "access_count": count + 1, 
                    "last_accessed": now_utc().isoformat()
                }).eq("id", document_id).execute()
            except Exception:
                pass
                
            business_metrics.increment("documents_downloaded")
            return decompress_data(decrypt_data(data), doc.get("compression_method", "none"))
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None

    def get_full_text(self, document_id):
        """Retrieve the extracted text for AI processing."""
        try:
            if not supabase:
                return ""
            result = supabase.table("documents").select("text_key").eq("id", document_id).execute()
            if result.data and result.data[0].get("text_key"):
                key = result.data[0]["text_key"]
                method = 'none'
                if key.endswith('.lzma'): method = 'lzma'
                elif key.endswith('.gz'): method = 'gzip'
                elif key.endswith('.zstd'): method = 'zstd'
                
                if self.r2:
                    raw = self.r2.get_object(Bucket=self.hot_bucket, Key=key)['Body'].read()
                    return decompress_data(raw, method).decode('utf-8')
            return ""
        except Exception as e:
            logger.error(f"Text retrieval failed: {e}")
            return ""

storage_system = StorageSystem()

# ============================================
# AUTO-TIERING ENGINE
# ============================================
def auto_tier_documents():
    """Move old documents to cold storage, and hot documents back to hot storage."""
    if not supabase:
        return {'error': 'Supabase unavailable'}
    try:
        # Move to Cold (Not accessed in 90 days)
        cutoff = (now_utc() - timedelta(days=90)).isoformat()
        cold_candidates = supabase.table("documents").select("id, file_key").eq(
            "storage_tier", "hot"
        ).lt("last_accessed", cutoff).limit(100).execute().data or []
        
        moved_cold = 0
        for d in cold_candidates:
            data = storage_system._download_from_storage(d['file_key'], 'hot')
            if data and storage_system._upload_to_storage(data, d['file_key'], 'cold'):
                try:
                    r2_client.delete_object(Bucket=storage_system.hot_bucket, Key=d['file_key'])
                except Exception:
                    pass
                supabase.table("documents").update({"storage_tier": "cold"}).eq("id", d['id']).execute()
                moved_cold += 1

        # Move to Hot (Accessed > 10 times)
        hot_candidates = supabase.table("documents").select("id, file_key").eq(
            "storage_tier", "cold"
        ).gte("access_count", 10).limit(50).execute().data or []
        
        moved_hot = 0
        for d in hot_candidates:
            data = storage_system._download_from_storage(d['file_key'], 'cold')
            if data and storage_system._upload_to_storage(data, d['file_key'], 'hot'):
                try:
                    b2_client.get_bucket_by_name(storage_system.cold_bucket).delete_file_name(d['file_key'])
                except Exception:
                    pass
                supabase.table("documents").update({
                    "storage_tier": "hot", "access_count": 0
                }).eq("id", d['id']).execute()
                moved_hot += 1

        return {'moved_to_cold': moved_cold, 'moved_to_hot': moved_hot}
    except Exception as e:
        return {'error': str(e)}

# ============================================
# AUDIT LOGGING
# ============================================
def audit_log(email, action, rtype, rid=None, meta=None):
    """Write immutable audit logs for compliance."""
    if not supabase:
        return
    try:
        supabase.table("audit_logs").insert({
            "user_email": email,
            "action": action,
            "resource_type": rtype,
            "resource_id": str(rid) if rid else None,
            "metadata": json.dumps(meta or {}),
            "created_at": now_utc().isoformat()
        }).execute()
    except Exception as e:
        logger.error(f"Audit log failed: {e}")

# ============================================
# MULTI-PROVIDER AI SYSTEM
# ============================================
gemini_breaker = CircuitBreaker("gemini")
openai_breaker = CircuitBreaker("openai")
anthropic_breaker = CircuitBreaker("anthropic")

class MultiAI:
    """Handles AI requests with circuit breakers and semantic caching."""
    def __init__(self):
        self.providers = []
        for n, k in [
            ("Gemini", secret("GEMINI_API_KEY")), 
            ("OpenAI", secret("OPENAI_API_KEY")), 
            ("Anthropic", secret("ANTHROPIC_API_KEY"))
        ]:
            if k:
                self.providers.append({'name': n, 'key': k})

    def _call_gemini(self, p, k):
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={k}",
            json={"contents": [{"parts": [{"text": p}]}]}, timeout=15
        )
        if r.status_code == 200:
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        if r.status_code == 429:
            raise Exception("Rate limited")
        return None

    def _call_openai(self, p, k):
        r = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {k}"},
            json={"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": p}]}, timeout=15)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        if r.status_code == 429:
            raise Exception("Rate limited")
        return None

    def _call_anthropic(self, p, k):
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": k, "anthropic-version": "2023-06-01"},
            json={"model": "claude-3-haiku-20240307", "max_tokens": 500, "messages": [{"role": "user", "content": p}]}, timeout=15)
        if r.status_code == 200:
            return r.json()["content"][0]["text"].strip()
        if r.status_code == 429:
            raise Exception("Rate limited")
        return None

    def request(self, prompt):
        """Execute AI request with exact-match and semantic caching."""
        business_metrics.increment("ai_queries_total")
        h = hashlib.md5(prompt.encode()).hexdigest()
        
        # 1. Exact Match Cache (Redis)
        if redis_client:
            try:
                c = redis_client.get(f"ai_cache:{h}")
                if c:
                    business_metrics.increment("ai_queries_cached")
                    return {'success': True, 'response': json.loads(c), 'provider': 'cache'}
            except Exception:
                pass
                
        # 2. Semantic Cache (Qdrant)
        if qdrant_client:
            try:
                hits = qdrant_client.search(
                    collection_name="ai_semantic_cache",
                    query_vector=generate_embedding(prompt), limit=1, score_threshold=0.90
                )
                if hits:
                    business_metrics.increment("ai_queries_cached")
                    return {'success': True, 'response': hits[0].payload['response'], 'provider': 'semantic_cache'}
            except Exception:
                pass
                
        # 3. Call Providers
        for p in self.providers:
            try:
                if p['name'] == 'Gemini':
                    resp = gemini_breaker.call(self._call_gemini, prompt, p['key'])
                elif p['name'] == 'OpenAI':
                    resp = openai_breaker.call(self._call_openai, prompt, p['key'])
                elif p['name'] == 'Anthropic':
                    resp = anthropic_breaker.call(self._call_anthropic, prompt, p['key'])
                    
                if resp:
                    # Cache the successful response
                    if redis_client:
                        try:
                            redis_client.setex(f"ai_cache:{h}", 86400, json.dumps(resp))
                        except Exception:
                            pass
                    if qdrant_client:
                        try:
                            qdrant_client.upsert(collection_name="ai_semantic_cache", points=[PointStruct(
                                id=uuid.uuid4().hex, vector=generate_embedding(prompt),
                                payload={"query": prompt, "response": resp}
                            )])
                        except Exception:
                            pass
                    return {'success': True, 'response': resp, 'provider': p['name']}
            except Exception:
                continue
                
        return {'success': False, 'error': 'All providers failed'}

    def summarize(self, text):
        r = self.request(f"Summarize: {text[:3000]}")
        return r.get('response') if r['success'] else None

ai_system = MultiAI()

# ============================================
# AGENTIC WEB SEARCH
# ============================================
def agentic_web_search(query, stype="gov"):
    """Search the web using Serper API."""
    key = secret("SERPER_API_KEY")
    if not key:
        return ""
    if stype == "gov":
        query = f"{query} site:ap.gov.in OR site:gov.in"
    try:
        r = requests.post("https://google.serper.dev/search",
            headers={'X-API-KEY': key, 'Content-Type': 'application/json'},
            json={"q": query, "num": 3}, timeout=10)
        return "".join([
            f"Source: {x.get('link')}\nSnippet: {x.get('snippet')}\n\n" 
            for x in r.json().get("organic", [])
        ])
    except Exception:
        return ""

# ============================================
# VECTOR EMBEDDINGS & SEARCH
# ============================================
def generate_embedding(text):
    """Generate 384-dimensional vector for Qdrant."""
    dim = 384
    key = secret("GEMINI_EMBEDDING_KEY") or secret("GEMINI_API_KEY")
    if key:
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key={key}",
                json={"content": {"parts": [{"text": text[:1500]}]}}, timeout=10
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
    # 1. Fuzzy Search
    if FUZZY_AVAILABLE and supabase:
        try:
            docs = supabase.table("documents").select(
                "id, filename, file_key, storage_tier, doc_type, ai_summary, uploaded_at"
            ).limit(200).execute().data or []
            if docs:
                matches = process.extract(
                    query, [d['filename'] for d in docs], 
                    scorer=fuzz.token_sort_ratio, limit=limit
                )
                ids = [docs[m[2]]['id'] for m in matches if m[1] >= 60]
                return [d for d in docs if d['id'] in ids]
        except Exception:
            pass
            
    # 2. Vector Search
    if qdrant_client:
        try:
            hits = qdrant_client.search(
                collection_name="rta_documents", 
                query_vector=generate_embedding(query), limit=limit
            )
            ids = [h.payload.get("doc_id") for h in hits if h.payload]
            if ids:
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

# ============================================
# AUTHENTICATION & SESSION
# ============================================
def hash_password(p):
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt(rounds=10)).decode()

def check_password(p, h):
    try:
        return bcrypt.checkpw(p.encode(), h.encode())
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
    """Check-only: report whether this email is currently rate limited, without counting this check as an attempt."""
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
            r = supabase.table("login_attempts").select("count").eq("email", email).gte("created_at", cutoff).execute()
            supabase.table("login_attempts").delete().lt("created_at", (now_utc() - timedelta(hours=1)).isoformat()).execute()
            return r.count >= 5 if hasattr(r, 'count') else False
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

cookies = CookieController()
COOKIE_NAME = "rta_session"
SESSION_DAYS = 7

def init_session_state():
    defaults = {"user": None, "logged_in": False, "page": "feed", "admin_level": "staff"}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def try_auto_login():
    if st.session_state.logged_in:
        return
    try:
        token = cookies.get(COOKIE_NAME)
    except Exception:
        token = None
    if not token:
        return
    h = hashlib.sha256(token.encode()).hexdigest()
    if supabase:
        try:
            r = supabase.table("sessions").select("*").eq("token_hash", h).execute()
            if r.data:
                s = r.data[0]
                if datetime.fromisoformat(s["expires_at"].replace("Z", "+00:00")) > now_utc():
                    u = get_user(s["email"])
                    if u and u.get("active", True):
                        st.session_state.logged_in = True
                        st.session_state.user = u
                        st.session_state.admin_level = u.get("admin_level", "staff")
                    elif u and not u.get("active", True):
                        # Deactivated account: drop the stale session instead of logging in
                        try:
                            supabase.table("sessions").delete().eq("token_hash", h).execute()
                        except Exception:
                            pass
                        cookies.delete(COOKIE_NAME)
        except Exception:
            pass

def do_login(u):
    st.session_state.logged_in = True
    st.session_state.user = u
    st.session_state.admin_level = u.get("admin_level", "staff")
    token = secrets.token_urlsafe(32)
    h = hashlib.sha256(token.encode()).hexdigest()
    if supabase:
        try:
            supabase.table("sessions").insert({
                "token_hash": h, "email": u["email"],
                "expires_at": (now_utc() + timedelta(days=SESSION_DAYS)).isoformat()
            }).execute()
            cookies.set(COOKIE_NAME, token, max_age=SESSION_DAYS * 24 * 3600)
        except Exception:
            pass
    audit_log(u["email"], "user.login", "user", None)
    business_metrics.increment("active_users", u["email"])
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
    audit_log(st.session_state.user.get("email", "unknown"), "user.logout", "user", None)
    st.session_state.clear()
    cookies.delete(COOKIE_NAME)
    st.rerun()

# ============================================
# SOCIAL FEED HELPERS
# ============================================
def extract_mentions(content):
    """Find @email mentions in text."""
    pattern = r'@([a-zA-Z0-9._]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    return re.findall(pattern, content)

def extract_hashtags(content):
    """Find #hashtags in text."""
    pattern = r'#([a-zA-Z0-9_]+)'
    return re.findall(pattern, content)

def send_notification(recipient_email, sender_email, ntype, post_id, message):
    """Send an in-app notification to a user."""
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
            "created_at": now_utc().isoformat()
        }).execute()
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")

# ============================================
# UI PAGES
# ============================================
def show_login():
    """Render the login page with rotating quotes."""
    quotes = [
        {"text": "Service to the public is service to the nation", "author": "Mahatma Gandhi"},
        {"text": "Together we move Andhra forward", "author": "RTA Mission"},
        {"text": "Every file processed is a citizen served", "author": "RTA Vision"}
    ]
    q = quotes[int(time.time()) % len(quotes)]
    
    st.markdown(f"""
    <div class="login-container">
        <div style="text-align:center;">
            <div style="font-size:50px;">🏛️</div>
            <h1 style="color:var(--primary);">RTA Anubandhan</h1>
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
                if u and check_password(password, u.get("password_hash", "")):
                    do_login(u)
                else:
                    increment_login_attempt(email)
                    show_toast("Invalid credentials", "error")

def show_feed():
    """Enhanced social feed with reactions, comments, mentions, and search."""
    u = st.session_state.user
    hour = now_utc().hour
    g = "☀️ Good Morning" if hour < 12 else " Hello" if hour < 17 else " Good Evening"
    
    st.markdown(f"### {g}, {u.get('name', 'User')}!")
    st.caption(f"📍 {u.get('office_name', 'Office')} | {u.get('designation', 'Staff')}")
    
    # 1. Show Announcements
    if supabase:
        try:
            anns = supabase.table("announcements").select("*").gt(
                "expires_at", now_utc().isoformat()
            ).order("created_at", desc=True).limit(3).execute().data or []
            
            for ann in anns:
                color = {"info": "#e8f0fe", "warning": "#fff4e5", "critical": "#fee2e2"}.get(ann.get('priority', 'info'), "#e8f0fe")
                icon = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(ann.get('priority', 'info'), "ℹ️")
                st.markdown(f"""
                <div class="announcement-card">
                    <div style="font-size:20px;">{icon}</div>
                    <h3>{ann['title']}</h3>
                    <p>{ann['message']}</p>
                    <small>Expires: {ann['expires_at'][:10]}</small>
                </div>
                """, unsafe_allow_html=True)
        except Exception:
            pass
    
    # 2. Search and Filter Bar
    col1, col2 = st.columns([3, 1])
    with col1:
        search_q = st.text_input("🔍 Search posts", placeholder="Search by keyword, @mention, or #tag", key="feed_search")
    with col2:
        try:
            if supabase:
                tags = supabase.table("post_tags").select("tag").execute().data or []
                tag_counts = {}
                for t in tags:
                    tag_counts[t['tag']] = tag_counts.get(t['tag'], 0) + 1
                top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:5]
                filter_tag = st.selectbox("Filter by Tag", ["All"] + [f"#{t[0]}" for t in top_tags], key="tag_filter")
            else:
                filter_tag = "All"
        except Exception:
            filter_tag = "All"
    
    # 3. Create Post Form
    with st.form("post_form", clear_on_submit=False):
        content = st.text_area("What's on your mind?", placeholder="Use @email to mention, #tag to categorize", height=100, key="post_content")
        post_type = st.selectbox("Post Type", ["📝 Update", "📢 Announcement", "❓ Question", "🎉 Celebration", "📅 Event"], key="post_type")
        
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            file_upload = st.file_uploader("📎 Attachment", type=['jpg', 'png', 'pdf'], key="post_file")
        with col_a2:
            is_pinned = st.checkbox("📌 Pin Post", key="post_pin") if u.get('admin_level') != 'staff' else False
            
        submitted = st.form_submit_button("📤 Post")
        
        if submitted and content.strip():
            content_clean = sanitize_input(content)
            post_id = None
            try:
                result = supabase.table("social_posts").insert({
                    "author_email": u["email"],
                    "content": content_clean,
                    "post_type": post_type.split()[-1].lower(),
                    "is_pinned": is_pinned,
                    "pinned_by": u["email"] if is_pinned else None,
                    "created_at": now_utc().isoformat()
                }).execute()
                
                if result.data:
                    post_id = result.data[0]['id']
                    
                    # Handle file attachment
                    if file_upload:
                        file_result = storage_system.upload_document(file_upload.read(), file_upload.name, "social_post", u["email"])
                        if file_result.get('success'):
                            supabase.table("social_posts").update({
                                "file_key": file_result.get('document_id'),
                                "filename": file_upload.name
                            }).eq("id", post_id).execute()
                    
                    # Extract and store hashtags
                    hashtags = extract_hashtags(content)
                    for tag in hashtags:
                        supabase.table("post_tags").insert({"post_id": post_id, "tag": tag.lower()}).execute()
                    
                    # Handle @mentions and send notifications
                    mentions = extract_mentions(content)
                    for mention_email in mentions:
                        mentioned_user = get_user(mention_email)
                        if mentioned_user:
                            send_notification(mention_email, u["email"], "mention", post_id, f"{u['name']} mentioned you in a post")
                    
                    audit_log(u["email"], "post.create", "post", post_id)
                    show_toast("Posted successfully!")
                    st.rerun()
            except Exception as e:
                show_toast(f"Failed to post: {str(e)}", "error")
    
    # 4. Load Posts
    try:
        if search_q:
            posts = supabase.table("social_posts").select("*, users(name, designation)").or_(
                f"content.ilike.%{search_q}%,author_email.ilike.%{search_q}%"
            ).order("is_pinned", desc=True).order("created_at", desc=True).limit(50).execute().data or []
        elif filter_tag != "All":
            tag_posts = supabase.table("post_tags").select("post_id").eq("tag", filter_tag.lower()).execute().data or []
            if tag_posts:
                post_ids = [p['post_id'] for p in tag_posts]
                posts = supabase.table("social_posts").select("*, users(name, designation)").in_("id", post_ids).order("is_pinned", desc=True).order("created_at", desc=True).execute().data or []
            else:
                posts = []
        else:
            posts = supabase.table("social_posts").select("*, users(name, designation)").order("is_pinned", desc=True).order("created_at", desc=True).limit(50).execute().data or []
    except Exception as e:
        show_toast(f"Failed to load posts: {str(e)}", "error")
        posts = []
    
    if not posts:
        st.markdown('<div class="empty-state"><div style="font-size:60px;">📭</div><h3>No posts yet</h3><p>Be the first to share an update!</p></div>', unsafe_allow_html=True)
    
    # 5. Render Posts
    for p in posts:
        with st.container():
            if p.get('is_pinned'):
                st.markdown('<span class="pinned-badge">📌 PINNED</span>', unsafe_allow_html=True)
            
            col_avatar, col_info = st.columns([1, 5])
            with col_avatar:
                author_name = (p.get("users") or {}).get("name") or "?"
                st.markdown(f'<div class="post-avatar">{author_name[0].upper()}</div>', unsafe_allow_html=True)
            with col_info:
                st.markdown(f'**{p.get("users",{}).get("name","Unknown")}**')
                st.caption(f'{p.get("users",{}).get("designation","")} • {p["created_at"][:16]}')
                if p.get('post_type'):
                    st.caption(f'Type: {p.get("post_type")}')
            
            st.markdown(f'<div style="margin: 12px 0; font-size: 15px;">{p["content"]}</div>', unsafe_allow_html=True)
            
            # Show hashtags
            try:
                if supabase:
                    post_tags = supabase.table("post_tags").select("tag").eq("post_id", p["id"]).execute().data or []
                    if post_tags:
                        tags_html = " ".join([f'<span class="tag-badge">#{t["tag"]}</span>' for t in post_tags])
                        st.markdown(f'<div style="margin-bottom: 8px;">{tags_html}</div>', unsafe_allow_html=True)
            except Exception:
                pass
            
            # Show attachment
            if p.get('file_key'):
                st.markdown(f'📎 **{p.get("filename", "Attachment")}**')
                if st.button("⬇️ Download Attachment", key=f"dl_post_{p['id']}"):
                    file_data = storage_system.download_document(p['file_key'])
                    if file_data:
                        st.download_button("Save to Device", file_data, file_name=p.get('filename', 'file'), key=f"save_{p['id']}")
            
            # Post actions (reactions, comments)
            st.markdown('<div class="post-actions">', unsafe_allow_html=True)
            col_react1, col_react2, col_react3, col_comment = st.columns(4)
            
            with col_react1:
                like_count = 0
                user_liked = False
                try:
                    if supabase:
                        reactions = supabase.table("post_reactions").select("*").eq("post_id", p["id"]).eq("reaction", "like").execute().data or []
                        like_count = len(reactions)
                        user_liked = any(r['user_email'] == u["email"] for r in reactions)
                except Exception:
                    pass
                
                if st.button(f"👍 {like_count}", key=f"like_{p['id']}", type="primary" if user_liked else "secondary"):
                    try:
                        existing = supabase.table("post_reactions").select("id").eq("post_id", p["id"]).eq("user_email", u["email"]).eq("reaction", "like").execute()
                        if existing.data:
                            supabase.table("post_reactions").delete().eq("id", existing.data[0]['id']).execute()
                        else:
                            supabase.table("post_reactions").insert({"post_id": p["id"], "user_email": u["email"], "reaction": "like"}).execute()
                            if p['author_email'] != u["email"]:
                                send_notification(p['author_email'], u["email"], "reaction", p["id"], f"{u['name']} liked your post")
                        st.rerun()
                    except Exception as e:
                        show_toast(f"Failed: {str(e)}", "error")
            
            with col_react2:
                if st.button("👏 Appreciate", key=f"clap_{p['id']}"):
                    try:
                        existing = supabase.table("post_reactions").select("id").eq("post_id", p["id"]).eq("user_email", u["email"]).eq("reaction", "clap").execute()
                        if existing.data:
                            supabase.table("post_reactions").delete().eq("id", existing.data[0]['id']).execute()
                        else:
                            supabase.table("post_reactions").insert({"post_id": p["id"], "user_email": u["email"], "reaction": "clap"}).execute()
                        st.rerun()
                    except Exception:
                        pass
            
            with col_react3:
                if st.button("🎉 Celebrate", key=f"celebrate_{p['id']}"):
                    try:
                        existing = supabase.table("post_reactions").select("id").eq("post_id", p["id"]).eq("user_email", u["email"]).eq("reaction", "celebrate").execute()
                        if existing.data:
                            supabase.table("post_reactions").delete().eq("id", existing.data[0]['id']).execute()
                        else:
                            supabase.table("post_reactions").insert({"post_id": p["id"], "user_email": u["email"], "reaction": "celebrate"}).execute()
                        st.rerun()
                    except Exception:
                        pass
            
            with col_comment:
                comment_count = 0
                try:
                    if supabase:
                        comment_count = supabase.table("post_comments").select("count", count="exact").eq("post_id", p["id"]).execute().count or 0
                except Exception:
                    pass
                if st.button(f"💬 Comment ({comment_count})", key=f"comment_btn_{p['id']}"):
                    st.session_state[f"show_comments_{p['id']}"] = not st.session_state.get(f"show_comments_{p['id']}", False)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Comments Section
            if st.session_state.get(f"show_comments_{p['id']}", False):
                st.markdown("---")
                st.markdown(f"#### 💬 Comments ({comment_count})")
                try:
                    if supabase:
                        comments = supabase.table("post_comments").select("*, users(name)").eq("post_id", p["id"]).is_("parent_comment_id", "null").order("created_at").execute().data or []
                        for c in comments:
                            with st.container():
                                st.markdown(f'<div class="comment-item"><div class="comment-author">{c.get("users",{}).get("name","Unknown")}</div><div class="comment-text">{c["content"]}</div><div class="comment-time">{c["created_at"][:16]}</div></div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Failed to load comments: {str(e)}")
                
                new_comment = st.text_area("Add a comment", key=f"new_comment_{p['id']}", height=60, placeholder="Write your comment...")
                if st.button("Post Comment", key=f"post_comment_{p['id']}"):
                    if new_comment.strip() and supabase:
                        try:
                            supabase.table("post_comments").insert({
                                "post_id": p["id"],
                                "author_email": u["email"],
                                "content": sanitize_input(new_comment),
                                "created_at": now_utc().isoformat()
                            }).execute()
                            if p['author_email'] != u["email"]:
                                send_notification(p['author_email'], u["email"], "reply", p["id"], f"{u['name']} commented on your post")
                            show_toast("Comment posted!")
                            st.rerun()
                        except Exception as e:
                            show_toast(f"Failed: {str(e)}", "error")
            
            # Delete button
            if u['admin_level'] != 'staff' or p['author_email'] == u["email"]:
                if st.button("🗑️ Delete Post", key=f"del_post_{p['id']}", type="secondary"):
                    try:
                        supabase.table("social_posts").delete().eq("id", p["id"]).execute()
                        audit_log(u["email"], "post.delete", "post", p["id"])
                        show_toast("Post deleted")
                        st.rerun()
                    except Exception as e:
                        show_toast(f"Failed: {str(e)}", "error")
            
            st.divider()

def show_workspace():
    """Quick access workspace dashboard."""
    st.markdown("### 🧰 Workspace")
    c = st.columns(4)
    with c[0]:
        if st.button("📥 Tapal"): st.session_state.page="tapal"; st.rerun()
    with c[1]:
        if st.button("📮 Dispatch"): st.session_state.page="dispatch"; st.rerun()
    with c[2]:
        if st.button("📄 Docs"): st.session_state.page="documents"; st.rerun()
    with c[3]:
        if st.button("🤖 AI"): st.session_state.page="ai"; st.rerun()

def show_tapal():
    """Smart Tapal registration form."""
    u = st.session_state.user
    st.markdown("### 📥 Smart Tapal")
    with st.form("tapal_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            direction = st.selectbox("Direction", ["Inward", "Outward"])
            d = st.date_input("Date")
        with c2:
            seq = st.text_input("Seq No.")
            ft = st.text_input("From/To")
        with c3:
            subj = st.text_input("Subject")
            pri = st.selectbox("Priority", ["Normal", "Urgent", "Immediate"])
        
        rno = f"R.No/{u.get('section','A')}/{u.get('designation','JA')}/{now_utc().year}/{seq}" if seq else ""
        if rno:
            st.info(f"📋 Reference: {rno}")
            
        remarks = st.text_area("Remarks", height=80)
        file = st.file_uploader("Attachment", type=['pdf', 'jpg', 'png'])
        
        if st.form_submit_button("💾 Save"):
            if seq and subj:
                did = None
                if file:
                    if file.size > 20*1024*1024:
                        show_toast("File too large. Max 20MB.", "error")
                    else:
                        with st.spinner("Uploading..."):
                            res = storage_system.upload_document(file.read(), file.name, "tapal", u["email"])
                        if res.get('success'):
                            did = res.get('document_id')
                        else:
                            show_toast(res.get('error', 'Failed'), "error")
                            return
                
                if supabase:
                    try:
                        supabase.table("tapal_log").insert({
                            "r_no": rno, "direction": direction, "tapal_date": d.isoformat(),
                            "section": u.get("section"), "designation": u.get("designation"),
                            "from_to": ft, "subject": subj, "priority": pri, "remarks": remarks,
                            "document_id": did, "created_by": u["email"], "created_at": now_utc().isoformat()
                        }).execute()
                        show_toast("Saved successfully!")
                        st.rerun()
                    except Exception:
                        show_toast("Failed to save", "error")

def show_dispatch():
    """Dispatch label generator."""
    u = st.session_state.user
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
            safe_to, safe_frm, safe_subj = html.escape(to), html.escape(frm), html.escape(subj)
            dno = f"Dispatch/{u.get('section','A')}/{u.get('designation','JA')}/{now_utc().year}/{seq}"
            st.session_state.dispatch_ready = True
            st.session_state.dispatch_html = f"""
            <div style="border:2px solid #000;padding:20px;">
                <b>Dispatch No:</b> {dno}<br>
                <b>From:</b> {safe_frm}<br>
                <b>To:</b><br>{safe_to}<br>
                <b>Subject:</b> {safe_subj}
            </div>
            """
            show_toast("Generated!")
            
    if st.session_state.get("dispatch_ready"):
        st.markdown(st.session_state.dispatch_html, unsafe_allow_html=True)

def document_card(doc):
    """Render a single document card."""
    with st.expander(f"📄 {doc['filename']}"):
        st.write(f"Summary: {doc.get('ai_summary', '(Processing)')}")
        if st.button("Download", key=f"dl_{doc['id']}"):
            presigned = storage_system.get_presigned_url(doc['file_key'], doc.get('storage_tier', 'hot'))
            if presigned:
                st.markdown(f"[Download]({presigned})")
            else:
                data = storage_system.download_document(doc['id'])
                if data:
                    st.download_button("Save", data, file_name=doc['filename'], key=f"sv_{doc['id']}")

def show_documents():
    """Document repository with search and upload."""
    u = st.session_state.user
    st.markdown("### 📄 Documents")
    file = st.file_uploader("Upload", type=['pdf', 'jpg', 'png', 'doc'])
    if file:
        if file.size > 20*1024*1024:
            show_toast("Too large", "error")
        else:
            with st.spinner("Uploading..."):
                res = storage_system.upload_document(file.read(), file.name, "circular", u["email"])
            if res.get('success'):
                if res.get('duplicate'):
                    show_toast(res.get('message', 'Duplicate'), "warning")
                else:
                    show_toast(f"Uploaded! {res.get('compression_ratio',0)*100:.1f}% compressed")
            else:
                show_toast(res.get('error', 'Failed'), "error")
                
    q = st.text_input("Search")
    if q:
        docs = search_documents(q)
    else:
        try:
            docs = supabase.table("documents").select("id, filename, file_key, storage_tier, doc_type, ai_summary, uploaded_at").order("uploaded_at", desc=True).limit(20).execute().data or []
        except Exception:
            docs = []
            
    if not docs:
        st.markdown('<div class="empty-state"><div style="font-size:60px;">📭</div><h3>No documents</h3></div>', unsafe_allow_html=True)
        
    for d in docs:
        document_card(d)

def show_ai():
    """AI Assistant chat interface with RAG."""
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
                    
            ctx = "Answer using only context.\n\n"
            ctx += "".join([f"- {s.get('filename')}: {s.get('ai_summary')}\n" for s in src]) if src else f"WEB:\n{web}"
            
            r = ai_system.request(ctx + f"\nQuestion: {p}")
            resp = r.get('response') if r.get('success') else "AI unavailable"
            
            st.markdown(resp)
            st.session_state.messages.append({"role": "assistant", "content": resp})

# ============================================
# ADMIN & SYSTEM HEALTH
# ============================================
def show_system_health():
    """Check connectivity to all external services."""
    st.markdown("### 🩺 System Health Check")
    cols = st.columns(3)
    with cols[0]:
        try:
            supabase.table("users").select("id").limit(1).execute()
            st.success("✅ Supabase: Connected")
        except Exception:
            st.error("❌ Supabase: Down")
    with cols[1]:
        storage_status = []
        if r2_client:
            try: r2_client.list_buckets(); storage_status.append("✅ R2")
            except: storage_status.append("❌ R2")
        if b2_client:
            try: b2_client.list_buckets(); storage_status.append("✅ B2")
            except: storage_status.append("❌ B2")
        if minio_client:
            try: minio_client.list_buckets(); storage_status.append("✅ MinIO")
            except: storage_status.append("❌ MinIO")
        st.info("Storage: " + (" | ".join(storage_status) or "❌ None"))
    with cols[2]:
        try:
            if qdrant_client:
                qdrant_client.get_collections()
                st.success("✅ Qdrant: Connected")
            else:
                st.warning("⚠️ Qdrant: Disabled")
        except Exception:
            st.error("❌ Qdrant: Down")

def get_office_directory(office_code):
    """Fetch staff directory via D1 Worker or Supabase fallback."""
    worker_url = secret("CF_WORKER_URL", "")
    if worker_url:
        try:
            resp = requests.get(f"{worker_url}/directory", params={"office": office_code}, timeout=2)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
    try:
        return supabase.table("users").select("name, designation, section, seat_number").eq("office_code", office_code).execute().data or []
    except Exception:
        return []

def show_admin():
    """Comprehensive Admin Panel with 8 sections."""
    u = st.session_state.user
    if u.get("admin_level") not in ["system_admin", "office_admin"]:
        st.warning("Access denied")
        return
        
    st.markdown("### 🏛️ Admin Panel")
    section = st.radio(
        "Section",
        ["🩺 Health", "👥 Users", "📊 Storage", "🔄 Maintenance", "📋 Audit", "🚨 Emergency", "📢 Announcements", "📊 Analytics"],
        horizontal=True, label_visibility="collapsed", key="admin_section"
    )

    if section == "🩺 Health":
        st.markdown("#### 🩺 Health")
        if st.button("Check Health", key="hcheck"):
            show_system_health()
        st.divider()
        st.markdown("#### 📜 Recent Errors")
        if supabase:
            try:
                errs = supabase.table("audit_logs").select("*").eq("action", "error").gte("created_at", (now_utc()-timedelta(hours=24)).isoformat()).order("created_at", desc=True).limit(20).execute().data or []
                if not errs:
                    st.success("No errors in 24h!")
                for e in errs:
                    st.error(f"{e.get('resource_type','Unknown')} at {str(e.get('created_at',''))[:16]}")
                    st.caption(str(e.get('metadata',''))[:200])
            except Exception:
                pass
                
    elif section == "👥 Users":
        st.markdown("#### 👥 Users")
        with st.expander("➕ Add User"):
            with st.form("adduser"):
                ne = st.text_input("Email")
                nn = st.text_input("Name")
                na = st.selectbox("Role", ["staff", "office_admin", "system_admin"])
                if st.form_submit_button("Create"):
                    if ne and nn:
                        tp = secrets.token_urlsafe(8)
                        try:
                            supabase.table("users").insert({"email": ne.strip().lower(), "name": nn, "password_hash": hash_password(tp), "admin_level": na, "active": True}).execute()
                            show_toast(f"Created! Password: {tp}")
                        except Exception:
                            show_toast("Failed", "error")
                            
        with st.expander("📥 Bulk Import CSV"):
            csvf = st.file_uploader("CSV", type=['csv'])
            if csvf and st.button("Import", key="bimp"):
                try:
                    df = pd.read_csv(csvf)
                    created = []
                    for _, row in df.iterrows():
                        tp = secrets.token_urlsafe(8)
                        try:
                            supabase.table("users").insert({"email": row['email'].strip().lower(), "password_hash": hash_password(tp), "name": row['name'], "admin_level": row.get('admin_level', 'staff'), "active": True}).execute()
                            created.append((row['email'], tp))
                        except Exception:
                            pass
                    if created:
                        st.download_button("Download Passwords", pd.DataFrame(created, columns=['Email', 'Password']).to_csv(index=False), "passwords.csv")
                        show_toast(f"Created {len(created)} users")
                except Exception as e:
                    show_toast(f"Import failed: {e}", "error")
                    
        if supabase:
           r = supabase.table("users").select("id, email, name, office_code, office_name, designation, section, seat_number, admin_level, active, password_hash").eq("email", email).execute(), name, active, admin_level").execute().data or []:
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"{'🟢' if usr.get('active', True) else '🔴'} **{usr['name']}** ({usr['email']})")
                if c2.button("🔑", key=f"rst_{usr['id']}"):
                    tp = secrets.token_urlsafe(8)
                    supabase.table("users").update({"password_hash": hash_password(tp)}).eq("id", usr['id']).execute()
                    show_toast(f"New: {tp}")
                confirm_key = f"confirm_deactivate_{usr['id']}"
                if not st.session_state.get(confirm_key):
                    if c3.button("Toggle", key=f"tg_{usr['id']}"):
                        st.session_state[confirm_key] = True
                        st.rerun()
                else:
                    if c3.button("✅ Confirm", key=f"tgc_{usr['id']}"):
                        supabase.table("users").update({"active": not usr.get('active', True)}).eq("id", usr['id']).execute()
                        if redis_client:
                            try:
                                redis_client.delete(f"user:{usr['email']}")
                            except Exception:
                                pass
                        st.session_state[confirm_key] = False
                        st.rerun()
                    if c3.button("Cancel", key=f"tgx_{usr['id']}"):
                        st.session_state[confirm_key] = False
                        st.rerun()

    elif section == "📊 Storage":
        st.markdown("#### 📊 Storage")
        if st.button("Auto-Tier", key="atier"):
            r = auto_tier_documents()
            if 'error' in r:
                show_toast(r['error'], "error")
            else:
                show_toast(f"Moved {r.get('moved_to_cold', 0)} cold, {r.get('moved_to_hot', 0)} hot")

    elif section == "🔄 Maintenance":
        st.markdown("#### 🔄 Maintenance")
        if st.button("Reprocess Failed", key="reproc"):
            failed = supabase.table("documents").select("id").eq("processing_status", "failed").limit(10).execute().data or []
            for d in failed:
                text = storage_system.get_full_text(d['id'])
                if text:
                    s = ai_system.summarize(text[:3000])
                    if s:
                        supabase.table("documents").update({"ai_summary": s, "processing_status": "ready"}).eq("id", d['id']).execute()
            show_toast(f"Reprocessed {len(failed)}")
            
        st.divider()
        st.markdown("##### ⏰ Scheduled Tasks")
        for tid, tname, freq in [("cleanup_login", "Clean login attempts", "Daily"), ("auto_tier", "Auto-tier", "Weekly"), ("reset_stuck", "Reset stuck", "Hourly"), ("clean_sessions", "Clean sessions", "Daily")]:
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{tname}** ({freq})")
            if c2.button("Run", key=f"t_{tid}"):
                with st.spinner("Running..."):
                    if tid == "cleanup_login":
                        supabase.table("login_attempts").delete().lt("created_at", (now_utc()-timedelta(days=7)).isoformat()).execute()
                    elif tid == "auto_tier":
                        auto_tier_documents()
                    elif tid == "reset_stuck":
                        stuck = supabase.table("documents").select("id").eq("processing_status", "pending").lt("uploaded_at", (now_utc()-timedelta(hours=1)).isoformat()).execute()
                        if stuck.data:
                            supabase.table("documents").update({"processing_status": "failed"}).in_("id", [d['id'] for d in stuck.data]).execute()
                    elif tid == "clean_sessions":
                        supabase.table("sessions").delete().lt("expires_at", now_utc().isoformat()).execute()
                    show_toast("Done!")
                    st.rerun()

    elif section == "📋 Audit":
        st.markdown("#### 📋 Audit")
        if supabase:
            for log in supabase.table("audit_logs").select("*").order("created_at", desc=True).limit(50).execute().data or []:
                st.caption(f"{str(log.get('created_at',''))[:16]} | {log.get('user_email','')} | {log.get('action','')}")

    elif section == "🚨 Emergency":
        st.markdown("#### 🚨 Emergency")
        maint = False
        if redis_client:
            try:
                maint = redis_client.get("maintenance_mode") == "1"
            except Exception:
                pass
                
        if not maint:
            if st.button("🔧 Enable Maintenance", type="secondary", key="mon"):
                if redis_client:
                    redis_client.set("maintenance_mode", "1")
                show_toast("Maintenance ON", "warning")
                st.rerun()
        else:
            st.warning("⚠️ In maintenance")
            if st.button("✅ Disable Maintenance", key="moff"):
                if redis_client:
                    redis_client.delete("maintenance_mode")
                show_toast("Maintenance OFF")
                st.rerun()
                
        st.divider()
        if st.button("🔒 Force Logout All", type="secondary", key="flog"):
            supabase.table("sessions").delete().neq("id", "0").execute()
            show_toast("All logged out", "warning")
            
        if st.button("🗑️ Clear AI Cache", type="secondary", key="ccache"):
            if redis_client:
                for k in redis_client.scan_iter("ai_cache:*"):
                    redis_client.delete(k)
                show_toast("Cache cleared")

    elif section == "📢 Announcements":
        st.markdown("#### 📢 Announcements")
        with st.form("ann"):
            title = st.text_input("Title")
            msg = st.text_area("Message", height=100)
            pri = st.selectbox("Priority", ["info", "warning", "critical"])
            dur = st.number_input("Days", 1, 30, 7)
            if st.form_submit_button("Broadcast"):
                if title and msg:
                    supabase.table("announcements").insert({"title": title, "message": msg, "priority": pri, "expires_at": (now_utc()+timedelta(days=int(dur))).isoformat(), "created_by": u["email"]}).execute()
                    show_toast("Posted!")
                    st.rerun()
                    
        st.divider()
        if supabase:
            for ann in supabase.table("announcements").select("*").gt("expires_at", now_utc().isoformat()).order("created_at", desc=True).execute().data or []:
                c1, c2 = st.columns([4, 1])
                icon = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(ann.get('priority', 'info'), "ℹ️")
                c1.write(f"{icon} **{ann['title']}**")
                c1.caption(f"{ann['message'][:100]}...")
                if c2.button("🗑️", key=f"dann_{ann['id']}"):
                    supabase.table("announcements").delete().eq("id", ann['id']).execute()
                    st.rerun()

    elif section == "📊 Analytics":
        st.markdown("#### 📊 Analytics")
        if supabase:
            try:
                logs = supabase.table("audit_logs").select("user_email, action").gte("created_at", (now_utc()-timedelta(days=30)).isoformat()).execute().data or []
                if logs:
                    users = supabase.table("users").select("email, office_name").execute().data or []
                    em = {u['email']: u.get('office_name', 'Unknown') for u in users}
                    oc = {}
                    for l in logs:
                        o = em.get(l['user_email'], 'Unknown')
                        oc[o] = oc.get(o, 0) + 1
                    if oc:
                        st.bar_chart(pd.DataFrame([{'Office': k, 'Actions': v} for k, v in oc.items()]).set_index('Office'))
                        
                    ac = {}
                    for l in logs:
                        ac[l['action']] = ac.get(l['action'], 0) + 1
                    st.markdown("##### Top Features")
                    for a, c in sorted(ac.items(), key=lambda x: -x[1])[:5]:
                        st.write(f"**{a}**: {c}")
            except Exception:
                pass

# ============================================
# NAVIGATION & MAIN ENTRY
# ============================================
def render_sidebar_nav():
    """Professional sidebar navigation using streamlit-option-menu."""
    with st.sidebar:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0A66C2 0%, #004182 100%); padding: 16px; border-radius: 12px; color: white; margin-bottom: 20px;">
            <div style="font-size: 14px; opacity: 0.9;">Welcome,</div>
            <div style="font-size: 18px; font-weight: 700;">{st.session_state.user.get('name', 'User')}</div>
            <div style="font-size: 12px; opacity: 0.8;">🏢 {st.session_state.user.get('office_name', 'Office')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        menu_items = ["Feed", "Workspace", "Tapal", "Documents", "AI Assistant"]
        menu_icons = ["house", "briefcase", "envelope-paper", "file-earmark-text", "robot"]
        
        if st.session_state.user.get("admin_level") in ["system_admin", "office_admin"]:
            menu_items.append("Admin Panel")
            menu_icons.append("gear")
            
        selected = option_menu(
            "Navigation", 
            menu_items, 
            icons=menu_icons, 
            menu_icon="cast", 
            default_index=0, 
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "#0A66C2", "font-size": "18px"}, 
                "nav-link": {"font-size": "15px", "text-align": "left", "margin": "2px 0", "padding": "12px 16px"}, 
                "nav-link-selected": {"background-color": "#0A66C2", "color": "white", "font-weight": "600"}
            }
        )
        
        st.divider()
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            logout()
            
    page_map = {
        "Feed": "feed", "Workspace": "workspace", "Tapal": "tapal", 
        "Documents": "documents", "AI Assistant": "ai", "Admin Panel": "admin"
    }
    st.session_state.page = page_map.get(selected, "feed")

def main():
    """Main application entry point."""
    # Check Maintenance Mode
    if redis_client:
        try:
            if redis_client.get("maintenance_mode") == "1":
                st.markdown("""
                <div style="text-align:center; padding:50px;">
                    <h1>🔧 Under Maintenance</h1>
                    <p>We're making improvements. Please check back soon.</p>
                    <p><small>— RTA Anubandhan Team</small></p>
                </div>
                """, unsafe_allow_html=True)
                return
        except Exception:
            pass
            
    init_session_state()
    try_auto_login()
    
    if st.session_state.logged_in:
        render_sidebar_nav()
        
    if not st.session_state.logged_in:
        show_login()
    else:
        page = st.session_state.page
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
        elif page == "ai":
            show_ai()
        elif page == "admin":
            show_admin()
        else:
            show_feed()

if __name__ == "__main__":
    main()
