import streamlit as st
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import pytz
from duckduckgo_search import DDGS
import re

st.set_page_config(page_title="Fanilla AI", page_icon="🎓", layout="centered", initial_sidebar_state="collapsed")

# ==================== CSS META AI + TOMBOL + MIRIP SS ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
    #MainMenu, footer, header {visibility: hidden;}

    /* Meta AI Dark */
  .stApp,.main { background-color: #0C0C0C; }
  .block-container {
        padding-top: 2rem!important;
        padding-bottom: 8rem!important;
        max-width: 48rem!important;
    }

    /* Title */
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
    }

    /* Chat Bubble */
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
    }
  .stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"] {
        background-color: #262626!important;
        border: 1px solid #404040;
    }

    /* Input Box + Tombol Plus Kayak SS Lu */
  .stChatInput {
        position: fixed!important;
        bottom: 0!important;
        left: 0!important;
        right: 0!important;
        background: linear-gradient(180deg, rgba(12,12,12,0) 0%, #0C0C0C 30%)!important;
        padding: 1rem 1rem 1.5rem 1rem!important;
        max-width: 48rem!important;
        margin: 0 auto!important;
        backdrop-filter: blur(8px);
    }
  .stChatInput > div {
        background-color: #1A1A1A!important;
        border: 1px solid #333333!important;
        border-radius: 26px!important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        display: flex!important;
        align-items: center!important;
        padding-left: 8px!important;
    }
  .stChatInput input {
        color: #E4E4E7!important;
        font-size: 0.95rem!important;
        padding: 14px 18px!important;
    }
  .stChatInput input::placeholder { color: #737373!important; }

    /* Tombol Upload + Send */
    button[kind="secondary"] {
        background-color: transparent!important;
        border: none!important;
        color: #A3A3A3!important;
        border-radius: 50%!important;
        width: 36px!important;
        height: 36px!important;
        padding: 0!important;
        margin: 0 4px!important;
    }
    button[kind="secondary"]:hover {
        background-color: #262626!important;
        color: #E4E4E7!important;
    }
    button[kind="primary"] {
        background-color: #60A5FA!important;
        border-radius: 50%!important;
        width: 36px!important;
        height: 36px!important;
        padding: 0!important;
        margin: 0 4px!important;
    }

  .stImage img {
        border-radius: 14px!important;
        border: 1px solid #262626;
        margin: 8px 0;
    }
  .stToast {
        background-color: #1A1A1A!important;
        border: 1px solid #333333!important;
        border-radius: 12px!important;
    }

    /* Mode Badge */
  .mode-badge {
        display: inline-block;
        font-size: 0.75rem;
        padding: 4px 10px;
        border-radius: 12px;
        margin-bottom: 8px;
        font-weight: 500;
    }
  .mode-dosen { background-color: #1E40AF; color: #BFDBFE; }
  .mode-teman { background-color: #166534; color: #BBF7D0; }
</style>
""", unsafe_allow_html=True)

# ==================== INIT ====================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    st.error("API Key belum diset bro.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# ==================== DETEKSI MODE ====================
def deteksi_mode(text, ada_gambar=False):
    """Deteksi Mode Dosen vs Mode Teman"""
    t = text.lower()

    # Kalau ada gambar = auto Mode Dosen
    if ada_gambar:
        return "dosen"

    # Kata kunci soal = Mode Dosen
    kata_soal = [
        "berapa", "hitung", "kerjakan", "jawab", "soal", "rumus", "integral", "turunan",
        "limit", "akar", "persamaan", "matriks", "jelaskan", "definisi", "sebutkan",
        "apa itu", "kenapa", "bagaimana", "buktikan", "analisis", "utbk", "sbmptn",
        "skripsi", "tesis", "disertasi", "jurnal"
    ]

    if any(k in t for k in kata_soal):
        return "dosen"

    # Cek ada angka/rumus
    if re.search(r"\d+\s*[\+\-\x\*\/\=]\s*\d+|[a-z]\^2|∫|√|∑", text):
        return "dosen"

    # Default = Mode Teman
    return "teman"

def deteksi_level(text):
    """Deteksi tingkatan TK-S3 buat Mode Dosen"""
    t = text.lower()
    if any(k in t for k in ["tk", "paud", "anak kecil"]): return "TK", 12
    if any(k in t for k in ["sd", "kelas 1", "kelas 2", "kelas 3", "kelas 4", "kelas 5", "kelas 6"]): return "SD", 14
    if any(k in t for k in ["smp", "kelas 7", "kelas 8", "kelas 9"]): return "SMP", 17
    if any(k in t for k in ["sma", "kelas 10", "kelas 11", "kelas 12", "utbk"]): return "SMA", 22
    if any(k in t for k in ["s2", "tesis", "magister", "master"]): return "S2", 28
    if any(k in t for k in ["s3", "phd", "disertasi", "doktor"]): return "S3", 30
    if any(k in t for k in ["kuliah", "s1", "mahasiswa", "skripsi"]): return "S1", 26

    # Deteksi susah/gampang
    if re.search(r"integral|turunan|limit|diferensial|matriks|buktikan|analisis", t): return "SMA", 22
    if re.search(r"akar|persamaan|pecahan", t): return "SMP", 17
    return "SMA", 20 # Default

def search_web(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{query} penjelasan", max_results=2))
            if results:
                return "\n".join([f"- {r['body'][:200]}" for r in results])
    except:
        return ""
    return ""

def jawab_fanilla(text, image=None):
    """Dual Mode: Teman vs Dosen"""
    mode = deteksi_mode(text, ada_gambar=image is not None)

    if mode == "dosen":
        level, max_baris = deteksi_level(text)

        gaya_dosen = {
            "TK": "Oke dek, kita pake cerita ya. Bayangin gini...",
            "SD": "Baik, kita pake contoh yang ada di rumah aja ya. Gini...",
            "SMP": "Oke bro, kita bedah bareng. Catat rumusnya dulu:",
            "SMA": "Baik, kita analisis step-by-step. Pertama identifikasi soalnya.",
            "S1": "Secara akademis, perlu kita kaji komprehensif. Merujuk pada teori...",
            "S2": "Jika ditelaah kritis, terdapat research gap di sini. Coba bandingkan...",
            "S3": "Untuk level doctoral, hipotesis ini perlu diuji. Novelty-nya terletak pada..."
        }

        # Search referensi
        with st.spinner("Buka buku referensi..."):
            ref = search_web(text)
            if ref:
                text += f"\n\n[Referensi]:\n{ref}"

        tz = pytz.timezone('Asia/Jakarta')
        tgl = datetime.now(tz).strftime("%d %B %Y")

        prompt = f"""Anda adalah Dosen Fanilla, pengajar 15 tahun dari TK sampai S3. Tanggal {tgl}.
Anda BUKAN AI. Anda dosen beneran. Jangan sebut "AI/model/program".

MODE: DOSEN - LEVEL {level}
ATURAN:
1. GAYA: {gaya_dosen[level]}
2. PANJANG: WAJIB {max_baris-1} sampai {max_baris+1} baris. Minimal 2 paragraf, maksimal 4 paragraf.
3. STRUKTUR: Pembuka 1 baris, Isi step-by-step, Penutup 1 baris motivasi.
4. AKURAT 100%. Matematika pake $LaTeX$: $x = \\frac{{-b \\pm \\sqrt{{b^2 - 4ac}}}}{{2a}}$
5. Bahasa: Gaul tapi baku. Contoh: "Nah bro, rumus integral itu gini..." bukan "Anda harus mengintegralkan"
6. Jika gambar = lembar jawaban siswa. Koreksi dan jelaskan.
7. Penutup: "Paham ya bro?" / "Silakan dikembangkan." / "Semangat!"

Soal: {text}"""

        st.toast(f"Mode Dosen {level} Aktif", icon="🎓")

    else: # MODE TEMAN
        prompt = f"""Kamu adalah Fanilla AI, temen nongkrong yang pinter tapi santai.

ATURAN MODE TEMAN:
1. Bahasa: Gaul abis, informatif, kayak ngobrol di tongkrongan. Pake "lu", "gw", "anjir", "wkwk" boleh.
2. PANJANG: Minimal 1 paragraf, MAKSIMAL 2 paragraf. Jangan panjang-panjang.
3. Topik: Bebas. Ngobrol santai, curhat, bahas game, anime, dll.
4. Jangan sok dosen. Jadi temen.
5. Jangan sebut "AI" atau "model bahasa".

Chat dari temen: {text}"""

        st.toast("Mode Teman Aktif", icon="😎")

    try:
        if image:
            res = st.session_state.chat.send_message([prompt, image], stream=True)
        else:
            res = st.session_state.chat.send_message(prompt, stream=True)

        for chunk in res:
            if chunk.text:
                yield chunk.text, mode
    except:
        yield "Waduh error bro. Coba lagi ya.", mode

# ==================== UI ====================
if len(st.session_state.messages) == 0:
    st.markdown('<div class="meta-title">Fanilla AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="meta-subtitle">Fantastic Question, As Simple As The Answer<br>Ngobrol santai bisa, nanya soal juga bisa 📸</div>', unsafe_allow_html=True)

# Tampilkan chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("mode"):
            badge = "mode-dosen" if msg["mode"] == "dosen" else "mode-teman"
            label = "🎓 Mode Dosen" if msg["mode"] == "dosen" else "😎 Mode Teman"
            st.markdown(f'<div class="mode-badge {badge}">{label}</div>', unsafe_allow_html=True)

        if msg["type"] == "image":
            st.image(msg["content"], caption=msg.get("caption"))
        else:
            st.markdown(msg["content"])

# INPUT CUSTOM KAYAK SS LU
prompt = st.chat_input(
    "Tanya Fanilla...",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"]
)

if prompt:
    mode_aktif = "teman"

    # Kalau ada gambar
    if prompt.get("files"):
        img = Image.open(prompt["files"][0])
        txt = prompt.get("text", "Tolong koreksi soal ini dong.")
        st.session_state.messages.append({"role": "user", "content": img, "type": "image", "caption": txt})

        with st.chat_message("user"):
            st.image(img, caption=txt)

        with st.chat_message("assistant"):
            ph = st.empty()
            out = ""
            for c, m in jawab_fanilla(txt, image=img):
                out += c
                mode_aktif = m
                ph.markdown(out + "▌")
            ph.markdown(out)
            st.session_state.messages.append({"role": "assistant", "content": out, "type": "text", "mode": mode_aktif})

    # Kalau cuma teks
    elif prompt.get("text"):
        txt = prompt["text"]
        st.session_state.messages.append({"role": "user", "content": txt, "type": "text"})

        with st.chat_message("user"):
            st.markdown(txt)

        with st.chat_message("assistant"):
            ph = st.empty()
            out = ""
            for c, m in jawab_fanilla(txt):
                out += c
                mode_aktif = m
                ph.markdown(out + "▌")
            ph.markdown(out)
            st.session_state.messages.append({"role": "assistant", "content": out, "type": "text", "mode": mode_aktif})

    st.rerun()
