import streamlit as st
import requests
import json
import base64
from datetime import datetime

# --- הגדרות אבטחה ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GEMINI_KEY = st.secrets["GEMINI_KEY"]
except:
    st.error("חסרים מפתחות ב-Secrets!")
    st.stop()

GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"
REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"

# --- "הידיים" של דני: פונקציות גיטהאב ---

def github_action(path, method="GET", data=None, sha=None):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"{REPO_API}/{path}"
    try:
        if method == "GET":
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                content = base64.b64decode(r.json()['content']).decode('utf-8')
                try: return json.loads(content), r.json()['sha']
                except: return content, r.json()['sha'] # למקרה של קובץ טקסט/קוד
        elif method == "PUT":
            content_str = json.dumps(data, indent=4) if isinstance(data, (dict, list)) else str(data)
            payload = {
                "message": f"דני מעדכן: {path}",
                "content": base64.b64encode(content_str.encode()).decode(),
                "sha": sha
            }
            r = requests.put(url, headers=headers, json=payload)
            return r.status_code in [200, 201]
    except: return None, None

def ask_dani(prompt):
    # כאן אנחנו נותנים לדני את ה"מוח" - הנחיה שהוא סוכן שיכול לערוך קוד
    system_instr = f"""
    שמך דני. אתה סוכן AI אוטונומי. 
    יש לך הרשאה מלאה לערוך את הקבצים במאגר הגיטהאב {GITHUB_REPO}.
    אם המשתמש מבקש לתקן את הקוד או להוסיף סקיל, עליך להחזיר את הקוד המלא המעודכן בתוך בלוק קוד.
    ענה תמיד בעברית ובידידותיות.
    """
    payload = {"contents": [{"parts": [{"text": f"{system_instr}\n\nמשתמש: {prompt}"}]}]}
    try:
        r = requests.post(GEMINI_URL, json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()['candidates'][0]['content']['parts'][0]['text']
        return f"שגיאת תקשורת ({r.status_code}). וודא שה-API KEY תקין."
    except: return "דני לא הצליח להתחבר לג'מיני."

# --- עיצוב ממשק ---
st.set_page_config(page_title="Danny AI Agent", layout="centered")
st.markdown("""
<style>
    .chat-container {
        height: 450px; overflow-y: auto; padding: 15px;
        border: 2px solid #e0e0e0; border-radius: 15px;
        background: #fdfdfd; display: flex; flex-direction: column; gap: 10px;
    }
    .msg-box { padding: 12px; border-radius: 12px; max-width: 85%; line-height: 1.4; position: relative; }
    .user-msg { align-self: flex-end; background: #dcf8c6; border: 1px solid #c1e1a6; text-align: right; }
    .ai-msg { align-self: flex-start; background: white; border: 1px solid #ddd; text-align: left; }
    .msg-header { font-weight: bold; font-size: 0.85rem; margin-bottom: 4px; display: block; }
</style>
""", unsafe_allow_html=True)

st.title("🤖 דני - סוכן בשליטה מלאה")

# טעינת היסטוריה
history, sha_hist = github_action("history.json")
if not isinstance(history, list): history = []

# הצגת צ'אט
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for m in history:
    st.markdown(f'''
    <div class="msg-box user-msg"><span class="msg-header">👤 אתה:</span>{m.get("user")}</div>
    <div class="msg-box ai-msg"><span class="msg-header">🤖 דני:</span>{m.get("ai")}</div>
    ''', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# שליחת פקודה
with st.form(key="dani_chat", clear_on_submit=True):
    user_cmd = st.text_input("דבר עם דני (למשל: דני, תקן את העיצוב):")
    submit = st.form_submit_button("שלח")

    if submit and user_cmd:
        with st.spinner("דני מעבד..."):
            answer = ask_dani(user_cmd)
            history.append({"time": datetime.now().strftime("%H:%M"), "user": user_cmd, "ai": answer})
            github_action("history.json", "PUT", history, sha_hist)
            st.rerun()

# --- לוח בקרה ---
with st.sidebar:
    st.header("⚡ שליטה בסוכן")
    if st.button("נקה זיכרון"):
        github_action("history.json", "PUT", [], sha_hist)
        st.rerun()
    
    st.warning("שים לב: דני יכול לשנות את הקוד של עצמו. אם הוא מבצע שינוי, האתר יתרענן אוטומטית.")
