import os
import time
import discord
import asyncio
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone

# ✅ 환경 변수 불러오기
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
WEAPON_CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # 보조무기
DROPITEM_CHANNEL_ID = int(os.getenv("DROPITEM_CHANNEL_ID"))  # 드메템

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
            weapon_res = supabase.table("Weapon_Rentals")\
                .select("*").order("id", desc=True).limit(20).execute()

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
                    msg = f"📥 `{data['borrower']}`님이 `{data['weapon_name']}` 을 대여 요청하였습니다."
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
            drop_res = supabase.table("DropItem_Rentals")\
                .select("*").order("id", desc=True).limit(20).execute()

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
                    msg = f"🎁 `{data['drop_borrower']}`님이 `{data['dropitem_name']}` 을 대여 요청하였습니다."
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

@client.event
async def on_ready():
    print(f"🤖 디스코드 봇 로그인됨: {client.user}")
    client.loop.create_task(polling_loop())

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)