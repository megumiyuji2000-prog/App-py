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

# ==================== CONFIG ====================
st.set_page_config(page_title="Fanilla AI by FNL", page_icon="✨", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
#MainMenu, footer, header {visibility: hidden;}
.main.block-container {padding-top: 0.5rem; max-width: 900px;}
.stChatInput > div {background-color: #374151; border-radius: 24px;}
.fanilla-title {background: linear-gradient(90deg, #A855F7, #EC4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.2rem; font-weight: 800; text-align: center;}
.custom-sidebar {background-color: #111827; border: 1px solid #374151; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;}
.image-note {font-size: 0.8rem; color: #9CA3AF; text-align: center; margin-top: 8px; font-style: italic;}
</style>""", unsafe_allow_html=True)

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
        "messages": [{"role": "assistant", "content": "Fanilla V9.2 Ultra Lite. Fitur: Chat, Liat Gambar, Buat Gambar, Search. Gas bro ✨", "type": "text"}],
        "created_at": datetime.now()
    }
    st.session_state.active_chat_id = chat_id
    st.session_state.show_sidebar = False

if "chats" not in st.session_state:
    st.session_state.chats = {}
    buat_chat_baru()

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = list(st.session_state.chats.keys())[0]
if "show_sidebar" not in st.session_state:
    st.session_state.show_sidebar = False
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
                st.toast("Search: DDG ✅", icon="🦆")
                return "\n\n".join(hasil_final)
    except:
        pass
    try:
        for url in google_search(query, num_results=3, lang="id"):
            hasil_final.append(f"Sumber: {url}")
        if hasil_final:
            st.toast("Search: Google ✅", icon="✅")
            return "\n\n".join(hasil_final)
    except:
        pass
    return "Search error."

def chat_ai(messages):
    """1. CHAT + AUTO SEARCH"""
    try:
        user_terakhir = messages[-1]["content"].lower()
        keyword_realtime = ["hari ini", "terbaru", "sekarang", "harga", "kurs", "berita", "cuaca", "siapa", "kapan", "skor", "update", "2024", "2025", "2026", "hasil"]
        perlu_search = any(kata in user_terakhir for kata in keyword_realtime)

        if perlu_search:
            with st.spinner("🔍 Browsing..."):
                hasil_search = search_internet(messages[-1]["content"])
                messages[-1]["content"] += f"\n\n[INFO TERBARU]:\n{hasil_search}\nJawab pake info di atas."

        tz = pytz.timezone('Asia/Jakarta')
        tanggal = datetime.now(tz).strftime("%A, %d %B %Y, %H:%M WIB")
        system_prompt = {
            "role": "system",
            "content": f"Kamu Fanilla AI dari FNL. Hari ini {tanggal}. Tahun 2026. Jawab santai pake 'bro'."
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
        st.error(f"Error Chat: {e}")
        return None

def chat_vision(image, prompt):
    """2. LIAT GAMBAR"""
    try:
        content_list = [{"type": "text", "text": f"Lo Fanilla AI dari FNL. User upload gambar. Pertanyaan: {prompt}. Jawab 'bro', rating 1-10 kalo logo, jelasin singkat. Max 3 kalimat."}]

        image.thumbnail((512, 512))
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=70)
        base64_image = base64.b64encode(buffered.getvalue()).decode()
        content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}})

        messages = [{"role": "user", "content": content_list}]

        st.toast("Analisis gambar...", icon="🚀")
        stream = groq_client.chat.completions.create(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            messages=messages,
            stream=True,
            timeout=15,
            max_tokens=150
        )
        return stream_with_timeout(stream, timeout=15)

    except TimeoutError as e:
        st.error(f"TIMEOUT: {e}")
        return None
    except Exception as e:
        error_msg = str(e)
        st.error(f"GAGAL VISION: {error_msg}")
        if "rate_limit" in error_msg.lower():
            st.warning("Limit Groq abis. Tunggu jam 7 pagi WIB.")
        return None

def generate_image(prompt):
    """3. BUAT GAMBAR"""
    if not st.secrets.get("HF_TOKEN"):
        st.error("HF_TOKEN belum diset")
        return None
    try:
        st.toast("Ngelukis...", icon="🎨")
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

# ==================== UI ====================
if st.button("☰ Menu", use_container_width=True):
    st.session_state.show_sidebar = not st.session_state.show_sidebar
    st.rerun()

if st.session_state.show_sidebar:
    with st.container():
        st.markdown('<div class="custom-sidebar">', unsafe_allow_html=True)
        if st.button("📝 Obrolan Baru", use_container_width=True, type="primary"):
            buat_chat_baru(); st.rerun()
        st.markdown("**Fitur Aktif:**")
        st.write("✅ Chat + Search Internet")
        st.write("✅ Liat Gambar")
        st.write("✅ Buat Gambar")
        st.markdown("**List Obrolan:**")
        sorted_chats = sorted(st.session_state.chats.items(), key=lambda x: x[1]["created_at"], reverse=True)
        for chat_id, chat_data in sorted_chats:
            c1, c2 = st.columns([0.85, 0.15])
            with c1:
                if st.button(f"💬 {chat_data['title']}", key=f"chat_{chat_id}", use_container_width=True):
                    st.session_state.active_chat_id = chat_id; st.session_state.show_sidebar = False; st.rerun()
            with c2:
                if st.button("🗑️", key=f"del_{chat_id}"):
                    if len(st.session_state.chats) > 1: del st.session_state.chats[chat_id]; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

active_chat = st.session_state.chats[st.session_state.active_chat_id]
messages = active_chat["messages"]

col1, col2 = st.columns([0.15, 0.85])
with col1:
    st.write("✨")
with col2:
    st.markdown('<p class="fanilla-title">Fanilla AI</p>', unsafe_allow_html=True)

for msg in messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image":
            st.image(msg["content"], caption=msg.get("caption"))
        else:
            st.markdown(msg["content"])

# ==================== INPUT ====================
prompt = st.chat_input(
    "Ketik / upload gambar...",
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
                with st.spinner("Mikirin..."):
                    stream = chat_vision(image, user_text)
                    if stream:
                        for full_response in stream:
                            placeholder.markdown(full_response + "▌")
                        placeholder.markdown(full_response)
                        messages.append({"role": "assistant", "content": full_response, "type": "text"})
                    else:
                        placeholder.error("Vision gagal. Cek error di atas.")
            except Exception as e:
                placeholder.error(f"Error: {e}")

    # HANDLE TEKS - BISA TRIGGER BUAT GAMBAR ATAU CHAT BIASA
    elif prompt.get("text"):
        user_text = prompt["text"]

        # DETEKSI KALO USER MAU BIKIN GAMBAR
        if any(kata in user_text.lower() for kata in ["buatkan gambar", "bikin gambar", "gambar", "lukis", "generate image"]):
            messages.append({"role": "user", "content": user_text, "type": "text"})
            with st.chat_message("user"):
                st.markdown(user_text)
            with st.chat_message("assistant"):
                with st.spinner("Ngelukis..."):
                    result = generate_image(user_text)
                    if result:
                        st.image(result, caption=user_text)
                        st.markdown('<p class="image-note">Note: maaf bila gambar tidak memuaskan 🙏</p>', unsafe_allow_html=True)
                        messages.append({"role": "assistant", "content": result, "type": "image", "caption": user_text})
                    else:
                        st.error("Gagal bikin gambar")
        else:
            # CHAT BIASA + AUTO SEARCH
            messages.append({"role": "user", "content": user_text, "type": "text"})
            with st.chat_message("user"):
                st.markdown(user_text)
            with st.chat_message("assistant"):
                placeholder = st.empty()
                try:
                    with st.spinner("Ngetik..."):
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

st.markdown("---")
st.caption("Fanilla AI is a product of FNL © 2026")
