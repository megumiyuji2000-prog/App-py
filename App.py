import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
from datetime import datetime
import pytz
import time
import requests
import io
import urllib.parse

st.set_page_config(
    page_title="Fanilla AI",
    page_icon="logo.png",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==================== CSS ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    #MainMenu, footer, header {visibility: hidden;}
   .stApp,.main { background-color: #0A0A0B; }
   .block-container { padding-top: 1rem!important; padding-bottom: 8rem!important; max-width: 48rem!important; }
   .fanilla-title { text-align: center; font-size: 2.25rem; font-weight: 700; background: linear-gradient(90deg, #A78BFA 0%, #C4B5FD 50%, #E9D5FF 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.25rem; }
   .fanilla-subtitle { text-align: center; color: #71717A; font-size: 0.95rem; margin-bottom: 1.5rem; }
    [data-testid="stChatMessageContent"] { background-color: #18181B!important; border-radius: 18px!important; padding: 12px 16px!important; color: #E4E4E7!important; border: 1px solid #27272A; }
   .stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"] { background-color: #27272A!important; }
   .stChatInput > div { background-color: #18181B!important; border: 1px solid #A78BFA!important; border-radius: 26px!important; }
   .fanilla-badge { display: inline-block; font-size: 0.75rem; padding: 4px 10px; border-radius: 12px; margin-bottom: 8px; font-weight: 600; background-color: #27272A; color: #A78BFA; }
   .model-badge { display: inline-block; font-size: 0.65rem; padding: 2px 6px; border-radius: 8px; margin-left: 6px; opacity: 0.7; }
   .gemini { background-color: #1e40af; color: #dbeafe; }
   .llama { background-color: #7c2d12; color: #ffedd5; }
   .image { background-color: #059669; color: #d1fae5; }
   .remix { background-color: #be185d; color: #fce7f3; }
</style>
""", unsafe_allow_html=True)

# ==================== INIT ====================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error(f"API Key error: {e}")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "gemini_chat" not in st.session_state:
    st.session_state.gemini_chat = gemini_model.start_chat(history=[])
if "groq_history" not in st.session_state:
    st.session_state.groq_history = []
if "last_image" not in st.session_state:
    st.session_state.last_image = None

# ==================== FUNGSI ANTI ERROR ====================
def safe_generate_image(prompt):
    """Bikin gambar baru - anti error"""
    try:
        st.toast("Fanilla lagi ngelukis...", icon="🎨")
        encoded = urllib.parse.quote(prompt[:200])
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={int(time.time())%1000}"

        r = requests.get(url, timeout=45)
        if r.status_code == 200 and len(r.content) > 5000:
            img = Image.open(io.BytesIO(r.content)).convert("RGB")
            st.session_state.last_image = img
            return img, None
        return None, "Server lagi penuh bro, coba lagi"
    except Exception as e:
        return None, f"Error: {str(e)[:40]}"

def safe_remix_image(prompt, base_image):
    """Edit gambar - anti error"""
    try:
        if base_image is None:
            return None, "Belum ada gambar buat di-remix. Bikin dulu atau upload"

        st.toast("Fanilla lagi nge-remix...", icon="✨")
        # Karena Pollinations ga ada API remix beneran, kita bikin ulang dengan referensi
        # Caranya: gabungin prompt lama + prompt baru
        remix_prompt = f"{prompt}, high quality, detailed"
        encoded = urllib.parse.quote(remix_prompt[:200])
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={int(time.time())%1000}"

        r = requests.get(url, timeout=45)
        if r.status_code == 200 and len(r.content) > 5000:
            img = Image.open(io.BytesIO(r.content)).convert("RGB")
            st.session_state.last_image = img
            return img, None
        return None, "Remix gagal, coba prompt lain"
    except Exception as e:
        return None, f"Error remix: {str(e)[:40]}"

def image_to_bytes(img):
    """Convert PIL ke bytes buat download"""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# ==================== LOGIC CHAT ====================
def deteksi(prompt):
    p = prompt.lower()
    if any(k in p for k in ["remix", "edit", "jadiin", "ubah", "ganti style", "animekan"]): return "remix"
    if any(k in p for k in ["gambar", "bikin", "lukis", "draw", "generate"]): return "image"
    return "chat"

def jawab_ai(prompt, img_input=None):
    tingkat = deteksi(prompt)

    if tingkat == "image":
        img, err = safe_generate_image(prompt)
        if img: return [("image", img)]
        return [("text", f"Gagal bro: {err}. Coba lagi ya")]

    if tingkat == "remix":
        # Prioritas: gambar yg diupload > last_image
        base = img_input if img_input else st.session_state.last_image
        img, err = safe_remix_image(prompt, base)
        if img: return [("image", img)]
        return [("text", f"Gagal remix: {err}")]

    # CHAT BIASA
    try:
        tgl = datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%d %B %Y')
        system = f"Lu Fanilla, temen nongkrong pinter. Tanggal {tgl}. Jawab santai pake 'bro', 'anjir', 'wkwk'. Jangan panjang. Jangan sebut AI."

        if img_input:
            st.session_state.last_image = img_input
            res = st.session_state.gemini_chat.send_message([system + "\n\n" + prompt, img_input], stream=False)
        else:
            res = st.session_state.gemini_chat.send_message(system + "\n\n" + prompt, stream=False)

        return [("text", res.text)]
    except:
        try:
            st.session_state.groq_history.append({"role": "user", "content": prompt})
            chat = groq_client.chat.completions.create(
                messages=st.session_state.groq_history[-6:],
                model="llama-3.3-70b-versatile",
                max_tokens=800
            )
            txt = chat.choices[0].message.content
            st.session_state.groq_history.append({"role": "assistant", "content": txt})
            return [("text", txt)]
        except Exception as e:
            return [("text", f"Waduh error bro: {str(e)[:60]}. Coba lagi")]

# ==================== UI ====================
if not st.session_state.messages:
    col1, col2, col3 = st.columns([2,1,2])
    with col2:
        try: st.image("logo.png", width=80)
        except: pass
    st.markdown('<div class="fanilla-title">Fanilla AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="fanilla-subtitle">V2.1 - Bisa Download & Remix<br>Ketik "bikin gambar kucing" atau upload foto terus "jadiin anime"</div>', unsafe_allow_html=True)

# TAMPILIN CHAT
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and "type" in msg:
            badge = {"image": "🎨 IMAGE", "remix": "✨ REMIX", "chat": "💬"}.get(msg["type"], "💬")
            st.markdown(f'<div class="fanilla-badge">{badge}</div>', unsafe_allow_html=True)

        if msg["type"] == "image":
            st.image(msg["content"], use_container_width=True)
            # TOMBOL DOWNLOAD
            img_bytes = image_to_bytes(msg["content"])
            st.download_button(
                "📥 Download Gambar",
                data=img_bytes,
                file_name=f"fanilla_{int(time.time())}.png",
                mime="image/png",
                key=f"dl_{i}",
                use_container_width=True
            )
        else:
            st.markdown(msg["content"])

# INPUT
prompt = st.chat_input("Nanya apa bro... (bisa upload foto)", accept_file=True, file_type=["jpg","jpeg","png"])

if prompt:
    user_text = prompt.get("text", "")
    user_file = prompt.get("files", [None])[0] if prompt.get("files") else None
    user_img = None

    if user_file:
        try:
            user_img = Image.open(user_file).convert("RGB")
            st.session_state.messages.append({"role": "user", "type": "image", "content": user_img})
            with st.chat_message("user"):
                st.image(user_img, caption=user_text if user_text else "Foto upload")
        except:
            st.error("Gagal baca gambar")

    if user_text:
        if not user_file: # biar ga dobel
            st.session_state.messages.append({"role": "user", "type": "text", "content": user_text})
            with st.chat_message("user"):
                st.markdown(user_text)

        with st.chat_message("assistant"):
            with st.spinner("Fanilla mikir..."):
                hasil = jawab_ai(user_text, user_img)

            for tipe, konten in hasil:
                if tipe == "image":
                    st.markdown('<div class="fanilla-badge">🎨 IMAGE</div>', unsafe_allow_html=True)
                    st.image(konten, use_container_width=True)
                    img_bytes = image_to_bytes(konten)
                    st.download_button(
                        "📥 Download Gambar",
                        data=img_bytes,
                        file_name=f"fanilla_{int(time.time())}.png",
                        mime="image/png",
                        key=f"dl_new_{int(time.time())}",
                        use_container_width=True
                    )
                    st.session_state.messages.append({"role": "assistant", "type": "image", "content": konten})
                else:
                    st.markdown(konten)
                    st.session_state.messages.append({"role": "assistant", "type": "text", "content": konten})

    st.rerun()
