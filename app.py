import streamlit as st
import pandas as pd
import uuid
import os

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
