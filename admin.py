import streamlit as st
import google.generativeai as genai
import requests, json, base64
from datetime import datetime

# --- 1. ניקוי וטעינת מפתחות (חובה למניעת שגיאות 400) ---
def get_clean_key(name):
    # שולף מה-Secrets ומנקה רווחים או גרשיים מיותרים
    val = st.secrets.get(name, "")
    return str(val).strip().strip('"').strip("'")

GEMINI_KEY = get_clean_key("GEMINI_KEY")
GITHUB_TOKEN = get_clean_key("GITHUB_TOKEN")

# --- 2. מנגנון בחירת מודל חכם (מתאים ל-Gemini 1.5/2.0 וכו') ---
@st.cache_resource
def load_ai_engine():
    if not GEMINI_KEY: 
        return None, "המפתח חסר ב-Secrets!"
    
    genai.configure(api_key=GEMINI_KEY)
    
    # רשימת מודלים לניסיון - מהחדש ביותר ליציב
    # הערה: אם גוגל תשחרר את 2.5, הוא יתווסף כאן ראשון
    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
    
    for m_name in models_to_try:
        try:
            m = genai.GenerativeModel(m_name)
            m.generate_content("ping") # בדיקת תקשורת
            return m, m_name
        except:
            continue
    return None, "שגיאת תקשורת: המודלים לא מגיבים למפתח"

model, active_model_name = load_ai_engine()

# --- 3. הגדרות GitHub (לשמירת שיחות) ---
REPO = "efi-source/my-skills-system"
URL = f"https://api.github.com/repos/{REPO}/contents"

def github_sync(path, method="GET", data=None, sha=None):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        if method == "GET":
            r = requests.get(f"{URL}/{path}", headers=headers)
            if r.status_code == 200:
                content = base64.b64decode(r.json()['content']).decode('utf-8')
                return json.loads(content), r.json()['sha']
            return [], None
        else: # PUT (שמירה)
            payload = {
                "message": "Update from Admin",
                "content": base64.b64encode(json.dumps(data, indent=2).encode()).decode(),
                "sha": sha
            }
            return requests.put(f"{URL}/{path}", headers=headers, json=payload).status_code in [200, 201]
    except: return [], None

# --- 4. ממשק המשתמש (UI) ---
st.set_page_config(page_title="דני - מערכת ניהול", layout="wide")

# סרגל צד לסטטוס
with st.sidebar:
    st.title("🤖 סטטוס דני")
    if model:
        st.success(f"מחובר למודל: {active_model_name}")
    else:
        st.error(active_model_name)
    
    if st.button("➕ צ'אט חדש", use_container_width=True):
        st.session_state.active_chat = None
        st.rerun()
    
    st.divider()
    st.subheader("📁 שיחות שמורות")
    # טעינת רשימת קבצים מ-GitHub
    files_res = requests.get(URL, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    if files_res.status_code == 200:
        for f in [x for x in files_res.json() if x['name'].startswith("chat_")]:
            if st.button(f"💬 {f['name'][5:-5]}", key=f['name'], use_container_width=True):
                st.session_state.active_chat = f['name']
                st.rerun()

# --- 5. גוף הצ'אט ---
st.title(f"📺 שיחה נוכחית: {st.session_state.get('active_chat', 'חדשה')}")

active_file = st.session_state.get("active_chat")
history, current_sha = github_sync(active_file) if active_file else ([], None)

# הצגת היסטוריה בבועות
for m in history:
    with st.chat_message("user"): st.write(m["u"])
    with st.chat_message("assistant"): st.write(m["a"])

# קלט מהמשתמש
if prompt := st.chat_input("דבר עם דני..."):
    if not model:
        st.error("לא ניתן לשלוח הודעה - ה-AI לא מחובר.")
    else:
        with st.spinner("דני חושב..."):
            try:
                # יצירת תשובה
                response = model.generate_content(prompt).text
                history.append({"u": prompt, "a": response})
                
                # יצירת שם קובץ ושמירה לגיטהאב
                fname = active_file or f"chat_{datetime.now().strftime('%H%M%S')}.json"
                github_sync(fname, "PUT", history, current_sha)
                
                st.session_state.active_chat = fname
                st.rerun()
            except Exception as e:
                st.error(f"תקלה בייצור תשובה: {e}")
