import streamlit as st
import requests
import pandas as pd
from datetime import date,datetime
import re
import urllib.parse
import io
import os
from PIL import Image
from datetime import date, timezone, timedelta
from supabase import create_client, Client
import json
import uuid
from streamlit.components.v1 import html
from utils.time_grid import generate_slot_table
import bcrypt
import textwrap
import codecs
#=============위치고정=============================================#
st.set_page_config(page_title="악마길드 관리 시스템", layout="wide")
#=============위치고정=============================================#
##
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


ADMIN_USERS = ["자리스틸의왕", "나영진", "죤냇", "o차월o"]
guild_options = ["악질", "악먀"]  # 혹은 DB나 리스트에서 불러오기

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

def update_mainmember(member_id, data):
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
def get_drop_range(time_slots_str):
    if not time_slots_str:
        return ""

    slots = sorted([
        datetime.strptime(s.strip(), "%Y-%m-%d %H:%M")
        for s in time_slots_str.split(",")
        if s.strip()
    ])

    if not slots:
        return ""

    weekday_map = ["월", "화", "수", "목", "금", "토", "일"]

    def format_time(dt):
        hour = dt.hour
        if hour == 0:
            return "0시 (AM)"
        elif 1 <= hour < 12:
            return f"{hour}시 (AM)"
        elif hour == 12:
            return "12시 (PM)"
        else:
            return f"{hour - 12}시 (PM)"

    result = []
    start = slots[0]
    prev = slots[0]

    for current in slots[1:]:
        if current - prev != timedelta(hours=24):  # 드메셋은 하루 단위
            end = prev + timedelta(hours=24)
            start_str = f"{start.month}월 {start.day}일 ({weekday_map[start.weekday()]}) {format_time(start)}"
            end_str = f"{end.month}월 {end.day}일 ({weekday_map[end.weekday()]}) {format_time(end)}"
            result.append(f"{start_str} ~ {end_str}")
            start = current
        prev = current

    # 마지막 구간
    end = prev + timedelta(hours=24)
    start_str = f"{start.month}월 {start.day}일 ({weekday_map[start.weekday()]}) {format_time(start)}"
    end_str = f"{end.month}월 {end.day}일 ({weekday_map[end.weekday()]}) {format_time(end)}"
    result.append(f"{start_str} ~ {end_str}")

    return " / ".join(result)


#✅ 보조무기 대여 계산함수
def get_weapon_range(time_slots_str):
    if not time_slots_str:
        return ""

    slots = sorted([
        datetime.strptime(s.strip(), "%Y-%m-%d %H:%M")
        for s in time_slots_str.split(",")
        if s.strip()
    ])

    if not slots:
        return ""

    weekday_map = ["월", "화", "수", "목", "금", "토", "일"]

    def format_time(dt):
        hour = dt.hour
        if hour == 0:
            return "0시 (AM)"
        elif 1 <= hour < 12:
            return f"{hour}시 (AM)"
        elif hour == 12:
            return "12시 (PM)"
        else:
            return f"{hour - 12}시 (PM)"

    result = []
    start = slots[0]
    prev = slots[0]

    for current in slots[1:]:
        if current - prev != timedelta(hours=2):
            end = prev + timedelta(hours=2)
            start_str = f"{start.month}월 {start.day}일 ({weekday_map[start.weekday()]}) {format_time(start)}"
            end_str = f"{end.month}월 {end.day}일 ({weekday_map[end.weekday()]}) {format_time(end)}"
            result.append(f"{start_str} ~ {end_str}")
            start = current
        prev = current

    # 마지막 구간 추가
    end = prev + timedelta(hours=2)
    start_str = f"{start.month}월 {start.day}일 ({weekday_map[start.weekday()]}) {format_time(start)}"
    end_str = f"{end.month}월 {end.day}일 ({weekday_map[end.weekday()]}) {format_time(end)}"
    result.append(f"{start_str} ~ {end_str}")

    return " / ".join(result)


    
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

#====================================================================================#
# 🔐 Nexon API 설정
API_KEY = st.secrets["NEXON_API_KEY"]
NEXON_HEADERS = {"x-nxopen-api-key": API_KEY}

# 🧩 장비 부위별 위치 정의
EQUIP_POSITIONS = {
    "무기": "left", "보조무기": "right", "엠블렘": "right",
    "펜던트": "left", "펜던트2": "left", "반지1": "left", "반지2": "left", "반지3": "right", "반지4": "right",
    "상의": "center", "하의": "center", "신발": "center", "장갑": "center", "망토": "center", "모자": "center",
    "눈장식": "right", "얼굴장식": "right", "귀고리": "right", "뱃지": "right", "벨트": "right",
    "포켓 아이템": "right"
}

# ✅ 서버 한글명 → 영문 코드 매핑
SERVER_NAME_MAP = {
    "스카니아": "SCANIA",
    "베라": "BERA",
    "루나": "LUNA",
    "엘리시움": "ELYSIUM",
    "크로아": "CROA",
    "유니온": "UNION",
    "제니스": "ZENITH",
    "이노시스": "INNOSIS",
    "레드": "RED",
    "오로라": "AURORA",
    "아케인": "ARCADIA",
    "노바": "NOVA",
    "리부트": "REBOOT",
    "리부트2": "REBOOT2",
    "버닝": "BURNING",
    "버닝2": "BURNING2",
    "버닝3": "BURNING3",
}

SERVER_LIST = list(SERVER_NAME_MAP.keys())

# ✅ 캐릭터 ID 조회
def get_character_id(name, server):
    encoded_name = urllib.parse.quote(name)
    encoded_server = urllib.parse.quote(SERVER_NAME_MAP[server])
    url = f"https://open.api.nexon.com/maplestory/v1/id?character_name={encoded_name}&world_name={encoded_server}"
    res = requests.get(url, headers=NEXON_HEADERS)
    
    st.write("🔗 최종 요청 URL:", url)
    st.write("🧾 응답 상태:", res.status_code)
    st.write("📦 응답 본문:", res.text)
    
    if res.status_code == 200:
        data = res.json()
        st.write("🧩 CID:", data.get("ocid"))
        st.write("🗺️ 응답된 서버 이름:", data.get("world_name"))
        return data.get("ocid")
    
    return None

# ✅ 캐릭터 기본 정보 조회
def get_character_basic_by_id(char_id, server):
    encoded_server = urllib.parse.quote(SERVER_NAME_MAP[server])
    url = f"https://open.api.nexon.com/maplestory/v1/character/basic?character_id={char_id}&world_name={encoded_server}"
    res = requests.get(url, headers=NEXON_HEADERS)
    st.write("📥 캐릭터 상세 요청:", url)
    st.write("🧾 상태 코드:", res.status_code)
    return res.json() if res.status_code == 200 else None

#=================================================#
def get_character_stat(char_id, server):
    encoded_server = SERVER_NAME_MAP[server]
    url = f"https://open.api.nexon.com/maplestory/v1/character/stat?character_id={char_id}&world_name={encoded_server}"
    res = requests.get(url, headers=NEXON_HEADERS)
    return res.json() if res.status_code == 200 else None

def get_character_popularity(char_id, server):
    encoded_server = urllib.parse.quote(SERVER_NAME_MAP[server])
    url = f"https://open.api.nexon.com/maplestory/v1/character/popularity?character_id={char_id}&world_name={encoded_server}"
    res = requests.get(url, headers=NEXON_HEADERS)
    return res.json() if res.status_code == 200 else None

def get_character_hyperstat(char_id, server):
    encoded_server = urllib.parse.quote(SERVER_NAME_MAP[server])
    url = f"https://open.api.nexon.com/maplestory/v1/character/hyper-stat?character_id={char_id}&world_name={encoded_server}"
    res = requests.get(url, headers=NEXON_HEADERS)
    return res.json() if res.status_code == 200 else None

# ✅ Streamlit UI 함수
def show_character_viewer():
    st.title("📝 메이플 캐릭터 정보 검색기")
    char_name = st.text_input("🔎 캐릭터명을 입력하세요").strip()

    if char_name:
        st.write("입력된 캐릭터명:", repr(char_name))
        found = False

        for server in SERVER_LIST:
            st.write(f"🔍 서버 확인 중: `{server}`")
            char_id = get_character_id(char_name, server)

            if char_id:
                # ▶ 캐릭터 존재 확인용 API 호출
                stat = get_character_stat(char_id, server)
                pop = get_character_popularity(char_id, server)
                hyper = get_character_hyperstat(char_id, server)

                if stat or pop or hyper:
                    st.success(f"✅ `{char_name}` 캐릭터는 `{server}` 서버에 존재합니다.")
                    if stat:
                        st.subheader("📊 능력치 정보")
                        st.json(stat)
                    if pop:
                        st.subheader("💖 인기도")
                        st.json(pop)
                    if hyper:
                        st.subheader("🌟 하이퍼 스탯")
                        st.json(hyper)
                    found = True
                    break
                else:
                    st.warning("⚠️ 캐릭터 ID는 있으나 모든 API 정보 조회 실패 → 비정상 상태 또는 API 버그")
        

# 🧰 장비 정보 API
def get_character_equipment(name):
    url = f"https://open.api.nexon.com/maplestory/v1/character/item-equipment?character_name={name}"
    res = requests.get(url, headers=NEXON_HEADERS)
    return res.json() if res.status_code == 200 else None

# 🪄 장비 아이콘 + tooltip
def equipment_icon_with_tooltip(item):
    tooltip = f"""
    <div class="tooltip">
        <img src="{item['item_icon']}" width="50">
        <span class="tooltiptext">
            <b>{item['item_name']}</b><br>
            {item.get('item_description', '')}<br>
            옵션: {item.get('potential_option_grade', '정보 없음')}<br>
            스타포스: {item.get('starforce', '0')}성
        </span>
    </div>
    """
    style = """
    <style>
    .tooltip { position: relative; display: inline-block; }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 180px;
        background-color: #222;
        color: #fff;
        text-align: left;
        border-radius: 6px;
        padding: 8px;
        position: absolute;
        z-index: 1;
        bottom: 125%; left: 50%; margin-left: -90px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    </style>
    """
    return style + tooltip

# 🧱 장비창 출력 함수
def show_equipment_grid(equip_list):
    left, center, right = [], [], []

    for item in equip_list:
        part = item["item_equipment_part"]
        html_block = equipment_icon_with_tooltip(item)

        if EQUIP_POSITIONS.get(part, "center") == "left":
            left.append(html_block)
        elif EQUIP_POSITIONS.get(part, "center") == "right":
            right.append(html_block)
        else:
            center.append(html_block)

    cols = st.columns(3)
    with cols[0]:
        for block in left:
            html(block, height=80)
    with cols[1]:
        for block in center:
            html(block, height=80)
    with cols[2]:
        for block in right:
            html(block, height=80)



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
                res = supabase.table("Users").select("*").eq("user_id", login_id.strip()).execute()

                if res.data:
                    user_info = res.data[0]
                    stored_pw = user_info["password"]
                    # 🔐 비밀번호 해시 비교
                    if bcrypt.checkpw(login_pw.strip().encode('utf-8'), stored_pw.encode('utf-8')):
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
        🔹 ID와 PW를 까먹으면 개발자에게 연락하세요.(o차월o) \n
        🔹 보안에 취약하므로 자주 사용하는 비밀번호로 가입하지 마세요. \n
        🔹 악마길드에 가입한 캐릭터 닉네임으로 가입하세요. \n
        🔹 부길드에 본캐로 가입한 분들은 따로 연락 바랍니다. \n
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
                    # ✅ 비밀번호 해시 처리
                    hashed_pw = bcrypt.hashpw(new_pw.strip().encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

                    res = supabase.table("Users").insert({
                        "user_id": new_id.strip(),
                        "password": hashed_pw,  # 🔐 해시된 비밀번호 저장
                        "nickname": new_nick.strip()
                    }).execute()
                    already_member = supabase.table("Members").select("nickname").eq("nickname", new_nick.strip()).execute()
                    if not already_member.data:
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
                            # ✅ MainMembers 테이블 중복 검사
                            existing_main = supabase.table("MainMembers").select("nickname").eq("nickname", new_nick.strip()).execute()

                            if not existing_main.data:
                                supabase.table("MainMembers").insert({
                                    "nickname": new_nick.strip(),
                                    "position": "길드원",  # 기본 직책
                                    "suro_score": 0,
                                    "flag_score": 0,
                                    "mission_point": 0,
                                    "event_sum": 0
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

#관리자만 보이는 메뉴
if st.session_state.get("is_admin"):
    menu_options.extend(["악마 길드원 정보 등록", "악마길드 길컨관리", "부캐릭터 관리"])

# 모든 사용자에게 보이는 메뉴
menu_options.extend(["부캐릭터 등록", "보조대여 신청", "드메템 대여 신청","마니또 신청"])

menu = st.sidebar.radio("메뉴", menu_options)


if menu == "악마 길드원 정보 등록":
    st.subheader("👥 길드원 정보")
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
            "note": "비고"
            })


        # ✅ 탈퇴 여부 대신 표시용 컬럼으로 보여주기
        st.dataframe(
            df_display[[
                "ID", "닉네임", "직위", "비고"
            ]].reset_index(drop=True)
        )
        # ✅ 다운로드 버튼 추가
        excel_data = convert_df_to_excel(df_display)
        st.download_button("📥 길드원 목록 다운로드", data=excel_data, file_name="길드원_목록.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        if is_admin:
            st.subheader("길드원 정보 수정")
            selected_name = st.selectbox("수정 또는 삭제할 닉네임 선택", df["nickname"])
            selected_row = df[df["nickname"] == selected_name].iloc[0]
            with st.form("edit_form"):
                nickname_edit = st.text_input("닉네임", selected_row["nickname"])
                position_edit = st.text_input("직위", selected_row["position"])
                note_edit = st.text_input("비고", selected_row["note"])

                update_btn = st.form_submit_button("✏️ 수정")
                delete_btn = st.form_submit_button("🗑 삭제")

                if update_btn:
                    updated_data = {
                        "nickname": nickname_edit.strip(),
                        "position": position_edit.strip(),
                        "note": note_edit.strip()
                    }
                    if update_member(selected_row["id"], updated_data):
                        old_nickname = selected_row["nickname"]
                        new_nickname = nickname_edit.strip()

                        # ✅ MainMembers에도 닉네임 + 직위 업데이트
                        if old_nickname != new_nickname:
                            supabase.table("MainMembers").update({
                                "nickname": new_nickname,
                                "position": position_edit.strip() or "길드원"
                            }).eq("nickname", old_nickname).execute()
                        else:
                            supabase.table("MainMembers").update({
                                "position": position_edit.strip() or "길드원"
                            }).eq("nickname", old_nickname).execute()

                        st.success("수정 완료!")
                        st.rerun()
                    else:
                        st.error("수정 실패!")
                elif delete_btn:
                    if delete_member(selected_row["id"]):
                        # ✅ MainMembers에서도 삭제
                        supabase.table("MainMembers").delete().eq("nickname", selected_row["nickname"]).execute()

                        st.success("삭제 완료!")
                        st.rerun()
                    else:
                        st.error("삭제 실패!")

    else:
        st.info("아직 등록된 길드원이 없습니다.")

    st.subheader("길드원 정보 등록")
    with st.form("add_member_form"):
        nickname_input = st.text_input("닉네임")
        position_input = st.text_input("직위")
        note = st.text_input("비고")

        submitted = st.form_submit_button("등록")
        if submitted:
            if nickname_input in df["nickname"].values:
                st.warning(f"⚠️ '{nickname_input}' 닉네임은 이미 등록되어 있습니다.")
            else:
                data = {
                    "nickname": nickname_input,
                    "position": position_input,
                    "note": note,
                }
                if insert_member(data):
                    # ✅ 먼저 Members에 정상 등록되었으면 MainMembers 중복 확인 후 추가
                    existing_main = supabase.table("MainMembers").select("nickname").eq("nickname", nickname_input.strip()).execute()
                    if not existing_main.data:
                        supabase.table("MainMembers").insert({
                            "nickname": nickname_input.strip(),
                            "position": position_input or "길드원",
                            "suro_score": 0,
                            "flag_score": 0,
                            "mission_point": 0,
                            "event_sum": 0
                        }).execute()

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

        # ✅ 정렬
        df_main = df_main.sort_values(
            by=["position", "nickname"],
            key=lambda x: x.map(get_position_priority) if x.name == "position" else x.map(korean_first_sort)
        ).reset_index(drop=True)

        # ✅ 표시용 ID 추가
        df_main["ID"] = df_main.index + 1
        id_map = df_main.set_index("ID")["id"].to_dict()

        # ✅ 한글 컬럼 변환 (표시용)
        df_display = df_main[["ID", "nickname", "position", "suro_score", "flag_score", "mission_point", "event_sum"]].copy()
        df_display.rename(columns={
            "nickname": "닉네임",
            "position": "직위",
            "suro_score": "수로 점수",
            "flag_score": "플래그 점수",
            "mission_point": "주간미션포인트",
            "event_sum": "합계"
        }, inplace=True)
        df_display.set_index("ID", inplace=True)

        # ✅ 토글 상태
        if "show_all_mainmembers" not in st.session_state:
            st.session_state["show_all_mainmembers"] = False

        show_all = st.session_state["show_all_mainmembers"]

        # ✅ 토글 버튼
        btn_label = "🔽 전체 보기" if not show_all else "🔼 일부만 보기"
        if st.button(btn_label, key="toggle_mainmember_display"):
            st.session_state["show_all_mainmembers"] = not show_all
            st.rerun()

        # ✅ 높이만 조건부로 설정 (행 수 제한 없음!)
        height_value = None if show_all else 210 

        # ✅ 표 표시
        st.markdown("### 📋 악마 길드 길드컨트롤 등록현황 ")
        edited_df = st.data_editor(
            df_display,  # 전체 데이터 항상 사용
            use_container_width=True,
            disabled=["닉네임"],
            num_rows="dynamic",
            height=height_value,  # ✅ 보기 상태에 따라 height만 다르게
            key="main_editor"
        )


        # ✅ 수정 저장 처리
        column_map = {
            "직위": "position",
            "수로 점수": "suro_score",
            "플래그 점수": "flag_score",
            "주간미션포인트": "mission_point",
            "합계": "event_sum"
        }
        original_cols = list(column_map.values())

        if st.button("💾 수정 내용 저장"):
            for idx, row in edited_df.iterrows():
                row_id = id_map.get(idx)
                if not row_id:
                    continue

                updated = {eng: row[kor] for kor, eng in column_map.items()}
                original = df_main[df_main["id"] == row_id][original_cols].iloc[0]

                if not original.equals(pd.Series(updated)):
                    if update_mainmember(row_id, updated):
                        st.success(f"✅ `{row['닉네임']}` 수정 완료")
                    else:
                        st.error(f"❌ `{row['닉네임']}` 수정 실패")
            st.rerun()
    else:
        st.info("기록된 길드컨트롤 정보가 없습니다.")
        # 표 하단 점수 초기화 버튼 (각 점수 항목 바로 아래)
    button_cols = st.columns(7)

    with button_cols[0]:
        st.empty()  # ID

    with button_cols[1]:
        st.empty()  # 닉네임

    with button_cols[2]:
        st.empty()  # 직위

    with button_cols[3]:
        if st.button("🧹 수로 삭제"):
            for row in df_main.itertuples():
                update_mainmember(row.id, {"suro_score": 0})
            st.success("✅ 수로 점수가 초기화되었습니다.")
            st.rerun()

    with button_cols[4]:
        if st.button("🧹 플래그 삭제"):
            for row in df_main.itertuples():
                update_mainmember(row.id, {"flag_score": 0})
            st.success("✅ 플래그 점수가 초기화되었습니다.")
            st.rerun()

    with button_cols[5]:
        if st.button("🧹 주간미션 삭제"):
            for row in df_main.itertuples():
                update_mainmember(row.id, {"mission_point": 0})
            st.success("✅ 주간미션포인트가 초기화되었습니다.")
            st.rerun()

    with button_cols[6]:
        if st.button("🧹 합계 삭제"):
            for row in df_main.itertuples():
                update_mainmember(row.id, {"event_sum": 0})
            st.success("✅ 합계 점수가 초기화되었습니다.")
            st.rerun()

    # with st.form("main_member_add_form"):
    #     st.markdown("### ➕ 악마 길드원 길드컨트롤 등록")

    #     nickname_input = st.selectbox("닉네임", member_nicknames, key="nickname_input")
    #     suro_score_input = st.number_input("수로 점수", min_value=0, step=1, key="suro_score_input")
    #     flag_score_input = st.number_input("플래그 점수", min_value=0, step=1, key="flag_score_input")
    #     mission_point_input = st.number_input("주간미션포인트", min_value=0, step=1, key="mission_point_input")
    #     event_sum_input = st.number_input("합산", min_value=0, step=1, key="event_sum_input")

    #     submitted = st.form_submit_button("등록")

    #     if submitted:
    #         df_main = pd.DataFrame(mainmembers)
    #         if nickname_input in df_main["nickname"].values:
    #             st.warning(f"⚠️ '{nickname_input}' 닉네임은 이미 메인 캐릭터로 등록되어 있습니다.")
    #         else:
    #             position_value = member_dict.get(nickname_input, "길드원")
    #             new_data = {
    #                 "nickname": nickname_input,
    #                 "position": position_value,
    #                 "suro_score": suro_score_input,
    #                 "flag_score": flag_score_input,
    #                 "mission_point": mission_point_input,
    #                 "event_sum": event_sum_input
    #             }
    #             res = requests.post(f"{SUPABASE_URL}/rest/v1/MainMembers", headers=HEADERS, json=new_data)
    #             if res.status_code == 201:
    #                 st.success("✅ 메인 캐릭터가 등록되었습니다!")
    #                 st.rerun()
    #             else:
    #                 st.error(f"❌ 등록 실패! 에러 코드: {res.status_code}")
    #                 st.code(res.text)



elif menu == "부캐릭터 관리":
    st.subheader("👥 부캐릭터 등록 및 관리")
    members = get_members()
    main_names = [m['nickname'] for m in members]
    submembers = get_submembers()
    df_sub = pd.DataFrame(submembers)

    with st.form("add_sub_form"):
        selected_main = st.selectbox("본캐 닉네임 선택", main_names)
        guild_name1 = st.selectbox("길드 이름", guild_options)
        sub_name = st.text_input("부캐 이름")
        # 선택된 본캐 기준으로 등록된 부캐 가져오기
        # linked_subs = df_sub[df_sub["main_name"] == selected_main]["sub_name"].tolist()
        # sub_name = st.selectbox("부캐 이름 선택", linked_subs) if linked_subs else st.warning("⚠️ 선택한 본캐에 등록된 부캐가 없습니다.")
        suro_score = st.number_input("수로 점수", min_value=0, step=1)
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
                    "guild_name1": guild_name1,
                    "sub_name": sub_name,
                    "main_name": selected_main,
                    "suro_score": suro_score,
                    "flag_score": flag_score,
                    "mission_point": mission_point,
                    "created_by": nickname
                }
                if insert_submember(data):
                    st.success(f"✅ {sub_name} 등록 완료")
                    st.rerun()
                else:
                    st.error("🚫 등록 실패")

    st.markdown("---")
    st.subheader("📊 부캐릭터 요약")

    # ✅ 부캐 전체 목록 테이블 추가
    st.markdown("### 📑 등록된 전체 부캐릭터 목록")
    if not df_sub.empty:
        df_sub = df_sub.reset_index(drop=True)       # 인덱스 재정렬
        df_sub["ID"] = df_sub.index + 1              # id 다시 부여
        display_all_df = df_sub.rename(columns={
            "ID": "ID",
            "guild_name1": "부캐 길드",
            "sub_name": "부캐 닉네임",
            "main_name": "본캐 닉네임",
            "suro_score": "수로 점수",
            "flag_score": "플래그 점수",
            "mission_point": "주간미션포인트"
        })
        st.dataframe(display_all_df[["ID", "부캐 길드","부캐 닉네임", "본캐 닉네임", "수로 점수", "플래그 점수", "주간미션포인트"]].reset_index(drop=True))
        excel_data = convert_df_to_excel(display_all_df)
        button_cols = st.columns(7)

        with button_cols[0]:
            st.empty()  # ID

        with button_cols[1]:
            st.empty()  # 닉네임

        with button_cols[2]:
            st.empty()  # 직위
        
        with button_cols[3]:
            st.empty()  # 직위

        with button_cols[4]:
            if st.button("🧹 수로 삭제"):
                for row in df_sub.itertuples():
                    update_submember(row.sub_id, {"suro_score": 0})
                st.success("✅ 수로 점수가 초기화되었습니다.")
                st.rerun()

        with button_cols[5]:
            if st.button("🧹 플래그 삭제"):
                for row in df_sub.itertuples():
                    update_submember(row.sub_id, {"flag_score": 0})
                st.success("✅ 플래그 점수가 초기화되었습니다.")
                st.rerun()

        with button_cols[6]:
            if st.button("🧹 주간미션 삭제"):
                for row in df_sub.itertuples():
                    update_submember(row.sub_id, {"mission_point": 0})
                st.success("✅ 주간미션포인트가 초기화되었습니다.")
                st.rerun()
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
                    "suro_score": "수로 점수",
                    "flag_score": "플래그 점수",
                    "mission_point": "주간미션포인트"
                })

                st.markdown(f"### 🔹 {main} - 부캐 {len(display_df)}개")
                st.dataframe(display_df[["부캐 길드", "부캐 닉네임", "수로 점수", "플래그 점수", "주간미션포인트"]])

                if is_admin:
                    with st.expander(f"✏️ {main} 부캐 수정"):
                        sub_names = df_main["sub_name"].tolist()
                        selected_sub_filter = st.selectbox("🔍 수정할 부캐 선택", sub_names, key=f"select_{main}")

                        # ✅ 선택된 부캐만 필터링
                        df_main = df_main[df_main["sub_name"] == selected_sub_filter]
                        sub_row = df_main.iloc[0]
                        sub = sub_row["sub_id"]

                        # 🔽 이 아래부터는 수정 입력 영역
                        new_guild_name = st.selectbox(
                            "부캐 길드",
                            options=guild_options,
                            index=guild_options.index(sub_row.get("guild_name1", "길드A")) if sub_row.get("guild_name1", "길드A") in guild_options else 0,
                            key=f"guild_{sub}"
                        )
                        new_suro_score = st.number_input("수로 점수", min_value=0, step=1, value=sub_row.get("suro_score", 0), key=f"suro_score_{sub}")
                        new_flag_score = st.number_input("플래그 점수", min_value=0, step=1, value=sub_row.get("flag_score", 0), key=f"flag_score_{sub}")
                        new_mission = st.number_input("주간미션포인트", min_value=0, step=1, value=sub_row.get("mission_point", 0), key=f"mission_{sub}")

                        if st.button("저장", key=f"save_{sub}"):
                            update_data = {
                                "guild_name1": new_guild_name,
                                "suro_score": new_suro_score,
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

            if sub_name in df_sub["sub_name"].values:
                st.warning(f"⚠️ '{sub_name}'은 이미 등록된 부캐입니다.")
            else:
                new_sub_data = {
                    "sub_name": sub_name,
                    "guild_name1": guild_name1,
                    "main_name": nickname,
                    "suro_score": 0,
                    "flag_score": 0,
                    "mission_point": 0,
                    "created_by": nickname
                }
                if insert_submember(new_sub_data):
                    st.success("✅ 부캐릭터가 등록되었습니다!")
                    st.rerun()
                else:
                    st.error("❌ 등록 실패")

    #수정 칸
    st.markdown("---")
    st.subheader("✏️ 등록된 부캐릭터 정보 수정")

    # 로그인한 유저의 부캐 목록만 필터링
    submembers = get_submembers()
    df_sub = pd.DataFrame(submembers)
    user_subs = df_sub[df_sub["main_name"] == nickname]

    if user_subs.empty:
        st.info("등록된 부캐릭터가 없습니다.")
    else:
        # ✅ 닉네임과 길드만 표시하는 표
        display_df = user_subs[["sub_name", "guild_name1"]].rename(columns={
            "sub_name": "부캐 닉네임",
            "guild_name1": "부캐 길드"
        }).reset_index(drop=True)

        st.markdown("### 📋 현재 등록된 내 부캐 목록")
        st.dataframe(display_df, use_container_width=True)

    

    if user_subs.empty:
        st.info("등록된 부캐릭터가 없습니다.")
    else:
        sub_names = user_subs["sub_name"].tolist()
        selected_sub = st.selectbox("수정할 부캐 선택", sub_names)

        sub_row = user_subs[user_subs["sub_name"] == selected_sub].iloc[0]
        sub_id = sub_row["sub_id"]

        # 수정 입력창
        new_sub_name = st.text_input("부캐 이름", value=sub_row["sub_name"], key="edit_subname")
        new_guild_name = st.selectbox(
            "부캐 길드 선택",
            guild_options,
            index=guild_options.index(sub_row.get("guild_name1", guild_options[0])) if sub_row.get("guild_name1") in guild_options else 0,
            key="edit_guildname")
        
         # ✅ 수정 완료 버튼
        if st.button("✅ 수정하기", key="edit_sub_submit"):
            update_data = {
                "sub_name": new_sub_name,
                "guild_name1": new_guild_name
            }
            if update_submember(sub_id, update_data):
                st.success("✅ 부캐릭터 정보가 수정되었습니다.")
                st.rerun()
            else:
                st.error("❌ 수정 실패")

    st.warning("⚠️ 허위정보 등록 적발 시 이용이 제한됩니다.")
    st.markdown("### ❗ 필독 ❗")
    st.info(''' 
    🔹보조무기와 드메셋 대여를 위해 등록이 필요합니다.\n
    🔹 미등록시 대여 기능에 이용이 제한될 수 있습니다.\n
    🔹 부캐릭터로 대여 기능을 이용하려는 경우에만 해당합니다.    
    ''')


elif menu == "보조대여 신청":
    from utils.time_grid import generate_slot_table
    from datetime import datetime, timedelta, timezone

    st.header("\U0001F6E1️ 보조무기 대여 시스템")
    nickname = st.session_state["nickname"]
    owner = ["자리스틸의왕", "죤냇", "나영진", "o차월o"]

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

    col_left, col_right = st.columns([1, 2])
    with col_left:
        nickname_options = get_all_character_names(nickname)
        selected_borrower = st.selectbox("보조무기 대여자", nickname_options)
        job_group = st.selectbox("\U0001F9E9 직업군", list(job_data.keys()))
        selected_job = st.selectbox("\U0001F50D 직업", job_data[job_group])

    with col_right:
        image_path = os.path.join(
            IMAGE_FOLDER, "시그너스보조.jpg" if selected_job in CYGNUS_SHARED else f"{selected_job}보조.jpg")
        image_available = os.path.exists(image_path)
        if image_available:
            st.image(Image.open(image_path).resize((1000, 500)), caption=f"{selected_job}의 보조무기")
        else:
            st.warning("⚠️ 보유중인 보조무기가 없어 대여가 불가능합니다.")

    weapon_data = fetch_weapon_rentals()

    if image_available:
        editing_id = st.session_state.get("edit_rental_id")
        editing_slots = st.session_state.get("edit_time_slots", []) if editing_id else []

        reserved_slots = {
            slot.strip(): row["borrower"]
            for row in weapon_data
            if selected_job in row.get("weapon_name", "")
            and (not editing_id or row["id"] != editing_id)
            for slot in row.get("time_slots", "").split(",")
            if slot.strip()
        }

        st.markdown(f"### ⏰ `{selected_job}`")
        time_slot_grid, days = generate_slot_table()
        weekday_labels = ["월", "화", "수", "목", "금", "토", "일"]
        cols = st.columns(len(days) + 1)
        cols[0].markdown("**시간**")
        day_selected = {}

        for i, day in enumerate(days):
            label = f"{weekday_labels[day.weekday()]}<br>{day.strftime('%m/%d')}"
            day_str = day.strftime("%Y-%m-%d")
            now = datetime.now(timezone.utc) + timedelta(hours=9)

            has_available_slot = any(
                reserved_slots.get(slot_time) is None and
                datetime.strptime(slot_time, "%Y-%m-%d %H:%M").replace(tzinfo=timezone(timedelta(hours=9))) > now
                for time_label, row in time_slot_grid.items()
                for slot_time, _ in row if slot_time.startswith(day_str)
            )

            with cols[i + 1]:
                st.markdown(label, unsafe_allow_html=True)
                day_selected[i] = st.checkbox("전체", key=f"day_select_{i}", disabled=not has_available_slot)

        selection = {}
        KST = timezone(timedelta(hours=9))
        now = datetime.now(KST)

        for time_label, row in time_slot_grid.items():
            row_cols = st.columns(len(row) + 1)
            row_cols[0].markdown(f"**{time_label}**")
            for j, (slot_time, slot_key) in enumerate(row):
                slot_time_obj = datetime.strptime(slot_time, "%Y-%m-%d %H:%M").replace(tzinfo=timezone(timedelta(hours=9)))
                borrower = reserved_slots.get(slot_time)
                default_checked = slot_time in editing_slots or day_selected.get(j, False)

                if editing_id and slot_time in editing_slots:
                    if slot_time_obj < now:
                        # 수정중인데, 이 슬롯이 이미 지났으면 수정 불가
                        row_cols[j + 1].checkbox("지남", value=True, key=slot_key, disabled=True)
                    else:
                        # 수정중인데, 이 슬롯이 미래면 수정 가능
                        selection[slot_time] = row_cols[j + 1].checkbox("", value=True, key=slot_key)
                elif borrower and (not editing_id or slot_time not in editing_slots):
                    # 다른 사람 or 자기 다른 대여 기록에서 이미 예약된 시간
                    row_cols[j + 1].checkbox(borrower, value=True, key=slot_key, disabled=True)
                elif now > slot_time_obj:
                    # 아무도 대여 안했지만 이미 과거시간
                    row_cols[j + 1].checkbox("지남", value=False, key=slot_key, disabled=True)
                else:
                    # 아무 문제 없는 슬롯 (선택 가능)
                    selection[slot_time] = row_cols[j + 1].checkbox("", value=default_checked, key=slot_key)


        selected_time_slots = [k for k, v in selection.items() if v]
        selected_dates = sorted({datetime.strptime(k.split()[0], "%Y-%m-%d").date() for k in selected_time_slots})

        if editing_id:
            st.info("✏️ 현재 대여 정보를 수정 중입니다. 원하는 시간대를 다시 선택 후 '수정 완료'를 눌러주세요.")

        if st.button("✏️ 수정 완료" if editing_id else "📥 대여 등록"):
            if not selected_time_slots:
                st.warning("❗ 최소 1개 이상의 시간을 선택해주세요.")
            elif len(selected_dates) > 7:
                st.warning("❗ 대여 기간은 최대 7일까지만 선택할 수 있습니다.")
            else:
                rental_data = {
                    "borrower": selected_borrower,
                    "weapon_name": selected_job + " 보조무기",
                    "owner": json.dumps(owner),
                    "time_slots": ", ".join(selected_time_slots),
                    "is_edit": editing_id is not None
                }

                if editing_id:
                    delete_weapon_rental(editing_id)
                    del st.session_state["edit_rental_id"]
                    del st.session_state["edit_time_slots"]

                response = requests.post(f"{SUPABASE_URL}/rest/v1/Weapon_Rentals", headers=HEADERS, json=rental_data)
                if response.status_code == 201:
                    st.success("✅ 수정이 완료되었습니다!" if editing_id else "✅ 대여 등록이 완료되었습니다!")
                    st.rerun()
                else:
                    st.error(f"❌ 등록 실패: {response.status_code}")


    # ✅ 대여 현황 및 반납/수정 처리
    weapon_data = fetch_weapon_rentals()
    filtered = [
        r for r in (weapon_data or [])
        if isinstance(r.get("weapon_name"), str)
        and selected_job in r["weapon_name"]
        and "time_slots" in r
    ]

    if filtered:
        df = pd.DataFrame(filtered).sort_values(by="id").reset_index(drop=True)
        df_display = df.copy()
        df_display["ID"] = df_display.index + 1
        df_display["대여기간"] = df_display["time_slots"].apply(get_weapon_range)
        df_display["대표소유자"] = df_display["owner"].apply(
            lambda x: json.loads(x)[0] if isinstance(x, str) and x.startswith("[") else x
        )
        df_display.rename(columns={
            "borrower": "대여자",
            "weapon_name": "대여 아이템"
        }, inplace=True)

        st.markdown("### 📄 보조무기 대여 현황")
        st.dataframe(df_display[["ID", "대여자", "대여 아이템", "대표소유자", "대여기간"]], use_container_width=True)

        excel_df = df_display[["대여자", "대여 아이템", "대표소유자", "대여기간"]].copy()
        excel_data = convert_df_to_excel(excel_df)
        st.download_button(
            label="📅 보조무기 대여 현황 다운로드",
            data=excel_data,
            file_name="보조무기_대여현황.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        for _, row in df.iterrows():
            owners_list = json.loads(row["owner"]) if isinstance(row["owner"], str) and row["owner"].startswith("[") else [row["owner"]]
            borrower_name = row.get("borrower", "(이름 없음)")
            if not borrower_name or str(borrower_name).lower() == "nan":
                borrower_name = "(이름 없음)"

            is_owner = nickname in owners_list
            is_borrower = nickname == borrower_name

            if is_owner or is_borrower:
                with st.expander(f"🛡️ '{row['weapon_name']}' - 대여자: {borrower_name}"):
                    st.markdown(f"**📅 대여기간:** `{get_weapon_range(row['time_slots'])}`")
                    st.markdown(f"**소유자:** `{', '.join(owners_list)}`")

                    if is_owner:
                        if st.button("🗑 반납 완료", key=f"weapon_return_{row['id']}"):
                            if delete_weapon_rental(row["id"]):
                                st.success("✅ 반납 완료되었습니다!")
                                st.rerun()
                            else:
                                st.error("❌ 반납 실패! 다시 시도해주세요.")

                    if is_borrower:
                        try:
                            KST = timezone(timedelta(hours=9))
                            now = datetime.now(KST)
                            slot_times = [
                                datetime.strptime(t.strip(), "%Y-%m-%d %H:%M").replace(tzinfo=KST)
                                for t in row["time_slots"].split(",") if t.strip()
                            ]

                            earliest_time = min(slot_times)
                            


                            if now < earliest_time:
                                if st.button("✏️ 수정하기", key=f"edit_rental_{row['id']}"):
                                    st.session_state["edit_rental_id"] = row["id"]
                                    st.session_state["edit_time_slots"] = row["time_slots"].split(", ")
                                    st.rerun()
                            else:
                                st.caption("⏰ 이미 시작된 대여로 수정할 수 없습니다.")
                        except Exception as e:
                            st.error(f"시간 파싱 오류: {e}")



elif menu == "드메템 대여 신청":
    st.header("\U0001F4FF 드메템 대여 시스템")
    nickname = st.session_state["nickname"]
    owners = ["자리스틸의왕", "새훨", "죤냇", "나영진", "o차월o"]

    # 드메템 이미지 폴더 지정
    DROP_IMAGE_FOLDER = "드메템 사진"

    # 드메템 이미지 매핑 
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
                    borrower_name = row.get("대여자", "(이름 없음)")
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
##333
elif menu == "마니또 신청":

    st.header("마니또 신청")
    nickname = st.session_state["nickname"]
    is_admin = st.session_state.get("is_admin", False)

    members = get_members()
    maniddo_options = [m["nickname"] for m in members if "nickname" in m]
    selected_name = st.selectbox("신청자 닉네임", maniddo_options)
    selected_role = st.selectbox("🌟 신청 역할", ["튜터", "튜티"])

    # ✅ 모든 신청 데이터 조회
    res = supabase.table("ManiddoRequests").select("*").execute()
    all_requests = res.data or []
    df = pd.DataFrame(all_requests)

    # ✅ 튜터 선택 필터 (튜티일 경우만)
    desired_tutor = None
    already_chosen_tutors = set(r["desired_tutor"] for r in all_requests if r.get("desired_tutor"))
    available_tutors = [
        r["tutor_name"] for r in all_requests
        if r.get("tutor_name") and r["tutor_name"] not in already_chosen_tutors and r["tutor_name"] != selected_name
    ]

    if selected_role == "튜티":
        st.markdown("### 🙋 함께하고 싶은 튜터 선택")
        if available_tutors:
            desired_tutor = st.selectbox("원하는 튜터", available_tutors)
        else:
            st.warning("⚠️ 현재 모든 튜터가 마니또를 진행 중입니다.")

    note_input = st.text_input("📝 비고 (선택사항)", placeholder="하고 싶은 말, 요청사항 등")

    if st.button("📥 신청하기"):
        now = datetime.now().isoformat()
        data = {
            "tutor_name": selected_name if selected_role == "튜터" else None,
            "tutee_name": selected_name if selected_role == "튜티" else None,
            "desired_tutor": desired_tutor if selected_role == "튜티" else None,
            "note": note_input.strip() if note_input else None,
            "timestamp": now
        }

        res = supabase.table("ManiddoRequests").insert(data).execute()
        if res.data:
            st.success(f"✅ {selected_name}님이 '{selected_role}'로 신청되었습니다.")
            st.rerun()
        else:
            st.error("❌ 신청 실패. 다시 시도해주세요.")

    st.markdown("---")

    # ✅ 신청 목록 보기
    if df.empty:
        st.info("아직 신청된 마니또가 없습니다.")
    else:
        if is_admin:
            st.subheader(" 전체 신청 목록 ")
            view_df = df.drop(columns=["timestamp"], errors="ignore").rename(columns={
                "tutor_name": "튜터",
                "tutee_name": "튜티",
                "desired_tutor": "튜티가 선택한 튜터",
                "note": "비고",
                "memo": "메모"
            })
            st.dataframe(view_df.reset_index(drop=True), use_container_width=True)

            excel_data = convert_df_to_excel(view_df)
            st.download_button(
                label="📥 마니또 신청 목록 다운로드",
                data=excel_data,
                file_name="마니또_신청목록.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.subheader("📋 내 마니또 매칭 정보")

            tutor_matches = df[
                (df["desired_tutor"] == nickname) & (df["tutor_name"] == nickname)
            ][["tutee_name", "note", "memo"]].rename(columns={
                "tutee_name": "매칭된 튜티", "note": "비고", "memo": "메모"
            })

            tutee_matches = df[
                (df["tutee_name"] == nickname) &
                (df["desired_tutor"].isin(df["tutor_name"]))
            ][["desired_tutor", "note", "memo"]].rename(columns={
                "desired_tutor": "매칭된 튜터", "note": "비고", "memo": "메모"
            })

            if not tutor_matches.empty:
                st.markdown("### 🎯 당신을 선택한 튜티")
                st.dataframe(tutor_matches.reset_index(drop=True), use_container_width=True)

            if not tutee_matches.empty:
                st.markdown("### 📬 당신이 선택한 튜터")
                st.dataframe(tutee_matches.reset_index(drop=True), use_container_width=True)

            if tutor_matches.empty and tutee_matches.empty:
                st.info("🙅 아직 매칭된 마니또가 없습니다.")

    st.markdown("---")
    st.subheader("🛠️ 마니또 관리 (튜터/관리자 전용)")

    if st.button("✏️ 수정하기"):
        if is_admin:
            # ✅ 관리자: 매칭된 튜터-튜티 목록 선택
            editables = df[df["tutor_name"].notna() & df["tutee_name"].notna()]
            edit_titles = [f"{r['tutor_name']} - {r['tutee_name']}" for r in editables.to_dict("records")]
            selected_pair = st.selectbox("✍️ 수정할 마니또 선택", edit_titles)
            selected_row = editables.iloc[edit_titles.index(selected_pair)]

            st.markdown(f"#### ✏️ {selected_row['tutor_name']} - {selected_row['tutee_name']} 메모 수정")
            new_memo = st.text_area("기록", value=selected_row.get("memo", ""), key="admin_edit")
            if st.button("💾 수정완료"):
                supabase.table("ManiddoRequests").update({"memo": new_memo}).eq("id", selected_row["id"]).execute()
                st.success("✅ 메모가 수정되었습니다.")
                st.rerun()
            if st.button("❌ 마니또 종료"):
                supabase.table("ManiddoRequests").delete().eq("id", selected_row["id"]).execute()
                st.success("🗑️ 매칭이 종료되었습니다.")
                st.rerun()
        else:
            # ✅ 튜터 본인: 자신의 매칭된 튜티 목록만
            matched = df[(df["tutor_name"] == nickname) & (df["tutee_name"].notna())]
            if matched.empty:
                st.info("🙅 진행 중인 마니또가 없습니다.")
            else:
                for row in matched.itertuples():
                    st.markdown(f"#### ✏️ {row.tutee_name}님과의 메모")
                    updated_memo = st.text_area("기록", value=row.memo or "", key=f"memo_{row.id}")
                    if st.button(f"💾 수정완료 - ID {row.id}"):
                        supabase.table("ManiddoRequests").update({"memo": updated_memo}).eq("id", row.id).execute()
                        st.success("✅ 메모가 저장되었습니다.")
                        st.rerun()
                    if st.button(f"❌ 마니또 종료 - ID {row.id}"):
                        supabase.table("ManiddoRequests").delete().eq("id", row.id).execute()
                        st.success("🗑️ 마니또가 종료되었습니다.")
                        st.rerun()




    

# elif menu == "캐릭터 정보 검색":
#     show_character_viewer()

          