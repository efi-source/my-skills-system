import streamlit as st
import requests
import json
import base64
from datetime import datetime

# --- הגדרות ה"טיל" (המפתחות המעודכנים שלך) ---
GEMINI_API_KEY = "AIzaSyDbGtzd4_Q6Vd346hh84A81ugtHGaWHHYo"
GITHUB_TOKEN = "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"
GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"

# נתיבי עבודה מול ה-APIs
REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# --- עיצוב ממשק יוקרתי, נקי ורגוע ---
st.set_page_config(page_title="AI Master Control v2", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f8fafc; color: #1e293b; font-family: 'Segoe UI', sans-serif; }
    
    /* כרטיסי סקילים */
    .skill-box { 
        background: white; padding: 20px; border-radius: 12px; 
        border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px; text-align: center; height: 120px;
    }
    
    /* בועות צ'אט והיסטוריה */
    .chat-bubble {
        background: white; padding: 20px; border-radius: 15px;
        border-right: 6px solid #3b82f6; margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .user-text { color: #64748b; font-size: 0.9rem; font-weight: 600; margin-bottom: 8px; }
    .ai-text { color: #1e293b; font-size: 1rem; line-height: 1.6; background: #f1f5f9; padding: 12px; border-radius: 8px; }
    .time-stamp { font-size: 0.75rem; color: #94a3b8; margin-top: 10px; display: block; }
</style>
""", unsafe_allow_html=True)

# --- פונקציות ליבה (GitHub & Gemini) ---

def github_request(file_path, method="GET", data=None, sha=None):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    url = f"{REPO_API}/{file_path}"
    
    try:
        if method == "GET":
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                content = base64.b64decode(r.json()['content']).decode('utf-8')
                return json.loads(content), r.json()['sha']
            return [], None
        
        elif method == "PUT":
            payload = {
                "message": f"AI Sync: {datetime.now().strftime('%H:%M')}",
                "content": base64.b64encode(json.dumps(data, indent=4).encode('utf-8')).decode('utf-8'),
                "sha": sha
            }
            r = requests.put(url, headers=headers, json=payload)
            return r.status_code in [200, 201]
    except Exception as e:
        st.error(f"GitHub Error: {e}")
        return None, None

def ask_gemini(prompt):
    try:
        payload = {"contents": [{"parts": [{"text": f"אתה סוכן AI חכם שמנהל מערכת. המשתמש ביקש: {prompt}. ענה בעברית מקצועית וקצרה."}]}]}
        r = requests.post(GEMINI_URL, json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"שגיאת ג'מיני: {r.status_code}"
    except Exception as e:
        return f"שגיאת חיבור ל-AI: {e}"

# --- מבנה הדף ---

st.title("🛡️ AI Master Command Center")
st.caption("מערכת אוטונומית בחיבור ישיר | סטטוס: מחובר לגיטהאב")

# תפריט צד לבדיקה מהירה
with st.sidebar:
    st.header("🛠️ כלי מערכת")
    if st.button("🔄 רענן נתונים"):
        st.rerun()
    if st.button("🔍 בדיקת חיבור לגיטהאב"):
        _, sha = github_request("history.json")
        if sha: st.success("חיבור תקין!")
        else: st.error("שגיאת חיבור. בדוק טוקן.")

# חלק 1: סקילים (Skills Grid)
st.subheader("🛠️ סקילים פעילים")
skills, _ = github_request("skills.json")

if skills:
    cols = st.columns(3)
    for i, skill in enumerate(skills):
        with cols[i % 3]:
            st.markdown(f"""<div class="skill-box">
                <div style="font-weight:bold; color:#3b82f6; font-size:1.1rem;">{skill.get('name')}</div>
                <div style="font-size:0.85rem; color:#64748b; margin-top:5px;">{skill.get('description')}</div>
            </div>""", unsafe_allow_html=True)
            if st.button("הפעל סקיל", key=f"btn_{i}"):
                st.toast(f"מפעיל {skill.get('name')}...")

st.divider()

# חלק 2: צ'אט פקודות (The Brain)
st.subheader("🤖 מרכז פקודות וניהול")
with st.container():
    col_in, col_btn = st.columns([4, 1])
    with col_in:
        user_cmd = st.text_input("הזן הנחיה לסוכן (תיקון באג, הוספת מידע, שאלה):", key="cmd_input")
    with col_btn:
        st.write("##")
        if st.button("שגר פקודה", type="primary", use_container_width=True):
            if user_cmd:
                with st.spinner("הסוכן חושב ומעדכן את השרת..."):
                    # 1. ג'מיני עונה
                    ai_answer = ask_gemini(user_cmd)
                    
                    # 2. עדכון היסטוריה בגיטהאב
                    history, h_sha = github_request("history.json")
                    history.append({
                        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "user": user_cmd,
                        "ai": ai_answer
                    })
                    
                    if github_request("history.json", method="PUT", data=history, sha=h_sha):
                        st.success("הפעולה בוצעה והזיכרון עודכן!")
                        st.rerun()

st.divider()

# חלק 3: היסטוריית פעולות (History)
st.subheader("📜 יומן פעולות וזיכרון מערכת")
history_data, _ = github_request("history.json")

if history_data:
    for entry in reversed(history_data):
        st.markdown(f"""
        <div class="chat-bubble">
            <div class="user-text">👤 פקודת משתמש: {entry.get('user')}</div>
            <div class="ai-text">🤖 {entry.get('ai')}</div>
            <span class="time-stamp">🕒 {entry.get('timestamp')}</span>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("היסטוריית המערכת ריקה. שלח פקודה ראשונה כדי להתחיל!")
