import os
import time
import discord
import asyncio
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone
from discord.ext import commands
from discord import app_commands

# ✅ 환경 변수 불러오기
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
WEAPON_CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # 보조무기 채널 ID
DROPITEM_CHANNEL_ID = int(os.getenv("DROPITEM_CHANNEL_ID"))  # 드메템 채널 ID

# ✅ 멘션할 유저 ID 리스트
MENTION_USERS_WEAPON = [380952595293929473, 339743306802135041]  # 보조무기 담당자
MENTION_USERS_DROP = [380952595293929473, 339743306802135041]    # 드메템 담당자

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

# ✅ 폴링 루프
async def polling_loop():
    global last_weapon_ids, last_weapon_data
    global last_dropitem_ids, last_dropitem_data

    await client.wait_until_ready()
    weapon_channel = client.get_channel(WEAPON_CHANNEL_ID)
    dropitem_channel = client.get_channel(DROPITEM_CHANNEL_ID)

    if not weapon_channel or not dropitem_channel:
        print("❌ 채널을 찾을 수 없습니다.")
        return

    print("✅ 채널 연결 완료")

    while not client.is_closed():
        if not is_active_time():
            print("⏰ 현재는 작동 시간이 아니므로 대기 중...")
            await asyncio.sleep(120)
            continue

        try:
            # ✅ 보조무기 데이터 확인
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
                new_ids = current_weapon_ids - last_weapon_ids
                for new_id in new_ids:
                    data = current_weapon_data[new_id]
                    msg = f"{get_mentions(MENTION_USERS_WEAPON)} 📥 `{data['borrower']}`님이 `{data['weapon_name']}` 을 대여 요청하였습니다."
                    await weapon_channel.send(msg)
                    print(f"[Weapon 등록] {msg}")

                removed_ids = last_weapon_ids - current_weapon_ids
                for removed_id in removed_ids:
                    data = last_weapon_data.get(removed_id, {})
                    now = datetime.now(timezone.utc) + timedelta(hours=9)
                    msg = f"🗑 `{data.get('borrower', '?')}`님이 대여한 `{data.get('weapon_name', '?')}` 이/가 {now.strftime('%y-%m-%d %H:%M')} 반납되었습니다."
                    await weapon_channel.send(msg)
                    print(f"[Weapon 반납] {msg}")

                last_weapon_ids = current_weapon_ids
                last_weapon_data = current_weapon_data

            # ✅ 드메템 데이터 확인
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
                new_ids = current_drop_ids - last_dropitem_ids
                for new_id in new_ids:
                    data = current_drop_data[new_id]
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

        except Exception as e:
            print(f"❌ 오류 발생: {e}")

        await asyncio.sleep(120)


# ✅ 디스코드 봇 함수
tree = app_commands.CommandTree(client)

@tree.command(name="도움말", description="이 봇의 주요 명령어를 안내합니다.")
async def help_command(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🛠 사용 가능한 명령어 목록:\n"
        "/정보 - 봇의 정보 출력\n"
        "/대여정보 - 대여 현황 요약 출력 \n"
        "/이벤트 - 진행중인 이벤트 내용 출력",
        ephemeral=True
    )

@tree.command(name="대여정보", description="현재 대여 중인 아이템을 확인합니다.")
async def rental_info(interaction: discord.Interaction):
    channel_id = interaction.channel_id

    if channel_id == WEAPON_CHANNEL_ID:
        await interaction.response.send_message("🛡 보조무기 대여 현황을 불러오는 중입니다...")
        # 🔄 여기에 Supabase에서 보조무기 요약 불러오는 코드 추가
    elif channel_id == DROPITEM_CHANNEL_ID:
        await interaction.response.send_message("🎁 드메템 대여 현황을 불러오는 중입니다...")
        # 🔄 여기에 드메템 요약 불러오는 코드 추가
    else:
        await interaction.response.send_message("⚠️ 이 채널에서는 대여 정보를 볼 수 없습니다.")

@tree.command(name="대여정보", description="특정 장비/세트의 대여 정보를 확인합니다.")
@app_commands.describe(item="직업 이름 또는 드메템 세트명")
async def rental_info(interaction: discord.Interaction, item: str):
    channel_id = interaction.channel_id
    item = item.strip()

    if channel_id == WEAPON_CHANNEL_ID:
        res = supabase.table("Weapon_Rentals").select("*").execute()
        filtered = [r for r in res.data if item in r.get("weapon_name", "")]
    elif channel_id == DROPITEM_CHANNEL_ID:
        res = supabase.table("DropItem_Rentals").select("*").execute()
        filtered = [r for r in res.data if item in r.get("dropitem_name", "")]
    else:
        await interaction.response.send_message("⚠️ 이 채널에서는 대여정보를 조회할 수 없습니다.")
        return

    if not filtered:
        await interaction.response.send_message(f"❌ `{item}`에 대한 대여 정보가 없습니다.")
        return

    target = filtered[0]
    borrower = target.get("borrower") or target.get("drop_borrower", "?")
    time_slots = target.get("time_slots", "").split(",")
    dates = sorted({s.split()[0] for s in time_slots if s.strip()})
    date_range = f"{dates[0]} ~ {dates[-1]}" if dates else "기간 정보 없음"

    label = "🛡️" if channel_id == WEAPON_CHANNEL_ID else "📿"
    name = target.get("weapon_name") or target.get("dropitem_name")

    await interaction.response.send_message(
        f"{label} **{name}**\n• 대여자: `{borrower}`\n• 기간: `{date_range}`"
    )

@client.event
async def on_ready():
    print(f"🤖 디스코드 봇 로그인됨: {client.user}")
    await tree.sync()
    client.loop.create_task(polling_loop())

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
