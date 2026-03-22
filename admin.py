import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- הגדרות מערכת ---
PIPEDREAM_URL = "https://eoz6msqotx1bbg9.m.pipedream.net/"
GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"
RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main"

# --- עיצוב ממשק רגוע ויוקרתי ---
st.set_page_config(page_title="AI Management Console", layout="wide")

st.markdown("""
<style>
    /* רקע כללי ופונטים */
    .stApp { background-color: #f8fafc; color: #1e293b; }
    
    /* כרטיסי סקילים */
    .skill-card { 
        background: white; 
        padding: 20px; 
        border-radius: 12px; 
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        border: 1px solid #e2e8f0;
        margin-bottom: 15px;
        transition: transform 0.2s;
    }
    .skill-card:hover { transform: translateY(-3px); }
    
    /* בועות היסטוריה */
    .history-item {
        background: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #3b82f6;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgb(0 0 0 / 0.1);
    }
    .timestamp { color: #64748b; font-size: 0.8em; }
    .user-msg { color: #1e293b; font-weight: 600; margin-bottom: 5px; }
    .ai-res { color: #334155; background: #f1f5f9; padding: 10px; border-radius: 5px; font-family: monospace; }
    
    /* כפתורים */
    .stButton>button {
        border-radius: 8px;
        background-color: #3b82f6;
        color: white;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #2563eb; color: white; }
</style>
""", unsafe_allow_html=True)

# --- פונקציות עזר ---
def fetch_json(file_name):
    try:
        r = requests.get(f"{RAW_BASE}/{file_name}")
        return r.json() if r.status_code == 200 else []
    except:
        return []

# --- תפריט צד ---
with st.sidebar:
    st.title("⚙️ הגדרות")
    st.info("המערכת מחוברת ל-GitHub ומסנכרנת נתונים בזמן אמת.")
    if st.button("רענן נתונים"):
        st.rerun()

# --- גוף העמוד ---
st.title("🛡️ AI Command Center")
st.caption("ניהול סקילים, תיקון באגים ומעקב אחר פעולות הסוכן")

# --- חלק 1: סקילים פעילים ---
st.subheader("🛠️ סקילים זמינים")
skills = fetch_json("skills.json")

if skills:
    cols = st.columns(3)
    for i, skill in enumerate(skills):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="skill-card">
                <div style="font-size: 1.2em; font-weight: bold;">{skill.get('name', 'סקיל ללא שם')}</div>
                <div style="color: #64748b; font-size: 0.9em; margin-bottom: 10px;">{skill.get('description', 'אין תיאור זמין')}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"הפעל את {skill.get('name')}", key=f"btn_{i}"):
                with st.spinner("מבצע פקודה..."):
                    res = requests.post(PIPEDREAM_URL, json={"message": f"Execute skill: {skill.get('name')}"})
                    st.toast(f"תגובה: {res.text[:50]}...")

st.divider()

# --- חלק 2: שליחת פקודות פיתוח ---
st.subheader("🤖 מרכז פיתוח ותיקון")
col_text, col_btn = st.columns([4, 1])

with col_text:
    user_input = st.text_input("הנחיות לסוכן (למשל: 'תקן את הבאג בנתיב ה-API')", key="main_input")

with col_btn:
    st.write("##")
    if st.button("שלח פקודה", use_container_width=True):
        if user_input:
            with st.spinner("הסוכן מעדכן את המערכת..."):
                try:
                    requests.post(PIPEDREAM_URL, json={"message": user_input})
                    st.success("הפקודה נשלחה! המתן לעדכון בגיטהאב.")
                    st.rerun()
                except:
                    st.error("שגיאה בחיבור לשרת.")

st.divider()

# --- חלק 3: היסטוריית פעולות (הזיכרון) ---
st.subheader("📜 יומן פעולות המערכת")
history = fetch_json("history.json")

if history:
    # טיפול במקרה שהקובץ אינו רשימה
    if not isinstance(history, list):
        history = [history]
        
    for item in reversed(history):
        st.markdown(f"""
        <div class="history-item">
            <div class="timestamp">🕒 {item.get('timestamp', 'זמן לא ידוע')}</div>
            <div class="user-msg">👤 פקודה: {item.get('user', '-')}</div>
            <div class="ai-res">🤖 {item.get('ai', 'מבצע עדכון...')}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.write("היסטוריית הפעולות ריקה.")
