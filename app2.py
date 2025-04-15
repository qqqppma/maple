import streamlit as st
import requests
import pandas as pd
from datetime import date

# 🔐 Supabase 연결 정보 (Streamlit Cloud의 Secrets에서 설정하세요)
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ✅ Supabase에 길드원 등록

def insert_member(data):
    res = requests.post(
        f"{SUPABASE_URL}/rest/v1/Members",
        headers=HEADERS,
        json=data
    )
    st.write("🧪 응답 코드:", res.status_code)
    st.write("🔍 응답 본문:", res.text)
    return res.status_code == 201

# ✅ Supabase에서 길드원 목록 불러오기

def get_members():
    res = requests.get(
        f"{SUPABASE_URL}/rest/v1/Members?select=*&order=id.desc",
        headers=HEADERS
    )
    if res.status_code == 200:
        return res.json()
    return []

# ✅ Streamlit 인터페이스

st.title("🛡️ 악마길드 - 길드원 등록")

# 🔽 전체 목록 보여주기
members = get_members()
df = pd.DataFrame(members)
if not df.empty:
    st.dataframe(df)
else:
    st.info("아직 등록된 길드원이 없습니다.")

# ✍️ 신규 등록 폼
st.subheader("📋 길드원 정보 등록")
with st.form("add_member_form"):
    nickname = st.text_input("닉네임")
    position = st.text_input("직위")
    active = st.selectbox("활동 여부", [True, False])
    resume_date = st.date_input("활동 재개일", value=None)
    join_date = st.date_input("가입일", value=date.today())
    note = st.text_input("비고")
    guild_name = st.text_input("길드명")
    withdrawn = st.selectbox("탈퇴 여부", [False, True])
    withdraw_date = st.date_input("탈퇴일", value=None)

    submitted = st.form_submit_button("등록")
    if submitted:
        data = {
            "nickname": nickname,
            "position": position,
            "active": active,
            "join_date": join_date.isoformat(),
            "note": note,
            "guild_name": guild_name,
            "withdrawn": withdrawn
        }

        if resume_date:
            data["resume_date"] = resume_date.isoformat()

        if withdraw_date:
            data["withdraw_date"] = withdraw_date.isoformat()

        success = insert_member(data)
        if success:
            st.success("✅ 길드원이 등록되었습니다!")
            st.rerun()
        else:
            st.error("🚫 등록에 실패했습니다. 데이터를 다시 확인해주세요.")