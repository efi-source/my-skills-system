import streamlit as st
import requests
import json
import base64
from datetime import datetime

# --- הגדרות אבטחה (משיכה מה-Secrets) ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GEMINI_API_KEY = st.secrets["GEMINI_KEY"]
except:
    st.error("המפתחות חסרים ב-Secrets!")
    st.stop()

GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"
REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"
# תיקון נתיב ה-API של ג'מיני
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# --- פונקציות עזר ---
def github_action(path, method="GET", data=None, sha=None):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"{REPO_API}/{path}"
    try:
        r = requests.get(url, headers=headers) if method == "GET" else None
        if method == "GET" and r.status_code == 200:
            content = base64.b64decode(r.json()['content']).decode('utf-8')
            return json.loads(content), r.json()['sha']
        elif method == "PUT":
            payload = {"message": "Sync", "content": base64.b64encode(json.dumps(data, indent=4).encode()).decode(), "sha": sha}
            r = requests.put(url, headers=headers, json=payload)
            return r.status_code in [200, 201]
        return [], None
    except: return [], None

def ask_gemini(prompt):
    try:
        # מבנה בקשה תקין לג'מיני
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        r = requests.post(GEMINI_URL, json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()['candidates'][0]['content']['parts'][0]['text']
        return f"שגיאת AI: {r.status_code}"
    except: return "שגיאת חיבור ל-AI"

# --- עיצוב ממשק ---
st.set_page_config(page_title="AI Admin Pro", layout="wide")
st.markdown("""
<style>
    .stTextInput>div>div>input { background-color: #f1f5f9; }
    .chat-card { background: white; padding: 15px; border-radius: 10px; border-right: 5px solid #3b82f6; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .skill-box { background: #e2e8f0; padding: 10px; border-radius: 8px; text-align: center; cursor: pointer; border: 1px solid #cbd5e1; }
    .skill-box:hover { background: #d1d5db; }
</style>
""", unsafe_allow_html=True)

st.title("🧠 AI Master Control")

# --- חלק 1: ניהול סקילים (לוח בחירה) ---
st.subheader("🛠️ ספרייית סקילים")
skills, _ = github_action("skills.json")
if skills:
    cols = st.columns(4)
    for i, s in enumerate(skills):
        with cols[i % 4]:
            if st.button(f"⚡ {s.get('name')}", use_container_width=True, help=s.get('description')):
                st.session_state.input = f"הפעל סקיל: {s.get('name')}"

st.divider()

# --- חלק 2: צ'אט (פקודות) ---
# פונקציה לניקוי הטקסט לאחר שליחה
def send_command():
    cmd = st.session_state.user_input
    if cmd:
        with st.spinner("מעבד..."):
            ans = ask_gemini(cmd)
            hist, sha = github_action("history.json")
            hist.append({"time": datetime.now().strftime("%H:%M"), "user": cmd, "ai": ans})
            github_action("history.json", "PUT", hist, sha)
            st.session_state.user_input = "" # מנקה את התיבה

st.subheader("🤖 שלח פקודה")
st.text_input("הזן פקודה ולחץ Enter:", key="user_input", on_change=send_command)

st.divider()

# --- חלק 3: יומן פעולות (האחרון למטה) ---
st.subheader("📜 יומן פעולות")
history, _ = github_action("history.json")
if history:
    # כאן אנחנו לא הופכים (reversed) - כדי שהחדש יהיה למטה
    for e in history:
        st.markdown(f"""
        <div class="chat-card">
            <small style="color:gray;">{e.get('time')} | 👤 {e.get('user')}</small>
            <div style="margin-top:5px;"><b>🤖:</b> {e.get('ai')}</div>
        </div>
        """, unsafe_allow_html=True)
