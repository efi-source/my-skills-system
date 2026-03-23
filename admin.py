import streamlit as st
import google.generativeai as genai
import requests
import json
import base64
from datetime import datetime

# --- 1. הגדרות וחיבורים (חסין שגיאות) ---
try:
    # ניקוי תווים מיותרים מהמפתחות ליתר ביטחון
    GEMINI_KEY = st.secrets["GEMINI_KEY"].strip().replace('"', '')
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"].strip().replace('"', '')
    
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"שגיאת קונפיגורציה: {e}. וודא שה-Secrets מוגדרים נכון.")
    st.stop()

GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"
REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"

# --- 2. פונקציות ליבה (GitHub & AI) ---
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
            "message": "Update from Admin",
            "content": base64.b64encode(json.dumps(data, indent=4).encode()).decode(),
            "sha": sha
        }
        return requests.put(url, headers=headers, json=payload).status_code in [200, 201]

def generate_chat_name(first_msg):
    try:
        res = model.generate_content(f"תן שם של 2-3 מילים בעברית לשיחה שמתחילה ב: {first_msg}. ענה רק את השם.")
        return res.text.strip().replace(" ", "_")[:20]
    except:
        return datetime.now().strftime("%d%m_%H%M")

# --- 3. עיצוב הממשק (CSS) ---
st.set_page_config(page_title="Danny AI Master Admin", layout="wide")
st.markdown("""
<style>
    .main { background-color: #f5f7f9; }
    .chat-container { height: 550px; overflow-y: auto; padding: 20px; background: white; border-radius: 15px; border: 1px solid #e0e0e0; margin-bottom: 20px; }
    .stTextInput>div>div>input { border-radius: 10px; padding: 15px; }
    .user-msg { background: #dcf8c6; padding: 10px 15px; border-radius: 15px; margin-bottom: 10px; align-self: flex-end; border: 1px solid #c1e1a6; }
    .ai-msg { background: #ffffff; padding: 10px 15px; border-radius: 15px; margin-bottom: 10px; align-self: flex-start; border: 1px solid #ddd; }
    .sidebar-btn { margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 4. סרגל צד (ניהול שיחות וסקילים) ---
with st.sidebar:
    st.title("🤖 דני - שליטה")
    if st.button("➕ צ'אט חדש", use_container_width=True):
        st.session_state.active_chat = None
        st.rerun()
    
    st.divider()
    st.subheader("📂 שיחות שמורות")
    
    # טעינת רשימת קבצים מהמאגר
    files_req = requests.get(REPO_API, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    if files_req.status_code == 200:
        chats = [f for f in files_req.json() if isinstance(f, dict) and f['name'].startswith("chat_")]
        for c in sorted(chats, key=lambda x: x['name'], reverse=True):
            col_name, col_del = st.columns([4, 1])
            display_name = c['name'].replace("chat_", "").replace(".json", "").replace("_", " ")
            if col_name.button(f"💬 {display_name}", key=c['name'], use_container_width=True):
                st.session_state.active_chat = c['name']
                st.rerun()
            if col_del.button("🗑️", key=f"del_{c['name']}"):
                github_action(c['name'], "DELETE", sha=c['sha'])
                st.session_state.active_chat = None
                st.rerun()

    st.divider()
    if st.button("🔄 רענן מערכת", use_container_width=True):
        st.rerun()

# --- 5. חלון הצ'אט הראשי ---
active_file = st.session_state.get("active_chat")
history, current_sha = github_action(active_file) if active_file else ([], None)

st.title(f"📺 צ'אט: {active_file.replace('chat_', '').replace('.json', '') if active_file else 'חדש'}")

# הצגת היסטוריה
chat_placeholder = st.container()
with chat_placeholder:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for m in history:
        st.markdown(f'<div class="user-msg"><b>👤 אתה:</b><br>{m["user"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ai-msg"><b>🤖 דני:</b><br>{m["ai"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# פונקציית שליחה
def handle_input():
    user_input = st.session_state.user_input
    if user_input:
        with st.spinner("דני מעבד נתונים..."):
            try:
                # קבלת תשובה מה-AI
                response = model.generate_content(f"שמך דני. ענה בעברית: {user_input}")
                ai_response = response.text
                
                # עדכון היסטוריה
                history.append({"user": user_input, "ai": ai_response})
                
                # קביעת שם קובץ (אם זה צ'אט חדש)
                target_file = active_file
                if not target_file:
                    new_name = generate_chat_name(user_input)
                    target_file = f"chat_{new_name}.json"
                    st.session_state.active_chat = target_file
                
                # שמירה ל-GitHub
                github_action(target_file, "PUT", history, current_sha)
                st.session_state.user_input = "" # איפוס התיבה
            except Exception as e:
                st.error(f"שגיאה בתקשורת עם ה-AI: {e}")

st.text_input("הקלד הודעה לדני...", key="user_input", on_change=handle_input)
