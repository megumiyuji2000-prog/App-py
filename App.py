import streamlit as st
from groq import Groq
import time

# Config halaman
st.set_page_config(
    page_title="Fanilla AI",
    page_icon="💜",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS biar mirip Meta AI
st.markdown("""
<style>
    /* Hide streamlit default */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Main container */
   .main.block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 800px;
    }

    /* Chat bubble user */
   .stChatMessage[data-testid="user-message"] {
        background-color: #7C3AED!important;
    }

    /* Chat bubble AI */
   .stChatMessage[data-testid="assistant-message"] {
        background-color: #1F2937!important;
    }

    /* Input box */
   .stChatInput > div {
        background-color: #374151;
        border-radius: 24px;
    }

    /* Title gradient */
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
st.markdown('<p class="fanilla-title">💜 Fanilla AI</p>', unsafe_allow_html=True)
st.markdown('<p class="fanilla-caption">AI Assistant buatan lo, powered by Llama 3</p>', unsafe_allow_html=True)

# Init Groq
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hai bro! Gw Fanilla AI 💜\n\nAda yang bisa gw bantu hari ini? Tanya apa aja, ngobrol santai, atau minta bikinin kode juga bisa."}
    ]

# Tampilin chat history
for msg in st.session_state.messages:
    avatar = "💜" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Contoh prompt kalo chat masih kosong
if len(st.session_state.messages) == 1:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧠 Jelaskan relativitas Einstein", use_container_width=True):
            prompt = "Jelasin teori relativitas Einstein dengan bahasa yang gampang dimengerti anak SMA"
            st.session_state.prompt_from_button = prompt
            st.rerun()
    with col2:
        if st.button("💻 Bikinin kode Python", use_container_width=True):
            prompt = "Bikinin kode Python buat sorting data pake bubble sort + penjelasannya"
            st.session_state.prompt_from_button = prompt
            st.rerun()

# Handle input dari button atau chat_input
prompt = st.chat_input("Tanya Fanilla AI...")
if "prompt_from_button" in st.session_state:
    prompt = st.session_state.prompt_from_button
    del st.session_state.prompt_from_button

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant", avatar="💜"):
        message_placeholder = st.empty()
        full_response = ""

        # System prompt biar gayanya mirip Meta AI: helpful, warm, playful
        system_prompt = """Kamu adalah Fanilla AI, AI assistant yang friendly, pinter, dan agak playful.
        Kamu ngomong pake bahasa Indonesia santai kayak ke temen.
        Jawaban lo harus helpful, to the point, tapi tetep asik.
        Kalo ga tau, bilang ga tau. Jangan sok formal."""

        stream = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            ],
            stream=True,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
                message_placeholder.markdown(full_response + "▌")
                time.sleep(0.01)

        message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})

# Sidebar buat reset
with st.sidebar:
    st.header("💜 Fanilla AI")
    st.markdown("Versi 1.0")
    if st.button("🔄 Mulai Obrolan Baru", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.caption("Dibuat pake Streamlit + Groq")
