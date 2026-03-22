import streamlit as st
import json
import os
import requests

st.set_page_config(page_title="ניהול סקילים ו-AI", layout="wide")

# פונקציות לניהול הקובץ
def load_skills():
    if os.path.exists('skills.json'):
        with open('skills.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_skills(skills_list):
    with open('skills.json', 'w', encoding='utf-8') as f:
        json.dump(skills_list, f, indent=2, ensure_ascii=False)

# עיצוב הכותרת
st.title("🛠️ לוח בקרה - My Skills System")

# תצוגת סקילים קיימים
skills = load_skills()
st.subheader("הסקילים שלך:")
cols = st.columns(3)
for i, s in enumerate(skills):
    with cols[i % 3]:
        st.info(f"**{s['name']}**\n\n{s['description']}")

st.divider()

# חלק הפעלת ה-AI
st.subheader("🤖 דבר עם ה-AI שלך")
user_input = st.text_input("מה תרצה שהמערכת תעשה?")

if st.button("שגר פקודה ל-Gemini"):
    if user_input:
        with st.spinner("Gemini חושב..."):
            # כאן תדביק את הכתובת שהעתקת מ-Pipedream
            webhook_url = "https://eoz6msqotx1bbg9.m.pipedream.net" 
            
            try:
                response = requests.post(webhook_url, json={"message": user_input})
                if response.status_code == 200:
                    st.success("תשובת המערכת:")
                    st.write(response.text) # מציג את מה ש-Gemini החזיר
                else:
                    st.error("היתה שגיאה בחיבור ל-Pipedream")
            except Exception as e:
                st.error(f"שגיאה: {e}")
    else:
        st.warning("נא לכתוב פקודה לפני הלחיצה.")

st.divider()

# טופס הוספה (בתחתית כדי שלא יפריע)
with st.expander("➕ הוספת סקיל חדש לרשימה"):
    with st.form("add_form"):
        name = st.text_input("שם הסקיל")
        desc = st.text_area("תיאור הפעולה")
        if st.form_submit_button("שמור"):
            skills.append({"name": name, "description": desc})
            save_skills(skills)
            st.rerun()
