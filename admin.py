import streamlit as st
import google.generativeai as genai
import requests, json, base64
from datetime import datetime

# --- הגדרות וניקוי מפתחות ---
def get_key(name):
    return str(st.secrets.get(name, "")).strip().strip('"').strip("'")

GEMINI_KEY = get_key("GEMINI_KEY")
GITHUB_TOKEN = get_key("GITHUB_TOKEN")
REPO = "efi-source/my-skills-system"
BASE_URL = f"https://api.github.com/repos/{REPO}/contents"

# --- חיבור למוח (AI) ---
@st.cache_resource
def init_ai():
    if not GEMINI_KEY: return None
    genai.configure(api_key=GEMINI_KEY)
    # ניסיון טעינה של מודל יציב למניעת שגיאת 404
    for m in ['gemini-1.5-flash', 'gemini-pro']:
        try:
            model = genai.GenerativeModel(m)
            model.generate_content("hi")
            return model
        except: continue
    return None

danny_brain = init_ai()

# --- פונקציות עבודה מול GitHub ---
def github_api(path="", method="GET", data=None, sha=None):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        if method == "GET":
            r = requests.get(f"{BASE_URL}/{path}", headers=headers)
            if r.status_code == 200:
                if isinstance(r.json(), list): return r.json(), None # רשימת קבצים
                content = base64.b64decode(r.json()['content']).decode('utf-8')
                return json.loads(content), r.json()['sha']
            return None, None
        else: # PUT - שמירה
            payload = {"message": "Danny Auto Update", "content": base64.b64encode(json.dumps(data).encode()).decode(), "sha": sha}
            return requests.put(f"{BASE_URL}/{path}", headers=headers, json=payload)
    except: return None, None

# --- עיצוב הממשק ---
st.set_page_config(page_title="Danny AI - Master", layout="wide")

# סרגל צד אוטומטי
with st.sidebar:
    st.title("🤖 דני - שליטה")
    if danny_brain:
        st.success("✅ המוח מחובר")
    else:
        st.error("❌ המוח מנותק - בדוק מפתח")

    if st.button("➕ שיחה חדשה", use_container_width=True):
        st.session_state.chat_path = None
        st.rerun()

    st.divider()
    st.subheader("📂 שיחות וסקילים")
    
    # טעינה אוטומטית של כל הקבצים מה-Repository
    files, _ = github_api("")
    if files:
        for f in files:
            name = f['name']
            if name.startswith("chat_") or name.endswith(".json"):
                label = f"💬 {name.replace('chat_', '').replace('.json', '')}"
                if st.button(label, key=name, use_container_width=True):
                    st.session_state.chat_path = name
                    st.rerun()

# --- חלון הצ'אט ---
active_chat = st.session_state.get("chat_path")
st.title(f"📺 צ'אט: {active_chat or 'חדש'}")

# טעינת תוכן השיחה
chat_data, current_sha = github_api(active_chat) if active_chat else ([], None)
if not isinstance(chat_data, list): chat_data = []

# הצגת ההיסטוריה
for msg in chat_data:
    with st.chat_message("user"): st.write(msg["u"])
    with st.chat_message("assistant"): st.write(msg["a"])

# קלט ושליחה
if prompt := st.chat_input("דבר עם דני..."):
    if danny_brain:
        with st.spinner("דני כותב..."):
            try:
                # יצירת תשובה
                response = danny_brain.generate_content(prompt).text
                chat_data.append({"u": prompt, "a": response})
                
                # שמירה אוטומטית ל-GitHub
                file_to_save = active_chat or f"chat_{datetime.now().strftime('%H%M%S')}.json"
                github_api(file_to_save, "PUT", chat_data, current_sha)
                
                st.session_state.chat_path = file_to_save
                st.rerun()
            except Exception as e:
                st.error(f"שגיאה: {e}")
