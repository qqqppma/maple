import os
import time
import discord
import asyncio
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone  # 🔧 추가

# ✅ 환경 변수 불러오기
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# ✅ Supabase 클라이언트 생성
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ Discord 클라이언트 설정
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ✅ 상태 저장용
last_known_ids = set()
last_known_data = {}

# ✅ 작동 시간 확인 함수 (04:00 ~ 12:00 비활성, KST 기준)
def is_active_time():
    kst_now = datetime.now(timezone.utc) + timedelta(hours=9)  # 🔧 한국 시간 변환
    hour = kst_now.hour
    print(f"🕒 [DEBUG] 현재 한국 시간: {kst_now.strftime('%Y-%m-%d %H:%M:%S')} / 작동여부: {not (4 <= hour < 12)}")
    return not (4 <= hour < 12)

# ✅ 폴링 루프
async def polling_loop():
    global last_known_ids, last_known_data
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    if channel is None:
        print("❌ 채널을 찾을 수 없습니다.")
        return

    print(f"✅ 채널 연결됨: {channel.name}")

    while not client.is_closed():
        if not is_active_time():
            print("⏰ 현재는 작동 시간이 아니므로 대기 중...")
            await asyncio.sleep(120)
            continue

        try:
            response = supabase.table("Weapon_Rentals")\
                .select("*")\
                .order("id", desc=True)\
                .limit(20)\
                .execute()

            current_ids = set()
            current_data = {}

            for row in response.data:
                row_id = row["id"]
                current_ids.add(row_id)
                current_data[row_id] = row

            if not last_known_ids:
                last_known_ids = current_ids
                last_known_data = current_data
                print("🚫 첫 실행이므로 알림 없이 상태만 초기화됨")
                await asyncio.sleep(120)
                continue

            # 1️⃣ 신규 등록 감지
            new_ids = current_ids - last_known_ids
            for new_id in new_ids:
                data = current_data[new_id]
                borrower = data.get("borrower", "알 수 없음")
                weapon_name = data.get("weapon_name", "무기 이름 없음")
                msg = f"📥 {borrower}님이 {weapon_name} 을 대여 요청하였습니다."
                await channel.send(msg)
                print(f"[등록] {msg}")

            # 2️⃣ 반납(삭제) 감지
            removed_ids = last_known_ids - current_ids
            for removed_id in removed_ids:
                removed_data = last_known_data.get(removed_id, {})
                borrower = removed_data.get("borrower", "알 수 없음")
                weapon_name = removed_data.get("weapon_name", "무기 이름 없음")
                now = (datetime.now(timezone.utc) + timedelta(hours=9)).strftime("%y-%m-%d %H:%M")  # 🔧 KST 반영
                msg = f"🗑 {borrower}님이 대여한 {weapon_name} 이/가 {now} 부로 반납완료 되었습니다."
                await channel.send(msg)
                print(f"[반납] {msg}")

            # 🔄 상태 업데이트
            last_known_ids = current_ids
            last_known_data = current_data

        except Exception as e:
            print(f"❌ 폴링 중 오류 발생: {e}")

        await asyncio.sleep(120)

@client.event
async def on_ready():
    print(f"🤖 디스코드 봇 로그인됨: {client.user}")
    client.loop.create_task(polling_loop())

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
