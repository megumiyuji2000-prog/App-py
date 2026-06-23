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

st.set_page_config(page_title="Orion AI", page_icon="logo.png", layout="centered")

# ==================== CEK SECRETS DULU ====================
try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("API Key belum diisi. Masuk Manage app → Settings → Secrets")
    st.code('GEMINI_API_KEY = "xxx"\nGROQ_API_KEY = "xxx"', language="toml")
    st.stop()

# ==================== LIMIT CHAT ====================
MAX_CHAT = 25
if "chat_count" not in st.session_state:
    st.session_state.chat_count = 0

# ==================== AUTO DARK/LIGHT ====================
jakarta_tz = pytz.timezone('Asia/Jakarta')
current_hour = datetime.now(jakarta_tz).hour
IS_DARK = not (6 <= current_hour < 18)

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
    "toast_bg": "#27272A" if IS_DARK else "#FFFFFF",
}

# ==================== CSS ====================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    #MainMenu, footer, header {{visibility: hidden;}}
.stApp,.main {{ background-color: {THEME['bg']}; }}
.block-container {{ padding-top: 1rem!important; padding-bottom: 7rem!important; max-width: 42rem!important; }}
.orion-logo {{ position: fixed; top: 18px; right: 18px; z-index: 999; width: 36px; height: 36px; }}
.orion-logo img {{ border-radius: 8px; }}
.meta-opening {{ margin-top: 25vh; margin-bottom: 2rem; }}
.meta-title {{ font-size: 2rem; font-weight: 700; color: {THEME['text']}; margin-bottom: 2rem; line-height: 1.2; }}
.meta-btn {{ display: block; width: 100%; text-align: left; padding: 14px 18px; margin-bottom: 12px; background-color: {THEME['chat_bg']}; border: 1px solid {THEME['border']}; border-radius: 24px; color: {THEME['text']}; font-size: 0.95rem; cursor: pointer; transition: all 0.2s; }}
.meta-btn:hover {{ border-color: {THEME['primary']}; background-color: {THEME['user_chat_bg']}; }}
.meta-btn-icon {{ margin-right: 12px; font-size: 1.1rem; }}
    [data-testid="stChatMessageContent"] {{ background-color: {THEME['chat_bg']}!important; border-radius: 18px!important; padding: 14px 18px!important; color: {THEME['text']}!important; border: 1px solid {THEME['border']}; line-height: 1.8; font-size: 0.95rem; }}
.stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"] {{ background-color: {THEME['user_chat_bg']}!important; }}
.stChatInput > div {{ background-color: {THEME['bg']}!important; border: 1px solid {THEME['input_border']}!important; border-radius: 24px!important; }}
.orion-badge {{ display: inline-block; font-size: 0.7rem; padding: 3px 8px; border-radius: 10px; margin-bottom: 8px; font-weight: 600; background-color: {THEME['badge_bg']}; color: {THEME['badge_text']}; border: 1px solid {THEME['border']}; }}
   [data-testid="stChatMessageContent"] h3 {{ font-size: 1rem!important; font-weight: 600!important; margin: 14px 0 6px 0!important; color: {THEME['text']}!important; }}
   [data-testid="stChatMessageContent"] ul {{ margin: 6px 0!important; padding-left: 18px!important; }}
   [data-testid="stChatMessageContent"] li {{ margin-bottom: 4px!important; }}
   [data-testid="stChatMessageContent"] strong {{ color: #7C3AED!important; font-weight: 600!important; }}
.orion-toast {{ position: fixed; top: 70px; right: 20px; z-index: 9999; background: {THEME['toast_bg']}; color: {THEME['text']}; padding: 12px 16px; border-radius: 12px; border: 1px solid {THEME['border']}; box-shadow: 0 4px 12px rgba(0,0,0,0.15); display: flex; align-items: center; gap: 12px; max-width: 320px; animation: slideIn 0.3s ease; }}
.orion-toast-close {{ background: none; border: none; color: {THEME['badge_text']}; font-size: 18px; cursor: pointer; padding: 0 4px; }}
   @keyframes slideIn {{ from {{ transform: translateX(100%); opacity: 0; }} to {{ transform: translateX(0); opacity: 1; }} }}
</style>
""", unsafe_allow_html=True)

# LOGO
try:
    with open("logo.png", "rb") as f:
        data = base64.b64encode(f.read()).decode()
    st.markdown(f'<div class="orion-logo"><img src="data:image/png;base64,{data}"></div>', unsafe_allow_html=True)
except:
    pass

# ==================== INIT API - GAK PAKE CACHE + GAK PAKE start_chat ====================
genai.configure(api_key=GEMINI_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')
groq_client = Groq(api_key=GROQ_KEY)

if "messages" not in st.session_state: st.session_state.messages = []
if "last_generated_prompt" not in st.session_state: st.session_state.last_generated_prompt = None

# ==================== TOAST CUSTOM ====================
def show_custom_toast(message, icon="🎨"):
    toast_placeholder = st.empty()
    toast_id = f"toast_{int(time.time()*1000)}"
    toast_html = f"""
    <div id="{toast_id}" class="orion-toast">
        <span>{icon} {message}</span>
        <button class="orion-toast-close" onclick="document.getElementById('{toast_id}').remove()">×</button>
    </div>
    <script>
        setTimeout(() => {{
            const el = document.getElementById('{toast_id}');
            if(el) el.remove();
        }}, 5000);
    </script>
    """
    toast_placeholder.markdown(toast_html, unsafe_allow_html=True)

# ==================== ORION BRAIN V7.2 ====================
def deteksi_tingkat(text):
    t = text.lower()
    if any(k in t for k in ["solusi", "pecahkan", "selesaikan", "masalah", "problem", "gimana caranya", "bantu atasi", "jalan keluar", "saran", "bingung", "pusing"]):
        return "problem_solver"
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
    show_custom_toast("Maaf jika hasilnya kurang memuaskan 🙏", "🎨")
    st.session_state.last_generated_prompt = prompt
    encoded = urllib.parse.quote(prompt[:200])
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={int(time.time())%10000}"
    try:
        r = requests.get(url, timeout=45)
        if r.status_code == 200:
            return Image.open(io.BytesIO(r.content)).convert("RGB"), None
        return None, "Server sedang penuh"
    except:
        return None, "Terjadi kesalahan, silakan coba lagi"

def remix_gambar_hasil_generate(prompt_remix):
    if not st.session_state.last_generated_prompt:
        return None, "Buat gambar dulu baru bisa di-remix. Contoh: 'buatkan gambar kucing'"

    show_custom_toast("Maaf jika hasilnya kurang memuaskan 🙏", "✨")
    full_prompt = f"{st.session_state.last_generated_prompt}, {prompt_remix}"
    st.session_state.last_generated_prompt = full_prompt

    encoded = urllib.parse.quote(full_prompt[:200])
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={int(time.time())%10000}"
    try:
        r = requests.get(url, timeout=45)
        if r.status_code == 200:
            return Image.open(io.BytesIO(r.content)).convert("RGB"), None
        return None, "Gagal me-remix gambar"
    except:
        return None, "Terjadi kesalahan saat remix"

def image_to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def kirim_ke_ai(prompt, image=None):
    tingkat = deteksi_tingkat(prompt)

    if tingkat == "image":
        img, err = generate_gambar(prompt)
        if img: return [("image", img, tingkat)]
        return [("text", f"Gagal membuat gambar: {err}", "ngobrol")]

    if tingkat == "remix":
        img, err = remix_gambar_hasil_generate(prompt)
        if img: return [("image", img, "remix")]
        return [("text", f"Gagal remix: {err}", "ngobrol")]

    tgl = datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%d %B %Y')

    system_prompt = f"""Anda adalah Orion. Asisten AI cerdas yang membantu menyelesaikan masalah apa pun. Tanggal: {tgl}.

KEPRIBADIAN:
Profesional, empatik, dan solutif. Gunakan bahasa Indonesia yang sopan, jelas, dan mudah dipahami semua kalangan. Gunakan kata "Anda" atau "kamu".

ATURAN PARAGRAF MUTLAK:
1. **NGOBROL**: WAJIB 2 paragraf. WAJIB 5 baris per paragraf.
2. **NGAJAR SD-SMP**: 2-3 paragraf. WAJIB 5 baris per paragraf.
3. **NGAJAR SMA**: 3-4 paragraf. WAJIB 5 baris per paragraf.
4. **NGAJAR KULIAH/S3**: 3-5 paragraf. WAJIB 5 baris per paragraf.
5. **PROBLEM SOLVER**: 3-4 paragraf. WAJIB 5 baris per paragraf.

FORMAT PROBLEM SOLVER WAJIB:
Basa basi-
[Baris 1: Empati ke masalah user]
[Baris 2: Validasi bahwa masalahnya wajar]
[Baris 3: Kasih harapan bahwa ada jalan keluar]
[Baris 4: Tegaskan Orion akan bantu step by step]
[Baris 5: Transisi ke solusi]

Oke jadi begini caranya
1. [Langkah 1 + penjelasan singkat]
   [Contoh konkret langkah 1]
2. [Langkah 2 + penjelasan singkat]
   [Contoh konkret langkah 2]
3. [Langkah 3 + penjelasan singkat]
   [Contoh konkret langkah 3]

Jadi gitu cara mengatasinya
[Baris 1: Rangkum solusi inti]
[Baris 2: Tekankan manfaat jika diterapkan]
[Baris 3: Motivasi bahwa user pasti bisa]
[Baris 4: Tawarkan bantuan lanjutan jika masih bingung]
[Baris 5: Sudah paham kan?]

STRUKTUR LAIN: Pake ### Heading, bullet `-`, **bold** untuk kata kunci.

ATURAN LAIN:
1. Jangan sebut "AI" atau "model". Anda adalah Orion.
2. Langsung ke inti jawaban. Jangan bertele-tele."""

    full_prompt = system_prompt + f"\n\nJenis: {tingkat}\nPertanyaan user: {prompt}"

    # GAK PAKE start_chat - LANGSUNG generate_content BIAR GAK HANG
    try:
        if image:
            res = gemini_model.generate_content([full_prompt, image])
        else:
            res = gemini_model.generate_content(full_prompt)
        return [("text", res.text, tingkat)]
    except Exception as e:
        try:
            chat = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": full_prompt}],
                model="llama-3.3-70b-versatile",
                max_tokens=2000,
                temperature=0.3
            )
            return [("text", chat.choices[0].message.content, tingkat)]
        except:
            return [("text", "Mohon maaf, terjadi gangguan sistem.\nSilakan coba lagi dalam 1 menit.\nKami sedang mengupayakan perbaikan secepatnya.\nData Anda tetap aman.\nTerima kasih atas pengertiannya.", "ngobrol")]

# ==================== UI OPENING ====================
if not st.session_state.messages:
    st.markdown(f"""
    <div class="meta-opening">
        <div class="meta-title">Ada yang bisa<br>Orion bantu?</div>
        <button class="meta-btn" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'Buat gambar'}}, '*')">
            <span class="meta-btn-icon">🖼️</span> Buat gambar
        </button>
        <button class="meta-btn" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'Bantu selesaikan masalah saya'}}, '*')">
            <span class="meta-btn-icon">💡</span> Bantu selesaikan masalah
        </button>
        <button class="meta-btn" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'Belajar dan berkembang'}}, '*')">
            <span class="meta-btn-icon">🎓</span> Belajar dan berkembang
        </button>
    </div>
    """, unsafe_allow_html=True)

# NOTIF LIMIT
sisa_chat = MAX_CHAT - st.session_state.chat_count
if sisa_chat == 3:
    st.toast("Sesi ngobrol hampir habis, persiapkan pertanyaan terakhir Anda", icon="⚠️")

# TAMPILIN CHAT
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            badge_class = msg.get("tingkat", "ngobrol")
            badge_text = {"image": "🎨 GAMBAR", "remix": "✨ REMIX", "sd": "📘 SD", "smp": "📗 SMP", "sma": "📙 SMA", "kuliah": "📕 KULIAH", "ngobrol": "💬 NGOBROL", "problem_solver": "💡 SOLUSI"}.get(badge_class, "💬")
            st.markdown(f'<div class="orion-badge {badge_class}">{badge_text}</div>', unsafe_allow_html=True)

        if msg["type"] == "image":
            st.image(msg["content"], use_container_width=True)
            st.download_button("📥 Unduh", image_to_bytes(msg["content"]), f"orion_{i}.png", "image/png", key=f"dl_{i}", use_container_width=True)
        else:
            st.markdown(msg["content"], unsafe_allow_html=True)

# HANDLE INPUT - GAK PAKE st.rerun() BIAR GAK LOOP
prompt = st.chat_input("Tanya Orion...", accept_file=True, file_type=["jpg","png","jpeg"])

if prompt:
    # CEK LIMIT
    if st.session_state.chat_count >= MAX_CHAT:
        st.error("Sesi ngobrol hari ini sudah habis. Silakan kembali besok 🙏")
        st.stop()

    st.session_state.chat_count += 1

    if hasattr(prompt, 'text'):
        user_text = prompt.text
        user_file = prompt.files[0] if prompt.files else None
    else:
        user_text = prompt.get("text", "") if isinstance(prompt, dict) else prompt
        user_file = prompt.get("files", [None])[0] if isinstance(prompt, dict) and prompt.get("files") else None

    user_img = None

    if user_file:
        user_img = Image.open(user_file).convert("RGB")
        st.session_state.messages.append({"role": "user", "type": "image", "content": user_img})

    if user_text:
        st.session_state.messages.append({"role": "user", "type": "text", "content": user_text})

    # PROSES AI
    hasil = kirim_ke_ai(user_text, user_img)
    for tipe, konten, *rest in hasil:
        tingkat = rest[0] if rest else "ngobrol"
        st.session_state.messages.append({"role": "assistant", "type": tipe, "content": konten, "tingkat": tingkat})
