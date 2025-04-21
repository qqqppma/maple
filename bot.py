import os
import asyncio
import discord
from datetime import datetime
from supabase import create_client, Client
from threading import Thread
# from dotenv import load_dotenv

# ✅ 환경변수 로딩 (.env 사용 시 필요)
# load_dotenv()

# ✅ 환경변수 불러오기
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

# ✅ Supabase 클라이언트
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ Discord 봇 설정
intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ 디스코드 봇 로그인됨: {client.user}")
    print(f"🔍 채널 ID: {CHANNEL_ID}")

    try:
        channel = await client.fetch_channel(CHANNEL_ID)
        print(f"📢 채널 로딩 성공: {channel.name}")
        await channel.send("✅ 봇이 채널에 정상 연결되었습니다!")
    except Exception as e:
        print(f"❌ 채널 불러오기 실패: {e}")
        return

    # ✅ Supabase 실시간 이벤트 핸들러
    def handle_insert(payload):
        data = payload["new"]
        msg = f"📥 `{data['borrower']}`님이 `{data['weapon_name']}` 을 대여 요청하였습니다."
        asyncio.run_coroutine_threadsafe(channel.send(msg), client.loop)

    def handle_delete(payload):
        data = payload["old"]
        now = datetime.now().strftime("%y-%m-%d %H:%M")
        msg = f"🗑 `{data['borrower']}`님이 대여한 `{data['weapon_name']}` 이/가 {now} 부로 반납완료 되었습니다."
        asyncio.run_coroutine_threadsafe(channel.send(msg), client.loop)

    try:
        supabase.table("Weapon_Rentals").on("INSERT", handle_insert).on("DELETE", handle_delete).subscribe()
        print("✅ Supabase 구독 시작됨")
    except Exception as e:
        print(f"❌ Supabase 실시간 구독 실패: {e}")

# ✅ 디스코드 봇 실행 (Thread 제거!)
if __name__ == "__main__":
    client.run(DISCORD_TOKEN)