import streamlit as st
import requests, os, base64, time, random
from datetime import datetime
from gtts import gTTS
import io
from PIL import Image
from streamlit_lottie import st_lottie
import json

st.set_page_config(page_title="Orion AI", page_icon="logo.png", layout="centered")

KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

# INIT STATE
if "chat" not in st.session_state:
    st.session_state.chat = []
if "count" not in st.session_state:
    st.session_state.count = 0
if "loading" not in st.session_state:
    st.session_state.loading = False

MAX_CHAT = 70

# TEMA AUTO SIANG/MALAM
jam = datetime.now().hour
THEME = "dark" if jam < 6 or jam >= 18 else "light"

if THEME == "dark":
    CSS = """
    <style>
    .stApp {background-color: #0b0f19; color: #e5e7eb}
    .stChatInput {background-color: #1f2937; border: 1px solid #374151}
    .suggest-btn {
        background: #1f2937!important; border: 1px solid #374151!important; 
        color: #e5e7eb!important; border-radius: 16px!important; 
        padding: 18px!important; text-align: left!important; width: 100%!important;
        margin-bottom: 10px!important;
    }
    .suggest-btn:hover {background: #374151!important}
    #MainMenu, footer, header {visibility: hidden;}
    </style>
    """
    TEKS_WARNA = "white"
else:
    CSS = """
    <style>
    .stApp {background-color: #ffffff; color: #111827}
    .stChatInput {background-color: #f3f4f6; border: 1px solid #e5e7eb}
    .suggest-btn {
        background: #ffffff!important; border: 1px solid #e5e7eb!important; 
        color: #111827!important; border-radius: 16px!important;
        padding: 18px!important; text-align: left!important; width: 100%!important;
        margin-bottom: 10px!important; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .suggest-btn:hover {background: #f9fafb!important}
    #MainMenu, footer, header {visibility: hidden;}
    </style>
    """
    TEKS_WARNA = "#111827"

st.markdown(CSS, unsafe_allow_html=True)

# LOADING RASI BINTANG - ANIMASI LOTTIE
def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200: return None
    return r.json()

# RASI BINTANG RANDOM - NANTI STOP DI ORION
RASI_URLS = [
    "https://lottie.host/4f9e4e1e-5c1a-4e1a-9e1a-4e1a5c1a4e1a/2y1Z2y1Z2y.json", # Big Dipper
    "https://lottie.host/5a0f5f2f-6d2b-5f2b-af2b-5f2b6d2b5f2b/3z2A3z2A3z.json", # Cassiopeia  
    "https://lottie.host/6b1g6g3g-7e3c-6g3c-bf3c-6g3c7e3c6g3c/4a3B4a3B4a.json", # Orion - INI YANG TERAKHIR
]
RASI_ORION = RASI_URLS[-1]

def encode_image(image_path):
    with open(image_path, "rb") as img:
        return base64.b64encode(img.read()).decode('utf-8')

def tts_teks(teks):
    try:
        teks_bersih = teks.replace('*', '').replace('#', '').replace('`', '').replace('_', '')
        tts = gTTS(text=teks_bersih, lang='id', slow=False)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return mp3_fp
    except:
        return None

def kirim_ke_gemini(pesan, gambar=None):
    parts = [{"text": pesan}]
    if gambar is not None:
        img = Image.open(gambar)
        img.save("temp.png")
        img_b64 = encode_image("temp.png")
        parts.append({"inline_data": {"mime_type": "image/png", "data": img_b64}})
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={KEY}"
    data = {"contents": [{"parts": parts}]}
    r = requests.post(url, json=data, timeout=60)
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]

# TAMPILAN HOME
if not st.session_state.chat:
    col1, col2 = st.columns([1, 10])
    with col1:
        st.image("logo.png", width=50)
    with col2:
        st.markdown(f"<h1 style='color:{TEKS_WARNA}; font-size: 32px; font-weight: 600;'>Ada yang bisa Orion bantu?</h1>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    
    if st.button("🖼️ Buat gambar", key="s1", use_container_width=True, type="secondary"):
        st.session_state.chat.append({"role": "user", "content": "Buatin gambar kucing astronot"})
        st.rerun()
    if st.button("💡 Bantu selesaikan masalah", key="s2", use_container_width=True, type="secondary"):
        st.session_state.chat.append({"role": "user", "content": "Bantu aku selesaikan masalah ini"})
        st.rerun()
    if st.button("🎓 Belajar dan berkembang", key="s3", use_container_width=True, type="secondary"):
        st.session_state.chat.append({"role": "user", "content": "Ajari aku sesuatu yang baru"})
        st.rerun()

# TAMPILIN CHAT
for i, msg in enumerate(st.session_state.chat):
    with st.chat_message(msg["role"], avatar="logo.png" if msg["role"] == "assistant" else "👤"):
        if isinstance(msg["content"], str):
            st.markdown(msg["content"])
        else:
            st.image(msg["content"])
        # TOMBOL TTS DI BAWAH TIAP JAWABAN BOT
        if msg["role"] == "assistant" and isinstance(msg["content"], str):
            if st.button("🔊 Dengerin", key=f"tts_{i}"):
                audio = tts_teks(msg["content"])
                if audio: st.audio(audio, format="audio/mp3")

# LOADING ANIMATION - GANTI-GANTI RASI TERUS STOP DI ORION
if st.session_state.loading:
    with st.chat_message("assistant", avatar="logo.png"):
        placeholder = st.empty()
        # Muter 2 detik ganti-ganti rasi
        for i in range(6):
            rasi = load_lottie_url(RASI_URLS[i % len(RASI_URLS)])
            with placeholder.container():
                if rasi: st_lottie(rasi, height=100, key=f"rasi_{i}")
            time.sleep(0.4)
        # STOP DI RASI ORION
        rasi_orion = load_lottie_url(RASI_ORION)
        with placeholder.container():
            if rasi_orion: st_lottie(rasi_orion, height=100, key="rasi_final")
            st.markdown("Orion lagi mikir...")
    st.session_state.loading = False

# INPUT CHAT
if prompt := st.chat_input("Tanya Orion..."):
    if st.session_state.count >= MAX_CHAT:
        st.error(f"Limit {MAX_CHAT} chat habis bro. Refresh ya")
    else:
        st.session_state.count += 1
        st.session_state.chat.append({"role": "user", "content": prompt})
        st.session_state.loading = True
        st.rerun()

# UPLOAD GAMBAR + MIC
uploaded_file = st.file_uploader("+", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
if uploaded_file:
    st.session_state.chat.append({"role": "user", "content": uploaded_file})
    st.session_state.loading = True
    st.rerun()

# PROSES JAWABAN SETELAH LOADING
if st.session_state.chat and st.session_state.chat[-1]["role"] == "user" and not st.session_state.loading:
    pesan = st.session_state.chat[-1]["content"]
    gambar = None
    
    if not isinstance(pesan, str):
        gambar = pesan
        pesan = "Jelaskan isi foto ini"
    
    if any(k in str(pesan).lower() for k in ["gambar", "buatin", "lukis"]):
        url = f"https://image.pollinations.ai/prompt/{pesan}"
        st.session_state.chat.append({"role": "assistant", "content": f"![Hasil]({url})"})
    else:
        try:
            jawab = kirim_ke_gemini(pesan, gambar)
            st.session_state.chat.append({"role": "assistant", "content": jawab})
        except Exception as e:
            st.session_state.chat.append({"role": "assistant", "content": f"Error: {str(e)}"})
    st.rerun()
