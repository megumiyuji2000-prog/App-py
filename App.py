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

try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("API Key belum diisi. Masuk Manage app → Settings → Secrets")
    st.stop()

if "all_chats" not in st.session_state:
    st.session_state.all_chats = {"chat_1": {"title": "Obrolan Baru", "messages": [], "chat_count": 0}}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = "chat_1"
if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = False
if "last_generated_prompt" not in st.session_state: st.session_state.last_generated_prompt = None

MAX_CHAT = 25
jakarta_tz = pytz.timezone('Asia/Jakarta')
IS_DARK = not (6 <= datetime.now(jakarta_tz).hour < 18)
T = {"bg":"#0A0A0B" if IS_DARK else "#FFFFFF","chat_bg":"#18181B" if IS_DARK else "#F4F4F5","user_bg":"#27272A" if IS_DARK else "#E4E4E7","text":"#E4E4E7" if IS_DARK else "#18181B","border":"#27272A" if IS_DARK else "#E4E4E7","badge_bg":"#18181B" if IS_DARK else "#F4F4F5","badge_text":"#A1A1AA" if IS_DARK else "#71717A","primary":"#A78BFA","sidebar":"#18181B" if IS_DARK else "#FAFAFA"}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif}}#MainMenu,footer,header{{visibility:hidden}}
.stApp,.main{{background-color:{T['bg']}}}.block-container{{padding-top:4rem!important;padding-bottom:120px!important;max-width:42rem!important}}
.orion-logo{{position:fixed;top:18px;right:18px;z-index:999;width:36px;height:36px}}.orion-logo img{{border-radius:8px}}
.hamburger-btn{{position:fixed;top:18px;left:18px;z-index:1002;width:36px;height:36px;background:{T['chat_bg']};border:1px solid {T['border']};border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all.3s}}
.hamburger-btn:hover{{background:{T['user_bg']}}}
.hamburger-icon{{width:18px;height:2px;background:{T['text']};position:relative;transition:all.3s}}
.hamburger-icon::before,.hamburger-icon::after{{content:'';position:absolute;width:18px;height:2px;background:{T['text']};left:0;transition:all.3s}}
.hamburger-icon::before{{top:-5px}}.hamburger-icon::after{{top:5px}}
.hamburger-btn.open.hamburger-icon{{background:transparent}}
.hamburger-btn.open.hamburger-icon::before{{top:0;transform:rotate(45deg)}}
.hamburger-btn.open.hamburger-icon::after{{top:0;transform:rotate(-45deg)}}
.chat-title{{position:fixed;top:18px;left:50%;transform:translateX(-50%);z-index:999;color:{T['text']};font-weight:600;font-size:.95rem;max-width:200px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.sidebar{{position:fixed;top:0;left:-300px;width:280px;height:100vh;background:{T['sidebar']};border-right:1px solid {T['border']};z-index:1001;transition:left.3s ease;overflow-y:auto;padding:70px 16px 20px}}
.sidebar.open{{left:0}}.sidebar-overlay{{position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,0,0,.5);z-index:1000;display:none}}.sidebar-overlay.show{{display:block}}
.sidebar-item{{padding:12px 16px;margin-bottom:4px;border-radius:12px;color:{T['text']};cursor:pointer;display:flex;align-items:center;gap:12px;font-size:.9rem}}
.sidebar-item:hover{{background:{T['user_bg']}}}.sidebar-divider{{height:1px;background:{T['border']};margin:12px 0}}
.sidebar-section{{color:{T['badge_text']};font-size:.75rem;font-weight:600;padding:8px 16px}}
.chat-history-item{{padding:10px 16px;margin-bottom:4px;border-radius:12px;color:{T['text']};cursor:pointer;font-size:.85rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.chat-history-item:hover{{background:{T['user_bg']}}}.chat-history-item.active{{background:{T['user_bg']}}}
.stButton>button[data-testid="scroll-btn"]{{position:fixed!important;bottom:90px!important;right:20px!important;width:40px!important;height:40px!important;background:{T['chat_bg']}!important;border:1px solid {T['border']}!important;border-radius:50%!important;z-index:998!important;cursor:pointer!important;display:flex!important;align-items:center!important;justify-content:center!important;box-shadow:0 2px 8px rgba(0,0,0,.2)!important;padding:0!important;min-height:40px!important}}
.stButton>button[data-testid="scroll-btn"]:hover{{background:{T['user_bg']}!important}}.stButton>button[data-testid="scroll-btn"] p{{font-size:20px!important;margin:0!important}}
.meta-opening{{margin-top:25vh;margin-bottom:2rem}}.meta-title{{font-size:2rem;font-weight:700;color:{T['text']};margin-bottom:2rem;line-height:1.2}}
.meta-btn{{display:block;width:100%;text-align:left;padding:14px 18px;margin-bottom:12px;background-color:{T['chat_bg']};border:1px solid {T['border']};border-radius:24px;color:{T['text']};font-size:.95rem;cursor:pointer;transition:all.2s}}
.meta-btn:hover{{border-color:{T['primary']};background-color:{T['user_bg']}}}.meta-btn-icon{{margin-right:12px;font-size:1.1rem}}
[data-testid="stChatMessageContent"]{{background-color:{T['chat_bg']}!important;border-radius:18px!important;padding:14px 18px!important;color:{T['text']}!important;border:1px solid {T['border']};line-height:1.8;font-size:.95rem}}
.stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"]{{background-color:{T['user_bg']}!important}}
.stChatInput{{position:fixed!important;bottom:0!important;left:50%!important;transform:translateX(-50%)!important;width:100%!important;max-width:42rem!important;padding:0 1rem 1rem 1rem!important;background:{T['bg']}!important;z-index:997!important}}
.stChatInput>div{{background-color:{T['bg']}!important;border:1px solid {T['primary']}!important;border-radius:24px!important}}
.orion-badge{{display:inline-block;font-size:.7rem;padding:3px 8px;border-radius:10px;margin-bottom:8px;font-weight:600;background-color:{T['badge_bg']};color:{T['badge_text']};border:1px solid {T['border']}}}
[data-testid="stChatMessageContent"] h3{{font-size:1rem!important;font-weight:600!important;margin:14px 0 6px 0!important;color:{T['text']}!important}}
[data-testid="stChatMessageContent"] ul{{margin:6px 0!important;padding-left:18px!important}}[data-testid="stChatMessageContent"] li{{margin-bottom:4px!important}}
[data-testid="stChatMessageContent"] strong{{color:#7C3AED!important;font-weight:600!important}}
[data-testid="stChatMessageContent"] a{{color:{T['primary']}!important;text-decoration:underline!important}}
.orion-toast{{position:fixed;top:70px;right:20px;z-index:9999;background:{T['chat_bg']};color:{T['text']};padding:12px 16px;border-radius:12px;border:1px solid {T['border']};box-shadow:0 4px 12px rgba(0,0,0,.15);display:flex;align-items:center;gap:12px;max-width:320px;animation:slideIn.3s ease}}
.orion-toast-close{{background:none;border:none;color:{T['badge_text']};font-size:18px;cursor:pointer;padding:0 4px}}
@keyframes slideIn{{from{{transform:translateX(100%);opacity:0}}to{{transform:translateX(0);opacity:1}}}}
</style>
""", unsafe_allow_html=True)

try:
    with open("logo.png", "rb") as f: data = base64.b64encode(f.read()).decode()
    st.markdown(f'<div class="orion-logo"><img src="data:image/png;base64,{data}"></div>', unsafe_allow_html=True)
except: pass

genai.configure(api_key=GEMINI_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')
groq_client = Groq(api_key=GROQ_KEY)

def toggle_sidebar(): st.session_state.sidebar_open = not st.session_state.sidebar_open
def new_chat():
    cid = f"chat_{int(time.time())}"; st.session_state.all_chats[cid] = {"title": "Obrolan Baru", "messages": [], "chat_count": 0}
    st.session_state.current_chat_id = cid; st.session_state.sidebar_open = False
def switch_chat(cid): st.session_state.current_chat_id = cid; st.session_state.sidebar_open = False
def generate_title(text):
    text = re.sub(r'^(bisa|tolong|gimana|bagaimana|cara|bantu|minta)\s+', '', text.lower()); text = re.sub(r'[?!.]', '', text).strip().capitalize()
    return text[:40] + "..." if len(text) > 40 else text

current_chat = st.session_state.all_chats[st.session_state.current_chat_id]

col1, col2 = st.columns([1, 20])
with col1:
    if st.button("←" if st.session_state.sidebar_open else "≡", key="hamburger", help="Menu"): toggle_sidebar(); st.rerun()
st.markdown(f'<div class="chat-title">{current_chat["title"]}</div>', unsafe_allow_html=True)

if st.session_state.sidebar_open:
    st.markdown(f"""<div class="sidebar-overlay show" onclick="window.parent.postMessage({{type: 'streamlit:closeSidebar'}}, '*')"></div><div class="sidebar open"><div class="sidebar-item" onclick="window.parent.postMessage({{type: 'streamlit:newChat'}}, '*')"><span>✏️</span> Obrolan baru</div><div class="sidebar-divider"></div><div class="sidebar-item"><span>✨</span> Vibes</div><div class="sidebar-item"><span>👓</span> Kacamata</div><div class="sidebar-item"><span>🖼️</span> Media</div><div class="sidebar-item"><span>🔔</span> Notifikasi</div><div class="sidebar-divider"></div><div class="sidebar-section">Obrolan</div>""", unsafe_allow_html=True)
    for cid, chat in st.session_state.all_chats.items():
        if st.button(chat['title'], key=f"chat_{cid}", use_container_width=True): switch_chat(cid); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

if "component_value" in st.query_params:
    val = st.query_params["component_value"]
    if val == "toggle_sidebar": toggle_sidebar()
    elif val == "new_chat": new_chat()
    elif val.startswith("switch_"): switch_chat(val.replace("switch_", ""))
    elif val == "closeSidebar": st.session_state.sidebar_open = False
    st.query_params.clear(); st.rerun()

def show_custom_toast(msg, icon="🎨"):
    ph = st.empty(); tid = f"toast_{int(time.time()*1000)}"
    ph.markdown(f"""<div id="{tid}" class="orion-toast"><span>{icon} {msg}</span><button class="orion-toast-close" onclick="document.getElementById('{tid}').remove()">×</button></div><script>setTimeout(()=>{{const el=document.getElementById('{tid}');if(el)el.remove()}},5000);</script>""", unsafe_allow_html=True)

def butuh_link_produk(text):
    t = text.lower()
    kata_produk = ["rusak","copot","hilang","patah","pecah","habis","beli","ganti","butuh","cari","rekomendasi","yang bagus"]
    kata_tutorial = ["cara","gimana","bagaimana","tutorial","langkah","memasak","memasang","memakai","mencopot","menggunakan"]
    return any(k in t for k in kata_produk) and not any(k in t for k in kata_tutorial)

def extract_keyword_produk(text):
    stop = ["saya","aku","gue","punya","ini","itu","yang","kok","sih","dong","ya"]
    words = re.findall(r'\b\w+\b', text.lower())
    return " ".join([w for w in words if w not in stop and len(w) > 2][:3])

def deteksi_tingkat(t):
    t = t.lower()
    if any(k in t for k in ["solusi","pecahkan","selesaikan","masalah","problem","gimana caranya","bantu atasi","jalan keluar","saran","bingung","pusing","rusak","copot","hilang"]): return "problem_solver"
    if any(k in t for k in ["s3","disertasi","rbv","dynamic capabilities","transformer","freire","dekonstruksi","backpropagation","doktoral"]): return "kuliah"
    if any(k in t for k in ["ubah jadi","jadiin","remix","ganti style","versi","ganti jadi"]) and st.session_state.last_generated_prompt: return "remix"
    if any(k in t for k in ["gambar","bikin","lukis","draw","buatin","generate"]): return "image"
    if any(k in t for k in ["sd","kelas 1","kelas 2","kelas 3","kelas 4","kelas 5","kelas 6","penjumlahan","perkalian","untuk anak"]): return "sd"
    if any(k in t for k in ["smp","kelas 7","kelas 8","kelas 9","aljabar","persamaan"]): return "smp"
    if any(k in t for k in ["sma","kelas 10","kelas 11","kelas 12","utbk","snbt","limit","turunan","integral"]): return "sma"
    if any(k in t for k in ["kuliah","kalkulus","aljabar linear","statistik","matkul","universitas"]): return "kuliah"
    return "ngobrol"

def generate_gambar(p):
    show_custom_toast("Maaf jika hasilnya kurang memuaskan 🙏", "🎨"); st.session_state.last_generated_prompt = p
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p[:200])}?width=1024&height=1024&nologo=true&seed={int(time.time())%10000}"
    try: r = requests.get(url, timeout=45); return (Image.open(io.BytesIO(r.content)).convert("RGB"), None) if r.status_code == 200 else (None, "Server sedang penuh")
    except: return None, "Terjadi kesalahan, silakan coba lagi"

def remix_gambar_hasil_generate(pr):
    if not st.session_state.last_generated_prompt: return None, "Buat gambar dulu baru bisa di-remix. Contoh: 'buatkan gambar kucing'"
    show_custom_toast("Maaf jika hasilnya kurang memuaskan 🙏", "✨"); fp = f"{st.session_state.last_generated_prompt}, {pr}"; st.session_state.last_generated_prompt = fp
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(fp[:200])}?width=1024&height=1024&nologo=true&seed={int(time.time())%10000}"
    try: r = requests.get(url, timeout=45); return (Image.open(io.BytesIO(r.content)).convert("RGB"), None) if r.status_code == 200 else (None, "Gagal me-remix gambar")
    except: return None, "Terjadi kesalahan saat remix"

def image_to_bytes(img): buf = io.BytesIO(); img.save(buf, format="PNG"); return buf.getvalue()

def kirim_ke_ai(prompt, image=None):
    tingkat = deteksi_tingkat(prompt)
    if tingkat == "image":
        img, err = generate_gambar(prompt); return [("image", img, tingkat)] if img else [("text", f"Gagal membuat gambar: {err}", "ngobrol")]
    if tingkat == "remix":
        img, err = remix_gambar_hasil_generate(prompt); return [("image", img, "remix")] if img else [("text", f"Gagal remix: {err}", "ngobrol")]

    perlu_link = butuh_link_produk(prompt)
    keyword = extract_keyword_produk(prompt) if perlu_link else ""

    tgl = datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%d %B %Y')
    link_instruksi = f"""
PENTING: User butuh barang pengganti. Setelah kasih solusi, tambahkan:
### Rekomendasi Produk
- **Shopee**: https://shopee.co.id/search?keyword={urllib.parse.quote(keyword)}
- **Tokopedia**: https://www.tokopedia.com/search?st=product&q={urllib.parse.quote(keyword)}
Jelaskan kenapa barang ini cocok.
""" if perlu_link else "JANGAN kasih link produk. User hanya butuh tutorial."

    sys_p = f"""Anda adalah Orion. Asisten AI cerdas yang membantu menyelesaikan masalah apa pun. Tanggal: {tgl}.

KEPRIBADIAN: Profesional, empatik, dan solutif. Gunakan bahasa Indonesia yang sopan, jelas, dan mudah dipahami semua kalangan. Gunakan kata "Anda" atau "kamu".

FORMAT PROBLEM SOLVER:
Basa basi-
[Tunjukkan empati dan validasi masalah user. Beri harapan bahwa ada solusi. Tegaskan Orion akan bantu step by step]

Oke jadi begini caranya
1. [Langkah 1 + penjelasan detail + contoh konkret]
2. [Langkah 2 + penjelasan detail + contoh konkret]
3. [Langkah 3 + penjelasan detail + contoh konkret]

Jadi gitu cara mengatasinya
[Rangkum solusi inti. Tekankan manfaat. Motivasi user. Tawarkan bantuan lanjutan. Tutup dengan "Sudah paham kan?"]

{link_instruksi}

ATURAN LAIN:
1. Jangan sebut "AI" atau "model". Anda adalah Orion.
2. Untuk ngajar/ngobrol, jawab natural tanpa batasan baris.
3. Gunakan ### Heading, bullet `-`, **bold** untuk struktur.
4. Jika ada link produk, pastikan format markdown: [Nama Toko](url)"""
    full_p = sys_p + f"\n\nJenis: {tingkat}\nPertanyaan user: {prompt}"
    try:
        res = gemini_model.generate_content([full_p, image] if image else full_p); return [("text", res.text, tingkat)]
    except:
        try:
            chat = groq_client.chat.completions.create(messages=[{"role": "user", "content": full_p}], model="llama-3.3-70b-versatile", max_tokens=2000, temperature=0.3)
            return [("text", chat.choices[0].message.content, tingkat)]
        except: return [("text", "Mohon maaf, terjadi gangguan sistem.\nSilakan coba lagi dalam 1 menit.", "ngobrol")]

if not current_chat['messages']:
    st.markdown(f"""<div class="meta-opening"><div class="meta-title">Ada yang bisa<br>Orion bantu?</div><button class="meta-btn" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'Buat gambar'}}, '*')"><span class="meta-btn-icon">🖼️</span> Buat gambar</button><button class="meta-btn" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'Bantu selesaikan masalah saya'}}, '*')"><span class="meta-btn-icon">💡</span> Bantu selesaikan masalah</button><button class="meta-btn" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'Belajar dan berkembang'}}, '*')"><span class="meta-btn-icon">🎓</span> Belajar dan berkembang</button></div>""", unsafe_allow_html=True)

if MAX_CHAT - current_chat['chat_count'] == 3: st.toast("Sesi ngobrol hampir habis, persiapkan pertanyaan terakhir Anda", icon="⚠️")

for i, msg in enumerate(current_chat['messages']):
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            bc = msg.get("tingkat", "ngobrol"); bt = {"image": "🎨 GAMBAR", "remix": "✨ REMIX", "sd": "📘 SD", "smp": "📗 SMP", "sma": "📙 SMA", "kuliah": "📕 KULIAH", "ngobrol": "💬 NGOBROL", "problem_solver": "💡 SOLUSI"}.get(bc, "💬")
            st.markdown(f'<div class="orion-badge {bc}">{bt}</div>', unsafe_allow_html=True)
        if msg["type"] == "image":
            st.image(msg["content"], use_container_width=True)
            st.download_button("📥 Unduh", image_to_bytes(msg["content"]), f"orion_{i}.png", "image/png", key=f"dl_{i}_{st.session_state.current_chat_id}", use_container_width=True)
        else: st.markdown(msg["content"], unsafe_allow_html=True)

st.markdown('<div id="scroll-anchor"></div>', unsafe_allow_html=True)

if len(current_chat['messages']) > 3:
    col1, col2, col3 = st.columns([10, 1, 1])
    with col3:
        if st.button("↓", key="scroll-btn", help="Scroll ke bawah"):
            st.markdown("<script>window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});</script>", unsafe_allow_html=True)

prompt = st.chat_input("Tanya Orion...", accept_file=True, file_type=["jpg","png","jpeg"])

if prompt:
    if current_chat['chat_count'] >= MAX_CHAT: st.error("Sesi ngobrol hari ini sudah habis. Silakan kembali besok 🙏"); st.stop()
    current_chat['chat_count'] += 1
    user_text = prompt.text if hasattr(prompt, 'text') else (prompt.get("text", "") if isinstance(prompt, dict) else prompt)
    user_file = prompt.files[0] if hasattr(prompt, 'files') and prompt.files else (prompt.get("files", [None])[0] if isinstance(prompt, dict) and prompt.get("files") else None)
    user_img = None
    if len(current_chat['messages']) == 0 and user_text: current_chat['title'] = generate_title(user_text)
    if user_file: user_img = Image.open(user_file).convert("RGB"); current_chat['messages'].append({"role": "user", "type": "image", "content": user_img})
    if user_text: current_chat['messages'].append({"role": "user", "type": "text", "content": user_text})
    hasil = kirim_ke_ai(user_text, user_img)
    for tipe, konten, *rest in hasil:
        tingkat = rest[0] if rest else "ngobrol"
        current_chat['messages'].append({"role": "assistant", "type": tipe, "content": konten, "tingkat": tingkat})
    st.rerun()
