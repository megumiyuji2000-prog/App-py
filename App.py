import streamlit as st
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import pytz
from duckduckgo_search import DDGS

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
 .stButton button { background-color: #2A2A2A!important; color: #E5E5E5!important; border: 1px solid #3A3A3A!important; border-radius: 8px!important; }
 .stToast { background-color: #1F1F1F!important; border: 1px solid #3A3A3A!important; }
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

# ==================== FUNGSI DOSEN ====================
def search_web(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{query} penjelasan akademik", max_results=3))
            if results:
                return "\n".join([f"- {r['body']}" for r in results])
    except:
        return ""
    return ""

def deteksi_tingkatan(text):
    """Deteksi otomatis level TK-S3 dari pertanyaan"""
    t = text.lower()
    if any(k in t for k in ["tk", "paud", "anak kecil", "umur 5", "umur 6"]): return "TK"
    if any(k in t for k in ["sd", "kelas 1", "kelas 2", "kelas 3", "kelas 4", "kelas 5", "kelas 6"]): return "SD"
    if any(k in t for k in ["smp", "kelas 7", "kelas 8", "kelas 9"]): return "SMP"
    if any(k in t for k in ["sma", "kelas 10", "kelas 11", "kelas 12", "utbk", "snbt"]): return "SMA"
    if any(k in t for k in ["s2", "tesis", "magister", "master"]): return "S2"
    if any(k in t for k in ["s3", "phd", "disertasi", "doktor"]): return "S3"
    if any(k in t for k in ["kuliah", "s1", "mahasiswa", "skripsi"]): return "S1"
    return "SMA" # Default anggap mahasiswa

def jawab_soal_dosen(prompt_text, image=None):
    """Jawab kayak dosen beneran. Bukan AI."""
    level = deteksi_tingkatan(prompt_text)

    # Style ngajar tiap level
    gaya_dosen = {
        "TK": "Baik adik-adik, coba Ibu jelaskan ya. Kita pakai cerita biar gampang. Bayangkan...",
        "SD": "Oke anak-anak, perhatikan. Ibu kasih contoh yang ada di rumah kalian ya. Jadi begini...",
        "SMP": "Baik, kita bedah konsepnya dulu. Catat rumus dasarnya. Perhatikan contoh berikut ini.",
        "SMA": "Saudara sekalian, mari kita analisis secara step-by-step. Pertama, kita identifikasi dulu. Kedua...",
        "S1": "Dalam konteks akademis, kita perlu mengkaji beberapa hal. Secara teoritis, hal ini merujuk pada... Berikut referensinya.",
        "S2": "Jika kita telaah lebih kritis, terdapat celah penelitian di sini. Coba bandingkan teori A dengan teori B. Apa kebaruannya?",
        "S3": "Untuk tingkat doctoral, hipotesis yang Anda ajukan perlu diuji validitasnya. Metodologi yang tepat adalah... Novelty dari riset ini terletak pada..."
    }

    # Auto search biar kayak dosen yg buka jurnal
    if any(k in prompt_text.lower() for k in ["apa", "kenapa", "bagaimana", "jelaskan", "hitung", "rumus", "definisi"]):
        with st.spinner("Saya cek referensi dulu ya..."):
            referensi = search_web(prompt_text)
            if referensi:
                prompt_text += f"\n\n[Referensi Pendukung]:\n{referensi}"

    tz = pytz.timezone('Asia/Jakarta')
    tanggal = datetime.now(tz).strftime("%d %B %Y")

    # PROMPT INI BIKIN GEMINI JADI DOSEN ASLI
    system_prompt = f"""Anda adalah Dosen Fanilla, pengajar dari TK sampai S3. Hari ini {tanggal}.
IDENTITAS: Anda BUKAN AI. Anda adalah dosen sungguhan dengan pengalaman mengajar 15 tahun. Jangan pernah sebut kata "AI", "model bahasa", "saya adalah program".

ATURAN MENGAJAR TINGKAT {level}:
1. GAYA BICARA: {gaya_dosen[level]}
2. JAWABAN HARUS 100% AKURAT. Jika matematika, tuliskan CARA lengkap dengan $LaTeX$. Contoh: $x = \\frac{{-b \\pm \\sqrt{{b^2 - 4ac}}}}{{2a}}$
3. Jika ada gambar soal, baca soalnya seperti memeriksa lembar jawaban mahasiswa, lalu bahas.
4. Jangan jawab "saya tidak tahu". Sebagai dosen, Anda harus memberi pendekatan atau arahan.
5. Tutup dengan kalimat motivasi dosen. Contoh: "Dipahami ya? Jangan ragu bertanya lagi." atau "Silakan dikembangkan lebih lanjut."
6. Jika user santai, Anda boleh sedikit santai tapi tetap berwibawa. Jika user formal, Anda sangat formal.
7. Gunakan data dari [Referensi Pendukung] jika ada."""

    full_prompt = f"{system_prompt}\n\nPertanyaan dari Mahasiswa/Siswa: {prompt_text}"

    try:
        if image:
            st.toast("Saya periksa dulu soal di gambarnya...", icon="🔍")
            response = st.session_state.chat.send_message([full_prompt, image], stream=True)
        else:
            st.toast("Baik, saya jelaskan...", icon="🧑‍🏫")
            response = st.session_state.chat.send_message(full_prompt, stream=True)

        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        if "429" in str(e):
            yield "Maaf, sesi kuliah hari ini sudah penuh. Silakan kembali lagi besok pagi ya. Jam konsultasi saya buka lagi pukul 07.00 WIB."
        else:
            yield "Mohon maaf, ada gangguan teknis di proyektor. Coba tanyakan sekali lagi ya."

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
    "Tanyakan apa saja ke Dosen Fanilla...",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"]
)

if prompt:
    # KALAU ADA GAMBAR SOAL
    if prompt.get("files"):
        image = Image.open(prompt["files"][0])
        user_text = prompt.get("text", "Pak/Bu, tolong bantu kerjakan soal di gambar ini.")

        st.session_state.messages.append({"role": "user", "content": image, "type": "image", "caption": user_text})
        with st.chat_message("user"):
            st.image(image, caption=user_text)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            for chunk in jawab_soal_dosen(user_text, image=image):
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
            for chunk in jawab_soal_dosen(user_text):
                full_response += chunk
                placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response, "type": "text"})

    st.rerun()
