import streamlit as st
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import pytz
from duckduckgo_search import DDGS
import re

st.set_page_config(page_title="Fanilla AI", page_icon="🎓", layout="centered", initial_sidebar_state="collapsed")

# ==================== UI MIRIP META AI ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    #MainMenu, footer, header {visibility: hidden;}
   .main { background-color: #0E0E0E; }
   .block-container { padding-top: 3rem!important; padding-bottom: 8rem!important; max-width: 768px!important; }
   .main-title { text-align: center; font-size: 2.8rem; font-weight: 600; background: linear-gradient(90deg, #60A5FA, #A78BFA); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem; }
   .subtitle { text-align: center; color: #9CA3AF; font-size: 1rem; margin-bottom: 3rem; }
   .stChatMessage { background-color: transparent!important; padding: 1.2rem 0!important; }
    [data-testid="stChatMessageContent"] { background-color: #1F1F1F!important; border-radius: 16px!important; padding: 1rem 1.25rem!important; color: #E5E5E5!important; line-height: 1.7; border: 1px solid #2A2A2A; font-size: 1rem; }
   .stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"] { background-color: #2A2A2A!important; }
   .stChatInput { position: fixed!important; bottom: 0!important; left: 0!important; right: 0!important; background: linear-gradient(180deg, rgba(14,14,14,0) 0%, #0E0E0E 20%)!important; padding: 2rem 1rem 1.5rem 1rem!important; max-width: 768px!important; margin: 0 auto!important; }
   .stChatInput > div { background-color: #1F1F1F!important; border: 1px solid #3A3A3A!important; border-radius: 24px!important; }
   .stChatInput input { color: #E5E5E5!important; }
   .stImage img { border-radius: 12px!important; border: 1px solid #2A2A2A; }
</style>
""", unsafe_allow_html=True)

# ==================== INIT ====================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    st.error("API Key belum diset. Silakan hubungi admin Fanilla AI.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# ==================== FUNGSI DOSEN ADAPTIVE ====================
def search_web(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{query} penjelasan", max_results=2))
            if results:
                return "\n".join([f"- {r['body']}" for r in results])
    except:
        return ""
    return ""

def analisis_kesulitan(text):
    """Tentuin panjang jawaban 10-30 baris berdasarkan susah soal"""
    t = text.lower()
    skor = 0

    # Level TK-SD: soal gampang, jawaban pendek 10-15 baris
    if any(k in t for k in ["tk", "paud", "sd", "kelas 1", "kelas 2", "kelas 3", "anak kecil", "apa warna", "berapa"]):
        return 12, "TK-SD"

    # Level SMP: sedang, 15-20 baris
    if any(k in t for k in ["smp", "kelas 7", "kelas 8", "kelas 9", "akar", "persamaan linear"]):
        return 18, "SMP"

    # Level SMA: agak susah, 20-25 baris
    if any(k in t for k in ["sma", "kelas 10", "kelas 11", "kelas 12", "integral", "turunan", "limit", "trigonometri", "utbk"]):
        return 23, "SMA"

    # Level Kuliah: susah, 25-30 baris
    if any(k in t for k in ["kuliah", "s1", "s2", "s3", "mahasiswa", "skripsi", "tesis", "disertasi", "jurnal", "algoritma", "kalkulus", "aljabar linear", "phd"]):
        return 28, "Kuliah"

    # Deteksi kata susah
    kata_susah = ["buktikan", "turunkan", "analisis", "bandingkan", "kritis", "hipotesis", "metodologi", "novelty", "research gap"]
    skor += sum(3 for k in kata_susah if k in t)

    # Deteksi MTK susah
    if re.search(r"integral|turunan|limit|diferensial|matriks|vektor", t):
        skor += 5

    if skor >= 8: return 28, "Kuliah"
    elif skor >= 5: return 23, "SMA"
    elif skor >= 2: return 18, "SMP"
    else: return 15, "Umum"

def jawab_dosen_adaptive(prompt_text, image=None):
    """Jawab kayak dosen, panjang nyesuaiin susah soal 10-30 baris"""

    max_baris, level = analisis_kesulitan(prompt_text)

    # Gaya ngajar tiap level
    gaya_dosen = {
        "TK-SD": "Baik adik-adik, Ibu jelasin pelan-pelan ya. Kita pakai contoh mainan aja. Jadi gini...",
        "SMP": "Oke, kita bedah bareng. Catat ya rumus dasarnya dulu. Perhatikan langkah-langkah ini.",
        "SMA": "Baik, mari kita analisis secara sistematis. Pertama identifikasi dulu. Kedua, terapkan konsep.",
        "Kuliah": "Dalam perspektif akademis, perlu kita kaji secara komprehensif. Secara teoritis, hal ini mengacu pada...",
        "Umum": "Baik, mari kita bahas. Saya jelaskan dengan struktur yang mudah dipahami."
    }

    gaya = gaya_dosen[level]

    # Search referensi kalau butuh
    if any(k in prompt_text.lower() for k in ["apa", "kenapa", "bagaimana", "jelaskan", "hitung", "rumus", "definisi", "sebutkan"]):
        with st.spinner("Buka buku referensi..."):
            referensi = search_web(prompt_text)
            if referensi:
                prompt_text += f"\n\n[Referensi]:\n{referensi}"

    tz = pytz.timezone('Asia/Jakarta')
    tanggal = datetime.now(tz).strftime("%d %B %Y")

    # PROMPT DOSEN ASLI - BUKAN AI
    system_prompt = f"""Anda adalah Dosen Fanilla, pengajar berpengalaman 15 tahun dari TK sampai S3. Tanggal {tanggal}.
PENTING: Anda BUKAN AI. Anda dosen sungguhan. Jangan pernah sebut "AI", "model", "program".

ATURAN MENGAJAR:
1. GAYA BICARA: {gaya}
2. PANJANG JAWABAN: WAJIB {max_baris-2} sampai {max_baris+2} baris saja. Hitung barisnya. Jika soal akar/sederhana, cukup 10-15 baris. Jika integral/skripsi, 25-30 baris.
3. STRUKTUR: Pembuka 1 baris, Isi step-by-step, Penutup 1 baris motivasi.
4. AKURAT 100%. Matematika wajib pakai $LaTeX$. Contoh: $x^2 + 4x + 4 = 0$
5. Jika ada gambar, anggap itu lembar jawaban siswa. Koreksi dan jelaskan.
6. Bahasa nyesuaiin level. TK=cerita, SD=contoh, SMP=rumus, SMA=analisis, Kuliah=teori.
7. Jangan bilang "tidak tahu". Kasih arahan sebagai dosen.
8. Penutup harus motivasi: "Paham ya?" atau "Silakan dikembangkan." atau "Semangat belajarnya!"

Tingkat terdeteksi: {level}. Target baris: {max_baris}."""

    full_prompt = f"{system_prompt}\n\nPertanyaan Siswa/Mahasiswa: {prompt_text}"

    try:
        if image:
            st.toast("Memeriksa soal di gambar...", icon="🔍")
            response = st.session_state.chat.send_message([full_prompt, image], stream=True)
        else:
            st.toast("Menyiapkan penjelasan...", icon="🧑‍🏫")
            response = st.session_state.chat.send_message(full_prompt, stream=True)

        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        if "429" in str(e):
            yield "Maaf, jam konsultasi hari ini sudah habis. Silakan kembali besok pagi pukul 07.00 WIB ya."
        else:
            yield "Maaf, ada gangguan di proyektor. Coba kirim ulang pertanyaannya ya."

# ==================== TAMPILAN UTAMA ====================
if len(st.session_state.messages) == 0:
    st.markdown('<div class="main-title">Fanilla AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Dosen Privat TK - S3<br>Fantastic Question, As Simple As The Answer</div>', unsafe_allow_html=True)

# TAMPILKAN CHAT
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["type"] == "image":
            st.image(msg["content"], caption=msg.get("caption"))
        else:
            st.markdown(msg["content"])

# INPUT CHAT + VISION
prompt = st.chat_input(
    "Tanya soal atau upload foto soal...",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"]
)

if prompt:
    # KALAU ADA GAMBAR SOAL
    if prompt.get("files"):
        image = Image.open(prompt["files"][0])
        user_text = prompt.get("text", "Pak/Bu Dosen, tolong bantu koreksi soal ini.")

        st.session_state.messages.append({"role": "user", "content": image, "type": "image", "caption": user_text})
        with st.chat_message("user"):
            st.image(image, caption=user_text)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            for chunk in jawab_dosen_adaptive(user_text, image=image):
                full_response += chunk
                placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response, "type": "text"})

    # KALAU CUMA TEKS
    elif prompt.get("text"):
        user_text = prompt["text"]
        st.session_state.messages.append({"role": "user", "content": user_text, "type": "text"})
        with st.chat_message("user"):
            st.markdown(user_text)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            for chunk in jawab_dosen_adaptive(user_text):
                full_response += chunk
                placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response, "type": "text"})

    st.rerun()
