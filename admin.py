import streamlit as st
import requests
import json
import base64
from datetime import datetime

# --- הגדרות אבטחה וחיבור ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GEMINI_KEY = st.secrets["GEMINI_KEY"]
except:
    st.error("חסרים מפתחות ב-Secrets!")
    st.stop()

GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"
REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"
# שימוש בכתובת API יציבה ביותר
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
            payload = {"message": "Danny Update", "content": base64.b64encode(content_str.encode()).decode(), "sha": sha}
            return requests.put(url, headers=headers, json=payload).status_code in [200, 201]
    except: return None, None

def ask_dani(prompt):
    # מבנה הודעה מתוקן למניעת שגיאה 400
    payload = {
        "contents": [{
            "parts": [{"text": f"שמך דני, אתה סוכן AI אוטונומי. ענה בעברית על: {prompt}"}]
        }]
    }
    headers = {'Content-Type': 'application/json'}
    try:
        r = requests.post(GEMINI_URL, json=payload, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json()['candidates'][0]['content']['parts'][0]['text']
        return f"דני לא זמין (קוד {r.status_code}): {r.text[:100]}"
    except Exception as e:
        return f"שגיאת חיבור: {str(e)[:50]}"

# --- עיצוב ממשק ---
st.set_page_config(page_title="Danny AI Agent", layout="centered")

st.markdown("""
<style>
    .chat-container {
        height: 500px; overflow-y: auto; padding: 20px;
        border: 1px solid #ddd; border-radius: 15px;
        background: #f9f9f9; display: flex; flex-direction: column; gap: 15px;
        margin-bottom: 20px;
    }
    .bubble { padding: 12px 18px; border-radius: 18px; max-width: 80%; line-height: 1.5; font-size: 1rem; }
    .user { align-self: flex-end; background: #dcf8c6; border: 1px solid #c1e1a6; text-align: right; }
    .ai { align-self: flex-start; background: white; border: 1px solid #eee; text-align: left; }
    .name-tag { font-weight: bold; font-size: 0.75rem; margin-bottom: 4px; display: block; color: #666; }
</style>
""", unsafe_allow_html=True)

# --- סרגל צדדי (סקילים וניהול) ---
with st.sidebar:
    st.title("🛠️ סקילים וניהול")
    skills, _ = github_action("skills.json")
    if skills and isinstance(skills, list):
        st.subheader("סקילים פעילים")
        for s in skills:
            if st.button(f"⚡ {s.get('name')}", use_container_width=True):
                st.session_state.skill_trigger = s.get('name')
    
    st.divider()
    if st.button("🗑️ נקה היסטוריה", use_container_width=True):
        _, sha_h = github_action("history.json")
        github_action("history.json", "PUT", [], sha_h)
        st.rerun()

# --- גוף העמוד - צ'אט ---
st.title("🤖 דני: סוכן אוטונומי")

history, sha_hist = github_action("history.json")
if not isinstance(history, list): history = []

# הצגת הצ'אט
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
if not history:
    st.markdown("<p style='text-align:center; color:grey; padding-top:200px;'>דני מחכה לפקודה שלך...</p>", unsafe_allow_html=True)
else:
    for m in history:
        st.markdown(f'<div class="bubble user"><span class="name-tag">👤 אתה</span>{m.get("user")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="bubble ai"><span class="name-tag">🤖 דני</span>{m.get("ai")}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# פונקציית שליחה
def handle_send():
    cmd = st.session_state.user_input
    if cmd:
        with st.spinner("דני חושב..."):
            res = ask_dani(cmd)
            history.append({"user": cmd, "ai": res, "time": datetime.now().strftime("%H:%M")})
            github_action("history.json", "PUT", history, sha_hist)
            st.session_state.user_input = "" # איפוס השורה

# שורת הקלדה קבועה למטה
st.text_input("הקלד הודעה לדני...", key="user_input", on_change=handle_send)

# טיפול בהפעלת סקיל מהצד
if 'skill_trigger' in st.session_state:
    skill_name = st.session_state.pop('skill_trigger')
    with st.spinner(f"מפעיל {skill_name}..."):
        res = ask_dani(f"הפעל את הסקיל: {skill_name}")
        history.append({"user": f"הפעלה: {skill_name}", "ai": res, "time": datetime.now().strftime("%H:%M")})
        github_action("history.json", "PUT", history, sha_hist)
        st.rerun()
