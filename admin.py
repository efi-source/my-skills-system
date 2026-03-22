import streamlit as st
import requests

# הגדרות דף רחב ועיצוב
st.set_page_config(page_title="AI Admin Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .skill-card { border: 1px solid #30363d; padding: 15px; border-radius: 10px; background-color: #161b22; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 AI Skills Admin - Dashboard")

# פונקציה לשליחת פקודה ל-Pipedream
def send_to_ai(message):
    url = "YOUR_PIPEDREAM_WEBHOOK_URL" # שים פה את הכתובת שלך!
    try:
        res = requests.post(url, json={"message": message})
        return res.text
    except:
        return "שגיאה בחיבור לשרת"

# חלוקה לעמודות: סקילים בצד ותצוגה מרכזית
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("🛠️ סקילים פעילים")
    # כאן אפשר להוסיף לופ שמושך את הסקילים מגיטהאב כפי שעשית
    st.info("בדיקת מזג אוויר")
    st.info("ניתוח נתונים")

with col2:
    st.subheader("💬 ממשק פקודות")
    user_input = st.text_area("מה תרצה שהמערכת תעשה?", placeholder="למשל: תציג לי טבלת מכירות של החודש האחרון...")
    
    if st.button("שגר פקודה"):
        if user_input:
            with st.spinner("Gemini מעבד נתונים..."):
                response = send_to_ai(user_input)
                st.success("תשובת המערכת:")
                # שימוש ב-Markdown מאפשר ל-Gemini להציג טבלאות וגרפים
                st.markdown(response) 
        else:
            st.warning("נא להזין פקודה")

# הוספת אזור לגרפים (דוגמה)
st.divider()
st.subheader("📊 ניתוח נתונים חזותי")
if st.checkbox("הצג נתוני פעילות"):
    st.line_chart([10, 25, 40, 35, 50]) # כאן Gemini יוכל להזין נתונים בעתיד
