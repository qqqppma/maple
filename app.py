import streamlit as st
from db import init_db, register_user, login_user, get_user_nickname
from secret_guild import get_character_info_from_nexon, get_guild_members_selenium

ALLOWED_GUILD_NAME = "악마"

init_db()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = ""
    st.session_state.char_name = ""
    st.session_state.is_guild_member = False

st.title("🧙‍♂️ 악마길드 로그인 시스템")

def logout():
    st.session_state.logged_in = False
    st.session_state.user_id = ""
    st.session_state.char_name = ""
    st.session_state.is_guild_member = False
    st.rerun()

if st.session_state.logged_in:
    st.success(f"{st.session_state.user_id}님 환영합니다!")

    nickname = get_user_nickname(st.session_state.user_id)
    st.write("내 캐릭터 이름:", nickname)

    char_info = get_character_info_from_nexon(nickname)
    st.write("🔍 검색된 캐릭터 정보:", char_info)

    if not char_info:
        st.error("❌ 캐릭터 정보를 불러올 수 없습니다.")
        if st.button("로그아웃"):
            logout()
        st.stop()

    guild_members = get_guild_members_selenium(ALLOWED_GUILD_NAME)
    st.write("📋 길드원 수:", len(guild_members))

    if char_info["character_name"] in guild_members:
        st.session_state.char_name = char_info["character_name"]
        st.session_state.is_guild_member = True
    else:
        st.error("⚠️ 길드원이 아닙니다. 메뉴 접근 불가")
        if st.button("로그아웃"):
            logout()
        st.stop()

    if st.session_state.is_guild_member:
        st.subheader("📋 길드원 전용 메뉴")
        menu = st.selectbox("메뉴를 선택하세요", ["메뉴1", "메뉴2", "메뉴3"])
        st.info(f"선택한 메뉴: {menu}")
        if st.button("로그아웃"):
            logout()

else:
    tab1, tab2 = st.tabs(["🔐 로그인", "📝 회원가입"])
    with tab1:
        user_id = st.text_input("아이디", key="login_id")
        pw = st.text_input("비밀번호", type="password", key="login_pw")
        if st.button("로그인", key="login_btn"):
            if login_user(user_id, pw):
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.rerun()
            else:
                st.error("❌ 로그인 실패: 아이디 또는 비밀번호가 틀렸습니다.")
    with tab2:
        new_id = st.text_input("새 아이디", key="register_id")
        new_pw = st.text_input("비밀번호", type="password", key="register_pw")
        nickname = st.text_input("캐릭터 이름(닉네임)", key="register_nick")
        if st.button("회원가입", key="register_btn"):
            try:
                register_user(new_id, new_pw, nickname)
                st.success("✅ 회원가입 성공! 로그인해 주세요.")
            except ValueError as ve:
                st.error(str(ve))
            except Exception as e:
                st.error(f"회원가입 중 오류 발생: {e}")
