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

try:
    from gtts import gTTS
    TTS = True
except:
    TTS = False

st.set_page_config(page_title="Orion AI", page_icon="logo.png", layout="wide", initial_sidebar_state="collapsed")

try:
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("API Key belum diisi")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_count" not in st.session_state:
    st.session_state.chat_count = 0
if "audio_processed_id" not in st.session_state:
    st.session_state.audio_processed_id = None
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "gemini"
if "last_model" not in st.session_state:
    st.session_state.last_model = "gemini"

GEMINI_LIMIT = 35
GROQ_LIMIT = 35
MAX_CHAT = GEMINI_LIMIT + GROQ_LIMIT

jakarta_tz = pytz.timezone('Asia/Jakarta')
IS_DARK = not (6 <= datetime.now(jakarta_tz).hour < 18)

T = {
    "bg": "#0A0A0B" if IS_DARK else "#FFFFFF",
    "chat_bg": "#18181B" if IS_DARK else "#F4F4F5",
    "user_bg": "#27272A" if IS_DARK else "#E4E7",
    "text": "#E4E4E7" if IS_DARK else "#18181B",
    "border": "#3F3F46" if IS_DARK else "#D4D4D8",
    "badge_bg": "#18181B" if IS_DARK else "#F4F4F5",
    "badge_text": "#A1A1AA" if IS_DARK else "#71717A",
    "primary": "#A78BFA",
    "user_bubble": "#3F3F46" if IS_DARK else "#E4E4E7",
    "ai_bubble": "#18181B" if IS_DARK else "#FFFFFF",
    "icon": "#FFFFFF" if IS_DARK else "#000000"
}

BLACKLIST = ["bom", "senjata", "bunuh", "bunuh diri", "teroris", "narkoba", "bokep", "hentai", "porn", "seks", "sex", "bugil", "telanjang", "memek", "jembut", "kontol", "ngentot", "coli", "masturbasi", "ganja", "sabu", "ekstasi", "heroin", "kokain"]

def cek_sensitif(t):
    for k in BLACKLIST:
        if k in t.lower():
            return True, k
    return False, None

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif}}
#MainMenu,footer,header{{visibility:hidden}}
.stApp,.main{{background-color:{T['bg']}!important}}
.block-container{{padding-top:80px!important;padding-bottom:160px!important;max-width:48rem!important}}
.orion-header{{position:fixed!important;top:0!important;left:0!important;right:0!important;height:60px!important;background:{T['bg']}!important;border-bottom:3px solid {T['border']}!important;z-index:9998!important}}
.orion-logo{{position:fixed!important;top:14px!important;right:16px!important;z-index:9999!important;width:32px!important;height:32px!important}}
.orion-logo img{{border-radius:8px!important}}
.chat-counter{{position:fixed!important;top:70px!important;right:16px!important;z-index:9999!important;background:{T['chat_bg']}!important;border:1px solid {T['border']}!important;border-radius:20px!important;padding:6px 14px!important;font-size:0.8rem!important;color:{T['badge_text']}!important;font-weight:600!important}}
.meta-opening{{margin-top:1rem!important;margin-bottom:2rem!important}}
.meta-title{{font-size:2.5rem!important;font-weight:700!important;color:{T['text']}!important;margin-bottom:2.5rem!important;line-height:1.1!important;letter-spacing:-0.02em!important}}
.meta-btn{{display:flex!important;width:100%!important;text-align:left!important;padding:18px 20px!important;margin-bottom:12px!important;background-color:{T['chat_bg']}!important;border:1px solid {T['border']}!important;border-radius:16px!important;color:{T['text']}!important;font-size:1rem!important;cursor:pointer!important;transition:all .2s!important;align-items:center!important}}
.meta-btn:hover{{border-color:{T['primary']}!important;background-color:{T['user_bg']}!important}}
.meta-btn-icon{{margin-right:14px!important;font-size:1.3rem!important}}
.stChatMessage{{padding:0.5rem 0!important;gap:0.75rem!important}}
[data-testid="stChatMessageAvatar"]{{background:linear-gradient(135deg,#F97316,#EF4444)!important;width:32px!important;height:32px!important}}
.stChatMessage[data-testid*="user"] [data-testid="stChatMessageAvatar"]{{background:linear-gradient(135deg,#3B82F6,#6366F1)!important}}
[data-testid="stChatMessageContent"]{{background-color:{T['ai_bubble']}!important;border-radius:18px!important;padding:12px 16px!important;color:{T['text']}!important;border:1px solid {T['border']}!important;line-height:1.6!important;font-size:0.95rem!important;max-width:85%!important}}
.stChatMessage[data-testid*="user"]{{flex-direction:row-reverse!important}}
.stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"]{{background-color:{T['user_bubble']}!important;margin-left:0!important;margin-right:8px!important}}
.stChatInput{{position:fixed!important;bottom:40px!important;left:50%!important;transform:translateX(-50%)!important;width:100%!important;max-width:48rem!important;padding:0 1rem!important;background:transparent!important;z-index:10001!important}}
.stChatInput>div{{background-color:{T['chat_bg']}!important;border:1px solid {T['border']}!important;border-radius:28px!important;padding:4px 8px 4px 80px!important;box-shadow:0 2px 8px rgba(0,0,0,.15)!important;position:relative!important}}
.stChatInput input{{color:{T['text']}!important;background:transparent!important;border:none!important;padding-left:0!important}}
.orion-badge{{display:inline-block!important;font-size:.7rem!important;padding:4px 10px!important;border-radius:12px!important;margin-bottom:10px!important;margin-right:6px!important;font-weight:600!important;background-color:{T['badge_bg']}!important;color:{T['badge_text']}!important;border:1px solid {T['border']}!important}}
.model-badge{{background:#A78BFA!important;color:white!important}}
.footer-fnl{{position:fixed!important;bottom:8px!important;left:50%!important;transform:translateX(-50%)!important;font-size:0.7rem!important;color:{T['badge_text']}!important;z-index:10000!important;opacity:0.6!important}}
[data-testid="stFileUploader"],[data-testid="stAudioInput"]{{display:none!important}}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="orion-header"></div>', unsafe_allow_html=True)

try:
    with open("logo.png", "rb") as f:
        data = base64.b64encode(f.read()).decode()
    st.markdown(f'<div class="orion-logo"><img src="data:image/png;base64,{data}"></div>', unsafe_allow_html=True)
except:
    pass

sisa = MAX_CHAT - st.session_state.chat_count
if sisa <= 3 and sisa > 0:
    st.toast(f"waduh waktu ngobrol sisa {sisa} Kali lagi, nih siap-siap ya", icon="⚠️")

st.markdown(f'<div class="chat-counter">{st.session_state.chat_count}/({MAX_CHAT})</div>', unsafe_allow_html=True)

genai.configure(api_key=GEMINI_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')
groq_client = Groq(api_key=GROQ_KEY)

def toast(msg, icon="🎯"):
    st.toast(msg, icon=icon)

def transcribe_audio(audio_bytes):
    try:
        t = groq_client.audio.transcriptions.create(file=("audio.wav", audio_bytes), model="whisper-large-v3", language="id", response_format="text", temperature=0.0).strip()
        return t if len(t) >= 3 else ""
    except:
        return ""

def text_to_speech(text):
    if not TTS:
        return []
    try:
        text = re.sub(r'[#*`\-_]', '', text)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text).strip()
        chunks = []
        t = text
        while t:
            if len(t) <= 3000:
                chunks.append(t)
                break
            p = t[:3000].rfind('. ')
            if p == -1:
                p = 3000
            chunks.append(t[:p+1])
            t = t[p+1:].strip()
        audios = []
        for c in chunks:
            tts = gTTS(text=c, lang='id', slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            audios.append(fp)
        return audios
    except:
        return []

def butuh_link_produk(text):
    t = text.lower()
    kata_produk = ["rusak", "copot", "hilang", "patah", "pecah", "habis", "beli", "ganti", "butuh", "cari", "rekomendasi", "yang bagus", "sparepart", "suku cadang", "minta link", "dimana beli"]
    kata_tutorial = ["cara", "gimana", "bagaimana", "tutorial", "langkah", "memasak", "memasang", "memakai", "mencopot", "menggunakan", "pasang"]
    return any(k in t for k in kata_produk) and not any(k in t for k in kata_tutorial)

def extract_keyword_produk(text):
    stop = ["saya", "aku", "gue", "punya", "ini", "itu", "yang", "kok", "sih", "dong", "ya", "mulu", "terus", "sering", "kenapa"]
    text = re.sub(r'[^\w\s]', '', text.lower())
    words = [w for w in text.split() if w not in stop and len(w) > 2]
    return " ".join(words[:4])

def deteksi_tingkat(t):
    t = t.lower()
    if any(k in t for k in ["solusi", "pecahkan", "selesaikan", "masalah", "problem", "gimana caranya", "bantu atasi", "jalan keluar", "saran", "bingung", "pusing", "rusak", "copot", "hilang", "patah"]):
        return "problem_solver"
    if any(k in t for k in ["ubah jadi", "jadiin", "remix", "ganti style", "versi", "ganti jadi"]):
        return "remix"
    if any(k in t for k in ["gambar", "bikin", "lukis", "draw", "buatin", "generate"]):
        return "image"
    return "ngobrol"

def generate_gambar(p):
    toast("maaf jika gambar kurang memuaskan🙏", "🎨")
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p[:200])}?width=1024&height=1024&nologo=true&seed={int(time.time())%10000}"
    try:
        r = requests.get(url, timeout=60)
        return (Image.open(io.BytesIO(r.content)).convert("RGB"), None) if r.status_code == 200 else (None, "Server penuh")
    except:
        return None, "Error"

def image_to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def kirim_ke_ai(prompt, image=None):
    start_time = time.time()
    is_sensitif, kata = cek_sensitif(prompt)
    if is_sensitif:
        return [("text", f"Maaf, aku gak bisa bantu soal '{kata}' ya.", "ngobrol")]
    
    tingkat = deteksi_tingkat(prompt)
    if tingkat == "image":
        img, err = generate_gambar(prompt)
        return [("image", img, tingkat)] if img else [("text", f"Gagal: {err}", "ngobrol")]
    
    perlu_link = butuh_link_produk(prompt)
    keyword = extract_keyword_produk(prompt) if perlu_link else ""
    tgl = datetime.now(jakarta_tz).strftime('%d %B %Y')
    
    link_instruksi = f"""Setelah solusi, tambahkan:\n### Rekomendasi Produk\n- Shopee: https://shopee.co.id/search?keyword={urllib.parse.quote(keyword)}\n- Tokopedia: https://tokopedia.com/search?q={urllib.parse.quote(keyword)}""" if perlu_link else ""
    
    sys_p = f"Anda Orion AI. Tanggal {tgl}. Jawab akurat, jelas, solutif. {link_instruksi}"
    full_p = sys_p + f"\n\nPertanyaan: {prompt}"
    
    models = [st.session_state.selected_model, "groq" if st.session_state.selected_model == "gemini" else "gemini"]
    
    for try_model in models:
        try:
            if time.time() - start_time > 55:
                toast("aduh seperti nya sistemnya lagi capek,coba lagi nanti,atau refresh halaman ya☺️🙏", "😅")
                return [("text", "aduh seperti nya sistemnya lagi capek,coba lagi nanti,atau refresh halaman ya☺️🙏", "ngobrol")]
            
            if try_model == "gemini":
                content = [full_p]
                if image:
                    content.append(image)
                res = gemini_model.generate_content(content, stream=True, request_options={"timeout": 55})
                full_text = "".join([c.text for c in res if c.text])
            else:
                chat = groq_client.chat.completions.create(messages=[{"role": "user", "content": full_p}], model="llama-3.3-70b-versatile", stream=True, timeout=55)
                full_text = "".join([c.choices[0].delta.content for c in chat if c.choices[0].delta.content])
            
            if full_text:
                return [("text", full_text, tingkat, try_model)]
        except Exception as e:
            if "timeout" in str(e).lower():
                toast("aduh seperti nya sistemnya lagi capek,coba lagi nanti,atau refresh halaman ya☺️🙏", "😅")
                return [("text", "aduh seperti nya sistemnya lagi capek,coba lagi nanti,atau refresh halaman ya☺️🙏", "ngobrol")]
    
    return [("text", "Error", "ngobrol")]

with st.sidebar:
    st.markdown("### ⚙️ Manage Orion")
    m = st.selectbox("Pilih Model AI", ["Gemini 2.5 Flash", "Llama 3.3 70B Groq"], index=0 if st.session_state.selected_model == "gemini" else 1)
    new_model = "gemini" if m == "Gemini 2.5 Flash" else "groq"
    if new_model != st.session_state.last_model:
        st.session_state.selected_model = new_model
        st.session_state.last_model = new_model
        toast(f"Pindah ke {m}", "🔄")
    if st.button("🗑️ Hapus Semua Chat"):
        st.session_state.messages = []
        st.session_state.chat_count = 0
        st.rerun()

if not st.session_state.messages:
    st.markdown('<div class="meta-opening"><div class="meta-title">Ada yang bisa<br>Orion bantu?</div><button class="meta-btn"><span class="meta-btn-icon">🖼️</span> Buat gambar</button><button class="meta-btn"><span class="meta-btn-icon">💡</span> Bantu selesaikan masalah</button><button class="meta-btn"><span class="meta-btn-icon">🎓</span> Belajar dan berkembang</button></div>', unsafe_allow_html=True)

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            bc = msg.get("tingkat", "ngobrol")
            bt = {"image": "🎨 GAMBAR", "remix": "✨ REMIX", "ngobrol": "💬 NGOBROL", "problem_solver": "💡 SOLUSI"}.get(bc, "💬")
            model = "Gemini" if msg.get("model") == "gemini" else "Groq"
            st.markdown(f'<div class="orion-badge">{bt}</div><div class="orion-badge model-badge">{model}</div>', unsafe_allow_html=True)
        if msg["type"] == "image":
            st.image(msg["content"], use_container_width=True)
        else:
            st.markdown(msg["content"], unsafe_allow_html=True)

upload_file = st.file_uploader("Upload", type=["jpg", "png", "jpeg"], key="upload_hidden", label_visibility="collapsed")
audio_value = st.audio_input("Rekam", key=f"audio_{st.session_state.chat_count}", label_visibility="collapsed")

st.markdown(f"""
<script>
function addButtons(){{
  const inputDiv = document.querySelector('[data-testid="stChatInput"] > div');
  if(!inputDiv) return;
  
  if(!document.getElementById('btn-plus')){{
    const btn = document.createElement('button');
    btn.id = 'btn-plus';
    btn.innerHTML = '+';
    btn.style.cssText = 'position:absolute;left:12px;top:50%;transform:translateY(-50%);width:28px;height:28px;border:none;background:transparent;color:{T["icon"]};font-size:22px;cursor:pointer;z-index:9999;';
    btn.onclick = () => document.querySelector('[data-testid="stFileUploader"] input').click();
    inputDiv.appendChild(btn);
  }}
  
  if(!document.getElementById('btn-mic')){{
    const btn = document.createElement('button');
    btn.id = 'btn-mic';
    btn.innerHTML = '🎤';
    btn.style.cssText = 'position:absolute;left:44px;top:50%;transform:translateY(-50%);width:28px;height:28px;border:none;background:transparent;color:{T["icon"]};font-size:16px;cursor:pointer;z-index:9999;';
    btn.onclick = () => document.querySelector('[data-testid="stAudioInput"] button').click();
    inputDiv.appendChild(btn);
  }}
}}
setTimeout(addButtons, 800);
setInterval(addButtons, 1000);
</script>
""", unsafe_allow_html=True)

if audio_value:
    voice_text = transcribe_audio(audio_value.getvalue())
    if voice_text and st.session_state.chat_count < MAX_CHAT:
        st.session_state.chat_count += 1
        st.session_state.messages.append({"role": "user", "type": "text", "content": voice_text})
        hasil = kirim_ke_ai(voice_text, None)
        for tipe, konten, *rest in hasil:
            tingkat = rest[0] if rest else "ngobrol"
            model = rest[1] if len(rest) > 1 else st.session_state.selected_model
            st.session_state.messages.append({"role": "assistant", "type": tipe, "content": konten, "tingkat": tingkat, "model": model})
        st.rerun()

if upload_file and st.session_state.chat_count < MAX_CHAT:
    st.session_state.chat_count += 1
    user_img = Image.open(upload_file).convert("RGB")
    st.session_state.messages.append({"role": "user", "type": "image", "content": user_img})
    hasil = kirim_ke_ai("", user_img)
    for tipe, konten, *rest in hasil:
        tingkat = rest[0] if rest else "ngobrol"
        model = rest[1] if len(rest) > 1 else st.session_state.selected_model
        st.session_state.messages.append({"role": "assistant", "type": tipe, "content": konten, "tingkat": tingkat, "model": model})
    st.rerun()

prompt = st.chat_input("Tanya Orion...")
if prompt and st.session_state.chat_count < MAX_CHAT:
    st.session_state.chat_count += 1
    st.session_state.messages.append({"role": "user", "type": "text", "content": prompt})
    hasil = kirim_ke_ai(prompt, None)
    for tipe, konten, *rest in hasil:
        tingkat = rest[0] if rest else "ngobrol"
        model = rest[1] if len(rest) > 1 else st.session_state.selected_model
        st.session_state.messages.append({"role": "assistant", "type": tipe, "content": konten, "tingkat": tingkat, "model": model})
    st.rerun()

st.markdown('<div class="footer-fnl">product of F.N.L</div>', unsafe_allow_html=True)
