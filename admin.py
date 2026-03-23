import streamlit as st
import requests
import json
import base64
from datetime import datetime

# --- אבטחה (Secrets) ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GEMINI_API_KEY = st.secrets["GEMINI_KEY"]
except:
    st.error("בדוק שהגדרת Secrets ב-Streamlit!")
    st.stop()

# הגדרות מערכת
GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"
REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"
# כתובת API יציבה (v1)
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# --- פונקציות ליבה של דני ---

def github_file(path, method="GET", content=None, sha=None):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"{REPO_API}/{path}"
    try:
        if method == "GET":
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                return json.loads(base64.b64decode(r.json()['content']).decode('utf-8')), r.json()['sha']
        else:
            payload = {"message": f"דני מעדכן: {path}", "content": base64.b64encode(json.dumps(content, indent=4).encode()).decode(), "sha": sha}
            r = requests.put(url, headers=headers, json=payload)
            return r.status_code in [200, 201]
        return [], None
    except: return [], None

def dani_think(prompt):
    # הנחיה לדני: הוא סוכן אוטונומי
    system_prompt = f"שמך דני. אתה סוכן AI עם גישה לקבצי ה-GitHub של המערכת. פקודה נוכחית: {prompt}"
    payload = {"contents": [{"parts": [{"text": system_prompt}]}]}
    try:
        r = requests.post(GEMINI_URL, json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()['candidates'][0]['content']['parts'][0]['text']
        return f"דני נתקל בשגיאה ({r.status_code}). בדוק את ה-API Key."
    except: return "דני לא מצליח להתחבר לרשת."

# --- עיצוב ממשק Pro ---
st.set_page_config(page_title="Danny AI Agent", layout="centered")

st.markdown(f"""
<style>
    /* קוביית צ'אט נגללת */
    .chat-box {{
        height: 400px;
        overflow-y: auto;
        border: 1px solid #e0e0e0;
        border-radius: 15px;
        padding: 20px;
        background: #f9f9f9;
        display: flex;
        flex-direction: column;
        margin-bottom: 20px;
    }}
    .user-msg {{ align-self: flex-end; background: #dcf8c6; padding: 10px; border-radius: 10px; margin: 5px; max-width: 80%; text-align: right; }}
    .ai-msg {{ align-self: flex-start; background: white; padding: 10px; border-radius: 10px; margin: 5px; max-width: 80%; border: 1px solid #ddd; }}
</style>
""", unsafe_allow_html=True)

st.title("🤖 דני - סוכן אוטונומי")

# הצגת הצ'אט בתוך קוביה
history, _ = github_file("history.json")

chat_html = '<div class="chat-box">'
if history:
    for m in history:
        chat_html += f'<div class="user-msg"><b>אתה:</b><br>{m.get("user")}</div>'
        chat_html += f'<div class="ai-msg"><b>דני:</b><br>{m.get("ai")}</div>'
chat_html += '</div>'
st.markdown(chat_html, unsafe_allow_html=True)

# שורת שליחה למטה
with st.form(key="chat_input", clear_on_submit=True):
    cmd = st.text_input("דבר עם דני:", placeholder="למשל: דני, תיצור סקיל חדש של בדיקת מזג אוויר")
    submit = st.form_submit_button("שלח לדני")

    if submit and cmd:
        with st.spinner("דני מעבד ומתעדכן..."):
            res = dani_think(cmd)
            hist, sha = github_file("history.json")
            hist.append({"time": datetime.now().strftime("%H:%M"), "user": cmd, "ai": res})
            if github_file("history.json", "PUT", hist, sha):
                st.rerun()

# --- לוח בקרה של דני ---
with st.sidebar:
    st.header("🛠️ יכולות של דני")
    if st.button("נקה זיכרון צ'אט"):
        github_file("history.json", "PUT", [], _)
        st.rerun()
    
    st.info("דני יכול כעת לערוך את הקבצים: admin.py, skills.json, history.json")
