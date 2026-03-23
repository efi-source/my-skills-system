import streamlit as st
import google.generativeai as genai
import requests
import json
import base64
from datetime import datetime

# --- 1. הגדרות וחיבורים (כולל ניקוי כפוי של תווים) ---
def get_secret(key_name):
    """שליפת מפתח וניקוי יסודי של גרשיים ורווחים"""
    try:
        raw_key = st.secrets[key_name]
        return raw_key.strip().replace('"', '').replace("'", "")
    except:
        return None

GEMINI_KEY = get_secret("GEMINI_KEY")
GITHUB_TOKEN = get_secret("GITHUB_TOKEN")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Missing GEMINI_KEY in Secrets!")
    st.stop()

GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"
REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"

# --- 2. פונקציות עזר (GitHub) ---
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
        return requests.delete(url, headers=headers, json={"message": "Delete chat", "sha": sha}).status_code == 200
    else: # PUT
        payload = {
            "message": "Chat Update",
            "content": base64.b64encode(json.dumps(data, indent=4).encode()).decode(),
            "sha": sha
        }
        return requests.put(url, headers=headers, json=payload).status_code in [200, 201]

def generate_chat_name(text):
    try:
        res = model.generate_content(f"תן שם קצר (2-3 מילים) בעברית לנושא הבא: {text}. ענה רק את השם.")
        return res.text.strip().replace(" ", "_")[:20]
    except:
        return datetime.now().strftime("%H%M%S")

# --- 3. עיצוב הממשק ---
st.set_page_config(page_title="דני AI - שליטה מלאה", layout="wide")
st.markdown("""
<style>
    .chat-card { background: white; padding: 20px; border-radius: 15px; border: 1px solid #ddd; height: 500px; overflow-y: auto; margin-bottom: 20px; }
    .user-msg { background: #e1ffc7; padding: 10px; border-radius: 10px; margin: 5px 0; text-align: right; }
    .ai-msg { background: #f0f2f6; padding: 10px; border-radius: 10px; margin: 5px 0; }
</style>
""", unsafe_allow_html=True)

# --- 4. סרגל צד (ניהול) ---
with st.sidebar:
    st.title("🤖 דני - שליטה")
    if st.button("➕ צ'אט חדש", use_container_width=True):
        st.session_state.active_chat = None
        st.rerun()
    
    st.divider()
    st.subheader("📁 שיחות שמורות")
    files_req = requests.get(REPO_API, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    if files_req.status_code == 200:
        for f in [x for x in files_req.json() if x['name'].startswith("chat_")]:
            col1, col2 = st.columns([4, 1])
            name = f['name'].replace("chat_", "").replace(".json", "").replace("_", " ")
            if col1.button(f"💬 {name}", key=f['name'], use_container_width=True):
                st.session_state.active_chat = f['name']
                st.rerun()
            if col2.button("🗑️", key=f"del_{f['name']}"):
                github_action(f['name'], "DELETE", sha=f['sha'])
                st.rerun()

# --- 5. הצ'אט ---
active_file = st.session_state.get("active_chat")
history, current_sha = github_action(active_file) if active_file else ([], None)

st.title(f"📺 שיחה: {active_file or 'חדשה'}")

# תצוגת היסטוריה
with st.container():
    st.markdown('<div class="chat-card">', unsafe_allow_html=True)
    for m in history:
        st.markdown(f'<div class="user-msg"><b>אתה:</b> {m["user"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ai-msg"><b>דני:</b> {m["ai"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# שליחת הודעה
def on_send():
    msg = st.session_state.user_input
    if msg:
        try:
            with st.spinner("דני חושב..."):
                response = model.generate_content(f"ענה בעברית: {msg}")
                ans = response.text
                history.append({"user": msg, "ai": ans})
                
                fname = active_file or f"chat_{generate_chat_name(msg)}.json"
                github_action(fname, "PUT", history, current_sha)
                st.session_state.active_chat = fname
                st.session_state.user_input = ""
        except Exception as e:
            st.error(f"שגיאה: {e}")

st.text_input("דבר עם דני...", key="user_input", on_change=on_send)
