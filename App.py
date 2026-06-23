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
import base64

st.set_page_config(page_title="Fanilla AI", page_icon="logo.png", layout="centered")

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
  .image { background-color: #059669; color: #d1fae5; }
  .remix { background-color: #be185d; color: #fce7f3; }
</style>
""", unsafe_allow_html=True)

# ==================== INIT ====================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    HF_TOKEN = st.secrets.get("HF_TOKEN")
except Exception as e:
    st.error(f"API Key error: {e}")
    st.stop()

if "messages" not in st.session_state: st.session_state.messages = []
if "last_image" not in st.session_state: st.session_state.last_image = None

# ==================== FUNGSI BENERAN ====================
def generate_gambar(prompt):
    """Bikin gambar baru dari teks"""
    try:
        st.toast("Fanilla lagi ngelukis...", icon="🎨")
        encoded = urllib.parse.quote(prompt[:200])
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={int(time.time())%1000}"
        r = requests.get(url, timeout=45)
        if r.status_code == 200:
            img = Image.open(io.BytesIO(r.content)).convert("RGB")
            st.session_state.last_image = img
            return img, None
        return None, "Server rame"
    except Exception as e:
        return None, str(e)[:50]

def remix_gambar_beneran(prompt, base_image):
    """EDIT GAMBAR BENERAN PAKE HF IMG2IMG"""
    if not HF_TOKEN:
        return None, "HF_TOKEN belum ada bro. Remix butuh ini"
    if base_image is None:
        return None, "Upload gambar dulu bro baru bisa remix"

    try:
        st.toast("Fanilla lagi nge-remix foto lu...", icon="✨")
        API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-refiner-1.0"

        # Convert image ke bytes
        buffered = io.BytesIO()
        base_image.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()

        # HF butuh base64
        img_b64 = base64.b64encode(img_bytes).decode()

        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {
            "inputs": prompt,
            "image": img_b64,
            "parameters": {"strength": 0.7} # 0.7 = 70% mirip asli, 30% berubah
        }

        r = requests.post(API_URL, headers=headers, json=payload, timeout=60)

        if r.status_code == 200:
            img = Image.open(io.BytesIO(r.content)).convert("RGB")
            st.session_state.last_image = img
            return img, None
        elif r.status_code == 503:
            return None, "Model lagi loading, coba 20 detik lagi"
        else:
            return None, f"Error HF: {r.status_code}"
    except Exception as e:
        return None, f"Error remix: {str(e)[:50]}"

def image_to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# ==================== LOGIC ====================
def deteksi(prompt):
    p = prompt.lower()
    if any(k in p for k in ["remix", "edit", "jadiin", "ubah", "ganti", "animekan", "kartun"]): return "remix"
    if any(k in p for k in ["gambar", "bikin", "lukis", "draw"]): return "image"
    return "chat"

def jawab_ai(prompt, img_input=None):
    tingkat = deteksi(prompt)

    if tingkat == "image":
        img, err = generate_gambar(prompt)
        if img: return [("image", img)]
        return [("text", f"Gagal: {err}")]

    if tingkat == "remix":
        base = img_input if img_input else st.session_state.last_image
        img, err = remix_gambar_beneran(prompt, base)
        if img: return [("image", img)]
        return [("text", f"Gagal remix: {err}")]

    # CHAT
    try:
        tgl = datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%d %B %Y')
        system = f"Lu Fanilla, temen nongkrong. Tanggal {tgl}. Jawab santai pake bro, anjir. Jangan panjang."
        if img_input:
            st.session_state.last_image = img_input
            res = gemini_model.generate_content([system + "\n\n" + prompt, img_input])
        else:
            res = gemini_model.generate_content(system + "\n\n" + prompt)
        return [("text", res.text)]
    except:
        try:
            chat = groq_client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
            return [("text", chat.choices[0].message.content)]
        except:
            return [("text", "Waduh error bro, coba lagi")]

# ==================== UI ====================
if not st.session_state.messages:
    st.markdown('<div class="fanilla-title">Fanilla AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="fanilla-subtitle">V2.2 - Remix Beneran<br>Upload foto → "jadiin anime" → Download</div>', unsafe_allow_html=True)

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            badge = "✨ REMIX" if msg["type"] == "image" and "remix" in str(msg.get("caption","")) else "🎨 IMAGE" if msg["type"] == "image" else "💬"
            st.markdown(f'<div class="fanilla-badge">{badge}</div>', unsafe_allow_html=True)

        if msg["type"] == "image":
            st.image(msg["content"], use_container_width=True)
            st.download_button("📥 Download", image_to_bytes(msg["content"]), f"fnl_{i}.png", "image/png", key=f"dl_{i}", use_container_width=True)
        else:
            st.markdown(msg["content"])

prompt = st.chat_input("Nanya apa bro... (bisa upload foto)", accept_file=True, file_type=["jpg","png","jpeg"])

if prompt:
    user_text = prompt.get("text", "")
    user_file = prompt.get("files", [None])[0] if prompt.get("files") else None
    user_img = None

    if user_file:
        user_img = Image.open(user_file).convert("RGB")
        st.session_state.messages.append({"role": "user", "type": "image", "content": user_img, "caption": user_text})
        with st.chat_message("user"):
            st.image(user_img, caption=user_text if user_text else "Upload")

    if user_text:
        if not user_file:
            st.session_state.messages.append({"role": "user", "type": "text", "content": user_text})
            with st.chat_message("user"): st.markdown(user_text)

        with st.chat_message("assistant"):
            with st.spinner("Fanilla mikir..."):
                hasil = jawab_ai(user_text, user_img)
            for tipe, konten in hasil:
                if tipe == "image":
                    st.markdown('<div class="fanilla-badge">✨ REMIX</div>', unsafe_allow_html=True)
                    st.image(konten, use_container_width=True)
                    st.download_button("📥 Download", image_to_bytes(konten), f"fnl_{int(time.time())}.png", "image/png", key=f"dl_{time.time()}", use_container_width=True)
                    st.session_state.messages.append({"role": "assistant", "type": "image", "content": konten, "caption": "remix"})
                else:
                    st.markdown(konten)
                    st.session_state.messages.append({"role": "assistant", "type": "text", "content": konten})
    st.rerun()
