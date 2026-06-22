import streamlit as st
from groq import Groq
from huggingface_hub import InferenceClient
from PIL import Image
import time

# --- 1. CONFIG HALAMAN ---
st.set_page_config(
    page_title="Fanilla AI",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS BIAR MIRIP META AI ---
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
</style>
""", unsafe_allow_html=True)

# --- 3. HEADER ---
st.markdown('<p class="fanilla-title">✨ Fanilla AI</p>', unsafe_allow_html=True)
st.markdown('<p class="fanilla-caption">Your AI bestie buat ngobrol & bikin gambar</p>', unsafe_allow_html=True)

# --- 4. INIT API CLIENTS ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("GROQ_API_KEY belum diset di Secrets bro! Cek Settings > Secrets.")
    st.stop()

groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
hf_client = InferenceClient(token=st.secrets.get("HF_TOKEN"))

# --- 5. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hai bro! Gw Fanilla AI ✨\n\nMau ngobrol atau bikin gambar? Bisa semua.\n\n**Coba ketik:**\n1. `Apa itu AI?`\n2. `/gambar astronot lagi main bola di Mars`",
            "type": "text"
        }
    ]

# --- 6. FUNGSI-FUNGSI UTAMA ---
def generate_image(prompt):
    if not st.secrets.get("HF_TOKEN"):
        return "Buat bikin gambar, lo harus set `HF_TOKEN` dulu di Secrets bro. Dapetin gratis di huggingface.co"
    try:
        image = hf_client.text_to_image(
            prompt,
            model="stabilityai/stable-diffusion-xl-base-1.0",
        )
        return image
    except Exception as e:
        return f"Gagal bikin gambar bro: {str(e)}. Mungkin servernya lagi sleep, coba lagi 20 detik."

def generate_chat_response():
    system_prompt = """Kamu adalah Fanilla AI, AI assistant yang friendly, pinter, dan agak playful.
    Kamu ngomong pake bahasa Indonesia santai kayak ke temen.
    Jawaban lo harus helpful, to the point, tapi tetep asik.
    Kalo user minta gambar tapi ga pake /gambar, arahin buat pake command /gambar.
    Kalo ga tau, bilang ga tau."""

    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
        if m.get("type") == "text"
    ]

    stream = groq_client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[{"role": "system", "content": system_prompt}, *history],
        stream=True,
    )
    return stream

# --- 7. TAMPILIN CHAT HISTORY - AVATAR UDAH DIGANTI ---
for msg in st.session_state.messages:
    avatar = "✨" if msg["role"] == "assistant" else "🧑‍💻"
    with st.chat_message(msg["role"], avatar=avatar):
        if msg.get("type") == "image":
            st.image(msg["content"], caption=msg.get("caption", ""))
        else:
            st.markdown(msg["content"])

# --- 8. CONTOH PROMPT ---
if len(st.session_state.messages) == 1:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💬 Jelaskan Quantum", use_container_width=True):
            st.session_state.prompt = "Jelasin quantum computing pake analogi yang gampang"
            st.rerun()
    with col2:
        if st.button("🎨 /gambar cat astronaut", use_container_width=True):
            st.session_state.prompt = "/gambar a cute cat astronaut on the moon, 4k, cinematic"
            st.rerun()

# --- 9. INPUT USER ---
if prompt := st.chat_input("Ketik pesan atau /gambar..."):
    st.session_state.prompt = prompt

if "prompt" in st.session_state:
    prompt = st.session_state.prompt
    del st.session_state.prompt

    st.session_state.messages.append({"role": "user", "content": prompt, "type": "text"})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    if prompt.startswith("/gambar "):
        with st.chat_message("assistant", avatar="✨"):
            with st.spinner("Fanilla lagi ngelukis... 🎨"):
                image_prompt = prompt.replace("/gambar ", "")
                result = generate_image(image_prompt)

                if isinstance(result, str):
                    st.error(result)
                    st.session_state.messages.append({"role": "assistant", "content": result, "type": "text"})
                else:
                    st.image(result, caption=f"Prompt: {image_prompt}")
                    st.session_state.messages.append({
                        "role": "assistant", "content": result, "type": "image", "caption": f"Prompt: {image_prompt}"
                    })
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

# --- 10. SIDEBAR ---
with st.sidebar:
    st.header("✨ Fanilla AI V3.1")
    st.markdown("**Model:** Llama 3.1 70B\n**Image:** SDXL")
    if st.button("🔄 New Chat", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "Sip, obrolan baru bro! Mau ngapain kita? ✨", "type": "text"}
        ]
        st.rerun()
    st.divider()
    st.caption("Tips: `/gambar prompt lo` buat generate gambar")
