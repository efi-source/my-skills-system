import streamlit as st
import google.generativeai as genai
import requests
import json
import base64
from datetime import datetime

# --- חיבור וניקוי מפתחות ---
def get_clean_secret(name):
    try:
        return str(st.secrets[name]).strip().strip('"').strip("'")
    except: return None

GEMINI_KEY = get_clean_secret("GEMINI_KEY")
GITHUB_TOKEN = get_clean_secret("GITHUB_TOKEN")

# בדיקת המוח של דני
try:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    # בדיקת דופק מהירה
    model.generate_content("test")
    HAS_AI = True
except Exception as e:
    HAS_AI = False
    AI_ERROR = str(e)

GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"
REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"

# --- פונקציות GitHub ---
def github_action(path, method="GET", data=None, sha=None):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"{REPO_API}/{path}"
    try:
        if method == "GET":
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                return json.loads(base64.b64decode(r.json()['content']).decode('utf-8')), r.json()['sha']
            return [], None
        elif method == "DELETE":
            return requests.delete(url, headers=headers, json={"message": "del", "sha": sha}).status_code == 200
        else:
            payload = {"message": "update", "content": base64.b64encode(json.dumps(data).encode()).decode(), "sha": sha}
            return requests.put(url, headers=headers, json=payload).status_code in [200, 201]
    except: return [], None

# --- ממשק משתמש ---
st.set_page_config(page_title="דני AI - מאסטר", layout="wide")

with st.sidebar:
    st.title("🤖 סטטוס מערכת")
    if HAS_AI: 
        st.success("✅ דני מחובר ומוכן!")
    else: 
        st.error(f"❌ שגיאת AI: {AI_ERROR[:50]}")
    
    if st.button("➕ צ'אט חדש"):
        st.session_state.active_chat = None
        st.rerun()

    st.divider()
    st.subheader("📁 שיחות קודמות")
    res = requests.get(REPO_API, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    if res.status_code == 200:
        for f in [x for x in res.json() if x['name'].startswith("chat_")]:
            col1, col2 = st.columns([4, 1])
            if col1.button(f"💬 {f['name'][5:-5]}", key=f['name']):
                st.session_state.active_chat = f['name']
                st.rerun()
            if col2.button("🗑️", key=f"del_{f['name']}"):
                github_action(f['name'], "DELETE", sha=f['sha'])
                st.rerun()

# --- הצ'אט ---
active_file = st.session_state.get("active_chat")
history, current_sha = github_action(active_file) if active_file else ([], None)

st.title(f"📺 שיחה פעילה: {active_file or 'חדשה'}")

for m in history:
    with st.chat_message("user"): st.write(m["user"])
    with st.chat_message("assistant"): st.write(m["ai"])

def handle_send():
    msg = st.session_state.user_input
    if msg and HAS_AI:
        with st.spinner("דני מקליד..."):
            try:
                res = model.generate_content(msg).text
                history.append({"user": msg, "ai": res})
                # יצירת שם קובץ חכם או לפי זמן
                fname = active_file or f"chat_{datetime.now().strftime('%H%M%S')}.json"
                github_action(fname, "PUT", history, current_sha)
                st.session_state.active_chat = fname
                st.session_state.user_input = ""
            except Exception as e: st.error(f"שגיאה: {e}")

st.text_input("דבר עם דני...", key="user_input", on_change=handle_send)
