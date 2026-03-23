import streamlit as st
import requests
import json
import base64
from datetime import datetime

# --- משיכת מפתחות מאובטחת מה-Secrets של Streamlit ---
# GitHub לא יראה את המפתחות כאן ולכן לא יבטל אותם!
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GEMINI_API_KEY = st.secrets["GEMINI_KEY"]
except Exception as e:
    st.error("שגיאה: המפתחות לא נמצאו ב-Secrets. וודא שהגדרת אותם ב-Streamlit Cloud.")
    st.stop()

GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"

# נתיבי API
REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# --- עיצוב ממשק Master UI ---
st.set_page_config(page_title="AI Master Control", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    .main-title { color: #1e293b; text-align: center; font-weight: 800; }
    .chat-bubble {
        background: white; padding: 20px; border-radius: 15px;
        border-right: 6px solid #3b82f6; margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .ai-response { color: #1e293b; background: #f1f5f9; padding: 10px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- פונקציות תקשורת ---
def github_action(path, method="GET", data=None, sha=None):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"{REPO_API}/{path}"
    try:
        if method == "GET":
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                content = base64.b64decode(r.json()['content']).decode('utf-8')
                return json.loads(content), r.json()['sha']
            return [], None
        elif method == "PUT":
            payload = {
                "message": "System Sync via Secrets",
                "content": base64.b64encode(json.dumps(data, indent=4).encode('utf-8')).decode('utf-8'),
                "sha": sha
            }
            r = requests.put(url, headers=headers, json=payload)
            return r.status_code in [200, 201]
    except: return [], None

def ask_gemini(prompt):
    try:
        payload = {"contents": [{"parts": [{"text": f"ענה בעברית: {prompt}"}]}]}
        r = requests.post(GEMINI_URL, json=payload, timeout=10)
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except: return "שגיאה בתקשורת עם ה-AI"

# --- גוף האפליקציה ---
st.markdown('<h1 class="main-title">🧠 AI Autonomous Admin</h1>', unsafe_allow_html=True)

# כפתור בדיקה בסידבר
with st.sidebar:
    if st.button("🔍 בדיקת חיבור סופית"):
        _, sha = github_action("history.json")
        if sha: st.success("המערכת מחוברת ומאובטחת! ✅")
        else: st.error("חיבור נכשל. בדוק את ה-Secrets.")

# הצגת סקילים
st.subheader("🛠️ סקילים")
skills, _ = github_action("skills.json")
if skills:
    cols = st.columns(3)
    for i, s in enumerate(skills):
        with cols[i % 3]:
            st.info(f"**{s.get('name')}**")

st.divider()

# צ'אט
st.subheader("🤖 שלח פקודה")
user_cmd = st.text_input("הזן הודעה:", key="input")
if st.button("שגר פקודה", type="primary"):
    if user_cmd:
        with st.spinner("הסוכן חושב..."):
            answer = ask_gemini(user_cmd)
            hist, sha = github_action("history.json")
            hist.append({"time": datetime.now().strftime("%H:%M"), "user": user_cmd, "ai": answer})
            if github_action("history.json", "PUT", hist, sha):
                st.success("נשמר בזיכרון המאובטח!")
                st.rerun()

st.divider()

# היסטוריה
st.subheader("📜 יומן פעולות")
history, _ = github_action("history.json")
if history:
    for entry in reversed(history):
        st.markdown(f"""
        <div class="chat-bubble">
            <div style="color:gray;">👤 פקודה: {entry.get('user')}</div>
            <div class="ai-response">🤖 {entry.get('ai')}</div>
        </div>
        """, unsafe_allow_html=True)
