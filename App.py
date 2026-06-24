import streamlit as st
import requests, os, base64, time
from datetime import datetime
from gtts import gTTS
import io
from PIL import Image
import speech_recognition as sr
from streamlit_chat import message

st.set_page_config(page_title="Orion AI", page_icon="logo.png", layout="centered")

KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

if "chat" not in st.session_state: 
    st.session_state.chat = []
    st.session_state.first_chat = True # Buat ilangin opening
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
.block-container {{padding-top: 1rem; padding-bottom: 120px; max-width: 720px}}

/* HEADER ABU2 */
.header-abu {{color: {ABU}; font-size: 14px; margin-bottom: 8px;}}

/* TOMBOL SARAN */
.stButton button {{
    background: {INPUT_BG}!important; border: 1px solid {BORDER}!important; 
    color: {TEKS}!important; border-radius: 24px!important; 
    padding: 20px 24px!important; text-align: left!important; width: 100%!important;
    margin-bottom: 12px!important; font-size: 16px!important; font-weight: 500!important;
}}

/* BUBBLE CHAT KIRI-KANAN KAYAK META AI */
.stChatMessage {{background: transparent!important;}}
.stChatMessage[data-testid="chat-message-user"] {{
    flex-direction: row!important;
}}
.stChatMessage[data-testid="chat-message-assistant"] {{
    flex-direction: row-reverse!important;
}}
.stChatMessage > div[data-testid="stChatMessageContent"] {{
    background: {BUBBLE_USER}!important; color: {TEKS}!important; 
    border-radius: 20px!important; border-bottom-left-radius: 6px!important;
    padding: 14px 18px!important; max-width: 75%!important;
}}
.stChatMessage[data-testid="chat-message-assistant"] > div[data-testid="stChatMessageContent"] {{
    background: {BUBBLE_AI}!important; border: 1px solid {BORDER}!important;
    border-bottom-left-radius: 20px!important; border-bottom-right-radius: 6px!important;
}}
.stChatMessage.avatar {{background: transparent!important;}}

/* ANIMASI 3 TITIK → SEGITIGA */
.orion-loading {{
    display: flex; justify-content: flex-end; align-items: center; 
    height: 60px; width: 80px; margin: 10px 0; position: relative;
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

/* INPUT BAR - + DAN 🎤 DI DALEM KIRI */
[data-testid="stBottom"] {{background: {BG};}}
.stChatInputContainer {{
    background: {INPUT_BG}!important; border: 1px solid {BORDER}!important; 
    border-radius: 28px!important; padding: 8px 8px 14px!important;
}}
.stChatInputContainer textarea {{
    background: transparent!important; color: {TEKS}!important; 
    font-size: 16px!important;
}}

/* TOMBOL UPLOAD + MIC DI KIRI INPUT */
.upload-row {{
    position: fixed; bottom: 20px; left: calc(50% - 360px + 14px); 
    z-index: 1000; display: flex; gap: 8px;
}}
.upload-btn {{
    background: transparent!important; border: 1px solid {BORDER}!important; 
    border-radius: 50%!important; width: 36px!important; height: 36px!important;
    min-width: 36px!important; color: {TEKS}!important; font-size: 20px!important;
}}
[data-testid="stFileUploader"] {{width: 36px!important;}}
[data-testid="stFileUploader"] section {{padding: 0!important}}
[data-testid="stFileUploader"] section > div {{display: none}}
[data-testid="stFileUploader"] section button {{
    background: transparent!important; border: 1px solid {BORDER}!important; 
    border-radius: 50%!important; width: 36px!important; height: 36px!important;
    min-width: 36px!important; color: {TEKS}!important;
}}
[data-testid="stFileUploader"] section button:before {{content: '+'; font-size: 22px;}}
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

# HEADER + OPENING - ILANG PAS UDAH CHAT
if st.session_state.first_chat:
    st.markdown('<p class="header-abu">product of F.N.L</p>', unsafe_allow_html=True)
    st.markdown(f"<h1 style='color:{TEKS}; font-size: 32px; font-weight: 600; margin-top: 10px; margin-bottom: 30px;'>Ada yang bisa Orion bantu?</h1>", unsafe_allow_html=True)
    
    if st.button("🖼️ Buat gambar", use_container_width=True): 
        st.session_state.chat.append({"role": "user", "content": "Buatin gambar kucing astronot"})
        st.session_state.first_chat = False
        st.rerun()
    if st.button("💡 Bantu selesaikan masalah", use_container_width=True): 
        st.session_state.chat.append({"role": "user", "content": "Bantu aku selesaikan masalah ini"})
        st.session_state.first_chat = False
        st.rerun()
    if st.button("🎓 Belajar dan berkembang", use_container_width=True): 
        st.session_state.chat.append({"role": "user", "content": "Ajari aku sesuatu yang baru"})
        st.session_state.first_chat = False
        st.rerun()

# TAMPILIN CHAT PAKE streamlit-chat BIAR KIRI-KANAN
for i, msg in enumerate(st.session_state.chat):
    if msg["role"] == "user":
        if isinstance(msg["content"], str):
            message(msg["content"], is_user=True, key=f"user_{i}", avatar_style="personas")
        else:
            st.image(msg["content"], width=300)
    else:
        message(msg["content"], is_user=False, key=f"ai_{i}", logo=LOGO_B64)
        if isinstance(msg["content"], str):
            col1, col2 = st.columns([5, 1])
            with col2:
                if st.button("🔊 Dengerin", key=f"tts_{i}"):
                    audio = tts_teks(msg["content"])
                    if audio: st.audio(audio, format="audio/mp3")

# LOADING + PROSES
if st.session_state.chat and st.session_state.chat[-1]["role"] == "user":
    st.session_state.first_chat = False # ILANGIN OPENING
    with st.container():
        st.markdown('''
        <div class="orion-loading">
            <div class="orion-dot dot1"></div>
            <div class="orion-dot dot2"></div>
            <div class="orion-dot dot3"></div>
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

# INPUT BAR - TOMBOL + DAN 🎤 DI KIRI
col1, col2 = st.columns([1, 10])
with col1:
    uploaded_file = st.file_uploader("", type=["png", "jpg", "jpeg"], label_visibility="collapsed", key="upload")
    mic_file = st.file_uploader("", type=["wav", "mp3"], label_visibility="collapsed", key="mic")
    st.markdown('<button class="upload-btn">🎤</button>', unsafe_allow_html=True)

with col2:
    if prompt := st.chat_input("Tanya Orion..."):
        if st.session_state.count < MAX_CHAT:
            st.session_state.first_chat = False # ILANGIN OPENING
            st.session_state.chat.append({"role": "user", "content": prompt})
            st.rerun()
        else:
            st.toast(f"Limit {MAX_CHAT} chat habis bro. Refresh ya")

if uploaded_file:
    st.session_state.first_chat = False
    st.session_state.chat.append({"role": "user", "content": uploaded_file})
    st.rerun()

if mic_file:
    st.session_state.first_chat = False
    teks_mic = voice_to_text(mic_file)
    if teks_mic: 
        st.session_state.chat.append({"role": "user", "content": teks_mic})
        st.rerun()
