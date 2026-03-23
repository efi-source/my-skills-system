import streamlit as st
import google.generativeai as genai
import requests, json, base64
from datetime import datetime

# --- ניקוי מפתחות ---
G_KEY = str(st.secrets.get("GEMINI_KEY", "")).strip().replace('"', '').replace("'", "")
G_TOKEN = str(st.secrets.get("GITHUB_TOKEN", "")).strip().replace('"', '').replace("'", "")

# --- מנגנון בחירת מודל יצירתי ---
def get_working_model():
    # רשימת מודלים מהחדש לישן
    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
    genai.configure(api_key=G_KEY)
    
    for m_name in models_to_try:
        try:
            m = genai.GenerativeModel(m_name)
            m.generate_content("hi") # בדיקת דופק
            return m, m_name
        except:
            continue
    return None, None

model, model_name = get_working_model()

# --- הגדרות GitHub ---
REPO = "efi-source/my-skills-system"
URL = f"https://api.github.com/repos/{REPO}/contents"

def github_io(path, method="GET", data=None, sha=None):
    headers = {"Authorization": f"token {G_TOKEN}"}
    if method == "GET":
        r = requests.get(f"{URL}/{path}", headers=headers)
        if r.status_code == 200:
            return json.loads(base64.b64decode(r.json()['content']).decode()), r.json()['sha']
        return [], None
    else: # PUT
        payload = {"message": "update", "content": base64.b64encode(json.dumps(data).encode()).decode(), "sha": sha}
        return requests.put(f"{URL}/{path}", headers=headers, json=payload)

# --- ממשק ---
st.set_page_config(page_title="דני AI v2", layout="wide")

with st.sidebar:
    st.title("🤖 דני - מרכז שליטה")
    if model:
        st.success(f"מחובר למודל: {model_name}")
    else:
        st.error("לא נמצא מודל פעיל. בדוק את ה-API Key.")
    
    if st.button("➕ שיחה חדשה"):
        st.session_state.active = None
        st.rerun()

# --- ניהול שיחה ---
active_chat = st.session_state.get("active")
history, current_sha = github_io(active_chat) if active_chat else ([], None)

st.title(f"📺 צ'אט: {active_chat or 'חדש'}")

for m in history:
    with st.chat_message("user"): st.write(m["u"])
    with st.chat_message("assistant"): st.write(m["a"])

if prompt := st.chat_input("דבר עם דני..."):
    if model:
        with st.spinner("חושב..."):
            try:
                res = model.generate_content(prompt).text
                history.append({"u": prompt, "a": res})
                fname = active_chat or f"chat_{datetime.now().strftime('%H%M%S')}.json"
                github_io(fname, "PUT", history, current_sha)
                st.session_state.active = fname
                st.rerun()
            except Exception as e:
                st.error(f"שגיאה: {e}")
