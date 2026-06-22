import streamlit as st
from groq import Groq
from openai import OpenAI
from PIL import Image
import time, base64, io
from datetime import datetime
import pytz
from duckduckgo_search import DDGS

st.set_page_config(page_title="Fanilla AI", page_icon="✨", layout="centered", initial_sidebar_state="collapsed")

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
</style>
""", unsafe_allow_html=True)

# ==================== INIT ====================
try:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    # PAKE OPENROUTER BUAT VISION GEMINI
    openrouter_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=st.secrets["OPENROUTER_API_KEY"],
    )
except Exception as e:
    st.error(f"API Key Error: {e}. Cek Secrets OPENROUTER_API_KEY sama GROQ_API_KEY")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False

# ==================== CORE ====================
def search_web(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if results:
                return "\n\n".join([f"Sumber: {r['href']}\n{r['body']}" for r in results])
    except:
        return "Search error."
    return "Tidak ada hasil."

def chat_stream(messages):
    try:
        user_msg = messages[-1]["content"].lower()
        need_search = any(word in user_msg for word in ["hari ini", "terbaru", "sekarang", "harga", "berita", "2024", "2025", "2026"])

        if need_search:
            with st.spinner("🔍 Searching..."):
                search_result = search_web(messages[-1]["content"])
                messages[-1]["content"] += f"\n\n[INFO WEB]:\n{search_result}"

        tz = pytz.timezone('Asia/Jakarta')
        date_now = datetime.now(tz).strftime("%d %B %Y")
        system = {"role": "system", "content": f"Kamu Fanilla AI dari FNL. Tanggal {date_now}. Jawab santai pake 'bro'."}
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
            if time.time() - start > 10: break
            if chunk.choices[0].delta.content:
                full += chunk.choices[0].delta.content
                yield full
    except Exception as e:
        yield f"Error Chat: {str(e)}"

def vision_gemini(image, prompt):
    """VISION PAKE GEMINI FLASH VIA OPENROUTER - DIJAMIN IDUP 24 JAM"""
    try:
        st.toast("Analisis pake Gemini...", icon="✨")
        image.thumbnail((768, 768))
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=85)
        base64_image = base64.b64encode(buffered.getvalue()).decode()

        response = openrouter_client.chat.completions.create(
            model="google/gemini-flash-1.5", # GRATIS 50 REQ/HARI
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Deskripsi gambar ini. User tanya: {prompt}. Jawab 'bro', rating 1-10 kalo logo. Max 3 kalimat."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }],
            max_tokens=200,
            timeout=15
        )
        yield response.choices[0].message.content
    except Exception as e:
        yield f"Error Vision Gemini: {str(e)[:100]}. Cek OPENROUTER_API_KEY di Secrets."

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### ✨ Fanilla AI")
    if st.button("🗑️ Hapus Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.caption("Fanilla AI v10.3 © FNL 2026")

# ==================== MAIN ====================
if len(st.session_state.messages) == 0:
    st.markdown('<div class="main-title">Fanilla AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Powered by Gemini Vision. Upload logo FNL coba bro.</div>', unsafe_allow_html=True)

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

    if prompt.get("files"):
        image = Image.open(prompt["files"][0])
        user_text = prompt.get("text", "Gimana gambar ini?")
        st.session_state.messages.append({"role": "user", "content": image, "type": "image", "caption": user_text})
        with st.chat_message("user"):
            st.image(image, caption=user_text)
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            try:
                for chunk in vision_gemini(image, user_text):
                    full_response = chunk
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response, "type": "text"})
            except Exception as e:
                placeholder.error(f"Error: {e}")

    elif prompt.get("text"):
        user_text = prompt["text"]
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
                st.session_state.messages.append({"role": "assistant", "content": full_response, "type": "text"})
            except Exception as e:
                placeholder.error(f"Error: {e}")

    st.session_state.processing = False
    st.rerun()
