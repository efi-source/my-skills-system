import streamlit as st
import requests
import json
import base64
from datetime import datetime

# --- חיבור מאובטח ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GEMINI_KEY = st.secrets["GEMINI_KEY"]
except:
    st.error("המפתחות ב-Secrets לא מעודכנים!")
    st.stop()

GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"
REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"
# כתובת API מעודכנת למודל החדש
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"

def github_action(path, method="GET", data=None, sha=None):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"{REPO_API}/{path}"
    try:
        if method == "GET":
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                content = base64.b64decode(r.json()['content']).decode('utf-8')
                try: return json.loads(content), r.json()['sha']
                except: return content, r.json()['sha']
        elif method == "PUT":
            content_str = json.dumps(data, indent=4) if isinstance(data, (dict, list)) else str(data)
            payload = {"message": "דני מעדכן קוד", "content": base64.b64encode(content_str.encode()).decode(), "sha": sha}
            return requests.put(url, headers=headers, json=payload).status_code in [200, 201]
    except: return None, None

def ask_dani(prompt):
    # הנחיה לדני להיות סוכן אוטונומי שמתקן קוד
    system_instr = "שמך דני. אתה סוכן AI עם גישה מלאה לקבצי ה-GitHub. אם מבקשים ממך תיקון קוד, תן את הקוד המלא. ענה בעברית בתוך בועת הצ'אט."
    payload = {"contents": [{"parts": [{"text": f"{system_instr}\n\nמשתמש: {prompt}"}]}]}
    try:
        r = requests.post(GEMINI_URL, json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()['candidates'][0]['content']['parts'][0]['text']
        return f"שגיאת API ({r.status_code}). וודא שהמפתח ב-Secrets תואם לתמונה."
    except: return "דני לא מצליח לגשת לשרת."

# --- עיצוב ממשק ---
st.set_page_config(page_title="Danny AI Agent", layout="centered")
st.markdown("""
<style>
    .scroll-box {
        height: 400px; overflow-y: auto; padding: 15px;
        border: 2px solid #f0f0f0; border-radius: 15px;
        background: #fafafa; display: flex; flex-direction: column; gap: 10px;
    }
    .msg { padding: 10px 15px; border-radius: 15px; max-width: 80%; position: relative; }
    .user { align-self: flex-end; background: #e3ffcc; border: 1px solid #c2e0a6; text-align: right; }
    .ai { align-self: flex-start; background: white; border: 1px solid #ddd; text-align: left; }
    .label { font-weight: bold; font-size: 0.8rem; display: block; margin-bottom: 3px; color: #555; }
</style>
""", unsafe_allow_html=True)

st.title("🤖 דני: סוכן אוטונומי")

# הצגת היסטוריה בתוך קוביה
history, sha_h = github_action("history.json")
if not isinstance(history, list): history = []

st.markdown('<div class="scroll-box">', unsafe_allow_html=True)
for m in history:
    st.markdown(f'<div class="msg user"><span class="label">👤 אתה:</span>{m.get("user")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="msg ai"><span class="label">🤖 דני:</span>{m.get("ai")}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# שורת הקלדה
with st.form(key="chat", clear_on_submit=True):
    cmd = st.text_input("פקודה לדני (למשל: דני, תתקן את עצמך):")
    if st.form_submit_button("שלח") and cmd:
        with st.spinner("דני חושב ומתקן..."):
            ans = ask_dani(cmd)
            history.append({"time": datetime.now().strftime("%H:%M"), "user": cmd, "ai": ans})
            github_action("history.json", "PUT", history, sha_h)
            st.rerun()

with st.sidebar:
    st.header("ניהול")
    if st.button("נקה צ'אט"):
        github_action("history.json", "PUT", [], sha_h)
        st.rerun()
