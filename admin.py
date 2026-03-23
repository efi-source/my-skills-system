import streamlit as st
import google.generativeai as genai
import requests
import json
import base64
from datetime import datetime

# --- הגדרות וחיבור ---
try:
    # מנקה רווחים וגרשיים אם השתרבבו בטעות
    GEMINI_KEY = st.secrets["GEMINI_KEY"].strip().replace('"', '')
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"].strip().replace('"', '')
    
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"שגיאה ב-Secrets: {e}")
    st.stop()

GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"
REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"

# --- פונקציות GitHub ---
def github_action(path, method="GET", data=None, sha=None):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"{REPO_API}/{path}"
    
    if method == "GET":
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            content = base64.b64decode(r.json()['content']).decode('utf-8')
            return json.loads(content), r.json()['sha']
        return [], None
    
    elif method == "DELETE":
        payload = {"message": "Delete chat", "sha": sha}
        return requests.delete(url, headers=headers, json=payload).status_code == 200
    
    else: # PUT
        payload = {"message": "Update chat", "content": base64.b64encode(json.dumps(data, indent=4).encode()).decode(), "sha": sha}
        return requests.put(url, headers=headers, json=payload).status_code in [200, 201]

def ask_dani(prompt):
    try:
        response = model.generate_content(f"אתה דני, סוכן AI עוזר. ענה בעברית: {prompt}")
        return response.text
    except Exception as e:
        return f"שגיאה (בדוק מפתח): {str(e)[:50]}"

# --- עיצוב ---
st.set_page_config(page_title="דני - ניהול שיחות", layout="wide")
st.markdown("""
<style>
    .chat-box { height: 500px; overflow-y: auto; padding: 15px; background: #f9f9f9; border-radius: 15px; border: 1px solid #ddd; display: flex; flex-direction: column; gap: 10px; }
    .msg { padding: 12px; border-radius: 15px; max-width: 80%; }
    .user { align-self: flex-end; background: #e1ffc7; border: 1px solid #b7e68d; }
    .ai { align-self: flex-start; background: white; border: 1px solid #eee; }
</style>
""", unsafe_allow_html=True)

# --- סרגל צד (היסטוריה וניהול) ---
with st.sidebar:
    st.title("🤖 דני - צ'אטים")
    
    if st.button("➕ צ'אט חדש", use_container_width=True):
        st.session_state.chat_id = f"chat_{datetime.now().strftime('%d%m_%H%M%S')}.json"
        st.rerun()
    
    st.divider()
    st.subheader("📁 שיחות שמורות")
    
    # טעינת רשימת הקבצים
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    files = requests.get(REPO_API, headers=headers).json()
    chat_files = [f for f in files if isinstance(f, dict) and f['name'].startswith("chat_")]

    for f in sorted(chat_files, key=lambda x: x['name'], reverse=True):
        col_chat, col_del = st.columns([4, 1])
        name = f['name'].replace(".json", "").replace("chat_", "")
        
        if col_chat.button(f"💬 {name}", key=f['name'], use_container_width=True):
            st.session_state.chat_id = f['name']
            st.rerun()
        
        if col_del.button("🗑️", key=f"del_{f['name']}"):
            github_action(f['name'], "DELETE", sha=f['sha'])
            st.rerun()

# --- תוכן ראשי ---
active_chat = st.session_state.get("chat_id", "chat_main.json")
st.title(f"שיחה: {active_chat.replace('.json', '')}")

history, sha = github_action(active_chat)

st.markdown('<div class="chat-box">', unsafe_allow_html=True)
for m in history:
    st.markdown(f'<div class="msg user"><b>אתה:</b><br>{m.get("user")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="msg ai"><b>דני:</b><br>{m.get("ai")}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

def send():
    p = st.session_state.inp
    if p:
        with st.spinner("דני חושב..."):
            res = ask_dani(p)
            history.append({"user": p, "ai": res})
            github_action(active_chat, "PUT", history, sha)
            st.session_state.inp = ""

st.text_input("הקלד הודעה...", key="inp", on_change=send)
