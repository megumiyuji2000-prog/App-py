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

try:from gtts import gTTS;TTS=True
except:TTS=False
st.set_page_config(page_title="Orion AI",page_icon="logo.png",layout="wide",initial_sidebar_state="collapsed")
try:GEMINI_KEY=st.secrets["GEMINI_API_KEY"];GROQ_KEY=st.secrets["GROQ_API_KEY"]
except:st.error("API Key belum diisi");st.stop()
if"messages"not in st.session_state:st.session_state.messages=[]
if"chat_count"not in st.session_state:st.session_state.chat_count=0
if"audio_processed_id"not in st.session_state:st.session_state.audio_processed_id=None
if"selected_model"not in st.session_state:st.session_state.selected_model="gemini"
if"show_mic"not in st.session_state:st.session_state.show_mic=False
GEMINI_LIMIT=35
GROQ_LIMIT=35
MAX_CHAT=GEMINI_LIMIT+GROQ_LIMIT
jakarta_tz=pytz.timezone('Asia/Jakarta')
IS_DARK=not(6<=datetime.now(jakarta_tz).hour<18)
T={"bg":"#0A0A0B"if IS_DARK else"#FFFFFF","chat_bg":"#18181B"if IS_DARK else"#F4F4F5","user_bg":"#27272A"if IS_DARK else"#E4E4E7","text":"#E4E4E7"if IS_DARK else"#18181B","border":"#3F3F46"if IS_DARK else"#D4D4D8","badge_bg":"#18181B"if IS_DARK else"#F4F4F5","badge_text":"#A1A1AA"if IS_DARK else"#71717A","primary":"#A78BFA","user_bubble":"#3F3F46"if IS_DARK else"#E4E4E7","ai_bubble":"#18181B"if IS_DARK else"#FFFFFF","icon":"#FFFFFF"if IS_DARK else"#000000"}
BLACKLIST=["bom","senjata","bunuh","bunuh diri","teroris","narkoba","bokep","hentai","porn","seks","sex","bugil","telanjang","memek","jembut","kontol","ngentot","coli","masturbasi","ganja","sabu","ekstasi","heroin","kokain"]
def cek_sensitif(t):
 for k in BLACKLIST:
  if k in t.lower():return True,k
 return False,None
st.markdown(f"""<style>@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');html,body,[class*="css"]{{font-family:'Inter',sans-serif}}#MainMenu,footer,header{{visibility:hidden}}.stApp,.main{{background-color:{T['bg']}!important}}.block-container{{padding-top:80px!important;padding-bottom:160px!important;max-width:48rem!important}}.orion-header{{position:fixed!important;top:0!important;left:0!important;right:0!important;height:60px!important;background:{T['bg']}!important;border-bottom:3px solid {T['border']}!important;z-index:9998!important}}.orion-logo{{position:fixed!important;top:14px!important;right:16px!important;z-index:9999!important;width:32px!important;height:32px!important}}.orion-logo img{{border-radius:8px!important}}.chat-counter{{position:fixed!important;top:70px!important;right:16px!important;z-index:9999!important;background:{T['chat_bg']}!important;border:1px solid {T['border']}!important;border-radius:20px!important;padding:6px 14px!important;font-size:0.8rem!important;color:{T['badge_text']}!important;font-weight:600!important}}.meta-opening{{margin-top:1rem!important;margin-bottom:2rem!important}}.meta-title{{font-size:2.5rem!important;font-weight:700!important;color:{T['text']}!important;margin-bottom:2.5rem!important;line-height:1.1!important;letter-spacing:-0.02em!important}}.meta-btn{{display:flex!important;width:100%!important;text-align:left!important;padding:18px 20px!important;margin-bottom:12px!important;background-color:{T['chat_bg']}!important;border:1px solid {T['border']}!important;border-radius:16px!important;color:{T['text']}!important;font-size:1rem!important;cursor:pointer!important;transition:all.2s!important;align-items:center!important}}.meta-btn:hover{{border-color:{T['primary']}!important;background-color:{T['user_bg']}!important}}.meta-btn-icon{{margin-right:14px!important;font-size:1.3rem!important}}.stChatMessage{{padding:0.5rem 0!important;gap:0.75rem!important}}[data-testid="stChatMessageAvatar"]{{background:linear-gradient(135deg,#F97316,#EF4444)!important;width:32px!important;height:32px!important}}.stChatMessage[data-testid*="user"] [data-testid="stChatMessageAvatar"]{{background:linear-gradient(135deg,#3B82F6,#6366F1)!important}}[data-testid="stChatMessageContent"]{{background-color:{T['ai_bubble']}!important;border-radius:18px!important;padding:12px 16px!important;color:{T['text']}!important;border:1px solid {T['border']}!important;line-height:1.6!important;font-size:0.95rem!important;max-width:85%!important}}.stChatMessage[data-testid*="user"]{{flex-direction:row-reverse!important}}.stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"]{{background-color:{T['user_bubble']}!important;margin-left:0!important;margin-right:8px!important}}.stChatInput{{position:fixed!important;bottom:40px!important;left:50%!important;transform:translateX(-50%)!important;width:100%!important;max-width:48rem!important;padding:0 1rem!important;background:transparent!important;z-index:10001!important}}.stChatInput>div{{background-color:{T['chat_bg']}!important;border:1px solid {T['border']}!important;border-radius:28px!important;padding:4px 8px 4px 90px!important;box-shadow:0 2px 8px rgba(0,0,0,.15)!important}}.stChatInput input{{color:{T['text']}!important;background:transparent!important;border:none!important;padding-left:0!important}}.orion-badge{{display:inline-block!important;font-size:.7rem!important;padding:4px 10px!important;border-radius:12px!important;margin-bottom:10px!important;margin-right:6px!important;font-weight:600!important;background-color:{T['badge_bg']}!important;color:{T['badge_text']}!important;border:1px solid {T['border']}!important}}.model-badge{{background:#A78BFA!important;color:white!important}}[data-testid="stChatMessageContent"] h3{{font-size:1.05rem!important;font-weight:600!important;margin:16px 0 8px 0!important;color:{T['text']}!important}}[data-testid="stChatMessageContent"] ul{{margin:8px 0!important;padding-left:20px!important}}[data-testid="stChatMessageContent"] li{{margin-bottom:6px!important}}[data-testid="stChatMessageContent"] strong{{color:#A78BFA!important;font-weight:600!important}}[data-testid="stChatMessageContent"] a{{color:{T['primary']}!important;text-decoration:none!important;font-weight:500!important;border-bottom:1px solid {T['primary']}!important}}.tts-icon{{background:transparent!important;border:none!important;width:28px!important;height:28px!important;margin-top:8px!important;cursor:pointer!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;font-size:1.1rem!important;color:{T['badge_text']}!important;opacity:0.7!important}}.tts-icon:hover{{opacity:1!important}}.footer-fnl{{position:fixed!important;bottom:8px!important;left:50%!important;transform:translateX(-50%)!important;font-size:0.7rem!important;color:{T['badge_text']}!important;z-index:10000!important;opacity:0.6!important}}.custom-input-bar{{position:fixed!important;bottom:40px!important;left:50%!important;transform:translateX(-50%)!important;width:100%!important;max-width:48rem!important;padding:0 1rem!important;z-index:10002!important;display:flex!important;align-items:center!important;gap:8px!important}}[data-testid="stFileUploader"],[data-testid="stAudioInput"]{{display:none!important}}</style>""",unsafe_allow_html=True)
st.markdown('<div class="orion-header"></div>',unsafe_allow_html=True)
try:
 with open("logo.png","rb")as f:data=base64.b64encode(f.read()).decode()
 st.markdown(f'<div class="orion-logo"><img src="data:image/png;base64,{data}"></div>',unsafe_allow_html=True)
except:pass
st.markdown(f'<div class="chat-counter">{st.session_state.chat_count}/({MAX_CHAT})</div>',unsafe_allow_html=True)
genai.configure(api_key=GEMINI_KEY)
gemini_model=genai.GenerativeModel('gemini-2.5-flash')
groq_client=Groq(api_key=GROQ_KEY)
def toast(msg,icon="🎯"):st.toast(msg,icon=icon)
def transcribe_audio(audio_bytes):
 try:
  t=groq_client.audio.transcriptions.create(file=("audio.wav",audio_bytes),model="whisper-large-v3",language="id",response_format="text",temperature=0.0).strip()
  if len(t)<3:return""
  return t
 except:return""
def text_to_speech(text):
 if not TTS:return[]
 try:
  text=re.sub(r'[#*`\-_]','',text);text=re.sub(r'\[([^\]]+)\]\([^\)]+\)',r'\1',text).strip()
  chunks=[];t=text
  while t:
   if len(t)<=3000:chunks.append(t);break
   p=t[:3000].rfind('. ')
   if p==-1:p=3000
   chunks.append(t[:p+1]);t=t[p+1:].strip()
  audios=[]
  for c in chunks:
   tts=gTTS(text=c,lang='id',slow=False);fp=io.BytesIO();tts.write_to_fp(fp);fp.seek(0);audios.append(fp)
  return audios
 except:return[]
def butuh_link_produk(text):
 t=text.lower()
 kata_produk=["rusak","copot","hilang","patah","pecah","habis","beli","ganti","butuh","cari","rekomendasi","yang bagus","sparepart","suku cadang","minta link","dimana beli"]
 kata_tutorial=["cara","gimana","bagaimana","tutorial","langkah","memasak","memasang","memakai","mencopot","menggunakan","pasang"]
 return any(k in t for k in kata_produk)and not any(k in t for k in kata_tutorial)
def extract_keyword_produk(text):
 stop=["saya","aku","gue","punya","ini","itu","yang","kok","sih","dong","ya","mulu","terus","sering","kenapa"]
 text=re.sub(r'[^\w\s]','',text.lower())
 words=[w for w in text.split()if w not in stop and len(w)>2]
 return" ".join(words[:4])
def deteksi_tingkat(t):
 t=t.lower()
 if any(k in t for k in["solusi","pecahkan","selesaikan","masalah","problem","gimana caranya","bantu atasi","jalan keluar","saran","bingung","pusing","rusak","copot","hilang","patah"]):return"problem_solver"
 if any(k in t for k in["ubah jadi","jadiin","remix","ganti style","versi","ganti jadi"])and st.session_state.last_generated_prompt:return"remix"
 if any(k in t for k in["gambar","bikin","lukis","draw","buatin","generate"]):return"image"
 return"ngobrol"
def generate_gambar(p):
 toast("Maaf jika hasilnya kurang memuaskan 🙏","🎨");st.session_state.last_generated_prompt=p
 url=f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p[:200])}?width=1024&height=1024&nologo=true&seed={int(time.time())%10000}"
 try:r=requests.get(url,timeout=45);return(Image.open(io.BytesIO(r.content)).convert("RGB"),None)if r.status_code==200 else(None,"Server penuh")
 except:return None,"Error"
def remix_gambar_hasil_generate(pr):
 if not st.session_state.last_generated_prompt:return None,"Buat gambar dulu baru bisa di-remix"
 toast("Maaf jika hasilnya kurang memuaskan 🙏","✨");fp=f"{st.session_state.last_generated_prompt}, {pr}";st.session_state.last_generated_prompt=fp
 url=f"https://image.pollinations.ai/prompt/{urllib.parse.quote(fp[:200])}?width=1024&height=1024&nologo=true&seed={int(time.time())%10000}"
 try:r=requests.get(url,timeout=45);return(Image.open(io.BytesIO(r.content)).convert("RGB"),None)if r.status_code==200 else(None,"Gagal remix")
 except:return None,"Error remix"
def image_to_bytes(img):buf=io.BytesIO();img.save(buf,format="PNG");return buf.getvalue()
def kirim_ke_ai(prompt,image=None):
 is_sensitif,kata=cek_sensitif(prompt)
 if is_sensitif:return[("text",f"Maaf, aku gak bisa bantu soal '{kata}' ya. Itu termasuk konten sensitif/berbahaya.\n\nKalau kamu lagi ada masalah, coba ngobrol sama orang dewasa yang kamu percaya. Aku bisa bantu topik lain yang positif kok!","ngobrol")]
 tingkat=deteksi_tingkat(prompt)
 if tingkat=="image":
  img,err=generate_gambar(prompt);return[("image",img,tingkat)]if img else[("text",f"Gagal membuat gambar: {err}","ngobrol")]
 if tingkat=="remix":
  img,err=remix_gambar_hasil_generate(prompt);return[("image",img,"remix")]if img else[("text",f"Gagal remix: {err}","ngobrol")]
 perlu_link=butuh_link_produk(prompt)
 keyword=extract_keyword_produk(prompt)if perlu_link else""
 tgl=datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%d %B %Y')
 link_instruksi=f"""ATURAN PRODUK: User butuh barang. Setelah solusi, WAJIB tambahkan:\n### Rekomendasi Produk\nBerikut link untuk mencari "{keyword}":\n- **Shopee**: [Cari di Shopee](https://shopee.co.id/search?keyword={urllib.parse.quote(keyword)})\n- **Tokopedia**: [Cari di Tokopedia](https://www.tokopedia.com/search?st=product&q={urllib.parse.quote(keyword)})"""if perlu_link else"ATURAN PRODUK: User hanya butuh tutorial. JANGAN berikan link produk."
 sys_p=f"""Anda adalah Orion, asisten AI yang sangat cerdas, teliti, dan akurat. Tanggal: {tgl}.\n\nPRINSIP UTAMA:\n1. AKURASI: Jawaban harus 100% benar.\n2. KEJELASAN: Bahasa Indonesia baku, mudah dipahami.\n3. SOLUTIF: Langkah konkret.\n4. EMPATI: Tunjukkan pemahaman.\n5. KEAMANAN: Tolak permintaan berbahaya/ilegal dengan sopan.\n\nFORMAT PROBLEM SOLVER:\nBasa basi-\n[Tunjukkan empati + validasi + harapan]\n\nOke jadi begini caranya\n1. [Langkah 1: Diagnosis + solusi + contoh]\n2. [Langkah 2: Solusi lanjutan + contoh]\n3. [Langkah 3: Pencegahan + contoh]\n\nJadi gitu cara mengatasinya\n[Rangkum inti. Motivasi. Tawarkan bantuan. Tutup "Sudah paham kan?"]\n\n{link_instruksi}\n\nATURAN TEKNIS:\n1. Jangan sebut "AI". Anda adalah Orion.\n2. Gunakan ### untuk heading, `-` untuk bullet, **bold** untuk penekanan.\n3. Untuk link: [Nama Toko](url_lengkap)\n4. Jawab langsung ke inti.\n5. TOLAK konten dewasa/kekerasan/senjata/narkoba/ilegal."""
 full_p=sys_p+f"\n\nJenis: {tingkat}\nPertanyaan user: {prompt}"
 models=[st.session_state.selected_model,"groq"if st.session_state.selected_model=="gemini"else"gemini"]
 for try_model in models:
  try:
   if try_model=="gemini":
    toast("Pake Gemini...","✨")
    content=[full_p]
    if image:content.append(image)
    res=gemini_model.generate_content(content,stream=True)
    full_text="".join([c.text for c in res if c.text])
   else:
    toast("Pake Groq...","⚡")
    chat=groq_client.chat.completions.create(messages=[{"role":"user","content":full_p}],model="llama-3.3-70b-versatile",stream=True)
    full_text="".join([c.choices[0].delta.content for c in chat if c.choices[0].delta.content])
   if full_text:return[("text",full_text,tingkat,try_model)]
  except Exception as e:
   err=str(e)
   if"401"in err:toast("API Key salah/expired","❌")
   elif"429"in err:toast("Limit abis, coba model lain...","⚠️")
   elif"quota"in err.lower():toast("Quota abis","⚠️")
   if try_model==models[-1]:return[("text",f"Error: {err[:80]}. Cek API Key di Secrets.","ngobrol")]
 return[("text","Error gak dikenal bro.","ngobrol")]
with st.sidebar:
 st.markdown("### ⚙️ Manage Orion")
 m=st.selectbox("Pilih Model AI",["Gemini 2.5 Flash","Llama 3.3 70B Groq"],index=0 if st.session_state.selected_model=="gemini"else 1)
 st.session_state.selected_model="gemini"if m=="Gemini 2.5 Flash"else"groq"
 if st.button("🗑️ Hapus Semua Chat"):st.session_state.messages=[];st.session_state.chat_count=0;st.rerun()
 st.metric("Chat Tersisa",f"{MAX_CHAT-st.session_state.chat_count}/({MAX_CHAT})")
if not st.session_state.messages:
 st.markdown('<div class="meta-opening"><div class="meta-title">Ada yang bisa<br>Orion bantu?</div><button class="meta-btn"><span class="meta-btn-icon">🖼️</span> Buat gambar</button><button class="meta-btn"><span class="meta-btn-icon">💡</span> Bantu selesaikan masalah</button><button class="meta-btn"><span class="meta-btn-icon">🎓</span> Belajar dan berkembang</button></div>',unsafe_allow_html=True)
if MAX_CHAT-st.session_state.chat_count==3:st.toast("Sesi ngobrol hampir habis",icon="⚠️")
for i,msg in enumerate(st.session_state.messages):
 with st.chat_message(msg["role"]):
  if msg["role"]=="assistant":
   bc=msg.get("tingkat","ngobrol");bt={"image":"🎨 GAMBAR","remix":"✨ REMIX","ngobrol":"💬 NGOBROL","problem_solver":"💡 SOLUSI"}.get(bc,"💬")
   model="Gemini"if msg.get("model")=="gemini"else"Groq"
   st.markdown(f'<div class="orion-badge {bc}">{bt}</div><div class="orion-badge model-badge">{model}</div>',unsafe_allow_html=True)
  if msg["type"]=="image":
   st.image(msg["content"],use_container_width=True)
   st.download_button("📥 Unduh",image_to_bytes(msg["content"]),f"orion_{i}.png","image/png",key=f"dl_{i}",use_container_width=True)
  else:
   st.markdown(msg["content"],unsafe_allow_html=True)
   if msg["role"]=="assistant"and msg["type"]=="text"and TTS:
    col1,col2=st.columns([1,20])
    with col1:
     if st.button("🔊",key=f"tts_{i}",help="Dengarkan"):
      audio_files=text_to_speech(msg["content"])
      if audio_files:
       for idx,audio_fp in enumerate(audio_files):st.audio(audio_fp,format='audio/mp3')
with st.container():
 col1,col2,col3=st.columns([1,1,12])
 with col1:
  if st.button("+",key="plus_btn",help="Upload gambar"):
   st.session_state.trigger_upload=True
   st.rerun()
 with col2:
  if st.button("🎤",key="mic_btn",help="Rekam suara"):
   st.session_state.trigger_mic=True
   st.rerun()
 st.markdown(f'<style>.stButton[data-testid="baseButton-secondary"]{{position:fixed!important;bottom:44px!important;z-index:10002!important;width:36px!important;height:36px!important;border-radius:50%!important;background:transparent!important;border:none!important;color:{T["icon"]}!important;font-size:1.8rem!important;font-weight:300!important;padding:0!important}}.stButton[data-testid="baseButton-secondary"]:nth-of-type(1){{left:calc(50% - 24rem + 12px)!important}}.stButton[data-testid="baseButton-secondary"]:nth-of-type(2){{left:calc(50% - 24rem + 52px)!important;font-size:1.2rem!important}}.stButton[data-testid="baseButton-secondary"]:hover{{background:{T["user_bg"]}!important}}</style>',unsafe_allow_html=True)
if st.session_state.get("trigger_upload",False):
 upload_file=st.file_uploader("Upload",type=["jpg","png","jpeg"],key="upload_hidden",label_visibility="collapsed")
 st.session_state.trigger_upload=False
 if upload_file:
  if st.session_state.chat_count>=MAX_CHAT:st.error("Sesi ngobrol hari ini sudah habis");st.stop()
  st.session_state.chat_count+=1
  user_img=Image.open(upload_file).convert("RGB")
  st.session_state.messages.append({"role":"user","type":"image","content":user_img})
  hasil=kirim_ke_ai("",user_img)
  for tipe,konten,*rest in hasil:
   tingkat=rest[0]if rest else"ngobrol";model=rest[1]if len(rest)>1 else st.session_state.selected_model
   st.session_state.messages.append({"role":"assistant","type":tipe,"content":konten,"tingkat":tingkat,"model":model})
  st.rerun()
if st.session_state.get("trigger_mic",False):
 audio_value=st.audio_input("Rekam",key=f"audio_recorder_{st.session_state.chat_count}",label_visibility="collapsed")
 st.session_state.trigger_mic=False
 if audio_value:
  current_audio_id=id(audio_value)
  if st.session_state.audio_processed_id!=current_audio_id:
   st.session_state.audio_processed_id=current_audio_id
   voice_text=transcribe_audio(audio_value.getvalue())
   if voice_text:
    if st.session_state.chat_count>=MAX_CHAT:st.error("Sesi ngobrol hari ini sudah habis");st.stop()
    st.session_state.chat_count+=1
    st.session_state.messages.append({"role":"user","type":"text","content":voice_text})
    hasil=kirim_ke_ai(voice_text,None)
    for tipe,konten,*rest in hasil:
     tingkat=rest[0]if rest else"ngobrol";model=rest[1]if len(rest)>1 else st.session_state.selected_model
     st.session_state.messages.append({"role":"assistant","type":tipe,"content":konten,"tingkat":tingkat,"model":model})
    st.rerun()
prompt=st.chat_input("Tanya Orion...")
if prompt:
 if st.session_state.chat_count>=MAX_CHAT:st.error("Sesi ngobrol hari ini sudah habis. Silakan kembali besok 🙏");st.stop()
 st.session_state.chat_count+=1
 user_text=prompt if isinstance(prompt,str)else""
 st.session_state.messages.append({"role":"user","type":"text","content":user_text})
 hasil=kirim_ke_ai(user_text,None)
 for tipe,konten,*rest in hasil:
  tingkat=rest[0]if rest else"ngobrol";model=rest[1]if len(rest)>1 else st.session_state.selected_model
  st.session_state.messages.append({"role":"assistant","type":tipe,"content":konten,"tingkat":tingkat,"model":model})
 st.rerun()
st.markdown('<div class="footer-fnl">product of F.N.L</div>',unsafe_allow_html=True)
