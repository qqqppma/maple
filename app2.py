import streamlit as st
import requests
import pandas as pd
from datetime import date,datetime
import re
import urllib.parse

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

ADMIN_USERS = ["자리스틸의왕", "나영진", "죤냇", "o차월o"]

# ✅ Supabase 함수
def get_members():
    res = requests.get(f"{SUPABASE_URL}/rest/v1/Members?select=*&order=position.desc", headers=HEADERS)
    if res.status_code == 200:
        return res.json()
    return []

def insert_member(data):
    res = requests.post(f"{SUPABASE_URL}/rest/v1/Members", headers=HEADERS, json=data)
    return res.status_code == 201

def update_member(member_id, data):
    res = requests.patch(f"{SUPABASE_URL}/rest/v1/Members?id=eq.{member_id}", headers=HEADERS, json=data)
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
    res = requests.patch(f"{SUPABASE_URL}/rest/v1/MainMembers?sub_id=eq.{member_id}", headers=HEADERS, json=data)
    return res.status_code == 204

def delete_mainmember(member_id):
    res = requests.delete(f"{SUPABASE_URL}/rest/v1/MainMembers?sub_id=eq.{member_id}", headers=HEADERS)
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

# ✅ 로그인 처리 (주소창 유지 + 로그아웃 + 디코딩 적용)
st.title("\U0001F6E1️ 악마길드 관리 시스템")

query_params = st.query_params
if "user" not in st.session_state:
    nickname_encoded = query_params.get("nickname", None)
    key_encoded = query_params.get("key", None)

    # ✅ 자동 로그인 조건 강화
    if nickname_encoded and key_encoded:
        login_name = urllib.parse.unquote(nickname_encoded)
        login_pw = urllib.parse.unquote(key_encoded)

        try:
            csv_url = "https://raw.githubusercontent.com/qqqppma/maple/main/guild_user.csv"
            df_users = pd.read_csv(csv_url, encoding="utf-8-sig")

            df_users["닉네임"] = df_users["닉네임"].astype(str).str.strip()
            df_users["비밀번호"] = df_users["비밀번호"].astype(str).str.strip()

            matched = df_users[
                (df_users["닉네임"] == login_name.strip()) &
                (df_users["비밀번호"] == login_pw.strip())
            ]

            if not matched.empty:
                st.session_state["user"] = login_name
                st.session_state["is_admin"] = login_name in ADMIN_USERS
                st.query_params.update(nickname=login_name, key=login_pw)
                st.rerun()
            else:
                # 자동 로그인 실패 시 조용히 실패
                st.stop()
        except Exception as e:
            st.error(f"CSV 로드 오류: {e}")
            st.stop()

if "user" not in st.session_state:
    st.subheader("\U0001F512 로그인")
    login_name = st.text_input("닉네임")
    login_pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        try:
            csv_url = "https://raw.githubusercontent.com/qqqppma/maple/main/guild_user.csv"
            df_users = pd.read_csv(csv_url, encoding="utf-8-sig")

            df_users["닉네임"] = df_users["닉네임"].astype(str).str.strip()
            df_users["비밀번호"] = df_users["비밀번호"].astype(str).str.strip()

            matched = df_users[
                (df_users["닉네임"] == login_name.strip()) &
                (df_users["비밀번호"] == login_pw.strip())
            ]

            if not matched.empty:
                st.session_state["user"] = login_name
                st.session_state["is_admin"] = login_name in ADMIN_USERS
                st.query_params.update(nickname=login_name, key=login_pw)
                st.rerun()
            else:
                st.error("❌ 일치하는 사용자 정보가 없습니다.")
        except Exception as e:
            st.error(f"CSV 로드 오류: {e}")
    st.stop()

nickname = st.session_state["user"]
is_admin = st.session_state["is_admin"]

st.sidebar.write(f"👤 로그인: {nickname}")
if st.sidebar.button("로그아웃"):
    st.session_state.clear()
    st.query_params.clear()
    st.query_params
    st.rerun()

nickname = st.session_state["user"]
is_admin = st.session_state["is_admin"]

menu = st.sidebar.radio("메뉴", ["악마 길드원 정보 등록", "악마길드 길컨관리", "부캐릭터 관리","보조대여 관리","드메템 대여 관리"])

if menu == "악마 길드원 정보 등록":
    st.subheader("👥 길드원 정보 등록")
    members = get_members()
    df = pd.DataFrame(members)
    if not df.empty:
        df["position"] = df["position"].fillna("")
        
        df = df.sort_values(by=["position", "nickname"],
                            key=lambda x: x.map(get_position_priority) if x.name == "position" else x.map(korean_first_sort))
        
        df = df.reset_index(drop=True)
        df["id"] = df.index + 1
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

        st.dataframe(df_display.reset_index(drop=True))

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
                withdrawn_edit_display = st.selectbox("탈퇴 여부", ["탈퇴함", "여기만한 길드 없다"], index=1 if selected_row["withdrawn"] else 0)
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
    # st.write("📦 가져온 mainmembers:", mainmembers)

    members = get_members()

    # ✅ 오타 수정 + 닉네임-직위 dict 생성
    member_dict = {m['nickname']: m['position'] for m in members if m.get('nickname')}
    member_nicknames = sorted(member_dict.keys())

    if mainmembers:
        df_main = pd.DataFrame(mainmembers)
        # ✅ ID를 자동으로 다시 부여
        df_main = df_main.sort_values(
        by=["position", "nickname"],
        key=lambda x: x.map(get_position_priority) if x.name == "position" else x.map(korean_first_sort)
        ).reset_index(drop=True)
        df_main["id"] = df_main.index + 1
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
        st.dataframe(df_main_display.reset_index(drop=True))
    else:
        st.info("기록된 길드컨트롤 정보가 없습니다.")

    # ✅ 캐릭터 등록 & 수정 폼 (닉네임 선택 시 직위 자동 표시)
    with st.form("main_member_add_form"):
        st.markdown("### ➕ 메인 캐릭터 등록")

        nickname_input = st.selectbox("닉네임", member_nicknames, key="nickname_input")
        # ✅ 직위 DataFrame 방식으로 가져오기
        df_members = pd.DataFrame(members)
        row = df_members[df_members["nickname"] == nickname_input]
        if not row.empty:
            position_value = row.iloc[0]["position"]
        else:
            position_value = "직위 정보 없음"
        st.markdown(f"**직위:** `{position_value}`")

        suro_display = st.selectbox("수로 참여 여부", ["참여", "미참"], key="suro_input")
        suro_input = True if suro_display == "참여" else False
        suro_score_input = st.number_input("수로 점수", min_value=0, step=1, key="suro_score_input")

        flag_display = st.selectbox("플래그 참여 여부", ["참여", "미참"], key="flag_input")
        flag_input = True if suro_display == "참여" else False
        flag_score_input = st.number_input("플래그 점수", min_value=0, step=1, key="flag_score_input")

        mission_point_input = st.number_input("주간미션포인트", min_value=0, step=1, key="mission_point_input")
        event_sum_input = st.number_input("합산", min_value=0, step=1, key="event_sum_input")

        submitted = st.form_submit_button("등록")

        if submitted:
            if nickname_input in df_main["nickname"].values:
                st.warning(f"⚠️ '{nickname_input}' 닉네임은 이미 메인 캐릭터로 등록되어 있습니다.")
            else:
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

    # ✅ 수정/삭제 섹션 (등록 폼 밖에서 별도로 처리)
    if is_admin and mainmembers:
        st.markdown("### ✏️ 메인 캐릭터 수정 및 삭제")

        selected = st.selectbox("수정/삭제할 닉네임 선택", [m["nickname"] for m in mainmembers])
        selected_row = [m for m in mainmembers if m["nickname"] == selected][0]

        suro_input_display = st.selectbox("수로 참여 여부", ["참여", "미참"],index=0 if selected_row["suro"] else 1,key="suro_edit")
        suro_input_edit = True if suro_input_display == "참여" else False
        suro_score_edit = st.number_input("수로 점수", min_value=0, step=1,value=selected_row["suro_score"],key="suro_score_edit")

        flag_input_display = st.selectbox("플래그 참여 여부", ["참여", "미참"],index=0 if selected_row["flag"] else 1, key="flag_edit")
        flag_input_edit = True if flag_input_display == "참여" else False
        flag_score_edit = st.number_input("플래그 점수", min_value=0, step=1, value=selected_row["flag_score"], key="flag_score_edit")

        mission_point_edit = st.number_input("주간미션포인트", min_value=0, step=1, value=selected_row["mission_point"],key="mission_point_edit")
        event_sum_edit = st.number_input("합산", min_value=0, step=1, value=selected_row["event_sum"],key="event_sum_edit")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 수정", key="main_update_btn"):
                updated = {
                    "suro": bool(suro_input_edit),
                    "suro_score": int(suro_score_edit) if suro_score_edit is not None else 0,
                    "flag": bool(flag_input_edit),
                    "flag_score": int(flag_score_edit) if flag_score_edit is not None else 0,
                    "mission_point": int(mission_point_edit) if mission_point_edit is not None else 0,
                    "event_sum": int(event_sum_edit) if event_sum_edit is not None else 0
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
        df_sub["id"] = df_sub.index + 1              # id 다시 부여
        display_all_df = df_sub.rename(columns={
            "id": "ID",
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
        st.dataframe(display_all_df[["ID", "Sub ID", "부캐 길드","부캐 닉네임", "본캐 닉네임","수로", "수로 점수", "플래그", "플래그 점수", "주간미션포인트"]].reset_index(drop=True))
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
                df_main["id"] = df_main.index + 1
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
                st.dataframe(display_df[["sub_id","부캐 길드", "부캐 닉네임", "수로", "수로 점수", "플래그", "플래그 점수", "주간미션포인트"]])

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

#보조 대여 관리 코드
elif menu == "보조대여 관리":
       
    # ✅ Streamlit UI
    st.header("🛡️ 보조무기 대여 현황")

    # 📋 등록 폼
    with st.form("register_form"):
        st.markdown("### ➕ 대여 등록")
        borrower = st.text_input("대여자 닉네임")
        weapon_name = st.text_input("대여 보조무기 이름")
        owner = st.text_input(" 소유자 닉네임")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("대여 시작일", value=date.today())
        with col2:
            end_date = st.date_input("대여 종료일", value=date.today())

        if st.form_submit_button("등록"):
            if insert_weapon_rental(borrower, weapon_name, owner, start_date, end_date):
                st.success("✅ 등록 완료")
                st.rerun()
            else:
                st.error("❌ 등록 실패")

     # 📊 데이터 조회 및 표시
    data = fetch_weapon_rentals()
    if data:
        df = pd.DataFrame(data)
        df = df.sort_values(by="id").reset_index(drop=True)

        # 표시용 ID 및 대여기간 계산
        df["ID"] = df.index + 1
        df["대여기간"] = df.apply(
            lambda row: f"{row['start_date']} ~ {row['end_date']} ({(pd.to_datetime(row['end_date']) - pd.to_datetime(row['start_date'])).days}일)",
            axis=1
        )

        # 📄 대여 목록 출력
        st.markdown("### 📄 대여 목록")
        st.dataframe(df[["ID", "borrower", "weapon_name", "owner", "대여기간"]].rename(columns={
            "borrower": "대여자",
            "weapon_name": "보조무기",
            "owner": "소유자"
        }))
        # ✏️ 수정 & 삭제 대상 선택
        st.markdown("### ✏️ 수정 또는 삭제")
        selected = st.selectbox("수정/삭제할 표시 ID 선택", df["ID"])
        selected_row = df[df["ID"] == selected].iloc[0]
        actual_id = selected_row["id"]

        # ✍️ 수정 폼
        with st.form("edit_form"):
            st.markdown("**수정할 내용 입력:**")
            edit_borrower = st.text_input("대여자", value=selected_row["borrower"])
            edit_weapon = st.text_input("보조무기 이름", value=selected_row["weapon_name"])
            edit_owner = st.text_input("소유자", value=selected_row["owner"])
            col1, col2 = st.columns(2)
            with col1:
                edit_start = st.date_input("시작일", value=pd.to_datetime(selected_row["start_date"]))
            with col2:
                edit_end = st.date_input("종료일", value=pd.to_datetime(selected_row["end_date"]))
            if st.form_submit_button("수정"):
                updated = update_weapon_rental(actual_id, {
                    "borrower": edit_borrower,
                    "weapon_name": edit_weapon,
                    "owner": edit_owner,
                    "start_date": str(edit_start),
                    "end_date": str(edit_end)
                })
                if updated:
                    st.success("✏️ 수정 완료")
                    st.rerun()
                else:
                    st.error("수정 실패")

        # 🗑 삭제 버튼
        if st.button("❌ 삭제"):
            if delete_weapon_rental(actual_id):
                st.success("🗑 삭제 완료")
                st.rerun()
            else:
                st.error("삭제 실패")

 #드메 대여 관리 코드
elif menu == "드메템 대여 관리":
       
    # ✅ Streamlit UI
    st.header("🛡️ 드메템 대여 현황")

    # 📋 등록 폼
    with st.form("register_form"):
        st.markdown("### ➕ 대여 등록")
        drop_borrower = st.text_input("대여자 닉네임")
        dropitem_name = st.text_input("대여 드메템 목록")
        drop_owner = st.text_input(" 소유자 닉네임")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("대여 시작일", value=date.today())
        with col2:
            end_date = st.date_input("대여 종료일", value=date.today())

        if st.form_submit_button("등록"):
            if insert_dropitem_rental(drop_borrower, dropitem_name, drop_owner, start_date, end_date):
                st.success("✅ 등록 완료")
                st.rerun()
            else:
                st.error("❌ 등록 실패")

     # 📊 데이터 조회 및 표시
    data = fetch_dropitem_rentals()
    if data:
        df = pd.DataFrame(data)
        df = df.sort_values(by="id").reset_index(drop=True)

        # 표시용 ID 및 대여기간 계산
        df["ID"] = df.index + 1
        df["대여기간"] = df.apply(
            lambda row: f"{row['start_date']} ~ {row['end_date']} ({(pd.to_datetime(row['end_date']) - pd.to_datetime(row['start_date'])).days}일)",
            axis=1
        )

        # 📄 대여 목록 출력
        st.markdown("### 📄 대여 목록")
        st.dataframe(df[["ID", "drop_borrower", "dropitem_name", "drop_owner", "대여기간"]].rename(columns={
            "drop_borrower": "대여자",
            "dropitem_name": "보조무기",
            "drop_owner": "소유자"
        }))
        # ✏️ 수정 & 삭제 대상 선택
        st.markdown("### ✏️ 수정 또는 삭제")
        selected = st.selectbox("수정/삭제할 표시 ID 선택", df["ID"])
        selected_row = df[df["ID"] == selected].iloc[0]
        actual_id = selected_row["id"]

        # ✍️ 수정 폼
        with st.form("edit_form"):
            st.markdown("**수정할 내용 입력:**")
            edit_drop_borrower = st.text_input("대여자", value=selected_row["drop_borrower"])
            edit_dropitem = st.text_input("드메템 이름", value=selected_row["dropitem_name"])
            edit_drop_owner = st.text_input("소유자", value=selected_row["drop_owner"])
            col1, col2 = st.columns(2)
            with col1:
                edit_start = st.date_input("시작일", value=pd.to_datetime(selected_row["start_date"]))
            with col2:
                edit_end = st.date_input("종료일", value=pd.to_datetime(selected_row["end_date"]))
            if st.form_submit_button("수정"):
                updated = update_weapon_rental(actual_id, {
                    "drop_borrower": edit_drop_borrower,
                    "dropitem_name": edit_dropitem,
                    "drop_owner": edit_drop_owner,
                    "start_date": str(edit_start),
                    "end_date": str(edit_end)
                })
                if updated:
                    st.success("✏️ 수정 완료")
                    st.rerun()
                else:
                    st.error("수정 실패")

        # 🗑 삭제 버튼
        if st.button("❌ 삭제"):
            if delete_dropitem_rental(actual_id):
                st.success("🗑 삭제 완료")
                st.rerun()
            else:
                st.error("삭제 실패")
