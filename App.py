import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
from datetime import datetime
import pytz
import time

st.set_page_config(
    page_title="Fanilla AI", 
    page_icon="logo.png",  # ← Yg diganti cuma ini
    layout="centered", 
    initial_sidebar_state="collapsed"
)
# ==================== CSS FANILLA GAUL ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
    #MainMenu, footer, header {visibility: hidden;}
  .stApp,.main { background-color: #0A0A0B; }
  .block-container { padding-top: 2rem!important; padding-bottom: 8rem!important; max-width: 48rem!important; }
  .fanilla-title { text-align: center; font-size: 2.25rem; font-weight: 700; background: linear-gradient(90deg, #A78BFA 0%, #C4B5FD 50%, #E9D5FF 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.25rem; letter-spacing: -0.02em; }
  .fanilla-subtitle { text-align: center; color: #71717A; font-size: 0.95rem; margin-bottom: 3rem; line-height: 1.5; }
  .stChatMessage { background-color: transparent!important; padding: 0.75rem 0!important; margin: 0!important; }
    [data-testid="stChatMessageContent"] { background-color: #18181B!important; border-radius: 18px!important; padding: 12px 16px!important; color: #E4E4E7!important; line-height: 1.65; border: 1px solid #27272A; font-size: 0.95rem; }
  .stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"] { background-color: #27272A!important; border: 1px solid #3F3F46; }
  .stChatInput { position: fixed!important; bottom: 0!important; left: 0!important; right: 0!important; background: linear-gradient(180deg, rgba(10,10,11,0) 0%, #0A0A0B 30%)!important; padding: 1rem 1rem 1.5rem 1rem!important; max-width: 48rem!important; margin: 0 auto!important; backdrop-filter: blur(8px); }
  .stChatInput > div { background-color: #18181B!important; border: 1px solid #A78BFA!important; border-radius: 26px!important; box-shadow: 0 4px 12px rgba(167,139,250,0.2); }
  .stChatInput input { color: #E4E4E7!important; font-size: 0.95rem!important; padding: 14px 18px!important; }
  .stChatInput input::placeholder { color: #71717A!important; }
  .stImage img { border-radius: 14px!important; border: 1px solid #27272A; margin: 8px 0; }
  .stToast { background-color: #18181B!important; border: 1px solid #A78BFA!important; border-radius: 12px!important; }
  .fanilla-badge { display: inline-block; font-size: 0.75rem; padding: 4px 10px; border-radius: 12px; margin-bottom: 8px; font-weight: 600; background-color: #27272A; color: #A78BFA; }
  .model-badge { display: inline-block; font-size: 0.65rem; padding: 2px 6px; border-radius: 8px; margin-left: 6px; font-weight: 500; opacity: 0.7; }
  .gemini { background-color: #1e40af; color: #dbeafe; }
  .llama { background-color: #7c2d12; color: #ffedd5; }
</style>
""", unsafe_allow_html=True)

# ==================== INIT MULTI-MODEL ====================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("Waduh bro, API Key belum diset. Butuh GEMINI_API_KEY dan GROQ_API_KEY di Secrets.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "gemini_chat" not in st.session_state:
    st.session_state.gemini_chat = gemini_model.start_chat(history=[])
if "groq_history" not in st.session_state:
    st.session_state.groq_history = []

# ==================== OTAK FANILLA GAUL MAX ====================
def deteksi_tingkat(text):
    t = text.lower()
    if any(k in t for k in ["sd","kelas 1","kelas 2","kelas 3","kelas 4","kelas 5","kelas 6","penjumlahan","perkalian"]): return "sd"
    if any(k in t for k in ["smp","kelas 7","kelas 8","kelas 9","aljabar","persamaan"]): return "smp"
    if any(k in t for k in ["sma","kelas 10","kelas 11","kelas 12","utbk","snbt","limit","turunan","integral"]): return "sma"
    if any(k in t for k in ["kuliah","kalkulus","aljabar linear","statistik","matkul","universitas"]): return "kuliah"
    return "ngobrol"

def kirim_ke_ai(prompt, image=None):
    tingkat = deteksi_tingkat(prompt)
    tgl = datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%d %B %Y')

    # ========== PROMPT GAUL MAX - ANAK NONGKRONG ==========
    system_prompt = f"""Lu itu Fanilla. Temen nongkrong yg pinter kebangetan. Bukan dosen, bukan AI. Tanggal {tgl}.

GAYA NGOMONG LU:
1. SANTUY + GAUL ABIS. Pake: "Anjir", "Wkwk", "Bro", "Santuy", "Goks", "Mantap", "Gile", "Asli", "Btw", "Nah", "Oke jadi gini".
2. EMPATI DULUAN. Kalo user nanya soal: "Waduh pusing ya? Santuy bro gua bantuin". Kalo ngobrol: "Wkwk sama bro".
3. JANGAN SOK PINTER. Jelasi kayak ke temen nongkrong. Misal "Turunan itu gampangnya gini bro, bayangin lu lagi naik motor, nah kecepatannya tuh..."
4. JANGAN SEBUT "AI", "MODEL", "ASISTEN". Lu itu Fanilla, temennya user.
5. JANGAN NGASIH CERAMAH PANJANG. To the point tapi tetep asik.

ATURAN JAWAB:
- TK-SD: 10-16 baris. Bahasa bocil: "Jadi gini adek, 2+2 itu kayak lu punya 2 permen...". Pake analogi makanan/mainan.
- SMP: 13-19 baris. Bahasa ABG: "Oke bro, aljabar tuh sebenernya gampang...". Pake analogi game/sosmed.
- SMA: 17-23 baris. Bahasa anak SMA: "Anjir UTBK ya? Santuy, integral tuh kayak...". Format: 1. Konsep Gampangnya, 2. Step by Step, 3. Jawaban, 4. Tips Ngafalin.
- Kuliah: 20-30 baris. Bahasa mahasiswa: "Wkwk matkul neraka nih. Oke gini bro...". Boleh agak teknis tapi tetep gaul.
- Ngobrol biasa: 1-2 paragraf MAX. Pendek, empati, selipin joke dikit. Contoh: "Wkwk sama bro gua juga mager hari ini. Btw udah makan belum?"

KALO ADA GAMBAR SOAL:
Scan dulu, terus bilang "Oalah soal ini toh, santuy bro" terus jawab sesuai tingkat.

INTI: BIKIN USER NGERASA LAGI NANYA KE TEMEN PINTER, BUKAN LAGI LES."""

    full_prompt = system_prompt + f"\n\nTingkat terdeteksi: {tingkat}\nPertanyaan user: {prompt}"

    # ========== COBA GEMINI DULU ==========
    try:
        time.sleep(2)
        st.toast("Fanilla lagi mikir...", icon="🎓")
        if image:
            res = st.session_state.gemini_chat.send_message([full_prompt, image], stream=True)
        else:
            res = st.session_state.gemini_chat.send_message(full_prompt, stream=True)

        for chunk in res:
            if chunk.text:
                yield chunk.text, tingkat, "gemini"
        return

    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            # ========== FALLBACK LLAMA 3.3 ==========
            if image:
                yield "Anjir bro, Gemini gua lagi limit trus Llama ga bisa liat gambar 😭 Coba kirim soalnya diketik aja, atau tunggu besok jam 7 pagi ya. Maapkeun 🙏", tingkat, "error"
                return

            st.toast("Gemini capek, ganti Llama dulu...", icon="⚡")
            try:
                time.sleep(2)
                st.session_state.groq_history.append({"role": "user", "content": full_prompt})

                chat = groq_client.chat.completions.create(
                    messages=st.session_state.groq_history,
                    model="llama-3.3-70b-versatile",
                    temperature=0.8,
                    max_tokens=2048,
                    stream=True
                )

                full_response = ""
                for chunk in chat:
                    if chunk.choices[0].delta.content:
                        text = chunk.choices[0].delta.content
                        full_response += text
                        yield text, tingkat, "llama"

                st.session_state.groq_history.append({"role": "assistant", "content": full_response})
                return

            except Exception as e2:
                yield f"Waduh bro, Llama juga tumbang 😭 Server lagi rame. Coba lagi 5 menit ya.", tingkat, "error"
                return
        else:
            yield f"Error anjir: {str(e)[:100]}. Coba refresh deh bro.", tingkat, "error"
            return

# ==================== UI ====================
if len(st.session_state.messages) == 0:
    st.markdown('<div class="fanilla-title">Fanilla AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="fanilla-subtitle">Fantastic Question, As Simple As The Answer<br>Ngobrol santai bisa, nanya soal juga bisa 😎</div>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("tingkat") and msg["role"] == "assistant":
            badge_map = {"sd": "📘 SD", "smp": "📗 SMP", "sma": "📙 SMA", "kuliah": "📕 Kuliah", "ngobrol": "💬 Ngobrol"}
            label = badge_map.get(msg["tingkat"], "💬 Ngobrol")
            model_badge = f"<span class='model-badge {msg.get('model','gemini')}'>{msg.get('model','gemini').upper()}</span>"
            st.markdown(f'<div class="fanilla-badge">{label}{model_badge}</div>', unsafe_allow_html=True)

        if msg["type"] == "image":
            st.image(msg["content"], caption=msg.get("caption"))
        else:
            st.markdown(msg["content"])

prompt = st.chat_input("Nanya apa bro...", accept_file=True, file_type=["jpg", "jpeg", "png"])

if prompt:
    tingkat_aktif = "ngobrol"
    model_aktif = "gemini"

    if prompt.get("files"):
        img = Image.open(prompt["files"][0])
        txt = prompt.get("text", "Bro jelasin soal di foto ini dong")
        st.session_state.messages.append({"role": "user", "content": img, "type": "image", "caption": txt})
        with st.chat_message("user"):
            st.image(img, caption=txt)
        with st.chat_message("assistant"):
            ph = st.empty()
            out = ""
            for c, t, m in kirim_ke_ai(txt, image=img):
                out += c
                tingkat_aktif = t
                model_aktif = m
                ph.markdown(out + "▌")
            ph.markdown(out)
            st.session_state.messages.append({"role": "assistant", "content": out, "type": "text", "tingkat": tingkat_aktif, "model": model_aktif})

    elif prompt.get("text"):
        txt = prompt["text"]
        st.session_state.messages.append({"role": "user", "content": txt, "type": "text"})
        with st.chat_message("user"):
            st.markdown(txt)
        with st.chat_message("assistant"):
            ph = st.empty()
            out = ""
            for c, t, m in kirim_ke_ai(txt):
                out += c
                tingkat_aktif = t
                model_aktif = m
                ph.markdown(out + "▌")
            ph.markdown(out)
            st.session_state.messages.append({"role": "assistant", "content": out, "type": "text", "tingkat": tingkat_aktif, "model": model_aktif})
    st.rerun()
