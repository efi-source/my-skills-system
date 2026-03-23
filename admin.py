import streamlit as st
import requests
import json
import base64
from datetime import datetime

# --- הגדרות אבטחה (Secrets) ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GEMINI_API_KEY = st.secrets["GEMINI_KEY"]
except:
    st.error("חסרים מפתחות ב-Secrets!")
    st.stop()

GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"
REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"
# כתובת API מעודכנת שעובדת בוודאות
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

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
        # אם יש שגיאה, נדפיס אותה כדי שנדע מה קרה
        if r.status_code == 200:
            return r.json()['candidates'][0]['content']['parts'][0]['text']
        return f"שגיאת AI ({r.status_code}): {r.text[:50]}"
    except Exception as e:
        return f"שגיאת חיבור: {str(e)[:50]}"

# --- עיצוב ממשק ---
st.set_page_config(page_title="AI Master Chat", layout="centered")

st.markdown("""
<style>
    .main .block-container { max-width: 600px; padding-bottom: 120px; }
    /* עיצוב בועות צ'אט */
    .user-bubble { background-color: #dcf8c6; padding: 12px; border-radius: 15px 15px 0 15px; margin: 10px 0; align-self: flex-end; width: fit-content; max-width: 85%; margin-left: auto; border: 1px solid #c5e1a5; }
    .ai-bubble { background-color: white; padding: 12px; border-radius: 15px 15px 15px 0; margin: 10px 0; align-self: flex-start; width: fit-content; max-width: 85%; border: 1px solid #e0e0e0; }
    .time { font-size: 0.65rem; color: #888; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

st.title("💬 AI Master Chat")

# --- הצגת סקילים כפתורים ---
st.subheader("🛠️ סקילים")
skills, _ = github_action("skills.json")
if skills:
    cols = st.columns(len(skills))
    for i, s in enumerate(skills):
        if cols[i].button(f"⚡ {s.get('name')}", use_container_width=True):
             # לחיצה על כפתור תשלח פקודה אוטומטית
             with st.spinner("מפעיל סקיל..."):
                ans = ask_gemini(f"הפעל סקיל: {s.get('name')}")
                hist, sha = github_action("history.json")
                hist.append({"time": datetime.now().strftime("%H:%M"), "user": f"הפעלה: {s.get('name')}", "ai": ans})
                github_action("history.json", "PUT", hist, sha)
                st.rerun()

st.divider()

# --- הצגת הצ'אט (חדש למטה) ---
history, _ = github_action("history.json")
if history:
    for e in history:
        st.markdown(f'<div class="user-bubble"><b>👤 אתה:</b><br>{e.get("user")}<div class="time">{e.get("time")}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ai-bubble"><b>🤖 AI:</b><br>{e.get("ai")}</div>', unsafe_allow_html=True)

# --- שורת הקלדה קבועה למטה ---
# אנחנו משתמשים ב-container כדי לקבע את זה
input_container = st.container()
with input_container:
    with st.form(key='chat_form', clear_on_submit=True):
        user_input = st.text_input("הקלד הודעה...", placeholder="מה תרצה לעשות?")
        submit_button = st.form_submit_button(label='שלח')
        
        if submit_button and user_input:
            with st.spinner("ה-AI מגיב..."):
                answer = ask_gemini(user_input)
                hist, sha = github_action("history.json")
                hist.append({"time": datetime.now().strftime("%H:%M"), "user": user_input, "ai": answer})
                if github_action("history.json", "PUT", hist, sha):
                    st.rerun()
