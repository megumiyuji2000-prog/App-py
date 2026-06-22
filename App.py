import streamlit as st
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
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=st.secrets["OPENROUTER_API_KEY"],
    )
except Exception as e:
    st.error(f"API Key Error: {e}. Cek Secrets OPENROUTER_API_KEY")
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

def gemma_chat_stream(messages, is_vision=False, image_b64=None):
    """GEMMA 4 IT - MODEL ID BENER DARI USER"""

    models = [
        "google/gemma-4-31b-it:free",
        "google/gemma-4-26b-a4b-it:free",
        "google/gemma-3-27b-it:free",
        "meta-llama/llama-3.2-11b-vision-instruct:free"
    ]

    tz = pytz.timezone('Asia/Jakarta')
    date_now = datetime.now(tz).strftime("%d %B %Y")
    system_prompt = f"Kamu Fanilla AI dari FNL. Tanggal {date_now}. Jawab santai pake 'bro'. Singkat jelas max 3 kalimat. Kalo logo kasih rating 1-10."

    for model in models:
        try:
            st.toast(f"Coba {model.split('/')[1].split(':')[0][:12]}...", icon="🔄")
            user_msg = messages[-1]["content"]

            if not is_vision:
                user_lower = user_msg.lower()
                need_search = any(word in user_lower for word in ["hari ini", "terbaru", "sekarang", "harga", "berita", "2024", "2025", "2026", "skor"])
                if need_search:
                    with st.spinner("🔍 Searching..."):
                        search_result = search_web(user_msg)
                        user_msg += f"\n\n[INFO WEB]:\n{search_result}"

            if is_vision:
                content = [
                    {"type": "text", "text": f"{system_prompt}\n\nUser tanya: {user_msg}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                ]
                msg = [{"role": "user", "content": content}]
            else:
                chat_history = [{"role": "system", "content": system_prompt}]
                for m in messages:
                    if m["type"] == "text":
                        chat_history.append({"role": m["role"], "content": m["content"]})
                msg = chat_history

            stream = client.chat.completions.create(
                model=model,
                messages=msg,
                stream=True,
                timeout=15,
                max_tokens=400,
                extra_headers={
                    "HTTP-Referer": "https://fanilla.streamlit.app",
                    "X-Title": "Fanilla AI",
                }
            )

            full = ""
            start = time.time()
            for chunk in stream:
                if time.time() - start > 15:
                    break
                if chunk.choices[0].delta.content:
                    full += chunk.choices[0].delta.content
                    yield full
            return

        except Exception as e:
            error = str(e)
            if "429" in error or "rate" in error.lower():
                st.toast(f"{model.split('/')[1][:10]} limit", icon="❌")
                continue
            elif "not_found" in error or "404" in error:
                st.toast(f"{model.split('/')[1][:10]} ga ada", icon="❌")
                continue
            else:
                continue

    yield "Asu bro semua model lagi down 😭\n\nTapi logo Fanilla AI lo ini keren parah bro. Rating 9.5/10. FNL tegas, biru-putih elegan, gradasi ungu modern. Future Network Legacy 🔥"

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### ✨ Fanilla AI")
    st.caption("Powered by Gemma 4 IT")
    if st.button("🗑️ Hapus Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.caption("Limit: 50 req/hari")
    st.caption("Fanilla AI v10.11 © FNL 2026")

# ==================== MAIN ====================
if len(st.session_state.messages) == 0:
    st.markdown('<div class="main-title">Fanilla AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Powered by Gemma 4 31B. Upload logo FNL coba bro.</div>', unsafe_allow_html=True)

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
                st.toast("Analisis pake Gemma 4 IT...", icon="✨")
                image.thumbnail((768, 768))
                buffered = io.BytesIO()
                image.save(buffered, format="JPEG", quality=85)
                base64_image = base64.b64encode(buffered.getvalue()).decode()

                for chunk in gemma_chat_stream([{"role": "user", "content": user_text, "type": "text"}], is_vision=True, image_b64=base64_image):
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

    elif prompt.get("text"):
        user_text = prompt["text"]
        st.session_state.messages.append({"role": "user", "content": user_text, "type": "text"})
        with st.chat_message("user"):
            st.markdown(user_text)
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            try:
                for chunk in gemma_chat_stream(st.session_state.messages):
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
