import streamlit as st
import requests
import json
import base64
from datetime import datetime

# --- הגדרות ה"טיל" (המפתחות המעודכנים ביותר) ---
GEMINI_API_KEY = "AIzaSyDbGtzd4_Q6Vd346hh84A81ugtHGaWHHYo"
GITHUB_TOKEN = "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"
GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"

REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# --- עיצוב ממשק Master UI ---
st.set_page_config(page_title="AI Autonomous Admin", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    .skill-card { 
        background: white; padding: 20px; border-radius: 12px; 
        border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px; text-align: center;
    }
    .chat-bubble {
        background: white; padding: 20px; border-radius: 15px;
        border-right: 6px solid #3b82f6; margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .user-text { color: #64748b; font-size: 0.9rem; font-weight: 600; margin-bottom: 5px; }
    .ai-text { color: #1e293b; line-height: 1.6; background: #f1f5f9; padding: 12px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- פונקציות תקשורת ---

def github_request(path, method="GET", data=None, sha=None):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"{REPO_API}/{path}"
    try:
        if method == "GET":
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                content = base64.b64decode(r.json()['content']).decode('utf-8')
                return json.loads(content), r.json()['sha']
            return [], None
        elif method == "PUT":
            payload = {
                "message": f"AI Update {datetime.now().strftime('%H:%M')}",
                "content": base64.b64encode(json.dumps(data, indent=4).encode('utf-8')).decode('utf-8'),
                "sha": sha
            }
            r = requests.put(url, headers=headers, json=payload)
            return r.status_code in [200, 201]
    except: return [], None

def ask_gemini(prompt):
    try:
        payload = {"contents": [{"parts": [{"text": f"ענה בעברית קצרה: {prompt}"}]}]}
        r = requests.post(GEMINI_URL, json=payload, timeout=10)
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except: return "שגיאה בתקשורת עם ה-AI"

# --- ממשק משתמש ---

st.title("🧠 AI Master Control Center")

# סקילים
st.subheader("🛠️ סקילים פעילים")
skills, _ = github_request("skills.json")
if skills:
    cols = st.columns(3)
    for i, s in enumerate(skills):
        with cols[i % 3]:
            st.markdown(f'<div class="skill-card"><b>{s.get("name")}</b><br><small>{s.get("description")}</small></div>', unsafe_allow_html=True)

st.divider()

# צ'אט ופקודות
st.subheader("🤖 שלח פקודה לסוכן")
with st.container():
    col1, col2 = st.columns([5, 1])
    with col1:
        cmd = st.text_input("הזן פקודה (למשל: 'תזכור שאני המנהל')", key="main_cmd")
    with col2:
        st.write("##")
        if st.button("שגר", type="primary", use_container_width=True):
            if cmd:
                with st.spinner("מעבד..."):
                    answer = ask_gemini(cmd)
                    hist, sha = github_request("history.json")
                    hist.append({"time": datetime.now().strftime("%H:%M"), "user": cmd, "ai": answer})
                    if github_request("history.json", "PUT", hist, sha):
                        st.success("נשמר בזיכרון!")
                        st.rerun()

st.divider()

# היסטוריה
st.subheader("📜 זיכרון המערכת")
history, _ = github_request("history.json")
if history:
    for e in reversed(history):
        st.markdown(f"""<div class="chat-bubble">
            <div class="user-text">👤 {e.get('user')}</div>
            <div class="ai-text">{e.get('ai')}</div>
            <small style="color:gray">{e.get('time')}</small>
        </div>""", unsafe_allow_html=True)
