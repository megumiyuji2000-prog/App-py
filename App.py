import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
import requests, io, time, urllib.parse, base64
from datetime import datetime
import pytz

# CONFIG
st.set_page_config(page_title="Orion AI", page_icon="🤖", layout="centered")
GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
GROQ_KEY = st.secrets["GROQ_API_KEY"]

# STATE
if "msgs" not in st.session_state: st.session_state.msgs = []
if "count" not in st.session_state: st.session_state.count = 0
if "model" not in st.session_state: st.session_state.model = "gemini"

MAX = 70
IS_DARK = datetime.now(pytz.timezone('Asia/Jakarta')).hour < 6 or datetime.now(pytz.timezone('Asia/Jakarta')).hour >= 18

# STYLE SIMPLE
st.markdown(f"""
<style>
.stApp {{background:{'#0A0A0B' if IS_DARK else '#FFF'}}}
.block-container{{padding-top:60px;padding-bottom:120px;max-width:680px}}
.header{{position:fixed;top:0;left:0;right:0;height:55px;background:{'#0A0A0B' if IS_DARK else '#FFF'};border-bottom:2px solid {'#333' if IS_DARK else '#EEE'};z-index:999;display:flex;align-items:center;justify-content:space-between;padding:0 20px}}
.counter{{background:{'#222' if IS_DARK else '#F5F5F5'};padding:4px 12px;border-radius:20px;font-size:13px}}
.title{{font-size:32px;font-weight:700;margin:30px 0;line-height:1.2;color:{'#FFF' if IS_DARK else '#000'}}}
.card{{background:{'#18181B' if IS_DARK else '#F5F5F5'};border:1px solid {'#333' if IS_DARK else '#DDD'};border-radius:14px;padding:16px;margin-bottom:10px;cursor:pointer}}
.input-row{{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);width:95%;max-width:680px;display:flex;gap:8px}}
.input-row button{{width:44px;height:44px;border-radius:50%;border:1px solid {'#333' if IS_DARK else '#DDD'};background:{'#18181B' if IS_DARK else '#FFF'};font-size:20px}}
</style>
<div class="header">
  <div></div>
  <div class="counter">{st.session_state.count}/({MAX})</div>
</div>
""", unsafe_allow_html=True)

# NOTIF SISA 3
if 0 < MAX - st.session_state.count <= 3:
    st.toast(f"waduh waktu ngobrol sisa {MAX - st.session_state.count} Kali lagi, nih siap-siap ya", icon="⚠️")

# AI
genai.configure(api_key=GEMINI_KEY)
gemini = genai.GenerativeModel('gemini-2.5-flash')
groq = Groq(api_key=GROQ_KEY)

def ask(prompt, img=None):
    start = time.time()
    try:
        # Gambar
        if "gambar" in prompt.lower() or "bikin" in prompt.lower():
            st.toast("maaf jika gambar kurang memuaskan🙏", icon="🎨")
            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024"
            r = requests.get(url, timeout=50)
            return Image.open(io.BytesIO(r.content)) if r.status_code==200 else None

        # Timeout check
        if time.time()-start > 50:
            st.toast("aduh seperti nya sistemnya lagi capek,coba lagi nanti,atau refresh halaman ya☺️🙏", icon="😅")
            return "aduh seperti nya sistemnya lagi capek,coba lagi nanti,atau refresh halaman ya☺️🙏"

        if st.session_state.model == "gemini":
            content = [prompt, img] if img else [prompt]
            res = gemini.generate_content(content, request_options={"timeout": 50})
            return res.text
        else:
            res = groq.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}], timeout=50)
            return res.choices[0].message.content
    except:
        st.toast("aduh seperti nya sistemnya lagi capek,coba lagi nanti,atau refresh halaman ya☺️🙏", icon="😅")
        return "aduh seperti nya sistemnya lagi capek,coba lagi nanti,atau refresh halaman ya☺️🙏"

# SIDEBAR
with st.sidebar:
    m = st.selectbox("Model", ["Gemini", "Groq"], index=0 if st.session_state.model=="gemini" else 1)
    new = "gemini" if m=="Gemini" else "groq"
    if new!= st.session_state.model:
        st.session_state.model = new
        st.toast(f"Pindah ke {m}", icon="🔄")
    if st.button("Hapus chat"): st.session_state.msgs=[]; st.session_state.count=0; st.rerun()

# OPENING
if not st.session_state.msgs:
    st.markdown('<div class="title">Ada yang bisa<br>Orion bantu?</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">🖼️ Buat gambar</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">💡 Bantu selesaikan masalah</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">🎓 Belajar dan berkembang</div>', unsafe_allow_html=True)

# CHAT
for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        if m["type"]=="img": st.image(m["content"], use_container_width=True)
        else: st.write(m["content"])

# INPUT BAR - TOMBOL MUNCUL DI SINI
st.markdown('<div class="input-row">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1,1,10])
with c1:
    up = st.file_uploader("", type=["jpg","png"], label_visibility="collapsed", key="u")
    st.markdown('<style>[data-testid="stFileUploader"]{width:44px!important} [data-testid="stFileUploader"] button{width:44px!important;height:44px!important;border-radius:50%!important;font-size:24px!important;padding:0!important} [data-testid="stFileUploader"] button:after{content:"+";}</style>', unsafe_allow_html=True)
with c2:
    au = st.audio_input("", label_visibility="collapsed", key=f"a{st.session_state.count}")
    st.markdown('<style>[data-testid="stAudioInput"]{width:44px!important} [data-testid="stAudioInput"] button{width:44px!important;height:44px!important;border-radius:50%!important;font-size:16px!important}</style>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# HANDLE UPLOAD
if up and st.session_state.count < MAX:
    st.session_state.count += 1
    img = Image.open(up).convert("RGB")
    st.session_state.msgs.append({"role":"user","type":"img","content":img})
    st.rerun()

# HANDLE AUDIO
if au and st.session_state.count < MAX:
    try:
        txt = groq.audio.transcriptions.create(file=("a.wav", au.getvalue()), model="whisper-large-v3", language="id").text
        if txt:
            st.session_state.count += 1
            st.session_state.msgs.append({"role":"user","type":"text","content":txt})
            ans = ask(txt)
            st.session_state.msgs.append({"role":"assistant","type":"text","content":ans})
            st.rerun()
    except: pass

# TEXT INPUT
prompt = st.chat_input("Tanya Orion...")
if prompt and st.session_state.count < MAX:
    st.session_state.count += 1
    st.session_state.msgs.append({"role":"user","type":"text","content":prompt})
    ans = ask(prompt)
    if isinstance(ans, Image.Image):
        st.session_state.msgs.append({"role":"assistant","type":"img","content":ans})
    else:
        st.session_state.msgs.append({"role":"assistant","type":"text","content":ans})
    st.rerun()

st.markdown('<div style="text-align:center;opacity:0.4;font-size:12px;margin-top:20px">product of F.N.L</div>', unsafe_allow_html=True)
