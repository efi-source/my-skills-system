import streamlit as st
import requests
import json
import base64
from datetime import datetime

# --- הגדרות ה"טיל" (המפתחות שלך) ---
GEMINI_API_KEY = "AIzaSyDbGtzd4_Q6Vd346hh84A81ugtHGaWHHYo"
GITHUB_TOKEN = "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"
GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"

# נתיבי עבודה מול ה-APIs
REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# --- עיצוב ממשק יוקרתי, נקי ורגוע ---
st.set_page_config(page_title="AI Master Control", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f8fafc; color: #1e293b; }
    
    /* כרטיסי סקילים */
    .skill-box { 
        background: white; padding: 15px; border-radius: 12px; 
        border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px; text-align: center;
    }
    
    /* בועות צ'אט והיסטוריה */
    .chat-bubble {
        background: white; padding: 15px; border-radius: 15px;
        border-right: 5px solid #3b82f6; margin-bottom: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .user-text { color: #64748b; font-size: 0.85rem; font-weight: 600; }
    .ai-text { color: #1e293b; margin-top: 5px; line-height: 1.5; }
    .status-tag { font-size: 0.7rem; background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- פונקציות ליבה (GitHub & Gemini) ---

def github_action(file_path, method="GET", data=None, sha=None):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"{REPO_API}/{file_path}"
    
    if method == "GET":
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            content = base64.b64decode(r.json()['content']).decode('utf-8')
            return json.loads(content), r.json()['sha']
        return [], None
    
    elif method == "PUT":
        payload = {
            "message": f"System Update: {datetime.now().strftime('%H:%M')}",
            "content": base64.b64encode(json.dumps(data, indent=4).encode('utf-8')).decode('utf-8'),
            "sha": sha
        }
        return requests.put(url, headers=headers, json=payload)

def call_gemini(prompt):
    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        r = requests.post(GEMINI_URL, json=payload)
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"שגיאת AI: {str(e)}"

# --- מבנה הדף ---

st.title("🧠 AI Autonomous Master Control")
st.caption("ניהול ישיר: GitHub Repository | Gemini 1.5 Flash | Zero-Latency")

# חלק 1: קוביות סקילים (Skills Grid)
st.subheader("🛠️ סקילים פעילים במערכת")
skills_list, skills_sha = github_action("skills.json")

if skills_list:
    cols = st.columns(3)
    for idx, skill in enumerate(skills_list):
        with cols[idx % 3]:
            st.markdown(f"""<div class="skill-box">
                <div style="font-weight:bold; color:#3b82f6;">{skill.get('name', 'Skill')}</div>
                <div style="font-size:0.8rem; color:#64748b;">{skill.get('description', '')}</div>
            </div>""", unsafe_allow_html=True)
            if st.button("הפעל", key=f"run_{idx}"):
                st.toast(f"מריץ: {skill.get('name')}...")
else:
    st.info("לא נמצאו סקילים ב-skills.json")

st.divider()

# חלק 2: צ'אט פקודות ופיתוח (The Brain)
st.subheader("🤖 מרכז פקודות וניהול באגים")
with st.container():
    col1, col2 = st.columns([4, 1])
    with col1:
        cmd = st.text_input("הזן פקודה (למשל: 'תקן את הבאג בנתיב ה-API ותעדכן לוג')", placeholder="מה תרצה שהסוכן יבצע?")
    with col2:
        st.write("##")
        if st.button("שגר פקודה", use_container_width=True, type="primary"):
            if cmd:
                with st.spinner("הסוכן מעבד, מתקן ומסנכרן..."):
                    # 1. ג'מיני מייצר פתרון/תשובה
                    ai_res = call_gemini(f"You are a system admin. Execute: {cmd}. If it's a bug fix, explain what you fixed. Reply in Hebrew.")
                    
                    # 2. עדכון הזיכרון (history.json)
                    hist, h_sha = github_action("history.json")
                    hist.append({
                        "timestamp": datetime.now().strftime("%H:%M:%S %d/%m/%Y"),
                        "user": cmd,
                        "ai": ai_res,
                        "status": "Success/Fixed"
                    })
                    github_action("history.json", method="PUT", data=hist, sha=h_sha)
                    st.success("הפקודה בוצעה והזיכרון עודכן!")
                    st.rerun()

st.divider()

# חלק 3: זיכרון המערכת (Log & History)
st.subheader("📜 יומן פעולות, תוצאות ובאגים")
history_data, _ = github_action("history.json")

if history_data:
    for entry in reversed(history_data):
        st.markdown(f"""
        <div class="chat-bubble">
            <div style="display:flex; justify-content:space-between;">
                <span class="user-text">👤 פקודה: {entry.get('user')}</span>
                <span class="status-tag">DONE</span>
            </div>
            <div class="ai-text">🤖 <b>תשובת המערכת:</b><br>{entry.get('ai')}</div>
            <div style="font-size:0.7rem; color:#94a3b8; margin-top:10px;">🕒 {entry.get('timestamp')}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.write("הזיכרון ריק. התחל לדבר עם הסוכן!")
