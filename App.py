import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
import requests, io, time, urllib.parse
from datetime import datetime
import pytz

st.set_page_config(page_title="Orion AI", layout="centered")
GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
GROQ_KEY = st.secrets["GROQ_API_KEY"]

if "msgs" not in st.session_state: st.session_state.msgs = []
if "count" not in st.session_state: st.session_state.count = 0
if "model" not in st.session_state: st.session_state.model = "gemini"

MAX = 70
now = datetime.now(pytz.timezone('Asia/Jakarta'))
IS_DARK = now.hour < 6 or now.hour >= 18
ICON = "#FFF" if IS_DARK else "#000"
BG = "#000" if IS_DARK else "#FFF"
INPUT = "#1C1C1E" if IS_DARK else "#F2F2F7"

# UI
st.markdown(f"""
<style>
.stApp{{background:{BG}}}
.block-container{{padding-top:60px;padding-bottom:160px;max-width:700px}}
.counter{{position:fixed;top:12px;right:20px;background:{INPUT};padding:5px 12px;border-radius:16px;font-size:13px;z-index:999;color:{ICON}}}
.title{{font-size:32px;font-weight:700;margin:60px 0 25px;color:{ICON}}}
.card{{background:{INPUT};border-radius:16px;padding:18px;margin-bottom:10px;color:{ICON}}}
.input-wrap{{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);width:94%;max-width:680px;background:{INPUT};border-radius:26px;height:52px;display:flex;align-items:center;padding:0 12px;gap:8px;z-index:9999}}
.input-wrap button{{width:34px;height:34px;border:none;background:transparent;color:{ICON};font-size:22px;border-radius:50%}}
.input-wrap input{{flex:1;background:transparent;border:none;outline:none;color:{ICON};font-size:16px}}
</style>
<div class="counter">{st.session_state.count}/({MAX})</div>
""", unsafe_allow_html=True)

if 0 < MAX - st.session_state.count <= 3:
    st.toast(f"waduh waktu ngobrol sisa {MAX - st.session_state.count} Kali lagi, nih siap-siap ya", icon="⚠️")

# AI
genai.configure(api_key=GEMINI_KEY)
gemini = genai.GenerativeModel('gemini-2.5-flash')
groq = Groq(api_key=GROQ_KEY)

def ask(p):
    if "gambar" in p.lower():
        st.toast("maaf jika gambar kurang memuaskan🙏", icon="🎨")
        try:
            r = requests.get(f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p)}", timeout=50)
            return Image.open(io.BytesIO(r.content))
        except: return None
    try:
        if st.session_state.model == "gemini":
            return gemini.generate_content(p, request_options={"timeout":50}).text
        else:
            return groq.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":p}], timeout=50).choices[0].message.content
    except:
        st.toast("aduh seperti nya sistemnya lagi capek,coba lagi nanti,atau refresh halaman ya☺️🙏", icon="😅")
        return "aduh seperti nya sistemnya lagi capek,coba lagi nanti,atau refresh halaman ya☺️🙏"

# Sidebar
with st.sidebar:
    m = st.selectbox("Model", ["Gemini","Groq"])
    new = "gemini" if m=="Gemini" else "groq"
    if new!= st.session_state.model:
        st.session_state.model = new
        st.toast(f"Pindah ke {m}", icon="🔄")

# Opening
if not st.session_state.msgs:
    st.markdown(f'<div class="title">Ada yang bisa<br>Orion bantu?</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">🖼️ Buat gambar</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">💡 Bantu selesaikan masalah</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">🎓 Belajar dan berkembang</div>', unsafe_allow_html=True)

# Chat
for m in st.session_state.msgs:
    with st.chat_message(m["r"]):
        if m["t"]=="i": st.image(m["c"], use_container_width=True)
        else: st.write(m["c"])

# INPUT CUSTOM DENGAN 2 TOMBOL DI DALEM
st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1,1,10])
with c1:
    up = st.file_uploader("", type=["jpg","png"], key="u", label_visibility="collapsed")
with c2:
    au = st.audio_input("", key=f"a{st.session_state.count}", label_visibility="collapsed")
with c3:
    txt = st.text_input("", placeholder="Tanya Orion...", key="t", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# Style tombol jadi + dan mic
st.markdown(f"""
<style>
[data-testid="stFileUploader"]{{width:34px!important}}
[data-testid="stFileUploader"] section{{padding:0!important;border:none!important;background:transparent!important}}
[data-testid="stFileUploader"] button{{width:34px!important;height:34px!important;min-height:34px!important;background:transparent!important;border:none!important;color:{ICON}!important;font-size:0!important}}
[data-testid="stFileUploader"] button::after{{content:"+";font-size:26px!important;position:absolute;top:-2px;left:7px}}
[data-testid="stAudioInput"]{{width:34px!important}}
[data-testid="stAudioInput"] button{{width:34px!important;height:34px!important;background:transparent!important;border:none!important;color:{ICON}!important}}
[data-testid="stTextInput"] input{{background:transparent!important;border:none!important;color:{ICON}!important}}
</style>
""", unsafe_allow_html=True)

# Handle
if up and st.session_state.count < MAX:
    st.session_state.count += 1
    st.session_state.msgs.append({"r":"user","t":"i","c":Image.open(up).convert("RGB")})
    st.rerun()

if au and st.session_state.count < MAX:
    try:
        t = groq.audio.transcriptions.create(file=("a.wav", au.getvalue()), model="whisper-large-v3", language="id").text
        if t:
            st.session_state.count += 1
            st.session_state.msgs.append({"r":"user","t":"t","c":t})
            a = ask(t)
            st.session_state.msgs.append({"r":"assistant","t":"i" if isinstance(a, Image.Image) else "t","c":a})
            st.rerun()
    except: pass

if txt and st.session_state.count < MAX:
    st.session_state.count += 1
    st.session_state.msgs.append({"r":"user","t":"t","c":txt})
    a = ask(txt)
    st.session_state.msgs.append({"r":"assistant","t":"i" if isinstance(a, Image.Image) else "t","c":a})
    st.rerun()
