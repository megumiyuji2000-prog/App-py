import streamlit as st
from groq import Groq
from huggingface_hub import InferenceClient
from PIL import Image
import time
import base64
import io

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
.main.block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 800px;
    }
.stChatMessage[data-testid="stChatMessage"] {
        background-color: transparent!important;
 }
 [data-testid="user-message"] {
        background-color: #7C3AED!important;
 }
 [data-testid="assistant-message"] {
        background-color: #1F2937!important;
 }
.stChatInput > div {
        background-color: #374151;
        border-radius: 24px;
        border: 1px solid #4B5563;
 }
.fanilla-title {
        background: linear-gradient(90deg, #A855F7, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0px;
 }
.fanilla-caption {
        text-align: center;
        color: #9CA3AF;
        margin-bottom: 2rem;
 }
.image-note {
        font-size: 0.8rem;
        color: #9CA3AF;
        text-align: center;
        margin-top: 8px;
        font-style: italic;
 }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="fanilla-title">✨ Fanilla AI</p>', unsafe_allow_html=True)
st.markdown('<p class="fanilla-caption">Chat, Bikin Gambar, & Liat Foto | Powered by Llama Vision</p>', unsafe_allow_html=True)

if "GROQ_API_KEY" not in st.secrets:
    st.error("GROQ_API_KEY belum diset di Secrets bro! Cek Settings > Secrets.")
    st.stop()

groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
hf_client = InferenceClient(token=st.secrets.get("HF_TOKEN"))

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hai bro! Gw Fanilla AI V5 ✨\n\nSekarang gw bisa:\n1. **Ngobrol** biasa\n2. **Bikin gambar** pake `/gambar`\n3. **Liat foto** yang lo upload 📷\n\nCoba upload gambar + tanya 'Ini gambar apa?'",
            "type": "text"
        }
    ]
if "generating_image" not in st.session_state:
    st.session_state.generating_image = False

STYLE_PROMPTS = {
    "Realistic": "photorealistic, 8k, ultra detailed, professional photography, sharp focus, cinematic lighting",
    "Anime": "anime style, studio ghibli, vibrant colors, detailed, key visual",
    "3D Render": "3d render, octane render, pixar style, unreal engine 5, detailed",
    "Fantasy Art": "fantasy art, epic, detailed, digital painting, artstation trending",
    "Cyberpunk": "cyberpunk, neon lights, futuristic, blade runner style, 4k"
}

def encode_image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

def generate_image(prompt, style="Realistic"):
    if not st.secrets.get("HF_TOKEN"):
        return "Buat bikin gambar, lo harus set `HF_TOKEN` dulu di Secrets bro."
    try:
        style_text = STYLE_PROMPTS.get(style, STYLE_PROMPTS["Realistic"])
        enhanced_prompt = f"{prompt}, {style_text}"
        negative_prompt = "multiple, duplicate, blurry, low quality, distorted, deformed, ugly, bad anatomy, watermark, text, signature, worst quality, jpeg artifacts, cropped, out of frame"
        image = hf_client.text_to_image(
            enhanced_prompt,
            model="stabilityai/stable-diffusion-3-medium-diffusers",
            negative_prompt=negative_prompt,
        )
        return image
    except Exception as e:
 m 
     return f"Gagal bikin gambar bro: {str(e)}. Server Hugging Face lagi rame, coba lagi 30 detik."
def generate_chat_response():
    system_prompt = """Kamu adalah Fanilla AI, AI assistant yang friendly, pinter, dan agak playful.
    Kamu ngomong pake bahasa Indonesia santai kayak ke temen.
    Kamu bisa melihat gambar yang diupload user. Jawab pertanyaan tentang gambar dengan detail.
    Kalo user nanya harga barang dari foto, kasih estimasi harga pasaran + disclaimer kalo itu cuma perkiraan.
    Kalo user minta gambar tapi ga pake /gambar, arahin buat pake command /gambar terus pilih style.
    Kalo ga tau, bilang ga tau."""

    messages_for_api = [{"role": "system", "content": system_prompt}]
    
    # CEK APAKAH PERTANYAAN TERAKHIR ADA GAMBAR
    last_user_msg = None
    for m in reversed(st.session_state.messages):
        if m["role"] == "user":
            last_user_msg = m
            break
    
    has_image_now = last_user_msg and last_user_msg.get("type") == "user_image"
    
    # --- FIX UTAMA: BIKIN 2 VERSI HISTORY ---
    for m in st.session_state.messages:
        if m.get("type") == "text":
            messages_for_api.append({"role": m["role"], "content": m["content"]})
        elif m.get("type") == "user_image":
            if has_image_now:
                # Kalo mode vision, masukin gambarnya
                base64_image = encode_image_to_base64(m["content"])
                messages_for_api.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": m.get("prompt", "Jelaskan gambar ini")},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                })
            else:
                # Kalo mode text biasa, ganti gambar jadi teks doang biar ga error
                messages_for_api.append({
                    "role": "user", 
                    "content": f"[User upload gambar] {m.get('prompt', '')}"
                })

    # PAKE LLAMA 4 SCOUT KALO ADA GAMBAR, KALO GA ADA PAKE 3.3 70B
    model = "meta-llama/llama-4-scout-17b-16e-instruct" if has_image_now else "llama-3.3-70b-versatile"

    stream = groq_client.chat.completions.create(
        model=model,
        messages=messages_for_api,
        stream=True,
    )
    return stream

# --- TAMPILIN CHAT ---
for msg in st.session_state.messages:
    avatar = "✨" if msg["role"] == "assistant" else "🧑‍💻"
    with st.chat_message(msg["role"], avatar=avatar):
        if msg.get("type") == "image":
            st.image(msg["content"], caption=msg.get("caption", ""))
            st.markdown('<p class="image-note">Note: maaf bila gambar yang dihasilkan tidak memuaskan 🙏</p>', unsafe_allow_html=True)
        elif msg.get("type") == "user_image":
            st.image(msg["content"], caption=msg.get("prompt", "Gambar yang diupload"))
        else:
            st.markdown(msg["content"])

# --- PROSES GENERATE GAMBAR ---
if st.session_state.generating_image:
    with st.chat_message("assistant", avatar="✨"):
        with st.spinner(f"Fanilla lagi ngelukis style {st.session_state.selected_style}... 🎨"):
            result = generate_image(st.session_state.image_prompt, st.session_state.selected_style)
            if isinstance(result, str):
                st.error(result)
                st.session_state.messages.append({"role": "assistant", "content": result, "type": "text"})
            else:
                st.image(result, caption=f"Prompt: {st.session_state.image_prompt} | Style: {st.session_state.selected_style}")
                st.markdown('<p class="image-note">Note: maaf bila gambar yang dihasilkan tidak memuaskan 🙏</p>', unsafe_allow_html=True)
                st.session_state.messages.append({
                    "role": "assistant", "content": result, "type": "image",
                    "caption": f"Prompt: {st.session_state.image_prompt} | Style: {st.session_state.selected_style}"
                })
    st.session_state.generating_image = False
    del st.session_state.selected_style
    del st.session_state.image_prompt
    st.rerun()

# --- INPUT USER + UPLOAD GAMBAR ---
prompt = st.chat_input("Ketik pesan, /gambar, atau upload foto...", accept_file=True, file_type=["jpg", "jpeg", "png"])

if prompt:
    if prompt.get("files"):
        # USER UPLOAD GAMBAR
        uploaded_file = prompt["files"][0]
        image = Image.open(uploaded_file)
        user_text = prompt.get("text", "Jelaskan gambar ini dong")

        st.session_state.messages.append({
            "role": "user",
            "content": image,
            "type": "user_image",
            "prompt": user_text
        })

        with st.chat_message("user", avatar="🧑‍💻"):
            st.image(image, caption=user_text)

        # LANGSUNG MINTA AI JELASIN
        with st.chat_message("assistant", avatar="✨"):
            placeholder = st.empty()
            full_response = ""
            try:
                with st.spinner("Fanilla lagi ngeliat gambarnya... 👁️"):
                    stream = generate_chat_response()
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            placeholder.markdown(full_response + "▌")
                    placeholder.markdown(full_response)
            except Exception as e:
                full_response = f"Waduh error bro: {e}"
                placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response, "type": "text"})

    elif prompt.get("text"):
        user_text = prompt["text"]
        st.session_state.messages.append({"role": "user", "content": user_text, "type": "text"})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(user_text)

        if user_text.startswith("/gambar "):
            st.session_state.image_prompt = user_text.replace("/gambar ", "")
            st.session_state.show_style_buttons = True
            st.rerun()
        else:
            with st.chat_message("assistant", avatar="✨"):
                placeholder = st.empty()
                full_response = ""
                try:
                    stream = generate_chat_response()
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            placeholder.markdown(full_response + "▌")
                    placeholder.markdown(full_response)
                except Exception as e:
                    full_response = f"Waduh error bro: {e}"
                    placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response, "type": "text"})

# --- TOMBOL STYLE ---
if st.session_state.get("show_style_buttons"):
    with st.chat_message("assistant", avatar="✨"):
        st.markdown("Pilih style gambarnya bro:")
        cols = st.columns(3)
        styles = list(STYLE_PROMPTS.keys())
        for i, style_name in enumerate(styles):
            if cols[i % 3].button(style_name, key=f"style_btn_{style_name}", use_container_width=True):
                st.session_state.selected_style = style_name
                st.session_state.generating_image = True
                st.session_state.show_style_buttons = False
                st.rerun()

# --- SIDEBAR ---
with st.sidebar:
    st.header("✨ Fanilla AI V5")
    st.markdown("**Model Chat:** Llama 3.3 70B\n**Model Vision:** Llama 3.2 11B\n**Model Image:** SD3-Medium")
    if st.button("🔄 New Chat", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "Sip, obrolan baru bro! Upload gambar atau bikin gambar baru? ✨", "type": "text"}
        ]
        st.session_state.generating_image = False
        st.session_state.show_style_buttons = False
        st.rerun()
    st.divider()
    st.caption("1. Upload foto + tanya\n2. `/gambar prompt` + pilih style")
