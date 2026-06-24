import streamlit as st
import requests, os, base64, time
from datetime import datetime
from gtts import gTTS
import io
from PIL import Image

st.set_page_config(page_title="Orion AI", page_icon="logo.png", layout="centered")

KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

if "chat" not in st.session_state: st.session_state.chat = []
if "count" not in st.session_state: st.session_state.count = 0
MAX_CHAT = 70

# TEMA AUTO
jam = datetime.now().hour
THEME = "dark" if jam < 6 or jam >= 18 else "light"

if THEME == "dark":
    BG, TEKS, INPUT_BG, BORDER = "#0b0f19", "#e5e7eb", "#1f2937", "#374151"
else:
    BG, TEKS, INPUT_BG, BORDER = "#ffffff", "#111827", "#f3f4f6", "#e5e7eb"

CSS = f"""
<style>
.stApp {{background-color: {BG}; color: {TEKS}}}
.stChatInput {{display: none}}
#MainMenu, footer, header {{visibility: hidden}}
.suggest-btn {{
    background: {INPUT_BG}!important; border: 1px solid {BORDER}!important; 
    color: {TEKS}!important; border-radius: 16px!important; 
    padding: 18px!important; text-align: left!important; width: 100%!important;
    margin-bottom: 10px!important;
}}
.suggest-btn:hover {{filter: brightness(1.1)}}

/* LOADING 3 TITIK → SEGITIGA */
.loading-dots {{
    display: flex; justify-content: center; align-items: center; 
    height: 40px; gap: 8px;
}}
.dot {{
    width: 10px; height: 10px; background: #60a5fa; border-radius: 50%;
    animation: bounce 1.4s infinite ease-in-out both;
}}
.dot:nth-child(1) {{animation-delay: -0.32s}}
.dot:nth-child(2) {{animation-delay: -0.16s}}
@keyframes bounce {{
    0%, 80%, 100% {{transform: scale(0);}} 
    40% {{transform: scale(1.0);}}
}}
.triangle {{
    width: 0; height: 0;
    border-left: 8px solid transparent;
    border-right: 8px solid transparent;
    border-bottom: 14px solid #60a5fa;
    animation: fadeIn 0.3s;
}}
@keyframes fadeIn {{from {{opacity: 0}} to {{opacity: 1}}}}

/* INPUT CUSTOM KAYAK NSC */
.custom-input {{
    position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
    width: 90%; max-width: 700px; background: {INPUT_BG}; 
    border: 1px solid {BORDER}; border-radius: 25px; padding: 8px;
    display: flex; align-items: center; gap: 8px;
}}
.custom-input input {{
    flex: 1; background: transparent; border: none; outline: none; 
    color: {TEKS}; font-size: 16px;
}}
.icon-btn {{
    background: transparent; border: 1px solid {BORDER}; border-radius: 50%;
    width: 32px; height: 32px; cursor: pointer; color: {TEKS};
}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

def tts_teks(teks):
    try:
        teks_bersih = teks.replace('*', '').replace('#', '').replace('`', '').replace('_', '')
        tts = gTTS(text=teks_bersih, lang='id', slow=False)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return mp3_fp
    except: return None

def kirim_ke_gemini(pesan, gambar=None):
    parts = [{"text": pesan}]
    if gambar:
        img = Image.open(gambar)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode()
        parts.append({"inline_data": {"mime_type": "image/png", "data": img_b64}})
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={KEY}"
    data = {"contents": [{"parts": parts}]}
    r = requests.post(url, json=data, timeout=60)
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]

# HOME SCREEN
if not st.session_state.chat:
    col1, col2 = st.columns([1, 10])
    with col1: st.image("logo.png", width=50)
    with col2: st.markdown(f"<h1 style='color:{TEKS}; font-size: 32px; font-weight: 600;'>Ada yang bisa Orion bantu?</h1>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    
    if st.button("🖼️ Buat gambar", key="s1", use_container_width=True): 
        st.session_state.chat.append({"role": "user", "content": "Buatin gambar kucing astronot"}); st.rerun()
    if st.button("💡 Bantu selesaikan masalah", key="s2", use_container_width=True): 
        st.session_state.chat.append({"role": "user", "content": "Bantu aku selesaikan masalah ini"}); st.rerun()
    if st.button("🎓 Belajar dan berkembang", key="s3", use_container_width=True): 
        st.session_state.chat.append({"role": "user", "content": "Ajari aku sesuatu yang baru"}); st.rerun()

# TAMPILIN CHAT
for i, msg in enumerate(st.session_state.chat):
    with st.chat_message(msg["role"], avatar="logo.png" if msg["role"] == "assistant" else "👤"):
        if isinstance(msg["content"], str): st.markdown(msg["content"])
        else: st.image(msg["content"])
        if msg["role"] == "assistant" and isinstance(msg["content"], str):
            if st.button("🔊 Dengerin", key=f"tts_{i}"):
                audio = tts_teks(msg["content"])
                if audio: st.audio(audio, format="audio/mp3")

# INPUT CUSTOM + LOADING 3 TITIK → SEGITIGA
with st.container():
    st.markdown('<div style="height: 100px"></div>', unsafe_allow_html=True) # Spacer
    
    # LOADING ANIMATION
    if st.session_state.chat and st.session_state.chat[-1]["role"] == "user":
        with st.chat_message("assistant", avatar="logo.png"):
            loading_placeholder = st.empty()
            # 1. Titik naik turun 2 detik
            with loading_placeholder:
                st.markdown('<div class="loading-dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>', unsafe_allow_html=True)
            time.sleep(2)
            # 2. Berubah jadi segitiga
            with loading_placeholder:
                st.markdown('<div class="loading-dots"><div class="triangle"></div></div>', unsafe_allow_html=True)
            time.sleep(0.5)
            
            # PROSES JAWABAN
            pesan = st.session_state.chat[-1]["content"]
            gambar = None
            if not isinstance(pesan, str):
                gambar = pesan
                pesan = "Jelaskan isi foto ini"
            
            try:
                if any(k in str(pesan).lower() for k in ["gambar", "buatin", "lukis"]):
                    url = f"https://image.pollinations.ai/prompt/{pesan}"
                    jawab = f"![Hasil]({url})"
                else:
                    jawab = kirim_ke_gemini(pesan, gambar)
            except Exception as e:
                jawab = f"Error: {str(e)}"
            
            loading_placeholder.empty()
            st.session_state.chat.append({"role": "assistant", "content": jawab})
            st.session_state.count += 1
            st.rerun()

# INPUT BAR BAWAH - PAKE FORM BIAR GAK KOTAK UPLOAD MUNCUL
with st.form("input_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([1, 10, 1])
    with col1:
        uploaded_file = st.file_uploader("", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    with col2:
        prompt = st.text_input("Tanya Orion...", label_visibility="collapsed")
    with col3:
        submit = st.form_submit_button("↑")
    
    if submit and st.session_state.count < MAX_CHAT:
        if uploaded_file:
            st.session_state.chat.append({"role": "user", "content": uploaded_file})
        elif prompt:
            st.session_state.chat.append({"role": "user", "content": prompt})
        st.rerun()
    elif submit:
        st.error(f"Limit {MAX_CHAT} chat habis bro. Refresh ya")
