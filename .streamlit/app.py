import io, os, re, secrets, smtplib
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage
import bcrypt, pandas as pd, streamlit as st
from supabase import create_client
from streamlit_cookies_controller import CookieController

st.set_page_config(page_title='RTA Vizag Staff Huddle', page_icon='🧭', layout='wide')

CSS='''<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{--navy:#1E3A5F;--navy2:#2C5282;--indigo:#4F46A5;--bg:#F7F9FB;--line:#E2E8F0;--text:#172033;--muted:#64748B}
html,body,[class*="css"]{font-family:Inter,sans-serif}.stApp{background:radial-gradient(900px 500px at 100% -10%,#dfeaf7,transparent 60%),var(--bg)}
#MainMenu,header,footer{visibility:hidden}h1,h2,h3{color:var(--text);letter-spacing:-.025em}
.stButton>button{border-radius:11px!important;border:1px solid var(--line)!important;background:#fff!important;color:var(--navy)!important;font-weight:600!important}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,var(--navy2),var(--navy))!important;color:#fff!important;border:0!important}
.stTextInput input,.stTextArea textarea,.stSelectbox [data-baseweb="select"],.stNumberInput input,.stDateInput input{border-radius:11px!important;border-color:var(--line)!important;background:#fff!important}
section[data-testid="stSidebar"]{background:#fff!important;border-right:1px solid var(--line)}
section[data-testid="stSidebar"] .stRadio>div>label{padding:.55rem .75rem;border-radius:10px;margin-bottom:3px}
section[data-testid="stSidebar"] .stRadio>div>label:has(div[aria-checked="true"]){background:#EAF0F7;color:var(--navy);font-weight:700}
.header{background:linear-gradient(135deg,var(--navy),var(--navy2));color:#fff;padding:1.6rem 1.8rem;border-radius:18px;margin-bottom:1.2rem;box-shadow:0 18px 50px #0f172a18}.header h1{color:#fff;margin:0}.header p{color:#dbe7f4;margin:.35rem 0 0}
.card,.plan{background:#fff;border:1px solid var(--line);border-radius:18px;padding:1.1rem 1.2rem;box-shadow:0 8px 30px #0f172a0d;margin-bottom:.75rem}.title{font-weight:700;color:var(--text)}.sub{color:var(--muted);font-size:.82rem;margin-top:.3rem}
.kpi{background:#fff;border:1px solid var(--line);border-radius:16px;padding:1rem;box-shadow:0 8px 25px #0f172a0b}.kpi label{display:block;color:var(--muted);font-size:.7rem;font-weight:700;text-transform:uppercase}.kpi b{font-size:1.7rem;color:var(--text)}
.badge{display:inline-block;padding:4px 9px;border-radius:999px;font-size:11px;font-weight:700;background:#eef2f7;color:#475569}.basic{background:#ecfdf3;color:#087443}.pro{background:#eaf2ff;color:#1d5aa6}.max{background:#f0edff;color:#5143a4}.admin{background:#efe7ff;color:#5b21b6}
.chat-user{background:#eaf0f7;border:1px solid #d9e3ef;border-radius:16px 16px 4px 16px;padding:.85rem 1rem;margin:.4rem 0 .4rem 16%}.chat-ai{background:#fff;border:1px solid var(--line);border-radius:16px 16px 16px 4px;padding:.9rem 1rem;margin:.4rem 16% .4rem 0;box-shadow:0 8px 25px #0f172a0b}
.login{max-width:980px;margin:5vh auto;background:#fff;border:1px solid var(--line);border-radius:24px;overflow:hidden;box-shadow:0 25px 70px #0f172a20}.brand{background:linear-gradient(145deg,#142a46,var(--navy2));color:#fff;padding:2.5rem;min-height:450px}.brand h1{color:#fff;font-size:2rem}.brand p{color:#dbe7f4}.panel{padding:2rem}
</style>'''
st.markdown(CSS,unsafe_allow_html=True)

TIERS={'Basic':1,'Staff':1,'Pro':2,'Max':3,'Admin':4}; DAILY_AI_LIMIT=20; SESSION_DAYS=30; OTP_MIN=10
PROVIDERS={
 'gemini':('Google Gemini','gemini','gemini-2.5-flash',''),
 'qwen':('Alibaba Qwen / DashScope','openai','qwen-plus','https://dashscope-intl.aliyuncs.com/compatible-mode/v1'),
 'groq':('Groq','openai','llama-3.3-70b-versatile','https://api.groq.com/openai/v1'),
 'openai':('OpenAI','openai','gpt-5-mini','https://api.openai.com/v1'),
 'mistral':('Mistral','openai','mistral-small-latest','https://api.mistral.ai/v1'),
 'custom':('Custom OpenAI-compatible','openai','','')}

def secret(k,d=''):
 try:return st.secrets.get(k,d) or os.getenv(k,d)
 except:return os.getenv(k,d)
def now():return datetime.now(timezone.utc)
def iso():return now().isoformat()
def email_ok(x):return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$',x or ''))
def phone_ok(x):return 10<=len(re.sub(r'\D','',x or ''))<=15
def badge(t):return f'<span class="badge {t.lower()}">{t}</span>'
def access(a,r):return TIERS.get(a,0)>=TIERS.get(r,0)
def log_error(area,msg):
 try:supabase.table('error_log').insert({'area':area,'message':str(msg)[:4000],'occurred_at':iso()}).execute()
 except:pass

@st.cache_resource
def db():
 u=secret('SUPABASE_URL'); k=secret('SUPABASE_SERVICE_ROLE_KEY') or secret('SUPABASE_KEY')
 if not u or not k: st.error('Missing Supabase secrets.'); st.stop()
 return create_client(u,k)
supabase=db(); cookies=CookieController()

def setting(k,d=''):
 try:
  r=supabase.table('app_settings').select('value').eq('key',k).limit(1).execute(); return r.data[0]['value'] if r.data else d
 except:return d
def set_setting(k,v):
 try:
  r=supabase.table('app_settings').select('key').eq('key',k).limit(1).execute()
  if r.data:supabase.table('app_settings').update({'value':str(v),'updated_at':iso()}).eq('key',k).execute()
  else:supabase.table('app_settings').insert({'key':k,'value':str(v)}).execute()
  return True
 except Exception as e:log_error('setting',e);return False

def user(email):
 try:r=supabase.table('users').select('*').eq('email',email.strip().lower()).limit(1).execute();return r.data[0] if r.data else None
 except Exception as e:log_error('user',e);return None
def hp(p):return bcrypt.hashpw(p.encode(),bcrypt.gensalt()).decode()
def cp(p,h):
 try:return bcrypt.checkpw(p.encode(),h.encode())
 except:return False

def otp_send(identifier,channel):
 code=f'{secrets.randbelow(1000000):06d}'; h=hp(code)
 supabase.table('otp_verifications').insert({'identifier':identifier,'channel':channel,'purpose':'signup','code_hash':h,'expires_at':(now()+timedelta(minutes=OTP_MIN)).isoformat()}).execute()
 if channel=='email':
  host=secret('SMTP_HOST');port=int(secret('SMTP_PORT','587'));usr=secret('SMTP_USERNAME');pw=secret('SMTP_PASSWORD');sender=secret('SMTP_FROM') or usr
  if not all([host,usr,pw,sender]):return False,'SMTP email OTP is not configured.'
  try:
   m=EmailMessage();m['Subject']='Staff Huddle verification code';m['From']=sender;m['To']=identifier;m.set_content(f'Your Staff Huddle OTP is {code}. It expires in {OTP_MIN} minutes.')
   with smtplib.SMTP(host,port,timeout=20) as s:s.starttls();s.login(usr,pw);s.send_message(m)
   return True,''
  except Exception as e:log_error('smtp_otp',e);return False,str(e)
 sid=secret('TWILIO_ACCOUNT_SID');tok=secret('TWILIO_AUTH_TOKEN');frm=secret('TWILIO_FROM_NUMBER')
 if not all([sid,tok,frm]):return False,'SMS OTP is not configured. Use Email OTP or add Twilio secrets.'
 try:
  from twilio.rest import Client
  Client(sid,tok).messages.create(body=f'Staff Huddle OTP: {code}. Valid {OTP_MIN} minutes.',from_=frm,to=identifier);return True,''
 except Exception as e:log_error('sms_otp',e);return False,str(e)

def otp_verify(identifier,channel,code):
 try:
  r=supabase.table('otp_verifications').select('*').eq('identifier',identifier).eq('channel',channel).eq('purpose','signup').eq('verified',False).order('created_at',desc=True).limit(1).execute()
  if not r.data:return False,'Request a new OTP.'
  x=r.data[0]
  if datetime.fromisoformat(x['expires_at'].replace('Z','+00:00'))<now():return False,'OTP expired.'
  if int(x.get('attempts',0))>=5:return False,'Too many attempts. Request a new OTP.'
  supabase.table('otp_verifications').update({'attempts':int(x.get('attempts',0))+1}).eq('id',x['id']).execute()
  if not cp(code.strip(),x['code_hash']):return False,'Incorrect OTP.'
  supabase.table('otp_verifications').update({'verified':True}).eq('id',x['id']).execute();return True,''
 except Exception as e:log_error('otp_verify',e);return False,'OTP verification failed.'

def session(email):
 t=secrets.token_urlsafe(48);exp=now()+timedelta(days=SESSION_DAYS);supabase.table('sessions').insert({'token':t,'email':email,'expires_at':exp.isoformat()}).execute();return t
def session_user(t):
 if not t:return None
 try:
  r=supabase.table('sessions').select('*').eq('token',t).limit(1).execute()
  if not r.data:return None
  x=r.data[0]
  if datetime.fromisoformat(x['expires_at'].replace('Z','+00:00'))<now():return None
  u=user(x['email']);return u if u and u.get('active',True) else None
 except:return None

def sign_in(u):
 t=session(u['email']);cookies.set('huddle_session',t,max_age=SESSION_DAYS*86400);st.session_state.logged=True;st.session_state.user=u;st.rerun()

@st.cache_data(ttl=30)
def rows(table,order=None):
 try:
  q=supabase.table(table).select('*')
  if order:q=q.order(order,desc=True)
  return q.execute().data or []
 except Exception as e:log_error('fetch_'+table,e);return []
def ai_usage(email):
 try:r=supabase.table('ai_usage').select('count').eq('email',email).eq('day',date.today().isoformat()).limit(1).execute();return int(r.data[0]['count']) if r.data else 0
 except:return 0
def ai_inc(email):
 d=date.today().isoformat();r=supabase.table('ai_usage').select('*').eq('email',email).eq('day',d).limit(1).execute()
 if r.data:supabase.table('ai_usage').update({'count':int(r.data[0]['count'])+1}).eq('id',r.data[0]['id']).execute()
 else:supabase.table('ai_usage').insert({'email':email,'day':d,'count':1}).execute()

def ai_call(prompt,context):
 p=setting('ai_provider','gemini');name,kind,model,endpoint=PROVIDERS.get(p,PROVIDERS['gemini']);key=setting(p+'_api_key') or secret(p.upper()+'_API_KEY')
 if not key:return None,f'{name} API key is not configured.'
 try:
  if kind=='gemini':
   from google import genai
   from google.genai import types
   c=genai.Client(api_key=key);r=c.models.generate_content(model=model,contents=prompt,config=types.GenerateContentConfig(system_instruction=context,temperature=.15));return r.text,None
  from openai import OpenAI
  c=OpenAI(api_key=key,base_url=endpoint.rstrip('/'));r=c.chat.completions.create(model=model,messages=[{'role':'system','content':context},{'role':'user','content':prompt}],temperature=.15);return r.choices[0].message.content,None
 except Exception as e:log_error('ai_'+p,repr(e));return None,f'{name} error: {e}'

def circular_search(q,limit=5):
 try:return supabase.rpc('search_circular_chunks',{'q':q,'limit_count':limit}).execute().data or []
 except Exception as e:log_error('ai_search',e);return []

def header(t,s=''):st.markdown(f'<div class="header"><h1>{t}</h1><p>{s}</p></div>',unsafe_allow_html=True)

def login():
 st.markdown('<div class="login"><div class="brand">🧭<h1>RTA Vizag<br>Staff Huddle</h1><p>Departmental circulars, Tapal, AI rules assistance and staff tools.</p><p><b>Basic is free.</b> Verify your email or phone and start immediately.</p></div>',unsafe_allow_html=True)
 st.markdown('<div class="panel">',unsafe_allow_html=True)
 a,b=st.tabs(['🔐 Sign In','✨ Create Basic Account'])
 with a:
  e=st.text_input('Email');p=st.text_input('Password',type='password')
  if st.button('Sign In →',type='primary',use_container_width=True):
   u=user(e)
   if u and u.get('active',True) and cp(p,u['password_hash']):sign_in(u)
   else:st.error('Invalid email/password or inactive account.')
 with b:
  ch=st.radio('OTP channel',['Email OTP','Phone OTP'],horizontal=True);n=st.text_input('Full Name *');o=st.text_input('Office Name *');d=st.text_input('Designation *');ph=st.text_input('Phone *');em=st.text_input('Email *')
  ident=em.strip().lower() if ch=='Email OTP' else ph.strip();channel='email' if ch=='Email OTP' else 'phone'
  if st.button('Send OTP',use_container_width=True):
   if not n.strip() or not o.strip() or not d.strip() or not email_ok(em) or not phone_ok(ph):st.warning('Fill all fields correctly.')
   elif channel=='email' and user(em):st.warning('Email already has an account.')
   else:
    ok,err=otp_send(ident,channel);st.success('OTP sent.') if ok else st.error(err)
  code=st.text_input('OTP',max_chars=6)
  if st.button('Verify OTP',use_container_width=True):
   ok,err=otp_verify(ident,channel,code);st.session_state.signup_verified=ok;st.session_state.signup_ident=ident;st.success('Verified ✓') if ok else st.error(err)
  pw=st.text_input('Create Password *',type='password');pw2=st.text_input('Confirm Password *',type='password')
  if st.button('Create Basic Account →',type='primary',use_container_width=True):
   if not st.session_state.get('signup_verified') or st.session_state.get('signup_ident')!=ident:st.warning('Verify OTP first.')
   elif len(pw)<8 or pw!=pw2:st.warning('Password must be 8+ characters and match confirmation.')
   else:
    try:
     supabase.table('users').insert({'email':em.strip().lower(),'phone':ph.strip(),'name':n.strip(),'office_name':o.strip(),'designation':d.strip(),'password_hash':hp(pw),'tier':'Basic','active':True,'email_verified':channel=='email','phone_verified':channel=='phone','profile_complete':True}).execute();sign_in(user(em))
    except Exception as e:log_error('signup',e);st.error('Could not create account. The email may already exist.')
 st.markdown('</div></div>',unsafe_allow_html=True)

def sidebar(u):
 with st.sidebar:
  st.markdown(f'<div class="card"><div class="title">🧭 {u["name"]}</div><div class="sub">{u.get("office_name","")} · {u.get("designation","")}</div><br>{badge(u.get("tier","Basic"))}</div>',unsafe_allow_html=True)
  m=st.radio('Navigation',['🏠 Dashboard','📢 Circulars & G.O.s','🤖 AI Rules Assistant','📝 Templates','✉️ Tapal Register','📮 Dispatch Labels','📞 Staff Directory','💳 Plans & Access','⚙️ Admin Command Center'],label_visibility='collapsed')
  if st.button('🚪 Sign Out',use_container_width=True):
   try:supabase.table('sessions').delete().eq('email',u['email']).execute();cookies.remove('huddle_session')
   except:pass
   st.session_state.logged=False;st.session_state.user=None;st.rerun()
 return m

def app():
 u=user(st.session_state.user['email']);st.session_state.user=u
 m=sidebar(u);tier=u['tier']
 if m=='🏠 Dashboard':
  header(f'Good {"morning" if datetime.now().hour<12 else "afternoon" if datetime.now().hour<17 else "evening"}, {u["name"].split()[0]} 👋','Your departmental workspace at a glance.')
  cs=rows('circulars','doc_date');tp=rows('tapal_log','tapal_date');used=ai_usage(u['email']);month=date.today().strftime('%Y-%m');tp=[x for x in tp if str(x.get('tapal_date','')).startswith(month)]
  for c,l,v in zip(st.columns(4),['Circulars','Tapal this month','AI today','Plan'],[len(cs),len(tp),f'{used}/{DAILY_AI_LIMIT}',tier]):c.markdown(f'<div class="kpi"><label>{l}</label><b>{v}</b></div>',unsafe_allow_html=True)
  st.markdown('### Quick actions');q=st.columns(4)
  for c,x,y in zip(q,['📢 Circulars','🤖 Rules AI','✉️ Tapal','📮 Dispatch'],['Search G.O.s','Ask procedures','Record correspondence','Print labels']):c.markdown(f'<div class="card"><div class="title">{x}</div><div class="sub">{y}</div></div>',unsafe_allow_html=True)
 elif m=='📢 Circulars & G.O.s':
  header('Circulars, G.O.s & Memos','Search reference numbers, subjects and categories.');q=st.text_input('🔍 Search');cat=st.selectbox('Category',['All','Finance / HR','Operations','Confidential','Executive']);data=rows('circulars','doc_date');data=[x for x in data if cat=='All' or x.get('category')==cat];data=[x for x in data if not q.strip() or q.lower() in str(x).lower()]
  for x in data:
   st.markdown(f'<div class="card"><div>{badge(x.get("tier","Basic"))} &nbsp; <b>{x.get("ref_id")}</b></div><div class="title">{x.get("title")}</div><div class="sub">📅 {x.get("doc_date")} · 📁 {x.get("category")}</div></div>',unsafe_allow_html=True)
   if access(tier,x.get('tier','Basic')) and x.get('link'):st.link_button('📥 Open Document',x['link'])
   elif not access(tier,x.get('tier','Basic')):st.info(f'🔒 Requires {x.get("tier")} access.')
 elif m=='🤖 AI Rules Assistant':
  header('AI Rules Assistant','Circular-first answers. Provider is controlled by Admin > AI Gateway.');used=ai_usage(u['email']);st.metric('AI queries today',f'{used}/{DAILY_AI_LIMIT}');p=setting('ai_provider','gemini');st.caption(f'Active engine: {PROVIDERS.get(p,PROVIDERS["gemini"])[0]}')
  if 'messages' not in st.session_state:st.session_state.messages=[]
  for x in st.session_state.messages:st.markdown(f'<div class="{"chat-user" if x["role"]=="user" else "chat-ai"}">{x["content"]}</div>',unsafe_allow_html=True)
  if used<DAILY_AI_LIMIT or tier in ['Pro','Max','Admin']:
   q=st.chat_input('Ask about a rule or circular...')
   if q:
    st.session_state.messages.append({'role':'user','content':q});src=circular_search(q);context='You are an internal office rules assistant. Never invent G.O. numbers. Use the supplied circular excerpts first. If not found, say Not found in the uploaded circulars and give brief general guidance. Tell the user to confirm current orders.'+''.join(f'\n---{x.get("ref_id")} {x.get("title")}---\n{x.get("content","")}' for x in src);reply,err=ai_call(q,context);text=err or reply or 'Empty AI response.';st.session_state.messages.append({'role':'assistant','content':text});
    if not err:ai_inc(u['email'])
    else:log_error('ai_assistant',err)
    st.rerun()
  else:st.warning('Basic daily AI limit reached.')
  if st.button('Clear conversation'):st.session_state.messages=[];st.rerun()
 elif m=='📝 Templates':
  header('Templates','Approved reusable office formats.');
  for x in rows('templates'):
   st.markdown(f'<div class="card"><div class="title">📝 {x.get("title")}</div><div class="sub">{x.get("description","")} · {x.get("tier","Basic")}</div></div>',unsafe_allow_html=True)
   if access(tier,x.get('tier','Basic')) and x.get('link'):st.link_button('📥 Download',x['link'])
 elif m=='✉️ Tapal Register':
  header('Tapal Register','Record inward and outward correspondence.');a,b,c=st.tabs(['➕ New','📋 Browse','📊 Report'])
  with a:
   with st.form('tapal'):
    direction=st.selectbox('Direction',['Inward','Outward']);d=st.date_input('Date',date.today(),max_value=date.today());ft=st.text_input('From / To *');sub=st.text_input('Subject *');ref=st.text_input('Reference');rem=st.text_area('Remarks')
    if st.form_submit_button('Save',type='primary'):
     if not ft.strip() or not sub.strip():st.warning('From/To and Subject are required.')
     else:supabase.table('tapal_log').insert({'direction':direction,'tapal_date':d.isoformat(),'from_to':ft,'subject':sub,'file_ref':ref or None,'remarks':rem or None,'entered_by':u['email'],'entered_at':iso()}).execute();rows.clear();st.success('Saved.')
  with b:
   q=st.text_input('🔍 Search records');data=rows('tapal_log','tapal_date');
   for x in [x for x in data if not q or q.lower() in str(x).lower()]:st.markdown(f'<div class="card"><div class="title">{"📥" if x.get("direction")=="Inward" else "📤"} {x.get("subject")}</div><div class="sub">{x.get("from_to")} · {x.get("tapal_date")} · {x.get("file_ref","")}</div></div>',unsafe_allow_html=True)
  with c:st.info('Use the Browse tab for live records. Add CSV reporting here later if required.')
 elif m=='📮 Dispatch Labels':
  header('Dispatch Label Generator','OCR address and create a printable PDF.');photo=st.file_uploader('Address photo/scan',type=['png','jpg','jpeg']);ex=''
  if photo:
   try:
    import pytesseract;from PIL import Image,ImageOps
    img=ImageOps.exif_transpose(Image.open(photo)).convert('L');ex=pytesseract.image_to_string(img,config='--psm 6').strip();st.image(img,use_container_width=True)
   except Exception as e:st.warning(f'OCR unavailable: {e}')
  addr=st.text_area('Confirm address *',ex,height=120);copies=st.number_input('Copies',1,100,1)
  if st.button('🖨️ Generate Label PDF',type='primary') and addr.strip():
   try:
    from reportlab.pdfgen import canvas;from reportlab.lib.units import mm
    b=io.BytesIO();c=canvas.Canvas(b,pagesize=(220*mm,110*mm));lines=addr.splitlines()
    for _ in range(int(copies)):
     c.setFont('Helvetica-Bold',20);y=80*mm
     for line in lines:c.drawString(10*mm,y,line);y-=9*mm
     c.showPage()
    c.save();st.download_button('📥 Download PDF',b.getvalue(),'dispatch_labels.pdf','application/pdf')
   except Exception as e:log_error('dispatch',e);st.error(str(e))
 elif m=='📞 Staff Directory':
  header('Staff Directory','Find office contacts.');df=pd.DataFrame(rows('directory'));q=st.text_input('🔍 Search');
  if q and not df.empty:df=df[df.apply(lambda r:q.lower() in ' '.join(map(str,r.values)).lower(),axis=1)]
  st.dataframe(df,use_container_width=True,hide_index=True)
 elif m=='💳 Plans & Access':
  header('Plans & Access','Basic is permanently free. Elevated plans require admin approval.');
  for c,(n,p,features) in zip(st.columns(3),[('Basic','Free',['Basic circulars','Tapal','Directory','20 AI queries/day']),('Pro','₹199/month',['Priority AI','Pro documents','Advanced templates']),('Max','₹499/month',['Full archive','Advanced AI','Priority routing'])]):
   with c:
    st.markdown(f'<div class="plan"><h3>{n}</h3><h2>{p}</h2>'+''.join(f'✓ {z}<br>' for z in features)+'</div>',unsafe_allow_html=True)
    if n=='Basic':st.button('Current plan',disabled=True,key='pb')
    elif not access(tier,n) and st.button(f'Request {n}',key='req'+n):supabase.table('access_requests').insert({'user_id':u['id'],'email':u['email'],'requested_tier':n,'status':'pending'}).execute();st.success('Request sent.')
 elif m=='⚙️ Admin Command Center':
  if tier!='Admin':st.error('Admin access required.');return
  header('Admin Command Center','Users, documents, AI gateway and diagnostics.');s=st.radio('Admin',['👥 Users','📢 Publisher','🔧 AI Gateway','🩺 Health'],horizontal=True,label_visibility='collapsed')
  if s=='👥 Users':
   for x in supabase.table('users').select('*').order('created_at',desc=True).execute().data or []:
    with st.container(border=True):
     a,b,c=st.columns([2,1,1]);a.write(f"**{x['name']}** — {x['email']}\n{x.get('office_name','')}");nt=b.selectbox('Tier',['Basic','Pro','Max','Admin'],index=['Basic','Pro','Max','Admin'].index(x.get('tier','Basic')),key='tier'+x['id']);act=c.toggle('Active',value=x.get('active',True),key='act'+x['id']);
     if st.button('Save',key='save'+x['id']):supabase.table('users').update({'tier':nt,'active':act}).eq('id',x['id']).execute();st.rerun()
  elif s=='🔧 AI Gateway':
   p=st.selectbox('Provider',list(PROVIDERS),format_func=lambda x:PROVIDERS[x][0]);name,kind,default_model,default_endpoint=PROVIDERS[p];key=st.text_input('API key',setting(p+'_api_key') or secret(p.upper()+'_API_KEY'),type='password');model=st.text_input('Model',setting(p+'_model',default_model));endpoint=st.text_input('Base URL',setting(p+'_endpoint',default_endpoint),disabled=kind=='gemini');
   if st.button('Save gateway',type='primary'):
    set_setting('ai_provider',p);set_setting(p+'_api_key',key);set_setting(p+'_model',model);set_setting(p+'_endpoint',endpoint);st.success('Saved.')
   if st.button('🧪 Test provider'):
    r,e=ai_call('Reply exactly: AI gateway connection OK','You are a connection test. Reply exactly with the requested phrase.');st.error(e) if e else st.success(r)
  elif s=='🩺 Health':
   e=supabase.table('error_log').select('*').order('occurred_at',desc=True).limit(30).execute().data or [];a,b,c=st.columns(3);a.metric('Users',len(supabase.table('users').select('id').execute().data or []));b.metric('Circulars',len(supabase.table('circulars').select('id').execute().data or []));c.metric('Errors',len(e));
   for x in e:st.code(f"{x.get('area')} | {x.get('occurred_at')}\n{x.get('message')}")
  elif s=='📢 Publisher':st.info('Use the publisher implementation from the previous app or add the R2 upload/index workflow next. The schema below supports it.')

if 'logged' not in st.session_state:st.session_state.logged=False;st.session_state.user=None;st.session_state.messages=[]
if not st.session_state.logged:
 try:
  u=session_user(cookies.get('huddle_session'))
  if u:st.session_state.logged=True;st.session_state.user=u
 except:pass
if st.session_state.logged:app()
else:login()
