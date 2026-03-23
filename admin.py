import streamlit as st
import requests
import json
import base64
from datetime import datetime

# --- הגדרות ה"טיל" ---
GEMINI_API_KEY = "AIzaSyDbGtzd4_Q6Vd346hh84A81ugtHGaWHHYo"
GITHUB_TOKEN = "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"
GITHUB_USER = "efi-source"
GITHUB_REPO = "my-skills-system"

REPO_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# --- פונקציות תקשורת עם אבחון שגיאות ---

def github_request(path, method="GET", data=None, sha=None):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"{REPO_API}/{path}"
    try:
        if method == "GET":
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                content = base64.b64decode(r.json()['content']).decode('utf-8')
                return json.loads(content), r.json()['sha']
            else:
                st.error(f"שגיאת קריאה מגיטהאב ({path}): {r.status_code}")
                return [], None
        elif method == "PUT":
            payload = {
                "message": f"AI Update {datetime.now().strftime('%H:%M')}",
                "content": base64.b64encode(json.dumps(data, indent=4).encode('utf-8')).decode('utf-8'),
                "sha": sha
            }
            r = requests.put(url, headers=headers, json=payload)
            if r.status_code not in [200, 201]:
                st.error(f"שגיאת כתיבה לגיטהאב: {r.status_code} - {r.text}")
            return r.status_code in [200, 201]
    except Exception as e:
        st.error(f"שגיאה טכנית: {str(e)}")
        return [], None

def ask_gemini(prompt):
    try:
        payload = {"contents": [{"parts": [{"text": f"ענה בעברית: {prompt}"}]}]}
        r = requests.post(GEMINI_URL, json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            st.error(f"ג'מיני לא עונה: {r.status_code}")
            return None
    except Exception as e:
        st.error(f"שגיאת חיבור ל-AI: {e}")
        return None

# --- ממשק משתמש ---
st.title("🧠 AI Master Control Center")

# בדיקת סנכרון ראשונית
if st.sidebar.button("🔍 בדוק חיבור עכשיו"):
    h, s = github_request("history.json")
    if s: st.sidebar.success("חיבור לגיטהאב: תקין ✅")

# סקילים
st.subheader("🛠️ סקילים פעילים")
skills, _ = github_request("skills.json")
if skills:
    cols = st.columns(3)
    for i, s in enumerate(skills):
        with cols[i % 3]:
            st.info(f"**{s.get('name')}**")

st.divider()

# מרכז פקודות
st.subheader("🤖 שלח פקודה לסוכן")
cmd = st.text_input("הזן פקודה:", key="main_cmd")

if st.button("שגר", type="primary"):
    if cmd:
        with st.spinner("מבצע פעולה..."):
            answer = ask_gemini(cmd)
            if answer:
                hist, sha = github_request("history.json")
                if sha:
                    hist.append({"time": datetime.now().strftime("%H:%M"), "user": cmd, "ai": answer})
                    if github_request("history.json", "PUT", hist, sha):
                        st.success("המידע נשמר בהצלחה!")
                        st.rerun()

st.divider()

# זיכרון
st.subheader("📜 זיכרון המערכת")
history, _ = github_request("history.json")
if history:
    for e in reversed(history):
        st.write(f"**👤 אתה:** {e.get('user')}")
        st.info(f"**🤖 AI:** {e.get('ai')}")
        st.divider()
else:
    st.write("ההיסטוריה ריקה כרגע. נסה לשלוח הודעה.")
