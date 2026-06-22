import streamlit as st
from groq import Groq
from huggingface_hub import InferenceClient
from PIL import Image
import time
import base64
import io

# ==================== CONFIG & STYLE ====================
st.set_page_config(
    page_title="Fanilla AI",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
   .main.block-container {padding-top: 2rem; padding-bottom: 5rem; max-width: 800px;}
   .stChatMessage[data-testid="stChatMessage"] {background-color: transparent!important;}
    [data-testid="user-message"] {background-color: #7C3AED!important;}
    [data-testid="assistant-message"] {background-color: #1F2937!important;}
   .stChatInput > div {background-color: #374151; border-radius: 24px; border: 1px solid #4B5563;}
   .fanilla-title {
        background: linear-gradient(90deg, #A855F7, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem; font-weight: 800; text-align: center; margin-bottom: 0px;
    }
   .fanilla-caption {text-align: center; color: #9CA3AF; margin-bottom: 2rem;}
   .image-note {font-size: 0.8rem; color: #9CA3AF; text-align: center; margin-top: 8px; font-style: italic;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="fanilla-title">✨ Fanilla AI</p>', unsafe_allow_html=True)
st.markdown('<p class="fanilla-caption">Chat | Generate | Vision - Dipisah Biar Rapi</p>', unsafe_allow_html=True)

# ==================== INIT CLIENTS ====================
if "GROQ_API_KEY" not in st.secrets:
    st.error("GROQ_API_KEY belum diset di Secrets bro!")
    st.stop()

groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
hf_client = InferenceClient(token=st.secrets.get("HF_TOKEN"))

# ==================== SESSION STATE ====================
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Hai bro! Gw Fanilla AI V6 ✨\n\n**3 Mode Gw:**\n1. **Chat**: Ngobrol biasa\n2. **/gambar**: Bikin gambar + pilih style\n3. **Upload foto**: Gw bisa liatin + jelasin\n\nCoba salah satu bro!",
        "type": "text"
    }]
if "mode" not in st.session_state:
    st.session_state.mode = "idle" # idle, style_select, generating_image

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

# ==================== FUNGSI HELPER ====================
def encode_image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

# ==================== OTAK 1: NGOBROL BIASA ====================
def chat_biasa():
    system_prompt = """Kamu adalah Fanilla AI, AI assistant yang friendly, pinter, dan agak playful.
    Kamu ngomong pake bahasa Indonesia santai kayak ke temen. Jawaban lo harus helpful, to the point, tapi tetep asik.
    Kalo user minta gambar tapi ga pake /gambar, arahin buat pake command /gambar.
    Kalo ga tau, bilang ga tau. Jangan bahas gambar yang diupload user karena ini mode chat biasa."""

    # History khusus text doang, biar ga error 400
    history = [{"role": "system", "content": system_prompt}]
    for m in st.session_state.messages:
        if m.get("type") == "text":
            history.append({"role": m["role"], "content": m["content"]})
        elif m.get("type") == "user_image":
            history.append({"role": "user", "content": f"[User pernah upload gambar dengan caption: {m.get('prompt', '')}]"})

    stream = groq_client.chat.completions.create(model=MODEL_CHAT, messages=history, stream=True)
    return stream

# ==================== OTAK 2: MELIHAT GAMBAR ====================
def chat_vision(image, prompt):
    system_prompt = """Kamu adalah Fanilla AI dengan kemampuan vision. Kamu bisa melihat gambar yang diupload user.
    Jawab pertanyaan tentang gambar dengan detail, santai, dan helpful kayak ngobrol sama temen.
    Kalo ditanya harga barang dari foto, kasih estimasi harga pasaran + disclaimer kalo itu cuma perkiraan.
    Kalo ga yakin, bilang aja ga yakin."""

    base64_image = encode_image_to_base64(image)

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
        }
    ]

    stream = groq_client.chat.completions.create(model=MODEL_VISION, messages=messages, stream=True)
    return stream

# ==================== OTAK 3: BIKIN GAMBAR ====================
def generate_image(prompt, style="Realistic"):
    if not st.secrets.get("HF_TOKEN"):
        return "Error: HF_TOKEN belum diset di Secrets bro."
    try:
        style_text = STYLE_PROMPTS.get(style, STYLE_PROMPTS["Realistic"])
        enhanced_prompt = f"{prompt}, {style_text}"
        negative_prompt = "multiple, duplicate, blurry, low quality, distorted, deformed, ugly, bad anatomy, watermark, text, signature, worst quality, jpeg artifacts, cropped, out of frame"

        image = hf_client.text_to_image(
            enhanced_prompt,
            model=MODEL_IMAGE,
            negative_prompt=negative_prompt,
        )
        return image
    except Exception as e:
        return f"Gagal bikin gambar bro: {str(e)}. Server Hugging Face lagi rame, coba lagi 30 detik."

# ==================== RENDER CHAT HISTORY ====================
for msg in st.session_state.messages:
    avatar = "✨" if msg["role"] == "assistant" else "🧑‍💻"
    with st.chat_message(msg["role"], avatar=avatar):
        if msg.get("type") == "image_generated":
            st.image(msg["content"], caption=msg.get("caption", ""))
            st.markdown('<p class="image-note">Note: maaf bila gambar yang dihasilkan tidak memuaskan 🙏</p>', unsafe_allow_html=True)
        elif msg.get("type") == "user_image":
            st.image(msg["content"], caption=msg.get("prompt", "Gambar yang diupload"))
        else:
            st.markdown(msg["content"])

# ==================== LOGIKA UTAMA - PEMISAHAN MODE ====================

# MODE 1: LAGI GENERATE GAMBAR
if st.session_state.mode == "generating_image":
    with st.chat_message("assistant", avatar="✨"):
        with st.spinner(f"Fanilla lagi ngelukis style {st.session_state.selected_style}... 🎨"):
            result = generate_image(st.session_state.image_prompt, st.session_state.selected_style)
            if isinstance(result, str):
                st.error(result)
                st.session_state.messages.append({"role": "assistant", "content": result, "type": "text"})
            else:
                caption = f"Prompt: {st.session_state.image_prompt} | Style: {st.session_state.selected_style}"
                st.image(result, caption=caption)
                st.markdown('<p class="image-note">Note: maaf bila gambar yang dihasilkan tidak memuaskan 🙏</p>', unsafe_allow_html=True)
                st.session_state.messages.append({
                    "role": "assistant", "content": result, "type": "image_generated", "caption": caption
                })
    st.session_state.mode = "idle"
    st.rerun()

# MODE 2: LAGI PILIH STYLE GAMBAR
if st.session_state.mode == "style_select":
    with st.chat_message("assistant", avatar="✨"):
        st.markdown("Pilih style gambarnya bro:")
        cols = st.columns(len(STYLE_PROMPTS))
        for i, style_name in enumerate(STYLE_PROMPTS.keys()):
            if cols[i].button(style_name, key=f"style_{style_name}", use_container_width=True):
                st.session_state.selected_style = style_name
                st.session_state.mode = "generating_image"
                st.rerun()

# MODE 3: IDLE - NUNGGU INPUT USER
if st.session_state.mode == "idle":
    prompt = st.chat_input("Ketik pesan, /gambar, atau upload foto...", accept_file=True, file_type=["jpg", "jpeg", "png"])

    if prompt:
        # SUB-MODE 3A: USER UPLOAD GAMBAR -> PAKE OTAK VISION
        if prompt.get("files"):
            uploaded_file = prompt["files"][0]
            image = Image.open(uploaded_file)
            user_text = prompt.get("text", "Jelaskan gambar ini dong")

            st.session_state.messages.append({"role": "user", "content": image, "type": "user_image", "prompt": user_text})

            with st.chat_message("user", avatar="🧑‍💻"):
                st.image(image, caption=user_text)

            with st.chat_message("assistant", avatar="✨"):
                placeholder = st.empty()
                full_response = ""
                try:
                    with st.spinner("Fanilla lagi ngeliat gambarnya... 👁️"):
                        stream = chat_vision(image, user_text) # PAKE OTAK VISION
                        for chunk in stream:
                            if chunk.choices[0].delta.content:
                                full_response += chunk.choices[0].delta.content
                                placeholder.markdown(full_response + "▌")
                        placeholder.markdown(full_response)
                except Exception as e:
                    full_response = f"Waduh error bro: {e}"
                    placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response, "type": "text"})
            st.rerun()

        # SUB-MODE 3B: USER CHAT TEKS
        elif prompt.get("text"):
            user_text = prompt["text"]
            st.session_state.messages.append({"role": "user", "content": user_text, "type": "text"})

            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(user_text)

            # CEK APAKAH MAU BIKIN GAMBAR
            if user_text.startswith("/gambar "):
                st.session_state.image_prompt = user_text.replace("/gambar ", "")
                st.session_state.mode = "style_select" # PINDAH KE MODE PILIH STYLE
                st.rerun()
            else:
                # PAKE OTAK NGOBROL BIASA
                with st.chat_message("assistant", avatar="✨"):
                    placeholder = st.empty()
                    full_response = ""
                    try:
                        stream = chat_biasa() # PAKE OTAK CHAT BIASA
                        for chunk in stream:
                            if chunk.choices[0].delta.content:
                                full_response += chunk.choices[0].delta.content
                                placeholder.markdown(full_response + "▌")
                        placeholder.markdown(full_response)
                    except Exception as e:
                        full_response = f"Waduh error bro: {e}"
                        placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response, "type": "text"})
                st.rerun()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("✨ Fanilla AI V6")
    st.markdown(f"**Chat:** `{MODEL_CHAT}`\n**Vision:** `{MODEL_VISION}`\n**Image:** `SD3-Medium`")
    if st.button("🔄 New Chat", use_container_width=True):
        st.session_state.messages = [{
            "role": "assistant", "content": "Sip, obrolan baru bro! Mau ngapain? ✨", "type": "text"
        }]
        st.session_state.mode = "idle"
        st.rerun()
    st.divider()
    st.caption("Mode dipisah biar ga error:\n1. Chat biasa\n2. `/gambar` + style\n3. Upload foto")
