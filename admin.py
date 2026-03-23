import streamlit as st
import google.generativeai as genai
import requests, json, base64
from datetime import datetime

# --- הגדרת כתובת ה-Pipedream שלך ---
# שים כאן את הכתובת שקיבלת מהטריגר ב-Pipedream
PIPEDREAM_KEYS_URL = "https://eox6msqotx1b.m.pipedream.net" 

@st.cache_data(ttl=600) # מרענן את המפתחות כל 10 דקות
def fetch_remote_keys():
    try:
        r = requests.get(PIPEDREAM_KEYS_URL)
        if r.status_code == 200:
            return r.json() # מחזיר dict עם GEMINI_KEY ו-GITHUB_TOKEN
    except:
        # גיבוי מה-Secrets אם Pipedream לא זמין
        return {
            "GEMINI_KEY": st.secrets.get("GEMINI_KEY", ""),
            "GITHUB_TOKEN": st.secrets.get("GITHUB_TOKEN", "")
        }
    return {}

keys = fetch_remote_keys()
G_KEY = str(keys.get("GEMINI_KEY", "")).strip()
G_TOKEN = str(keys.get("GITHUB_TOKEN", "")).strip()

# --- חיבור ל-AI (עם מנגנון סריקה אוטומטי) ---
@st.cache_resource
def get_brain():
    if not G_KEY: return None, "חסר מפתח GEMINI"
    genai.configure(api_key=G_KEY)
    # ניסיון טעינת מודלים לפי סדר
    for model_name in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']:
        try:
            m = genai.GenerativeModel(model_name)
            m.generate_content("hi")
            return m, model_name
        except: continue
    return None, "לא נמצא מודל תואם למפתח"

model, active_model = get_brain()

# --- הגדרות GitHub (סנכרון אוטומטי) ---
REPO = "efi-source/my-skills-system"
API_URL = f"https://api.github.com/repos/{REPO}/contents"

def github_io(path="", method="GET", data=None, sha=None):
    headers = {"Authorization": f"token {G_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        if method == "GET":
            r = requests.get(f"{API_URL}/{path}", headers=headers)
            if r.status_code == 200:
                if isinstance(r.json(), list): return r.json(), None
                return json.loads(base64.b64decode(r.json()['content']).decode()), r.json()['sha']
        else: # PUT
            payload = {"message": "Update", "content": base64.b64encode(json.dumps(data).encode()).decode(), "sha": sha}
            return requests.put(f"{API_URL}/{path}", headers=headers, json=payload)
    except: return None, None

# --- ממשק דני ---
st.set_page_config(page_title="Danny Remote Master", layout="wide")

with st.sidebar:
    st.title("🤖 דני - שליטה מרחוק")
    if model: st.success(f"מחובר דרך Pipedream ל-{active_model}")
    else: st.error(f"תקלה: {active_model}")
    
    if st.button("➕ צ'אט חדש", use_container_width=True):
        st.session_state.chat_id = None
        st.rerun()

    st.divider()
    st.subheader("📁 קבצים ב-GitHub")
    files, _ = github_io("")
    if files:
        for f in [x for x in files if x['name'].endswith(".json")]:
            if st.button(f"💬 {f['name']}", use_container_width=True):
                st.session_state.chat_id = f['name']
                st.rerun()

# --- צ'אט ---
chat_file = st.session_state.get("chat_id")
history, current_sha = github_io(chat_file) if chat_file else ([], None)

st.title(f"📺 שיחה: {chat_file or 'חדשה'}")

for m in (history if isinstance(history, list) else []):
    with st.chat_message("user"): st.write(m["u"])
    with st.chat_message("assistant"): st.write(m["a"])

if p := st.chat_input("דבר עם דני..."):
    if model:
        with st.spinner("מעבד..."):
            res = model.generate_content(p).text
            history.append({"u": p, "a": res})
            fname = chat_file or f"chat_{datetime.now().strftime('%H%M%S')}.json"
            github_io(fname, "PUT", history, current_sha)
            st.session_state.chat_id = fname
            st.rerun()
