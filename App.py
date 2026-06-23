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
from gtts import gTTS
import speech_recognition as sr

st.set_page_config(page_title="Orion AI", page_icon="logo.png", layout="wide", initial_sidebar_state="collapsed")

try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("API Key belum diisi. Masuk Manage app → Settings → Secrets")
    st.stop()

if "messages" not in st.session_state: st.session_state.messages = []
if "chat_count" not in st.session_state: st.session_state.chat_count = 0
if "last_generated_prompt" not in st.session_state: st.session_state.last_generated_prompt = None
if "voice_text" not in st.session_state: st.session_state.voice_text = ""

MAX_CHAT = 25
jakarta_tz = pytz.timezone('Asia/Jakarta')
IS_DARK = not (6 <= datetime.now(jakarta_tz).hour < 18)
T = {"bg":"#0A0A0B" if IS_DARK else "#FFFFFF","chat_bg":"#18181B" if IS_DARK else "#F4F4F5","user_bg":"#27272A" if IS_DARK else "#E4E4E7","text":"#E4E4E7" if IS_DARK else "#18181B","border":"#27272A" if IS_DARK else "#E4E4E7","badge_bg":"#18181B" if IS_DARK else "#F4F4F5","badge_text":"#A1A1AA" if IS_DARK else "#71717A","primary":"#A78BFA"}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif}}#MainMenu,footer,header{{visibility:hidden}}
.stApp,.main{{background-color:{T['bg']}}}.block-container{{padding-top:1rem!important;padding-bottom:140px!important;max-width:48rem!important}}
.orion-logo{{position:fixed;top:16px;right:16px;z-index:999;width:32px;height:32px}}.orion-logo img{{border-radius:8px}}
.stButton>button[data-testid="scroll-btn"]{{position:fixed!important;bottom:88px!important;right:20px!important;width:36px!important;height:36px!important;background:{T['chat_bg']}!important;border:1px solid {T['border']}!important;border-radius:50%!important;z-index:998!important;cursor:pointer!important;display:flex!important;align-items:center!important;justify-content:center!important;box-shadow:0 2px 8px rgba(0,0,0,.25)!important;padding:0!important;min-height:36px!important}}
.stButton>button[data-testid="scroll-btn"]:hover{{background:{T['user_bg']}!important}}.stButton>button[data-testid="scroll-btn"] p{{font-size:18px!important;margin:0!important;color:{T['text']}!important}}
.meta-opening{{margin-top:28vh;margin-bottom:2rem}}.meta-title{{font-size:2.25rem;font-weight:700;color:{T['text']};margin-bottom:2.5rem;line-height:1.1;letter-spacing:-0.02em}}
.meta-btn{{display:flex;width:100%;text-align:left;padding:16px 20px;margin-bottom:14px;background-color:{T['chat_bg']};border:1px solid {T['border']};border-radius:28px;color:{T['text']};font-size:1rem;cursor:pointer;transition:all.2s;align-items:center}}
.meta-btn:hover{{border-color:{T['primary']};background-color:{T['user_bg']}}}.meta-btn-icon{{margin-right:14px;font-size:1.2rem}}
.stChatMessage{{padding:0.5rem 0!important}}
[data-testid="stChatMessageAvatar"]{{background-color:#EF4444!important}}
.stChatMessage[data-testid*="assistant"] [data-testid="stChatMessageAvatar"]{{background-color:#F97316!important}}
[data-testid="stChatMessageContent"]{{background-color:{T['chat_bg']}!important;border-radius:20px!important;padding:16px 20px!important;color:{T['text']}!important;border:1px solid {T['border']};line-height:1.7;font-size:0.95rem;margin-left:8px!important}}
.stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"]{{background-color:{T['user_bg']}!important}}
.stChatInput{{position:fixed!important;bottom:0!important;left:50%!important;transform:translateX(-50%)!important;width:100%!important;max-width:48rem!important;padding:0 1rem 1rem 1rem!important;background:{T['bg']}!important;z-index:997!important}}
.stChatInput>div{{background-color:{T['bg']}!important;border:1.5px solid {T['primary']}!important;border-radius:28px!important;padding:2px!important}}
.orion-badge{{display:inline-block;font-size:.7rem;padding:4px 10px;border-radius:12px;margin-bottom:10px;font-weight:600;background-color:{T['badge_bg']};color:{T['badge_text']};border:1px solid {T['border']}}}
[data-testid="stChatMessageContent"] h3{{font-size:1.05rem!important;font-weight:600!important;margin:16px 0 8px 0!important;color:{T['text']}!important}}
[data-testid="stChatMessageContent"] ul{{margin:8px 0!important;padding-left:20px!important}}[data-testid="stChatMessageContent"] li{{margin-bottom:6px!important}}
[data-testid="stChatMessageContent"] strong{{color:#A78BFA!important;font-weight:600!important}}
[data-testid="stChatMessageContent"] a{{color:{T['primary']}!important;text-decoration:none!important;font-weight:500!important;border-bottom:1px solid {T['primary']}!important}}
.orion-toast{{position:fixed;top:70px;right:20px;z-index:9999;background:{T['chat_bg']};color:{T['text']};padding:12px 16px;border-radius:12px;border:1px solid {T['border']};box-shadow:0 4px 12px rgba(0,0,0,.15);display:flex;align-items:center;gap:12px;max-width:320px;animation:slideIn.3s ease}}
.orion-toast-close{{background:none;border:none;color:{T['badge_text']};font-size:18px;cursor:pointer;padding:0 4px}}
.tts-btn{{background:{T['badge_bg']};border:1px solid {T['border']};border-radius:8px;padding:6px 12px;margin-top:8px;cursor:pointer;font-size:0.85rem;color:{T['badge_text']};display:inline-flex;align-items:center;gap:6px}}
.tts-btn:hover{{background:{T['user_bg']};color:{T['text']}}}
.voice-btn{{position:fixed!important;bottom:88px!important;left:20px!important;width:36px!important;height:36px!important;background:{T['chat_bg']}!important;border:1px solid {T['border']}!important;border-radius:50%!important;z-index:998!important;cursor:pointer!important;display:flex!important;align-items:center!important;justify-content:center!important;box-shadow:0 2px 8px rgba(0,0,0,.25)!important}}
.voice-btn:hover{{background:{T['user_bg']}!important}}
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

def show_custom_toast(msg, icon="🎤"):
    ph = st.empty(); tid = f"toast_{int(time.time()*1000)}"
    ph.markdown(f"""<div id="{tid}" class="orion-toast"><span>{icon} {msg}</span><button class="orion-toast-close" onclick="document.getElementById('{tid}').remove()">×</button></div><script>setTimeout(()=>{{const el=document.getElementById('{tid}');if(el)el.remove()}},5000);</script>""", unsafe_allow_html=True)

def voice_to_text():
    try:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            show_custom_toast("Mendengarkan... Ngomong sekarang", "🎤")
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
        show_custom_toast("Memproses suara...", "⏳")
        text = r.recognize_google(audio, language='id-ID')
        return text
    except sr.WaitTimeoutError:
        show_custom_toast("Gak ada suara terdeteksi", "⚠️"); return ""
    except sr.UnknownValueError:
        show_custom_toast("Gak paham yang diomongin, coba lagi", "⚠️"); return ""
    except Exception as e:
        show_custom_toast(f"Mic error: Browser mungkin gak support", "❌"); return ""

def text_to_speech(text):
    try:
        text_clean = re.sub(r'[#*`\-]', '', text)[:500]
        tts = gTTS(text=text_clean, lang='id', slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception as e:
        show_custom_toast("TTS gagal dibuat", "❌"); return None

def butuh_link_produk(text):
    t = text.lower()
    kata_produk = ["rusak","copot","hilang","patah","pecah","habis","beli","ganti","butuh","cari","rekomendasi","yang bagus","sparepart","suku cadang","minta link","dimana beli"]
    kata_tutorial = ["cara","gimana","bagaimana","tutorial","langkah","memasak","memasang","memakai","mencopot","menggunakan","pasang"]
    return any(k in t for k in kata_produk) and not any(k in t for k in kata_tutorial)

def extract_keyword_produk(text):
    stop = ["saya","aku","gue","punya","ini","itu","yang","kok","sih","dong","ya","mulu","terus","sering","kenapa"]
    text = re.sub(r'[^\w\s]', '', text.lower())
    words = [w for w in text.split() if w not in stop and len(w) > 2]
    return " ".join(words[:4])

def deteksi_tingkat(t):
    t = t.lower()
    if any(k in t for k in ["solusi","pecahkan","selesaikan","masalah","problem","gimana caranya","bantu atasi","jalan keluar","saran","bingung","pusing","rusak","copot","hilang","patah"]): return "problem_solver"
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
ATURAN PRODUK: User butuh barang pengganti. Setelah solusi, WAJIB tambahkan:
### Rekomendasi Produk
Berikut link untuk mencari "{keyword}":
- **Shopee**: [Cari di Shopee](https://shopee.co.id/search?keyword={urllib.parse.quote(keyword)})
- **Tokopedia**: [Cari di Tokopedia](https://www.tokopedia.com/search?st=product&q={urllib.parse.quote(keyword)})
Jelaskan spesifikasi yang cocok untuk masalah user.
""" if perlu_link else "ATURAN PRODUK: User hanya butuh tutorial. JANGAN berikan link produk."

    sys_p = f"""Anda adalah Orion, asisten AI yang sangat cerdas, teliti, dan akurat. Tanggal: {tgl}.

PRINSIP UTAMA:
1. AKURASI: Jawaban harus 100% benar secara faktual.
2. KEJELASAN: Gunakan bahasa Indonesia yang baku, mudah dipahami. Hindari typo.
3. SOLUTIF: Berikan langkah konkret yang bisa langsung dipraktikkan.
4. EMPATI: Tunjukkan pemahaman terhadap masalah user.

FORMAT PROBLEM SOLVER:
Basa basi-
[Tunjukkan empati + validasi masalah + beri harapan + komitmen membantu]

Oke jadi begini caranya
1. [Langkah 1: Diagnosis + solusi + contoh konkret]
2. [Langkah 2: Solusi lanjutan + contoh konkret]
3. [Langkah 3: Pencegahan + contoh konkret]

Jadi gitu cara mengatasinya
[Rangkum inti solusi. Tekankan manfaat. Motivasi. Tawarkan bantuan. Tutup dengan "Sudah paham kan?"]

{link_instruksi}

ATURAN TEKNIS:
1. Jangan sebut "AI" atau "model". Anda adalah Orion.
2. Gunakan ### untuk heading, `-` untuk bullet, **bold** untuk penekanan.
3. Untuk link produk, format WAJIB: [Nama Toko](url_lengkap)
4. Jawab langsung ke inti, jangan bertele-tele."""
    full_p = sys_p + f"\n\nJenis: {tingkat}\nPertanyaan user: {prompt}"
    try:
        res = gemini_model.generate_content([full_p, image] if image else full_p); return [("text", res.text, tingkat)]
    except:
        try:
            chat = groq_client.chat.completions.create(messages=[{"role": "user", "content": full_p}], model="llama-3.3-70b-versatile", max_tokens=2000, temperature=0.3)
            return [("text", chat.choices[0].message.content, tingkat)]
        except: return [("text", "Mohon maaf, terjadi gangguan sistem. Silakan coba lagi.", "ngobrol")]

if not st.session_state.messages:
    st.markdown(f"""<div class="meta-opening"><div class="meta-title">Ada yang bisa<br>Orion bantu?</div><button class="meta-btn" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'Buat gambar'}}, '*')"><span class="meta-btn-icon">🖼️</span> Buat gambar</button><button class="meta-btn" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'Bantu selesaikan masalah saya'}}, '*')"><span class="meta-btn-icon">💡</span> Bantu selesaikan masalah</button><button class="meta-btn" onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'Belajar dan berkembang'}}, '*')"><span class="meta-btn-icon">🎓</span> Belajar dan berkembang</button></div>""", unsafe_allow_html=True)

if MAX_CHAT - st.session_state.chat_count == 3: st.toast("Sesi ngobrol hampir habis, persiapkan pertanyaan terakhir Anda", icon="⚠️")

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            bc = msg.get("tingkat", "ngobrol"); bt = {"image": "🎨 GAMBAR", "remix": "✨ REMIX", "sd": "📘 SD", "smp": "📗 SMP", "sma": "📙 SMA", "kuliah": "📕 KULIAH", "ngobrol": "💬 NGOBROL", "problem_solver": "💡 SOLUSI"}.get(bc, "💬")
            st.markdown(f'<div class="orion-badge {bc}">{bt}</div>', unsafe_allow_html=True)
        if msg["type"] == "image":
            st.image(msg["content"], use_container_width=True)
            st.download_button("📥 Unduh", image_to_bytes(msg["content"]), f"orion_{i}.png", "image/png", key=f"dl_{i}", use_container_width=True)
        else: 
            st.markdown(msg["content"], unsafe_allow_html=True)
            if msg["role"] == "assistant" and msg["type"] == "text":
                if st.button("🔊 Dengarkan", key=f"tts_{i}", help="Bacakan jawaban"):
                    audio_fp = text_to_speech(msg["content"])
                    if audio_fp: st.audio(audio_fp, format='audio/mp3')

col1, col2, col3 = st.columns([1, 8, 1])
with col1:
    if st.button("🎤", key="voice-btn", help="Ngomong aja"):
        st.session_state.voice_text = voice_to_text(); st.rerun()
with col3:
    if len(st.session_state.messages) > 3:
        if st.button("↓", key="scroll-btn", help="Scroll ke bawah"):
            st.markdown("<script>window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});</script>", unsafe_allow_html=True)

prompt_val = st.session_state.voice_text if st.session_state.voice_text else None
st.session_state.voice_text = ""

prompt = st.chat_input("Tanya Orion...", accept_file=True, file_type=["jpg","png","jpeg"], key="chat_input")

if prompt_val: prompt = type('obj', (object,), {'text': prompt_val, 'files': []})()

if prompt:
    if st.session_state.chat_count >= MAX_CHAT: st.error("Sesi ngobrol hari ini sudah habis. Silakan kembali besok 🙏"); st.stop()
    st.session_state.chat_count += 1
    user_text = prompt.text if hasattr(prompt, 'text') else (prompt.get("text", "") if isinstance(prompt, dict) else prompt)
    user_file = prompt.files[0] if hasattr(prompt, 'files') and prompt.files else (prompt.get("files", [None])[0] if isinstance(prompt, dict) and prompt.get("files") else None)
    user_img = None
    if user_file: user_img = Image.open(user_file).convert("RGB"); st.session_state.messages.append({"role": "user", "type": "image", "content": user_img})
    if user_text: st.session_state.messages.append({"role": "user", "type": "text", "content": user_text})
    hasil = kirim_ke_ai(user_text, user_img)
    for tipe, konten, *rest in hasil:
        tingkat = rest[0] if rest else "ngobrol"
        st.session_state.messages.append({"role": "assistant", "type": tipe, "content": konten, "tingkat": tingkat})
    st.rerun()
