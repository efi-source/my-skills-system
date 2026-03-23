import streamlit as st
import requests
import json
import base64
from datetime import datetime

# ניסיון טעינת הספרייה של גוגל
try:
    import google.generativeai as genai
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False

# --- הגדרות אבטחה ---
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"].strip()
    GEMINI_KEY = st.secrets["GEMINI_KEY"].strip()
    if HAS_GOOGLE:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("וודא שהמפתחות ב-Secrets מוגדרים נכון (GITHUB_TOKEN ו-GEMINI_KEY)")
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
    if not HAS_GOOGLE:
        return "שגיאה: ספריית google-generativeai לא מותקנת ב-requirements.txt"
    try:
        response = model.generate_content(f"שמך דני. ענה בעברית: {prompt}")
        return response.text
    except Exception as e:
        return f"שגיאת API: {e}"

# --- עיצוב הממשק ---
st.set_page_config(page_title="Danny AI - Workspace", layout="wide")
st.markdown("""
<style>
    .chat-container { height: 500px; overflow-y: auto; padding: 15px; background: #f7f9fc; border-radius: 15px; border: 1px solid #e6e9ef; display: flex; flex-direction: column; gap: 10px; }
    .bubble { padding: 12px; border-radius: 15px; max-width: 80%; line-height: 1.4; }
    .user-b { align-self: flex-end; background: #dcf8c6; border: 1px solid #c1e1a6; }
    .ai-b { align-self: flex-start; background: white; border: 1px solid #ddd; }
    .name { font-weight: bold; font-size: 0.75rem; color: #777; margin-bottom: 3px; display: block; }
</style>
""", unsafe_allow_html=True)

# --- סרגל צד: ניהול שיחות וסקילים ---
with st.sidebar:
    st.title("🤖 דני - ניהול")
    
    if st.button("➕ צ'אט חדש", use_container_width=True):
        st.session_state.current_chat = f"chat_{datetime.now().strftime('%d%m_%H%M%S')}.json"
        st.rerun()

    st.divider()
    st.subheader("📁 היסטוריית שיחות")
    files = github_get_files()
    chat_files = [f['name'] for f in files if f['name'].startswith("chat_") and f['name'].endswith(".json")]
    
    for cf in sorted(chat_files, reverse=True):
        display_name = cf.replace("chat_", "").replace(".json", "")
        if st.button(f"💬 {display_name}", use_container_width=True):
            st.session_state.current_chat = cf
            st.rerun()

    st.divider()
    st.subheader("⚡ סקילים")
    skills, _ = github_action("skills.json")
    if skills:
        for s in skills:
            if st.button(f"🚀 {s.get('name')}", use_container_width=True):
                st.session_state.run_skill = s.get('name')

# --- תוכן ראשי ---
current_file = st.session_state.get("current_chat", "chat_main.json")
st.title(f"שיחה פעילה: {current_file.replace('.json', '')}")

if not HAS_GOOGLE:
    st.warning("שים לב: המערכת ממתינה להתקנת google-generativeai ב-requirements.txt")

history, sha = github_action(current_file)

# תצוגת בועות הצ'אט
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for m in history:
    st.markdown(f'<div class="bubble user-b"><span class="name">👤 אתה</span>{m.get("user")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="bubble ai-b"><span class="name">🤖 דני</span>{m.get("ai")}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# פונקציית שליחה
def handle_msg():
    user_txt = st.session_state.msg_input
    if user_txt:
        with st.spinner("דני כותב..."):
            ans = ask_dani(user_txt)
            history.append({"user": user_txt, "ai": ans})
            github_action(current_file, "PUT", history, sha)
            st.session_state.msg_input = ""

st.text_input("דבר עם דני...", key="msg_input", on_change=handle_msg)

# הפעלת סקיל
if "run_skill" in st.session_state:
    sk_name = st.session_state.pop("run_skill")
    ans = ask_dani(f"הפעל את הסקיל: {sk_name}")
    history.append({"user": f"הפעלה: {sk_name}", "ai": ans})
    github_action(current_file, "PUT", history, sha)
    st.rerun()
