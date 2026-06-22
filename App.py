import streamlit as st
from groq import Groq
from huggingface_hub import InferenceClient
from PIL import Image
import time, base64, io, uuid, asyncio, os, signal
from datetime import datetime
import pytz
import fitz
from duckduckgo_search import DDGS
from googlesearch import search as google_search
import requests
from bs4 import BeautifulSoup
import edge_tts
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr

# ==================== CONFIG & STYLE ====================
st.set_page_config(page_title="Fanilla AI by FNL", page_icon="✨", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
#MainMenu, footer, header {visibility: hidden;}
.main.block-container {padding-top: 0.5rem; max-width: 900px;}
.stChatInput > div {background-color: #374151; border-radius: 24px;}
.fanilla-title {background: linear-gradient(90deg, #A855F7, #EC4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.2rem; font-weight: 800; text-align: center;}
.custom-sidebar {background-color: #111827; border: 1px solid #374151; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;}
.image-note {font-size: 0.8rem; color: #9CA3AF; text-align: center; margin-top: 8px; font-style: italic;}
</style>""", unsafe_allow_html=True)

# ==================== INIT CLIENTS ====================
try:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    hf_client = InferenceClient(token=st.secrets.get("HF_TOKEN"))
except Exception as e:
    st.error(f"API Key error bro: {e}. Cek Secrets!")
    st.stop()

# ==================== SESSION STATE ====================
def buat_chat_baru():
    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {
        "title": "Obrolan Baru",
        "messages": [{"role": "assistant", "content": "Hai bro! Fanilla V9.0.4 Anti Stuck. Timeout 15 detik. Gas upload logo FNL ✨", "type": "text"}],
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
if "mode" not in st.session_state:
    st.session_state.mode = "idle"
if "processing" not in st.session_state:
    st.session_state.processing = False

# ==================== FUNGSI ANTI STUCK ====================
def stream_with_timeout(stream, timeout=15):
    """V9.0.4 - Kalo 15 detik ga ada chunk, matiin paksa"""
    start_time = time.time()
    full_response = ""
    for chunk in stream:
        if time.time() - start_time > timeout:
            raise TimeoutError("Kelamaan bro, Groq ngambek >15 detik")
        if chunk.choices[0].delta.content:
            full_response += chunk.choices[0].delta.content
            yield full_response
    yield full_response

def chat_ai(messages, model="llama-3.3-70b-versatile"):
    try:
        user_terakhir = messages[-1]["content"].lower()
        keyword_realtime = ["hari ini", "terbaru", "sekarang", "harga", "kurs", "berita", "cuaca", "siapa yang", "kapan", "skor", "update", "2024", "2025", "2026", "hasil"]
        perlu_search = any(kata in user_terakhir for kata in keyword_realtime)

        if perlu_search:
            with st.spinner("🔍 Browsing..."):
                hasil_search = search_internet(messages[-1]["content"])
                context_tambahan = f"\n\n[INFO TERBARU]:\n{hasil_search}\nJawab pake info di atas."
                messages[-1]["content"] += context_tambahan

        tz = pytz.timezone('Asia/Jakarta')
        tanggal_hari_ini = datetime.now(tz).strftime("%A, %d %B %Y, %H:%M WIB")
        system_prompt = {
            "role": "system",
            "content": f"Kamu Fanilla AI dari FNL. Hari ini {tanggal_hari_ini}. Tahun 2026. Jawab santai pake 'bro'."
        }

        history = [system_prompt] + [{"role": m["role"], "content": m["content"]} for m in messages if m.get("type") == "text"]
        return groq_client.chat.completions.create(model=model, messages=history, stream=True, timeout=15)
    except Exception as e:
        st.error(f"Error AI: {e}")
        return None

def chat_vision(images, prompt):
    """V9.0.4 - ANTI STUCK. Timeout 15 detik + Pake Model Ringan"""
    try:
        content_list = [{"type": "text", "text": f"Lo Fanilla AI. User upload logo FNL. Pertanyaan: {prompt}. Jawab 'bro', rating 1-10, filosofi F-N-L. Singkat 3 kalimat."}]

        # Pake 1 gambar aja + resize biar kecil
        image = images[0]
        image.thumbnail((512, 512)) # KECILIN GAMBAR BIAR GA BERAT
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=70)
        base64_image = base64.b64encode(buffered.getvalue()).decode()
        content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}})

        messages = [{"role": "user", "content": content_list}]

        st.toast("Panggil Llama-4-Maverick 15 detik...", icon="🚀")
        stream = groq_client.chat.completions.create(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            messages=messages,
            stream=True,
            timeout=15,
            max_tokens=200 # BATASIN BIAR CEPET
        )
        return stream_with_timeout(stream, timeout=15)

    except TimeoutError as e:
        st.error(f"TIMEOUT BRO: {e}. Groq lemot. Coba lagi atau upload gambar lebih kecil.")
        return None
    except Exception as e:
        error_msg = str(e)
        st.error(f"GAGAL VISION: {error_msg}")
        if "rate_limit" in error_msg.lower():
            st.warning("Limit Groq abis bro. Tunggu jam 7 pagi WIB.")
        return None

def baca_pdf(file):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = "".join([page.get_text() for page in doc])
        return text[:12000] if text else "PDF kosong bro"
    except Exception as e:
        return f"Gagal baca PDF: {e}"

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
    return "Search error bro."

def generate_image(prompt):
    if not st.secrets.get("HF_TOKEN"): return "HF_TOKEN belum diset bro"
    try:
        image = hf_client.text_to_image(f"{prompt}, photorealistic", model="stabilityai/stable-diffusion-3-medium-diffusers")
        return image
    except Exception as e:
        return f"Gagal bikin gambar: {e}"

def ganti_judul_otomatis(chat_id):
    chat = st.session_state.chats[chat_id]
    if chat["title"] == "Obrolan Baru":
        for msg in chat["messages"]:
            if msg["role"] == "user" and msg.get("type") == "text":
                title = " ".join(msg["content"].split()[:4])
                chat["title"] = title[:25] + "..." if len(title) > 25 else title
                break

# ==================== UI ====================
if st.button("☰ Menu Fitur", use_container_width=True):
    st.session_state.show_sidebar = not st.session_state.show_sidebar
    st.rerun()

if st.session_state.show_sidebar:
    with st.container():
        st.markdown('<div class="custom-sidebar">', unsafe_allow_html=True)
        if st.button("📝 Obrolan Baru", use_container_width=True, type="primary"):
            buat_chat_baru(); st.rerun()
        st.markdown("**Fitur Cepat:**")
        if st.button("🎨 Bikin Gambar", use_container_width=True): st.session_state.mode = "gambar"; st.rerun()
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
        if msg.get("type") == "image": st.image(msg["content"], caption=msg.get("caption"))
        else: st.markdown(msg["content"])

# ==================== MODE GAMBAR ====================
if st.session_state.mode == "gambar":
    prompt_gambar = st.text_input("Deskripsiin gambar:")
    if prompt_gambar:
        with st.spinner("Ngelukis..."):
            result = generate_image(prompt_gambar)
            if isinstance(result, str): st.error(result)
            else:
                st.image(result, caption=prompt_gambar)
                messages.append({"role": "assistant", "content": result, "type": "image", "caption": prompt_gambar})
            st.session_state.mode = "idle"; ganti_judul_otomatis(st.session_state.active_chat_id); st.rerun()

# ==================== INPUT UTAMA - ANTI STUCK ====================
prompt = st.chat_input("Ketik / upload gambar...", accept_file=True, file_type=["jpg", "png", "jpeg"], disabled=st.session_state.processing)

if prompt and not st.session_state.processing:
    st.session_state.processing = True

    # HANDLE GAMBAR
    if prompt.get("files"):
        image = Image.open(prompt["files"][0])
        user_text = prompt.get("text", "Gimana logo ini?")
        messages.append({"role": "user", "content": image, "type": "image", "caption": user_text})
        with st.chat_message("user"): st.image(image, caption=user_text)
        with st.chat_message("assistant"):
            placeholder = st.empty()
            try:
                with st.spinner("Mikirin logo 15 detik..."):
                    stream = chat_vision([image], user_text)
                    if stream:
                        for full_response in stream:
                            placeholder.markdown(full_response + "▌")
                        placeholder.markdown(full_response)
                        messages.append({"role": "assistant", "content": full_response, "type": "text"})
                    else:
                        placeholder.error("Vision gagal bro. Cek error merah di atas.")
            except Exception as e:
                placeholder.error(f"Stuck kecegah: {e}")

    # HANDLE TEKS
    elif prompt.get("text"):
        user_text = prompt["text"]
        messages.append({"role": "user", "content": user_text, "type": "text"})
        with st.chat_message("user"): st.markdown(user_text)
        with st.chat_message("assistant"):
            placeholder = st.empty()
            try:
                with st.spinner("Ngetik..."):
                    stream = chat_ai(messages)
                    if stream:
                        for full_response in stream_with_timeout(stream, timeout=15):
                            placeholder.markdown(full_response + "▌")
                        placeholder.markdown(full_response)
                        messages.append({"role": "assistant", "content": full_response, "type": "text"})
            except Exception as e:
                placeholder.error(f"Stuck kecegah: {e}")

    ganti_judul_otomatis(st.session_state.active_chat_id)
    st.session_state.processing = False
    st.rerun()

st.markdown("---")
st.caption("Fanilla AI is a product of FNL © 2026")
