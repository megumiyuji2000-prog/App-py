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
import re

st.set_page_config(page_title="Orion AI", page_icon="logo.png", layout="wide", initial_sidebar_state="collapsed")

# ==================== CEK SECRETS ====================
try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("API Key belum diisi. Masuk Manage app → Settings → Secrets")
    st.code('GEMINI_API_KEY = "xxx"\nGROQ_API_KEY = "xxx"', language="toml")
    st.stop()

# ==================== MULTI CHAT SYSTEM ====================
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {"chat_1": {"title": "Obrolan Baru", "messages": [], "chat_count": 0}}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = "chat_1"
if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = False

MAX_CHAT = 25

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
    "sidebar_bg": "#18181B" if IS_DARK else "#FAFAFA",
}

# ==================== CSS + AUTO SCROLL BUTTON ====================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    #MainMenu, footer, header {{visibility: hidden;}}
.stApp,.main {{ background-color: {THEME['bg']}; }}
.block-container {{ padding-top: 4rem!important; padding-bottom: 7rem!important; max-width: 42rem!important; }}
.orion-logo {{ position: fixed; top: 18px; right: 18px; z-index: 999; width: 36px; height: 36px; }}
.orion-logo img {{ border-radius: 8px; }}
.hamburger-btn {{ position: fixed; top: 18px; left: 18px; z-index: 1000; width: 36px; height: 36px; background: {THEME['chat_bg']}; border: 1px solid {THEME['border']}; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; }}
.hamburger-btn:hover {{ background: {THEME['user_chat_bg']}; }}
.hamburger-icon {{ width: 18px; height: 2px; background: {THEME['text']}; position: relative; }}
.hamburger-icon::before,.hamburger-icon::after {{ content: ''; position: absolute; width: 18px; height: 2px; background: {THEME['text']}; left: 0; }}
.hamburger-icon::before {{ top: -5px; }}
.hamburger-icon::after {{ top: 5px; }}
.chat-title {{ position: fixed; top: 18px; left: 50%; transform: translateX(-50%); z-index: 999; color: {THEME['text']}; font-weight: 600; font-size: 0.95rem; max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}

/* SIDEBAR */
.sidebar {{ position: fixed; top: 0; left: -300px; width: 280px; height: 100vh; background: {THEME['sidebar_bg']}; border-right: 1px solid {THEME['border']}; z-index: 1001; transition: left 0.3s ease; overflow-y: auto; padding: 70px 16px 20px 16px; }}
.sidebar.open {{ left: 0; }}
.sidebar-overlay {{ position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.5); z-index: 1000; display: none; }}
.sidebar-overlay.show {{ display: block; }}
.sidebar-item {{ padding: 12px 16px; margin-bottom: 4px; border-radius: 12px; color: {THEME['text']}; cursor: pointer; display: flex; align-items: center; gap: 12px; font-size: 0.9rem; }}
.sidebar-item:hover {{ background: {THEME['user_chat_bg']}; }}
.sidebar-divider {{ height: 1px; background: {THEME['border']}; margin: 12px 0; }}
.sidebar-section {{ color: {THEME['badge_text']}; font-size: 0.75rem; font-weight: 600; padding: 8px 16px; }}
.chat-history-item {{ padding: 10px 16px; margin-bottom: 4px; border-radius: 12px; color: {THEME['text']}; cursor: pointer; font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.chat-history-item:hover {{ background: {THEME['user_chat_bg']}; }}
.chat-history-item.active {{ background: {THEME['user_chat_bg']}; }}

/* TOMBOL AUTO SCROLL */
#scroll-bottom-btn {{
    position: fixed;
    bottom: 90px;
    right: 20px;
    width: 40px;
    height: 40px;
    background: {THEME['chat_bg']};
    border: 1px solid {THEME['border']};
    border-radius: 50%;
    z-index: 999;
    cursor: pointer;
    display: none;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    transition: all 0.2s;
}}
#scroll-bottom-btn:hover {{ background: {THEME['user_chat_bg']}; }}
#scroll-bottom-btn svg {{ width: 20px; height: 20px; fill: {THEME['text']}; }}

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

<!-- TOMBOL AUTO SCROLL -->
<button id="scroll-bottom-btn" onclick="window.scrollTo({{top: document.body.scrollHeight, behavior: 'smooth'}})">
    <svg viewBox="0 0 24 24"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>
</button>

<script>
// AUTO SHOW/HIDE SCROLL BUTTON
window.addEventListener('scroll', function() {{
    const btn = document.getElementById('scroll-bottom-btn');
    const scrollPosition = window.innerHeight + window.scrollY;
    const pageHeight = document.body.offsetHeight;
    if (scrollPosition < pageHeight - 200) {{
        btn.style.display = 'flex';
    }} else {{
        btn.style.display = 'none';
    }}
}});
</script>
""", unsafe_allow_html=True)

# LOGO
try:
    with open("logo.png", "rb") as f:
        data = base64.b64encode(f.read()).decode()
    st.markdown(f'<div class="orion-logo"><img src="data:image/png;base64,{data}"></div>', unsafe_allow_html=True)
except:
    pass

# ==================== INIT API ====================
genai.configure(api_key=GEMINI_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')
groq_client = Groq(api_key=GROQ_KEY)

if "last_generated_prompt" not in st.session_state: st.session_state.last_generated_prompt = None

# ==================== FUNGSI SIDEBAR ====================
def toggle_sidebar():
    st.session_state.sidebar_open = not st.session_state.sidebar_open

def new_chat():
    chat_id = f"chat_{int(time.time())}"
    st.session_state.all_chats[chat_id] = {"title": "Obrolan Baru", "messages": [], "chat_count": 0}
    st.session_state.current_chat_id = chat_id
    st.session_state.sidebar_open = False

def switch_chat(chat_id):
    st.session_state.current_chat_id = chat_id
    st.session_state.sidebar_open = False

# ==================== JUDUL OTOMATIS ====================
def generate_title(text):
    # Ambil inti kalimat, hapus kata tanya
    text = re.sub(r'^(bisa|tolong|gimana|bagaimana|cara|bantu)\s+', '', text.lower())
    text = text.strip().capitalize()
    return text[:40] + "..." if len(text) > 40 else text

# ==================== SIDEBAR HTML ====================
current_chat = st.session_state.all_chats[st.session_state.current_chat_id]
sidebar_html = f"""
<div class="hamburger-btn" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'toggle_sidebar'}}, '*')">
    <div class="hamburger-icon"></div>
</div>
<div class="chat-title">{current_chat['title']}</div>

<div class="sidebar-overlay {'show' if st.session_state.sidebar_open else ''}" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'toggle_sidebar'}}, '*')"></div>
<div class="sidebar {'open' if st.session_state.sidebar_open else ''}">
    <div class="sidebar-item" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'new_chat'}}, '*')">
        <span>✏️</span> Obrolan baru
    </div>
    <div class="sidebar-divider"></div>
    <div class="sidebar-item"><span>✨</span> Vibes</div>
    <div class="sidebar-item"><span>👓</span> Kacamata</div>
    <div class="sidebar-item"><span>🖼️</span> Media</div>
    <div class="sidebar-item"><span>🔔</span> Notifikasi</div>
    <div class="sidebar-divider"></div>
    <div class="sidebar-section">Obrolan</div>
"""

for cid, chat in st.session_state.all_chats.items():
    active = "active" if cid == st.session_state.current_chat_id else ""
    sidebar_html += f"""
    <div class="chat-history-item {active}" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'switch_{cid}'}}, '*')">
        {chat['title']}
    </div>
    """

sidebar_html += "</div>"
st.markdown(sidebar_html, unsafe_allow_html=True)

# HANDLE SIDEBAR CLICK
if "component_value" in st.query_params:
    val = st.query_params["component_value"]
    if val == "toggle_sidebar":
        toggle_sidebar()
        st.query_params.clear()
        st.rerun()
    elif val == "new_chat":
        new_chat()
        st.query_params.clear()
        st.rerun()
    elif val.startswith("switch_"):
        switch_chat(val.replace("switch_", ""))
        st.query_params.clear()
        st.rerun()

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

# ==================== ORION BRAIN ====================
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
if not current_chat['messages']:
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
sisa_chat = MAX_CHAT - current_chat['chat_count']
if sisa_chat == 3:
    st.toast("Sesi ngobrol hampir habis, persiapkan pertanyaan terakhir Anda", icon="⚠️")

# TAMPILIN CHAT
for i, msg in enumerate(current_chat['messages']):
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            badge_class = msg.get("tingkat", "ngobrol")
            badge_text = {"image": "🎨 GAMBAR", "remix": "✨ REMIX", "sd": "📘 SD", "smp": "📗 SMP", "sma": "📙 SMA", "kuliah": "📕 KULIAH", "ngobrol": "💬 NGOBROL", "problem_solver": "💡 SOLUSI"}.get(badge_class, "💬")
            st.markdown(f'<div class="orion-badge {badge_class}">{badge_text}</div>', unsafe_allow_html=True)

        if msg["type"] == "image":
            st.image(msg["content"], use_container_width=True)
          
