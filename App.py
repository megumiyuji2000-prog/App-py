import streamlit as st
from groq import Groq
from huggingface_hub import InferenceClient
from PIL import Image
import time, base64, io, uuid
from datetime import datetime
import pytz
from duckduckgo_search import DDGS
from googlesearch import search as google_search
import requests
from bs4 import BeautifulSoup

# ==================== GEMINI STYLE ====================
st.set_page_config(page_title="Fanilla AI", page_icon="✨", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Google Sans', sans-serif;
}

#MainMenu, footer, header {visibility: hidden;}

/* Background Gemini style */
.main {
    background-color: #131314;
}

/* Container tengah kayak Gemini */
.block-container {
    padding-top: 2rem!important;
    padding-bottom: 8rem!important;
    max-width: 768px!important;
}

/* Logo + Judul Center */
.gemini-header {
    text-align: center;
    margin-bottom: 2rem;
    margin-top: 4rem;
}
.gemini-title {
    background: linear-gradient(90deg, #8B5CF6, #EC4899, #3B82F6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3.5rem;
    font-weight: 500;
    letter-spacing: -2px;
}
.gemini-subtitle {
    color: #9AA0A6;
    font-size: 1.2rem;
    margin-top: 0.5rem;
}

/* Chat bubbles Gemini style */
.stChatMessage {
    background-color: transparent!important;
    padding: 1rem 0!important;
}
[data-testid="stChatMessageContent"] {
    background-color: #1E1F20!important;
    border-radius: 20px!important;
    padding: 1rem 1.25rem!important;
    color: #E3E3E3!important;
    line-height: 1.6;
}
.stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"] {
    background-color: #303134!important;
}

/* Input bar Gemini - nempel bawah */
.stChatInput {
    position: fixed!important;
    bottom: 0!important;
    left: 0!important;
    right: 0!important;
    background: linear-gradient(180deg, rgba(19,19,20,0) 0%, #131314 30%)!important;
    padding: 2rem 0 1.5rem 0!important;
    max-width: 768px!important;
    margin: 0 auto!important;
}
.stChatInput > div {
    background-color: #1E1F20!important;
    border: 1px solid #3C4043!important;
    border-radius: 28px!important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.3)!important;
}
.stChatInput input {
    color: #E3E3E3!important;
}
.stChatInput button {
    background-color: transparent!important;
}

/* Sidebar Gemini style */
[data-testid="stSidebar"] {
    background-color: #1E1F20;
    border-right: 1px solid #3C4043;
}
.sidebar-btn {
    background-color: #303134!important;
    color: #E3E3E3!important;
    border: none!important;
    border-radius: 12px!important;
    padding: 0.75rem!important;
    margin-bottom: 0.5rem!important;
    text-align: left!important;
}
.sidebar-btn:hover {
    background-color: #3C4043!important;
}

/* Suggestions cards */
.suggestion-card {
    background-color: #1E1F20;
    border: 1px solid #3C4043;
    border-radius: 16px;
    padding: 1rem;
    cursor: pointer;
    transition: all 0.2s;
}
.suggestion-card:hover {
    background-color: #303134;
    border-color: #8B5CF6;
}

/* Image style */
.stImage img {
    border-radius: 16px!important;
    border: 1px solid #3C4043;
}

/* Toast style */
.stToast {
    background-color: #1E1F20!important;
    border: 1px solid #3C4043!important;
}
</style>
""", unsafe_allow_html=True)

# ==================== INIT ====================
try:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    hf_client = InferenceClient(token=st.secrets.get("HF_TOKEN"))
except Exception as e:
    st.error(f"API Key error: {e}")
    st.stop()

# ==================== STATE ====================
def buat_chat_baru():
    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {
        "title": "Obrolan Baru",
        "messages": [],
        "created_at": datetime.now()
    }
    st.session_state.active_chat_id = chat_id

if "chats" not in st.session_state:
    st.session_state.chats = {}
    buat_chat_baru()

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = list(st.session_state.chats.keys())[0]
if "processing" not in st.session_state:
    st.session_state.processing = False

# ==================== FITUR CORE ====================
def stream_with_timeout(stream, timeout=15):
    start_time = time.time()
    full_response = ""
    for chunk in stream:
        if time.time() - start_time > timeout:
            raise TimeoutError("Timeout >15 detik")
        if chunk.choices[0].delta.content:
            full_response += chunk.choices[0].delta.content
            yield full_response
    yield full_response

def search_internet(query):
    hasil_final = []
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3, region="id-id")]
            if results:
                for r in results:
                    hasil_final.append(f"Sumber: {r['href']}\n{r['body']}")
                return "\n\n".join(hasil_final)
    except:
        pass
    try:
        for url in google_search(query, num_results=3, lang="id"):
            hasil_final.append(f"Sumber: {url}")
        if hasil_final:
            return "\n\n".join(hasil_final)
    except:
        pass
    return "Search error."

def chat_ai(messages):
    """1. CHAT + SEARCH"""
    try:
        user_terakhir = messages[-1]["content"].lower()
        keyword_realtime = ["hari ini", "terbaru", "sekarang", "harga", "kurs", "berita", "cuaca", "siapa", "kapan", "skor", "update", "2024", "2025", "2026"]
        perlu_search = any(kata in user_terakhir for kata in keyword_realtime)

        if perlu_search:
            with st.spinner("🔍 Searching..."):
                hasil_search = search_internet(messages[-1]["content"])
                messages[-1]["content"] += f"\n\n[INFO TERBARU]:\n{hasil_search}"

        tz = pytz.timezone('Asia/Jakarta')
        tanggal = datetime.now(tz).strftime("%A, %d %B %Y")
        system_prompt = {
            "role": "system",
            "content": f"Kamu Fanilla AI dari FNL. Hari ini {tanggal}. Tahun 2026. Jawab santai pake 'bro'. Singkat padat."
        }

        history = [system_prompt] + [{"role": m["role"], "content": m["content"]} for m in messages if m.get("type") == "text"]
        stream = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=history,
            stream=True,
            timeout=15
        )
        return stream_with_timeout(stream, timeout=15)
    except Exception as e:
        st.error(f"Error: {e}")
        return None

def chat_vision(image, prompt):
    """2. LIAT GAMBAR"""
    try:
        content_list = [{"type": "text", "text": f"Lo Fanilla AI. User upload gambar. Pertanyaan: {prompt}. Jawab 'bro', rating 1-10 kalo logo. Max 3 kalimat."}]

        image.thumbnail((512, 512))
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=70)
        base64_image = base64.b64encode(buffered.getvalue()).decode()
        content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}})

        messages = [{"role": "user", "content": content_list}]
        stream = groq_client.chat.completions.create(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            messages=messages,
            stream=True,
            timeout=15,
            max_tokens=150
        )
        return stream_with_timeout(stream, timeout=15)
    except Exception as e:
        st.error(f"GAGAL VISION: {str(e)}")
        return None

def generate_image(prompt):
    """3. BUAT GAMBAR"""
    if not st.secrets.get("HF_TOKEN"):
        st.error("HF_TOKEN belum diset")
        return None
    try:
        st.toast("Generate gambar...", icon="🎨")
        image = hf_client.text_to_image(
            f"{prompt}, photorealistic, 8k",
            model="stabilityai/stable-diffusion-3-medium-diffusers"
        )
        return image
    except Exception as e:
        st.error(f"Gagal bikin gambar: {e}")
        return None

def ganti_judul_otomatis(chat_id):
    chat = st.session_state.chats[chat_id]
    if chat["title"] == "Obrolan Baru":
        for msg in chat["messages"]:
            if msg["role"] == "user" and msg.get("type") == "text":
                title = " ".join(msg["content"].split()[:4])
                chat["title"] = title[:25] + "..." if len(title) > 25 else title
                break

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### ✨ Fanilla AI")
    if st.button("➕ Obrolan Baru", use_container_width=True):
        buat_chat_baru()
        st.rerun()

    st.markdown("---")
    st.markdown("**Riwayat**")
    sorted_chats = sorted(st.session_state.chats.items(), key=lambda x: x[1]["created_at"], reverse=True)
    for chat_id, chat_data in sorted_chats:
        if st.button(f"💬 {chat_data['title']}", key=f"chat_{chat_id}", use_container_width=True):
            st.session_state.active_chat_id = chat_id
            st.rerun()

# ==================== MAIN AREA ====================
active_chat = st.session_state.chats[st.session_state.active_chat_id]
messages = active_chat["messages"]

# Header Gemini style - cuma muncul kalo chat kosong
if len(messages) == 0:
    st.markdown("""
    <div class="gemini-header">
        <div class="gemini-title">Fanilla AI</div>
        <div class="gemini-subtitle">Dari FNL. Apa yang bisa kubantu hari ini bro?</div>
    </div>
    """, unsafe_allow_html=True)

    # Suggestions cards
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎨 Buatkan gambar logo FNL versi cyberpunk", use_container_width=True):
            st.session_state.suggestion = "buatkan gambar logo FNL versi cyberpunk"
            st.rerun()
        if st.button("📊 Analisis tren harga Bitcoin", use_container_width=True):
            st.session_state.suggestion = "harga bitcoin hari ini"
            st.rerun()
    with col2:
        if st.button("🖼️ Upload gambar untuk dianalisis", use_container_width=True):
            st.info("Upload gambar lewat tombol + di input bar bawah bro")
        if st.button("💡 Jelaskan AI dengan bahasa simpel", use_container_width=True):
            st.session_state.suggestion = "jelaskan AI dengan bahasa simpel"
            st.rerun()

# Render chat
for msg in messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image":
            st.image(msg["content"], caption=msg.get("caption"))
        else:
            st.markdown(msg["content"])

# ==================== INPUT ====================
if "suggestion" in st.session_state:
    prompt = {"text": st.session_state.suggestion}
    del st.session_state.suggestion
else:
    prompt = st.chat_input(
        "Tanya Fanilla...",
        accept_file=True,
        file_type=["jpg", "png", "jpeg"],
        disabled=st.session_state.processing
    )

if prompt and not st.session_state.processing:
    st.session_state.processing = True

    # HANDLE GAMBAR
    if prompt.get("files"):
        image = Image.open(prompt["files"][0])
        user_text = prompt.get("text", "Gimana gambar ini?")
        messages.append({"role": "user", "content": image, "type": "image", "caption": user_text})
        with st.chat_message("user"):
            st.image(image, caption=user_text)
        with st.chat_message("assistant"):
            placeholder = st.empty()
            try:
                with st.spinner(""):
                    stream = chat_vision(image, user_text)
                    if stream:
                        for full_response in stream:
                            placeholder.markdown(full_response + "▌")
                        placeholder.markdown(full_response)
                        messages.append({"role": "assistant", "content": full_response, "type": "text"})
            except Exception as e:
                placeholder.error(f"Error: {e}")

    # HANDLE TEKS
    elif prompt.get("text"):
        user_text = prompt["text"]

        # DETEKSI BIKIN GAMBAR
        if any(kata in user_text.lower() for kata in ["buatkan gambar", "bikin gambar", "gambar", "lukis", "generate"]):
            messages.append({"role": "user", "content": user_text, "type": "text"})
            with st.chat_message("user"):
                st.markdown(user_text)
            with st.chat_message("assistant"):
                with st.spinner(""):
                    result = generate_image(user_text)
                    if result:
                        st.image(result, caption=user_text)
                        st.caption("Note: maaf bila gambar tidak memuaskan 🙏")
                        messages.append({"role": "assistant", "content": result, "type": "image", "caption": user_text})
        else:
            # CHAT BIASA
            messages.append({"role": "user", "content": user_text, "type": "text"})
            with st.chat_message("user"):
                st.markdown(user_text)
            with st.chat_message("assistant"):
                placeholder = st.empty()
                try:
                    with st.spinner(""):
                        stream = chat_ai(messages)
                        if stream:
                            for full_response in stream:
                                placeholder.markdown(full_response + "▌")
                            placeholder.markdown(full_response)
                            messages.append({"role": "assistant", "content": full_response, "type": "text"})
                except Exception as e:
                    placeholder.error(f"Error: {e}")

    ganti_judul_otomatis(st.session_state.active_chat_id)
    st.session_state.processing = False
    st.rerun()
