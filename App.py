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
    DOT_COLOR = "#60a5fa"
else:
    BG, TEKS, INPUT_BG, BORDER = "#ffffff", "#111827", "#f3f4f6", "#e5e7eb"
    DOT_COLOR = "#2563eb"

CSS = f"""
<style>
.stApp {{background-color: {BG}; color: {TEKS}}}
#MainMenu, footer, header {{visibility: hidden}}
.block-container {{padding-top: 2rem; padding-bottom: 150px}}

.suggest-btn {{
    background: {INPUT_BG}!important; border: 1px solid {BORDER}!important; 
    color: {TEKS}!important; border-radius: 16px!important; 
    padding: 18px!important; text-align: left!important; width: 100%!important;
    margin-bottom: 10px!important;
}}
.suggest-btn:hover {{filter: brightness(1.1)}}

/* ANIMASI 3 TITIK NAIK TURUN → SEGITIGA */
.loading-container {{
    display: flex; justify-content: center; align-items: center; 
    height: 50px; margin: 20px 0;
}}
.orion-loader {{
    position: relative; width: 60px; height: 60px;
}}
.orion-loader.dot {{
    position: absolute;
    width: 12px; height: 12px; background: {DOT_COLOR}; border-radius: 50%;
    animation: orionAnim 2.5s ease-in-out forwards;
}}
.orion-loader.dot1 {{left: 0; top: 24px; animation-delay: 0s;}}
.orion-loader.dot2 {{left: 24px; top: 24px; animation-delay: 0.1s;}}
.orion-loader.dot3 {{left: 48px; top: 24px; animation-delay: 0.2s;}}

@keyframes orionAnim {{
    0% {{transform: translateY(0px);}}
    20% {{transform: translateY(-15px);}} /* Naik */
    40% {{transform: translateY(15px);}} /* Turun */
    60% {{transform: translateY(-10px);}} /* Naik lagi */
    80% {{transform: translateY(10px);}} /* Turun lagi */
    100% {{ /* STOP DI SEGITIGA ORION */
        transform: translateY(0);
    }}
}}
.orion-loader.dot1 {{animation-name: toOrion1;}}
.orion-loader.dot2 {{animation-name: toOrion2;}}
.orion-loader.dot3 {{animation-name: toOrion3;}}

@keyframes toOrion1 {{
    0%, 80% {{transform: translate(0, 0);}}
    100% {{transform: translate(12px, -15px);}} /* Kiri atas */
}}
@keyframes toOrion2 {{
    0%, 80% {{transform: translate(0, 0);}}
    100% {{transform: translate(0, 15px);}} /* Bawah tengah */
}}
@keyframes toOrion3 {{
    0%, 80% {{transform: translate(0, 0);}}
    100% {{transform: translate(-12px, -15px);}} /* Kanan atas */
}}

/* INPUT BAR CUSTOM 1:1 KAYAK NSC */
.input-wrapper {{
    position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
    width: 90%; max-width: 700px; z-index: 999;
}}
.input-container {{
    background: {INPUT_BG}; border: 1px solid {BORDER}; border-radius: 25px; 
    padding: 8px 12px; display: flex; align-items: center; gap: 8px;
}}
.stFileUploader {{width: 32px!important;}}
.stFileUploader section {{padding: 0!important}}
.stFileUploader section > div {{display: none}}
.stFileUploader section button {{
    background: transparent!important; border: 1px solid {BORDER}!important; 
    border-radius: 50%!important; width: 32px!important; height: 32px!important;
    min-width: 32px!important; color: {TEKS}!important;
}}
.stFileUploader section button:before {{content: '+'; font-size: 20px;}}
.stTextInput {{flex: 1}}
.stTextInput input {{
    background: transparent!important; border: none!important; outline: none!important; 
    color: {TEKS}!important; font-size: 16px!important; box-shadow: none!important;
}}
.stButton button {{
    background: {DOT_COLOR}!important; border: none!important; border-radius: 50%!important; 
    width: 32px!important; height: 32px!important; min-width: 32px!important; color: white!important;
}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

def tts_teks(teks):
    try:
        teks_bersih = ''.join(c for c in teks if c.isalnum() or c.isspace())
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

# PROSES JAWABAN + LOADING ANIMASI
if st.session_state.chat and st.session_state.chat[-1]["role"] == "user":
    with st.chat_message("assistant", avatar="logo.png"):
        # ANIMASI 3 TITIK → SEGITIGA
        with st.container():
            st.markdown("""
            <div class="loading-container">
                <div class="orion-loader">
                    <div class="dot dot1"></div>
                    <div class="dot dot2"></div>
                    <div class="dot dot3"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
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
        
        time.sleep(2.6) # Tunggu animasi selesai
        st.session_state.chat.append({"role": "assistant", "content": jawab})
        st.session_state.count += 1
        st.rerun()

# INPUT BAR CUSTOM
st.markdown('<div class="input-wrapper">', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 10, 1])
    with col1:
        uploaded_file = st.file_uploader("", type=["png", "jpg", "jpeg"], label_visibility="collapsed", key="upload")
    with col2:
        prompt = st.text_input("Tanya Orion...", label_visibility="collapsed", key="input", placeholder="Tanya Orion...")
    with col3:
        submit = st.button("↑", key="send")
    st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

if submit and st.session_state.count < MAX_CHAT:
    if uploaded_file:
        st.session_state.chat.append({"role": "user", "content": uploaded_file})
    elif prompt:
        st.session_state.chat.append({"role": "user", "content": prompt})
    st.rerun()
elif submit:
    st.toast(f"Limit {MAX_CHAT} chat habis bro. Refresh ya")
