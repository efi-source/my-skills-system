import streamlit as st
import requests
import json
import base64
from datetime import datetime

# --- אבטחה וחיבורים ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GEMINI_API_KEY = st.secrets["GEMINI_KEY"]
except:
    st.error("חסרים מפתחות ב-Secrets!")
    st.stop()

GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"
REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"
# כתובת API מעודכנת למניעת שגיאת 404
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

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
            payload = {"message": "Update", "content": base64.b64encode(json.dumps(data, indent=4).encode()).decode(), "sha": sha}
            r = requests.put(url, headers=headers, json=payload)
            return r.status_code in [200, 201]
        return [], None
    except: return [], None

def ask_gemini(prompt):
    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        r = requests.post(GEMINI_URL, json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()['candidates'][0]['content']['parts'][0]['text']
        return f"שגיאת AI ({r.status_code})"
    except: return "חיבור נכשל"

# --- עיצוב ממשק דמוי WhatsApp ---
st.set_page_config(page_title="AI Chat Admin", layout="centered")

st.markdown("""
<style>
    /* ריכוז המסך */
    .main .block-container { max-width: 600px; padding-top: 2rem; }
    
    /* בועות צ'אט */
    .chat-container { display: flex; flex-direction: column; gap: 10px; margin-bottom: 80px; }
    .user-bubble { align-self: flex-end; background-color: #dcf8c6; padding: 10px; border-radius: 10px 10px 0 10px; max-width: 80%; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
    .ai-bubble { align-self: flex-start; background-color: white; padding: 10px; border-radius: 10px 10px 10px 0; max-width: 80%; border: 1px solid #ececec; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
    .time { font-size: 0.7rem; color: #999; margin-top: 5px; text-align: left; }
    
    /* שורת הקלדה תחתונה */
    .stTextInput { position: fixed; bottom: 30px; left: 0; right: 0; padding: 0 20px; z-index: 100; max-width: 600px; margin: 0 auto; }
</style>
""", unsafe_allow_html=True)

st.title("💬 AI Master Chat")

# הצגת סקילים ככפתורי בחירה מהירה
skills, _ = github_action("skills.json")
if skills:
    st.caption("בחר סקיל להפעלה:")
    skill_cols = st.columns(len(skills))
    for i, s in enumerate(skills):
        if skill_cols[i].button(s.get('name')):
            st.session_state.temp_input = f"הפעל סקיל: {s.get('name')}"

st.divider()

# הצגת היסטוריית הצ'אט (מעל שורת ההקלדה)
history, _ = github_action("history.json")
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
if history:
    for e in history:
        # הודעת משתמש
        st.markdown(f'<div class="user-bubble">{e.get("user")}<div class="time">{e.get("time")}</div></div>', unsafe_allow_html=True)
        # הודעת AI
        st.markdown(f'<div class="ai-bubble"><b>🤖</b> {e.get("ai")}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# פונקציית שליחה
def handle_send():
    user_msg = st.session_state.chat_input
    if user_msg:
        with st.spinner("שולח..."):
            ai_ans = ask_gemini(user_msg)
            hist, sha = github_action("history.json")
            hist.append({"time": datetime.now().strftime("%H:%M"), "user": user_msg, "ai": ai_ans})
            github_action("history.json", "PUT", hist, sha)
            st.session_state.chat_input = "" # ניקוי השורה

# שורת הקלדה (נשארת למטה)
st.text_input("הקלד הודעה...", key="chat_input", on_change=handle_send)
