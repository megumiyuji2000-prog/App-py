import streamlit as st
from groq import Groq

st.set_page_config(page_title="AI Gw", page_icon="⚡", layout="wide")

st.title("⚡ Chat AI Punya Gw")
st.caption("Powered by Groq + Streamlit | Deploy gratis di share.streamlit.io")

# Sidebar buat setting
with st.sidebar:
    st.header("Settings")
    model = st.selectbox(
        "Pilih Model", 
        ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"]
    )
    st.divider()
    st.markdown("Dibuat sama @username_lo")
    if st.button("Hapus Chat"):
        st.session_state.messages = []
        st.rerun()

# Init Groq client pake secrets
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Init chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Bro ada yang bisa gw bantu?"}]

# Tampilin chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ketik pesan lo disini..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=model,
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
