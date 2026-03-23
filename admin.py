import streamlit as st
import requests
import json
import base64
from datetime import datetime

# --- הגדרות ליבה ---
try:
    # וודא שב-Streamlit Secrets השמות הם בדיוק אלו:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GEMINI_KEY = st.secrets["GEMINI_KEY"]
except Exception as e:
    st.error(f"שגיאה: מפתחות חסרים ב-Secrets! ({e})")
    st.stop()

GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"
REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"

# ניסיון שימוש במודל היציב ביותר למניעת 404
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"

# --- פונקציות עזר של דני ---

def github_action(path, method="GET", data=None, sha=None):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"{REPO_API}/{path}"
    try:
        if method == "GET":
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                content = base64.b64decode(r.json()['content']).decode('utf-8')
                return json.loads(content), r.json()['sha']
        elif method == "PUT":
            payload = {"message": f"דני מעדכן את {path}", "content": base64.b64encode(json.dumps(data, indent=4).encode()).decode(), "sha": sha}
            r = requests.put(url, headers=headers, json=payload)
            return r.status_code in [200, 201]
        return [], None
    except: return [], None

def ask_dani(prompt):
    # הנחיה לדני להיות סוכן שמתקן קוד ומוסיף סקילים
    context = "שמך דני. אתה סוכן AI עם גישה לעריכת קבצי ה-GitHub של המערכת. ענה בקצרה ובעברית."
    payload = {"contents": [{"parts": [{"text": f"{context}\n\nמשתמש: {prompt}"}]}]}
    try:
        r = requests.post(GEMINI_URL, json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()['candidates'][0]['content']['parts'][0]['text']
        return f"שגיאת חיבור (קוד {r.status_code}). וודא שה-API Key תקין ותומך במודל flash."
    except: return "דני לא מצליח לגשת לשרת ה-AI."

# --- עיצוב הממשק (קוביה נגללת) ---
st.set_page_config(page_title="Danny AI Agent", layout="centered")
st.markdown("""
<style>
    .chat-box {
        height: 500px;
        overflow-y: scroll;
        padding: 15px;
        border: 1px solid #ddd;
        border-radius: 10px;
        background-color: #fcfcfc;
        display: flex;
        flex-direction: column;
    }
    .user-bubble { background-color: #dcf8c6; padding: 10px; border-radius: 10px; margin: 5px; align-self: flex-end; max-width: 80%; border: 1px solid #c1e1a6; }
    .ai-bubble { background-color: #ffffff; padding: 10px; border-radius: 10px; margin: 5px; align-self: flex-start; max-width: 80%; border: 1px solid #eee; }
</style>
""", unsafe_allow_html=True)

st.title("🤖 הצ'אט של דני")

# טעינת היסטוריה
history, sha_hist = github_action("history.json")

# הצגת הצ'אט בתוך קוביה
chat_container = ""
if history:
    for msg in history:
        chat_container += f'<div class="user-bubble"><b>אתה:</b> {msg.get("user")}</div>'
        chat_container += f'<div class="ai-bubble"><b>דני:</b> {msg.get("ai")}</div>'
else:
    chat_container = "<p style='text-align:center; color:gray;'>אין הודעות בזיכרון.</p>"

st.markdown(f'<div class="chat-box">{chat_container}</div>', unsafe_allow_html=True)

# שורת הקלדה למטה
with st.form(key="send_msg", clear_on_submit=True):
    user_input = st.text_input("דבר עם דני (למשל: דני, תוסיף סקיל חדש):", key="input")
    submit = st.form_submit_button("שלח")

    if submit and user_input:
        with st.spinner("דני חושב..."):
            ans = ask_dani(user_input)
            history.append({"time": datetime.now().strftime("%H:%M"), "user": user_input, "ai": ans})
            github_action("history.json", "PUT", history, sha_hist)
            st.rerun()

# לוח בקרה צדדי
with st.sidebar:
    st.header("⚙️ בקרה")
    if st.button("🗑️ נקה היסטוריה"):
        github_action("history.json", "PUT", [], sha_hist)
        st.rerun()
