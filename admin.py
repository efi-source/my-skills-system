import streamlit as st
import requests
import json
import base64
from datetime import datetime

# --- הגדרות מערכת (המפתחות המעודכנים שלך) ---
GEMINI_API_KEY = "AIzaSyDbGtzd4_Q6Vd346hh84A81ugtHGaWHHYo"
GITHUB_TOKEN = "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"
GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"

# נתיבי API
REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# --- עיצוב ממשק Master UI ---
st.set_page_config(page_title="AI Master Control", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    .main-title { color: #1e293b; text-align: center; font-weight: 800; margin-bottom: 20px; }
    .skill-card { 
        background: white; padding: 15px; border-radius: 12px; 
        border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px; text-align: center;
    }
    .chat-bubble {
        background: white; padding: 20px; border-radius: 15px;
        border-right: 6px solid #3b82f6; margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .user-label { color: #64748b; font-size: 0.8rem; font-weight: bold; }
    .ai-response { color: #1e293b; background: #f1f5f9; padding: 10px; border-radius: 8px; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# --- פונקציות תקשורת ---

def github_action(path, method="GET", data=None, sha=None):
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
                "message": "System Sync",
                "content": base64.b64encode(json.dumps(data, indent=4).encode('utf-8')).decode('utf-8'),
                "sha": sha
            }
            r = requests.put(url, headers=headers, json=payload)
            return r.status_code in [200, 201]
    except: return [], None

def ask_gemini(prompt):
    try:
        payload = {"contents": [{"parts": [{"text": f"ענה בעברית קצרה ומקצועית: {prompt}"}]}]}
        r = requests.post(GEMINI_URL, json=payload, timeout=10)
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except: return "שגיאה בתקשורת עם ה-AI"

# --- גוף האפליקציה ---

st.markdown('<h1 class="main-title">🧠 AI Autonomous Command Center</h1>', unsafe_allow_html=True)

# כפתור בדיקה בסידבר
with st.sidebar:
    st.header("⚙️ הגדרות")
    if st.button("🔄 רענן מערכת"):
        st.rerun()
    if st.button("🔍 בדיקת חיבור"):
        _, sha = github_action("history.json")
        if sha: st.success("מחובר לגיטהאב!")
        else: st.error("שגיאת חיבור - בדוק את הטוקן")

# תצוגת סקילים
st.subheader("🛠️ סקילים פעילים")
skills, _ = github_action("skills.json")
if skills:
    cols = st.columns(3)
    for i, s in enumerate(skills):
        with cols[i % 3]:
            st.markdown(f'<div class="skill-card"><b>{s.get("name")}</b><br><small>{s.get("description")}</small></div>', unsafe_allow_html=True)

st.divider()

# מרכז פקודות
st.subheader("🤖 מרכז פקודות וניהול")
col_input, col_send = st.columns([4, 1])
with col_input:
    user_cmd = st.text_input("הזן פקודה חדשה:", placeholder="למשל: תזכור ששמי אפי", key="input")
with col_send:
    st.write("##")
    if st.button("שגר פקודה", type="primary", use_container_width=True):
        if user_cmd:
            with st.spinner("מעבד ושומר..."):
                answer = ask_gemini(user_cmd)
                hist, sha = github_action("history.json")
                hist.append({"time": datetime.now().strftime("%H:%M"), "user": user_cmd, "ai": answer})
                if github_action("history.json", "PUT", hist, sha):
                    st.success("נשמר בזיכרון!")
                    st.rerun()

st.divider()

# זיכרון היסטורי
st.subheader("📜 יומן פעולות (זיכרון)")
history, _ = github_action("history.json")
if history:
    for entry in reversed(history):
        st.markdown(f"""
        <div class="chat-bubble">
            <div class="user-label">👤 פקודה: {entry.get('user')}</div>
            <div class="ai-response">🤖 {entry.get('ai')}</div>
            <div style="font-size:0.7rem; color:#94a3b8; margin-top:10px;">🕒 {entry.get('time')}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("הזיכרון ריק כרגע. שלח פקודה כדי להתחיל.")
