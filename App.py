import streamlit as st
from groq import Groq
from huggingface_hub import InferenceClient
from PIL import Image
import time, base64, io, uuid
from datetime import datetime
import fitz # PyMuPDF buat baca PDF
from duckduckgo_search import DDGS # Search internet gratis
from gtts import gTTS # Text to speech
from streamlit_mic_recorder import mic_recorder # Voice input
import speech_recognition as sr

# ==================== CONFIG & STYLE ====================
st.set_page_config(page_title="Fanilla AI Ultimate", page_icon="✨", layout="wide")
st.markdown("""<style>
    #MainMenu, footer, header {visibility: hidden;}
.main.block-container {padding-top: 0.5rem; max-width: 900px;}
.stChatInput > div {background-color: #374151; border-radius: 24px;}
.fanilla-title {background: linear-gradient(90deg, #A855F7, #EC4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.2rem; font-weight: 800; text-align: center;}
.custom-sidebar {background-color: #111827; border: 1px solid #374151; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;}
</style>""", unsafe_allow_html=True)

# ==================== INIT ====================
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
hf_client = InferenceClient(token=st.secrets.get("HF_TOKEN"))

# ==================== SEMUA FUNGSI FITUR BARU ====================
def baca_pdf(file):
    """FITUR 1: Baca PDF"""
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc: text += page.get_text()
        return text[:12000] # Limit biar ga kepanjangan
    except Exception as e:
        return f"Gagal baca PDF: {e}"

def search_internet(query):
    """FITUR 2: Search Real-time"""
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
        return "\n\n".join([f"Judul: {r['title']}\n{r['body']}\nSumber: {r['href']}" for r in results])
    except:
        return "Gagal search internet. Coba lagi nanti."

def text_to_speech(text):
    """FITUR 3: Voice Output"""
    try:
        tts = gTTS(text=text, lang='id')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except:
        return None

def voice_to_text(audio_bytes):
    """FITUR 3: Voice Input"""
    r = sr.Recognizer()
    try:
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio = r.record(source)
        return r.recognize_google(audio, language='id-ID')
    except:
        return None

# ==================== SISTEM MULTI CHAT V7.2 ====================
def buat_chat_baru():
    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {"title": "Obrolan Baru", "messages": [{"role": "assistant", "content": "Hai bro! Fanilla V8 nih. Bisa baca PDF, search internet, + ngomong. Mau coba apa? ✨", "type": "text"}], "created_at": datetime.now()}
    st.session_state.active_chat_id = chat_id
    st.session_state.show_sidebar = False

if "chats" not in st.session_state: st.session_state.chats = {}; buat_chat_baru()
if "show_sidebar" not in st.session_state: st.session_state.show_sidebar = False
if "mode" not in st.session_state: st.session_state.mode = "idle"

# ==================== UI SIDEBAR CUSTOM ====================
if st.button("☰ Menu & Fitur", use_container_width=True):
    st.session_state.show_sidebar = not st.session_state.show_sidebar
    st.rerun()

if st.session_state.show_sidebar:
    with st.container():
        st.markdown('<div class="custom-sidebar">', unsafe_allow_html=True)
        if st.button("📝 Obrolan Baru", use_container_width=True, type="primary"):
            buat_chat_baru(); st.rerun()

        st.markdown("**Template Cepat:**")
        if st.button("📄 Rangkum PDF", use_container_width=True):
            st.session_state.mode = "upload_pdf"; st.rerun()
        if st.button("🌐 Search Internet", use_container_width=True):
            st.session_state.mode = "search"; st.rerun()

        st.markdown("**List Obrolan:**")
        sorted_chats = sorted(st.session_state.chats.items(), key=lambda x: x[1]["created_at"], reverse=True)
        for chat_id, chat_data in sorted_chats:
            c1, c2 = st.columns([0.85, 0.15])
            with c1:
                if st.button(f"💬 {chat_data['title']}", key=f"chat_{chat_id}", use_container_width=True):
                    st.session_state.active_chat_id = chat_id; st.session_state.show_sidebar = False; st.rerun()
            with c2:
                if st.button("🗑️", key=f"del_{chat_id}"):
                    if len(st.session_state.chats) > 1: del st.session_state.chats[chat_id]
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ==================== LOGIKA UTAMA ====================
active_chat = st.session_state.chats[st.session_state.active_chat_id]
messages = active_chat["messages"]

st.markdown('<p class="fanilla-title">✨ Fanilla AI Ultimate</p>', unsafe_allow_html=True)

# Render chat
for msg in messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "audio":
            st.audio(msg["content"])
        elif msg.get("type") == "user_image":
            st.image(msg["content"], caption=msg.get("prompt"))
        else:
            st.markdown(msg["content"])

# Handle mode khusus
if st.session_state.mode == "upload_pdf":
    pdf_file = st.file_uploader("Upload PDF buat dirangkum", type="pdf")
    if pdf_file:
        with st.spinner("Baca PDF..."):
            text = baca_pdf(pdf_file)
            prompt = f"Tolong rangkum dokumen ini dengan bahasa santai:\n\n{text}"
            messages.append({"role": "user", "content": f"[Upload PDF: {pdf_file.name}]", "type": "text"})
            # Kirim ke AI
            stream = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}], stream=True)
            response = st.write_stream(stream)
            messages.append({"role": "assistant", "content": response, "type": "text"})
            st.session_state.mode = "idle"
            st.rerun()

elif st.session_state.mode == "search":
    query = st.text_input("Mau cari apa di internet?")
    if query:
        with st.spinner("Searching..."):
            hasil_search = search_internet(query)
            prompt = f"Jawab pertanyaan user: '{query}' berdasarkan hasil search ini:\n{hasil_search}\n\nJawab pake bahasa santai + kasih sumbernya."
            messages.append({"role": "user", "content": f"[Search: {query}]", "type": "text"})
            stream = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}], stream=True)
            response = st.write_stream(stream)
            messages.append({"role": "assistant", "content": response, "type": "text"})
            st.session_state.mode = "idle"
            st.rerun()

# Chat input utama
col1, col2 = st.columns([0.9, 0.1])
with col1:
    prompt = st.chat_input("Ketik pesan / upload gambar...", accept_file=True, file_type=["jpg", "png"])
with col2:
    audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='recorder')

if audio: # FITUR VOICE INPUT
    text = voice_to_text(audio['bytes'])
    if text: prompt = {"text": text}

if prompt:
    # Logic chat biasa + vision + /gambar kayak V7.2, tambahin aja
    user_text = prompt.get("text", "")
    messages.append({"role": "user", "content": user_text, "type": "text"})
    with st.chat_message("user"): st.markdown(user_text)

    with st.chat_message("assistant"):
        stream = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "m", "content": m["content"]} for m in messages if m["type"]=="text"], stream=True)
        response = st.write_stream(stream)
        messages.append({"role": "assistant", "content": response, "type": "text"})
        # FITUR VOICE OUTPUT
        audio_fp = text_to_speech(response[:500]) # Limit 500 karakter biar ga lama
        if audio_fp:
            st.audio(audio_fp)
            messages.append({"role": "assistant", "content": audio_fp, "type": "audio"})
    st.rerun()
