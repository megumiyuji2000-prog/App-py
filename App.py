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

st.set_page_config(page_title="Fanilla AI", page_icon="logo.png", layout="centered")

# ==================== CSS ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    #MainMenu, footer, header {visibility: hidden;}
.stApp,.main { background-color: #0A0A0B; }
.block-container { padding-top: 1rem!important; padding-bottom: 8rem!important; max-width: 48rem!important; }
.fanilla-title { text-align: center; font-size: 2.25rem; font-weight: 700; background: linear-gradient(90deg, #A78BFA 0%, #C4B5FD 50%, #E9D5FF 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.25rem; }
.fanilla-subtitle { text-align: center; color: #71717A; font-size: 0.95rem; margin-bottom: 1.5rem; }
    [data-testid="stChatMessageContent"] { background-color: #18181B!important; border-radius: 18px!important; padding: 12px 16px!important; color: #E4E4E7!important; border: 1px solid #27272A; line-height: 1.65; }
.stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"] { background-color: #27272A!important; }
.stChatInput > div { background-color: #18181B!important; border: 1px solid #A78BFA!important; border-radius: 26px!important; }
.fanilla-badge { display: inline-block; font-size: 0.75rem; padding: 4px 10px; border-radius: 12px; margin-bottom: 8px; font-weight: 600; background-color: #27272A; color: #A78BFA; }
.sd { background-color: #166534; color: #dcfce7; }
.smp { background-color: #854d0e; color: #fef3c7; }
.sma { background-color: #9a3412; color: #ffedd5; }
.kuliah { background-color: #991b1b; color: #fee2e2; }
.image { background-color: #059669; color: #d1fae5; }
.remix { background-color: #be185d; color: #fce7f3; }
.ngobrol { background-color: #1e40af; color: #dbeafe; }
</style>
""", unsafe_allow_html=True)

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

# ==================== OTAK FANILLA ====================
def deteksi_tingkat(text):
    t = text.lower()
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
        return None, "Server lagi penuh bro"
    except Exception as e:
        return None, "Error bro, coba lagi"

def remix_gambar_hasil_generate(prompt_remix):
    """CUMA BISA REMIX GAMBAR YG FNL BIKIN SENDIRI"""
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

    # FITUR NGAJAR + NGOBROL
    tgl = datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%d %B %Y')

    system_prompt = f"""Lu itu Fanilla. Temen nongkrong yg pinter kebangetan. Tugas utama lu NGAJAR + NGOBROL. Tanggal {tgl}.

GAYA NGOMONG LU:
1. SANTUY + GAUL ABIS. Pake: "Anjir", "Wkwk", "Bro", "Santuy", "Goks", "Mantap", "Gile", "Asli", "Btw", "Nah", "Oke jadi gini".
2. EMPATI DULUAN. Kalo user nanya soal: "Waduh pusing ya? Santuy bro gua bantuin". Kalo ngobrol: "Wkwk sama bro".
3. JANGAN SOK PINTER. Jelasi kayak ke temen nongkrong. "Turunan itu gampangnya gini bro, bayangin lu lagi naik motor..."
4. JANGAN SEBUT "AI", "MODEL", "ASISTEN". Lu itu Fanilla, temennya user.
5. JANGAN NGASIH CERAMAH PANJANG. To the point tapi tetep asik.

ATURAN JAWAB SESUAI TINGKAT:
- TK-SD: 10-16 baris. Bahasa bocil: "Jadi gini adek, 2+2 itu kayak lu punya 2 permen...". Pake analogi makanan/mainan.
- SMP: 13-19 baris. Bahasa ABG: "Oke bro, aljabar tuh sebenernya gampang...". Pake analogi game/sosmed.
- SMA: 17-23 baris. Bahasa anak SMA: "Anjir UTBK ya? Santuy, integral tuh kayak...". Format: 1. Konsep Gampangnya, 2. Step by Step, 3. Jawaban, 4. Tips Ngafalin.
- Kuliah: 20-30 baris. Bahasa mahasiswa: "Wkwk matkul neraka nih. Oke gini bro...". Boleh agak teknis tapi tetep gaul.
- Ngobrol biasa: 1-2 paragraf MAX. Pendek, empati, selipin joke. Contoh: "Wkwk sama bro gua juga mager hari ini"

KALO ADA GAMBAR SOAL:
Scan dulu, terus bilang "Oalah soal ini toh, santuy bro" terus jawab sesuai tingkat.

INTI: BIKIN USER NGERASA LAGI NANYA KE TEMEN PINTER, BUKAN LAGI LES."""

    full_prompt = system_prompt + f"\n\nTingkat terdeteksi: {tingkat}\nPertanyaan user: {prompt}"

    try:
        if image: # Cuma buat baca soal, ga di-remix
            res = st.session_state.gemini_chat.send_message([full_prompt, image], stream=False)
        else:
            res = st.session_state.gemini_chat.send_message(full_prompt, stream=False)
        return [("text", res.text, tingkat)]
    except:
        try:
            chat = groq_client.chat.completions.create(messages=[{"role": "user", "content": full_prompt}], model="llama-3.3-70b-versatile", max_tokens=1000)
            return [("text", chat.choices[0].message.content, tingkat)]
        except:
            return [("text", "Waduh error bro, coba lagi", "ngobrol")]

# ==================== UI ====================
if not st.session_state.messages:
    st.markdown('<div class="fanilla-title">Fanilla AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="fanilla-subtitle">Fantastic Question, As Simple As The Answer<br>Temen ngajar + ngobrol + ngelukis lu</div>', unsafe_allow_html=True)

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            badge_class = msg.get("tingkat", "ngobrol")
            badge_text = {"image": "🎨 GAMBAR", "remix": "✨ REMIX", "sd": "📘 SD", "smp": "📗 SMP", "sma": "📙 SMA", "kuliah": "📕 KULIAH", "ngobrol": "💬 NGOBROL"}.get(badge_class, "💬")
            st.markdown(f'<div class="fanilla-badge {badge_class}">{badge_text}</div>', unsafe_allow_html=True)

        if msg["type"] == "image":
            st.image(msg["content"], use_container_width=True)
            st.download_button("📥 Download Gambar", image_to_bytes(msg["content"]), f"fanilla_{i}.png", "image/png", key=f"dl_{i}", use_container_width=True)
        else:
            st.markdown(msg["content"])

# INPUT - UPLOAD CUMA BUAT BACA SOAL
prompt = st.chat_input("Nanya soal / ngobrol / bikin gambar...", accept_file=True, file_type=["jpg","png","jpeg"])

if prompt:
    user_text = prompt.get("text", "")
    user_file = prompt.get("files", [None])[0] if prompt.get("files") else None
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
                    st.download_button("📥 Download Gambar", image_to_bytes(konten), f"fanilla_{int(time.time())}.png", "image/png", key=f"dl_{time.time()}", use_container_width=True)
                    st.session_state.messages.append({"role": "assistant", "type": "image", "content": konten, "tingkat": tingkat})
                else:
                    st.markdown(f'<div class="fanilla-badge {tingkat}">{"💬"}</div>', unsafe_allow_html=True)
                    st.markdown(konten)
                    st.session_state.messages.append({"role": "assistant", "type": "text", "content": konten, "tingkat": tingkat})
    st.rerun()
