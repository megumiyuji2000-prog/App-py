import streamlit as st
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import pytz
from duckduckgo_search import DDGS
import re

st.set_page_config(page_title="Fanilla AI", page_icon="🎓", layout="centered", initial_sidebar_state="collapsed")

# ==================== CSS 98% MIRIP META AI ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
    #MainMenu, footer, header {visibility: hidden;}

    /* Meta AI Dark Theme */
   .stApp { background-color: #0C0C0C; }
   .main { background-color: #0C0C0C; }
   .block-container {
        padding-top: 2rem!important;
        padding-bottom: 9rem!important;
        max-width: 48rem!important;
    }

    /* Title kayak Meta AI */
   .meta-title {
        text-align: center;
        font-size: 2.25rem;
        font-weight: 600;
        background: linear-gradient(90deg, #60A5FA 0%, #A78BFA 50%, #F472B6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
        letter-spacing: -0.02em;
    }
   .meta-subtitle {
        text-align: center;
        color: #9CA3AF;
        font-size: 0.95rem;
        margin-bottom: 3rem;
        font-weight: 400;
    }

    /* Chat Bubble Meta AI Style */
   .stChatMessage {
        background-color: transparent!important;
        padding: 0.75rem 0!important;
        margin: 0!important;
    }
    [data-testid="stChatMessageContent"] {
        background-color: #1A1A1A!important;
        border-radius: 18px!important;
        padding: 12px 16px!important;
        color: #E4E4E7!important;
        line-height: 1.65;
        border: 1px solid #262626;
        font-size: 0.95rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.3);
    }
   .stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"] {
        background-color: #262626!important;
        border: 1px solid #404040;
    }

    /* Input Box Meta AI Style */
   .stChatInput {
        position: fixed!important;
        bottom: 0!important;
        left: 0!important;
        right: 0!important;
        background: linear-gradient(180deg, rgba(12,12,12,0) 0%, #0C0C0C 30%)!important;
        padding: 2rem 1rem 1.5rem 1rem!important;
        max-width: 48rem!important;
        margin: 0 auto!important;
        backdrop-filter: blur(8px);
    }
   .stChatInput > div {
        background-color: #1A1A1A!important;
        border: 1px solid #333333!important;
        border-radius: 26px!important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }
   .stChatInput input {
        color: #E4E4E7!important;
        font-size: 0.95rem!important;
        padding: 14px 18px!important;
    }
   .stChatInput input::placeholder { color: #737373!important; }

    /* Image Style */
   .stImage img {
        border-radius: 14px!important;
        border: 1px solid #262626;
        margin: 8px 0;
    }

    /* Toast Meta AI Style */
   .stToast {
        background-color: #1A1A1A!important;
        border: 1px solid #333333!important;
        border-radius: 12px!important;
        color: #E4E4E7!important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #0C0C0C; }
    ::-webkit-scrollbar-thumb { background: #333333; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #404040; }

    /* Code block */
   .stMarkdown pre {
        background-color: #0A0A0A!important;
        border: 1px solid #262626!important;
        border-radius: 8px!important;
    }
   .stMarkdown code {
        background-color: #1A1A1A!important;
        border: 1px solid #262626!important;
        border-radius: 4px!important;
        padding: 2px 6px!important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== INIT ====================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    st.error("API Key belum dikonfigurasi.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# ==================== DOSEN ADAPTIVE 10-30 BARIS ====================
def search_web(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{query} penjelasan akademik", max_results=2))
            if results:
                return "\n".join([f"- {r['body'][:200]}" for r in results])
    except:
        return ""
    return ""

def analisis_kesulitan(text):
    """Tentuin panjang jawaban 10-30 baris + level"""
    t = text.lower()

    # TK-SD: 10-14 baris
    if any(k in t for k in ["tk", "paud", "sd", "kelas 1", "kelas 2", "kelas 3", "anak kecil", "apa warna", "berapa"]):
        return 12, "TK-SD"

    # SMP: 15-19 baris
    if any(k in t for k in ["smp", "kelas 7", "kelas 8", "kelas 9", "akar", "persamaan linear", "pecahan"]):
        return 17, "SMP"

    # SMA: 20-24 baris
    if any(k in t for k in ["sma", "kelas 10", "kelas 11", "kelas 12", "integral", "turunan", "limit", "trigonometri", "utbk", "logaritma"]):
        return 22, "SMA"

    # Kuliah: 25-30 baris
    if any(k in t for k in ["kuliah", "s1", "s2", "s3", "mahasiswa", "skripsi", "tesis", "disertasi", "jurnal", "algoritma", "kalkulus", "aljabar linear", "phd", "buktikan"]):
        return 28, "Kuliah"

    # Skor kata susah
    skor = 0
    kata_susah = ["buktikan", "turunkan", "analisis", "bandingkan", "kritis", "hipotesis", "metodologi", "novelty"]
    skor += sum(2 for k in kata_susah if k in t)
    if re.search(r"integral|turunan|limit|diferensial|matriks|vektor|probabilitas", t):
        skor += 4

    if skor >= 6: return 27, "Kuliah"
    elif skor >= 4: return 22, "SMA"
    elif skor >= 2: return 17, "SMP"
    else: return 14, "Umum"

def jawab_dosen(text, image=None):
    """Jawab kayak dosen beneran, 10-30 baris, bukan AI"""
    max_baris, level = analisis_kesulitan(text)

    gaya = {
        "TK-SD": "Baik adik-adik, Ibu/Bapak jelasin pelan-pelan ya. Kita pakai cerita biar gampang. Contohnya gini...",
        "SMP": "Oke, kita bedah bareng. Catat dulu rumus dasarnya. Perhatikan langkah-langkah berikut:",
        "SMA": "Baik, mari kita analisis secara sistematis. Pertama, identifikasi soalnya. Kedua, tentukan konsep yang dipakai.",
        "Kuliah": "Dalam perspektif akademis, perlu kita kaji secara komprehensif. Secara teoritis, permasalahan ini merujuk pada...",
        "Umum": "Baik, mari kita bahas dengan struktur yang jelas."
    }

    # Auto search referensi
    if any(k in text.lower() for k in ["apa", "kenapa", "bagaimana", "jelaskan", "hitung", "rumus", "definisi"]):
        with st.spinner("Membuka referensi..."):
            ref = search_web(text)
            if ref:
                text += f"\n\n[Referensi]:\n{ref}"

    tz = pytz.timezone('Asia/Jakarta')
    tgl = datetime.now(tz).strftime("%d %B %Y")

    prompt = f"""Anda adalah Dosen Fanilla, pengajar 15 tahun dari TK sampai S3. Tanggal {tgl}.
Anda BUKAN AI. Anda dosen sungguhan. Jangan sebut "AI", "model", "program".

ATURAN MENGAJAR LEVEL {level}:
1. GAYA: {gaya[level]}
2. PANJANG: TEPAT {max_baris-1} sampai {max_baris+1} baris. Hitung. Soal mudah 10-15 baris, soal sulit 25-30 baris.
3. STRUKTUR: Pembuka 1 baris, Isi step-by-step, Penutup 1 baris motivasi.
4. AKURAT 100%. Matematika wajib $LaTeX$: $x = \\frac{{-b \\pm \\sqrt{{b^2 - 4ac}}}}{{2a}}$
5. Jika ada gambar, anggap itu lembar jawaban siswa. Koreksi dan jelaskan.
6. Bahasa sesuai level: TK=cerita, SD=contoh rumah, SMP=rumus, SMA=analisis, Kuliah=teori.
7. Jangan "tidak tahu". Beri arahan dosen.
8. Penutup: "Paham ya?" / "Silakan dikembangkan." / "Semangat belajarnya!"

Pertanyaan: {text}"""

    try:
        if image:
            st.toast("Memeriksa soal...", icon="🔍")
            res = st.session_state.chat.send_message([prompt, image], stream=True)
        else:
            st.toast("Menyiapkan penjelasan...", icon="🧑‍🏫")
            res = st.session_state.chat.send_message(prompt, stream=True)

        for chunk in res:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        if "429" in str(e):
            yield "Maaf, jam konsultasi hari ini sudah habis. Silakan kembali besok pukul 07.00 WIB."
        else:
            yield "Maaf, ada gangguan teknis. Coba kirim ulang pertanyaannya."

# ==================== TAMPILAN ====================
if len(st.session_state.messages) == 0:
    st.markdown('<div class="meta-title">Fanilla AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="meta-subtitle">Dosen Privat TK - S3 | Fantastic Question, As Simple As The Answer</div>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["type"] == "image":
            st.image(msg["content"], caption=msg.get("caption"))
        else:
            st.markdown(msg["content"])

prompt = st.chat_input(
    "Tanyakan soal atau upload foto...",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"]
)

if prompt:
    if prompt.get("files"):
        img = Image.open(prompt["files"][0])
        txt = prompt.get("text", "Pak/Bu, tolong koreksi soal ini.")
        st.session_state.messages.append({"role": "user", "content": img, "type": "image", "caption": txt})
        with st.chat_message("user"):
            st.image(img, caption=txt)
        with st.chat_message("assistant"):
            ph = st.empty()
            out = ""
            for c in jawab_dosen(txt, image=img):
                out += c
                ph.markdown(out + "▌")
            ph.markdown(out)
            st.session_state.messages.append({"role": "assistant", "content": out, "type": "text"})
    elif prompt.get("text"):
        txt = prompt["text"]
        st.session_state.messages.append({"role": "user", "content": txt, "type": "text"})
        with st.chat_message("user"):
            st.markdown(txt)
        with st.chat_message("assistant"):
            ph = st.empty()
            out = ""
            for c in jawab_dosen(txt):
                out += c
                ph.markdown(out + "▌")
            ph.markdown(out)
            st.session_state.messages.append({"role": "assistant", "content": out, "type": "text"})
    st.rerun()
