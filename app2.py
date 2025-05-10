import streamlit as st
import requests
import pandas as pd
import xlsxwriter
import bcrypt
import textwrap
import codecs
import json
import uuid
import re
import urllib.parse
import io
import os, base64
import uuid, time
import pytz
from PIL import Image
from datetime import date, timezone, timedelta
from supabase import create_client, Client
from streamlit.components.v1 import html
from utils.time_grid import generate_slot_table
from datetime import date,datetime
from postgrest.exceptions import APIError
from io import BytesIO

#=============위치고정=============================================#
st.set_page_config(page_title="악마길드 관리 시스템", layout="wide")
st.markdown("""
    <style>
    .small-button > button {
        font-size: 13px !important;
        padding: 0.25rem 0.75rem;
        margin-bottom: 4px;
    }
    </style>
""", unsafe_allow_html=True)
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
KST = timezone(timedelta(hours=9))
now_kst = datetime.now(KST)
##

ADMIN_USERS = ["자리스틸의왕", "나영진", "죤냇", "o차월o","랩핑","관리자"]
guild_options = ["악마","악질", "악먀"]  # 혹은 DB나 리스트에서 불러오기

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

# def update_submember(sub_id, data):
#     res = requests.patch(f"{SUPABASE_URL}/rest/v1/SubMembers?sub_id=eq.{sub_id}", headers=HEADERS, json=data)
#     return res.status_code == 204

def update_submember(sub_id, data):
    if not sub_id:
        print("❗ sub_id is null, skipping update")
        return False
    return supabase.table("SubMembers").update(data).eq("sub_id", sub_id).execute()

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
        st.markdown("🔹 4분기에 홈페이지 최적화 예정입니다.")

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
        🔹 가입하기 후 로그인 화면으로 되돌아 가지지 않는다면 돌아가기 버튼을 눌러주세요.
        ''')
###
        col1, col2 = st.columns(2)
        with col1:
            if st.button("가입하기"):
                exist = supabase.table("Users").select("user_id").eq("user_id", new_id.strip()).execute()
                if exist.data:
                    st.warning("⚠️ 이미 존재하는 아이디입니다.")
                elif new_nick.strip() not in ALLOWED_NICKNAMES:
                    st.warning("⚠️ 해당 닉네임은 길드에 등록되어 있지 않습니다.")
                else:
                    try:
                        hashed_pw = bcrypt.hashpw(new_pw.strip().encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

                        res = supabase.table("Users").insert({
                            "user_id": new_id.strip(),
                            "password": hashed_pw,
                            "nickname": new_nick.strip()
                        }).execute()

                        already_member = supabase.table("Members").select("nickname").eq("nickname", new_nick.strip()).execute()

                        if not already_member.data and res.data:
                            supabase.table("Members").insert({
                                "nickname": new_nick.strip(),
                                "position": "길드원",
                                "note": None
                            }).execute()

                            supabase.table("MainMembers").insert({
                                "nickname": new_nick.strip(),
                                "position": "길드원",
                                "suro_score": 0,
                                "flag_score": 0,
                                "mission_point": 0,
                                "event_sum": 0
                            }).execute()

                            st.success("✅ 회원가입 완료! 로그인으로 이동합니다.")
                            st.session_state.signup_mode = False
                            st.rerun()

                    except APIError as e:
                        error_info = e.args[0] if e.args else "No error details available"
                        status_code = error_info.get("code", "No code") if isinstance(error_info, dict) else "Unknown"

                        st.error(f"🚫 Supabase API 에러 발생 (상태코드: {status_code})")
                        st.code(json.dumps(error_info, indent=2, ensure_ascii=False))

        with col2:
            if st.button("↩️ 돌아가기"):
                st.session_state.signup_mode = False
                st.rerun()

        

        st.stop()

# ✅ 로그인 이후 사이드바
if "user" in st.session_state:
    is_admin = st.session_state.get("is_admin", False)

    # ✅ 이벤트 이미지 경로 (고정된 이미지 파일명)
    EVENT_IMAGE_PATH = "이벤트이미지폴더/여름이벤트.jpg"  # 확장자 포함 정확히 지정

    # ✅ 이미지가 없으면 표시 안함
    if not os.path.exists(EVENT_IMAGE_PATH):
        st.stop()

    # ✅ 세션 상태 초기화
    if "hide_today_popup" not in st.session_state:
        st.session_state["hide_today_popup"] = False

    # ✅ 로그인 정보 출력
    nickname = st.session_state.get("nickname", "")
    st.sidebar.markdown(f"👤 로그인: {nickname}")

    # ✅ 로그아웃 버튼
    if st.sidebar.button("로그아웃"):
        user_id = st.session_state.get("user")
        if user_id:
            supabase.table("Users").update({"login_token": None}).eq("user_id", user_id).execute()
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()

    # ✅ 배너 닫기 버튼 (사이드바 하단)
    if not st.session_state["hide_today_popup"]:
        if st.sidebar.button("❌ 배너 닫기"):
            st.session_state["hide_today_popup"] = True

    # ✅ 배너 표시
    if not st.session_state["hide_today_popup"]:
        with open(EVENT_IMAGE_PATH, "rb") as img_file:
            base64_img = base64.b64encode(img_file.read()).decode()

        st.markdown(f"""
        <style>
        .event-popup {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 800px;
            height: 450px;
            padding: 20px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            font-family: sans-serif;
            z-index: 9999;
            text-align: center;
            overflow-y: auto;
        }}
        .event-popup img {{
            width: 100%;
            border-radius: 10px;
            margin-bottom: 12px;
        }}
        .event-popup h4 {{
            margin: 6px 0;
            font-size: 18px;
            color: #d62c2c;
        }}
        .event-popup p {{
            font-size: 14px;
            color: #333;
        }}
        </style>

        <div class="event-popup">
            <img src="data:image/png;base64,{base64_img}" alt="로또 이벤트">
        </div>
        """, unsafe_allow_html=True)
        
menu_options = []

#관리자만 보이는 메뉴
if st.session_state.get("is_admin"):
    menu_options.extend(["악마 길드원 정보 등록", "악마길드 길컨관리", "부캐릭터 관리","마니또 관리","이벤트 이미지 등록"])

# 모든 사용자에게 보이는 메뉴
menu_options.extend(["부캐릭터 등록", "보조대여 신청", "드메템 대여 신청","마니또 기록","이벤트 목록"])

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
        })

        # ✅ 전체 보기 토글 상태 관리
        if "show_all_guildmembers" not in st.session_state:
            st.session_state["show_all_guildmembers"] = False

        show_all = st.session_state["show_all_guildmembers"]
        btn_label = "🔽 전체 보기" if not show_all else "🔼 일부만 보기"
        if st.button(btn_label, key="toggle_guildmembers"):
            st.session_state["show_all_guildmembers"] = not show_all
            st.rerun()

        # ✅ 높이 설정
        height_value = None if show_all else 210

        # ✅ 표 표시 (수정 불가능하게 잠금)
        st.data_editor(
            df_display[["ID", "닉네임", "직위"]].reset_index(drop=True),
            use_container_width=True,
            height=height_value,
            disabled=["ID", "닉네임", "직위"],
            key="guild_view_editor"
        )

        # ✅ 다운로드 버튼
        excel_data = convert_df_to_excel(df_display)
        st.download_button("📥 길드원 목록 다운로드", data=excel_data, file_name="길드원_목록.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # ✅ 관리자 전용 수정/삭제
        if is_admin:
            st.subheader("길드원 정보 수정")
            selected_name = st.selectbox("수정 또는 삭제할 닉네임 선택", df["nickname"])
            selected_row = df[df["nickname"] == selected_name].iloc[0]

            with st.form("edit_form"):
                nickname_edit = st.text_input("닉네임", selected_row["nickname"])
                position_edit = st.text_input("직위", selected_row["position"])

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

                        # ✅ MainMembers 테이블에도 반영
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
                        supabase.table("MainMembers").delete().eq("nickname", selected_row["nickname"]).execute()
                        st.success("삭제 완료!")
                        st.rerun()
                    else:
                        st.error("삭제 실패!")

    else:
        st.info("아직 등록된 길드원이 없습니다.")

   # ✅ 역할 선택 (폼 밖에서 즉시 반응 가능하도록)
    role = st.selectbox("역할 선택", ["본캐", "부캐"], key="role_selector")

    # ✅ 길드원 등록 폼
    with st.form("add_member_form"):
        st.subheader("길드원 정보 등록")

        nickname_input = st.text_input("닉네임")
        position_input = st.text_input("직위", value="길드원")

        main_nickname_input = ""
        if role == "부캐":
            main_names = [m["nickname"] for m in get_members()]
            main_nickname_input = st.selectbox("본캐 닉네임 선택", [""] + main_names)

        submitted = st.form_submit_button("등록")

        if submitted:
            if nickname_input.strip() in df["nickname"].values:
                st.warning(f"⚠️ '{nickname_input}' 닉네임은 이미 등록되어 있습니다.")
            else:
                data = {
                    "nickname": nickname_input.strip(),
                    "position": position_input.strip(),
                    "note": role,
                    "main_nickname": main_nickname_input.strip() if role == "부캐" and main_nickname_input else None
                }

                result = insert_member(data)
                if result:
                    # ✅ 본캐일 경우에만 MainMembers 테이블 자동 추가
                    if role == "본캐":
                        existing_main = supabase.table("MainMembers").select("nickname").eq("nickname", nickname_input.strip()).execute()
                        if not existing_main.data:
                            supabase.table("MainMembers").insert({
                                "nickname": nickname_input.strip(),
                                "position": position_input.strip() or "길드원",
                                "suro_score": 0,
                                "flag_score": 0,
                                "mission_point": 0,
                                "event_sum": 0
                            }).execute()

                    st.success("✅ 길드원이 등록되었습니다!")
                    st.rerun()
                else:
                    st.error("🚫 등록에 실패했습니다. 입력값을 확인해주세요.")


                    
elif menu == "악마길드 길컨관리":
    st.subheader("👥 악마길드 길드컨트롤 관리")

    mainmembers = get_mainmembers()
    members = get_members()

    member_dict = {m['nickname']: m['position'] for m in members if m.get('nickname')}
    member_nicknames = sorted(member_dict.keys())

    if mainmembers:
        df_main = pd.DataFrame(mainmembers)
        df_main["id"] = [m["id"] for m in mainmembers]  # ✅ id 컬럼 명시적으로 설정

        # 🔽 부캐 점수를 본캐에 합산
        members = get_members()
        df_member = pd.DataFrame(members)

        df_main = pd.DataFrame(mainmembers)
        df_main["id"] = [m["id"] for m in mainmembers]
        df_main["ID"] = df_main.index + 1
        id_map = df_main.set_index("ID")["id"].to_dict()

        # ✅ 안전하게 부캐 필터링: 컬럼 존재 + 값 존재 확인
        if "note" in df_member.columns and "main_nickname" in df_member.columns:
            df_sub = df_member[
                (df_member["note"] == "부캐") &
                (df_member["main_nickname"].notnull())
            ].copy()
        else:
            df_sub = pd.DataFrame()

        # ✅ 부캐 점수 컬럼 처리
        for col in ["suro_score", "flag_score", "mission_point"]:
            if col not in df_sub.columns:
                df_sub[col] = 0
            df_sub[col] = df_sub[col].fillna(0).astype(int)

        # ✅ 본캐 기준 부캐 점수 합산
        sub_sums = df_sub.groupby("main_nickname")[["suro_score", "flag_score", "mission_point"]].sum().reset_index()

        # ✅ 부캐 점수 병합
        df_main = df_main.merge(sub_sums, how="left", left_on="nickname", right_on="main_nickname")

        # ✅ 본캐 점수 처리 (안전하게)
        for col in ["suro_score", "flag_score", "mission_point"]:
            if col not in df_main.columns:
                df_main[col] = 0
            df_main[col] = df_main[col].fillna(0).astype(int)

            sub_col = col + "_y"
            if sub_col in df_main.columns:
                df_main[f"{col}_sub"] = df_main[sub_col].fillna(0).astype(int)
                df_main[col] = df_main[col] + df_main[f"{col}_sub"]

        # ✅ 정리
        df_main.drop(columns=[c for c in df_main.columns if "_y" in c or "_sub" in c or c == "main_nickname"], inplace=True)

        # ✅ 합계 점수 계산
        df_main["event_sum"] = (
            (df_main["suro_score"] // 5000) +
            (df_main["flag_score"] // 1000) +
            (df_main["mission_point"] // 10)
        )

        # ✅ 정렬
        df_main = df_main.sort_values(
            by=["position", "nickname"],
            key=lambda x: x.map(get_position_priority) if x.name == "position" else x.map(korean_first_sort)
        ).reset_index(drop=True)

        df_main["ID"] = df_main.index + 1


        id_map = df_main.set_index("ID")["id"].to_dict()

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

        if "show_all_mainmembers" not in st.session_state:
            st.session_state["show_all_mainmembers"] = False

        show_all = st.session_state["show_all_mainmembers"]

        btn_label = "🔽 전체 보기" if not show_all else "🔼 일부만 보기"
        if st.button(btn_label, key="toggle_mainmember_display"):
            st.session_state["show_all_mainmembers"] = not show_all
            st.rerun()

        height_value = None if show_all else 210

        st.markdown("### 📋 악마 길드 길드컨트롤 등록현황")
        edited_df = st.data_editor(
            df_display,
            use_container_width=True,
            disabled=["닉네임"],
            num_rows="dynamic",
            height=height_value,
            key="main_editor"
        )

        column_map = {
            "직위": "position",
            "수로 점수": "suro_score",
            "플래그 점수": "flag_score",
            "주간미션포인트": "mission_point",
            "합계": "event_sum"
        }
        original_cols = list(column_map.values())

        st.markdown("""
        <style>
        div[data-testid="stDataEditorContainer"] { margin-bottom: 0px !important; }
        .tight-space { margin-top: -40px; }
        .uniform-btn button {
            height: 38px !important;
            width: 100%;
            white-space: nowrap;
            font-size: 14px;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="tight-space">', unsafe_allow_html=True)
        button_cols = st.columns([1, 0.8, 0.8, 1.1, 1.1, 1.1, 0.8])

        with button_cols[0]:
            st.markdown('<div class="uniform-btn">', unsafe_allow_html=True)
            if st.button("💾 저장", key="save_main_edit"):
                for idx, row in edited_df.iterrows():
                    row_id = id_map.get(idx)
                    if not row_id:
                        st.warning(f"❗ ID 매핑 실패: {idx}")
                        continue

                    updated = {eng: row[kor] for kor, eng in column_map.items()}
                    original = df_main[df_main["id"] == row_id][original_cols].iloc[0]
                    if not original.equals(pd.Series(updated)):
                        success = update_mainmember(row_id, updated)
                        if success:
                            st.success(f"✅ `{row['닉네임']}` 수정 완료")
                        else:
                            st.error(f"❌ `{row['닉네임']}` 수정 실패: {updated}")
                            st.code(f"패치 URL: {SUPABASE_URL}/rest/v1/MainMembers?id=eq.{row_id}")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        for i in [1, 2]:
            with button_cols[i]:
                st.empty()

        with button_cols[3]:
            st.markdown('<div class="uniform-btn">', unsafe_allow_html=True)
            if st.button("수로 초기화", key="reset_suro"):
                for row in df_main.itertuples():
                    update_mainmember(row.id, {"suro_score": 0})
                st.success("✅ 수로 점수 초기화")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with button_cols[4]:
            st.markdown('<div class="uniform-btn">', unsafe_allow_html=True)
            if st.button("플래그 초기화", key="reset_flag"):
                for row in df_main.itertuples():
                    update_mainmember(row.id, {"flag_score": 0})
                st.success("✅ 플래그 점수 초기화")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with button_cols[5]:
            st.markdown('<div class="uniform-btn">', unsafe_allow_html=True)
            if st.button("주간미션 초기화", key="reset_mission"):
                for row in df_main.itertuples():
                    update_mainmember(row.id, {"mission_point": 0})
                st.success("✅ 주간미션 초기화")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with button_cols[6]:
            st.markdown('<div class="uniform-btn">', unsafe_allow_html=True)
            if st.button("합계 초기화", key="reset_total"):
                for row in df_main.itertuples():
                    update_mainmember(row.id, {"event_sum": 0})
                st.success("✅ 합계 점수 초기화")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)



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
        suro_score = st.number_input("수로 점수", min_value=0, step=1)
        flag_score = st.number_input("플래그 점수", min_value=0, step=1)
        mission_point = st.number_input("주간미션포인트", min_value=0, step=1)
        submit_sub = st.form_submit_button("부캐 등록")

        if submit_sub:
            sub_id = str(uuid.uuid4())

            if not df_sub[(df_sub["main_name"] == selected_main) & (df_sub["sub_name"] == sub_name)].empty:
                st.warning(f"⚠️ '{selected_main}'의 부캐 '{sub_name}'은 이미 등록되어 있습니다.")
            else:
                data = {
                    "sub_id": sub_id,
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
    st.markdown("### 📑 등록된 전체 부캐릭터 목록")

    if not df_sub.empty:
        # ✅ 전체 보기 토글 상태 관리
        if "show_all_submembers" not in st.session_state:
            st.session_state["show_all_submembers"] = False
        show_all = st.session_state["show_all_submembers"]
        btn_label = "🔽 전체 보기" if not show_all else "🔼 일부만 보기"
        if st.button(btn_label, key="toggle_submember_display"):
            st.session_state["show_all_submembers"] = not show_all
            st.rerun()

        # ✅ display_all_df 구성
        df_sub = df_sub.reset_index(drop=True)
        df_sub["ID"] = df_sub.index + 1
        display_all_df = df_sub.rename(columns={
            "ID": "ID",
            "guild_name1": "부캐 길드",
            "sub_name": "부캐 닉네임",
            "main_name": "본캐 닉네임",
            "suro_score": "수로 점수",
            "flag_score": "플래그 점수",
            "mission_point": "주간미션포인트"
        })

        height_value = None if show_all else 210

        # ✅ 수정 가능한 전체 표
        edited_df = st.data_editor(
            display_all_df[["ID", "부캐 길드", "부캐 닉네임", "본캐 닉네임", "수로 점수", "플래그 점수", "주간미션포인트"]],
            use_container_width=True,
            height=height_value,
            disabled=["ID", "부캐 닉네임", "본캐 닉네임"],
            num_rows="dynamic",
            key="submember_editor"
        )

        button_cols = st.columns([1, 0.8, 0.8, 0.8, 0.8, 1, 1.1])
        with button_cols[0]:
            if st.button("💾 저장"):
                invalid_found = False
                for idx, row in edited_df.iterrows():
                    guild_name = row["부캐 길드"]
                    if not guild_name or guild_name not in guild_options:
                        st.warning(f"❌ `{row['부캐 닉네임']}`의 길드 이름이 잘못되었습니다. 확인해주세요.")
                        invalid_found = True
                        break

                if not invalid_found:
                    for idx, row in edited_df.iterrows():
                        sub_id = df_sub.iloc[idx]["sub_id"]
                        update_data = {
                            "guild_name1": row["부캐 길드"],
                            "suro_score": row["수로 점수"],
                            "flag_score": row["플래그 점수"],
                            "mission_point": row["주간미션포인트"]
                        }
                        update_submember(sub_id, update_data)
                    st.success("✅ 수정 완료!")
                    st.rerun()

        # 1~3번 열은 비워둠
        for i in [1, 2, 3]:
            with button_cols[i]:
                st.empty()

        # 수로/플래그/미션 삭제 버튼은 해당 컬럼 위치에 정확히 맞춰 배치
        with button_cols[4]:
            st.markdown('<div class="small-button">', unsafe_allow_html=True)
            if st.button("수로 초기화"):
                for row in df_sub.itertuples():
                    update_submember(row.sub_id, {"suro_score": 0})
                st.success("✅ 수로 점수가 초기화되었습니다.")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with button_cols[5]:
            st.markdown('<div class="small-button">', unsafe_allow_html=True)
            if st.button("플래그 초기화"):
                for row in df_sub.itertuples():
                    update_submember(row.sub_id, {"flag_score": 0})
                st.success("✅ 플래그 점수가 초기화되었습니다.")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with button_cols[6]:
            st.markdown('<div class="small-button">', unsafe_allow_html=True)
            if st.button("주간미션 초기화"):
                for row in df_sub.itertuples():
                    update_submember(row.sub_id, {"mission_point": 0})
                st.success("✅ 주간미션포인트가 초기화되었습니다.")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("등록된 부캐릭터가 없습니다.")
     # ✅ 다운로드 및 초기화 버튼
    excel_data = convert_df_to_excel(display_all_df)
    st.download_button("📥 부캐릭터 목록 다운로드", data=excel_data, file_name="부캐릭터_목록.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


   # ✅ 본캐별 부캐 보기 (중복 제거 통합)
    selected_main_filter = st.selectbox("🔍 본캐 닉네임으로 검색", ["전체 보기"] + main_names, index=0, key="main_filter")

    if not df_sub.empty and "main_name" in df_sub.columns:
        for main in main_names:
            if selected_main_filter != "전체 보기" and main != selected_main_filter:
                continue

            df_main = df_sub[df_sub["main_name"] == main]
            if not df_main.empty:
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

                editable_df = st.data_editor(
                    display_df[["부캐 길드", "부캐 닉네임", "수로 점수", "플래그 점수", "주간미션포인트"]],
                    use_container_width=True,
                    disabled=["부캐 닉네임"],
                    key=f"editor_{main}"
                )

                if st.button(f"💾 `{main}` 수정 내용 저장", key=f"btn_save_{main}"):
                    for idx, row in editable_df.iterrows():
                        sub_id = df_main.iloc[idx]["sub_id"]
                        update_data = {
                            "guild_name1": row["부캐 길드"],
                            "suro_score": row["수로 점수"],
                            "flag_score": row["플래그 점수"],
                            "mission_point": row["주간미션포인트"]
                        }
                        update_submember(sub_id, update_data)
                    st.success(f"✅ {main} 부캐 정보 수정 완료!")
                    st.rerun()

                # ✅ 관리자 전용 확장 수정
                with st.expander(f"✏️ {main} 부캐 수정"):
                    sub_names = df_main["sub_name"].tolist()
                    selected_sub_filter = st.selectbox("🔍 수정할 부캐 선택", sub_names, key=f"select_sub_{main}")

                    selected_row = df_main[df_main["sub_name"] == selected_sub_filter].iloc[0]
                    sub = selected_row["sub_id"]

                    new_guild_name = st.selectbox("부캐 길드", options=guild_options,
                                                index=guild_options.index(selected_row.get("guild_name1", "길드A")),
                                                key=f"guild_{sub}")
                    new_suro_score = st.number_input("수로 점수", value=selected_row.get("suro_score", 0),
                                                    min_value=0, step=1, key=f"suro_{sub}")
                    new_flag_score = st.number_input("플래그 점수", value=selected_row.get("flag_score", 0),
                                                    min_value=0, step=1, key=f"flag_{sub}")
                    new_mission = st.number_input("주간미션포인트", value=selected_row.get("mission_point", 0),
                                                min_value=0, step=1, key=f"mission_{sub}")

                    if st.button("저장", key=f"btn_save_individual_{sub}"):
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
                            st.error("❌ 수정 실패")

                    if st.button("삭제", key=f"btn_delete_{sub}"):
                        if delete_submember(sub):
                            st.success("🗑 삭제 완료")
                            st.rerun()
                        else:
                            st.error("삭제 실패")
    else:
        st.info("등록된 부캐릭터가 없습니다.")


elif menu == "이벤트 이미지 등록":
    st.subheader("🎯 이벤트 배너 등록 및 수정")

    # ✅ 공통 이미지 폴더 설정
    image_folder = "이벤트이미지폴더"
    available_images = ["이미지 없음"] + [
        f for f in os.listdir(image_folder)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    # --------------------------
    # 📌 신규 이벤트 등록 섹션
    # --------------------------
    st.markdown("새 이벤트 등록")

    new_title = st.text_input("이벤트 제목을 입력하세요", key="reg_title")
    new_desc = st.text_area("이벤트 설명을 입력하세요", key="reg_desc")
    new_image = st.selectbox("이벤트 이미지 선택", available_images, key="reg_image")
    st.info('''
            🔹 등록하기 누르면 안된거 같아도 올라간거에요''')

    if st.button("📤 등록하기", key="reg_submit"):
        if not new_title:
            st.warning("제목을 입력해주세요.")
        else:
            data = {
                "title": new_title,
                "description": new_desc,
                "image_file_name": None if new_image == "이미지 없음" else new_image
            }
            res = supabase.table("EventBanners").insert(data).execute()
            if res.data:
                st.session_state["event_created"] = True  # ✅ 등록 완료 플래그
                st.rerun()
            else:
                st.error("❌ 등록 실패. 다시 시도해주세요.")

    # --------------------------
    # ✏️ 기존 이벤트 수정 섹션
    # --------------------------
    st.markdown("---")
    st.subheader("✏️ 기존 이벤트 수정")

    res = supabase.table("EventBanners").select("*").order("created_at", desc=True).execute()
    event_list = res.data or []

    if not event_list:
        st.info("등록된 이벤트가 없습니다.")
    else:
        display_names = [f"{ev['title']} ({ev['id']})" for ev in event_list]
        selected_name = st.selectbox("수정할 이벤트 선택", display_names, key="edit_selector")
        selected_event = next((ev for ev in event_list if f"{ev['title']} ({ev['id']})" == selected_name), None)

        # ✅ 이 부분은 그대로 유지
        if selected_event:
            edited_title = st.text_input("제목 수정", value=selected_event["title"], key="edit_title")
            edited_desc = st.text_area("내용 수정", value=selected_event.get("description", ""), key="edit_desc")
            edited_image = st.selectbox("이미지 수정", available_images,
                                        index=available_images.index(selected_event.get("image_file_name", "이미지 없음"))
                                        if selected_event.get("image_file_name") in available_images else 0,
                                        key="edit_image")

            # ✅ 여기서부터 통째로 바꿔줘
            col1, col2 = st.columns(2)

            with col1:
                if st.button("✏️ 수정 완료", key="edit_confirm"):
                    update_data = {
                        "title": edited_title,
                        "description": edited_desc,
                        "image_file_name": None if edited_image == "이미지 없음" else edited_image
                    }
                    update_res = supabase.table("EventBanners").update(update_data).eq("id", selected_event["id"]).execute()
                    if update_res:
                        st.success("✅ 이벤트 수정 완료!")
                        st.rerun()
                    else:
                        st.error("❌ 수정 실패. 다시 시도해주세요.")

            with col2:
                if st.button("🗑️ 삭제하기", key="delete_event"):
                    delete_res = supabase.table("EventBanners").delete().eq("id", selected_event["id"]).execute()
                    if delete_res:
                        st.success("🗑️ 삭제 완료!")
                        st.rerun()
                    else:
                        st.error("❌ 삭제 실패. 다시 시도해주세요.")



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
        guild_name1 = st.selectbox("부캐릭터 길드", guild_options)

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
                    "sub_id": sub_id,
                    "sub_name": sub_name,
                    "guild_name1": guild_name1,
                    "main_name": nickname,
                    "suro_score": 0,
                    "flag_score": 0,
                    "mission_point": 0,
                    "created_by": nickname
                }
                if insert_submember(new_sub_data):
                    if guild_name1 == "악마":
                        existing_main = supabase.table("MainMembers").select("nickname").eq("nickname", sub_name.strip()).execute()
                        if not existing_main.data:
                            supabase.table("MainMembers").insert({
                                "nickname": sub_name.strip(),
                                "position": "길드원",
                                "suro_score": 0,
                                "flag_score": 0,
                                "mission_point": 0,
                                "event_sum": 0
                            }).execute()

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
            "길드 선택",
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
    🔹가입된 부캐릭터 미 등록시 이용이 제한될 수 있습니다.\n
    🔹대충 아무렇게 적어놓은 공지사항\n
    🔹대충 많이 이용해 달라는 글
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
        main_check = supabase.table("MainMembers").select("nickname").eq("nickname", nickname).execute()
        if main_check.data:
            selected_borrower = nickname
            st.markdown(f"#### 👤 대여자: `{selected_borrower}`")
        else:
            st.warning("⚠️ 닉네임이 등록되어 있지 않습니다.")
            st.stop()
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
        main_check = supabase.table("MainMembers").select("nickname").eq("nickname", nickname).execute()
        if main_check.data:
            selected_borrower = nickname
            st.markdown(f"#### 👤 대여자: `{selected_borrower}`")
        else:
            st.warning("⚠️ 닉네임이 등록되어 있지 않습니다.")
            st.stop()

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
elif menu == "마니또 관리":
    st.subheader("🎯 마니또 관리 페이지")

    # ✅ 전체 신청 데이터 불러오기
    res = supabase.table("ManiddoRequests").select("*").execute()
    all_requests = res.data or []
    df = pd.DataFrame(all_requests)

    # ✅ 여기 ↓↓↓ 아래에 이 코드 넣기
    mainmembers = get_mainmembers()
    guild_nicks = sorted([m["nickname"] for m in mainmembers if m.get("nickname")])

    # 중복/매칭된 인원 제외
    used_names = set()
    for r in all_requests:
        if r.get("tutor_name"):
            used_names.add(r["tutor_name"])
        if r.get("tutee_name"):
            used_names.add(r["tutee_name"])

    available_tutors = [n for n in guild_nicks if n not in used_names]
    available_tutees = [n for n in guild_nicks if n not in used_names]

    # ✅ 기존 튜터/튜티 등록 폼에 적용
    with st.form("tutor_form"):
        st.subheader("✅ 튜터 등록")
        new_tutor = st.selectbox("튜터 선택 (악마길드원만)", available_tutors, key="select_tutor")
        submit_tutor = st.form_submit_button("튜터 등록")
        if submit_tutor and new_tutor:
            supabase.table("ManiddoRequests").insert({"tutor_name": new_tutor}).execute()
            st.success(f"튜터 '{new_tutor}' 등록 완료!")
            st.rerun()

    with st.form("tutee_form"):
        st.subheader("✅ 튜티 등록")
        new_tutee = st.selectbox("튜티 선택 (악마길드원만)", available_tutees, key="select_tutee")
        submit_tutee = st.form_submit_button("튜티 등록")
        if submit_tutee and new_tutee:
            supabase.table("ManiddoRequests").insert({"tutee_name": new_tutee}).execute()
            st.success(f"튜티 '{new_tutee}' 등록 완료!")
            st.rerun()

    # ✅ 등록된 목록 보기
    res = supabase.table("ManiddoRequests").select("*").execute()
    all_requests = res.data or []
    df = pd.DataFrame(all_requests)
    is_tutor = any((r.get("tutor_name") == nickname) for r in all_requests)

    # ✅ 튜터/튜티 목록 필터링
    df_tutors = df[df["tutor_name"].notna() & df["tutee_name"].isna()].reset_index(drop=True)
    df_tutees = df[df["tutee_name"].notna() & df["tutor_name"].isna()].reset_index(drop=True)
    df_matched = df[df["tutor_name"].notna() & df["tutee_name"].notna()].reset_index(drop=True)

    # ✅ 좌우 컬럼 배치
    tutor_col, tutee_col = st.columns(2)

    with tutor_col:
        st.markdown("### 🧑‍🏫 튜터 목록")
        st.markdown("🔷 신청한 튜터 목록")
        st.dataframe(df_tutors[["tutor_name"]], use_container_width=True)

    with tutee_col:
        st.markdown("### 🧑‍🎓 튜티 목록")
        st.markdown("🔶 신청한 튜티 목록")
        st.dataframe(df_tutees[["tutee_name"]], use_container_width=True)

    # ✅ 튜터/튜티 선택해서 매칭 등록

    # 1. 매칭되지 않은 튜터/튜티 필터링
    unmatched_tutors = df[df["tutor_name"].notna() & df["tutee_name"].isna()]["tutor_name"].unique()
    unmatched_tutees = df[df["tutee_name"].notna() & df["tutor_name"].isna()]["tutee_name"].unique()

    # 2. 이미 매칭된 튜터/튜티 추출
    matched_df = df[df["tutor_name"].notna() & df["tutee_name"].notna()]
    matched_tutors = matched_df["tutor_name"].unique()
    matched_tutees = matched_df["tutee_name"].unique()

    # 3. 실제 선택 가능한 목록만 추림
    available_tutors = [t for t in unmatched_tutors if t not in matched_tutors]
    available_tutees = [t for t in unmatched_tutees if t not in matched_tutees]

    left_col, right_col = st.columns([1, 1])

    with left_col:
        st.markdown("### 🔗 튜터 - 튜티 매칭 등록")
        if available_tutors:
            selected_tutor = st.selectbox("튜터 선택", available_tutors, key="match_tutor")
        else:
            selected_tutor = None
            st.warning("⚠️ 진행 가능한 튜터가 없습니다.")

        if available_tutees:
            selected_tutee = st.selectbox("튜티 선택", available_tutees, key="match_tutee")
        else:
            selected_tutee = None
            st.warning("⚠️ 진행 가능한 튜티가 없습니다.")

        # ✅ 매칭 등록 버튼 누르면 ManiddoRequests + ManiddoLogs 동시 등록
        if selected_tutor and selected_tutee and st.button("📌 매칭 등록"):
            now = datetime.now().isoformat()

            # 1. ManiddoRequests에 등록
            supabase.table("ManiddoRequests").insert({
                "tutor_name": selected_tutor,
                "tutee_name": selected_tutee,
                "timestamp": now
            }).execute()

            # 2. ManiddoLogs에도 초기 로그 생성
            supabase.table("ManiddoLogs").insert({
                "tutor_name": selected_tutor,
                "tutee_name": selected_tutee,
                "memo": "",  # 초기 메모 없음
                "image_urls": [],
                "created_at": now,
                "updated_at": now
            }).execute()

            st.success(f"매칭 완료: 튜터 {selected_tutor} - 튜티 {selected_tutee}")
            st.rerun()

    with right_col:
        st.markdown("### 🗑 정보 관리")
        delete_target_type = st.radio("삭제할 대상 선택", ["튜터", "튜티"], horizontal=True)
        if delete_target_type == "튜터":
            tutor_names = df[df["tutor_name"].notna()]["tutor_name"].unique().tolist()
            selected_delete = st.selectbox("삭제할 튜터 선택", tutor_names, key="delete_tutor")
        else:
            tutee_names = df[df["tutee_name"].notna()]["tutee_name"].unique().tolist()
            selected_delete = st.selectbox("삭제할 튜티 선택", tutee_names, key="delete_tutee")

        if st.button("❌ 삭제하기"):
            if delete_target_type == "튜터":
                supabase.table("ManiddoRequests").delete().eq("tutor_name", selected_delete).execute()
            else:
                supabase.table("ManiddoRequests").delete().eq("tutee_name", selected_delete).execute()
            st.success(f"{delete_target_type} '{selected_delete}' 삭제 완료")
            st.rerun()

    # 4. 매칭된 목록 출력 및 수정
    st.subheader("📋 매칭된 마니또 목록")
    if not matched_df.empty:
        view_df = matched_df.copy().reset_index(drop=True)
        view_df["튜터"] = view_df["tutor_name"]
        view_df["튜티"] = view_df["tutee_name"]
        view_df["기록"] = view_df.get("memo", "")
        display_df = view_df[["튜터", "튜티"]]
        st.dataframe(display_df, use_container_width=True)

        # 관리자 또는 튜터만 수정 가능
        if is_admin:
            st.markdown("### 📂 확인할 마니또 기록 열람")

            # ✅ 튜터-튜티 쌍 목록 가져오기
            pair_options = [
                f"튜터: {r['tutor_name']} - 튜티: {r['tutee_name']}"
                for r in all_requests
                if r.get("tutor_name") and r.get("tutee_name")
            ]
            selected_pair = st.selectbox("열람할 마니또 선택", ["선택하지 않음"] + pair_options)

            if selected_pair != "선택하지 않음":
                selected_tutor, selected_tutee = selected_pair.replace("튜터: ", "").replace("튜티: ", "").split(" - ")

                # ✅ 해당 튜터-튜티 쌍의 로그 불러오기
                res_logs = supabase.table("ManiddoLogs").select("*").execute()
                all_logs = res_logs.data or []

                logs = [
                    log for log in all_logs
                    if log.get("tutor_name") == selected_tutor and log.get("tutee_name") == selected_tutee
                    and (log.get("title") or log.get("memo") or log.get("image_urls"))
                ]
                logs = [log for log in logs if "created_at" in log and log["created_at"]]
                logs = sorted(logs, key=lambda x: x["created_at"], reverse=True)

                col_del, _ = st.columns([2, 8])
                with col_del:
                    if st.button("❌ 마니또 종료", use_container_width=True):
                        if selected_pair == "선택하지 않음":
                            st.warning("⚠️ 마니또를 선택해주세요.")
                        elif selected_pair.startswith("튜터: ") and " - 튜티: " in selected_pair:
                            tutor_name, tutee_name = selected_pair.replace("튜터: ", "").split(" - 튜티: ")
                            tutor_name = tutor_name.strip()
                            tutee_name = tutee_name.strip()

                            st.write(f"삭제 시도 중: '{tutor_name}' '{tutee_name}'")

                            # ✅ ManiddoLogs 삭제
                            supabase.table("ManiddoLogs").delete()\
                                .eq("tutor_name", tutor_name)\
                                .eq("tutee_name", tutee_name)\
                                .execute()

                            # ✅ ManiddoRequests 삭제
                            supabase.table("ManiddoRequests").delete()\
                                .eq("tutor_name", tutor_name)\
                                .eq("tutee_name", tutee_name)\
                                .execute()

                            st.success(f"🧹 {tutor_name} - {tutee_name} 마니또가 완전히 종료되었습니다.")
                            st.rerun()
                st.markdown("----")
                st.markdown("### 📚 마니또 기록 목록 (관리자 전용)")

                # ✅ 기록 선택 셀렉트박스
                kst = timezone(timedelta(hours=9))
                log_titles = [
                    f"{log.get('title') or '(무제목)'} ({datetime.fromisoformat(log['created_at']).astimezone(kst).strftime('%Y-%m-%d %H:%M:%S')})"
                    for log in logs
                ]
                selected_title = st.selectbox("🔍 열람할 기록 선택", ["선택하지 않음"] + log_titles)

                if selected_title != "선택하지 않음":
                    selected_log = logs[log_titles.index(selected_title)]
                    created_at_kst = datetime.fromisoformat(selected_log['created_at']).astimezone(kst).strftime('%Y-%m-%d %H:%M:%S')

                    st.markdown(f"#### 🕒 작성일시: {created_at_kst}")
                    st.markdown(f"### 📌 {selected_log.get('title', '(무제목)')}")
                    st.markdown(selected_log.get("memo", ""))

                    if selected_log.get("image_urls"):
                        for url in selected_log["image_urls"]:
                            st.image(url, width=250)
                            st.markdown(f"[🔍 원본 보기]({url})", unsafe_allow_html=True)

                    col1, col2 = st.columns(2)
                    with col2:
                        if st.button("🗑 삭제하기", key=f"delete_admin_{selected_log['id']}"):
                            supabase.table("ManiddoLogs").delete().eq("id", selected_log["id"]).execute()
                            st.success("🧹 삭제 완료")
                            st.rerun()

                else:
                    # ✅ 전체 기록 보기 (2열 배치)
                    cols = st.columns(2)
                    for idx, log in enumerate(logs):
                        with cols[idx % 2]:
                            created_at_kst = datetime.fromisoformat(log["created_at"]).astimezone(kst).strftime('%Y-%m-%d %H:%M:%S')
                            st.markdown(f"### 📌 {log.get('title', '(무제목)')}")
                            st.markdown(f"🕒 {created_at_kst}")
                            st.markdown(log.get("memo", "")[:100] + "...")

                            if log.get("image_urls"):
                                st.image(log["image_urls"][0], width=150)
                                st.markdown(f"[🔍 원본 보기]({log['image_urls'][0]})", unsafe_allow_html=True)

                            if st.button("🗑 삭제하기", key=f"delete_admin_{log['id']}"):
                                supabase.table("ManiddoLogs").delete().eq("id", log["id"]).execute()
                                st.success("🧹 삭제 완료")
                                st.rerun()



    else:
        st.info("🙅 현재 매칭된 마니또가 없습니다.")


elif menu == "마니또 기록":
    st.title("📘 마니또 기록 페이지")
    nickname = st.session_state.get("nickname", "")
    is_admin = nickname in ADMIN_USERS

    # ✅ 전체 매칭 데이터 조회
    res_req = supabase.table("ManiddoRequests").select("*").execute()
    all_requests = res_req.data or []

    matched = next(
        (
            r for r in all_requests
            if (r.get("tutor_name") and r.get("tutee_name")) and
               (nickname == r["tutor_name"] or nickname == r["tutee_name"])
        ),
        None
    )

    if not matched:
        st.warning("🙅‍♀️ 아직 매칭이 완료되지 않았습니다. 관리자에게 문의하세요.")
    else:
        tutor = matched["tutor_name"]
        tutee = matched["tutee_name"]
        st.subheader(f"🧑‍🏫 튜터: {tutor} - 🎓 튜티: {tutee} 마니또 진행중")

        with st.form("write_form"):
            title = st.text_input("제목")
            memo = st.text_area("기록", height=150)
            images = st.file_uploader("새 이미지 업로드", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

            if st.form_submit_button("💾 등록"):
                if not title.strip() and not memo.strip() and not images:
                    st.warning("📌 제목, 내용 또는 이미지를 입력해주세요.")
                else:
                    urls = []
                    for img in images:
                        try:
                            ext = img.name.split(".")[-1]
                            file_id = f"{uuid.uuid4()}.{ext}"
                            path = f"{file_id}"
                            content = img.read()
                            supabase.storage.from_("maniddo-images").upload(path, content)
                            public_url = f"{SUPABASE_URL}/storage/v1/object/public/maniddo-images/{path}"
                            urls.append(public_url)
                        except Exception as e:
                            st.error(f"❌ 이미지 업로드 실패: {e}")

                    supabase.table("ManiddoLogs").insert({
                        "tutor_name": tutor,
                        "tutee_name": tutee,
                        "title": title,
                        "memo": memo or "",
                        "image_urls": urls,
                        "created_at": datetime.now(KST).isoformat(),
                        "updated_at": datetime.now(KST).isoformat()
                    }).execute()
                    st.success("✅ 기록이 저장되었습니다.")
                    st.rerun()

        res_logs = supabase.table("ManiddoLogs").select("*").execute()
        all_logs = res_logs.data or []
        my_logs = [
            log for log in all_logs
            if (nickname == log.get("tutor_name") or nickname == log.get("tutee_name"))
            and (log.get("title") or log.get("memo") or log.get("image_urls"))
        ]
        my_logs = [log for log in my_logs if "created_at" in log and log["created_at"]]
        my_logs = sorted(my_logs, key=lambda x: x["created_at"], reverse=True)

        st.markdown("---")
        st.markdown("### 📚 마니또 기록 목록")
        st.info('''
                🔹 확인할 기록에서 수정하고 싶은 기록을 선택하세요 \n
                🔹 수정하기 버튼을 눌러도 동작하지 않으면 한 번 더 눌러주세요
                ''')

        log_options = {f"{log.get('title') or '(무제목)'}": log for log in my_logs}
        selected_title = st.selectbox("🔍 확인할 기록 선택", ["선택하지 않음"] + list(log_options.keys()))

        if selected_title != "선택하지 않음":
            log = log_options[selected_title]
            log_id = log["id"]
            is_editing = st.session_state.get(f"edit_{log_id}", False)

            if is_editing:
                st.markdown("### ✏ 기록 수정")

                new_title = st.text_input("제목", value=log.get("title", ""), key=f"title_edit_{log_id}")
                new_memo = st.text_area("기록", value=log.get("memo", ""), height=150, key=f"memo_edit_{log_id}")
                new_images = st.file_uploader("새 이미지 업로드", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"img_edit_{log_id}")

                original_urls = log.get("image_urls", []) or []

                if original_urls:
                    st.markdown("#### 기존 이미지 (❌ 버튼으로 삭제)")
                    for i, url in enumerate(original_urls):
                        if st.session_state.get(f"delete_img_{log_id}_{i}", False):
                            continue  # 삭제 표시된 건 숨김
                        col1, col2 = st.columns([10, 1])
                        with col1:
                            st.image(url, width=200)
                        with col2:
                            if st.button("❌", key=f"remove_img_{log_id}_{i}"):
                                st.session_state[f"delete_img_{log_id}_{i}"] = True
                                st.rerun()

                # 수정 완료 버튼
                if st.button("💾 수정 완료", key=f"save_edit_{log_id}"):
                    keep_urls = [
                        url for i, url in enumerate(original_urls)
                        if not st.session_state.get(f"delete_img_{log_id}_{i}", False)
                    ]
                    for img in new_images:
                        try:
                            ext = img.name.split(".")[-1]
                            file_id = f"{uuid.uuid4()}.{ext}"
                            path = f"{file_id}"
                            content = img.read()
                            supabase.storage.from_("maniddo-images").upload(path, content)
                            public_url = f"{SUPABASE_URL}/storage/v1/object/public/maniddo-images/{path}"
                            keep_urls.append(public_url)
                        except Exception as e:
                            st.error(f"❌ 이미지 업로드 실패: {e}")

                    supabase.table("ManiddoLogs").update({
                        "title": new_title,
                        "memo": new_memo,
                        "image_urls": keep_urls,
                        "updated_at": datetime.now(KST).isoformat()
                    }).eq("id", log_id).execute()

                    st.success("✅ 수정이 완료되었습니다.")
                    st.session_state[f"edit_{log_id}"] = False
                    st.rerun()

            else:
                st.markdown(f"#### 🕒 작성일시: {log['created_at'][:19].replace('T',' ')} (KST)")
                st.markdown(f"#### 📌 {log.get('title', '')}")
                st.markdown(log.get("memo", ""))
                for url in log.get("image_urls", []):
                    st.image(url, width=250)
                    st.markdown(f"[🔍 원본 보기]({url})", unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏ 수정하기", key=f"edit_button_{log_id}"):
                        # ✅ 수정 진입 시 삭제 상태 초기화
                        for i in range(len(log.get("image_urls", []))):
                            st.session_state[f"delete_img_{log_id}_{i}"] = False
                        st.session_state[f"edit_{log_id}"] = True
                with col2:
                    if st.button("🗑 삭제하기", key=f"delete_button_{log_id}"):
                        supabase.table("ManiddoLogs").delete().eq("id", log_id).execute()
                        st.success("🧹 삭제 완료")
                        st.rerun()
        else:
            cols = st.columns(2)
            for idx, log in enumerate(my_logs):
                with cols[idx % 2]:
                    st.markdown(f"📌 {log.get('title', '')}")
                    st.markdown(f"{log['memo'][:30]}...")
                    if log.get("image_urls"):
                        st.image(log["image_urls"][0], width=150)
                        st.markdown(f"[🔍 원본 보기]({log['image_urls'][0]})", unsafe_allow_html=True)
                    if st.button("🗑 삭제하기", key=f"delete_{log['id']}"):
                        supabase.table("ManiddoLogs").delete().eq("id", log["id"]).execute()
                        st.success("🧹 삭제 완료")
                        st.rerun()

elif menu == "이벤트 목록":
    st.subheader("📅 진행 중인 길드 이벤트")

    try:
        res = supabase.table("EventBanners").select("*").order("id", desc=True).execute()
        event_list = res.data if res.data else []
    except Exception as e:
        st.error("❌ 이벤트 목록 불러오기 실패")
        event_list = []

    selected_event = st.session_state.get("selected_event")
    if selected_event:
        selected = next((ev for ev in event_list if ev["id"] == selected_event), None)
        if selected:
            st.markdown(f"## {selected['title']}")
            st.markdown(selected.get("description", ""))

            image_name = selected.get("image_file_name")
            if image_name and image_name.lower() != "이미지 없음":
                image_path = os.path.join("이벤트이미지폴더", image_name)
                if os.path.exists(image_path):
                    st.image(image_path, width=500)
                else:
                    st.warning("❗ 이미지 파일이 존재하지 않습니다.")

            if st.button("← 목록으로 돌아가기"):
                del st.session_state["selected_event"]
                st.rerun()
        else:
            st.warning("선택한 이벤트를 찾을 수 없습니다.")
    else:
        for i in range(0, len(event_list), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                if i + j < len(event_list):
                    ev = event_list[i + j]
                    with col:
                        image_name = ev.get("image_file_name")
                        if image_name and image_name.lower() != "이미지 없음":
                            image_path = os.path.join("이벤트이미지폴더", image_name)
                            if os.path.exists(image_path):
                                st.image(image_path, width=300)
                            else:
                                st.warning("❗ 이미지 없음")
                        st.markdown(f"**{ev['title']}**")
                        if st.button("자세히 보기", key=f"event_detail_{ev['id']}"):
                            st.session_state["selected_event"] = ev["id"]
                            st.rerun()






    

# elif menu == "캐릭터 정보 검색":
#     show_character_viewer()

          