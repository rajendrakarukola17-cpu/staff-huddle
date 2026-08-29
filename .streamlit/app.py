import io
import secrets as pysecrets
from datetime import date, datetime, timedelta
from typing import Optional
import bcrypt
import pandas as pd
import streamlit as st
from supabase import create_client, Client
from streamlit_cookies_controller import CookieController

st.set_page_config(page_title="GovDocs AI — Government Workspace", page_icon="🏛️", layout="wide", initial_sidebar_state="expanded")

CUSTOM_CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{--navy-900:#16324F;--navy-800:#1E3A5F;--navy-700:#2C5282;--blue:#2563EB;--canvas:#F7F9FB;--surface:#FFF;--border:#E2E8F0;--border-strong:#CBD5E1;--text:#0F172A;--muted:#64748B;--green:#16A34A;--shadow:0 2px 10px rgba(15,23,42,.05);--shadow-md:0 8px 24px rgba(15,23,42,.08);--shadow-lg:0 18px 45px rgba(15,23,42,.12);--radius-lg:16px;--radius-md:12px;}
html,body,[class*="css"]{font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}
body{background:var(--canvas);} .stApp{background:var(--canvas);color:var(--text);}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1.35rem;padding-bottom:3rem;max-width:1500px;}
h1,h2,h3,h4{color:var(--text);font-weight:700;letter-spacing:-.025em;}
p,label,.stMarkdown{color:var(--text);} ::selection{background:#DBEAFE;}
section[data-testid="stSidebar"]{background:#FFF !important;border-right:1px solid var(--border) !important;}
section[data-testid="stSidebar"]>div:first-child{padding:1rem .8rem;}
section[data-testid="stSidebar"] .stRadio>div{gap:4px;}
section[data-testid="stSidebar"] .stRadio>div>label{border-radius:10px;padding:.62rem .75rem;margin:0;color:#334155;font-weight:500;transition:.15s ease;}
section[data-testid="stSidebar"] .stRadio>div>label:hover{background:#F1F5F9;}
section[data-testid="stSidebar"] .stRadio>div>label:has(div[aria-checked="true"]){background:#EAF2FF;color:var(--navy-800);font-weight:700;}
section[data-testid="stSidebar"] .stRadio>div>label p{color:inherit !important;}
.sidebar-brand{display:flex;align-items:center;gap:10px;padding:.45rem .35rem 1.1rem;border-bottom:1px solid var(--border);margin-bottom:1rem;}
.sidebar-logo{width:38px;height:38px;border-radius:10px;background:var(--navy-800);color:#fff;display:flex;align-items:center;justify-content:center;font-size:20px;}
.sidebar-brand-title{font-size:17px;font-weight:800;color:var(--navy-900);line-height:1.1;}
.sidebar-brand-sub{font-size:10px;color:var(--muted);margin-top:3px;}
.profile-card{background:#F8FAFC;border:1px solid var(--border);border-radius:12px;padding:12px;margin-bottom:12px;}
.profile-name{font-size:13px;font-weight:700;} .profile-email{font-size:10px;color:var(--muted);margin-top:3px;overflow:hidden;text-overflow:ellipsis;}
.profile-role{margin-top:9px;display:flex;align-items:center;justify-content:space-between;}
.app-topbar{display:flex;align-items:center;justify-content:space-between;background:#FFF;border:1px solid var(--border);border-radius:14px;padding:13px 18px;margin-bottom:18px;box-shadow:var(--shadow);}
.app-topbar-title{font-size:13px;font-weight:700;color:var(--navy-800);} .app-topbar-sub{font-size:11px;color:var(--muted);margin-top:2px;}
.page-header{margin-bottom:20px;} .page-header h1{margin:0;font-size:27px;} .page-header p{margin:5px 0 0;color:var(--muted);font-size:13px;}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);padding:18px;box-shadow:var(--shadow);}
.kpi-card{background:#FFF;border:1px solid var(--border);border-radius:14
