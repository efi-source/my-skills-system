import streamlit as st
import json
import os

st.set_page_config(page_title="ניהול סקילים", layout="wide")

st.title("🛠️ לוח בקרה - My Skills System")

# פונקציה לקריאת הסקילים
def load_skills():
    if os.path.exists('skills.json'):
        with open('skills.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# פונקציה לשמירת סקילים
def save_skills(skills_list):
    with open('skills.json', 'w', encoding='utf-8') as f:
        json.dump(skills_list, f, indent=2, ensure_ascii=False)

skills = load_skills()

# תצוגה של מה שיש כרגע
st.subheader("הסקילים הקיימים במערכת:")
if not skills:
    st.info("אין עדיין סקילים. הוסף אחד למטה!")
else:
    for s in skills:
        with st.expander(f"📌 {s['name']}"):
            st.write(f"**תיאור:** {s['description']}")

st.divider()

# טופס להוספה
st.subheader("➕ הוספת סקיל חדש")
with st.form("add_form"):
    name = st.text_input("שם הסקיל (למשל: 'מזג אוויר')")
    desc = st.text_area("מה הסקיל עושה?")
    submit = st.form_submit_button("שמור במערכת")
    
    if submit and name:
        skills.append({"name": name, "description": desc})
        save_skills(skills)
        st.success(f"הסקיל '{name}' נשמר בהצלחה!")
        st.rerun()
