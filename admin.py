import streamlit as st
import google.generativeai as genai
import requests, json, base64
from datetime import datetime

# --- הגדרות ---
def get_config(name):
    return str(st.secrets.get(name, "")).strip().strip('"').strip("'")

GEMINI_KEY = get_config("GEMINI_KEY")
GITHUB_TOKEN = get_config("GITHUB_TOKEN")
REPO = "efi-source/my-skills-system"
API_URL = f"https://api.github.com/repos/{REPO}/contents"

# --- חיבור ל-AI (Gemini 1.5 Flash) ---
@st.cache_resource
def load_danny():
    if not GEMINI_KEY: return None
    try:
        genai.configure(api_key=GEMINI_KEY)
        # ניסיון טעינה של המודל הכי עדכני
        model = genai.GenerativeModel('gemini-1.5-flash')
        model.generate_content("test")
        return model
    except:
        return None

danny = load_danny()

# --- עבודה מול GitHub ---
def github_call(path="", method="GET", data=None, sha=None):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"{API_URL}/{path}"
    try:
        if method == "GET":
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                if isinstance(r.json(), list): return r.json(), None
                content = base64.b64decode(r.json()['content']).decode('utf-8')
                return json.loads(content), r.json()['sha']
        else:
            payload = {"message": "Danny Auto-Sync", "content": base64.b64encode(json.dumps(data).encode()).decode(), "sha": sha}
            return requests.put(url, headers=headers, json=payload).status_code in [200, 201]
    except: pass
    return None, None

# --- ממשק ---
st.set_page_config(page_title="Danny AI Master", layout="wide")

with st.sidebar:
    st.title("🤖 סטטוס דני")
    if danny: st.success("✅ המוח מחובר ומוכן!")
    else: st.error("❌ המוח מנותק - בדוק מפתח ב-Secrets")
    
    if st.button("➕ צ'אט חדש", use_container_width=True):
        st.session_state.active_file = None
        st.rerun()

    st.divider()
    st.subheader("📁 שיחות וסקילים (אוטומטי)")
    # משיכה אוטומטית של כל הקבצים
    files, _ = github_call("")
    if files:
        for f in files:
            if f['name'].endswith(".json"):
                label = f"📄 {f['name'].replace('.json', '').replace('chat_', '')}"
                if st.button(label, key=f['name'], use_container_width=True):
                    st.session_state.active_file = f['name']
                    st.rerun()

# --- גוף הצ'אט ---
active_f = st.session_state.get("active_file")
st.title(f"📺 שיחה פעילה: {active_f or 'חדשה'}")

history, current_sha = github_call(active_f) if active_f else ([], None)
if not isinstance(history, list): history = []

for m in history:
    with st.chat_message("user"): st.write(m["u"])
    with st.chat_message("assistant"): st.write(m["a"])

if p := st.chat_input("דבר עם דני..."):
    if danny:
        with st.spinner("דני חושב..."):
            res = danny.generate_content(p).text
            history.append({"u": p, "a": res})
            fname = active_f or f"chat_{datetime.now().strftime('%H%M%S')}.json"
            github_call(fname, "PUT", history, current_sha)
            st.session_state.active_file = fname
            st.rerun()
