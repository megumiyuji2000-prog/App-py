import streamlit as st
from groq import Groq
from huggingface_hub import InferenceClient
from PIL import Image
import time, base64, io, uuid, asyncio, os
from datetime import datetime
import pytz
import fitz # PyMuPDF
from duckduckgo_search import DDGS
from googlesearch import search as google_search
import requests
from bs4 import BeautifulSoup
import edge_tts
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
import cv2 # <-- BARU BUAT VIDEO
from moviepy.editor import VideoFileClip # <-- BARU BUAT VIDEO

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
    st.error(f"API Key error bro: {e}. Cek Secrets di Streamlit Cloud!")
    st.stop()

# ==================== SESSION STATE ====================
def buat_chat_baru():
    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {
        "title": "Obrolan Baru",
        "messages": [{"role": "assistant", "content": "Hai bro! Fanilla V9.0 nih. Udah bisa nonton video max 40MB. Upload aja ✨", "type": "text"}],
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

# ==================== FUNGSI FITUR ====================
def baca_pdf(file):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = "".join([page.get_text() for page in doc])
        return text[:12000] if text else "PDF kosong bro"
    except Exception as e:
        return f"Gagal baca PDF: {e}"

def search_internet(query):
    """V9.0 - TRIPLE ENGINE: DDG > Google > Fallback"""
    hasil_final = []
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3, region="id-id")]
            if results:
                for r in results:
                    hasil_final.append(f"Sumber: {r['href']}\nJudul: {r['title']}\n{r['body']}")
                st.toast("Search: DuckDuckGo ✅", icon="🦆")
                return "\n\n".join(hasil_final)
    except Exception as e:
        st.toast(f"DuckDuckGo gagal", icon="⚠️")
    try:
        st.toast("Coba Google Search...", icon="🔍")
        for url in google_search(query, num_results=3, lang="id"):
            try:
                page = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(page.content, 'html.parser')
                text = ' '.join(soup.get_text().split()[:50])
                hasil_final.append(f"Sumber: {url}\n{text}...")
            except:
                hasil_final.append(f"Sumber: {url}\nKonten ga bisa diambil")
        if hasil_final:
            st.toast("Search: Google ✅", icon="✅")
            return "\n\n".join(hasil_final)
    except Exception as e:
        st.toast(f"Google gagal", icon="⚠️")
    return "Waduh bro semua mesin search lagi error. Info realtime ga bisa diambil."

async def _edge_tts_async(text, voice="id-ID-ArdiNeural"):
    communicate = edge_tts.Communicate(text, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

def text_to_speech(text):
    try:
        if not text or len(text.strip()) == 0: return None
        audio_data = asyncio.run(_edge_tts_async(text[:500]))
        fp = io.BytesIO(audio_data)
        fp.seek(0)
        return fp
    except Exception as e:
        st.toast(f"TTS Error: {e}", icon="🔇")
        return None

def voice_to_text(audio_bytes):
    r = sr.Recognizer()
    try:
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio = r.record(source)
        return r.recognize_google(audio, language='id-ID')
    except: return None

def chat_ai(messages, model="llama-3.3-70b-versatile"):
    """V9.0 - AUTO SEARCH + TIME AWARE"""
    try:
        user_terakhir = messages[-1]["content"].lower()
        keyword_realtime = ["hari ini", "terbaru", "sekarang", "harga", "kurs", "berita", "cuaca", "siapa yang", "kapan", "skor", "update", "2024", "2025", "2026", "hasil"]
        perlu_search = any(kata in user_terakhir for kata in keyword_realtime)

        if perlu_search:
            with st.spinner("🔍 Browsing internet dulu bro..."):
                hasil_search = search_internet(messages[-1]["content"])
                with st.expander("📝 Hasil Search Mentah"):
                    st.code(hasil_search[:1000])
                context_tambahan = f"\n\n[INFO TERBARU DARI INTERNET]:\n{hasil_search}\nJawab pake info di atas. Sebutin sumbernya."
                messages[-1]["content"] += context_tambahan

        tz = pytz.timezone('Asia/Jakarta')
        tanggal_hari_ini = datetime.now(tz).strftime("%A, %d %B %Y, %H:%M WIB")
        system_prompt = {
            "role": "system",
            "content": f"Kamu adalah Fanilla AI, produk utama dari FNL. Hari ini {tanggal_hari_ini}. Tahun 2026. Kalo ada [INFO TERBARU DARI INTERNET], itu yang paling bener. Jawab santai pake 'bro'."
        }

        history = [system_prompt] + [{"role": m["role"], "content": m["content"]} for m in messages if m.get("type") == "text"]
        return groq_client.chat.completions.create(model=model, messages=history, stream=True, timeout=30)
    except Exception as e:
        st.error(f"Error AI: {e}")
        return None

def chat_vision(images, prompt): # <-- UPGRADE: Sekarang bisa banyak gambar
    """V9.0 - Bisa analisis multi-frame dari video"""
    try:
        content_list = [{"type": "text", "text": f"User upload beberapa frame dari video. Analisis keseluruhan videonya. Pertanyaan user: {prompt}. Jawab santai pake 'bro'."}]

        for image in images: # Loop semua frame
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            base64_image = base64.b64encode(buffered.getvalue()).decode()
            content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}})

        messages = [{"role": "user", "content": content_list}]
        return groq_client.chat.completions.create(model="meta-llama/llama-4-scout-17b-16e-instruct", messages=messages, stream=True, timeout=45)
    except Exception as e:
        st.error(f"Error Vision: {e}")
        return None

def proses_video(file):
    """V9.0 - Ekstrak 5 frame dari video buat dianalisis AI"""
    try:
        # Simpen video sementara
        tfile = io.BytesIO(file.read())
        with open("temp_video.mp4", "wb") as f:
            f.write(tfile.read())

        vidcap = cv2.VideoCapture("temp_video.mp4")
        total_frames = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_step = max(1, total_frames // 5) # Ambil 5 frame

        frames = []
        for i in range(5):
            vidcap.set(cv2.CAP_PROP_POS_FRAMES, i * frame_step)
            success, image = vidcap.read()
            if success:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) # Convert BGR ke RGB
                frames.append(Image.fromarray(image))

        vidcap.release()
        os.remove("temp_video.mp4") # Hapus file temp
        return frames
    except Exception as e:
        st.error(f"Gagal proses video: {e}")
        return []

def generate_image(prompt):
    if not st.secrets.get("HF_TOKEN"): return "HF_TOKEN belum diset bro"
    try:
        style = "photorealistic, 8k, ultra detailed, cinematic lighting"
        image = hf_client.text_to_image(f"{prompt}, {style}", model="stabilityai/stable-diffusion-3-medium-diffusers")
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

# ==================== UI MENU CUSTOM ====================
if st.button("☰ Menu Fitur", use_container_width=True):
    st.session_state.show_sidebar = not st.session_state.show_sidebar
    st.rerun()

if st.session_state.show_sidebar:
    with st.container():
        st.markdown('<div class="custom-sidebar">', unsafe_allow_html=True)
        if st.button("📝 Obrolan Baru", use_container_width=True, type="primary"):
            buat_chat_baru(); st.rerun()
        st.markdown("**Fitur Cepat:**")
        if st.button("📄 Rangkum PDF", use_container_width=True): st.session_state.mode = "pdf"; st.rerun()
        if st.button("🌐 Search Internet", use_container_width=True): st.session_state.mode = "search"; st.rerun()
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

# ==================== TAMPILAN CHAT ====================
active_chat = st.session_state.chats[st.session_state.active_chat_id]
messages = active_chat["messages"]

# LOGO HEADER FNL
col1, col2 = st.columns([0.15, 0.85])
with col1:
    st.image("https://i.imgur.com/placeholder.png", width=50) # Ganti URL logo FNL lo
with col2:
    st.markdown('<p class="fanilla-title">Fanilla AI</p>', unsafe_allow_html=True)

for msg in messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "audio": st.audio(msg["content"])
        elif msg.get("type") == "image": st.image(msg["content"], caption=msg.get("caption"))
        elif msg.get("type") == "video": st.video(msg["content"]) # <-- BARU
        else: st.markdown(msg["content"])

# ==================== HANDLE MODE KHUSUS ====================
if st.session_state.mode == "pdf":
    pdf_file = st.file_uploader("Upload PDF", type="pdf")
    if pdf_file:
        with st.spinner("Baca PDF..."):
            text = baca_pdf(pdf_file)
            prompt = f"Rangkum dokumen ini dengan bahasa santai:\n\n{text}"
            messages.append({"role": "user", "content": f"[Upload PDF: {pdf_file.name}]", "type": "text"})
            with st.chat_message("assistant"):
                placeholder = st.empty(); full_response = ""
                stream = chat_ai([{"role": "user", "content": prompt}])
                if stream:
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            placeholder.markdown(full_response + "▌")
                    placeholder.markdown(full_response)
                    messages.append({"role": "assistant", "content": full_response, "type": "text"})
            st.session_state.mode = "idle"; ganti_judul_otomatis(st.session_state.active_chat_id); st.rerun()

elif st.session_state.mode == "search":
    query = st.text_input("Mau cari apa?")
    if query:
        with st.spinner("Searching..."):
            hasil = search_internet(query)
            prompt = f"Jawab '{query}' berdasarkan info ini:\n{hasil}\nJawab santai + kasih sumber"
            messages.append({"role": "user", "content": f"[Search: {query}]", "type": "text"})
            with st.chat_message("assistant"):
                placeholder = st.empty(); full_response = ""
                stream = chat_ai([{"role": "user", "content": prompt}])
                if stream:
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            placeholder.markdown(full_response + "▌")
                    placeholder.markdown(full_response)
                    messages.append({"role": "assistant", "content": full_response, "type": "text"})
            st.session_state.mode = "idle"; ganti_judul_otomatis(st.session_state.active_chat_id); st.rerun()

elif st.session_state.mode == "gambar":
    prompt_gambar = st.text_input("Deskripsiin gambar yang mau dibikin:")
    if prompt_gambar:
        with st.spinner("Ngelukis..."):
            result = generate_image(prompt_gambar)
            if isinstance(result, str): st.error(result)
            else:
                st.image(result, caption=prompt_gambar)
                st.markdown('<p class="image-note">Note: maaf bila gambar yang dihasilkan tidak memuaskan 🙏</p>', unsafe_allow_html=True)
                messages.append({"role": "assistant", "content": result, "type": "image", "caption": prompt_gambar})
            st.session_state.mode = "idle"; ganti_judul_otomatis(st.session_state.active_chat_id); st.rerun()

# ==================== INPUT UTAMA - UPGRADE VIDEO ====================
col1, col2 = st.columns([0.9, 0.1])
with col1:
    prompt = st.chat_input("Ketik / upload gambar / video...", accept_file=True, file_type=["jpg", "png", "jpeg", "mp4", "mov", "avi"]) # <-- VIDEO MASUK
with col2:
    audio = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key='recorder')

if audio:
    text = voice_to_text(audio['bytes'])
    if text: prompt = {"text": text}

if prompt:
    # HANDLE VIDEO
    if prompt.get("files") and prompt["files"][0].type.startswith("video/"):
        video_file = prompt["files"][0]
        user_text = prompt.get("text", "Jelasin isi video ini bro")

        # Cek ukuran max 40MB
        if video_file.size > 40 * 1024 * 1024:
            st.error("Video kegedean bro, max 40MB")
        else:
            messages.append({"role": "user", "content": video_file, "type": "video", "caption": user_text})
            with st.chat_message("user"):
                st.video(video_file)
                st.write(user_text)

            with st.chat_message("assistant"):
                with st.spinner("Nonton videonya dulu bro... 🎬"):
                    frames = proses_video(video_file) # Ambil 5 frame

                if frames:
                    st.info(f"Dapet {len(frames)} cuplikan dari video. Lagi dianalisis...")
                    placeholder = st.empty(); full_response = ""
                    stream = chat_vision(frames, user_text) # Kirim 5 frame ke AI
                    if stream:
                        for chunk in stream:
                            if chunk.choices[0].delta.content:
                                full_response += chunk.choices[0].delta.content
                                placeholder.markdown(full_response + "▌")
                        placeholder.markdown(full_response)
                        messages.append({"role": "assistant", "content": full_response, "type": "text"})
                else:
                    st.error("Gagal ekstrak video bro")

    # HANDLE GAMBAR
    elif prompt.get("files") and prompt["files"][0].type.startswith("image/"):
        image = Image.open(prompt["files"][0])
        user_text = prompt.get("text", "Jelaskan gambar ini")
        messages.append({"role": "user", "content": image, "type": "image", "caption": user_text})
        with st.chat_message("user"): st.image(image, caption=user_text)
        with st.chat_message("assistant"):
            placeholder = st.empty(); full_response = ""
            stream = chat_vision([image], user_text) # <-- Kirim sebagai list
            if stream:
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
                messages.append({"role": "assistant", "content": full_response, "type": "text"})

    # HANDLE TEKS
    elif prompt.get("text"):
        user_text = prompt["text"]
        messages.append({"role": "user", "content": user_text, "type": "text"})
        with st.chat_message("user"): st.markdown(user_text)

        with st.chat_message("assistant"):
            placeholder = st.empty(); full_response = ""
            stream = chat_ai(messages)
            if stream:
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
                messages.append({"role": "assistant", "content": full_response, "type": "text"})
                with st.spinner("Bikin suara..."):
                    audio_fp = text_to_speech(full_response)
                    if audio_fp: st.audio(audio_fp, format="audio/mp3")

    ganti_judul_otomatis(st.session_state.active_chat_id)
    st.rerun()

# FOOTER FNL
st.markdown("---")
st.caption("Fanilla AI is a product of FNL © 2026")
