import streamlit as st
from groq import Groq
from huggingface_hub import InferenceClient
from PIL import Image
import time

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
st.markdown('<p class="fanilla-caption">Your AI bestie buat ngobrol & bikin gambar Pro</p>', unsafe_allow_html=True)

if "GROQ_API_KEY" not in st.secrets:
    st.error("GROQ_API_KEY belum diset di Secrets bro! Cek Settings > Secrets.")
    st.stop()

groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
hf_client = InferenceClient(token=st.secrets.get("HF_TOKEN"))

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hai bro! Gw Fanilla AI ✨\n\nSekarang gw udah pro bikin gambar. Pake `/gambar` terus pilih style ya!\n\n**Contoh:** `/gambar kucing astronot`",
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

def generate_image(prompt, style="Realistic"):
    if not st.secrets.get("HF_TOKEN"):
        return "Buat bikin gambar, lo harus set `HF_TOKEN` dulu di Secrets bro. Dapetin gratis di huggingface.co"
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
        return f"Gagal bikin gambar bro: {str(e)}. Server Hugging Face lagi rame, coba lagi 30 detik."

def generate_chat_response():
    system_prompt = """Kamu adalah Fanilla AI, AI assistant yang friendly, pinter, dan agak playful.
    Kamu ngomong pake bahasa Indonesia santai kayak ke temen.
    Jawaban lo harus helpful, to the point, tapi tetep asik.
    Kalo user minta gambar tapi ga pake /gambar, arahin buat pake command /gambar terus pilih style.
    Kalo ga tau, bilang ga tau."""

    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
        if m.get("type") == "text"
    ]

    stream = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": system_prompt}, *history],
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
        else:
            st.markdown(msg["content"])

# --- LOGIKA BARU: KALO LAGI PROSES GAMBAR ---
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

    # Reset state
    st.session_state.generating_image = False
    del st.session_state.selected_style
    del st.session_state.image_prompt
    st.rerun()

# --- INPUT USER ---
if prompt := st.chat_input("Ketik pesan atau /gambar..."):
    st.session_state.messages.append({"role": "user", "content": prompt, "type": "text"})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    if prompt.startswith("/gambar "):
        st.session_state.image_prompt = prompt.replace("/gambar ", "")
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
                full_response = f"Waduh error bro: {e}\nCoba cek API Key Groq lo di Secrets ya."
                placeholder.markdown(full_response)

            st.session_state.messages.append({"role": "assistant", "content": full_response, "type": "text"})

# --- TAMPILIN TOMBOL STYLE - UDAH DIBENERIN ---
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
    st.header("✨ Fanilla AI V4.1")
    st.markdown("**Model Chat:** Llama 3.3 70B\n**Model Image:** SD3-Medium")
    if st.button("🔄 New Chat", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "Sip, obrolan baru bro! Mau bikin gambar apa? ✨", "type": "text"}
        ]
        st.session_state.generating_image = False
        st.session_state.show_style_buttons = False
        st.rerun()
    st.divider()
    st.caption("Tips: `/gambar prompt lo` terus pilih style")
