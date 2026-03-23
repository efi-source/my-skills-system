import streamlit as st
import google.generativeai as genai
import requests
import json
import base64
from datetime import datetime

# --- הגדרות ליבה ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"].strip()
    GEMINI_KEY = st.secrets["GEMINI_KEY"].strip()
    # חיבור רשמי לגוגל
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"שגיאה בהגדרות: {e}")
    st.stop()

GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"
REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"

# --- פונקציות GitHub ---

def github_get_files():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(REPO_API, headers=headers)
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
        payload = {"message": "Danny update", "content": base64.b64encode(json.dumps(data, indent=4).encode()).decode(), "sha": sha}
        return requests.put(url, headers=headers, json=payload).status_code in [200, 201]

def ask_dani(prompt):
    try:
        response = model.generate_content(f"שמך דני. ענה בעברית: {prompt}")
        return response.text
    except Exception as e:
        return f"שגיאה בחיבור לגוגל: {str(e)}"

# --- עיצוב ממשק ---
st.set_page_config(page_title="Danny AI", layout="wide")
st.markdown("""
<style>
    .chat-box { height: 500px; overflow-y: auto; padding: 20px; background: #f8f9fa; border-radius: 15px; border: 1px solid #eee; display: flex; flex-direction: column; gap: 10px; }
    .msg { padding: 12px; border-radius: 12px; max-width: 75%; position: relative; }
    .user { align-self: flex-end; background: #e3ffcc; text-align: right; }
    .ai { align-self: flex-start; background: white; border: 1px solid #ddd; }
    .label { font-weight: bold; font-size: 0.7rem; display: block; margin-bottom: 2px; }
</style>
""", unsafe_allow_html=True)

# --- סרגל צדדי: ניהול צ'אטים וסקילים ---
with st.sidebar:
    st.title("🤖 דני - ניהול")
    
    if st.button("➕ צ'אט חדש", use_container_width=True):
        st.session_state.current_chat = f"chat_{datetime.now().strftime('%H%M%S')}.json"
        st.rerun()

    st.subheader("📁 שיחות קודמות")
    files = github_get_files()
    chat_files = [f['name'] for f in files if f['name'].startswith("chat_") and f['name'].endswith(".json")]
    for cf in sorted(chat_files, reverse=True):
        if st.button(f"💬 {cf}", use_container_width=True):
            st.session_state.current_chat = cf
            st.rerun()

    st.divider()
    st.subheader("⚡ סקילים")
    skills, _ = github_action("skills.json")
    if skills:
        for s in skills:
            if st.button(f"🚀 {s.get('name')}", use_container_width=True):
                st.session_state.trigger = s.get('name')

# --- גוף העמוד ---
current_file = st.session_state.get("current_chat", "chat_main.json")
st.title(f"שיחה: {current_file}")

history, sha = github_action(current_file)

# הצגת הצ'אט
st.markdown('<div class="chat-box">', unsafe_allow_html=True)
for m in history:
    st.markdown(f'<div class="msg user"><span class="label">👤 אתה</span>{m.get("user")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="msg ai"><span class="label">🤖 דני</span>{m.get("ai")}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# שליחת הודעה
def send_msg():
    txt = st.session_state.user_input
    if txt:
        with st.spinner("דני חושב..."):
            ans = ask_dani(txt)
            history.append({"user": txt, "ai": ans})
            github_action(current_file, "PUT", history, sha)
            st.session_state.user_input = ""

st.text_input("דבר עם דני...", key="user_input", on_change=send_msg)

# הפעלת סקיל
if "trigger" in st.session_state:
    skill = st.session_state.pop("trigger")
    ans = ask_dani(f"הפעל סקיל: {skill}")
    history.append({"user": f"הפעלה: {skill}", "ai": ans})
    github_action(current_file, "PUT", history, sha)
    st.rerun()
