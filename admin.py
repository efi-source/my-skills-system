import streamlit as st
import requests
import json
import base64
from datetime import datetime

# --- הגדרות ---
GEMINI_API_KEY = "AIzaSyDbGtzd4_Q6Vd346hh84A81ugtHGaWHHYo"
GITHUB_TOKEN = "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"
GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"

REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

st.set_page_config(page_title="AI Admin Debug Mode", layout="wide")

# פונקציית עזר לקריאה מגיטהאב
def get_github_file(path):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(f"{REPO_API}/{path}", headers=headers)
    if res.status_code == 200:
        content = base64.b64decode(res.json()['content']).decode('utf-8')
        return json.loads(content), res.json()['sha']
    else:
        st.error(f"שגיאת גיטהאב בקריאה: {res.status_code} - {res.text}")
        return [], None

# פונקציית עזר לכתיבה לגיטהאב
def save_github_file(path, data, sha):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    content_encoded = base64.b64encode(json.dumps(data, indent=4).encode('utf-8')).decode('utf-8')
    payload = {"message": "Update from Admin", "content": content_encoded, "sha": sha}
    res = requests.put(f"{REPO_API}/{path}", headers=headers, json=payload)
    if res.status_code not in [200, 201]:
        st.error(f"שגיאת גיטהאב בכתיבה: {res.status_code} - {res.text}")

# פונקציית עזר לג'מיני
def ask_gemini(prompt):
    try:
        res = requests.post(GEMINI_URL, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            st.error(f"שגיאת ג'מיני: {res.status_code} - {res.text}")
            return None
    except Exception as e:
        st.error(f"שגיאת חיבור לג'מיני: {e}")
        return None

# --- ממשק ---
st.title("🚀 AI Admin - Debug Mode")

# כפתור בדיקה מהירה
if st.button("🔍 בדוק חיבור לגיטהאב עכשיו"):
    hist, sha = get_github_file("history.json")
    if sha:
        st.success(f"החיבור לגיטהאב תקין! SHA: {sha}")

st.subheader("🤖 שלח פקודה")
user_input = st.text_input("הזן פקודה:")

if st.button("שגר"):
    if user_input:
        with st.spinner("מבצע..."):
            # 1. ג'מיני
            answer = ask_gemini(user_input)
            if answer:
                st.info(f"תשובת ג'מיני התקבלה: {answer[:50]}...")
                # 2. גיטהאב
                history, sha = get_github_file("history.json")
                if sha:
                    history.append({"time": datetime.now().isoformat(), "user": user_input, "ai": answer})
                    save_github_file("history.json", history, sha)
                    st.success("הכל עודכן בהצלחה!")
                    st.rerun()

st.divider()
st.subheader("📜 היסטוריה")
history_data, _ = get_github_file("history.json")
st.write(history_data)
