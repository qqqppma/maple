import streamlit as st
import requests
import pandas as pd
from datetime import date

# 🔐 Supabase 연결 정보
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

# ✅ Streamlit 로그인 인터페이스
st.title("🛡️ 악마길드 관리 시스템")

if "user" not in st.session_state:
    st.subheader("🔐 로그인")
    login_name = st.text_input("캐릭터명")
    login_pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        # GitHub CSV에서 불러오기
        try:
            csv_url = "https://raw.githubusercontent.com/qqqppma/maple/main/guild_user.csv"  # 사용자 csv URL
            df_users = pd.read_csv(csv_url)
            matched = df_users[
                (df_users["닉네임"] == login_name) & (df_users["비밀번호"] == login_pw)
            ]
            if not matched.empty:
                st.session_state["user"] = login_name
                st.session_state["position"] = matched.iloc[0]["직위"]
                st.rerun()
            else:
                st.error("일치하는 사용자 정보가 없습니다.")
        except Exception as e:
            st.error(f"CSV 로드 오류: {e}")
    st.stop()

# 로그인 된 사용자 정보
nickname = st.session_state["user"]
position = st.session_state["position"]

# 메뉴 구성
menu = st.sidebar.radio("메뉴", ["길드원 등록"])

if menu == "길드원 등록":
    st.subheader("👥 길드원 정보 등록")

    members = get_members()
    df = pd.DataFrame(members)
    if not df.empty:
        st.dataframe(df)
    else:
        st.info("아직 등록된 길드원이 없습니다.")

    with st.form("add_member_form"):
        nickname_input = st.text_input("닉네임")
        position_input = st.text_input("직위")
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
                "nickname": nickname_input,
                "position": position_input,
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
