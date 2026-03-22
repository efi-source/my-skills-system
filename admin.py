import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- הגדרות קישורים - חובה לעדכן את הקישורים שלך ---
PIPEDREAM_URL = "כאן_הלינק_של_ה-ENDPOINT_מ-PIPEDREAM"
GITHUB_USER = "efi-source" # שם המשתמש שלך
GITHUB_REPO = "my-skills-system" # שם הריפוזיטורי
SKILLS_FILE = "skills.json"
HISTORY_FILE = "history.json"

# יצירת קישורי RAW לקריאה מגיטהאב
RAW_SKILLS_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/{SKILLS_FILE}"
RAW_HISTORY_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/{HISTORY_FILE}"

# --- עיצוב דף האדמין ---
st.set_page_config(page_title="AI Autonomous Admin", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .skill-card { background: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 10px; }
    .history-card { background: #1c2128; padding: 15px; border-radius: 8px; border-right: 4px solid #58a6ff; margin-bottom: 12px; }
    .user-text { color: #8b949e; font-size: 0.9em; }
    .ai-text { color: #58a6ff; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🧠 AI Autonomous System - Command Center")

# --- פונקציות עזר ---
def get_data(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except:
        return []
    return []

# --- חלק 1: סקילים פעילים (ניהול וביצוע) ---
st.subheader("🛠️ סקילים במערכת (משיכה מ-GitHub)")
skills = get_data(RAW_SKILLS_URL)

if skills:
    cols = st.columns(3)
    for i, skill in enumerate(skills):
        with cols[i % 3]:
            st.markdown(f"""<div class="skill-card">
                <b>{skill.get('name', 'Unknown Skill')}</b><br>
                <small>{skill.get('description', 'No description')}</small>
            </div>""", unsafe_allow_html=True)
            if st.button(f"הפעל: {skill.get('name')}", key=f"run_{i}"):
                with st.spinner("מריץ סקיל..."):
                    res = requests.post(PIPEDREAM_URL, json={"message": f"Run skill: {skill.get('name')}"})
                    st.write(res.text)
else:
    st.info("לא נמצאו סקילים ב-GitHub. בקש מה-AI ליצור אחד!")

st.divider()

# --- חלק 2: ממשק פקודות (הזנה) ---
st.subheader("🤖 שלח פקודה ל-AI (תיקון באגים / הוספת קוד)")
col_input, col_btn = st.columns([4, 1])

with col_input:
    user_query = st.text_input("הזן פקודה חדשה:", placeholder="למשל: תתקן את הבאג בסקיל המזג אוויר ותעדכן בגיטהאב")

with col_btn:
    st.write("##") # ריוח
    if st.button("שגר פקודה", use_container_width=True):
        if user_query:
            with st.spinner("הסוכן מעבד ומעדכן מערכות..."):
                try:
                    response = requests.post(PIPEDREAM_URL, json={"message": user_query})
                    st.success("הפקודה נשלחה בהצלחה!")
                    st.rerun() # רענון כדי לראות את ההיסטוריה מתעדכנת
                except Exception as e:
                    st.error(f"שגיאה בחיבור ל-Pipedream: {e}")

st.divider()

# --- חלק 3: היסטוריית מערכת (הזיכרון של ה-AI) ---
st.subheader("📜 לוג פעולות וזיכרון (מהשרת)")
history = get_data(RAW_HISTORY_URL)

if history:
    # אם ההיסטוריה היא אובייקט בודד (כי Pipedream דרס), נהפוך אותה לרשימה
    if not isinstance(history, list):
        history = [history]
        
    for entry in reversed(history):
        st.markdown(f"""
        <div class="history-card">
            <div class="user-text">🕒 {entry.get('timestamp', 'N/A')} | <b>בקשתך:</b> {entry.get('user', 'Empty')}</div>
            <div class="ai-text">🤖 תשובת AI/ביצוע:</div>
            <div style="font-family: monospace; font-size: 0.85em; background: #0d1117; padding: 10px; margin-top: 5px;">
                {entry.get('ai', 'No data')}
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.write("היסטוריית השרת ריקה כרגע.")
