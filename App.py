import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
from datetime import datetime
import pytz
import time
import requests
import io
import urllib.parse
import base64
import re

try:
    from gtts import gTTS
    TTS = True
except:
    TTS = False

st.set_page_config(page_title="Orion AI", page_icon="logo.png", layout="wide", initial_sidebar_state="collapsed")

try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("API Key belum diisi")
    st.stop()

# Session
if "messages" not in st.session_state: st.session_state.messages = []
if "chat_count" not in st.session_state: st.session_state.chat_count = 0
if "selected_model" not in st.session_state: st.session_state.selected_model = "gemini"
if "last_model" not in st.session_state: st.session_state.last_model = "gemini"

MAX_CHAT = 70
IS_DARK = not (6 <= datetime.now(pytz.timezone('Asia/Jakarta')).hour < 18)
T = {"bg": "#0A0B" if IS_DARK else "#FFFFFF", "chat_bg": "#18181B" if IS_DARK else "#F4F4F5", "text": "#E4E4E7" if IS_DARK else "#18181B", "border": "#3F3F46" if IS_DARK else "#D4D4D8", "icon": "#FFFFFF" if IS_DARK else "#000000"}

# CSS
st.markdown(f"""
<style>
#MainMenu,footer,header{{visibility:hidden}}
.stApp{{background:{T['bg']}}}
.block-container{{padding-top:70px!important;padding-bottom:180px!important;max-width:700px!important}}
.chat-counter{{position:fixed;top:15px;right:70px;background:{T['chat_bg']};border:1px solid {T['border']};border-radius:20px;padding:5px 12px;font-size:0.8rem;z-index:999}}
.meta-title{{font-size:2.2rem;font-weight:700;color:{T['text']};margin:20px 0 30px 0}}
.meta-btn{{width:100%;text-align:left;padding:16px 20px;margin-bottom:10px;background:{T['chat_bg']};border:1px solid {T['border']};border-radius:14px;color:{T['text']};font-size:1rem}}
.input-bar{{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);width:95%;max-width:700px;display:flex;gap:8px;align-items:center;z-index:9999}}
.input-bar button{{width:40px;height:40px;border-radius:50%;border:1px solid {T['border']};background:{T['chat_bg']};color:{T['icon']};font-size:20px}}
</style>
""", unsafe_allow_html=True)

# Header
try:
    with open("logo.png", "rb") as f:
        st.markdown(f'<div style="position:fixed;top:12px;right:15px;z-index:9999"><img src="data:image/png;base64,{base64.b64encode(f.read()).decode()}" width="32" style="border-radius:8px"></div>', unsafe_allow_html=True)
except: pass

sisa = MAX_CHAT - st.session_state.chat_count
if 0 < sisa <= 3:
    st.toast(f"waduh waktu ngobrol sisa {sisa} Kali lagi, nih siap-siap ya", icon="⚠️")

st.markdown(f'<div class="chat-counter">{st.session_state.chat_count}/({MAX_CHAT})</div>', unsafe_allow_html=True)

# AI Setup
genai.configure(api_key=GEMINI_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')
groq_client = Groq(api_key=GROQ_KEY)

def kirim_ke_ai(prompt):
    start = time.time()
    if "gambar" in prompt.lower() or "bikin" in prompt.lower():
        st.toast("maaf jika gambar kurang memuaskan🙏", icon="🎨")
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true"
        try:
            r = requests.get(url, timeout=55)
            if r.status_code == 200:
                return Image.open(io.BytesIO(r.content))
        except:
            pass
        return None

    try:
        if time.time() - start > 55:
            st.toast("aduh seperti nya sistemnya lagi capek,coba lagi nanti,atau refresh halaman ya☺️🙏", icon="😅")
            return "aduh seperti nya sistemnya lagi capek,coba lagi nanti,atau refresh halaman ya☺️🙏"

        if st.session_state.selected_model == "gemini":
            res = gemini_model.generate_content(prompt, request_options={"timeout": 55})
            return res.text
        else:
            chat = groq_client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile", timeout=55)
            return chat.choices[0].message.content
    except:
        st.toast("aduh seperti nya sistemnya lagi capek,coba lagi nanti,atau refresh halaman ya☺️🙏", icon="😅")
        return "aduh seperti nya sistemnya lagi capek,coba lagi nanti,atau refresh halaman ya☺️🙏"

# Sidebar
with st.sidebar:
    m = st.selectbox("Model", ["Gemini 2.5 Flash", "Llama 3.3 70B"], index=0 if st.session_state.selected_model == "gemini" else 1)
    new_model = "gemini" if "Gemini" in m else "groq"
    if new_model!= st.session_state.last_model:
        st.session_state.selected_model = new_model
        st.session_state.last_model = new_model
        st.toast(f"Pindah ke {m}", icon="🔄")
    if st.button("Hapus Chat"):
        st.session_state.messages = []
        st.session_state.chat_count = 0
        st.rerun()

# Opening
if not st.session_state.messages:
    st.markdown('<div class="meta-title">Ada yang bisa<br>Orion bantu?</div>', unsafe_allow_html=True)
    st.markdown('<button class="meta-btn">🖼️ Buat gambar</button>', unsafe_allow_html=True)
    st.markdown('<button class="meta-btn">💡 Bantu selesaikan masalah</button>', unsafe_allow_html=True)
    st.markdown('<button class="meta-btn">🎓 Belajar dan berkembang</button>', unsafe_allow_html=True)

# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["type"] == "image":
            st.image(msg["content"], use_container_width=True)
        else:
            st.write(msg["content"])

# INPUT BAR DENGAN TOMBOL
st.markdown('<div class="input-bar">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 1, 12])
with col1:
    upload = st.file_uploader("+", type=["jpg", "png"], label_visibility="collapsed", key="up")
with col2:
    audio = st.audio_input("🎤", label_visibility="collapsed", key=f"au_{st.session_state.chat_count}")
st.markdown('</div>', unsafe_allow_html=True)

# Handle upload
if upload and st.session_state.chat_count < MAX_CHAT:
    st.session_state.chat_count += 1
    img = Image.open(upload).convert("RGB")
    st.session_state.messages.append({"role": "user", "type": "image", "content": img})
    st.rerun()

# Handle audio
if audio and st.session_state.chat_count < MAX_CHAT:
    try:
        text = groq_client.audio.transcriptions.create(file=("a.wav", audio.getvalue()), model="whisper-large-v3", language="id").text
        if text:
            st.session_state.chat_count += 1
            st.session_state.messages.append({"role": "user", "type": "text", "content": text})
            reply = kirim_ke_ai(text)
            st.session_state.messages.append({"role": "assistant", "type": "text", "content": reply})
            st.rerun()
    except:
        pass

# Text input
prompt = st.chat_input("Tanya Orion...")
if prompt and st.session_state.chat_count < MAX_CHAT:
    st.session_state.chat_count += 1
    st.session_state.messages.append({"role": "user", "type": "text", "content": prompt})

    reply = kirim_ke_ai(prompt)
    if isinstance(reply, Image.Image):
        st.session_state.messages.append({"role": "assistant", "type": "image", "content": reply})
    else:
        st.session_state.messages.append({"role": "assistant", "type": "text", "content": reply})
    st.rerun()

st.markdown('<div style="position:fixed;bottom:5px;left:50%;transform:translateX(-50%);font-size:0.7rem;opacity:0.5">product of F.N.L</div>', unsafe_allow_html=True)
