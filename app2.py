import streamlit as st
import requests
import pandas as pd
from datetime import date
import re

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
    res = requests.get(f"{SUPABASE_URL}/rest/v1/Members?select=*&order=id.desc", headers=HEADERS)
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

# ✅ Supabase 부캐 테이블 관련 함수
def insert_submember(data):
    res = requests.post(f"{SUPABASE_URL}/rest/v1/SubMembers", headers=HEADERS, json=data)
    return res.status_code == 201

def get_submembers():
    res = requests.get(f"{SUPABASE_URL}/rest/v1/SubMembers?select=*&order=sub_id.asc", headers=HEADERS)
    if res.status_code == 200:
        return res.json()
    return []

def update_submember(sub_id, data):
    res = requests.patch(f"{SUPABASE_URL}/rest/v1/SubMembers?sub_id=eq.{sub_id}", headers=HEADERS, json=data)
    return res.status_code == 204

# ✅ 로그인 처리
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

nickname = st.session_state["user"]
is_admin = st.session_state["is_admin"]

menu = st.sidebar.radio("메뉴", ["길드원 등록", "부캐릭터 관리","메뉴3","메뉴4"])
st.sidebar.write(f"👉 선택된 메뉴: {menu}")

if menu == "길드원 등록":
    st.subheader("👥 길드원 정보 등록")
    members = get_members()
    df = pd.DataFrame(members)
    if not df.empty:
        df["position"] = df["position"].fillna("")
        def get_position_priority(pos):
            priority = {"길드마스터": 1, "부마스터": 2, "길드원": 3}
            return priority.get(pos, 99)
        def korean_first_sort(value):
            return (not bool(re.match(r"[가-힣]", str(value)[0])), value)
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
                resume_date_edit = st.date_input("활동 재개일", value=pd.to_datetime(selected_row["resume_date"]).date() if selected_row["resume_date"] else None)
                join_date_edit = st.date_input("가입일", value=pd.to_datetime(selected_row["join_date"]).date() if selected_row["join_date"] else None)
                note_edit = st.text_input("비고", selected_row["note"])
                guild_name_edit = st.text_input("길드명", selected_row["guild_name"])
                withdrawn_edit = st.selectbox("탈퇴 여부", [False, True], index=1 if selected_row["withdrawn"] else 0)
                withdraw_date_edit = st.date_input("탈퇴일", value=pd.to_datetime(selected_row["withdraw_date"]).date() if selected_row["withdraw_date"] else None)

                update_btn = st.form_submit_button("✏️ 수정")
                delete_btn = st.form_submit_button("🗑 삭제")

                if update_btn:
                    updated_data = {
                        "nickname": nickname_edit,
                        "position": position_edit,
                        "active": active_edit,
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
        active = st.selectbox("활동 여부", [True, False])
        resume_date = st.date_input("활동 재개일", value=None)
        join_date = st.date_input("가입일", value=None)
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

elif menu == "부캐릭터 관리":
    st.subheader("👥 부캐릭터 등록 및 관리")
    members = get_members()
    main_names = [m['nickname'] for m in members]
    submembers = get_submembers()
    df_sub = pd.DataFrame(submembers)

    with st.form("add_sub_form"):
        selected_main = st.selectbox("본캐 닉네임 선택", main_names)
        sub_name = st.text_input("부캐 이름")
        suro = st.checkbox("수로 참여")
        suro_score = st.number_input("수로 점수", min_value=0, step=1)
        flag = st.text_input("플래그 종류")
        flag_score = st.number_input("플래그 점수", min_value=0, step=1)
        mission_point = st.number_input("주간미션포인트", min_value=0, step=1)
        submit_sub = st.form_submit_button("부캐 등록")

        if submit_sub:
            count = sum(df_sub['main_name'] == selected_main) + 1 if not df_sub.empty else 1
            sub_id = f"{selected_main}_{count}"
            data = {
                "sub_id": sub_id,
                "sub_name": sub_name,
                "main_name": selected_main,
                "suro": suro,
                "suro_score": suro_score,
                "flag": flag,
                "flag_socre": flag_score,
                "mission_poin": mission_point,
                "created_by": nickname
            }
            if insert_submember(data):
                st.success(f"✅ {sub_id} 등록 완료")
                st.rerun()
            else:
                st.error("🚫 등록 실패")

    st.markdown("---")
    st.subheader("📊 부캐릭터 요약")

    if not df_sub.empty:
        display_df = df_sub.rename(columns={
            "suro": "수로",
            "suro_score": "수로 점수",
            "flag": "플래그",
            "flag_socre": "플래그 점수",
            "mission_poin": "주간미션포인트"
        })
        for main in main_names:
            df_main = display_df[display_df["main_name"] == main]
            if not df_main.empty:
                st.markdown(f"### 🔹 {main} - 부캐 {len(df_main)}개")
                st.dataframe(df_main[["sub_id", "sub_name", "수로", "수로 점수", "플래그", "플래그 점수", "주간미션포인트"]])

                if is_admin:
                    with st.expander(f"✏️ {main} 부캐 수정"):
                        selected_sub = df_main["sub_id"].tolist()
                        for sub in selected_sub:
                            sub_row = df_sub[df_sub["sub_id"] == sub].iloc[0]
                            new_suro = st.checkbox("수로 참여", value=sub_row["suro"], key=f"suro_{sub}")
                            new_suro_score = st.number_input("수로 점수", min_value=0, step=1, value=sub_row["suro_score"] or 0, key=f"suro_score_{sub}")
                            new_flag = st.text_input("플래그 종류", value=sub_row["flag"], key=f"flag_{sub}")
                            new_flag_score = st.number_input("플래그 점수", min_value=0, step=1, value=sub_row["flag_socre"] or 0, key=f"flag_score_{sub}")
                            new_mission = st.number_input("주간미션포인트", min_value=0, step=1, value=sub_row["mission_poin"] or 0, key=f"mission_{sub}")
                            if st.button("저장", key=f"save_{sub}"):
                                update_data = {
                                    "suro": new_suro,
                                    "suro_score": new_suro_score,
                                    "flag": new_flag,
                                    "flag_socre": new_flag_score,
                                    "mission_poin": new_mission
                                }
                                if update_submember(sub, update_data):
                                    st.success("✅ 수정 완료")
                                    st.rerun()
                                else:
                                    st.error("🚫 수정 실패")
