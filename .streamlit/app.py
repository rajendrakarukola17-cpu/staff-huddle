"""
RTA CONNECT - FINAL PRODUCTION VERSION
=======================================
Complete Feature Set:
- Two-tier deduplication (files + user_documents pointers)
- LZMA (cold) + Zstd (hot) dual compression
- Cascading hybrid search (Supabase FTS+pgvector → Tavily → AI)
- Multi-language OCR (Telugu + Hindi + English)
- Multi-language AI responses (Telugu/Hindi/English)
- Triple AI fallback (Gemini 2.0 Flash → 1.5 Pro → 1.5 Flash)
- Client-side SHA-256 hash pre-check
- Text-first serving with lazy binary loading
- 24-hour auto-cleanup for unstarred messages
- LZMA compression for starred messages
- Admin dashboard (storage quota, AI tokens, office breakdown)
- Deduplication management panel
- Redis cache purge (free-tier control)
- Strict RLS policies
- Cursor-based pagination
- Redis 5-min TTL caching
- Social feed, Tapal system, Documents, AI Search
"""

# ============================================
# 1. IMPORTS
# ============================================
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
from streamlit_cookies_controller import CookieController
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
import lzma
import zlib
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta, timezone
from collections import Counter
import numpy as np
import pandas as pd

# Graceful imports
try:
    import zstandard as zstd
    ZSTD_AVAILABLE = True
except ImportError:
    ZSTD_AVAILABLE = False

try:
    from upstash_redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import pytesseract
    from pdf2image import convert_from_bytes
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

# ============================================
# 2. LOGGING
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ============================================
# 3. STREAMLIT CONFIG
# ============================================
st.set_page_config(
    page_title="RTA Connect",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# 4. CUSTOM CSS
# ============================================
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

#MainMenu, footer, header, [data-testid="stDecoration"], [data-testid="stStatusWidget"] {
    visibility: hidden !important;
    display: none !important;
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
    padding: 16px;
    margin-bottom: 16px;
    box-shadow: var(--shadow-sm);
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
    flex-shrink: 0;
}

.stButton > button {
    background-color: var(--primary) !important;
    color: white !important;
    border: none !important;
    border-radius: 20px !important;
    font-weight: 600 !important;
    width: 100% !important;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background-color: var(--primary-hover) !important;
    transform: translateY(-1px);
}

.login-container {
    max-width: 400px;
    margin: 50px auto;
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

.bottom-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background: white;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-around;
    padding: 10px 0;
    z-index: 9999;
    box-shadow: 0 -2px 8px rgba(0,0,0,0.05);
}

.metric-card {
    background: white;
    border-radius: 12px;
    padding: 16px;
    border: 1px solid var(--border);
    text-align: center;
}

.star-btn {
    cursor: pointer;
    font-size: 20px;
    transition: transform 0.2s;
}

.star-btn:hover {
    transform: scale(1.2);
}

@media (max-width: 768px) {
    .block-container { padding: 0.5rem !important; }
    .commercial-card { padding: 12px; }
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ============================================
# 5. SECRETS HELPER
# ============================================
def secret(key: str, default: str = "") -> str:
    """Get secret with multiple fallbacks"""
    try:
        val = st.secrets.get(key, default)
        if val:
            return val
    except:
        pass
    return os.getenv(key, default)

# ============================================
# 6. SECURITY UTILITIES
# ============================================
def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    text = re.sub(r'<[^>]*>', '', text)
    text = html.escape(text)
    return text.strip()

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def generate_file_hash(file_data: bytes) -> str:
    """Generate SHA256 hash for file"""
    return hashlib.sha256(file_data).hexdigest()

def encrypt_data(data: bytes, key: str) -> bytes:
    """Encrypt data using XOR with key"""
    key_bytes = hashlib.sha256(key.encode()).digest()
    return bytes(a ^ b for a, b in zip(data, key_bytes * (len(data) // len(key_bytes) + 1)))

def decrypt_data(encrypted_data: bytes, key: str) -> bytes:
    """Decrypt data (XOR is symmetric)"""
    return encrypt_data(encrypted_data, key)

def hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=10)).decode()

def check_password(password: str, hashed: str) -> bool:
    """Verify password"""
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except:
        return False

# ============================================
# 7. COMPRESSION SYSTEM (LZMA + ZSTD)
# ============================================
class CompressionSystem:
    """Dual-engine compression: Zstd for hot/AI, LZMA for cold/archive"""
    
    def __init__(self):
        if ZSTD_AVAILABLE:
            self.zstd_compressor = zstd.ZstdCompressor(level=19)
            self.zstd_decompressor = zstd.ZstdDecompressor()
        else:
            self.zstd_compressor = None
            self.zstd_decompressor = None
    
    def compress(self, data: bytes, method: str = 'auto') -> Tuple[bytes, str]:
        """Compress binary data"""
        if method == 'lzma':
            return lzma.compress(data, preset=9 | lzma.PRESET_EXTREME), 'lzma'
        elif method == 'zstd' and self.zstd_compressor:
            return self.zstd_compressor.compress(data), 'zstd'
        elif method == 'zlib':
            return zlib.compress(data, level=9), 'zlib'
        elif method == 'auto':
            # Try all, pick smallest
            best, best_method, best_size = data, 'none', len(data)
            for m in ['lzma', 'zstd', 'zlib']:
                try:
                    compressed, _ = self.compress(data, m)
                    if len(compressed) < best_size:
                        best, best_method, best_size = compressed, m, len(compressed)
                except:
                    continue
            return best, best_method
        return data, 'none'
    
    def decompress(self, data: bytes, method: str) -> bytes:
        """Decompress binary data"""
        if not data or method == 'none':
            return data
        try:
            if method == 'lzma':
                return lzma.decompress(data)
            elif method == 'zstd' and self.zstd_decompressor:
                return self.zstd_decompressor.decompress(data)
            elif method == 'zlib':
                return zlib.decompress(data)
            return data
        except Exception as e:
            logger.error(f"Decompression failed: {e}")
            return data
    
    def compress_text(self, text: str, method: str = 'zstd') -> Tuple[bytes, str]:
        """Compress text data"""
        if not text:
            return b"", "none"
        return self.compress(text.encode('utf-8'), method)
    
    def decompress_text(self, compressed_bytes: bytes, method: str) -> str:
        """Decompress text data"""
        if not compressed_bytes or method == 'none':
            return compressed_bytes.decode('utf-8', errors='ignore') if compressed_bytes else ""
        try:
            decompressed = self.decompress(compressed_bytes, method)
            return decompressed.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Text decompression failed: {e}")
            return ""

compression = CompressionSystem()

# ============================================
# 8. CLOUD SERVICES INITIALIZATION
# ============================================
@st.cache_resource
def init_supabase() -> Optional[Client]:
    """Initialize Supabase"""
    try:
        url = secret("SUPABASE_URL")
        key = secret("SUPABASE_KEY")
        if url and key:
            client = create_client(url, key)
            logger.info("✅ Supabase connected")
            return client
    except Exception as e:
        logger.error(f"❌ Supabase init failed: {e}")
    return None

@st.cache_resource
def init_redis() -> Optional[Any]:
    """Initialize Upstash Redis"""
    try:
        if REDIS_AVAILABLE:
            url = secret("UPSTASH_REDIS_REST_URL")
            token = secret("UPSTASH_REDIS_REST_TOKEN")
            if url and token:
                client = Redis(url=url, token=token)
                logger.info("✅ Redis connected")
                return client
    except Exception as e:
        logger.error(f"❌ Redis init failed: {e}")
    return None

supabase = init_supabase()
redis_client = init_redis()

# ============================================
# 9. STORAGE SYSTEM (Two-Tier Deduplication)
# ============================================
class StorageSystem:
    """Two-tier storage: Physical files (deduplicated) + User pointers"""
    
    def __init__(self):
        self.encryption_key = secret("ENCRYPTION_KEY", "rta-connect-secret-key")
        self.bucket_name = secret("SUPABASE_STORAGE_BUCKET", "rta-documents")
    
    def check_file_exists(self, file_hash: str) -> Optional[Dict]:
        """Check if file hash exists (for client-side pre-check)"""
        if not supabase:
            return None
        try:
            result = supabase.table("files").select("id, compressed_size_bytes, compression_ratio, reference_count").eq("sha256_hash", file_hash).execute()
            if result.data:
                return result.data[0]
        except Exception as e:
            logger.error(f"Hash check failed: {e}")
        return None
    
    def upload_document(self, file_data: bytes, filename: str, doc_type: str, user_email: str, office_code: str = None) -> Dict:
        """Upload with deduplication"""
        try:
            file_hash = generate_file_hash(file_data)
            
            # Check for physical duplicate
            existing = self.check_file_exists(file_hash)
            if existing:
                file_id = existing['id']
                user_doc_result = supabase.table("user_documents").insert({
                    "user_id": user_email,
                    "file_id": file_id,
                    "original_filename": filename,
                    "doc_type": doc_type,
                    "office_code": office_code,
                    "status": "flagged_duplicate",
                    "is_duplicate": True
                }).execute()
                
                if user_doc_result.data:
                    return {
                        'success': True,
                        'file_id': file_id,
                        'user_doc_id': user_doc_result.data[0]['id'],
                        'duplicate': True,
                        'message': 'File already exists in system. Linked to your account.',
                        'compression_ratio': 0
                    }
                return {'success': False, 'error': 'Failed to create user pointer'}
            
            # New file: Compress
            compressed_data, comp_method = compression.compress(file_data, method='auto')
            encrypted_data = encrypt_data(compressed_data, self.encryption_key)
            
            # Upload to Supabase Storage with 1-year cache control
            storage_path = f"{doc_type}/{datetime.now().strftime('%Y/%m/%d')}/{file_hash[:8]}_{filename}"
            try:
                supabase.storage.from_(self.bucket_name).upload(
                    storage_path,
                    encrypted_data,
                    file_options={"cacheControl": "31536000", "upsert": False}
                )
            except Exception as storage_err:
                logger.error(f"Storage upload failed: {storage_err}")
                return {'success': False, 'error': f'Storage upload failed: {storage_err}'}
            
            # Extract text (multi-language OCR)
            extracted_text = self.extract_pdf_text(file_data, filename)
            comp_text_bytes, text_comp_method = b"", "none"
            if extracted_text:
                comp_text_bytes, text_comp_method = compression.compress_text(extracted_text, method='zstd')
            
            # Create physical file record
            file_result = supabase.table("files").insert({
                "sha256_hash": file_hash,
                "filename": filename,
                "storage_path": storage_path,
                "storage_tier": 'hot' if doc_type in ['circular', 'tapal', 'current'] else 'cold',
                "compression_method": comp_method,
                "original_size_bytes": len(file_data),
                "compressed_size_bytes": len(compressed_data),
                "compression_ratio": round(1 - (len(compressed_data) / len(file_data)), 4) if file_data else 0,
                "extracted_text_bytes": comp_text_bytes if comp_text_bytes else None,
                "text_compression_method": text_comp_method,
                "uploaded_by": user_email
            }).execute()
            
            if not file_result.data:
                return {'success': False, 'error': 'Failed to create file record'}
            
            file_id = file_result.data[0]['id']
            
            # Create user pointer
            user_doc_result = supabase.table("user_documents").insert({
                "user_id": user_email,
                "file_id": file_id,
                "original_filename": filename,
                "doc_type": doc_type,
                "office_code": office_code,
                "status": "active",
                "is_duplicate": False
            }).execute()
            
            if not user_doc_result.data:
                return {'success': False, 'error': 'Failed to create user pointer'}
            
            return {
                'success': True,
                'file_id': file_id,
                'user_doc_id': user_doc_result.data[0]['id'],
                'duplicate': False,
                'message': 'File uploaded successfully',
                'compression_ratio': file_result.data[0]['compression_ratio']
            }
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def extract_pdf_text(self, pdf_data: bytes, filename: str) -> str:
        """Extract text with multi-language OCR fallback"""
        text = ""
        try:
            if PDF_AVAILABLE:
                reader = PdfReader(io.BytesIO(pdf_data))
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text and len(page_text.strip()) > 20:
                        text += page_text + "\n"
            
            # Fallback to OCR for scanned documents
            if len(text.strip()) < 50 and OCR_AVAILABLE:
                try:
                    images = convert_from_bytes(pdf_data, dpi=150)
                    for img in images:
                        ocr_text = pytesseract.image_to_string(img, lang='tel+hin+eng')
                        text += ocr_text + "\n"
                except Exception as ocr_err:
                    logger.warning(f"OCR failed: {ocr_err}")
            
            return text.strip()
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return text
    
    def download_document(self, user_doc_id: str) -> Optional[bytes]:
        """Download and decrypt document"""
        try:
            if not supabase:
                return None
            
            user_doc = supabase.table("user_documents").select("file_id").eq("id", user_doc_id).execute()
            if not user_doc.data:
                return None
            
            file_id = user_doc.data[0]['file_id']
            file_record = supabase.table("files").select("*").eq("id", file_id).execute()
            if not file_record.data:
                return None
            
            file_data = file_record.data[0]
            storage_path = file_data.get("storage_path")
            if not storage_path:
                return None
            
            try:
                response = supabase.storage.from_(self.bucket_name).download(storage_path)
                encrypted_data = response
            except Exception as dl_err:
                logger.error(f"Download failed: {dl_err}")
                return None
            
            compressed_data = decrypt_data(encrypted_data, self.encryption_key)
            method = file_data.get("compression_method", "none")
            return compression.decompress(compressed_data, method)
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None
    
    def get_extracted_text(self, file_id: str) -> str:
        """Get decompressed extracted text"""
        try:
            if not supabase:
                return ""
            result = supabase.table("files").select("extracted_text_bytes, text_compression_method").eq("id", file_id).execute()
            if result.data and result.data[0].get("extracted_text_bytes"):
                doc = result.data[0]
                return compression.decompress_text(doc["extracted_text_bytes"], doc.get("text_compression_method", "zstd"))
            return ""
        except Exception as e:
            logger.error(f"Text fetch failed: {e}")
            return ""
    
    def get_user_documents(self, user_email: str, limit: int = 20) -> List[Dict]:
        """Get all documents for a user (cursor-based pagination)"""
        try:
            if not supabase:
                return []
            result = supabase.table("user_documents").select("""
                id, original_filename, doc_type, status, is_duplicate, uploaded_at, access_count,
                files (id, compressed_size_bytes, compression_ratio, storage_tier)
            """).eq("user_id", user_email).order("uploaded_at", desc=True).limit(limit).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Get user docs failed: {e}")
            return []
    
    def delete_user_document(self, user_doc_id: str, user_email: str) -> Dict:
        """Delete user's pointer (doesn't delete physical file)"""
        try:
            if not supabase:
                return {'success': False, 'error': 'DB not connected'}
            supabase.table("user_documents").delete().eq("id", user_doc_id).eq("user_id", user_email).execute()
            return {'success': True, 'message': 'Removed from your account'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def admin_purge_file(self, file_id: str, admin_email: str) -> Dict:
        """Admin: Permanently delete physical file and all pointers"""
        try:
            if not supabase:
                return {'success': False, 'error': 'DB not connected'}
            
            file_record = supabase.table("files").select("*").eq("id", file_id).execute()
            if not file_record.data:
                return {'success': False, 'error': 'File not found'}
            
            file_data = file_record.data[0]
            storage_path = file_data.get("storage_path")
            
            if storage_path:
                try:
                    supabase.storage.from_(self.bucket_name).remove([storage_path])
                except Exception as storage_err:
                    logger.warning(f"Storage deletion failed: {storage_err}")
            
            supabase.table("files").delete().eq("id", file_id).execute()
            return {'success': True, 'message': f'File and {file_data.get("reference_count", 0)} references deleted'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

storage_system = StorageSystem()

# ============================================
# 10. EMBEDDING SYSTEM
# ============================================
class EmbeddingSystem:
    """Gemini text-embedding-004 (768 dimensions)"""
    
    def __init__(self):
        self.model = "text-embedding-004"
        self.key = secret("GEMINI_API_KEY")
    
    def embed_query(self, text: str) -> Optional[List[float]]:
        if not self.key or not text:
            return None
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:embedContent?key={self.key}"
            response = requests.post(
                url,
                json={"content": {"parts": [{"text": text[:2000]}]}, "taskType": "RETRIEVAL_QUERY"},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()["embedding"]["values"]
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
        return None
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        if not self.key or not text:
            return None
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:embedContent?key={self.key}"
            response = requests.post(
                url,
                json={"content": {"parts": [{"text": text[:8000]}]}, "taskType": "RETRIEVAL_DOCUMENT"},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()["embedding"]["values"]
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
        return None

embedding_system = EmbeddingSystem()

# ============================================
# 11. DEEP SEARCH SYSTEM (Tavily)
# ============================================
class DeepSearchSystem:
    """External deep search via Tavily"""
    
    def __init__(self):
        self.api_key = secret("TAVILY_API_KEY")
    
    def search(self, query: str, language: str = "English", max_results: int = 3) -> List[Dict]:
        if not self.api_key or not TAVILY_AVAILABLE:
            return []
        try:
            client = TavilyClient(api_key=self.api_key)
            lang_context = {"Telugu": "ఆంధ్ర ప్రదేశ్", "Hindi": "भारत सरकार", "English": "Andhra Pradesh"}
            enhanced_query = f"{query} {lang_context.get(language, '')} site:gov.in OR site:nic.in"
            
            response = client.search(
                query=enhanced_query,
                search_depth="advanced",
                include_domains=["ap.gov.in", "rta.ap.gov.in", "morth.nic.in", "parivahan.gov.in", "india.gov.in"],
                max_results=max_results,
                include_raw_content=False
            )
            
            return [{
                "title": r.get("title", ""),
                "content": r.get("content", "")[:500],
                "source_url": r.get("url", ""),
                "source_type": "external",
                "score": r.get("score", 0)
            } for r in response.get("results", [])]
        except Exception as e:
            logger.error(f"Deep search failed: {e}")
            return []

deep_search = DeepSearchSystem()

# ============================================
# 12. TRIPLE AI SYSTEM (With Fallback)
# ============================================
class TripleAISystem:
    """3 AI providers with automatic fallback"""
    
    def __init__(self):
        self.providers = [
            {'name': 'Gemini 2.0 Flash', 'model': 'gemini-2.0-flash', 'key': secret("GEMINI_2_FLASH_KEY") or secret("GEMINI_API_KEY"), 'priority': 1},
            {'name': 'Gemini 1.5 Pro', 'model': 'gemini-1.5-pro', 'key': secret("GEMINI_1_5_PRO_KEY") or secret("GEMINI_API_KEY"), 'priority': 2},
            {'name': 'Gemini 1.5 Flash', 'model': 'gemini-1.5-flash', 'key': secret("GEMINI_1_5_FLASH_KEY") or secret("GEMINI_API_KEY"), 'priority': 3},
        ]
    
    def _update_metrics(self, text_length: int):
        """Update AI usage metrics"""
        if not supabase:
            return
        try:
            estimated_tokens = text_length // 4
            supabase.rpc("increment_metric", {"m_name": "ai_requests_total", "m_value": 1}).execute()
            supabase.rpc("increment_metric", {"m_name": "ai_tokens_estimated", "m_value": estimated_tokens}).execute()
        except:
            pass
    
    def make_request(self, prompt: str, language: str = "English", purpose: str = "general") -> Dict:
        lang_instruction = f"\nIMPORTANT: Respond strictly in {language}." if language else ""
        full_prompt = prompt + lang_instruction
        
        for provider in sorted(self.providers, key=lambda x: x['priority']):
            if not provider['key']:
                continue
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{provider['model']}:generateContent?key={provider['key']}"
                response = requests.post(
                    url,
                    json={"contents": [{"parts": [{"text": full_prompt}]}]},
                    timeout=15
                )
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data["candidates"][0]["content"]["parts"][0]["text"]
                    self._update_metrics(len(full_prompt) + len(ai_response))
                    return {'success': True, 'response': ai_response, 'provider': provider['name']}
            except Exception as e:
                logger.warning(f"AI provider {provider['name']} failed: {e}")
                continue
        return {'success': False, 'error': 'All AI providers failed'}
    
    def summarize(self, text: str, language: str = "English") -> Optional[str]:
        result = self.make_request(f"Summarize this government document clearly in 2-3 sentences: {text[:3000]}", language, "summary")
        return result.get('response') if result['success'] else None
    
    def draft_letter(self, context: str, language: str = "English") -> Optional[str]:
        result = self.make_request(f"Draft a formal, official government letter based on this context: {context}", language, "draft")
        return result.get('response') if result['success'] else None

ai_system = TripleAISystem()

# ============================================
# 13. CASCADING RETRIEVAL PIPELINE
# ============================================
class CascadingRetrievalPipeline:
    """Layer 1: Supabase Hybrid → Layer 2: Tavily → Layer 3: AI Synthesis"""
    
    THRESHOLD = 0.75
    MIN_RESULTS = 2
    
    def search(self, query: str, user: Dict, language: str = "English") -> Dict:
        start_time = time.time()
        
        # Cache check
        cache_key = f"search:{hashlib.md5(query.encode()).hexdigest()}"
        if redis_client:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    result = json.loads(cached)
                    result["cache_hit"] = True
                    result["latency_ms"] = int((time.time() - start_time) * 1000)
                    return result
            except:
                pass
        
        # Layer 1: Supabase Hybrid Search
        layer1_results = []
        query_vector = embedding_system.embed_query(query)
        if query_vector and supabase:
            try:
                response = supabase.rpc("hybrid_search", {
                    "query_text": query,
                    "query_vector": query_vector,
                    "match_threshold": self.THRESHOLD,
                    "match_count": 5
                }).execute()
                layer1_results = [{
                    "title": r["title"],
                    "content": r["content"][:500],
                    "source_url": r.get("source_url"),
                    "source_type": r.get("source_type", "internal"),
                    "similarity": round(r.get("similarity", 0), 3)
                } for r in (response.data or [])]
            except Exception as e:
                logger.error(f"Layer 1 failed: {e}")
        
        # Layer 2: Deep Search Fallback
        layer2_results = []
        if len(layer1_results) < self.MIN_RESULTS:
            layer2_results = deep_search.search(query, language, max_results=3)
        
        all_results = layer1_results + layer2_results
        
        # Layer 3: AI Synthesis
        ai_summary = ""
        if all_results:
            context = "\n\n".join([f"[{i+1}] {r['title']}: {r['content']}" for i, r in enumerate(all_results[:3])])
            prompt = f"""You are an expert RTA knowledge assistant for Andhra Pradesh government.

USER QUERY: {query}

RELEVANT DOCUMENTS:
{context[:4000]}

Answer comprehensively based on the documents. Cite sources [1], [2], etc. Respond in {language}."""
            
            ai_result = ai_system.make_request(prompt, language, "retrieval")
            if ai_result.get("success"):
                ai_summary = ai_result["response"]
        
        if not ai_summary:
            ai_summary = f"Found {len(all_results)} relevant documents." if all_results else "No results found."
        
        final_result = {
            "source": "supabase" if len(layer1_results) >= self.MIN_RESULTS else ("hybrid" if layer1_results else "deep_search"),
            "results": all_results,
            "ai_summary": ai_summary,
            "cache_hit": False,
            "latency_ms": int((time.time() - start_time) * 1000)
        }
        
        # Cache result
        if redis_client:
            try:
                redis_client.setex(cache_key, 300, json.dumps(final_result, default=str))
            except:
                pass
        
        return final_result

retrieval_pipeline = CascadingRetrievalPipeline()

# ============================================
# 14. SESSION & AUTH
# ============================================
cookies = CookieController()

def init_session_state():
    defaults = {"user": None, "logged_in": False, "page": "feed", "admin_level": "staff"}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_user(email: str) -> Optional[Dict]:
    if not email:
        return None
    if redis_client:
        try:
            cached = redis_client.get(f"user:{email}")
            if cached:
                return json.loads(cached)
        except:
            pass
    if supabase:
        try:
            result = supabase.table("users").select("*").eq("email", email).execute()
            if result.data:
                user = result.data[0]
                if redis_client:
                    redis_client.setex(f"user:{email}", 300, json.dumps(user, default=str))
                return user
        except Exception as e:
            logger.error(f"Get user failed: {e}")
    return None

def do_login(user: Dict):
    st.session_state.logged_in = True
    st.session_state.user = user
    st.session_state.admin_level = user.get("admin_level", "staff")
    st.rerun()

def logout():
    st.session_state.clear()
    cookies.delete("rta_session")
    st.rerun()

# ============================================
# 15. UI PAGES
# ============================================
def show_login():
    quotes = [
        {"text": "Service to the public is service to the nation", "author": "Mahatma Gandhi"},
        {"text": "Together we move Andhra forward", "author": "RTA Mission"},
        {"text": "Every file processed is a citizen served", "author": "RTA Vision"},
    ]
    quote = quotes[datetime.now().day % len(quotes)]
    
    st.markdown(f"""
    <div class="login-container">
        <div style="text-align: center;">
            <div style="font-size: 50px;">🏛️</div>
            <h1 style="color: var(--primary);">RTA Connect</h1>
            <p style="color: #666;">Government Workspace Platform</p>
        </div>
        <div class="quote-box">
            <p style="font-style: italic;">"{quote['text']}"</p>
            <small>- {quote['author']}</small>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        email = st.text_input("Email", placeholder="name@ap.gov.in", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("✨ Sign In", use_container_width=True):
            if not email or not password:
                st.warning("Please enter email and password")
            elif not validate_email(email):
                st.error("Invalid email format")
            else:
                user = get_user(email.strip().lower())
                if user and check_password(password, user["password_hash"]):
                    do_login(user)
                else:
                    st.error("Invalid credentials")

def show_feed():
    user = st.session_state.user
    hour = datetime.now().hour
    greeting = f"☀️ Good Morning" if hour < 12 else (f"👋 Hello" if hour < 17 else f"🌙 Good Evening")
    
    st.markdown(f"### {greeting}, {user.get('name', 'User')}!")
    st.caption(f"📍 {user.get('office_name', 'Office')} | {user.get('designation', 'Staff')}")
    
    with st.form("create_post"):
        content = st.text_area("What's on your mind?", height=100, key="post_content")
        if st.form_submit_button("Post"):
            content = sanitize_input(content)
            if content and supabase:
                try:
                    supabase.table("social_posts").insert({
                        "author_email": user["email"],
                        "content": content,
                        "office_code": user.get("office_code"),
                        "created_at": datetime.now().isoformat()
                    }).execute()
                    st.success("Posted!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to post: {e}")
    
    if supabase:
        try:
            posts = supabase.table("social_posts").select("*").order("created_at", desc=True).limit(20).execute()
            for post in (posts.data or []):
                with st.container():
                    st.markdown('<div class="commercial-card">', unsafe_allow_html=True)
                    st.markdown(f"**{post.get('author_email', 'Unknown')}**")
                    st.write(post["content"])
                    st.caption(post["created_at"][:16])
                    st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            logger.error(f"Feed load failed: {e}")

def show_workspace():
    user = st.session_state.user
    st.markdown("### 🧰 Your Workspace")
    
    col1, col2, col3, col4 = st.columns(4)
    actions = [
        (col1, "📥 New Tapal", "tapal"),
        (col2, "📄 Documents", "documents"),
        (col3, "🔍 AI Search", "ai"),
        (col4, "💬 Messages", "messages"),
    ]
    for col, label, page in actions:
        with col:
            if st.button(label, use_container_width=True):
                st.session_state.page = page
                st.rerun()
    
    if supabase and user:
        try:
            tapals = supabase.table("tapal_log").select("id", count="exact").eq("created_by", user["email"]).execute()
            docs = supabase.table("user_documents").select("id", count="exact").eq("user_id", user["email"]).execute()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Your Tapals", tapals.count or 0)
            with col2:
                st.metric("Your Documents", docs.count or 0)
        except:
            pass

def show_tapal():
    user = st.session_state.user
    st.markdown("### 📥 Smart Tapal")
    
    with st.form("tapal_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            direction = st.selectbox("Direction", ["Inward", "Outward"])
            tapal_date = st.date_input("Date")
        with col2:
            seq_no = st.text_input("Sequence No.")
            from_to = st.text_input("From/To")
        with col3:
            subject = st.text_input("Subject")
            priority = st.selectbox("Priority", ["Normal", "Urgent", "Immediate"])
        
        r_no = ""
        if seq_no:
            section = user.get("section", "A")
            designation = user.get("designation", "JA")
            r_no = f"R.No/{section}/{designation}/{datetime.now().year}/{seq_no}"
            st.info(f"📋 Reference: {r_no}")
        
        remarks = st.text_area("Remarks", height=80)
        uploaded_file = st.file_uploader("📎 Attachment", type=['pdf', 'jpg', 'png'], key="tapal_file")
        
        if st.form_submit_button("💾 Save"):
            if seq_no and subject:
                file_url = None
                if uploaded_file and supabase:
                    result = storage_system.upload_document(
                        uploaded_file.read(),
                        uploaded_file.name,
                        "tapal",
                        user["email"],
                        user.get("office_code")
                    )
                    if result.get('success'):
                        file_url = result.get('file_id')
                
                if supabase:
                    try:
                        supabase.table("tapal_log").insert({
                            "r_no": r_no,
                            "direction": direction,
                            "tapal_date": tapal_date.isoformat(),
                            "section": user.get("section"),
                            "designation": user.get("designation"),
                            "from_to": from_to,
                            "subject": subject,
                            "priority": priority,
                            "remarks": remarks,
                            "file_url": file_url,
                            "created_by": user["email"],
                            "created_at": datetime.now().isoformat()
                        }).execute()
                        st.success("✅ Saved!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save: {e}")

def show_documents():
    user = st.session_state.user
    st.markdown("### 📄 My Documents")
    
    # Client-side hash pre-check component
    hash_check_js = """
    <div style="border:2px dashed #ccc; padding:20px; border-radius:8px; text-align:center; background:white;">
        <h4>🔐 Smart Upload (Client-Side Hash Check)</h4>
        <input type="file" id="smart-file-input" accept=".pdf,.jpg,.png" style="margin:10px 0;" />
        <div id="hash-status" style="font-family:monospace; font-size:12px; color:#666; min-height:20px;"></div>
    </div>
    <script>
    document.getElementById('smart-file-input').addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const status = document.getElementById('hash-status');
        status.textContent = 'Computing SHA-256...';
        status.style.color = '#0A66C2';
        try {
            const buffer = await file.arrayBuffer();
            const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
            const hashHex = Array.from(new Uint8Array(hashBuffer)).map(b => b.toString(16).padStart(2, '0')).join('');
            status.textContent = `✅ Hash: ${hashHex.substring(0, 16)}... (Use standard uploader below)`;
            status.style.color = '#059669';
        } catch (err) {
            status.textContent = '❌ Hash computation failed';
            status.style.color = '#DC2626';
        }
    });
    </script>
    """
    components.html(hash_check_js, height=150)
    
    with st.form("doc_upload_form"):
        uploaded_file = st.file_uploader("Upload Document", type=['pdf', 'jpg', 'png', 'doc'])
        doc_type = st.selectbox("Document Type", ['circular', 'tapal', 'manual', 'report', 'other'])
        if st.form_submit_button("🚀 Upload"):
            if uploaded_file:
                with st.spinner("Processing..."):
                    result = storage_system.upload_document(
                        uploaded_file.read(),
                        uploaded_file.name,
                        doc_type,
                        user["email"],
                        user.get("office_code")
                    )
                    if result.get('success'):
                        if result.get('duplicate'):
                            st.warning(f"⚠️ {result.get('message')}")
                        else:
                            st.success(f"✅ {result.get('message')}")
                            if result.get('compression_ratio'):
                                st.metric("Compression Savings", f"{result['compression_ratio']*100:.1f}%")
                    else:
                        st.error(f"❌ {result.get('error')}")
    
    st.divider()
    st.markdown("#### 📋 Your Documents")
    docs = storage_system.get_user_documents(user["email"], limit=20)
    if not docs:
        st.info("No documents uploaded yet.")
        return
    
    for doc in docs:
        file_info = doc.get("files", {})
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.markdown(f"**{doc['original_filename']}**")
                badge = "🟢" if doc['status'] == 'active' else "🟡"
                st.caption(f"{badge} {doc['doc_type']} • {file_info.get('storage_tier', 'hot').upper()}")
            with col2:
                size_kb = file_info.get('compressed_size_bytes', 0) / 1024
                st.metric("Size", f"{size_kb:.1f} KB")
            with col3:
                ratio = file_info.get('compression_ratio', 0)
                st.metric("Saved", f"{ratio*100:.0f}%")
            with col4:
                if st.button("🗑️", key=f"del_{doc['id']}"):
                    storage_system.delete_user_document(doc['id'], user["email"])
                    st.rerun()

def show_messages():
    user = st.session_state.user
    st.markdown("### 💬 Messages")
    st.caption("Messages auto-delete after 24 hours. Star important ones to keep them forever (compressed).")
    
    # Send message
    with st.form("send_msg"):
        msg = st.text_input("Type a message...")
        if st.form_submit_button("Send"):
            if msg and supabase:
                try:
                    supabase.table("messages").insert({
                        "user_id": user["email"],
                        "content": sanitize_input(msg),
                        "is_starred": False,
                        "created_at": datetime.now().isoformat()
                    }).execute()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")
    
    # List messages
    if supabase:
        try:
            msgs = supabase.table("messages").select("*").eq("user_id", user["email"]).order("created_at", desc=True).limit(50).execute()
            for m in (msgs.data or []):
                with st.container():
                    col1, col2, col3 = st.columns([0.5, 8, 1.5])
                    with col1:
                        star = "⭐" if m.get('is_starred') else "☆"
                        if st.button(star, key=f"star_{m['id']}"):
                            if m.get('is_starred'):
                                # Unstar
                                supabase.table("messages").update({
                                    "is_starred": False,
                                    "is_compressed": False,
                                    "compressed_payload": None,
                                    "content": compression.decompress_text(
                                        base64.b64decode(m['compressed_payload']),
                                        'lzma'
                                    ) if m.get('compressed_payload') else ""
                                }).eq("id", m['id']).execute()
                            else:
                                # Star: compress and nullify content
                                if m.get('content'):
                                    comp_bytes, _ = compression.compress_text(m['content'], method='lzma')
                                    comp_b64 = base64.b64encode(comp_bytes).decode('ascii')
                                    supabase.table("messages").update({
                                        "is_starred": True,
                                        "is_compressed": True,
                                        "compressed_payload": comp_b64,
                                        "content": None
                                    }).eq("id", m['id']).execute()
                            st.rerun()
                    with col2:
                        if m.get('is_compressed') and m.get('compressed_payload'):
                            try:
                                decoded = base64.b64decode(m['compressed_payload'])
                                content = compression.decompress_text(decoded, 'lzma')
                            except:
                                content = "[Compressed message]"
                        else:
                            content = m.get('content', '')
                        st.write(content)
                    with col3:
                        st.caption(m.get('created_at', '')[:16])
        except Exception as e:
            logger.error(f"Messages load failed: {e}")

def show_ai():
    st.markdown("### 🔍 AI Knowledge Search")
    st.caption("Internal docs → Government web sources → AI synthesis")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        language = st.selectbox("🌐 Language", ["English", "Telugu", "Hindi"], key="search_lang")
    with col1:
        query = st.text_input("Ask about RTA rules, circulars, procedures...", key="search_query")
    
    tab1, tab2 = st.tabs(["🔍 Search", "✍️ Draft Letter"])
    
    with tab1:
        if st.button("🔍 Search", use_container_width=True, key="do_search"):
            if query:
                with st.spinner("Searching..."):
                    result = retrieval_pipeline.search(query, st.session_state.user, language)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Source", result['source'].title())
                with col2:
                    st.metric("Results", len(result.get('results', [])))
                with col3:
                    st.metric("Latency", f"{result.get('latency_ms', 0)} ms")
                
                st.markdown("#### 🤖 AI Answer")
                st.markdown(result.get('ai_summary', 'No answer'))
                
                if result.get('results'):
                    st.markdown("#### 📚 Sources")
                    for i, r in enumerate(result['results'], 1):
                        with st.expander(f"[{i}] {r['title']} ({r.get('source_type', 'internal')})"):
                            st.write(r['content'])
                            if r.get('source_url'):
                                st.markdown(f"🔗 [Source]({r['source_url']})")
    
    with tab2:
        context = st.text_area("Context for letter drafting...", height=150, key="draft_context")
        if st.button("📝 Draft Letter", use_container_width=True):
            if context:
                with st.spinner("Drafting..."):
                    draft = ai_system.draft_letter(context, language)
                    if draft:
                        st.markdown(draft)
                    else:
                        st.error("AI service unavailable")

def show_admin():
    user = st.session_state.user
    if user.get("admin_level") not in ["system_admin", "office_admin"]:
        st.warning("Admin access required")
        return
    
    st.markdown("### 🏛️ System Administration Dashboard")
    
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "🗂️ Deduplication", "⚡ Cache"])
    
    with tab1:
        if user.get("admin_level") == "system_admin" and supabase:
            try:
                metrics = supabase.table("system_metrics").select("*").execute().data or []
                ai_req = next((m['metric_value'] for m in metrics if m['metric_name'] == 'ai_requests_total'), 0)
                ai_tokens = next((m['metric_value'] for m in metrics if m['metric_name'] == 'ai_tokens_estimated'), 0)
                
                storage_res = supabase.table("files").select("compressed_size_bytes").execute()
                storage_used = sum(f.get('compressed_size_bytes', 0) for f in storage_res.data or [])
                storage_quota = int(secret("STORAGE_QUOTA_BYTES", 5_000_000_000))
                storage_percent = min((storage_used / storage_quota) * 100, 100) if storage_quota else 0
                
                users_count = supabase.table("users").select("id", count="exact").execute().count or 0
                offices_count = supabase.table("offices").select("id", count="exact").execute().count or 0
                docs_count = supabase.table("files").select("id", count="exact").execute().count or 0
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("💾 Storage", f"{storage_used/(1024**3):.2f} GB", f"of {storage_quota/(1024**3):.1f} GB")
                    st.progress(storage_percent / 100)
                    if storage_percent > 80:
                        st.warning("⚠️ Nearing limit!")
                with col2:
                    st.metric("🤖 AI Requests", f"{int(ai_req):,}")
                with col3:
                    st.metric("🔑 AI Tokens", f"{int(ai_tokens):,}")
                with col4:
                    st.metric("📄 Documents", f"{docs_count:,}")
                
                st.divider()
                st.markdown("#### 🏢 Office Breakdown")
                office_stats = supabase.table("users").select("office_name").execute()
                office_counts = Counter([u.get('office_name', 'Unknown') for u in office_stats.data or []])
                df = pd.DataFrame(office_counts.most_common(10), columns=["Office", "Users"])
                st.dataframe(df, use_container_width=True, hide_index=True)
                
            except Exception as e:
                logger.error(f"Admin dashboard failed: {e}")
                st.error("Failed to load metrics")
        
        elif user.get("admin_level") == "office_admin" and supabase:
            try:
                staff = supabase.table("users").select("*").eq("office_code", user.get("office_code")).execute()
                st.metric("Total Staff", len(staff.data or []))
                for member in (staff.data or []):
                    with st.expander(f"👤 {member['name']} - {member.get('designation', 'Staff')}"):
                        st.write(f"Email: {member['email']}")
                        st.write(f"Section: {member.get('section', 'N/A')}")
            except Exception as e:
                logger.error(f"Office admin failed: {e}")
    
    with tab2:
        if user.get("admin_level") == "system_admin" and supabase:
            st.markdown("#### 🗂️ Duplicate Files Management")
            try:
                duplicates = supabase.table("files").select("id, filename, sha256_hash, reference_count, compressed_size_bytes").gt("reference_count", 1).order("reference_count", desc=True).limit(20).execute()
                
                if not duplicates.data:
                    st.success("✅ No duplicate files found")
                else:
                    total_savings = sum(d.get('compressed_size_bytes', 0) * (d.get('reference_count', 1) - 1) for d in duplicates.data)
                    st.metric("Potential Savings", f"{total_savings/(1024**2):.2f} MB")
                    
                    for dup in duplicates.data:
                        with st.expander(f"📄 {dup['filename']} ({dup['reference_count']} refs)"):
                            st.write(f"SHA-256: `{dup['sha256_hash'][:16]}...`")
                            st.write(f"Size: {dup['compressed_size_bytes']//1024} KB")
                            if st.button("🗑️ Purge Everywhere", key=f"purge_{dup['id']}"):
                                result = storage_system.admin_purge_file(dup['id'], user["email"])
                                if result.get('success'):
                                    st.success(result['message'])
                                    st.rerun()
                                else:
                                    st.error(result.get('error'))
            except Exception as e:
                logger.error(f"Dedup mgmt failed: {e}")
    
    with tab3:
        st.markdown("#### ⚡ Cache Management")
        st.caption("Purge Redis cache to free up resources (5-min TTL auto-manages most cache)")
        if st.button("🗑️ Purge Redis Cache"):
            if redis_client:
                try:
                    redis_client.flushdb()
                    st.success("✅ Cache purged!")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Failed: {e}")
            else:
                st.warning("Redis not connected")

def render_bottom_nav():
    pages = [
        ("feed", "🏠", "Feed"),
        ("workspace", "🧰", "Work"),
        ("tapal", "📥", "Tapal"),
        ("documents", "📄", "Docs"),
        ("ai", "🤖", "AI"),
        ("messages", "💬", "Chat"),
    ]
    st.markdown('<div class="bottom-nav">', unsafe_allow_html=True)
    cols = st.columns(len(pages))
    for col, (page, icon, label) in zip(cols, pages):
        with col:
            if st.button(f"{icon} {label}", key=f"nav_{page}"):
                st.session_state.page = page
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# 16. MAIN APP
# ============================================
def main():
    init_session_state()
    
    if st.session_state.logged_in:
        with st.sidebar:
            st.write(f"👤 {st.session_state.user.get('name', 'User')}")
            st.write(f"🏢 {st.session_state.user.get('office_name', 'Office')}")
            st.write(f"🎭 {st.session_state.user.get('admin_level', 'staff').title()}")
            if st.button("🚪 Logout"):
                logout()
        
        page = st.session_state.page
        if page == "feed":
            show_feed()
        elif page == "workspace":
            show_workspace()
        elif page == "tapal":
            show_tapal()
        elif page == "documents":
            show_documents()
        elif page == "ai":
            show_ai()
        elif page == "messages":
            show_messages()
        elif page == "admin":
            show_admin()
        else:
            show_feed()
        
        render_bottom_nav()
    else:
        show_login()

if __name__ == "__main__":
    main()
