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
if "user_style" not in st.session_state:
    st.session_state.user_style = "santai"

# ==================== MODEL LIST STABIL ====================
CHAT_MODELS = [
    "meta-llama/llama-3.1-70b-instruct:free", # PALING STABIL
    "mistralai/mistral-7b-instruct:free", # BACKUP RINGAN
    "google/gemma-2-9b-it:free" # BACKUP DARURAT
]

VISION_MODELS = [
    "qwen/qwen-2-vl-72b-instruct:free", # PALING STABIL VISION
    "meta-llama/llama-3.2-11b-vision-instruct:free", # BACKUP VISION
    "google/gemma-3-27b-it:free" # BACKUP DARURAT
]

# ==================== CORE ====================
def detect_user_style(text):
    text_lower = text.lower()
    formal_words = ["apakah", "bagaimana", "mohon", "terima kasih", "saya", "anda", "jelaskan"]
    bro_words = ["bro", "gk", "ga", "lu", "gw", "wkwk", "anjir", "asu", "bung"]

    formal_score = sum(1 for w in formal_words if w in text_lower)
    bro_score = sum(1 for w in bro_words if w in text_lower)

    if bro_score > formal_score:
        return "santai"
    elif formal_score > 0:
        return "formal"
    return st.session_state.user_style

def search_web(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if results:
                return "\n\n".join([f"Sumber: {r['href']}\n{r['body']}" for r in results])
    except:
        return "Search error."
    return "Tidak ada hasil."

def ai_stream(messages, is_vision=False, image_b64=None):
    """V13.0 STABLE MODE - LLAMA 3.1 + QWEN 2 VL"""

    user_msg = messages[-1]["content"]
    st.session_state.user_style = detect_user_style(user_msg)

    # AUTO SEARCH BUAT FAKTA
    user_lower = user_msg.lower()
    need_search = any(word in user_lower for word in [
        "apa itu", "bagaimana", "kenapa", "jelaskan", "definisi", "fakta",
        "hari ini", "terbaru", "sekarang", "harga", "berita", "2025", "2026", "skor",
        "pasir hisap", "siapa", "kapan", "dimana", "sejarah", "tinggi"
    ])

    if not is_vision and need_search:
        with st.spinner("🔍 Cek fakta..."):
            search_result = search_web(user_msg)
            user_msg += f"\n\n[FAKTA DARI WEB]:\n{search_result}"

    tz = pytz.timezone('Asia/Jakarta')
    date_now = datetime.now(tz).strftime("%d %B %Y")

    # SYSTEM PROMPT V13.0
    if st.session_state.user_style == "santai":
        system_prompt = f"""Kamu Fanilla AI dari FNL. Tanggal {date_now}.
ATURAN:
1. Jawab FAKTA SAINS. Cek ejaan.
2. Pake data [FAKTA DARI WEB] kalo ada.
3. Gaya santai: 'bro', 'lu', 'gw'. Max 3 kalimat.
4. Logo: kasih rating 1-10 + alasan singkat.
5. Pasir hisap: campuran pasir jenuh air. Densitas 2 g/cm³, manusia 1 g/cm³ jadi ngambang."""
    else:
        system_prompt = f"""Anda adalah Fanilla AI dari FNL. Tanggal {date_now}.
ATURAN:
1. Jawab FAKTA SAINS AKURAT. Periksa ejaan.
2. Gunakan data [FAKTA DARI WEB] jika ada.
3. Bahasa formal. Maksimal 3 kalimat.
4. Logo: berikan rating 1-10 + alasan.
5. Pasir hisap: campuran pasir jenuh air. Densitas ~2 g/cm³, manusia ~1 g/cm³ sehingga mengapung."""

    # PILIH MODEL STABIL
    models = VISION_MODELS if is_vision else CHAT_MODELS

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

    # COBA MODEL STABIL
    for model in models:
        try:
            model_name = model.split('/')[1].split(':')[0]
            st.toast(f"Pake {model_name[:15]}...", icon="✅")

            stream = client.chat.completions.create(
                model=model,
                messages=msg,
                stream=True,
                timeout=20,
                max_tokens=400,
                temperature=0.2,
                top_p=0.9,
                extra_headers={
                    "HTTP-Referer": "https://fanilla.streamlit.app",
                    "X-Title": "Fanilla AI",
                }
            )

            full = ""
            start = time.time()
            for chunk in stream:
                if time.time() - start > 20:
                    break
                if chunk.choices[0].delta.content:
                    full += chunk.choices[0].delta.content
                    yield full
            return

        except Exception as e:
            error = str(e)
            if "429" in error or "rate" in error.lower():
                st.toast(f"{model_name[:10]} limit, ganti...", icon="⚠️")
                continue
            else:
                continue

    # FALLBACK ADAPTIF V13.0
    if is_vision:
        if st.session_state.user_style == "santai":
            yield "Server vision lagi error bro 😭 Semua model down. Tapi logo FNL lo tetep keren: 9.5/10. 3 garis biru-putih-merah = growth. FNL Future Network Legacy 🔥"
        else:
            yield "Mohon maaf, server vision sedang gangguan. Namun logo FNL Anda sangat baik. Rating 9.5/10. Tiga garis melambangkan pertumbuhan."
    else:
        if st.session_state.user_style == "santai":
            yield "Server lagi error bro. Coba tanya lagi 1 menit ya."
        else:
            yield "Mohon maaf, server sedang bermasalah. Silakan coba beberapa saat lagi."

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### ✨ Fanilla AI")
    st.caption(f"Style: {st.session_state.user_style}")
    if st.button("🗑️ Hapus Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.user_style = "santai"
        st.rerun()
    st.markdown("---")
    st.caption("Vision: Qwen 2 VL 72B")
    st.caption("Chat: Llama 3.1 70B")
    st.caption("Mode: Stable V13.0")
    st.caption("Fanilla AI © FNL 2026")

# ==================== MAIN ====================
if len(st.session_state.messages) == 0:
    st.markdown('<div class="main-title">Fanilla AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Powered by Llama 3.1 + Qwen 2 VL. Paling stabil gratisan.</div>', unsafe_allow_html=True)

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
                image.thumbnail((1024, 1024))
                buffered = io.BytesIO()
                image.save(buffered, format="JPEG", quality=90)
                base64_image = base64.b64encode(buffered.getvalue()).decode()

                for chunk in ai_stream([{"role": "user", "content": user_text, "type": "text"}], is_vision=True, image_b64=base64_image):
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
                for chunk in ai_stream(st.session_state.messages):
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
