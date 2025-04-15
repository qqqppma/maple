import streamlit as st
import pandas as pd
import uuid
import os
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
        f"{SUPABASE_URL}/rest/v1/members",
        headers=HEADERS,
        json=data
    )
    return res.status_code == 201

# ✅ Supabase에서 길드원 목록 불러오기

def get_members():
    res = requests.get(
        f"{SUPABASE_URL}/rest/v1/members?select=*&order=id.desc",
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
st.subheader("👤 신규 길드원 등록")
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
            "resume_date": resume_date.isoformat() if resume_date else None,
            "join_date": join_date.isoformat(),
            "note": note,
            "guild_name": guild_name,
            "withdrawn": withdrawn,
            "withdraw_date": withdraw_date.isoformat() if withdraw_date else None
        }
        success = insert_member(data)
        if success:
            st.success("✅ 길드원이 등록되었습니다!")
            st.rerun()
        else:
            st.error("🚫 등록에 실패했습니다. 데이터를 다시 확인해주세요.")

# ===== 설정 =====
USER_FILE = "길드원 목록.csv"  # 사용자 정보 (닉네임 포함)
DATA_FILE = "board.csv"
ADMIN_USERS = ["o차월o", "죤냇", "자리스틸의왕"]  # 관리자 닉네임 리스트

# ===== 사용자 인증 =====
def is_valid_user(nickname):
    if os.path.exists(USER_FILE):
        df_users = pd.read_csv(USER_FILE)
        return nickname in df_users["닉네임"].values
    return False

# 로그인 처리
if "user" not in st.session_state:
    nickname = st.text_input("닉네임을 입력하세요")
    if st.button("로그인"):
        if is_valid_user(nickname):
            st.session_state["user"] = nickname
            st.rerun()
        else:
            st.error("등록되지 않은 닉네임입니다.")
    st.stop()

user = st.session_state["user"]
is_admin = user in ADMIN_USERS

# ===== 데이터 로딩 / 저장 =====
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["id", "작성자", "제목", "내용"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# ===== 글 작성 =====
st.title("📋 게시판")
st.markdown(f"**👤 로그인 사용자:** `{user}`")
st.subheader("✏️ 글 작성하기")

title = st.text_input("제목을 입력하세요:")
new_content = st.text_area("내용을 입력하세요:")
if st.button("등록"):
    if title.strip() and new_content.strip():
        df = load_data()
        new_row = {"id": str(uuid.uuid4()), "작성자": user, "제목": title, "내용": new_content}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success("등록 완료!")
        st.rerun()
    else:
        st.warning("제목과 내용을 모두 입력해주세요.")

# ===== 게시글 목록 표시 =====
st.subheader("📄 게시글 목록")
df = load_data()
st.dataframe(df[["작성자", "제목", "내용"]], use_container_width=True)

# ===== 관리자 기능 =====
if is_admin and not df.empty:
    st.markdown("---")
    st.markdown("### 🔧 관리자 전용 - 글 수정/삭제")

    df = df[["id", "작성자", "제목", "내용"]]  # 열 순서 명시적으로 재정렬

    df["제목"] = df["제목"].fillna("(제목 없음)")
    df["글 식별"] = df.index.astype(str) + " - " + df["제목"]

    selected_display = st.selectbox("수정할 글 선택", df["글 식별"].tolist())
    selected_index = int(selected_display.split(" - ")[0])

    selected_title = df.iloc[selected_index]["제목"]
    selected_content = df.iloc[selected_index]["내용"]


    updated_title = st.text_input("제목 수정", value=selected_title, key="edit_title")
    updated_content = st.text_area("내용 수정", value=selected_content, key="edit_area")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("수정 저장"):
            df.at[selected_index, "제목"] = updated_title
            df.at[selected_index, "내용"] = updated_content
            save_data(df)
            st.success("수정 완료!")
            st.rerun()
    with col2:
        if st.button("삭제"):
            df = df.drop(index=selected_index).reset_index(drop=True)
            save_data(df)
            st.success("삭제 완료!")
            st.rerun()