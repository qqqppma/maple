import os
import asyncio
import discord
from datetime import datetime
from supabase import create_client, Client
from threading import Thread

SUPABASE_URL = os.getenv("https://tkhcojfyvdjahenllbab.supabase.co")
SUPABASE_KEY = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRraGNvamZ5dmRqYWhlbmxsYmFiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ2ODU2MzUsImV4cCI6MjA2MDI2MTYzNX0.HfejJXhxGsRdzr9UUgW57SSpOGG21iQcfxguvxEfDhU")
DISCORD_TOKEN = os.getenv("MTM2MjcwODY5MzY3NzkwNDA0NA.GFQ2uX.-9oWHu1cW3XZe49xFCuTrNa0xpgETmhW2ULpuc")
CHANNEL_ID = int(os.getenv("1362709414729089154"))

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ 디스코드 봇 로그인됨: {client.user}")
    channel = client.get_channel(CHANNEL_ID)

    def handle_insert(payload):
        data = payload["new"]
        msg = f"📥 `{data['borrower']}`님이 `{data['weapon_name']}` 을 대여 요청하였습니다."
        asyncio.run_coroutine_threadsafe(channel.send(msg), client.loop)

    def handle_delete(payload):
        data = payload["old"]
        now = datetime.now().strftime("%y-%m-%d %H:%M")
        msg = f"🗑 `{data['borrower']}`님이 대여한 `{data['weapon_name']}` 이/가 {now} 부로 반납완료 되었습니다."
        asyncio.run_coroutine_threadsafe(channel.send(msg), client.loop)

    supabase.table("Weapon_Rentals").on("INSERT", handle_insert).on("DELETE", handle_delete).subscribe()

# Run bot
Thread(target=client.run, args=(DISCORD_TOKEN,)).start()
