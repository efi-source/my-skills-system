import streamlit as st
import requests
import json
import base64
from datetime import datetime

# --- חיבור וניקוי מפתחות ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"].strip()
    # ניקוי המפתח מרווחים שגורמים לשגיאה 400
    GEMINI_KEY = st.secrets["GEMINI_KEY"].strip()
except:
    st.error("חסרים מפתחות ב-Secrets!")
    st.stop()

GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"
REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"

# --- פונקציות GitHub ---

def github_get_files(path):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(f"{REPO_API}/{path}", headers=headers)
    return r.json() if r.status_code == 200 else []

def github_action(path, method="GET", data=None, sha=None):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"{REPO_API}/{path}"
    if method == "GET":
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            content = base64.b64decode(r.json()['content']).decode('utf-8')
            return json.loads(content), r.json()['sha']
        return [], None
    else:
        payload = {"message": "Update Chat", "content": base64.b64encode(json.dumps(data, indent=4).encode()).decode(), "sha": sha}
        return requests.put(url, headers=headers, json=payload).status_code in [200, 201]

def ask_dani(prompt):
    payload = {"contents": [{"parts": [{"text": f"שמך דני, סוכן AI. ענה בעברית: {prompt}"}]}]}
    try:
        r = requests.post(GEMINI_URL, json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()['candidates'][0]['content']['parts'][0]['text']
        return f"שגיאה {r.status_code}: וודא שהמפתח ב-Secrets תקין ללא רווחים."
    except: return "שגיאת חיבור."

# --- הגדרות דף ועיצוב ---
st.set_page_config(page_title="Danny AI - Multi Chat", layout="wide")
st.markdown("""
<style>
    .chat-box { height: 550px; overflow-y: auto; padding: 15px; border-radius: 15px; background: #f0f2f6; display: flex; flex-direction: column; gap: 10px; }
    .msg { padding: 10px 15px; border-radius: 15px; max-width: 85%; position: relative; }
    .user { align-self: flex-end; background: #dcf8c6; border: 1px solid #c1e1a6; }
    .ai { align-self: flex-start; background: white; border: 1px solid #ddd; }
    .tag { font-weight: bold; font-size: 0.7rem; display: block; margin-bottom: 3px; }
</style>
""", unsafe_allow_html=True)

# --- סרגל צדדי: סקילים וניהול צ'אטים ---
with st.sidebar:
    st.title("🤖 דני - ניהול")
    
    # כפתור צ'אט חדש
    if st.button("➕ צ'אט חדש", use_container_width=True):
        new_id = f"chat_{datetime.now().strftime('%d%m_%H%M')}.json"
        st.session_state.current_chat = new_id
        st.rerun()

    st.divider()
    st.subheader("📁 צ'אטים קודמים")
    
    # טעינת רשימת קבצים מתיקיית הצאטים (אם אין תיקייה, השתמש בשורש)
    files = github_get_files("") 
    chat_files = [f['name'] for f in files if f['name'].startswith("chat_") and f['name'].endswith(".json")]
    
    for cf in sorted(chat_files, reverse=True):
        if st.button(f"💬 {cf.replace('.json', '')}", use_container_width=True):
            st.session_state.current_chat = cf
            st.rerun()

    st.divider()
    st.subheader("⚡ סקילים")
    skills, _ = github_action("skills.json")
    if skills:
        for s in skills:
            if st.button(f"🚀 {s.get('name')}", use_container_width=True):
                st.session_state.trigger_skill = s.get('name')

# --- גוף העמוד ---
current_chat_file = st.session_state.get("current_chat", "chat_main.json")
st.title(f"💬 צ'אט: {current_chat_file.replace('.json', '')}")

# טעינת היסטוריה של הצ'אט הנבחר
history, sha = github_action(current_chat_file)

# תצוגת צ'אט
st.markdown('<div class="chat-box">', unsafe_allow_html=True)
for m in history:
    st.markdown(f'<div class="msg user"><span class="tag">👤 אתה</span>{m.get("user")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="msg ai"><span class="tag">🤖 דני</span>{m.get("ai")}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# שליחה
def send():
    msg = st.session_state.user_msg
    if msg:
        with st.spinner("דני מגיב..."):
            ans = ask_dani(msg)
            history.append({"user": msg, "ai": ans})
            github_action(current_chat_file, "PUT", history, sha)
            st.session_state.user_msg = ""

st.text_input("הקלד הודעה לדני...", key="user_msg", on_change=send)

# הפעלת סקיל
if "trigger_skill" in st.session_state:
    skill = st.session_state.pop("trigger_skill")
    ans = ask_dani(f"הפעל סקיל: {skill}")
    history.append({"user": f"הפעלה: {skill}", "ai": ans})
    github_action(current_chat_file, "PUT", history, sha)
    st.rerun()
