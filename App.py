import streamlit as st
from groq import Groq
from huggingface_hub import InferenceClient
import time
import io
from PIL import Image

# Config halaman
st.set_page_config(
    page_title="Fanilla AI",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS biar mirip Meta AI
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
  .stChatMessage[data-testid="user-message"] {
        background-color: #7C3AED!important;
    }
  .stChatMessage[data-testid="assistant-message"] {
        background-color: #1F2937!important;
    }
  .stChatInput > div {
        background-color: #374151;
        border-radius: 24px;
    }
  .fanilla-title {
        background: linear-gradient(90deg, #7C3AED, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
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

# Header
st.markdown('<p class="fanilla-title">✨ Fanilla AI</p>', unsafe_allow_html=True)
st.markdown('<p class="fanilla-caption">Chat + Generate Gambar | Powered by Llama 3 & Stable Diffusion</p>', unsafe_allow_html=True)

# Init clients
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
hf_client = InferenceClient(token=st.secrets["HF_TOKEN"])

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hai bro! Gw Fanilla AI 💜\n\nGw bisa diajak ngobrol + buatin gambar juga lho.\n\n**Cara pake:**\n1. Chat biasa: `Jelasin black hole dong`\n2. Bikin gambar: `/gambar astronot lagi ngopi di bulan` \n\nCoba aja!"}
    ]

# Fungsi generate gambar
def generate_image(prompt):
    try:
        image = hf_client.text_to_image(
            prompt,
            model="stabilityai/stable-diffusion-xl-base-1.0",
        )
        return image
    except Exception as e:
        return f"Error generate gambar: {str(e)}"

# Fungsi chat LLM
def generate_chat(messages):
    system_prompt = """Kamu adalah Fanilla AI, AI assistant yang friendly, pinter, dan agak playful.
    Kamu ngomong pake bahasa Indonesia santai kayak ke temen.
    Jawaban lo harus helpful, to the point, tapi tetep asik.
    Kalo user minta gambar tapi ga pake /gambar, arahin buat pake command /gambar.
    Kalo ga tau, bilang ga tau. Jangan sok formal."""
    
    stream = groq_client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            *[{"role": m["role"], "content": m["content"]} for m in messages if m["type"] == "text"]
        ],
        stream=True,
    )
    return stream

# Tampilin chat history
for msg in st.session_state.messages:
    avatar = "✨" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        if msg["type"] == "text":
            st.markdown(msg["content"])
        elif msg["type"] == "image":
            st.image(msg["content"], caption=msg["caption"])

# Contoh prompt kalo chat masih kosong
if len(st.session_state.messages) == 1:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💬 Tanya coding", use_container_width=True):
            prompt = "Bikinin fungsi Python buat cek bilangan prima"
            st.session_state.prompt_from_button = prompt
            st.rerun()
    with col2:
        if st.button("🎨 /gambar cyberpunk city", use_container_width=True):
            prompt = "/gambar kota cyberpunk malam hari, neon, hujan, 4k"
            st.session_state.prompt_from_button = prompt
            st.rerun()

# Handle input
prompt = st.chat_input("Tanya atau /gambar prompt lo...")
if "prompt_from_button" in st.session_state:
    prompt = st.session_state.prompt_from_button
    del st.session_state.prompt_from_button

if prompt:
    # Simpen pesan user
    st.session_state.messages.append({"role": "user", "content": prompt, "type": "text"})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Cek command /gambar
    if prompt.startswith("/gambar "):
        with st.chat_message("assistant", avatar="💜"):
            with st.spinner("Fanilla AI lagi ngelukis... 🎨"):
                image_prompt = prompt.replace("/gambar ", "")
                image = generate_image(image_prompt)
                
                if isinstance(image, str): # Kalo error
                    st.error(image)
                    st.session_state.messages.append({"role": "assistant", "content": image, "type": "text"})
                else:
                    st.image(image, caption=f"Hasil: {image_prompt}")
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": image, 
                        "type": "image", 
                        "caption": f"Hasil: {image_prompt}"
                    })
    
    # Kalo chat biasa
    else:
        with st.chat_message("assistant", avatar="💜"):
            message_placeholder = st.empty()
            full_response = ""
            try:
                stream = generate_chat(st.session_state.messages)
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
            except Exception as e:
                full_response = f"Waduh error bro: {e}\nCek API key Groq lo ya 💜"
                message_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response, "type": "text"})

# Sidebar
with st.sidebar:
    st.header("✨ Fanilla AI V2")
    st.markdown("**Fitur:**\n- Chat AI\n- Generate Gambar")
    if st.button("🔄 Mulai Obrolan Baru", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.caption("Command: `/gambar prompt lo`")
