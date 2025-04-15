import streamlit as st
import requests
import pandas as pd
from datetime import date
import re

# 🔐 Supabase 연결 정보
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# 🔐 관리자 권한 유저 목록
ADMIN_USERS = ["자리스틸의왕", "나영진", "죤냇", "o차월o"]

# ✅ Supabase에 길드원 등록
def insert_member(data):
    res = requests.post(
        f"{SUPABASE_URL}/rest/v1/Members",
        headers=HEADERS,
        json=data
    )
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

# ✅ 길드원 삭제
def delete_member(member_id):
    res = requests.delete(
        f"{SUPABASE_URL}/rest/v1/Members?id=eq.{member_id}",
        headers=HEADERS
    )
    return res.status_code == 204

# ✅ 길드원 수정
def update_member(member_id, data):
    res = requests.patch(
        f"{SUPABASE_URL}/rest/v1/Members?id=eq.{member_id}",
        headers=HEADERS,
        json=data
    )
    return res.status_code == 204

# ✅ Streamlit 로그인 인터페이스
st.title("🛡️ 악마길드 관리 시스템")

if "user" not in st.session_state:
    st.subheader("🔐 로그인")
    login_name = st.text_input("닉네임")
    login_pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        try:
            csv_url = "https://raw.githubusercontent.com/qqqppma/maple/main/guild_user.csv"
            df_users = pd.read_csv(csv_url, encoding="utf-8-sig")
            matched = df_users[
                (df_users["닉네임"].str.strip() == login_name.strip()) &
                (df_users["비밀번호"].astype(str).str.strip() == login_pw.strip())
            ]
            if not matched.empty:
                st.session_state["user"] = login_name
                st.session_state["is_admin"] = login_name in ADMIN_USERS
                st.rerun()
            else:
                st.error("일치하는 사용자 정보가 없습니다.")
        except Exception as e:
            st.error(f"CSV 로드 오류: {e}")
    st.stop()

# 로그인 된 사용자 정보
nickname = st.session_state["user"]
is_admin = st.session_state["is_admin"]

# 메뉴 구성
menu = st.sidebar.radio("메뉴", ["길드원 등록"])

# 정렬 우선순위 지정
def get_position_priority(pos):
    priority = {"길드마스터": 1, "부마스터": 2, "길드원": 3}
    return priority.get(pos, 99)

def korean_first_sort(value):
    # 한글 시작 문자가 아닌 경우 우선순위를 뒤로
    return (not bool(re.match(r"[가-힣]", str(value)[0])), value)

if menu == "길드원 등록":
    st.subheader("👥 길드원 정보 등록")

    members = get_members()
    df = pd.DataFrame(members)
    if not df.empty:
        df["position"] = df["position"].fillna("")
        df = df.sort_values(by=["position", "nickname"],
                            key=lambda x: x.map(get_position_priority) if x.name == "position" else x.map(korean_first_sort))
        st.dataframe(df.reset_index(drop=True))

        if is_admin:
            selected_name = st.selectbox("수정 또는 삭제할 닉네임 선택", df["nickname"])
            selected_row = df[df["nickname"] == selected_name].iloc[0]

            with st.form("edit_form"):
                nickname_edit = st.text_input("닉네임", selected_row["nickname"])
                position_edit = st.text_input("직위", selected_row["position"])
                active_edit = st.selectbox("활동 여부", [True, False], index=0 if selected_row["active"] else 1)
                resume_date_edit = st.date_input("활동 재개일", value=pd.to_datetime(selected_row["resume_date"]).date() if selected_row["resume_date"] else date.today())
                join_date_edit = st.date_input("가입일", value=pd.to_datetime(selected_row["join_date"]).date())
                note_edit = st.text_input("비고", selected_row["note"])
                guild_name_edit = st.text_input("길드명", selected_row["guild_name"])
                withdrawn_edit = st.selectbox("탈퇴 여부", [False, True], index=1 if selected_row["withdrawn"] else 0)
                withdraw_date_edit = st.date_input("탈퇴일", value=pd.to_datetime(selected_row["withdraw_date"]).date() if selected_row["withdraw_date"] else date.today())

                update_btn = st.form_submit_button("✏️ 수정")
                delete_btn = st.form_submit_button("🗑 삭제")

                if update_btn:
                    updated_data = {
                        "nickname": nickname_edit,
                        "position": position_edit,
                        "active": active_edit,
                        "resume_date": resume_date_edit.isoformat(),
                        "join_date": join_date_edit.isoformat(),
                        "note": note_edit,
                        "guild_name": guild_name_edit,
                        "withdrawn": withdrawn_edit,
                        "withdraw_date": withdraw_date_edit.isoformat()
                    }
                    if update_member(selected_row["id"], updated_data):
                        st.success("수정 완료!")
                        st.rerun()
                    else:
                        st.error("수정 실패!")
                elif delete_btn:
                    if delete_member(selected_row["id"]):
                        st.success("삭제 완료!")
                        st.rerun()
                    else:
                        st.error("삭제 실패!")
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