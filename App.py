import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
from datetime import datetime
import pytz
import time
import requests
import io
import urllib.parse
import base64

st.set_page_config(page_title="Fanilla AI", page_icon="logo.png", layout="centered")

# ==================== AUTO DARK/LIGHT BERDASAR WAKTU ====================
jakarta_tz = pytz.timezone('Asia/Jakarta')
current_hour = datetime.now(jakarta_tz).hour
IS_DARK = not (6 <= current_hour < 18) # 06:00-17:59 terang, sisanya gelap

THEME = {
    "bg": "#0A0A0B" if IS_DARK else "#FFFFFF",
    "chat_bg": "#18181B" if IS_DARK else "#F4F4F5",
    "user_chat_bg": "#27272A" if IS_DARK else "#E4E4E7",
    "text": "#E4E4E7" if IS_DARK else "#18181B",
    "border": "#27272A" if IS_DARK else "#E4E4E7",
    "badge_bg": "#18181B" if IS_DARK else "#F4F4F5",
    "badge_text": "#A1A1AA" if IS_DARK else "#71717A",
    "input_border": "#A78BFA",
    "primary": "#A78BFA",
}

# ==================== CSS DYNAMIC ====================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    #MainMenu, footer, header {{visibility: hidden;}}
  .stApp,.main {{ background-color: {THEME['bg']}; }}
  .block-container {{ padding-top: 1rem!important; padding-bottom: 7rem!important; max-width: 42rem!important; }}
  .fanilla-logo {{ position: fixed; top: 18px; left: 18px; z-index: 999; width: 36px; height: 36px; }}
  .fanilla-logo img {{ border-radius: 8px; }}
    /* OPENING META AI STYLE */
  .meta-opening {{ margin-top: 25vh; margin-bottom: 2rem; }}
  .meta-title {{ font-size: 2rem; font-weight: 700; color: {THEME['text']}; margin-bottom: 2rem; line-height: 1.2; }}
  .meta-btn {{ display: block; width: 100%; text-align: left; padding: 14px 18px; margin-bottom: 12px; background-color: {THEME['chat_bg']}; border: 1px solid {THEME['border']}; border-radius: 24px; color: {THEME['text']}; font-size: 0.95rem; cursor: pointer; transition: all 0.2s; }}
  .meta-btn:hover {{ border-color: {THEME['primary']}; background-color: {THEME['user_chat_bg']}; }}
  .meta-btn-icon {{ margin-right: 12px; font-size: 1.1rem; }}

    [data-testid="stChatMessageContent"] {{ background-color: {THEME['chat_bg']}!important; border-radius: 18px!important; padding: 14px 18px!important; color: {THEME['text']}!important; border: 1px solid {THEME['border']}; line-height: 1.8; font-size: 0.95rem; }}
  .stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"] {{ background-color: {THEME['user_chat_bg']}!important; }}
  .stChatInput > div {{ background-color: {THEME['bg']}!important; border: 1px solid {THEME['input_border']}!important; border-radius: 24px!important; }}
  .fanilla-badge {{ display: inline-block; font-size: 0.7rem; padding: 3px 8px; border-radius: 10px; margin-bottom: 8px; font-weight: 600; background-color: {THEME['badge_bg']}; color: {THEME['badge_text']}; border: 1px solid {THEME['border']}; }}
   [data-testid="stChatMessageContent"] h3 {{ font-size: 1rem!important; font-weight: 600!important; margin: 14px 0 6px 0!important; color: {THEME['text']}!important; }}
   [data-testid="stChatMessageContent"] ul {{ margin: 6px 0!important; padding-left: 18px!important; }}
   [data-testid="stChatMessageContent"] li {{ margin-bottom: 4px!important; }}
   [data-testid="stChatMessageContent"] strong {{ color: #7C3AED!important; font-weight: 600!important; }}
</style>
""", unsafe_allow_html=True)

# LOGO
try:
    with open("logo.png", "rb") as f:
        data = base64.b64encode(f.read()).decode()
    st.markdown(f'<div class="fanilla-logo"><img src="data:image/png;base64,{data}"></div>', unsafe_allow_html=True)
except: pass

# ==================== INIT ====================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error(f"API Key error: {e}")
    st.stop()

if "messages" not in st.session_state: st.session_state.messages = []
if "gemini_chat" not in st.session_state: st.session_state.gemini_chat = gemini_model.start_chat(history=[])
if "last_generated_prompt" not in st.session_state: st.session_state.last_generated_prompt = None

# ==================== FANILLA BRAIN V5.0 ====================
def deteksi_tingkat(text):
    t = text.lower()
    if any(k in t for k in ["s3", "disertasi", "rbv", "dynamic capabilities", "transformer", "freire", "dekonstruksi", "backpropagation", "doktoral"]):
        return "kuliah"
    if any(k in t for k in ["ubah jadi", "jadiin", "remix", "ganti style", "versi", "ganti jadi"]) and st.session_state.last_generated_prompt:
        return "remix"
    if any(k in t for k in ["gambar", "bikin", "lukis", "draw", "buatin", "generate"]):
        return "image"
    if any(k in t for k in ["sd","kelas 1","kelas 2","kelas 3","kelas 4","kelas 5","kelas 6","penjumlahan","perkalian","untuk anak"]): return "sd"
    if any(k in t for k in ["smp","kelas 7","kelas 8","kelas 9","aljabar","persamaan"]): return "smp"
    if any(k in t for k in ["sma","kelas 10","kelas 11","kelas 12","utbk","snbt","limit","turunan","integral"]): return "sma"
    if any(k in t for k in ["kuliah","kalkulus","aljabar linear","statistik","matkul","universitas"]): return "kuliah"
    return "ngobrol"

def generate_gambar(prompt):
    try:
        st.toast("Fanilla lagi ngelukis... Maaf jika gambar kurang memuaskan atau bagus 🙏", icon="🎨")
        st.session_state.last_generated_prompt = prompt
        encoded = urllib.parse.quote(prompt[:200])
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={int(time.time())%10000}"
        r = requests.get(url, timeout=45)
        if r.status_code == 200:
            return Image.open(io.BytesIO(r.content)).convert("RGB"), None
        return None, "Server lagi penuh"
    except Exception as e:
        return None, "Error bro, coba lagi"

def remix_gambar_hasil_generate(prompt_remix):
    if not st.session_state.last_generated_prompt:
        return None, "Bikin gambar dulu bro baru bisa di-remix. Contoh: 'bikin gambar kucing'"

    try:
        st.toast("Fanilla lagi nge-remix... Maaf jika gambar kurang memuaskan atau bagus 🙏", icon="✨")
        full_prompt = f"{st.session_state.last_generated_prompt}, {prompt_remix}"
        st.session_state.last_generated_prompt = full_prompt

        encoded = urllib.parse.quote(full_prompt[:200])
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={int(time.time())%10000}"
        r = requests.get(url, timeout=45)
        if r.status_code == 200:
            return Image.open(io.BytesIO(r.content)).convert("RGB"), None
        return None, "Gagal remix"
    except Exception as e:
        return None, "Error remix"

def image_to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def kirim_ke_ai(prompt, image=None):
    tingkat = deteksi_tingkat(prompt)

    if tingkat == "image":
        img, err = generate_gambar(prompt)
        if img: return [("image", img, tingkat)]
        return [("text", f"Gagal bro: {err}", "ngobrol")]

    if tingkat == "remix":
        img, err = remix_gambar_hasil_generate(prompt)
        if img: return [("image", img, "remix")]
        return [("text", f"Gagal remix: {err}", "ngobrol")]

    tgl = datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%d %B %Y')

    # ========== PROMPT SEMPURNA V5.0 ==========
    system_prompt = f"""Kamu adalah Fanilla. Asisten AI analitis, rapi, to the point. Tanggal: {tgl}.

ATURAN PARAGRAF MUTLAK:
1. **NGOBROL**: WAJIB 2 paragraf. WAJIB 5 baris per paragraf. Total 10 baris.
   Format:
   Baris 1
   Baris 2
   Baris 3
   Baris 4
   Baris 5

   Baris 6
   Baris 7
   Baris 8
   Baris 9
   Baris 10

2. **NGAJAR SD-SMP**: 2-3 paragraf. WAJIB 5 baris per paragraf.
3. **NGAJAR SMA**: 3-4 paragraf. WAJIB 5 baris per paragraf.
4. **NGAJAR KULIAH/S3**: 3-5 paragraf. WAJIB 5 baris per paragraf.

STRUKTUR WAJIB: Pake ### Heading, bullet `-`, **bold** keyword.

CONTOH NGOBROL BENAR [2 paragraf, 5 baris/paragraf]:
Senang bisa bantu lu bro. Kalo ada tugas numpuk atau materi yg ga ngerti, tinggal tanya.
Gua bakal bedah pake bahasa sederhana dan struktur yg gampang diikutin.
Buat anak SD gua pake analogi mainan. Buat SMP pake analogi game.
Buat SMA gua kasih step-by-step plus tips ngafalin biar UTBK aman.
Buat kuliah sampe S3, gua bantu bedah jurnal sampe bikin sintesis teori.

Selain ngajar, gua juga bisa diajak ngobrol santai kalo lu gabut.
Butuh temen curhat? Gas aja. Mau bahas anime, bola, atau drama? Bisa.
Gua juga bisa bikinin gambar kalo lu butuh visualisasi materi.
Udah jadi bisa di-remix stylenya, terus langsung download.
Intinya anggap gua asisten pribadi lu yg standby 24/7. Deal?

CONTOH NGAJAR KULIAH BENAR [4 paragraf, 5 baris/paragraf]:
### Core Ide
RBV bilang keunggulan kompetitif tahan lama muncul kalo sumber daya lu **VRIN**.
Itu singkatan dari Valuable, Rare, Inimitable, Non-substitutable.
Tapi di era disrupsi kayak sekarang, VRIN aja ga cukup bro.
Kenapa? Karena kompetensi bisa kadaluarsa cepet banget.
TikTok bisa matiin Instagram Reels dalam setahun.

### Kritik Utama Teori
- **Statis**: RBV ga jelasin gimana perusahaan bikin resources baru pas pasar berubah.
- **Butuh Dynamic Capabilities**: Teece bilang firm harus bisa `sense` peluang, `seize` kesempatan.
- **Reconfig**: Sumber daya lama harus bisa dibongkar pasang jadi bentuk baru.
- **Contoh**: Nokia punya VRIN di hardware, tapi gagal reconfig ke software.
- **Akibatnya**: Bubar walau resources-nya dulu langka.

### Analisis Kasus GoTo
**Strength RBV**: `network effect` driver+merchant GoTo itu *valuable* & *rare*.
Susah ditiru 100% sama kompetitor karena butuh waktu dan bakar duit.
Tapi ini cuma fondasi awal. Ga jamin menang selamanya.
**Kelemahan RBV**: Ga jelasin gimana GoTo pivot pas Covid dari transport ke logistik.
Itu butuh **Dynamic Capabilities**, bukan cuma resources statis.

### Sintesis S3
**RBV jelasin fondasi awal**, tapi **Dynamic Capabilities jelasin sustain-nya**.
Tanpa kemampuan adaptasi, VRIN GoTo mati. Jadi keunggulan GoTo = RBV + kemampuan reconfig.
Jawaban level S3 harus kritik teori, bukan cuma hapal definisi.
Kaitkan sama konteks Indonesia biar dapet nilai A. Paham kan?

ATURAN LAIN:
1. Jangan sebut "AI", "model". Lu Fanilla.
2. Pake "lu/gua". "Bro" max 2x per jawaban.
3. Jangan mulai "Berikut adalah". Langsung tembak isi."""

    full_prompt = system_prompt + f"\n\nTingkat: {tingkat}\nPertanyaan user: {prompt}"

    try:
        if image:
            res = st.session_state.gemini_chat.send_message([full_prompt, image], stream=False)
        else:
            res = st.session_state.gemini_chat.send_message(full_prompt, stream=False)
        return [("text", res.text, tingkat)]
    except:
        try:
            chat = groq_client.chat.completions.create(messages=[{"role": "user", "content": full_prompt}], model="llama-3.3-70b-versatile", max_tokens=2000, temperature=0.2)
            return [("text", chat.choices[0].message.content, tingkat)]
        except:
            return [("text", "Waduh error bro, coba lagi.\nSistem lagi ada gangguan bentar.\nCoba refresh atau tanya ulang 1 menit lagi.\nMaaf ya, gua usahain cepet normal.\nTenang aja data lu aman.", "ngobrol")]

# ==================== UI OPENING META AI STYLE ====================
if not st.session_state.messages:
    st.markdown(f"""
    <div class="meta-opening">
        <div class="meta-title">Kita memulai<br>dari mana?</div>
        <button class="meta-btn" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'Animasikan foto saya'}}, '*')">
            <span class="meta-btn-icon">🎬</span> Animasikan foto saya
        </button>
        <button class="meta-btn" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'Buat gambar'}}, '*')">
            <span class="meta-btn-icon">🖼️</span> Buat gambar
        </button>
        <button class="meta-btn" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'Belajar dan berkembang'}}, '*')">
            <span class="meta-btn-icon">🎓</span> Belajar dan berkembang
        </button>
        <button class="meta-btn" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'Analisis untuk saya'}}, '*')">
            <span class="meta-btn-icon">💡</span> Analisis untuk saya
        </button>
    </div>
    """, unsafe_allow_html=True)

# TAMPILIN CHAT
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            badge_class = msg.get("tingkat", "ngobrol")
            badge_text = {"image": "🎨 GAMBAR", "remix": "✨ REMIX", "sd": "📘 SD", "smp": "📗 SMP", "sma": "📙 SMA", "kuliah": "📕 KULIAH", "ngobrol": "💬 NGOBROL"}.get(badge_class, "💬")
            st.markdown(f'<div class="fanilla-badge {badge_class}">{badge_text}</div>', unsafe_allow_html=True)

        if msg["type"] == "image":
            st.image(msg["content"], use_container_width=True)
            st.download_button("📥 Download", image_to_bytes(msg["content"]), f"fanilla_{i}.png", "image/png", key=f"dl_{i}", use_container_width=True)
        else:
            st.markdown(msg["content"], unsafe_allow_html=True)

# HANDLE TOMBOL SHORTCUT
if "shortcut" not in st.session_state:
    st.session_state.shortcut = None

prompt = st.chat_input("Tanya Fanilla...", accept_file=True, file_type=["jpg","png","jpeg"])

# Handle shortcut click
if st.session_state.shortcut:
    prompt = {"text": st.session_state.shortcut}
    st.session_state.shortcut = None

if prompt:
    user_text = prompt.get("text", "") if isinstance(prompt, dict) else prompt
    user_file = prompt.get("files", [None])[0] if isinstance(prompt, dict) and prompt.get("files") else None
    user_img = None

    if user_file:
        user_img = Image.open(user_file).convert("RGB")
        st.session_state.messages.append({"role": "user", "type": "image", "content": user_img})
        with st.chat_message("user"):
            st.image(user_img, caption=user_text if user_text else "Foto soal")

    if user_text:
        if not user_file:
            st.session_state.messages.append({"role": "user", "type": "text", "content": user_text})
            with st.chat_message("user"): st.markdown(user_text)

        with st.chat_message("assistant"):
            with st.spinner("Fanilla mikir..."):
                hasil = kirim_ke_ai(user_text, user_img)
            for tipe, konten, *rest in hasil:
                tingkat = rest[0] if rest else "ngobrol"
                if tipe == "image":
                    st.markdown(f'<div class="fanilla-badge {tingkat}">{ "✨ REMIX" if tingkat == "remix" else "🎨 GAMBAR"}</div>', unsafe_allow_html=True)
                    st.image(konten, use_container_width=True)
                    st.download_button("📥 Download", image_to_bytes(konten), f"fanilla_{int(time.time())}.png", "image/png", key=f"dl_{time.time()}", use_container_width=True)
                    st.session_state.messages.append({"role": "assistant", "type": "image", "content": konten, "tingkat": tingkat})
                else:
                    st.markdown(f'<div class="fanilla-badge {tingkat}">{"💬"}</div>', unsafe_allow_html=True)
                    st.markdown(konten, unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "type": "text", "content": konten, "tingkat": tingkat})
    st.rerun()
