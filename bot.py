import os
import asyncio
import discord
from datetime import datetime
from supabase import create_client, Client

# ✅ 환경변수 불러오기 (Railway에선 .env 없어도 작동)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# ✅ 채널 ID 로딩 및 예외 처리
try:
    channel_id_str = os.getenv("CHANNEL_ID")
    if not channel_id_str:
        raise ValueError("환경변수 CHANNEL_ID가 설정되지 않았습니다.")
    CHANNEL_ID = int(channel_id_str)
except ValueError as e:
    print(f"❌ CHANNEL_ID 로딩 실패: {e}")
    exit(1)

# ✅ 디버깅 출력
print("✅ DEBUG - DISCORD_TOKEN 존재 여부:", DISCORD_TOKEN is not None)
print("✅ DEBUG - CHANNEL_ID:", CHANNEL_ID)
print("✅ DEBUG - SUPABASE_URL:", SUPABASE_URL)
print("✅ DEBUG - SUPABASE_KEY 존재 여부:", SUPABASE_KEY is not None)

# ✅ Supabase 클라이언트 생성
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ Discord 봇 설정
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ✅ 작동 시간 체크 함수 (04:00 ~ 12:00은 꺼짐)
def is_active_time():
    hour = datetime.now().hour
    return hour < 4 or hour >= 12  # 새벽 4시 ~ 정오 전까지는 비활성

@client.event
async def on_ready():
    if not is_active_time():
        print("⏰ 현재는 작동 시간이 아니므로 봇을 종료합니다.")
        await client.close()
        return

    print(f"✅ 디스코드 봇 로그인됨: {client.user}")
    print(f"🔍 채널 ID: {CHANNEL_ID}")

    # ✅ 현재 봇이 속한 서버들과 텍스트 채널 목록 출력
    print("📋 봇이 인식한 채널 목록:")
    for guild in client.guilds:
        print(f"🔸 서버: {guild.name}")
        for channel in guild.text_channels:
            print(f"  - 채널 이름: {channel.name}, 채널 ID: {channel.id}")

    try:
        channel = await client.fetch_channel(CHANNEL_ID)
        print(f"📢 채널 로딩 성공: {channel.name}")
        await channel.send("✅ 봇이 채널에 정상 연결되었습니다!")
    except Exception as e:
        print(f"❌ 채널 불러오기 실패: {e}")
        return

    # ✅ Supabase 실시간 이벤트 핸들러
    def handle_insert(payload):
        if not is_active_time():
            return
        data = payload["new"]
        msg = f"📥 `{data['borrower']}`님이 `{data['weapon_name']}` 을 대여 요청하였습니다."
        asyncio.run_coroutine_threadsafe(channel.send(msg), client.loop)

    def handle_delete(payload):
        if not is_active_time():
            return
        data = payload["old"]
        now = datetime.now().strftime("%y-%m-%d %H:%M")
        msg = f"🗑 `{data['borrower']}`님이 대여한 `{data['weapon_name']}` 이/가 {now} 부로 반납완료 되었습니다."
        asyncio.run_coroutine_threadsafe(channel.send(msg), client.loop)

    try:
        supabase.table("Weapon_Rentals")\
            .on("INSERT", handle_insert)\
            .on("DELETE", handle_delete)\
            .subscribe()
        print("✅ Supabase 구독 시작됨")
    except Exception as e:
        print(f"❌ Supabase 실시간 구독 실패: {e}")

# ✅ 디스코드 봇 실행
if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
