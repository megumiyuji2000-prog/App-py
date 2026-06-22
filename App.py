import streamlit as st
import google.generativeai as genai
from PIL import Image
import time, io
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

# ==================== INIT GEMINI 2.5 ====================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash') # MODEL TERBARU PALING GACOR
except Exception as e:
    st.error(f"GEMINI_API_KEY Error: {e}. Cek Secrets")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False
if "user_style" not in st.session_state:
    st.session_state.user_style = "santai"
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

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

def ai_stream_gemini(prompt_text, image=None):
    """V14.1 GEMINI 2.5 FLASH - 1500 REQ/HARI"""

    st.session_state.user_style = detect_user_style(prompt_text)

    # AUTO SEARCH BUAT FAKTA
    user_lower = prompt_text.lower()
    need_search = any(word in user_lower for word in [
        "apa itu", "bagaimana", "kenapa", "jelaskan", "definisi", "fakta",
        "hari ini", "terbaru", "sekarang", "harga", "berita", "2025", "2026", "skor",
        "pasir hisap", "siapa", "kapan", "dimana", "sejarah", "tinggi", "rating"
    ])

    if need_search and not image:
        with st.spinner("🔍 Cek fakta..."):
            search_result = search_web(prompt_text)
            prompt_text += f"\n\n[FAKTA DARI WEB]:\n{search_result}"

    tz = pytz.timezone('Asia/Jakarta')
    date_now = datetime.now(tz).strftime("%d %B %Y")

    # SYSTEM PROMPT V14.1
    if st.session_state.user_style == "santai":
        system_prompt = f"""Kamu Fanilla AI dari FNL. Tanggal {date_now}.
ATURAN:
1. Jawab FAKTA SAINS. Cek ejaan.
2. Pake data [FAKTA DARI WEB] kalo ada.
3. Gaya santai: 'bro', 'lu', 'gw'. Max 3 kalimat.
4. Logo: kasih rating 1-10 + alasan singkat. Kalo logo FNL: 3 garis biru-putih-merah = growth/arrow naik. FNL = Future Network Legacy.
5. Pasir hisap: campuran pasir jenuh air. Densitas 2 g/cm³, manusia 1 g/cm³ jadi ngambang.
6. Jangan ngarang. Kalo ga tau bilang ga tau."""
    else:
        system_prompt = f"""Anda adalah Fanilla AI dari FNL. Tanggal {date_now}.
ATURAN:
1. Jawab FAKTA SAINS AKURAT. Periksa ejaan.
2. Gunakan data [FAKTA DARI WEB] jika ada.
3. Bahasa formal. Maksimal 3 kalimat.
4. Logo: berikan rating 1-10 + alasan. Jika logo FNL: tiga garis biru-putih-merah melambangkan pertumbuhan. FNL = Future Network Legacy.
5. Pasir hisap: campuran pasir jenuh air. Densitas ~2 g/cm³, manusia ~1 g/cm³ sehingga mengapung.
6. Jangan mengarang. Jika tidak tahu, sampaikan."""

    full_prompt = f"{system_prompt}\n\nUser: {prompt_text}"

    try:
        st.toast("Pake Gemini 2.5 Flash...", icon="⚡")

        # GEMINI HANDLE IMAGE + TEXT SEKALIGUS
        if image:
            response = st.session_state.chat.send_message([full_prompt, image], stream=True)
        else:
            response = st.session_state.chat.send_message(full_prompt, stream=True)

        full = ""
        for chunk in response:
            if chunk.text:
                full += chunk.text
                yield full

    except Exception as e:
        error = str(e)
        if "429" in error or "quota" in error.lower():
            yield "Limit Gemini 1500/hari abis bro 😭 Besok reset jam 7 pagi WIB. Atau topup di AI Studio kalo mau unlimited."
        elif "500" in error or "503" in error:
            yield "Server Gemini lagi overload bro. Coba 10 detik lagi."
        else:
            yield f"Error Gemini bro: {error}"

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### ✨ Fanilla AI")
    st.caption(f"Style: {st.session_state.user_style}")
    if st.button("🗑️ Hapus Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.user_style = "santai"
        st.session_state.chat = model.start_chat(history=[])
        st.rerun()
    st.markdown("---")
    st.caption("Model: Gemini 2.5 Flash")
    st.caption("Limit: 1500 req/hari")
    st.caption("Mode: Stable V14.1")
    st.caption("Fanilla AI © FNL 2026")

# ==================== MAIN ====================
if len(st.session_state.messages) == 0:
    st.markdown('<div class="main-title">Fanilla AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Powered by Google Gemini 2.5 Flash. Limit 1500 req/hari.</div>', unsafe_allow_html=True)

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
                for chunk in ai_stream_gemini(user_text, image=image):
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
                for chunk in ai_stream_gemini(user_text):
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
