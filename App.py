import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
from datetime import datetime
import pytz
from duckduckgo_search import DDGS

st.set_page_config(page_title="Fanilla AI - Bimbel", page_icon="🎓", layout="centered")

# ==================== CSS SUPER SIMPLE ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Fredoka', sans-serif; }
    #MainMenu, footer, header {visibility: hidden;}
  .main { background-color: #F0F8FF; }
  .block-container { padding-top: 2rem!important; padding-bottom: 7rem!important; max-width: 700px!important; }
  .main-title { text-align: center; font-size: 2.5rem; font-weight: 600; color: #4A90E2; margin-bottom: 0.5rem; }
  .subtitle { text-align: center; color: #555; font-size: 1rem; margin-bottom: 2rem; }
  .stChatMessage { background-color: transparent!important; padding: 1rem 0!important; }
    [data-testid="stChatMessageContent"] { background-color: white!important; border-radius: 20px!important; padding: 1rem!important; color: #333!important; line-height: 1.6; border: 2px solid #D1E8FF; font-size: 1.1rem; }
  .stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"] { background-color: #E3F2FD!important; border: 2px solid #4A90E2; }
  .stChatInput { position: fixed!important; bottom: 0!important; left: 0!important; right: 0!important; background: #F0F8FF!important; padding: 1rem!important; max-width: 700px!important; margin: 0 auto!important; }
  .stChatInput > div { background-color: white!important; border: 3px solid #4A90E2!important; border-radius: 25px!important; }
  .stButton button { background-color: #4A90E2!important; color: white!important; border: none!important; border-radius: 15px!important; font-size: 1.2rem!important; padding: 0.75rem!important; font-weight: 600!important; }
  .stImage img { border-radius: 15px!important; border: 3px solid #D1E8FF; }
  .level-button { font-size: 1rem!important; }
</style>
""", unsafe_allow_html=True)

# ==================== INIT ====================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    st.error("❌ Kunci API belum dipasang. Minta tolong orang dewasa pasang di Settings > Secrets ya!")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "level" not in st.session_state:
    st.session_state.level = "SD" # Default
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# ==================== FUNGSI INTI ====================
def search_web(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=2))
            if results:
                return "\n".join([r['body'] for r in results])
    except:
        return ""
    return ""

def get_level_prompt(level):
    prompts = {
        "TK": "Kamu guru TK. Jelaskan pake bahasa bocil banget, analogi mainan/dongeng, banyak emoji 🧸🎈. 2-3 kalimat aja. Contoh: Matahari itu kayak bola lampu gede di langit ☀️",
        "SD": "Kamu guru SD. Bahasa sederhana, contoh dari rumah/sekolah. Jelaskan per poin singkat. Pake emoji 🍎📚",
        "SMP": "Kamu guru SMP. Jelaskan konsep + kasih 1 rumus dasar + 1 contoh soal + cara jawabnya.",
        "SMA": "Kamu guru SMA. Step-by-step, rumus lengkap pake $LaTeX$, kasih 2 soal latihan HOTS. Bahasa semi-formal.",
        "S1": "Kamu dosen S1. Jawab formal, struktur jelas, kasih referensi atau code jika perlu. Bahasa akademik.",
        "S2": "Kamu dosen S2. Analisis kritis, bandingkan 2 teori, sebutkan research gap atau kebaruan.",
        "S3": "Kamu profesor S3. Level expert. Buat hipotesis, metodologi, novelty. Istilah teknis semua."
    }
    return prompts[level]

def jawab_soal(prompt_text, image=None):
    level = st.session_state.level
    level_instruction = get_level_prompt(level)

    # Auto search buat fakta
    if any(word in prompt_text.lower() for word in ["apa", "kenapa", "bagaimana", "jelaskan", "hitung", "rumus"]):
        with st.spinner("Fanilla lagi buka buku... 📚"):
            fakta = search_web(prompt_text)
            if fakta:
                prompt_text += f"\n\n[INFO DARI BUKU]:\n{fakta}"

    tz = pytz.timezone('Asia/Jakarta')
    tanggal = datetime.now(tz).strftime("%d %B %Y")

    system_prompt = f"""Kamu adalah Fanilla AI, guru pinter dari TK sampai S3. Tanggal {tanggal}.
MISI: "Fantastic Question, As Simple As The Answer"

ATURAN MENGAJAR UNTUK TINGKAT {level}:
1. {level_instruction}
2. WAJIB BENAR 100%. Jika matematika, TUNJUKKAN CARA HITUNG step-by-step.
3. Jika ada gambar soal, baca soalnya dulu baru jawab.
4. Jika soal ga jelas, tanya balik: "Soalnya buat {level} kan? Boleh lebih detail?"
5. Kasih semangat di akhir: "Kamu pasti bisa!" atau "Semangat belajarnya!"
6. Jangan pernah bilang "tidak tahu". Cari cara jawabnya."""

    full_prompt = f"{system_prompt}\n\nSoal dari murid: {prompt_text}"

    try:
        if image:
            st.toast("Fanilla lagi lihat gambar soal... 🔍", icon="🎓")
            response = st.session_state.chat.send_message([full_prompt, image], stream=True)
        else:
            st.toast("Fanilla lagi mikir... 🧠", icon="🎓")
            response = st.session_state.chat.send_message(full_prompt, stream=True)

        for chunk in response:
            if chunk.text:
                yield chunk.text
    except:
        yield "Aduh, Fanilla capek 😴 Coba lagi 1 menit ya. Kuota harian abis."

# ==================== UI UTAMA ====================
st.markdown('<div class="main-title">🎓 Fanilla AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Guru AI dari TK sampai S3<br>Tanya apa aja, atau foto soalmu!</div>', unsafe_allow_html=True)

# TOMBOL PILIH TINGKATAN - SUPER SIMPLE
st.markdown("**Pilih Kelasmu:**")
cols = st.columns(7)
levels = ["TK", "SD", "SMP", "SMA", "S1", "S2", "S3"]
for i, lvl in enumerate(levels):
    with cols[i]:
        if st.button(lvl, key=lvl, use_container_width=True):
            st.session_state.level = lvl
            st.toast(f"Mode {lvl} aktif!", icon="✅")
            st.rerun()

st.info(f"**Mode Aktif: {st.session_state.level}** - Fanilla akan jawab sesuai kelasmu.", icon="🎯")
st.markdown("---")

# TAMPILKAN CHAT
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["type"] == "image":
            st.image(msg["content"], caption=msg.get("caption"))
        else:
            st.markdown(msg["content"])

# INPUT CHAT
prompt = st.chat_input(
    f"Tanya Fanilla buat {st.session_state.level}...",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"]
)

if prompt:
    # JIKA ADA GAMBAR
    if prompt.get("files"):
        image = Image.open(prompt["files"][0])
        user_text = prompt.get("text", f"Tolong kerjain soal ini buat {st.session_state.level}")

        st.session_state.messages.append({"role": "user", "content": image, "type": "image", "caption": user_text})
        with st.chat_message("user"):
            st.image(image, caption=user_text)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            for chunk in jawab_soal(user_text, image=image):
                full_response += chunk
                placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response, "type": "text"})

    # JIKA HANYA TEKS
    elif prompt.get("text"):
        user_text = prompt["text"]
        st.session_state.messages.append({"role": "user", "content": user_text, "type": "text"})
        with st.chat_message("user"):
            st.markdown(user_text)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            for chunk in jawab_soal(user_text):
                full_response += chunk
                placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response, "type": "text"})

    st.rerun()
