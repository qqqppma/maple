import streamlit as st
import requests
import pandas as pd
from datetime import date,datetime
import re
import urllib.parse
import io
import os
from PIL import Image
from datetime import date, timedelta
st.set_page_config(page_title="악마길드 관리 시스템", layout="wide")
from supabase import create_client, Client
import json
import uuid

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_USERS = ["자리스틸의왕", "나영진", "죤냇", "o차월o"]

# ✅ 모든 캐릭터 닉네임 불러오기 함수 (Main + Sub)
def get_all_character_names(nickname):
    nickname = nickname.strip()
    # 본캐 목록 가져오기 (nickname이 Members 테이블에 존재하는 본캐)
    main_res = supabase.table("Members").select("nickname").eq("nickname", nickname).execute()
    main_names = [row["nickname"] for row in main_res.data] if main_res.data else []

    # 부캐 목록 가져오기 (SubMembers에서 main_name이 nickname과 일치)
    sub_res = supabase.table("SubMembers").select("sub_name").eq("main_name", nickname).execute()
    sub_names = [row["sub_name"] for row in sub_res.data] if sub_res.data else []

    return main_names + sub_names

# ✅ 날짜 계산 함수
def get_date_range_from_slots(time_slots_str):
    try:
        dates = sorted(set(slot.split()[0] for slot in time_slots_str.split(",") if slot.strip()))
        return f"{dates[0]} ~ {dates[-1]}" if dates else ""
    except:
        return ""


# ✅ Supabase 함수
@st.cache_data(ttl=0)
def get_members():
    res = requests.get(f"{SUPABASE_URL}/rest/v1/Members?select=*&order=position.desc", headers=HEADERS)
    if res.status_code == 200:
        return res.json()
    return []

def insert_member(data):
    res = requests.post(f"{SUPABASE_URL}/rest/v1/Members", headers=HEADERS, json=data)
    return res.status_code == 201

def update_member(member_id, data):
    # url = f"{SUPABASE_URL}/rest/v1/Members?id=eq.{member_id}" #디버깅코드
    res = requests.patch(f"{SUPABASE_URL}/rest/v1/Members?id=eq.{member_id}", headers=HEADERS, json=data)
    # 디버깅코드
    # st.write("📤 PATCH 요청:", url)
    # st.write("📦 데이터:", data)
    # st.write("📥 응답코드:", res.status_code)
    # st.write("📥 응답본문:", res.text)
    return res.status_code == 204

def delete_member(member_id):
    res = requests.delete(f"{SUPABASE_URL}/rest/v1/Members?id=eq.{member_id}", headers=HEADERS)
    return res.status_code == 204
#전체 코드에서 사용되는 함수
def get_position_priority(pos):
            priority = {"길드마스터": 1, "부마스터": 2, "길드원": 3}
            return priority.get(pos, 99)
def korean_first_sort(value):
            return (not bool(re.match(r"[가-힣]", str(value)[0])), value)

# ✅ Supabase 본캐길드 길드컨트롤 관련 함수
def get_mainmembers():
    res = requests.get(f"{SUPABASE_URL}/rest/v1/MainMembers?select=*&order=position.asc", headers=HEADERS)
    if res.status_code == 200:
        return res.json()
    return []

def update_mainember(member_id, data):
    res = requests.patch(f"{SUPABASE_URL}/rest/v1/MainMembers?id=eq.{member_id}", headers=HEADERS, json=data)
    return res.status_code == 204

def delete_mainmember(member_id):
    res = requests.delete(f"{SUPABASE_URL}/rest/v1/MainMembers?id=eq.{member_id}", headers=HEADERS)
    return res.status_code == 204

# ✅ Supabase 부캐 테이블 관련 함수
def insert_submember(data):
    res = requests.post(f"{SUPABASE_URL}/rest/v1/SubMembers", headers=HEADERS, json=data)
    if res.status_code != 201:
        st.error(f"에러 코드: {res.status_code}")
        st.code(res.text)
    return res.status_code == 201

def get_submembers():
    res = requests.get(f"{SUPABASE_URL}/rest/v1/SubMembers?select=*&order=sub_id.asc", headers=HEADERS)
    if res.status_code == 200:
        return res.json()
    return []

def update_submember(sub_id, data):
    res = requests.patch(f"{SUPABASE_URL}/rest/v1/SubMembers?sub_id=eq.{sub_id}", headers=HEADERS, json=data)
    return res.status_code == 204

def delete_submember(sub_id):
    res = requests.delete(f"{SUPABASE_URL}/rest/v1/SubMembers?sub_id=eq.{sub_id}", headers=HEADERS)
    return res.status_code == 204

# ✅ 보조무기 대여 현황 관련 함수
def fetch_weapon_rentals():
    res = requests.get(f"{SUPABASE_URL}/rest/v1/Weapon_Rentals?select=*&order=id.desc", headers=HEADERS)
    if res.status_code == 200:
        return res.json()
    return []

def insert_weapon_rental(borrower, weapon_name, owner, start_date, end_date):
    data = {
        "borrower": borrower,
        "weapon_name": weapon_name,
        "owner": owner,
        "start_date": str(start_date),
        "end_date": str(end_date)
    }
    res = requests.post(f"{SUPABASE_URL}/rest/v1/Weapon_Rentals", json=data, headers=HEADERS)
     # ✅ 실패 이유 출력
    # if res.status_code != 201:
    #     st.error("❌ 등록 실패 (디버깅 정보)")
    #     st.code(f"Status Code: {res.status_code}\nResponse: {res.text}")
    
    return res.status_code == 201
    
# ✅ 데이터 수정
def update_weapon_rental(row_id, data):
    url = f"{SUPABASE_URL}/rest/v1/Weapon_Rentals?id=eq.{row_id}"
    res = requests.patch(url, json=data, headers=HEADERS)
    return res.status_code == 204

# ✅ 데이터 삭제
def delete_weapon_rental(row_id):
    url = f"{SUPABASE_URL}/rest/v1/Weapon_Rentals?id=eq.{row_id}"
    res = requests.delete(url, headers=HEADERS)
    return res.status_code == 204

# ✅ 드메템 대여 현황 관련 함수
def fetch_dropitem_rentals():
    res = requests.get(f"{SUPABASE_URL}/rest/v1/DropItem_Rentals?select=*&order=id.desc", headers=HEADERS)
    if res.status_code == 200:
        return res.json()
    return []

def insert_dropitem_rental(drop_borrower, dropitem_name, drop_owner, start_date, end_date):
    data = {
        "drop_borrower": drop_borrower,
        "dropitem_name": dropitem_name,
        "drop_owner": drop_owner,
        "start_date": str(start_date),
        "end_date": str(end_date)
    }
    res = requests.post(f"{SUPABASE_URL}/rest/v1/DropItem_Rentals", json=data, headers=HEADERS)
     #✅ 실패 이유 출력
    if res.status_code != 201:
        st.error("❌ 등록 실패 (디버깅 정보)")
        st.code(f"Status Code: {res.status_code}\nResponse: {res.text}")
    
    return res.status_code == 201

#✅ 드메템 대여 계산함수
def get_drop_range(slots):
    try:
        if not slots:
            return ""
        times = sorted(set([s.split()[0] for s in slots.split(",") if s.strip()]))
        return f"{times[0]} ~ {times[-1]}" if times else ""
    except:
        return ""

#✅ 보조무기 대여 계산함수
def get_weapon_range(slots):
    try:
        from datetime import datetime

        # 빈값 방지
        slot_list = [s.strip() for s in slots.split(",") if s.strip()]
        if not slot_list:
            return ""

        # 시작 시간 기준으로 정렬
        sorted_slots = sorted(
            slot_list,
            key=lambda x: datetime.strptime(x.split("~")[0], "%Y-%m-%d %H:%M")
        )

        # 가장 처음과 마지막만 반환
        return f"{sorted_slots[0]} ~ {sorted_slots[-1]}"
    except Exception:
        return ""
    
# ✅ 데이터 수정
def update_dropitem_rental(row_id, data):
    url = f"{SUPABASE_URL}/rest/v1/DropItem_Rentals?id=eq.{row_id}"
    res = requests.patch(url, json=data, headers=HEADERS)
    return res.status_code == 204

# ✅ 데이터 삭제
def delete_dropitem_rental(row_id):
    url = f"{SUPABASE_URL}/rest/v1/DropItem_Rentals?id=eq.{row_id}"
    res = requests.delete(url, headers=HEADERS)
    return res.status_code == 204

# ✅ .xlsx로 파일 저장
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
        writer.close()
    processed_data = output.getvalue()
    return processed_data

# ✅ 유저 회원가입정보 저장
def insert_user(user_id, password, nickname):
    user_data = {
        "user_id": user_id,
        "password": password,
        "nickname": nickname
    }
    res = supabase.table("Users").insert(user_data).execute()
    return bool(res.data)

def authenticate_user(user_id, password):
    response = supabase.table("Users").select("*").eq("user_id", user_id).eq("password", password).execute()
    users = response.data
    if users:
        return users[0]  # 로그인 성공 시 유저 정보 반환
    else:
        return None
    
# ✅ 회원가입시 길드원인지 닉네임 확인 
@st.cache_data
def load_guild_user_nicknames():
    df = pd.read_csv("guild_user.csv")  # 파일 경로에 맞게 수정
    return df["닉네임"].astype(str).str.strip().tolist()

ALLOWED_NICKNAMES = load_guild_user_nicknames()
    
# =====================================================================================#
# ✅ 자동 로그인 시도
query_user_id = st.query_params.get("user_id")
query_token = st.query_params.get("key")

if query_user_id and query_token and "user" not in st.session_state:
    res = supabase.table("Users").select("*") \
        .eq("user_id", query_user_id.strip()) \
        .eq("login_token", query_token.strip()) \
        .execute()

    if res.data:
        user_info = res.data[0]
        st.session_state["user"] = user_info["user_id"]
        st.session_state["nickname"] = user_info["nickname"]
        st.session_state["is_admin"] = user_info["nickname"] in ADMIN_USERS
        st.rerun()
    else:
        st.warning("❌ 자동 로그인 실패")

# ✅ 로그인 & 회원가입 UI
if "user" not in st.session_state:
    st.title("🛡️ 악마길드 관리 시스템")

    if "signup_mode" not in st.session_state:
        st.session_state.signup_mode = False

    if not st.session_state.signup_mode:
        st.subheader("🔐 로그인")

        col_center = st.columns([1, 2, 1])[1]  # 가운데 정렬
        with col_center:
            with st.form("login_form"):
                login_id = st.text_input("아이디", key="login_id", max_chars=20)
                login_pw = st.text_input("비밀번호", type="password", key="login_pw", max_chars=20)
                col1, col2 = st.columns([1, 1])
            with col1:
                login_btn = st.form_submit_button("로그인")
            with col2:
                signup_btn = st.form_submit_button("회원가입")

            if login_btn:
                res = supabase.table("Users").select("*") \
                    .eq("user_id", login_id.strip()) \
                    .eq("password", login_pw.strip()) \
                    .execute()

                if res.data:
                    user_info = res.data[0]
                    login_token = str(uuid.uuid4())
                    supabase.table("Users").update({"login_token": login_token}) \
                        .eq("user_id", login_id.strip()).execute()

                    st.session_state["user"] = user_info["user_id"]
                    st.session_state["nickname"] = user_info["nickname"]
                    st.session_state["is_admin"] = user_info["nickname"] in ADMIN_USERS

                    st.query_params.clear()
                    st.query_params.update(user_id=login_id.strip(), key=login_token)
                    st.rerun()
                else:
                    st.error("❌ 아이디 또는 비밀번호가 올바르지 않습니다.")

            elif signup_btn:
                st.session_state.signup_mode = True
                st.rerun()

        st.stop()

    else:
        st.subheader("📝 회원가입")
        new_id = st.text_input("아이디")
        new_pw = st.text_input("비밀번호", type="password")
        new_nick = st.text_input("본캐 닉네임")

        st.markdown("### 📢 회원가입 주의사항")
        st.info('''
        🔹 자주 사용하는 ID와 PW로 가입하지 마세요. 보안이 취약합니다. \n
        🔹 ID와 PW를 까먹으면 개발자에게 연락하세요(o차월o) \n
        🔹 개발자는 여러분들의 계정 정보를 볼 수 있습니다. 꼭 다른 사이트에서 사용하지 않는 PW로 가입하세요. \n
        🔹 악마길드에 가입한 캐릭터 닉네임으로 가입하세요. \n
        🔹 부길드에 본캐로 가입한 분들은 따로 연락 바랍니다.
        🔹 리팩토링 해주실분 환영합니다.
        ''')

        col1, col2 = st.columns(2)
        with col1:
            if st.button("가입하기"):
                exist = supabase.table("Users").select("user_id").eq("user_id", new_id.strip()).execute()
                if exist.data:
                    st.warning("⚠️ 이미 존재하는 아이디입니다.")
                elif new_nick.strip() not in ALLOWED_NICKNAMES:
                    st.warning("⚠️ 해당 닉네임은 길드에 등록되어 있지 않습니다.")
                else:
                    res = supabase.table("Users").insert({
                        "user_id": new_id.strip(),
                        "password": new_pw.strip(),
                        "nickname": new_nick.strip()
                    }).execute()
                    if res.data:
                        # ✅ Members 테이블에도 자동 등록
                        supabase.table("Members").insert({
                            "nickname": new_nick.strip(),
                            "position": "길드원",  # 기본 직책
                            "active": True,
                            "resume_date": None,
                            "join_date": None,
                            "note": None
                        }).execute()
                        st.success("✅ 회원가입 완료! 로그인으로 이동합니다.")
                        st.session_state.signup_mode = False
                        st.rerun()
                    else:
                        st.error("🚫 회원가입 실패")

        with col2:
            if st.button("↩️ 돌아가기"):
                st.session_state.signup_mode = False
                st.rerun()

        st.stop()

# ✅ 로그인 이후 사이드바
if "user" in st.session_state:
    nickname = st.session_state.get("nickname", "")
    is_admin = st.session_state.get("is_admin", False)

    st.sidebar.markdown(f"👤 로그인: {nickname}")

    if st.sidebar.button("로그아웃"):
        user_id = st.session_state.get("user")
        if user_id:
            supabase.table("Users").update({"login_token": None}) \
                .eq("user_id", user_id).execute()

        st.session_state.clear()
        st.query_params.clear()
        st.rerun()
        
menu_options = []

if st.session_state.get("is_admin"):
    menu_options.extend(["악마 길드원 정보 등록", "악마길드 길컨관리", "부캐릭터 관리"])

# 모든 사용자에게 보이는 메뉴
menu_options.extend(["부캐릭터 등록", "보조대여 신청", "드메템 대여 신청"])

menu = st.sidebar.radio("메뉴", menu_options)


if menu == "악마 길드원 정보 등록":
    st.subheader("👥 길드원 정보 등록")
    members = get_members()
    df = pd.DataFrame(members)
    if not df.empty:
        df["position"] = df["position"].fillna("")
        
        df = df.sort_values(by=["position", "nickname"],
                            key=lambda x: x.map(get_position_priority) if x.name == "position" else x.map(korean_first_sort))
        
        df = df.reset_index(drop=True)
        df["ID"] = df.index + 1
        # ✅ 컬럼명을 한글로 바꾸기
        df_display = df.rename(columns={
            "nickname": "닉네임",
            "position": "직위",
            "active": "활동 여부",
            "resume_date": "활동 재개일",
            "join_date": "가입일",
            "note": "비고",
            "guild_name": "길드명",
            "withdrawn": "탈퇴 여부",
            "withdraw_date": "탈퇴일"
            })

        df_display["탈퇴 여부 ✅"] = df_display["탈퇴 여부"].apply(lambda x: "✅" if str(x).lower() == "true" else "")

        # ✅ 탈퇴 여부 대신 표시용 컬럼으로 보여주기
        st.dataframe(
            df_display[[
                "ID", "닉네임", "직위", "활동 여부", "활동 재개일", "가입일", "비고", "길드명", "탈퇴 여부 ✅", "탈퇴일"
            ]].reset_index(drop=True),
            use_container_width=True
        )
        # ✅ 다운로드 버튼 추가
        excel_data = convert_df_to_excel(df_display)
        st.download_button("📥 길드원 목록 다운로드", data=excel_data, file_name="길드원_목록.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        if is_admin:
            selected_name = st.selectbox("수정 또는 삭제할 닉네임 선택", df["nickname"])
            selected_row = df[df["nickname"] == selected_name].iloc[0]
            with st.form("edit_form"):
                nickname_edit = st.text_input("닉네임", selected_row["nickname"])
                position_edit = st.text_input("직위", selected_row["position"])
                active_edit = st.selectbox("활동 여부", ["활동중", "비활동"], index=0 if selected_row["active"] else 1)
                active1 = True if active_edit == "활동중" else False
                resume_date_edit = st.date_input("활동 재개일", value=pd.to_datetime(selected_row["resume_date"]).date() if selected_row["resume_date"] else None)
                join_date_edit = st.date_input("가입일", value=pd.to_datetime(selected_row["join_date"]).date() if selected_row["join_date"] else None)
                note_edit = st.text_input("비고", selected_row["note"])
                guild_name_edit = st.text_input("길드명", selected_row["guild_name"])
                withdrawn_edit_display = st.selectbox("탈퇴 여부", ["탈퇴함", "여기만한 길드 없다"], index=0 if selected_row["withdrawn"] else 1)
                withdrawn_edit = True if withdrawn_edit_display == "탈퇴함" else False
                withdraw_date_edit = st.date_input("탈퇴일", value=pd.to_datetime(selected_row["withdraw_date"]).date() if selected_row["withdraw_date"] else None)

                update_btn = st.form_submit_button("✏️ 수정")
                delete_btn = st.form_submit_button("🗑 삭제")

                if update_btn:
                    updated_data = {
                        "nickname": nickname_edit,
                        "position": position_edit,
                        "active": active1,
                        "note": note_edit,
                        "guild_name": guild_name_edit,
                        "withdrawn": withdrawn_edit,
                        "resume_date": resume_date_edit.isoformat() if resume_date_edit else None,
                        "join_date": join_date_edit.isoformat() if join_date_edit else None,
                        "withdraw_date": withdraw_date_edit.isoformat() if withdraw_date_edit else None
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
        active_edit1 = st.selectbox("활동 여부", ["활동중", "비활동"])
        active2 = True if active_edit == "활동중" else False
        resume_date = st.date_input("활동 재개일", value=None)
        join_date = st.date_input("가입일", value=None)
        note = st.text_input("비고")
        guild_name = st.text_input("길드명")
        withdrawn_display = st.selectbox("탈퇴 여부", ["탈퇴함", "여기만한 길드 없다"])
        withdrawn =True if withdrawn_display == "탈퇴함" else False
        withdraw_date = st.date_input("탈퇴일", value=None)

        submitted = st.form_submit_button("등록")
        if submitted:
            if nickname_input in df["nickname"].values:
                st.warning(f"⚠️ '{nickname_input}' 닉네임은 이미 등록되어 있습니다.")
            else:
                data = {
                    "nickname": nickname_input,
                    "position": position_input,
                    "active": active2,
                    "note": note,
                    "guild_name": guild_name,
                    "withdrawn": withdrawn,
                    "resume_date": resume_date.isoformat() if resume_date else None,
                    "join_date": join_date.isoformat() if join_date else None,
                    "withdraw_date": withdraw_date.isoformat() if withdraw_date else None
                }
                if insert_member(data):
                    st.success("✅ 길드원이 등록되었습니다!")
                    st.rerun()
                else:
                    st.error("🚫 등록에 실패했습니다. 데이터를 다시 확인해주세요.")
                    
elif menu == "악마길드 길컨관리":
    st.subheader("👥악마길드 길드컨트롤 관리")

    mainmembers = get_mainmembers()
    members = get_members()

    member_dict = {m['nickname']: m['position'] for m in members if m.get('nickname')}
    member_nicknames = sorted(member_dict.keys())

    if mainmembers:
        df_main = pd.DataFrame(mainmembers)
        df_main = df_main.sort_values(
            by=["position", "nickname"],
            key=lambda x: x.map(get_position_priority) if x.name == "position" else x.map(korean_first_sort)
        ).reset_index(drop=True)
        df_main["ID"] = df_main.index + 1
        df_main_display = df_main.rename(columns={
            "nickname": "닉네임",
            "position": "직위",
            "suro": "수로 참여 여부",
            "suro_score": "수로 점수",
            "flag": "플래그 참여 여부",
            "flag_score": "플래그 점수",
            "mission_point": "주간미션포인트",
            "event_sum": "합산",
        })
        st.markdown("### 📋 현재 등록된 메인 캐릭터")
        st.dataframe(
            df_main_display[["ID", "닉네임", "직위", "수로 참여 여부", "수로 점수", "플래그 참여 여부", "플래그 점수", "주간미션포인트", "합산"]],
            use_container_width=True)
        excel_data = convert_df_to_excel(df_main_display)
        st.download_button("📥 메인 캐릭터 다운로드", data=excel_data, file_name="메인캐릭터.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("기록된 길드컨트롤 정보가 없습니다.")

    with st.form("main_member_add_form"):
        st.markdown("### ➕ 메인 캐릭터 등록")

        nickname_input = st.selectbox("닉네임", member_nicknames, key="nickname_input")

        suro_display = st.selectbox("수로 참여 여부", ["참여", "미참"], key="suro_input")
        suro_input = True if suro_display == "참여" else False
        suro_score_input = st.number_input("수로 점수", min_value=0, step=1, key="suro_score_input")

        flag_display = st.selectbox("플래그 참여 여부", ["참여", "미참"], key="flag_input")
        flag_input = True if flag_display == "참여" else False
        flag_score_input = st.number_input("플래그 점수", min_value=0, step=1, key="flag_score_input")

        mission_point_input = st.number_input("주간미션포인트", min_value=0, step=1, key="mission_point_input")
        event_sum_input = st.number_input("합산", min_value=0, step=1, key="event_sum_input")

        submitted = st.form_submit_button("등록")

        if submitted:
            df_main = pd.DataFrame(mainmembers)
            if nickname_input in df_main["nickname"].values:
                st.warning(f"⚠️ '{nickname_input}' 닉네임은 이미 메인 캐릭터로 등록되어 있습니다.")
            else:
                position_value = member_dict.get(nickname_input, "길드원")
                new_data = {
                    "nickname": nickname_input,
                    "position": position_value,
                    "suro": suro_input,
                    "suro_score": suro_score_input,
                    "flag": flag_input,
                    "flag_score": flag_score_input,
                    "mission_point": mission_point_input,
                    "event_sum": event_sum_input
                }
                res = requests.post(f"{SUPABASE_URL}/rest/v1/MainMembers", headers=HEADERS, json=new_data)
                if res.status_code == 201:
                    st.success("✅ 메인 캐릭터가 등록되었습니다!")
                    st.rerun()
                else:
                    st.error(f"❌ 등록 실패! 에러 코드: {res.status_code}")
                    st.code(res.text)

    if is_admin and mainmembers:
        st.markdown("### ✏️ 메인 캐릭터 수정 및 삭제")

        selected = st.selectbox("수정/삭제할 닉네임 선택", [m["nickname"] for m in mainmembers])
        selected_row = [m for m in mainmembers if m["nickname"] == selected][0]

        suro_input_display = st.selectbox("수로 참여 여부", ["참여", "미참"], index=0 if selected_row["suro"] else 1, key="suro_edit")
        suro_input_edit = suro_input_display == "참여"
        suro_score_edit = st.number_input("수로 점수", min_value=0, step=1, value=selected_row["suro_score"], key="suro_score_edit")

        flag_input_display = st.selectbox("플래그 참여 여부", ["참여", "미참"], index=0 if selected_row["flag"] else 1, key="flag_edit")
        flag_input_edit = flag_input_display == "참여"
        flag_score_edit = st.number_input("플래그 점수", min_value=0, step=1, value=selected_row["flag_score"], key="flag_score_edit")

        mission_point_edit = st.number_input("주간미션포인트", min_value=0, step=1, value=selected_row["mission_point"], key="mission_point_edit")
        event_sum_edit = st.number_input("합산", min_value=0, step=1, value=selected_row["event_sum"], key="event_sum_edit")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 수정", key="main_update_btn"):
                updated = {
                    "suro": suro_input_edit,
                    "suro_score": suro_score_edit,
                    "flag": flag_input_edit,
                    "flag_score": flag_score_edit,
                    "mission_point": mission_point_edit,
                    "event_sum": event_sum_edit
                }
                if update_mainember(selected_row["id"], updated):
                    st.success("✅ 수정 완료")
                    st.rerun()
                else:
                    st.error("🚫 수정 실패")

        with col2:
            st.write("🧪 삭제 대상 ID 확인:", selected_row["id"])
            if st.button("🗑 삭제", key="main_delete_btn"):
                if delete_mainmember(selected_row["id"]):
                    st.success("🗑 삭제 완료")
                    st.rerun()
                else:
                    st.error("🚫 삭제 실패")


elif menu == "부캐릭터 관리":
    st.subheader("👥 부캐릭터 등록 및 관리")
    members = get_members()
    main_names = [m['nickname'] for m in members]
    submembers = get_submembers()
    df_sub = pd.DataFrame(submembers)

    with st.form("add_sub_form"):
        selected_main = st.selectbox("본캐 닉네임 선택", main_names)
        guild_name1 = st.text_input("길드 이름")
        sub_name = st.text_input("부캐 이름")
        suro_text = st.selectbox("수로 참여", ["참여", "미참"])
        suro = suro_text == "참여"
        suro_score = st.number_input("수로 점수", min_value=0, step=1)
        flag_text = st.selectbox("플래그 참여", ["참여", "미참"])
        flag = flag_text == "참여"
        flag_score = st.number_input("플래그 점수", min_value=0, step=1)
        mission_point = st.number_input("주간미션포인트", min_value=0, step=1)
        submit_sub = st.form_submit_button("부캐 등록")

        if submit_sub:
            count = sum(df_sub['main_name'] == selected_main) + 1 if not df_sub.empty else 1
            sub_id = f"{selected_main}_{count}"
            if not df_sub[(df_sub["main_name"] == selected_main) & (df_sub["sub_name"] == sub_name)].empty:
                st.warning(f"⚠️ '{selected_main}'의 부캐 '{sub_name}'은 이미 등록되어 있습니다.")
            else:
                data = {
                    "sub_id": sub_id,
                    "guild_name1": guild_name1,
                    "sub_name": sub_name,
                    "main_name": selected_main,
                    "suro": suro,
                    "suro_score": suro_score,
                    "flag": flag,
                    "flag_score": flag_score,
                    "mission_point": mission_point,
                    "created_by": nickname
                }
                if insert_submember(data):
                    st.success(f"✅ {sub_id} 등록 완료")
                    st.rerun()
                else:
                    st.error("🚫 등록 실패")

    st.markdown("---")
    st.subheader("📊 부캐릭터 요약")

    # ✅ 부캐 전체 목록 테이블 추가 (이 위치!)
    st.markdown("### 📑 등록된 전체 부캐릭터 목록")
    if not df_sub.empty:
        df_sub = df_sub.reset_index(drop=True)       # 인덱스 재정렬
        df_sub["ID"] = df_sub.index + 1              # id 다시 부여
        display_all_df = df_sub.rename(columns={
            "ID": "ID",
            "sub_id": "Sub ID",
            "guild_name1": "부캐 길드",
            "sub_name": "부캐 닉네임",
            "main_name": "본캐 닉네임",
            "suro": "수로",
            "suro_score": "수로 점수",
            "flag": "플래그",
            "flag_score": "플래그 점수",
            "mission_point": "주간미션포인트"
        })
        st.dataframe(display_all_df[["ID", "Sub ID", "부캐 길드","부캐 닉네임", "본캐 닉네임","수로", "수로 점수", "플래그", "플래그 점수", "주간미션포인트"]].reset_index(drop=True), use_container_width=True)
        excel_data = convert_df_to_excel(display_all_df)
        st.download_button("📥 부캐릭터 목록 다운로드", data=excel_data, file_name="부캐릭터_목록.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    else:
        st.info("등록된 부캐릭터가 없습니다.")



    selected_main_filter = st.selectbox(
        "🔍 본캐 닉네임으로 검색", ["전체 보기"] + main_names, index=0
    )
   


    if df_sub.empty or "main_name" not in df_sub.columns:
        st.info("등록된 부캐릭터가 없습니다.")
    else:
        for main in main_names:
            if selected_main_filter != "전체 보기" and main != selected_main_filter:
                continue
            df_main = df_sub[df_sub["main_name"] == main]
            if not df_main.empty:
                # ✅ ID 재정렬
                df_main = df_main.reset_index(drop=True)  
                df_main["ID"] = df_main.index + 1
                display_df = df_main.rename(columns={
                    "guild_name1": "부캐 길드",
                    "sub_name": "부캐 닉네임",
                    "suro": "수로",
                    "suro_score": "수로 점수",
                    "flag": "플래그",
                    "flag_score": "플래그 점수",
                    "mission_point": "주간미션포인트"
                })

                st.markdown(f"### 🔹 {main} - 부캐 {len(display_df)}개")
                st.dataframe(display_df[["sub_id","부캐 길드", "부캐 닉네임", "수로", "수로 점수", "플래그", "플래그 점수", "주간미션포인트"]], use_container_width=True)

                if is_admin:
                    with st.expander(f"✏️ {main} 부캐 수정"):
                        sub_names = df_main["sub_name"].tolist()
                        selected_sub_filter = st.selectbox("🔍 수정할 부캐 선택", sub_names, key=f"select_{main}")

                        # ✅ 선택된 부캐만 필터링
                        df_main = df_main[df_main["sub_name"] == selected_sub_filter]
                        sub_row = df_main.iloc[0]
                        sub = sub_row["sub_id"]

                        # 🔽 이 아래부터는 수정 입력 영역
                        new_guild_name = st.text_input("부캐 길드", value=sub_row.get("guild_name1", ""), key=f"guild_{sub}")
                        selected_suro = st.selectbox("수로 참여", ["참여", "미참여"], index=0 if sub_row["suro"] else 1, key=f"suro_select_{sub}")
                        new_suro = selected_suro == "참여"

                        new_suro_score = st.number_input("수로 점수", min_value=0, step=1, value=sub_row.get("suro_score", 0), key=f"suro_score_{sub}")
                        selected_flag = st.selectbox("플래그 참여", ["참여", "미참여"], index=0 if sub_row["flag"] else 1, key=f"flag_select_{sub}")
                        new_flag = selected_flag == "참여"

                        new_flag_score = st.number_input("플래그 점수", min_value=0, step=1, value=sub_row.get("flag_score", 0), key=f"flag_score_{sub}")
                        new_mission = st.number_input("주간미션포인트", min_value=0, step=1, value=sub_row.get("mission_point", 0), key=f"mission_{sub}")

                        if st.button("저장", key=f"save_{sub}"):
                            update_data = {
                                "guild_name1": new_guild_name,
                                "suro": new_suro,
                                "suro_score": new_suro_score,
                                "flag": new_flag,
                                "flag_score": new_flag_score,
                                "mission_point": new_mission
                            }
                            if update_submember(sub, update_data):
                                st.success("✅ 수정 완료")
                                st.rerun()
                            else:
                                st.error("🚫 수정 실패")

                        if st.button("삭제", key=f"delete_{sub}"):
                            if delete_submember(sub):
                                st.success("🗑 삭제 완료")
                                st.rerun()
                            else:
                                st.error("삭제 실패")

elif menu == "부캐릭터 등록":
    st.subheader("👥 부캐릭터 정보 등록")

    nickname = st.session_state["nickname"]
    members = get_members()
    main_names = [m["nickname"] for m in members]
    
    if nickname not in main_names:
        st.warning("⚠️ 본인의 닉네임이 길드원 목록에 없습니다. 관리자에게 문의해주세요.")
        st.stop()

    with st.form("simple_sub_register"):
        sub_name = st.text_input("부캐릭터 닉네임")
        guild_name1 = st.text_input("부캐릭터 길드")

        submit_btn = st.form_submit_button("등록하기")
        if submit_btn:
            submembers = get_submembers()
            df_sub = pd.DataFrame(submembers)
            count = sum(df_sub['main_name'] == nickname) + 1 if not df_sub.empty else 1
            sub_id = f"{nickname}_{count}"

            if not df_sub[(df_sub["main_name"] == nickname) & (df_sub["sub_name"] == sub_name)].empty:
                st.warning(f"⚠️ '{sub_name}'은 이미 등록된 부캐입니다.")
            else:
                new_sub_data = {
                    "sub_id": sub_id,
                    "sub_name": sub_name,
                    "guild_name1": guild_name1,
                    "main_name": nickname,
                    "suro": False,
                    "suro_score": 0,
                    "flag": False,
                    "flag_score": 0,
                    "mission_point": 0,
                    "created_by": nickname
                }
                if insert_submember(new_sub_data):
                    st.success("✅ 부캐릭터가 등록되었습니다!")
                    st.rerun()
                else:
                    st.error("❌ 등록 실패")
    st.warning("⚠️ 허위정보 등록 적발 시 이용에 제한됩니다.")


elif menu == "보조대여 신청":
    st.header("\U0001F6E1️ 보조무기 대여 시스템")
    nickname = st.session_state["nickname"]
    owner = ["자리스틸의왕", "죤냇", "새훨", "나영진", "o차월o"]

    # 이미지 및 직업군 설정
    IMAGE_FOLDER = "보조무기 사진"
    CYGNUS_SHARED = ["나이트워커", "스트라이커", "플레임위자드", "윈드브레이커", "소울마스터"]

    job_data = {
    "전사": ["히어로", "팔라딘", "다크나이트", "소울마스터", "미하일", "아란", "카이저", "제로", "아델"],
    "궁수": ["보우마스터", "신궁", "패스파인더", "윈드브레이커", "메르세데스", "와일드헌터"],
    "법사": ["아크메이지(썬콜)", "아크메이지(불독)", "비숍", "플레임위자드", "에반", "루미너스", "배틀메이지", "키네시스", "일리움"],
    "도적": ["나이트로드", "새도어", "듀얼블레이드", "나이트워커", "팬텀", "카데나", "호영"],
    "해적": ["바이퍼", "캐논슈터", "스트라이커", "메카닉", "엔젤릭버스터"],
    "특수직업": ["데몬어벤져", "제논"]
    }


    # 좌 1/3, 우 2/3 비율로 컬럼 나눔
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("#### 👤 대여자 선택")
        nickname_options = get_all_character_names(nickname)
        selected_borrower = st.selectbox("보조무기 대여자", nickname_options)

        job_group = st.selectbox("🧩 직업군을 선택하세요", list(job_data.keys()))
        selected_job = st.selectbox("🔍 직업을 선택하세요", job_data[job_group])

    with col_right:
        image_path = os.path.join(IMAGE_FOLDER, "시그너스보조.jpg") if selected_job in CYGNUS_SHARED \
                    else os.path.join(IMAGE_FOLDER, f"{selected_job}보조.jpg")
        image_available = os.path.exists(image_path)

        if image_available:
            image = Image.open(image_path)
            w_percent = 1000 / float(image.size[0])  # 더 큰 이미지 표시
            resized_image = image.resize((1000, int(float(image.size[1]) * w_percent)))
            st.image(resized_image, caption=f"{selected_job}의 보조무기")
        else:
            st.warning("⚠️ 보유중인 보조무기가 없어 대여가 불가능합니다.")

    # 무기 대여 데이터 로딩 (한 번만 호출)
    weapon_data = fetch_weapon_rentals()

    if image_available:
        # 날짜 및 시간 슬롯 생성
        today = date.today()
        dates = [today + timedelta(days=i) for i in range(7)]
        weekday_labels = ["월", "화", "수", "목", "금", "토", "일"]
        date_labels = [d.strftime("%m/%d") for d in dates]
        time_slots = [f"{h:02d}:00~{(h+2)%24:02d}:00" for h in range(0, 24, 2)]

        reserved_slots = {
            slot.strip(): row["borrower"]
            for row in weapon_data
            if selected_job in row.get("weapon_name", "")
            for slot in row.get("time_slots", "").split(",")
            if slot.strip()
        }

        st.markdown(f"### ⏰ `{selected_job}`")
        cols = st.columns(len(dates) + 1)
        cols[0].markdown("#### ")
        day_selected = {}

        for i, (day, label) in enumerate(zip([weekday_labels[d.weekday()] for d in dates], date_labels)):
            date_str = str(dates[i])
            reserved_count = sum(1 for t in time_slots if f"{date_str} {t}" in reserved_slots)
            disable_day_checkbox = reserved_count == len(time_slots)
            with cols[i + 1]:
                st.markdown(f"#### {day}", unsafe_allow_html=True)
                st.markdown(f"{label}")
                day_selected[i] = st.checkbox("전체", key=f"day_select_{i}", disabled=disable_day_checkbox)

        existing_slots = {
            slot.strip(): row["borrower"]
            for row in weapon_data
            if selected_job in row.get("weapon_name", "")  # ✅ 무기별 예약 필터
            for slot in row.get("time_slots", "").split(",")
            if slot.strip()
        }


        selection = {}
        for time in time_slots:
            row = st.columns(len(dates) + 1)
            row[0].markdown(f"**{time}**")
            for j, d in enumerate(dates):
                key = f"{selected_job}_{d} {time}"  # ✅ 무기별 고유 키
                date_str = str(d)
                full_key = f"{date_str} {time}"

                borrower = existing_slots.get(full_key)
                if borrower:
                    # 🔒 이미 대여된 시간 → 이름 표시 + 체크박스 비활성화
                    row[j + 1].checkbox(borrower, value=True, key=key, disabled=True)
                else:
                    # ✅ 선택 가능
                    selection[full_key] = row[j + 1].checkbox("", value=day_selected[j], key=key)

        selected_time_slots = [k for k, v in selection.items() if v]
        selected_dates = sorted({datetime.strptime(k.split()[0], "%Y-%m-%d").date() for k in selected_time_slots})

        if st.button("📥 대여 등록"):
            if not selected_time_slots:
                st.warning("❗ 최소 1개 이상의 시간을 선택해주세요.")
            elif len(selected_dates) > 7:
                st.warning("❗ 대여 기간은 최대 7일까지만 선택할 수 있습니다.")
            else:
                weapon_name = selected_job + " 보조무기"
                rental_data = {
                    "borrower": selected_borrower,
                    "weapon_name": weapon_name,
                    "owner": json.dumps(owner),
                    "time_slots": ", ".join(selected_time_slots)
                }
                response = requests.post(f"{SUPABASE_URL}/rest/v1/Weapon_Rentals", headers=HEADERS, json=rental_data)
                if response.status_code == 201:
                    st.success("✅ 대여 등록이 완료되었습니다!")
                    st.rerun()
                else:
                    st.error(f"❌ 등록 실패: {response.status_code}")

   # 1. 무기 대여 데이터 가져오기
    weapon_data = fetch_weapon_rentals()

    # 2. 현재 선택한 직업 기준으로 필터링 (로직은 원본 필드명 사용)
    filtered = [
        r for r in (weapon_data or [])
        if isinstance(r.get("weapon_name"), str)
        and selected_job in r["weapon_name"]
        and "time_slots" in r
    ]

    if filtered:
        # 3. 원본 DataFrame 구성
        df = pd.DataFrame(filtered).sort_values(by="id").reset_index(drop=True)

        # 4. 표시용 복사본 생성 + 컬럼명 변경
        df_display = df.copy()
        df_display["ID"] = df_display.index + 1
        df_display["대여기간"] = df_display["time_slots"].apply(get_weapon_range)
        df_display["대표소유자"] = df_display["owner"].apply(
            lambda x: json.loads(x)[0] if isinstance(x, str) and x.startswith("[") else x
        )
        df_display.rename(columns={
            "borrower": "대여자",
            "weapon_name": "대여 아이템"  # 👈 사용자에겐 이걸 보여줌
        }, inplace=True)

        # 5. 현황 테이블 출력
        st.markdown("### 📄 보조무기 대여 현황")
        st.dataframe(df_display[["ID", "대여자", "대여 아이템", "대표소유자", "대여기간"]], use_container_width=True)

        # 6. 다운로드용 Excel
        excel_df = df_display[["대여자", "대여 아이템", "대표소유자", "대여기간"]].copy()
        excel_data = convert_df_to_excel(excel_df)
        st.download_button(
            label="📅 보조무기 대여 현황 다운로드",
            data=excel_data,
            file_name="보조무기_대여현황.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # 7. 반납 처리 영역
        for _, row in df.iterrows():  # df를 써야 weapon_name, owner 원본 필드 있음
            owners_list = json.loads(row["owner"]) if isinstance(row["owner"], str) and row["owner"].startswith("[") else [row["owner"]]
            borrower_name = row.get("borrower", "(이름 없음)")
            if not borrower_name or str(borrower_name).lower() == "nan":
                borrower_name = "(이름 없음)"

            if nickname in owners_list:
                with st.expander(f"🛡️ '{row['weapon_name']}' - 대여자: {borrower_name}"):
                    st.markdown(f"**📅 대여기간:** `{get_weapon_range(row['time_slots'])}`")
                    st.markdown(f"**소유자:** `{', '.join(owners_list)}`")
                    if st.button("🗑 반납 완료", key=f"weapon_return_{row['id']}"):
                        if delete_weapon_rental(row["id"]):
                            st.success("✅ 반납 완료되었습니다!")
                            st.rerun()
                        else:
                            st.error("❌ 반납 실패! 다시 시도해주세요.")
    else:
        pass



elif menu == "드메템 대여 신청":
    st.header("\U0001F4FF 드메템 대여 시스템")
    nickname = st.session_state["nickname"]
    owners = ["자리스틸의왕", "새훨", "죤냇", "나영진", "o차월o"]

    # 드메템 이미지 폴더 지정
    DROP_IMAGE_FOLDER = "드메템 사진"

    # 드메템 이미지 매핑 (파일명은 세트명 기준으로 미리 저장 필요)
    dropitem_image_map = {
        "보스 드드셋": "보스 드드셋.jpg",
        "사냥 드메셋 I": "사냥 드메셋 I.jpg",
        "사냥 드메셋 II": "사냥 드메셋 II.jpg",
    }

    # 좌 1/3, 우 2/3 비율로 나누기
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("#### 👤 대여자 선택")
        nickname_options = get_all_character_names(nickname)
        selected_borrower = st.selectbox("드메템 대여자", nickname_options)

        item_options = list(dropitem_image_map.keys())
        selected_item = st.selectbox("대여할 드메템 세트를 선택하세요", item_options)

    with col_right:
        selected_image_name = dropitem_image_map.get(selected_item)
        if selected_image_name:
            image_path = os.path.join(DROP_IMAGE_FOLDER, selected_image_name)
            if os.path.exists(image_path):
                image = Image.open(image_path)
                w_percent = 1000 / float(image.size[0])  # 이미지 더 크게
                resized_image = image.resize((1000, int(float(image.size[1]) * w_percent)))
                st.image(resized_image, caption=f"{selected_item} 이미지")
            else:
                st.warning("⚠️ 해당 드메셋 이미지가 존재하지 않습니다.")

    today = date.today()
    dates = [today + timedelta(days=i) for i in range(7)]
    date_labels = [d.strftime("%m/%d") for d in dates]
    day_names = ["월", "화", "수", "목", "금", "토", "일"]
    weekday_labels = [day_names[d.weekday()] for d in dates]
    time_slots = ["00:00~24:00"]

    drop_data = fetch_dropitem_rentals()
    filtered_data = [row for row in drop_data if row["dropitem_name"] == selected_item]

    reserved_slots = {
        slot.strip(): row["drop_borrower"]
        for row in filtered_data
        for slot in row.get("time_slots", "").split(",")
        if slot.strip()
    }

    st.markdown(f"### ⏰ `{selected_item}`")
    # 📅 날짜/요일 헤더 출력
    cols = st.columns(len(dates) + 1)
    cols[0].markdown("#### ")
    for i, (day, label) in enumerate(zip(weekday_labels, date_labels)):
        with cols[i + 1]:
            st.markdown(f"#### {day}", unsafe_allow_html=True)
            st.markdown(f"{label}")
    selection = {}
    for time in time_slots:
        row = st.columns(len(dates) + 1)
        row[0].markdown(f"**{time}**")
        for j, d in enumerate(dates):
            key = f"{d} {time}"
            if key in reserved_slots:
                label = reserved_slots[key]
                selection[key] = row[j + 1].checkbox(label, value=True, key=key, disabled=True)
            else:
                selection[key] = row[j + 1].checkbox("", key=key)

    selected_time_slots = [k for k, v in selection.items() if v]
    selected_dates = sorted({datetime.strptime(k.split()[0], "%Y-%m-%d").date() for k in selected_time_slots})

    if st.button("📥 대여 등록"):
        if not selected_time_slots:
            st.warning("❗ 최소 1개 이상의 날짜를 선택해주세요.")
        elif len(selected_dates) > 7:
            st.warning("❗ 대여 기간은 최대 7일까지만 선택할 수 있습니다.")
        else:
            rental_data = {
                "drop_borrower": selected_borrower,
                "dropitem_name": selected_item,
                "drop_owner": json.dumps(owners),
                "time_slots": ", ".join(selected_time_slots)
            }
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/DropItem_Rentals",
                headers=HEADERS,
                json=rental_data
            )
            if response.status_code == 201:
                st.success("✅ 대여 등록이 완료되었습니다!")
                st.rerun()
            else:
                st.error(f"❌ 등록 실패: {response.status_code}")
                st.code(response.text)


    # 📊 대여 현황 테이블 표시
    if drop_data:
        # ✅ 필터링
        filtered = [r for r in drop_data if r.get("dropitem_name") == selected_item]

        # ✅ drop_data가 있고, 'dropitem_name' & 'time_slots' 조건을 만족할 때만 필터링
        if drop_data:
            filtered = [
                r for r in drop_data
                if r.get("dropitem_name") == selected_item and "time_slots" in r
            ]

            if filtered:
                # ✅ 이후 DataFrame 처리
                df = pd.DataFrame(filtered).sort_values(by="id").reset_index(drop=True)
                df["ID"] = df.index + 1

                def get_drop_range(slots):
                    try:
                        times = sorted(set([s.split()[0] for s in slots.split(",")]))
                        return f"{times[0]} ~ {times[-1]}" if times else ""
                    except:
                        return ""

                df["대여기간"] = df["time_slots"].apply(get_drop_range)
                df["대표소유자"] = df["drop_owner"].apply(lambda x: json.loads(x)[0] if isinstance(x, str) and x.startswith("[") else x)
                df.rename(columns={
                    "drop_borrower": "대여자",
                    "dropitem_name": "대여 아이템"
                }, inplace=True)

                st.markdown("### 📄 드메템 대여 현황")
                st.dataframe(df[["ID", "대여자", "대여 아이템", "대표소유자", "대여기간"]], use_container_width=True)

                # 엑셀용 DataFrame 준비
                excel_df = df[["대여자", "대여 아이템", "대표소유자", "대여기간"]].copy()

                # 변환된 데이터로 엑셀 저장
                excel_data = convert_df_to_excel(excel_df)
                st.download_button("📥 드메템 대여 현황 다운로드", data=excel_data, file_name="드메템_대여현황.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                # ✅ 반납 처리 UI
                for _, row in df.iterrows():
                    owners_list = json.loads(row["drop_owner"]) if isinstance(row["drop_owner"], str) and row["drop_owner"].startswith("[") else [row["drop_owner"]]
                    borrower_name = row.get("drop_borrower", "(이름 없음)")
                    if not borrower_name or str(borrower_name).lower() == "nan":
                        borrower_name = "(이름 없음)"

                    if nickname in owners_list:
                        with st.expander(f"\U0001F4FF '{row['대여 아이템']}' - 대여자: {borrower_name}"):
                            st.markdown(f"**📅 대여기간:** `{row['time_slots']}`")
                            st.markdown(f"**소유자:** `{', '.join(owners_list)}`")
                            if st.button("🗑 반납 완료", key=f"drop_return_{row['id']}"):
                                if delete_dropitem_rental(row["id"]):
                                    st.success("✅ 반납 완료되었습니다!")
                                    st.rerun()
                                else:
                                    st.error("❌ 반납 실패! 다시 시도해주세요.")
            else:
                pass
            