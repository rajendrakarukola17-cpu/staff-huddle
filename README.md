# 🏛️ RTA Connect - Production Deployment Guide

## 1. Database Setup
1. Go to Supabase Dashboard → SQL Editor.
2. Copy the entire contents of `schema.sql` and run it.
3. Enable Auth → Email confirmation (or disable for internal testing).

## 2. Storage Setup
1. Go to Supabase → Storage.
2. Create a bucket named `rta-documents`.
3. Set Bucket Policy to allow authenticated reads/writes.

## 3. Local Development
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
