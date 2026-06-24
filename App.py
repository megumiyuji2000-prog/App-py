import streamlit as st
import requests, os, base64, time
from datetime import datetime
from gtts import gTTS
import io
from PIL import Image
import speech_recognition as sr
from pydub import AudioSegment

st.set_page_config(page_title="Orion AI", page_icon="logo.png", layout="centered")

KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

if "chat" not in st.session_state: st.session_state.chat = []
if "count" not in st.session_state: st.session_state.count = 0
MAX_CHAT = 70

# TEMA AUTO
jam = datetime.now().hour
THEME = "dark" if jam < 6 or jam >= 18 else "light"

if THEME == "dark":
    BG, TEKS, INPUT_BG, BORDER, DOT, ABU, BUBBLE_USER, BUBBLE_AI = "#0b0f19", "#e5e7eb", "#1f2937", "#374151", "#60a5fa", "#9ca3af", "#374151", "#1f2937"
else:
    BG, TEKS, INPUT_BG, BORDER, DOT, ABU, BUBBLE_USER, BUBBLE_AI = "#ffffff", "#111827", "#f3f4f6", "#e5e7eb", "#2563eb", "#6b7280", "#e5e7eb", "#f9fafb"

CSS = f"""
<style>
.stApp {{background-color: {BG}; color: {TEKS}}}
#MainMenu, footer, header {{visibility: hidden}}
.block-container {{padding-top: 1rem; padding-bottom: 150px; max-width: 720px}}

/* HEADER ABU2 */
.header-abu {{color: {ABU}; font-size: 14px; margin-bottom: 8px;}}

/* TOMBOL SARAN */
.stButton button {{
    background: {INPUT_BG}!important; border: 1px solid {BORDER}!important; 
    color: {TEKS}!important; border-radius: 20px!important; 
    padding: 18px 20px!important; text-align: left!important; width: 100%!important;
    margin-bottom: 12px!important; font-size: 16px!important;
}}

/* BUBBLE CHAT CUSTOM - USER KIRI, ORION KANAN */
.chat-row {{width: 100%; display: flex; margin-bottom: 16px;}}
.user-row {{justify-content: flex-start;}}
.ai-row {{justify-content: flex-end;}}
.chat-bubble {{
    max-width: 75%; padding: 12px 16px; border-radius: 18px;
    word-wrap: break-word; font-size: 16px; line-height: 1.5;
}}
.user-bubble {{background: {BUBBLE_USER}; color: {TEKS}; border-bottom-left-radius: 4px;}}
.ai-bubble {{background: {BUBBLE_AI}; color: {TEKS}; border-bottom-right-radius: 4px; border: 1px solid {BORDER};}}
.ai-header {{display: flex; align-items: center; gap: 8px; margin-bottom: 6px;}}
.ai-header img {{width: 24px; height: 24px;}}
.dengerin-btn {{
    background: {INPUT_BG}; border: 1px solid {BORDER}; border-radius: 16px;
    padding: 6px 12px; font-size: 14px; margin-top: 8px; cursor: pointer;
    display: inline-flex; align-items: center; gap: 6px; color: {TEKS};
}}

/* ANIMASI 3 TITIK → SEGITIGA ORION */
.orion-loading {{
    display: flex; justify-content: flex-end; align-items: center; 
    height: 60px; width: 80px; margin: 10px 0;
}}
.orion-dot {{
    position: absolute; width: 12px; height: 12px; background: {DOT}; border-radius: 50%;
}}
.dot1 {{animation: toOrion1 2.5s ease-in-out forwards;}}
.dot2 {{animation: toOrion2 2.5s ease-in-out forwards;}}
.dot3 {{animation: toOrion3 2.5s ease-in-out forwards;}}

@keyframes toOrion1 {{
    0% {{transform: translate(0px, 0px);}}
    20% {{transform: translate(0px, -15px);}}
    40% {{transform: translate(0px, 15px);}}
    60% {{transform: translate(0px, -10px);}}
    80% {{transform: translate(0px, 10px);}}
    100% {{transform: translate(-15px, -12px);}}
}}
@keyframes toOrion2 {{
    0% {{transform: translate(0px, 0px);}}
    20% {{transform: translate(0px, 15px);}}
    40% {{transform: translate(0px, -15px);}}
    60% {{transform: translate(0px, 10px);}}
    80% {{transform: translate(0px, -10px);}}
    100% {{transform: translate(0px, 15px);}}
}}
@keyframes toOrion3 {{
    0% {{transform: translate(0px, 0px);}}
    20% {{transform: translate(0px, -10px);}}
    40% {{transform: translate(0px, 10px);}}
    60% {{transform: translate(0px, -15px);}}
    80% {{transform: translate(0px, 15px);}}
    100% {{transform: translate(15px, -12px);}}
}}

/* INPUT BAR FIX */
.stChatInput {{display: none}}
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

def voice_to_text(audio_file):
    try:
        r = sr.Recognizer()
        with sr.AudioFile(audio_file) as source: audio = r.record(source)
        return r.recognize_google(audio, language='id-ID')
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

def get_base64_logo():
    try:
        with open("logo.png", "rb") as f: return base64.b64encode(f.read()).decode()
    except: return ""

LOGO_B64 = get_base64_logo()

# HEADER
st.markdown('<p class="header-abu">product of F.N.L</p>', unsafe_allow_html=True)

# HOME SCREEN
if not st.session_state.chat:
    st.markdown(f"<h1 style='color:{TEKS}; font-size: 32px; font-weight: 600; margin-top: 10px;'>Ada yang bisa Orion bantu?</h1>", unsafe_allow_html=True)
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    
    if st.button("🖼️ Buat gambar", use_container_width=True): 
        st.session_state.chat.append({"role": "user", "content": "Buatin gambar kucing astronot"}); st.rerun()
    if st.button("💡 Bantu selesaikan masalah", use_container_width=True): 
        st.session_state.chat.append({"role": "user", "content": "Bantu aku selesaikan masalah ini"}); st.rerun()
    if st.button("🎓 Belajar dan berkembang", use_container_width=True): 
        st.session_state.chat.append({"role": "user", "content": "Ajari aku sesuatu yang baru"}); st.rerun()

# TAMPILIN CHAT BUBBLE CUSTOM KIRI-KANAN
for i, msg in enumerate(st.session_state.chat):
    if msg["role"] == "user":
        if isinstance(msg["content"], str):
            st.markdown(f'''
            <div class="chat-row user-row">
                <div class="chat-bubble user-bubble">{msg["content"]}</div>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown('<div class="chat-row user-row">', unsafe_allow_html=True)
            st.image(msg["content"], width=300)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'''
        <div class="chat-row ai-row">
            <div class="chat-bubble ai-bubble">
                <div class="ai-header">
                    <img src="data:image/png;base64,{LOGO_B64}">
                </div>
                {msg["content"]}
            </div>
        </div>
        ''', unsafe_allow_html=True)
        if isinstance(msg["content"], str):
            if st.button("🔊 Dengerin", key=f"tts_{i}"):
                audio = tts_teks(msg["content"])
                if audio: st.audio(audio, format="audio/mp3")

# PROSES JAWABAN + LOADING
if st.session_state.chat and st.session_state.chat[-1]["role"] == "user":
    st.markdown('''
    <div class="chat-row ai-row">
        <div class="orion-loading">
            <div class="orion-dot dot1"></div>
            <div class="orion-dot dot2"></div>
            <div class="orion-dot dot3"></div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
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
    
    time.sleep(2.6)
    st.session_state.chat.append({"role": "assistant", "content": jawab})
    st.session_state.count += 1
    st.rerun()

# INPUT BAR
uploaded_file = st.file_uploader("Upload", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
mic_file = st.file_uploader("Mic", type=["wav", "mp3"], label_visibility="collapsed")

if prompt := st.chat_input("Tanya Orion..."):
    if st.session_state.count < MAX_CHAT:
        st.session_state.chat.append({"role": "user", "content": prompt})
        st.rerun()
    else:
        st.toast(f"Limit {MAX_CHAT} chat habis bro. Refresh ya")

if uploaded_file:
    st.session_state.chat.append({"role": "user", "content": uploaded_file})
    st.rerun()

if mic_file:
    teks_mic = voice_to_text(mic_file)
    if teks_mic: 
        st.session_state.chat.append({"role": "user", "content": teks_mic})
        st.rerun()
