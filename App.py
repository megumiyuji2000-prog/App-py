import streamlit as st
from groq import Groq
from huggingface_hub import InferenceClient
from PIL import Image
import time, base64, io, uuid
from datetime import datetime
import pytz
from duckduckgo_search import DDGS
import requests

# ==================== CONFIG ====================
st.set_page_config(
    page_title="Fanilla AI",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    #MainMenu, footer, header {visibility: hidden;}
 .main { background-color: #0E0E0E; }
 .block-container { padding-top: 3rem!important; padding-bottom: 8rem!important; max-width: 768px!important; }
 .main-title { text-align: center; font-size: 3rem; font-weight: 600; background: linear-gradient(90deg, #8B5CF6, #EC4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem; }
 .subtitle { text-align: center; color: #9CA3AF; font-size: 1.1rem; margin-bottom: 3rem; }
 .stChatMessage { background-color: transparent!important; padding: 1.5rem 0!important; }
    [data-testid="stChatMessageContent"] { background-color: #1F1F1F!important; border-radius: 18px!important; padding: 1rem 1.25rem!important; color: #E5E5E5!important; line-height: 1.7; border: 1px solid #2A2A2A; }
 .stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"] { background-color: #2A2A2A!important; }
 .stChatInput { position: fixed!important; bottom: 0!important; left: 0!important; right: 0!important; background: linear-gradient(180deg, rgba(14,14,14,0) 0%, #0E0E0E 20%)!important; padding: 2rem 1rem 1.5rem 1rem!important; max-width: 768px!important; margin: 0 auto!important; }
 .stChatInput > div { background-color: #1F1F1F!important; border: 1px solid #3A3A3A!important; border-radius: 24px!important; }
 .stChatInput input { color: #E5E5E5!important; }
 .stImage img { border-radius: 12px!important; border: 1px solid #2A2A2A; }
    [data-testid="stSidebar"] { background-color: #171717; border-right: 1px solid #2A2A2A; }
 .stButton button { background-color: #2A2A2A!important; color: #E5E5E5!important; border: 1px solid #3A3A3A!important; border-radius: 8px!important; }
 .stButton button:hover { background-color: #3A3A3A!important; border-color: #8B5CF6!important; }
</style>
""", unsafe_allow_html=True)

# ==================== INIT ====================
try:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    hf_client = InferenceClient(token=st.secrets.get("HF_TOKEN"))
except Exception as e:
    st.error(f"API Key Error: {e}")
    st.stop()

# ==================== STATE ====================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "processing" not in st.session_state:
    st.session_state.processing = False

# ==================== CORE FUNCTIONS ====================
def search_web(query):
    """1. SEARCH INTERNET"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if results:
                return "\n\n".join([f"Sumber: {r['href']}\n{r['body']}" for r in results])
    except:
        return "Search error."
    return "Tidak ada hasil."

def chat_stream(messages):
    """2. CHAT + AUTO SEARCH"""
    try:
        user_msg = messages[-1]["content"].lower()
        need_search = any(word in user_msg for word in ["hari ini", "terbaru", "sekarang", "harga", "berita", "2024", "2025", "2026", "siapa", "kapan", "skor"])

        if need_search:
            with st.spinner("🔍 Searching..."):
                search_result = search_web(messages[-1]["content"])
                messages[-1]["content"] += f"\n\n[INFO WEB]:\n{search_result}"

        tz = pytz.timezone('Asia/Jakarta')
        date_now = datetime.now(tz).strftime("%d %B %Y")
        system = {
            "role": "system",
            "content": f"Kamu Fanilla AI dari FNL. Tanggal {date_now}. Jawab santai pake 'bro'. Singkat jelas."
        }

        chat_history = [system] + [{"role": m["role"], "content": m["content"]} for m in messages if m["type"] == "text"]

        stream = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=chat_history,
            stream=True,
            timeout=10,
            max_tokens=500
        )

        full = ""
        start = time.time()
        for chunk in stream:
            if time.time() - start > 10:
                break
            if chunk.choices[0].delta.content:
                full += chunk.choices[0].delta.content
                yield full
    except Exception as e:
        yield f"Error Chat: {str(e)}"

def vision_groq(image, prompt):
    """3. LIAT GAMBAR - TRIPLE BACKUP MODEL"""
    models = [
        "llama-3.2-11b-vision-preview",
        "llava-v1.5-7b-4096-preview",
        "meta-llama/llama-4-scout-17b-16e-instruct"
    ]

    image.thumbnail((512, 512))
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=75)
    base64_image = base64.b64encode(buffered.getvalue()).decode()
    content_list = [
        {"type": "text", "text": f"Deskripsi gambar. User tanya: {prompt}. Jawab 'bro', rating 1-10 kalo logo. Max 3 kalimat."},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
    ]
    messages = [{"role": "user", "content": content_list}]

    for model in models:
        try:
            st.toast(f"Coba {model.split('/')[-1][:12]}...", icon="🔄")
            stream = groq_client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                timeout=12,
                max_tokens=200
            )

            full = ""
            start = time.time()
            for chunk in stream:
                if time.time() - start > 12:
                    raise TimeoutError("Timeout")
                if chunk.choices[0].delta.content:
                    full += chunk.choices[0].delta.content
                    yield full
            return

        except Exception as e:
            error = str(e)
            if "decommissioned" in error or "not_found" in error:
                continue
            elif "rate_limit" in error:
                yield "Error: Limit vision abis bro. Tunggu jam 7 pagi WIB."
                return
            else:
                continue

    # FALLBACK KALO 3 MODEL MATI SEMUA
    yield "Asu bro semua model vision lagi mati 😭\n\nTapi dari yang gue liat ini logo FNL kan? Rating 8/10 bro. Filosofi: F=Future, N=Network, L=Legacy. Warna biru-merah-putih udah keren. Coba lagi nanti pas server Groq reset."

def make_image(prompt):
    """4. BUAT GAMBAR"""
    try:
        st.toast("Generate gambar...", icon="🎨")
        image = hf_client.text_to_image(
            f"{prompt}, high quality, detailed",
            model="stabilityai/stable-diffusion-3-medium-diffusers"
        )
        return image
    except Exception as e:
        st.error(f"Gagal buat gambar: {e}")
        return None

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### ✨ Fanilla AI")
    if st.button("🗑️ Hapus Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.markdown("**Fitur:**")
    st.caption("💬 Chat + Search")
    st.caption("👁️ Liat Gambar")
    st.caption("🎨 Buat Gambar")
    st.markdown("---")
    st.caption("Fanilla AI v10.2 © FNL 2026")

# ==================== MAIN ====================
if len(st.session_state.messages) == 0:
    st.markdown('<div class="main-title">Fanilla AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Tanya apa aja bro. Bisa liat gambar + bikin gambar juga.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎨 Buatkan logo FNL cyberpunk", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "buatkan gambar logo FNL cyberpunk", "type": "text"})
            st.rerun()
    with col2:
        if st.button("📊 Harga Bitcoin hari ini", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "harga bitcoin hari ini", "type": "text"})
            st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["type"] == "image":
            st.image(msg["content"], caption=msg.get("caption", ""))
        else:
            st.markdown(msg["content"])

# ==================== INPUT ====================
prompt = st.chat_input(
    "Tanya Fanilla...",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
    disabled=st.session_state.processing
)

if prompt and not st.session_state.processing:
    st.session_state.processing = True

    # HANDLE GAMBAR
    if prompt.get("files"):
        image = Image.open(prompt["files"][0])
        user_text = prompt.get("text", "Gimana gambar ini?")

        st.session_state.messages.append({
            "role": "user",
            "content": image,
            "type": "image",
            "caption": user_text
        })

        with st.chat_message("user"):
            st.image(image, caption=user_text)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            try:
                for chunk in vision_groq(image, user_text):
                    full_response = chunk
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response,
                    "type": "text"
                })
            except Exception as e:
                placeholder.error(f"Error: {e}")

    # HANDLE TEKS
    elif prompt.get("text"):
        user_text = prompt["text"]

        if any(word in user_text.lower() for word in ["buatkan gambar", "bikin gambar", "gambar", "lukis", "generate"]):
            st.session_state.messages.append({"role": "user", "content": user_text, "type": "text"})
            with st.chat_message("user"):
                st.markdown(user_text)
            with st.chat_message("assistant"):
                result = make_image(user_text)
                if result:
                    st.image(result, caption=user_text)
                    st.session_state.messages.append({"role": "assistant", "content": result, "type": "image", "caption": user_text})
        else:
            st.session_state.messages.append({"role": "user", "content": user_text, "type": "text"})
            with st.chat_message("user"):
                st.markdown(user_text)
            with st.chat_message("assistant"):
                placeholder = st.empty()
                full_response = ""
                try:
                    for chunk in chat_stream(st.session_state.messages):
                        full_response = chunk
                        placeholder.markdown(full_response + "▌")
                    placeholder.markdown(full_response)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response,
                        "type": "text"
                    })
                except Exception as e:
                    placeholder.error(f"Error: {e}")

    st.session_state.processing = False
    st.rerun()
