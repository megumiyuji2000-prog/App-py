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
from duckduckgo_search import DDGS
try:from gtts import gTTS;TTS=True
except:TTS=False
st.set_page_config(page_title="Favion AI",page_icon="🎯",layout="centered",initial_sidebar_state="collapsed")
try:GEMINI_KEY=st.secrets["GEMINI_API_KEY"];GROQ_KEY=st.secrets["GROQ_API_KEY"]
except:st.error("API Key belum diset");st.stop()
if"messages"not in st.session_state:st.session_state.messages=[]
if"chat_count"not in st.session_state:st.session_state.chat_count=0
if"audio_processed_id"not in st.session_state:st.session_state.audio_processed_id=None
if"selected_model"not in st.session_state:st.session_state.selected_model="gemini"
MAX_CHAT=25
T={"bg":"#0A0F0D","chat_bg":"#111827","user_bg":"#1F2937","text":"#E5E7EB","border":"#1F2937","badge_bg":"#065F46","badge_text":"#A7F3D0","primary":"#10B981"}
BLACKLIST=["bom","senjata","bunuh","bunuh diri","teroris","narkoba","bokep","hentai","porn","seks","sex","bugil","telanjang","memek","jembut","kontol","ngentot","coli","masturbasi","ganja","sabu","ekstasi","heroin","kokain"]
def cek_sensitif(t):
 for k in BLACKLIST:
  if k in t.lower():return True,k
 return False,None
st.markdown(f"""<style>@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');html,body,[class*="css"]{{font-family:'Inter',sans-serif}}#MainMenu,footer,header{{visibility:hidden}}.stApp,.main{{background-color:{T['bg']}}}.block-container{{padding-top:2rem!important;padding-bottom:12rem!important;max-width:48rem!important}}.favion-title{{text-align:center;font-size:2.25rem;font-weight:700;background:linear-gradient(90deg,#10B981 0%,#34D399 50%,#6EE7B7 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:0.25rem}}.favion-subtitle{{text-align:center;color:#6B7280;font-size:0.95rem;margin-bottom:3rem}}.stChatMessage{{background-color:transparent!important;padding:0.75rem 0!important}}[data-testid="stChatMessageContent"]{{background-color:{T['chat_bg']}!important;border-radius:18px!important;padding:12px 16px!important;color:{T['text']}!important;border:1px solid {T['border']};line-height:1.65}}.stChatMessage[data-testid*="user"] [data-testid="stChatMessageContent"]{{background-color:{T['user_bg']}!important}}.stChatInput{{position:fixed!important;bottom:0!important;left:50%!important;transform:translateX(-50%)!important;width:100%!important;max-width:48rem!important;padding:1rem!important;background:{T['bg']}!important;z-index:1001!important}}.stChatInput>div{{background-color:{T['chat_bg']}!important;border:1px solid {T['primary']}!important;border-radius:26px!important}}.favion-badge{{display:inline-block;font-size:0.75rem;padding:4px 10px;border-radius:12px;margin-bottom:8px;margin-right:6px;font-weight:600;background-color:{T['badge_bg']};color:{T['badge_text']}}}.model-badge{{background:#10B981;color:white}}[data-testid="stAudioInput"]{{margin-bottom:10px!important}}</style>""",unsafe_allow_html=True)
genai.configure(api_key=GEMINI_KEY)
gemini_model=genai.GenerativeModel('gemini-2.5-flash')
groq_client=Groq(api_key=GROQ_KEY)
def toast(msg,icon="🎯"):st.toast(msg,icon=icon)
def transcribe_audio(audio_bytes):
 try:
  t=groq_client.audio.transcriptions.create(file=("audio.wav",audio_bytes),model="whisper-large-v3",language="id",response_format="text",temperature=0.0).strip()
  if len(t)<3:return""
  return t
 except Exception as e:toast(f"STT Error: {str(e)[:30]}","❌");return""
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
def search_web(q):
 try:
  with DDGS()as ddgs:r=list(ddgs.text(f"{q} strategi cara tips",max_results=3));return"\n".join([f"- {i['body'][:200]}"for i in r])if r else""
 except:return""
def deteksi_intent(t):
 t=t.lower()
 if any(k in t for k in["bisnis","jualan","omzet","usaha","umkm","profit","marketing"]):return"bisnis"
 if any(k in t for k in["konten","instagram","tiktok","youtube","fyp","ig"]):return"kanal"
 if any(k in t for k in["belajar","utbk","ujian","skripsi","fokus"]):return"belajar"
 if any(k in t for k in["uang","gaji","budget","nabung","investasi","duit"]):return"uang"
 if any(k in t for k in["waktu","sibuk","produktif","jadwal","todo","deadline"]):return"waktu"
 if any(k in t for k in["soal","hitung","rumus","integral","matematika"]):return"lempar_fanilla"
 return"ngobrol"
def jawab_favion(text,image,model_type):
 is_sensitif,kata=cek_sensitif(text)
 if is_sensitif:return f"Maaf bro, aku gak bisa bantu soal '{kata}'. Itu konten sensitif.\n\nCoba topik lain yang positif ya!","ngobrol",model_type
 intent=deteksi_intent(text)
 if intent=="lempar_fanilla":return"Soal sekolah/PR mending tanya Fanilla bro wkwk. Gw jagonya strategi & duit 💚","teman",model_type
 if intent!="ngobrol":
  toast("Favion nyari data...","🔍")
  ref=search_web(f"{intent} {text}")
  if ref:text+=f"\n\n[Data Referensi]:\n{ref}"
 tgl=datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%d %B %Y")
 p=f"""Kamu Favion,FAntastic inoVIsiON.Manager bisnis asik.Tanggal {tgl}.ATURAN:1.Bahasa gampang+gaul tipis."Oke bro,biar omzet naik gini caranya"2.Langsung solusi.3.WAJIB TABEL markdown.Kolom:Strategi|Langkah Aksi|Deadline|Cara Ukur Hasil4.3-5 langkah langsung dilakuin.5.2-3 paragraf+1 tabel.15-25 baris.6.Tutup:"Gas eksekusi bro!"Problem:{text}"""
 models=[model_type,"groq"if model_type=="gemini"else"gemini"]
 for try_model in models:
  try:
   if try_model=="gemini":
    toast("Pake Gemini...","✨")
    content=[p]
    if image:content.append(image)
    res=gemini_model.generate_content(content,stream=True)
    full_text="".join([c.text for c in res if c.text])
   else:
    toast("Pake Groq...","⚡")
    chat=groq_client.chat.completions.create(messages=[{"role":"user","content":p}],model="llama-3.3-70b-versatile",stream=True)
    full_text="".join([c.choices[0].delta.content for c in chat if c.choices[0].delta.content])
   if full_text:return full_text,intent,try_model
  except Exception as e:
   err=str(e)
   if"401"in err:toast("API Key Gemini salah/expired","❌")
   elif"429"in err:toast("Limit Gemini abis, coba Groq...","⚠️")
   elif"quota"in err.lower():toast("Quota abis","⚠️")
   if try_model==models[-1]:return f"Error: {err[:80]}. Cek API Key di Secrets atau coba lagi nanti.","ngobrol",try_model
 return"Error gak dikenal bro.","ngobrol",model_type
with st.sidebar:
 st.markdown("### ⚙️ Manage Favion")
 m=st.selectbox("Pilih Model AI",["Gemini 2.5 Flash","Llama 3.3 70B Groq"],index=0 if st.session_state.selected_model=="gemini"else 1)
 st.session_state.selected_model="gemini"if m=="Gemini 2.5 Flash"else"groq"
 if st.button("🗑️ Hapus Semua Chat"):st.session_state.messages=[];st.session_state.chat_count=0;st.rerun()
 st.metric("Chat Tersisa",f"{MAX_CHAT-st.session_state.chat_count}/{MAX_CHAT}")
if len(st.session_state.messages)==0:
 st.markdown('<div class="favion-title">Favion AI</div>',unsafe_allow_html=True)
 st.markdown('<div class="favion-subtitle">FAntastic inoVIsiON<br>Fantastic Problem,A Fantastic Solution<br>Manager Bisnis,Kanal,Belajar,Uang,Waktu 🎯</div>',unsafe_allow_html=True)
for i,msg in enumerate(st.session_state.messages):
 with st.chat_message(msg["role"]):
  if msg["role"]=="assistant":
   badge={"bisnis":"💼 Bisnis","kanal":"📱 Kanal","belajar":"📚 Belajar","uang":"💰 Uang","waktu":"⏰ Waktu","ngobrol":"💬 Ngobrol"}.get(msg["intent"],"🎯 Favion")
   model="Gemini"if msg.get("model")=="gemini"else"Groq"
   st.markdown(f'<div class="favion-badge">{badge}</div><div class="favion-badge model-badge">{model}</div>',unsafe_allow_html=True)
  if msg["type"]=="image":st.image(msg["content"],caption=msg.get("caption"))
  else:
   st.markdown(msg["content"])
   if msg["role"]=="assistant"and msg["type"]=="text"and TTS:
    if st.button("🔊 Dengarkan",key=f"tts_{i}"):
     audios=text_to_speech(msg["content"])
     if audios:
      for a in audios:st.audio(a,format='audio/mp3')
audio=st.audio_input("Rekam suara",key=f"audio_{st.session_state.chat_count}")
if audio:
 cid=id(audio)
 if st.session_state.audio_processed_id!=cid:
  st.session_state.audio_processed_id=cid
  vt=transcribe_audio(audio.getvalue())
  if vt:
   if st.session_state.chat_count>=MAX_CHAT:st.error("Sesi habis");st.stop()
   st.session_state.chat_count+=1
   st.session_state.messages.append({"role":"user","type":"text","content":vt})
   with st.chat_message("assistant"):
    with st.spinner("Favion mikir..."):
     konten,intent,model=jawab_favion(vt,None,st.session_state.selected_model)
   st.session_state.messages.append({"role":"assistant","type":"text","content":konten,"intent":intent,"model":model})
   st.rerun()
prompt=st.chat_input("Tanya Favion...",accept_file=True,file_type=["jpg","jpeg","png"])
if prompt:
 if st.session_state.chat_count>=MAX_CHAT:st.error("Sesi habis");st.stop()
 st.session_state.chat_count+=1
 user_text=prompt.text if hasattr(prompt,'text')else prompt
 user_file=prompt.files[0]if hasattr(prompt,'files')and prompt.files else None
 user_img=Image.open(user_file).convert("RGB")if user_file else None
 if user_file:st.session_state.messages.append({"role":"user","type":"image","content":user_img})
 if user_text:st.session_state.messages.append({"role":"user","type":"text","content":user_text})
 with st.chat_message("assistant"):
  with st.spinner("Favion mikir..."):
   konten,intent,model=jawab_favion(user_text,user_img,st.session_state.selected_model)
 st.session_state.messages.append({"role":"assistant","type":"text","content":konten,"intent":intent,"model":model})
 st.rerun()
