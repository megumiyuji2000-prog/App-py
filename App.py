import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
import requests, io, time, urllib.parse
from datetime import datetime
import pytz

st.set_page_config(page_title="Orion AI", layout="centered")
GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
GROQ_KEY = st.secrets["GROQ_API_KEY"]

if "msgs" not in st.session_state: st.session_state.msgs = []
if "count" not in st.session_state: st.session_state.count = 0
if "model" not in st.session_state: st.session_state.model = "gemini"

MAX = 70
now = datetime.now(pytz.timezone('Asia/Jakarta'))
IS_DARK = now.hour < 6 or now.hour >= 18
ICON_COLOR = "#FFFFFF" if IS_DARK else "#000000"
BG = "#0A0A0B" if IS_DARK else "#FFFFFF"
INPUT_BG = "#1C1C1E" if IS_DARK else "#F2F2F7"
BORDER = "#3A3A3C" if IS_DARK else "#E5E5EA"

# CSS - 2 tombol dalem input
st.markdown(f"""
<style>
.stApp {{background:{BG}}}
.block-container{{padding-bottom:140px;max-width:720px}}
.header{{position:fixed;top:0;left:0;right:0;height:50px;background:{BG};z-index:100;display:flex;align-items:center;justify-content:flex-end;padding:0 20px}}
.counter{{background:{INPUT_BG};padding:5px 12px;border-radius:16px;font-size:13px;color:{'#AAA' if IS_DARK else '#666'}}}
.title{{font-size:34px;font-weight:700;margin:70px 0 30px 0;color:{'#FFF' if IS_DARK else '#000'}}}
.card{{background:{INPUT_BG};border:1px solid {BORDER};border-radius:16px;padding:18px;margin-bottom:12px;font-size:16px;color:{'#FFF' if IS_DARK else '#000'}}}
/* INPUT PILL */
[data-testid="stChatInput"]{{position:fixed!important;bottom:25px!important;left:50%!important;transform:translateX(-50%)!important;width:92%!important;max-width:700px!important;z-index:1000}}
[data-testid="stChatInput"] > div{{background:{INPUT_BG}!important;border:1px solid {BORDER}!important;border-radius:24px!important;padding-left:88px!important;height:52px!important;display:flex!important;align-items:center!important}}
[data-testid="stChatInput"] input{{background:transparent!important;border:none!important;color:{'#FFF' if IS_DARK else '#000'}!important;font-size:16px!important}}
/* SEMBUNYIKAN UPLOADER ASLI */
[data-testid="stFileUploader"], [data-testid="stAudioInput"]{{display:none!important}}
</style>
<div class="header"><div class="counter">{st.session_state.count}/({MAX})</div></div>
""", unsafe_allow_html=True)

# NOTIF
if 0 < MAX - st.session_state.count <= 3:
    st.toast(f"waduh waktu ngobrol sisa {MAX - st.session_state.count} Kali lagi, nih siap-siap ya", icon="⚠️")

# AI
genai.configure(api_key=GEMINI_KEY)
gemini = genai.GenerativeModel('gemini-2.5-flash')
groq = Groq(api_key=GROQ_KEY)

def ask(p):
    if "gambar" in p.lower():
        st.toast("maaf jika gambar kurang memuaskan🙏", icon="🎨")
        try:
            r = requests.get(f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p)}?width=1024&height=1024", timeout=50)
            return Image.open(io.BytesIO(r.content)) if r.status_code==200 else "Gagal"
        except: return "Error"
    try:
        if st.session_state.model == "gemini":
            return gemini.generate_content(p, request_options={"timeout":50}).text
        else:
            return groq.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":p}], timeout=50).choices[0].message.content
    except:
        st.toast("aduh seperti nya sistemnya lagi capek,coba lagi nanti,atau refresh halaman ya☺️🙏", icon="😅")
        return "aduh seperti nya sistemnya lagi capek,coba lagi nanti,atau refresh halaman ya☺️🙏"

# SIDEBAR
with st.sidebar:
    m = st.selectbox("Model", ["Gemini","Groq"], index=0 if st.session_state.model=="gemini" else 1)
    new = "gemini" if m=="Gemini" else "groq"
    if new!= st.session_state.model:
        st.session_state.model = new
        st.toast(f"Pindah ke {m}", icon="🔄")

# OPENING
if not st.session_state.msgs:
    st.markdown('<div class="title">Ada yang bisa<br>Orion bantu?</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">🖼️ Buat gambar</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">💡 Bantu selesaikan masalah</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">🎓 Belajar dan berkembang</div>', unsafe_allow_html=True)

# CHAT
for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        if m["t"]=="img": st.image(m["c"], use_container_width=True)
        else: st.write(m["c"])

# HIDDEN UPLOADERS
up = st.file_uploader("", type=["jpg","png"], key="up", label_visibility="collapsed")
au = st.audio_input("", key=f"au{st.session_state.count}", label_visibility="collapsed")

# INJECT 2 TOMBOL DALEM INPUT
st.markdown(f"""
<script>
function addBtns(){{
  const box = document.querySelector('[data-testid="stChatInput"] > div');
  if(!box || document.getElementById('btn-plus')) return;

  // Tombol +
  const plus = document.createElement('button');
  plus.id = 'btn-plus';
  plus.innerHTML = '+';
  plus.style.cssText = 'position:absolute;left:14px;top:50%;transform:translateY(-50%);width:32px;height:32px;border:none;background:transparent;color:{ICON_COLOR};font-size:26px;font-weight:300;cursor:pointer;z-index:1001;line-height:1';
  plus.onclick = () => document.querySelector('[data-testid="stFileUploader"] input').click();
  box.appendChild(plus);

  // Tombol mic
  const mic = document.createElement('button');
  mic.id = 'btn-mic';
  mic.innerHTML = '🎤';
  mic.style.cssText = 'position:absolute;left:50px;top:50%;transform:translateY(-50%);width:32px;height:32px;border:none;background:transparent;color:{ICON_COLOR};font-size:18px;cursor:pointer;z-index:1001';
  mic.onclick = () => document.querySelector('[data-testid="stAudioInput"] button').click();
  box.appendChild(mic);
}}
setInterval(addBtns, 400);
</script>
""", unsafe_allow_html=True)

# HANDLE
if up and st.session_state.count < MAX:
    st.session_state.count += 1
    img = Image.open(up).convert("RGB")
    st.session_state.msgs.append({"role":"user","t":"img","c":img})
    st.rerun()

if au and st.session_state.count < MAX:
    try:
        txt = groq.audio.transcriptions.create(file=("a.wav", au.getvalue()), model="whisper-large-v3", language="id").text
        if txt:
            st.session_state.count += 1
            st.session_state.msgs.append({"role":"user","t":"text","c":txt})
            ans = ask(txt)
            st.session_state.msgs.append({"role":"assistant","t":"text","c":ans})
            st.rerun()
    except: pass

# INPUT
p = st.chat_input("Tanya Orion...")
if p and st.session_state.count < MAX:
    st.session_state.count += 1
    st.session_state.msgs.append({"role":"user","t":"text","c":p})
    ans = ask(p)
    if isinstance(ans, Image.Image):
        st.session_state.msgs.append({"role":"assistant","t":"img","c":ans})
    else:
        st.session_state.msgs.append({"role":"assistant","t":"text","c":ans})
    st.rerun()
