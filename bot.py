import os
import time
import discord
import asyncio
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone
from discord.ext import commands
from discord import app_commands
import discord
from discord.ext import commands
import asyncio
from datetime import datetime



# ✅ 환경 변수 불러오기
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # 보조무기 채널 ID
DROPITEM_CHANNEL_ID = int(os.getenv("DROPITEM_CHANNEL_ID"))
MANITTO_CHANNEL_ID = int(os.getenv("MANITTO_CHANNEL_ID"))


# ✅ 멘션할 유저 ID 리스트
MENTION_USERS_WEAPON = [380952595293929473, 339743306802135041]  # 보조무기 담당자
MENTION_USERS_DROP = [339743306802135041]    # 드메템 담당자

# ✅ 멘션 메시지 생성 함수
def get_mentions(user_ids):
    return " ".join([f"<@{uid}>" for uid in user_ids])
    

# ✅ Supabase 클라이언트 생성
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ Discord 클라이언트 설정
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ✅ 상태 저장용
last_weapon_ids = set()
last_weapon_data = {}
last_dropitem_ids = set()
last_dropitem_data = {}

# ✅ 작동 시간 확인 함수 (04:00 ~ 12:00 비활성)
def is_active_time():
    kst_now = datetime.now(timezone.utc) + timedelta(hours=9)
    hour = kst_now.hour
    print(f"[DEBUG] 현재 한국 시간: {kst_now.strftime('%Y-%m-%d %H:%M:%S')} / 작동여부: {not (4 <= hour < 12)}")
    return not (4 <= hour < 12)

# ✅ ⏱ 자동 종료 함수
async def auto_shutdown_during_sleep():
    while True:
        now_kst = (datetime.now(timezone.utc) + timedelta(hours=9)).hour
        if 4 <= now_kst < 12:
            print("⏱️ 현재는 작동 중지 시간 (04~12시)이므로 봇을 종료합니다.")
            await client.close()
            break
        await asyncio.sleep(300)


# ✅ 폴링 루프
async def polling_loop():
    await client.wait_until_ready()
    last_weapon_ids = set()
    last_weapon_data = {}
    last_dropitem_ids = set()
    last_dropitem_data = {}
    # ✅ 디스코드 채널 선언 (channel_id는 .env에서)
    weapon_channel = client.get_channel(int(os.getenv("CHANNEL_ID")))
    dropitem_channel = client.get_channel(int(os.getenv("DROPITEM_CHANNEL_ID")))
    manitto_channel = client.get_channel(int(os.getenv("MANITTO_CHANNEL_ID")))

    while not client.is_closed():
        try:
            # ✅ 보조무기 감시
            weapon_res = supabase.table("Weapon_Rentals").select("*").order("id", desc=True).limit(20).execute()
            current_weapon_ids = set()
            current_weapon_data = {}

            for row in weapon_res.data:
                row_id = row["id"]
                current_weapon_ids.add(row_id)
                current_weapon_data[row_id] = row

            if not last_weapon_ids:
                last_weapon_ids = current_weapon_ids
                last_weapon_data = current_weapon_data
                print("🚫 [Weapon] 첫 실행이므로 상태 초기화만 수행")
            else:
                weapon_new_ids = current_weapon_ids - last_weapon_ids
                for new_id in weapon_new_ids:
                    data = current_weapon_data[new_id]
                    if data.get("is_edit"):
                        msg = f"{get_mentions(MENTION_USERS_DROP)}📌 `{data['borrower']}`님이 신청한 `{data['weapon_name']}` 대여 정보가 수정되었습니다."
                    else:
                        msg = f"{get_mentions(MENTION_USERS_WEAPON)} 📥 `{data['borrower']}`님이 `{data['weapon_name']}` 을 대여 요청하였습니다."
                    await weapon_channel.send(msg)
                    print(f"[Weapon 등록] {msg}")

                removed_ids = last_weapon_ids - current_weapon_ids
                for removed_id in removed_ids:
                    deleted_data = last_weapon_data.get(removed_id, {})
                    was_edited = any(
                        r["borrower"] == deleted_data.get("borrower") and
                        r["weapon_name"] == deleted_data.get("weapon_name") and
                        r.get("is_edit")
                        for r in current_weapon_data.values()
                    )
                    if was_edited:
                        print(f"🔁 수정에 따른 삭제 생략: {deleted_data.get('borrower')} / {deleted_data.get('weapon_name')}")
                        continue

                    now = datetime.now(timezone.utc) + timedelta(hours=9)
                    msg = f"🗑 `{deleted_data.get('borrower', '?')}`님이 대여한 `{deleted_data.get('weapon_name', '?')}` 이/가 {now.strftime('%y-%m-%d %H:%M')} 반납되었습니다."
                    await weapon_channel.send(msg)
                    print(f"[Weapon 반납] {msg}")

                last_weapon_ids = current_weapon_ids
                last_weapon_data = current_weapon_data

            # ✅ 드메템 감시
            drop_res = supabase.table("DropItem_Rentals").select("*").order("id", desc=True).limit(20).execute()
            current_drop_ids = set()
            current_drop_data = {}

            for row in drop_res.data:
                row_id = row["id"]
                current_drop_ids.add(row_id)
                current_drop_data[row_id] = row

            if not last_dropitem_ids:
                last_dropitem_ids = current_drop_ids
                last_dropitem_data = current_drop_data
                print("🚫 [DropItem] 첫 실행이므로 상태 초기화만 수행")
            else:
                drop_new_ids = current_drop_ids - last_dropitem_ids
                for new_id in drop_new_ids:
                    data = current_drop_data[new_id]
                    if data.get("is_edit"):
                        msg = f"{get_mentions(MENTION_USERS_DROP)}📌 `{data['drop_borrower']}`님이 신청한 `{data['dropitem_name']}` 대여 정보가 수정되었습니다."
                    else:
                        msg = f"{get_mentions(MENTION_USERS_DROP)} 🎁 `{data['drop_borrower']}`님이 `{data['dropitem_name']}` 을 대여 요청하였습니다."
                    await dropitem_channel.send(msg)
                    print(f"[Drop 등록] {msg}")

                removed_ids = last_dropitem_ids - current_drop_ids
                for removed_id in removed_ids:
                    data = last_dropitem_data.get(removed_id, {})
                    now = datetime.now(timezone.utc) + timedelta(hours=9)
                    msg = f"📦 `{data.get('drop_borrower', '?')}`님이 대여한 `{data.get('dropitem_name', '?')}` 이/가 {now.strftime('%y-%m-%d %H:%M')} 반납되었습니다."
                    await dropitem_channel.send(msg)
                    print(f"[Drop 반납] {msg}")

                last_dropitem_ids = current_drop_ids
                last_dropitem_data = current_drop_data

            # ✅ 마니또 신청 감시
            manitto_res = supabase.table("Manitto").select("*").eq("notified", False).execute()
            new_rows = manitto_res.data

            for row in new_rows:
                tutee = row.get("tutee_name", "Unknown")
                tutor = row.get("tutor_name", "Unknown")
                message = f"🎯 `{tutee}`님이 `{tutor}`님께 마니또 신청을 하였습니다!"

                channel = client.get_channel(int(os.getenv("MANITTO_CHANNEL_ID")))
                if channel:
                    await channel.send(message)
                    print(f"[Manitto 신청] {message}")

                # 전송 후 알림 처리 상태 업데이트
                supabase.table("Manitto").update({"notified": True}).eq("id", row["id"]).execute()

        except Exception as e:
            print(f"❌ 오류 발생: {e}")

        await asyncio.sleep(300)  # 주기적으로 반복


tree = app_commands.CommandTree(client)

# ✅ 디스코드 봇 도움말 함수
@tree.command(name="도움말", description="이 봇의 주요 명령어를 안내합니다.")
async def help_command(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🛠 사용 가능한 명령어 목록:/정보, /대여정보, /주소\n"
        "/정보 - 봇의 정보 출력\n"
        "/대여정보 [조회할 내용]- ex) /대여정보 히어로 - 히어로 보조무기 대여정보 출력 \n"
        "/주소 - 악마길드 홈페이지 주소 출력",
        #"/이벤트 - 진행중인 이벤트 내용 출력",
        ephemeral=False
    )

# ✅ 봇의 기본정보 열람 함수
@tree.command(name="정보", description="이 봇의 기본 정보를 확인합니다.")
async def info_command(interaction: discord.Interaction):
    await interaction.response.send_message(
        "이 봇은 보조무기 및 드메템 대여 관리를 위한 자동화 도우미입니다.\n"
        "KST 기준 04~12는 봇이 작동하지 않습니다.\n"
        "대여신청과 반납완료는 등록부터 알림까지 5분가량 소요됩니다.", ephemeral=False
    )

# ✅ 링크주소 열람 함수
@tree.command(name="주소", description="악마길드 홈페이지")
async def fixed_link_command(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🔗 바로가기 링크: https://maple-demon-guild.streamlit.app/",
        ephemeral=False
    )

# ✅ 대여정보 열람 함수
@tree.command(name="대여정보", description="장비명으로 현재 대여 상태를 확인합니다.")
@app_commands.describe(item="장비 이름 또는 드메템 세트 이름")
async def rental_info(interaction: discord.Interaction, item: str):
    channel_id = interaction.channel_id
    item = item.strip()

    # 💬 Supabase에서 데이터 조회
    if channel_id == CHANNEL_ID:
        res = supabase.table("Weapon_Rentals").select("*").execute()
        filtered = [r for r in res.data if item in r.get("weapon_name", "")]
    elif channel_id == DROPITEM_CHANNEL_ID:
        res = supabase.table("DropItem_Rentals").select("*").execute()
        filtered = [r for r in res.data if item in r.get("dropitem_name", "")]
    else:
        await interaction.response.send_message("⚠️ 이 채널에서는 대여 정보를 조회할 수 없습니다.")
        return

    if not filtered:
        await interaction.response.send_message(f"❌ `{item}`에 대한 대여 정보가 없습니다.")
        return

    target = filtered[0]
    borrower = target.get("borrower") or target.get("drop_borrower", "?")
    time_slots = target.get("time_slots", "").split(",")
    dates = sorted({
    datetime.strptime(s.strip().split("~")[0], "%Y-%m-%d %H:%M")
    for s in time_slots if s.strip()
    })
    date_range = (
        f"{dates[0].strftime('%Y-%m-%d %H:%M')} ~ {dates[-1].strftime('%Y-%m-%d %H:%M')}"
        if dates else "기간 정보 없음"
    )

    name = target.get("weapon_name") or target.get("dropitem_name", item)
    label = "🛡️" if channel_id == CHANNEL_ID else "\U0001F4FF"

    await interaction.response.send_message(
        f"{label} **{name}**\n대여자: `{borrower}`\n기간: `{date_range}`"
    )

# ✅ 봇 실행시 정상작동 확인 함수
@client.event
async def on_ready():
    print(f"🤖 디스코드 봇 로그인됨: {client.user}")
    await tree.sync()
    client.loop.create_task(polling_loop())
    client.loop.create_task(auto_shutdown_during_sleep())

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
