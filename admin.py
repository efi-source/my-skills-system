import streamlit as st
import google.generativeai as genai
import requests, json, base64
from datetime import datetime

# --- הגדרות בסיסיות מ-Secrets ---
# ניקוי המפתחות מרווחים מיותרים כפי שראינו בתמונות
G_KEY = str(st.secrets.get("GEMINI_KEY", "")).strip().replace('"', '').replace("'", "")
G_TOKEN = str(st.secrets.get("GITHUB_TOKEN", "")).strip().replace('"', '').replace("'", "")

# --- חיבור ל-AI (Gemini 1.5 Flash) ---
def get_ai():
    try:
        genai.configure(api_key=G_KEY)
        # נצמד למודל ה-Flash שהוא המהיר והיציב ביותר כרגע
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"שגיאת חיבור ל-AI: {e}")
        return None

ai_model = get_ai()

# --- פונקציות GitHub (לניהול הזיכרון של דני) ---
REPO = "efi-source/my-skills-system"
GITHUB_URL = f"https://api.github.com/repos/{REPO}/contents"

def github_file_action(path, method="GET", data=None, sha=None):
    headers = {"Authorization": f"token {G_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    if method == "GET":
        r = requests.get(f"{GITHUB_URL}/{path}", headers=headers)
        if r.status_code == 200:
            content = base64.b64decode(r.json()['content']).decode('utf-8')
            return json.loads(content), r.json()['sha']
        return [], None
    else: # שמירה (PUT)
        payload = {
            "message": "Danny Update",
            "content": base64.b64encode(json.dumps(data).encode()).decode(),
            "sha": sha
        }
        return requests.put(f"{GITHUB_URL}/{path}", headers=headers, json=payload)

# --- ממשק משתמש (UI) ---
st.set_page_config(page_title="דני AI - ניהול", layout="wide")

# סרגל צד לסטטוס והיסטוריה
with st.sidebar:
    st.title("🤖 דני - שליטה")
    if ai_model:
        st.success("✅ המוח של דני מחובר")
    else:
        st.error("❌ תקלה בחיבור המוח")
    
    if st.button("➕ שיחה חדשה"):
        st.session_state.active_chat = None
        st.rerun()

    st.divider()
    st.subheader("📂 שיחות קודמות")
    # הצגת קבצי השיחות הקיימים
    res = requests.get(GITHUB_URL, headers={"Authorization": f"token {G_TOKEN}"})
    if res.status_code == 200:
        for file in [f for f in res.json() if f['name'].startswith("chat_")]:
            if st.button(f"💬 {file['name'][5:-5]}", key=file['name']):
                st.session_state.active_chat = file['name']
                st.rerun()

# --- חלון הצ'אט המרכזי ---
active_chat = st.session_state.get("active_chat")
history, current_sha = github_file_action(active_chat) if active_chat else ([], None)

st.title(f"📺 צ'אט: {active_chat or 'חדש'}")

# הצגת ההודעות (בועות)
for msg in history:
    with st.chat_message("user"): st.write(msg["u"])
    with st.chat_message("assistant"): st.write(msg["a"])

# קלט מהמשתמש
if user_input := st.chat_input("דבר עם דני..."):
    if ai_model:
        with st.spinner("דני חושב..."):
            try:
                # יצירת התשובה מה-AI
                ai_res = ai_model.generate_content(user_input).text
                history.append({"u": user_input, "a": ai_res})
                
                # שמירה ל-GitHub (בדיוק כמו ב-Workflow של Pipedream)
                filename = active_chat or f"chat_{datetime.now().strftime('%H%M%S')}.json"
                github_file_action(filename, "PUT", history, current_sha)
                
                st.session_state.active_chat = filename
                st.rerun()
            except Exception as e:
                st.error(f"תקלה: {e}")
