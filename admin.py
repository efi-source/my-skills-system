import streamlit as st
import google.generativeai as genai
import requests
import json
import base64
from datetime import datetime

# --- אבטחה וחיבור ---
try:
    # פונקציית strip() מנקה רווחים מיותרים מהקצוות אוטומטית
    GEMINI_KEY = st.secrets["GEMINI_KEY"].strip()
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"].strip()
    
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"שגיאה בהגדרות: {e}")
    st.stop()

GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"
REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"

# --- פונקציות עזר ---
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
        payload = {"message": "Update chat", "content": base64.b64encode(json.dumps(data, indent=4).encode()).decode(), "sha": sha}
        return requests.put(url, headers=headers, json=payload).status_code in [200, 201]

def ask_dani(prompt):
    try:
        # הנחיית מערכת כדי שדני ידע מי הוא
        response = model.generate_content(f"אתה דני, סוכן AI. ענה בעברית קצרה ולעניין: {prompt}")
        return response.text
    except Exception as e:
        return f"שגיאת API (תבדוק את המפתח): {str(e)[:100]}"

# --- עיצוב ממשק ---
st.set_page_config(page_title="Danny AI", layout="wide")
st.markdown("""
<style>
    .chat-container { height: 500px; overflow-y: auto; padding: 20px; background: #ffffff; border-radius: 15px; border: 1px solid #ddd; display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
    .bubble { padding: 12px 16px; border-radius: 18px; max-width: 75%; font-size: 1rem; position: relative; }
    .user { align-self: flex-end; background: #e1ffc7; border: 1px solid #b7e68d; text-align: right; }
    .ai { align-self: flex-start; background: #f1f1f1; border: 1px solid #ddd; text-align: left; }
    .header-tag { font-weight: bold; font-size: 0.75rem; margin-bottom: 5px; display: block; color: #555; }
</style>
""", unsafe_allow_html=True)

# --- סרגל צד: היסטוריה וסקילים ---
with st.sidebar:
    st.title("🤖 דני - ניהול")
    if st.button("➕ צ'אט חדש", use_container_width=True):
        st.session_state.current_chat = f"chat_{datetime.now().strftime('%H%M%S')}.json"
        st.rerun()

    st.divider()
    st.subheader("📁 היסטוריית שיחות")
    files = github_get_files()
    chat_files = [f['name'] for f in files if f['name'].startswith("chat_") and f['name'].endswith(".json")]
    for cf in sorted(chat_files, reverse=True):
        if st.button(f"💬 {cf}", use_container_width=True):
            st.session_state.current_chat = cf
            st.rerun()

# --- גוף העמוד ---
current_file = st.session_state.get("current_chat", "chat_main.json")
st.title(f"שיחה: {current_file.replace('.json', '')}")

history, sha = github_action(current_file)

# הצגת הצ'אט
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for m in history:
    st.markdown(f'<div class="bubble user"><span class="header-tag">👤 אתה</span>{m.get("user")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="bubble ai"><span class="header-tag">🤖 דני</span>{m.get("ai")}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# שליחת הודעה
def handle_send():
    txt = st.session_state.user_input
    if txt:
        with st.spinner("דני חושב..."):
            ans = ask_dani(txt)
            history.append({"user": txt, "ai": ans})
            github_action(current_file, "PUT", history, sha)
            st.session_state.user_input = ""

st.text_input("דבר עם דני...", key="user_input", on_change=handle_send)
