import streamlit as st
import google.generativeai as genai
import requests, json, base64
from datetime import datetime

# --- 1. שליפה וניקוי מפתחות (חובה למניעת שגיאות 400) ---
def get_clean_key(name):
    val = st.secrets.get(name, "")
    return str(val).strip().strip('"').strip("'")

GEMINI_KEY = get_clean_key("GEMINI_KEY")
GITHUB_TOKEN = get_clean_key("GITHUB_TOKEN")

# --- 2. מנגנון בחירת מודל אוטונומי ---
@st.cache_resource
def load_ai():
    if not GEMINI_KEY: return None, "חסר מפתח GEMINI_KEY"
    genai.configure(api_key=GEMINI_KEY)
    # ניסיון התחברות לכל המודלים האפשריים לפי סדר
    for model_name in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']:
        try:
            m = genai.GenerativeModel(model_name)
            m.generate_content("Hi") # בדיקת דופק
            return m, model_name
        except: continue
    return None, "לא נמצא מודל תואם למפתח"

model, active_model = load_ai()

# --- 3. ממשק GitHub ---
REPO = "efi-source/my-skills-system"
URL = f"https://api.github.com/repos/{REPO}/contents"

def github_io(path, method="GET", data=None, sha=None):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        if method == "GET":
            r = requests.get(f"{URL}/{path}", headers=headers)
            if r.status_code == 200:
                return json.loads(base64.b64decode(r.json()['content']).decode()), r.json()['sha']
            return [], None
        else:
            payload = {"message": "Admin Update", "content": base64.b64encode(json.dumps(data).encode()).decode(), "sha": sha}
            return requests.put(f"{URL}/{path}", headers=headers, json=payload)
    except: return [], None

# --- 4. עיצוב הממשק ---
st.set_page_config(page_title="Danny Master Admin", layout="wide")
st.markdown("<style>.stChatMessage { border-radius: 15px; margin-bottom: 10px; }</style>", unsafe_allow_html=True)

with st.sidebar:
    st.title("⚙️ בקרה מרכזית")
    if model: st.success(f"דני פעיל בתוך: {active_model}")
    else: st.error(f"תקלה: {active_model}")
    
    if st.button("➕ צ'אט חדש", use_container_width=True):
        st.session_state.chat_id = None
        st.rerun()
    
    st.divider()
    st.subheader("📁 שיחות בגיטהאב")
    # רשימת קבצים
    res = requests.get(URL, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    if res.status_code == 200:
        for f in [x for x in res.json() if x['name'].startswith("chat_")]:
            if st.button(f"💬 {f['name'][5:-5]}", key=f['name'], use_container_width=True):
                st.session_state.chat_id = f['name']
                st.rerun()

# --- 5. לוגיקה של הצ'אט ---
chat_file = st.session_state.get("chat_id")
history, current_sha = github_io(chat_file) if chat_file else ([], None)

st.title(f"📺 שיחה: {chat_file or 'חדשה'}")

# תצוגת היסטוריה
for msg in history:
    with st.chat_message("user"): st.write(msg["u"])
    with st.chat_message("assistant"): st.write(msg["a"])

# קלט מהמשתמש
if prompt := st.chat_input("דבר עם דני..."):
    if model:
        with st.spinner("מעבד..."):
            try:
                response = model.generate_content(prompt).text
                history.append({"u": prompt, "a": response})
                
                # שמירה אוטומטית עם שם חכם
                new_name = chat_file or f"chat_{datetime.now().strftime('%H%M%S')}.json"
                github_io(new_name, "PUT", history, current_sha)
                
                st.session_state.chat_id = new_name
                st.rerun()
            except Exception as e: st.error(f"שגיאת AI: {e}")
