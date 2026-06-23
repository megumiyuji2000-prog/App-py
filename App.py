import streamlit as st
import google.generativeai as genai
from PIL import Image
import time, io, requests
from datetime import datetime
import pytz
from duckduckgo_search import DDGS

st.set_page_config(page_title="Fanilla AI - Bimbel TK-S3", page_icon="🎓", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    #MainMenu, footer, header {visibility: hidden;}
   .main { background-color: #0E0E0E; }
   .block-container { padding-top: 3rem!important; padding-bottom: 8rem!important; max-width: 768px!important; }
   .main-title { text-align: center; font-size: 3rem; font-weight: 600; background: linear-gradient(90deg, #8B5CF6, #EC4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem; }
   .subtitle { text-align: center; color: #9CA3AF; font-size: 1.1rem; margin-bottom: 3rem; }
   .stChatMessage { background-color: transparent!important; padding: 1.5rem 0!important; }
    [data-testid="stChatMessageContent"] { background-color: #1F1F1F!important; border-radius: 18px!important; padding: 1rem 1.25rem!important; color: #E5E5E5!important; line-height: 1.7; border: 1px solid #2A2A2A; }
   .stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"] { background-color: #2A2A2A!important; }
   .stChatInput { position: fixed!important; bottom: 0!important; left: 0!important; right: 0!important; background: linear-gradient(180deg, rgba(14,14,14,0) 0%, #0E0E0E 20%)!important; padding: 2rem 1rem 1.5rem 1rem!important; max-width: 768px!important; margin: 0 auto!important; }
   .stChatInput > div { background-color: #1F1F1F!important; border: 1px solid #3A3A3A!important; border-radius: 24px!important; }
   .stChatInput input { color: #E5E5E5!important; }
   .stImage img { border-radius: 12px!important; border: 1px solid #2A2A2A; }
    [data-testid="stSidebar"] { background-color: #171717; border-right: 1px solid #2A2A2A; }
   .stButton button { background-color: #2A2A2A!important; color: #E5E5E5!important; border: 1px solid #3A3A3A!important; border-radius: 8px!important; }
</style>
""", unsafe_allow_html=True)

# ==================== INIT ====================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')
except KeyError as e:
    st.error(f"❌ Secrets Error: `GEMINI_API_KEY` tidak ditemukan. Tambahin di Settings > Secrets")
    st.stop()
except Exception as e:
    st.error(f"❌ Init Error: {e}")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False
if "user_style" not in st.session_state:
    st.session_state.user_style = "santai"
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# ==================== CORE FUNCTION ====================
def detect_user_style(text):
    text_lower = text.lower()
    formal_words = ["apakah", "bagaimana", "mohon", "terima kasih", "saya", "anda", "jelaskan", "analisis"]
    bro_words = ["bro", "gk", "ga", "lu", "gw", "wkwk", "anjir", "tolong", "dong"]
    formal_score = sum(1 for w in formal_words if w in text_lower)
    bro_score = sum(1 for w in bro_words if w in text_lower)
    if bro_score > formal_score:
        return "santai"
    elif formal_score > 0:
        return "formal"
    return st.session_state.user_style

def search_web(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if results:
                return "\n\n".join([f"Sumber: {r['href']}\n{r['body']}" for r in results])
    except:
        return "Search error."
    return "Tidak ada hasil."

def detect_level(prompt_text):
    """Deteksi tingkatan TK-S3 dari prompt"""
    user_lower = prompt_text.lower()
    if any(k in user_lower for k in ["tk", "paud", "anak kecil", "umur 5", "umur 6"]):
        return "TK: Gunakan analogi dongeng, kata super simple, banyak emoji. Contoh: Matahari itu kayak lampu besar banget di langit ☀️"
    elif any(k in user_lower for k in ["sd", "kelas 1", "kelas 2", "kelas 3", "kelas 4", "kelas 5", "kelas 6"]):
        return "SD: Bahasa sederhana, kasih contoh sehari-hari kayak di rumah/sekolah, 1-2 kalimat per poin."
    elif any(k in user_lower for k in ["smp", "kelas 7", "kelas 8", "kelas 9"]):
        return "SMP: Jelaskan konsep + rumus dasar + 1 contoh soal dengan cara."
    elif any(k in user_lower for k in ["sma", "kelas 10", "kelas 11", "kelas 12", "utbk", "snbt", "sbmptn"]):
        return "SMA: Step-by-step, rumus lengkap pake LaTeX $...$, kasih 2 latihan soal HOTS."
    elif any(k in user_lower for k in ["kuliah", "s1", "mahasiswa", "skripsi", "kampus"]):
        return "S1: Formal, kasih referensi atau jurnal, code jika perlu, struktur: Pendahuluan-Isi-Kesimpulan."
    elif any(k in user_lower for k in ["s2", "tesis", "magister", "master"]):
        return "S2: Analisis kritis, bandingkan minimal 2 teori, sebutkan research gap atau kebaruan."
    elif any(k in user_lower for k in ["s3", "phd", "disertasi", "doktor", "doctoral"]):
        return "S3: Level expert. Kasih hipotesis, metodologi, novelty/kebaruan. Gunakan istilah teknis."
    else:
        return "Umum: Sesuaikan gaya dengan user. Jika soal matematika/fisika, selalu tunjukkan cara."

def ai_stream_gemini(prompt_text, image=None):
    """V15 - BIMBEL AI TK-S3 + VISION"""
    st.session_state.user_style = detect_user_style(prompt_text)
    level_instruction = detect_level(prompt_text)

    # Fitur /gambar dimatiin, fokus bimbel
    if prompt_text.lower().startswith("/gambar"):
        yield "Fitur `/gambar` lagi istirahat bro 😴 Fanilla sekarang fokus jadi guru TK-S3. \n\nTapi lu bisa **upload foto soal** langsung, nanti gua jawab pake VISION 🔥"
        return

    # AUTO SEARCH buat soal
    user_lower = prompt_text.lower()
    need_search = any(word in user_lower for word in [
        "jelaskan", "apa itu", "kenapa", "bagaimana", "sebutkan", "hitung", "carilah",
        "terbaru", "2025", "2026", "rumus", "definisi", "contoh soal", "sejarah"
    ])

    if need_search and not image:
        with st.spinner("🔍 Cek buku & internet..."):
            search_result = search_web(prompt_text)
            prompt_text += f"\n\n[FAKTA DARI WEB]:\n{search_result}"

    tz = pytz.timezone('Asia/Jakarta')
    date_now = datetime.now(tz).strftime("%d %B %Y")

    # SYSTEM PROMPT BIMBEL
    system_prompt = f"""Kamu Fanilla AI - Bimbel AI dari TK sampai S3 by FNL. Tanggal {date_now}.
TAGLINE: "Fantastic Question, As Simple As The Answer"

ATURAN UTAMA:
1. TINGKATAN USER: {level_instruction}
2. FAKTA 100% AKURAT. Cek ejaan. Jika hitungan MTK/Fisika, TUNJUKKAN CARA step-by-step.
3. Gunakan data [FAKTA DARI WEB] jika ada. Jangan ngarang rumus atau data.
4. FORMAT: Untuk MTK/Fisika pake LaTeX $x^2 + y^2 = z^2$. Untuk code pake markdown ```python.
5. GAYA: Jika user santai pake 'bro/lu/gw', jika formal pake 'Anda'. Max 4 paragraf kecuali diminta.
6. VISION: Jika ada gambar soal, baca soalnya, pahami, lalu jawab sesuai tingkatan.
7. Jika soal tidak jelas, tanya balik: "Ini buat tingkatan apa bro? TK/SD/SMP/SMA/Kuliah?"
8. Jangan pernah jawab "saya tidak tahu". Cari di web atau kasih pendekatan logis.
9. MOTIVASI: Kasih semangat dikit di akhir kalo soal susah. Contoh: "Semangat bro, pasti bisa!"

KONTEN TERLARANG: Jangan jawab soal ujian yang sedang berlangsung real-time."""

    full_prompt = f"{system_prompt}\n\nSoal/User: {prompt_text}"

    try:
        if image:
            st.toast("Pake Vision Mode... 📸", icon="🎓")
            response = st.session_state.chat.send_message([full_prompt, image], stream=True)
        else:
            st.toast("Pake Gemini 2.5 Flash Mode Bimbel...", icon="🎓")
            response = st.session_state.chat.send_message(full_prompt, stream=True)

        full = ""
        for chunk in response:
            if chunk.text:
                full += chunk.text
                yield full

    except Exception as e:
        error = str(e)
        if "429" in error or "quota" in error.lower():
            yield "Limit Gemini 1500/hari abis bro 😭 Besok reset jam 7 pagi WIB. Fanilla istirahat dulu."
        else:
            yield f"Error bro: {error}"

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### 🎓 Fanilla AI")
    st.caption("Fantastic Question, As Simple As The Answer")
    st.caption(f"Style: {st.session_state.user_style}")
    if st.button("🗑️ Hapus Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.user_style = "santai"
        st.session_state.chat = model.start_chat(history=[])
        st.rerun()
    st.markdown("---")
    st.caption("**Bisa jawab:**")
    st.caption("TK, SD, SMP, SMA, S1, S2, S3")
    st.caption("**Fitur:**")
    st.caption("• Teks: Ketik soal apa aja")
    st.caption("• Vision: Upload foto soal 📸")
    st.caption("• LaTeX: Rumus $x^2$")
    st.caption("• Code: Python, dll")
    st.markdown("---")
    st.caption("Fanilla AI © FNL 2026")
    st.caption("{GRUB OF FNL crop}")

# ==================== MAIN ====================
if len(st.session_state.messages) == 0:
    st.markdown('<div class="main-title">Fanilla AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Fantastic Question, As Simple As The Answer<br>Bimbel AI TK - S3 | Upload foto soal juga bisa 📸</div>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["type"] == "image":
            st.image(msg["content"], caption=msg.get("caption", ""))
        else:
            st.markdown(msg["content"])

# ==================== INPUT ====================
prompt = st.chat_input(
    "Tanya soal TK-S3 atau upload foto soal...",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
    disabled=st.session_state.processing
)

if prompt and not st.session_state.processing:
    st.session_state.processing = True

    if prompt.get("files"):
        image = Image.open(prompt["files"][0])
        user_text = prompt.get("text", "Tolong jawab soal di gambar ini")

        st.session_state.messages.append({
            "role": "user",
            "content": image,
            "type": "image",
            "caption": user_text
        })

        with st.chat_message("user"):
            st.image(image, caption=user_text)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            try:
                for chunk in ai_stream_gemini(user_text, image=image):
                    full_response = chunk
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
                if full_response:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response,
                        "type": "text"
                    })
            except Exception as e:
                placeholder.error(f"Error: {e}")

    elif prompt.get("text"):
        user_text = prompt["text"]
        st.session_state.messages.append({"role": "user", "content": user_text, "type": "text"})
        with st.chat_message("user"):
            st.markdown(user_text)
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            try:
                for chunk in ai_stream_gemini(user_text):
                    full_response = chunk
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
                if full_response:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response,
                        "type": "text"
                    })
            except Exception as e:
                placeholder.error(f"Error: {e}")

    st.session_state.processing = False
    st.rerun()
