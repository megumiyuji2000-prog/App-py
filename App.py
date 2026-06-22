import streamlit as st
from groq import Groq
from huggingface_hub import InferenceClient
from PIL import Image
import time
import base64
import io
import uuid
from datetime import datetime

# ==================== CONFIG & STYLE ====================
st.set_page_config(
    page_title="Fanilla AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed" # BIARIN COLLAPSED, NANTI DIBUKA PAKE TOMBOL
)

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
 .main.block-container {padding-top: 1rem; padding-bottom: 5rem; max-width: 800px;}
 .stChatMessage[data-testid="stChatMessage"] {background-color: transparent!important;}
    [data-testid="user-message"] {background-color: #7C3AED!important;}
    [data-testid="assistant-message"] {background-color: #1F2937!important;}
 .stChatInput > div {background-color: #374151; border-radius: 24px; border: 1px solid #4B5563;}
 .fanilla-title {
        background: linear-gradient(90deg, #A855F7, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem; font-weight: 800; text-align: center; margin-bottom: 0px;
    }
 .fanilla-caption {text-align: center; color: #9CA3AF; margin-bottom: 1rem;}
 .image-note {font-size: 0.8rem; color: #9CA3AF; text-align: center; margin-top: 8px; font-style: italic;}
   /* Style buat list chat di sidebar */
    div[data-testid="stSidebarNav"] {display: none;}
 .stButton > button {
        width: 100%;
        border-radius: 12px;
        text-align: left;
        justify-content: flex-start;
        background-color: transparent;
        border: none;
        color: #D1D5DB;
    }
 .stButton > button:hover {
        background-color: #374151;
        color: white;
    }
 .stButton > button[kind="primary"] {
        background-color: #4B5563!important;
        color: white!important;
        font-weight: 600;
    }
   /* TOMBOL MENU BARU */
   .menu-button {
        position: fixed;
        top: 15px;
        left: 15px;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)

# ==================== TOMBOL MENU BUAT BUKA SIDEBAR ====================
if st.button("☰ Obrolan", key="menu_btn", help="Klik buat liat semua obrolan"):
    st.session_state.sidebar_open = not st.session_state.get("sidebar_open", False)

# ==================== INIT CLIENTS ====================
if "GROQ_API_KEY" not in st.secrets:
    st.error("GROQ_API_KEY belum diset di Secrets bro!")
    st.stop()

groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
hf_client = InferenceClient(token=st.secrets.get("HF_TOKEN"))

# ==================== SISTEM MULTI CHAT ====================
def buat_chat_baru():
    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {
        "title": "Obrolan Baru",
        "messages": [{
            "role": "assistant",
            "content": "Hai bro! Ada yang bisa gw bantu? ✨",
            "type": "text"
        }],
        "created_at": datetime.now()
    }
    st.session_state.active_chat_id = chat_id
    st.session_state.mode = "idle"

def ganti_judul_otomatis(chat_id):
    chat = st.session_state.chats[chat_id]
    if chat["title"] == "Obrolan Baru":
        for msg in chat["messages"]:
            if msg["role"] == "user" and msg.get("type") == "text":
                title = " ".join(msg["content"].split()[:4])
                chat["title"] = title[:30] + "..." if len(title) > 30 else title
                break

def hapus_chat(chat_id):
    if len(st.session_state.chats) > 1:
        del st.session_state.chats[chat_id]
        st.session_state.active_chat_id = list(st.session_state.chats.keys())[-1]
    else:
        buat_chat_baru()

if "chats" not in st.session_state:
    st.session_state.chats = {}
    buat_chat_baru()

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = list(st.session_state.chats.keys())[0]

if "mode" not in st.session_state:
    st.session_state.mode = "idle"

# ==================== KONSTANTA ====================
STYLE_PROMPTS = {
    "Realistic": "photorealistic, 8k, ultra detailed, professional photography, sharp focus, cinematic lighting",
    "Anime": "anime style, studio ghibli, vibrant colors, detailed, key visual",
    "3D Render": "3d render, octane render, pixar style, unreal engine 5, detailed",
    "Fantasy Art": "fantasy art, epic, detailed, digital painting, artstation trending",
    "Cyberpunk": "cyberpunk, neon lights, futuristic, blade runner style, 4k"
}

MODEL_CHAT = "llama-3.3-70b-versatile"
MODEL_VISION = "meta-llama/llama-4-scout-17b-16e-instruct"
MODEL_IMAGE = "stabilityai/stable-diffusion-3-medium-diffusers"

# ==================== FUNGSI OTAK AI ====================
def encode_image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

def chat_biasa(messages):
    system_prompt = """Kamu adalah Fanilla AI, AI assistant yang friendly, pinter, dan agak playful.
    Kamu ngomong pake bahasa Indonesia santai kayak ke temen. Jawaban lo harus helpful, to the point, tapi tetep asik.
    Kalo user minta gambar tapi ga pake /gambar, arahin buat pake command /gambar.
    Kalo ga tau, bilang ga tau."""
    history = [{"role": "system", "content": system_prompt}]
    for m in messages:
        if m.get("type") == "text":
            history.append({"role": m["role"], "content": m["content"]})
        elif m.get("type") == "user_image":
            history.append({"role": "user", "content": f"[User pernah upload gambar: {m.get('prompt', '')}]"})
    stream = groq_client.chat.completions.create(model=MODEL_CHAT, messages=history, stream=True)
    return stream

def chat_vision(image, prompt):
    system_prompt = """Kamu adalah Fanilla AI dengan kemampuan vision. Jawab pertanyaan tentang gambar dengan detail, santai, dan helpful.
    Kalo ditanya harga barang dari foto, kasih estimasi harga pasaran + disclaimer kalo itu cuma perkiraan."""
    base64_image = encode_image_to_base64(image)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]}
    ]
    stream = groq_client.chat.completions.create(model=MODEL_VISION, messages=messages, stream=True)
    return stream

def generate_image(prompt, style="Realistic"):
    if not st.secrets.get("HF_TOKEN"):
        return "Error: HF_TOKEN belum diset di Secrets bro."
    try:
        style_text = STYLE_PROMPTS.get(style, STYLE_PROMPTS["Realistic"])
        enhanced_prompt = f"{prompt}, {style_text}"
        negative_prompt = "multiple, duplicate, blurry, low quality, distorted, deformed, ugly, bad anatomy, watermark, text, signature, worst quality, jpeg artifacts, cropped, out of frame"
        image = hf_client.text_to_image(enhanced_prompt, model=MODEL_IMAGE, negative_prompt=negative_prompt)
        return image
    except Exception as e:
        return f"Gagal bikin gambar bro: {str(e)}. Server lagi rame, coba lagi 30 detik."

# ==================== SIDEBAR - SISTEM OBROLAN ====================
with st.sidebar:
    st.markdown("### ✨ Fanilla AI")
    if st.button("📝 Obrolan Baru", use_container_width=True, type="primary"):
        buat_chat_baru()
        st.rerun()
    st.divider()
    st.markdown("**Obrolan**")
    sorted_chats = sorted(st.session_state.chats.items(), key=lambda x: x[1]["created_at"], reverse=True)
    for chat_id, chat_data in sorted_chats:
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            if st.button(
                f"💬 {chat_data['title']}",
                key=f"chat_{chat_id}",
                use_container_width=True,
                type="primary" if chat_id == st.session_state.active_chat_id else "secondary"
            ):
                st.session_state.active_chat_id = chat_id
                st.session_state.mode = "idle"
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{chat_id}", help="Hapus obrolan"):
                hapus_chat(chat_id)
                st.rerun()
    st.divider()
    st.caption(f"Model: Llama 3.3 | Vision: Llama 4 Scout")

# ==================== AMBIL CHAT AKTIF ====================
active_chat = st.session_state.chats[st.session_state.active_chat_id]
messages = active_chat["messages"]

# ==================== TAMPILAN UTAMA ====================
st.markdown('<p class="fanilla-title">✨ Fanilla AI</p>', unsafe_allow_html=True)
st.markdown(f'<p class="fanilla-caption">{active_chat["title"]}</p>', unsafe_allow_html=True)

for msg in messages:
    avatar = "✨" if msg["role"] == "assistant" else "🧑‍💻"
    with st.chat_message(msg["role"], avatar=avatar):
        if msg.get("type") == "image_generated":
            st.image(msg["content"], caption=msg.get("caption", ""))
            st.markdown('<p class="image-note">Note: maaf bila gambar yang dihasilkan tidak memuaskan 🙏</p>', unsafe_allow_html=True)
        elif msg.get("type") == "user_image":
            st.image(msg["content"], caption=msg.get("prompt", "Gambar yang diupload"))
        else:
            st.markdown(msg["content"])

# ==================== LOGIKA MODE ====================
if st.session_state.mode == "generating_image":
    with st.chat_message("assistant", avatar="✨"):
        with st.spinner(f"Fanilla lagi ngelukis style {st.session_state.selected_style}... 🎨"):
            result = generate_image(st.session_state.image_prompt, st.session_state.selected_style)
            if isinstance(result, str):
                st.error(result)
                messages.append({"role": "assistant", "content": result, "type": "text"})
            else:
                caption = f"Prompt: {st.session_state.image_prompt} | Style: {st.session_state.selected_style}"
                st.image(result, caption=caption)
                st.markdown('<p class="image-note">Note: maaf bila gambar yang dihasilkan tidak memuaskan 🙏</p>', unsafe_allow_html=True)
                messages.append({"role": "assistant", "content": result, "type": "image_generated", "caption": caption})
    st.session_state.mode = "idle"
    ganti_judul_otomatis(st.session_state.active_chat_id)
    st.rerun()

if st.session_state.mode == "style_select":
    with st.chat_message("assistant", avatar="✨"):
        st.markdown("Pilih style gambarnya bro:")
        cols = st.columns(len(STYLE_PROMPTS))
        for i, style_name in enumerate(STYLE_PROMPTS.keys()):
            if cols[i].button(style_name, key=f"style_{style_name}", use_container_width=True):
                st.session_state.selected_style = style_name
                st.session_state.mode = "generating_image"
                st.rerun()

if st.session_state.mode == "idle":
    prompt = st.chat_input("Ketik pesan, /gambar, atau upload foto...", accept_file=True, file_type=["jpg", "jpeg", "png"])
    if prompt:
        if prompt.get("files"):
            uploaded_file = prompt["files"][0]
            image = Image.open(uploaded_file)
            user_text = prompt.get("text", "Jelaskan gambar ini dong")
            messages.append({"role": "user", "content": image, "type": "user_image", "prompt": user_text})
            with st.chat_message("user", avatar="🧑‍💻"):
                st.image(image, caption=user_text)
            with st.chat_message("assistant", avatar="✨"):
                placeholder = st.empty()
                full_response = ""
                try:
                    with st.spinner("Fanilla lagi ngeliat gambarnya... 👁️"):
                        stream = chat_vision(image, user_text)
                        for chunk in stream:
                            if chunk.choices[0].delta.content:
                                full_response += chunk.choices[0].delta.content
                                placeholder.markdown(full_response + "▌")
                        placeholder.markdown(full_response)
                except Exception as e:
                    full_response = f"Waduh error bro: {e}"
                    placeholder.markdown(full_response)
                messages.append({"role": "assistant", "content": full_response, "type": "text"})
            ganti_judul_otomatis(st.session_state.active_chat_id)
            st.rerun()
        elif prompt.get("text"):
            user_text = prompt["text"]
            messages.append({"role": "user", "content": user_text, "type": "text"})
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(user_text)
            if user_text.startswith("/gambar "):
                st.session_state.image_prompt = user_text.replace("/gambar ", "")
                st.session_state.mode = "style_select"
                st.rerun()
            else:
                with st.chat_message("assistant", avatar="✨"):
                    placeholder = st.empty()
                    full_response = ""
                    try:
                        stream = chat_biasa(messages)
                        for chunk in stream:
                            if chunk.choices[0].delta.content:
                                full_response += chunk.choices[0].delta.content
                                placeholder.markdown(full_response + "▌")
                        placeholder.markdown(full_response)
                    except Exception as e:
                        full_response = f"Waduh error bro: {e}"
                        placeholder.markdown(full_response)
                    messages.append({"role": "assistant", "content": full_response, "type": "text"})
                ganti_judul_otomatis(st.session_state.active_chat_id)
                st.rerun()
