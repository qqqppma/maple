import schedule
import time
from datetime import datetime
from supabase import create_client
import os

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def reset_mainmembers():
    print(f"[{datetime.now()}] ✅ Resetting MainMembers scores")
    supabase.table("MainMembers").update({
        "suro_score": 0,
        "flag_score": 0,
        "mission_point": 0,
        "event_sum": 0
    }).neq("nickname", "").execute()

def reset_submembers():
    print(f"[{datetime.now()}] ✅ Resetting SubMembers scores")
    supabase.table("SubMembers").update({
        "suro_score": 0,
        "flag_score": 0,
        "mission_point": 0
    }).neq("sub_name", "").execute()

def weekly_reset():
    reset_mainmembers()
    reset_submembers()

# ✅ 원하는 요일과 시간 설정 (예: 일요일 23:59)
schedule.every().sunday.at("23:59").do(weekly_reset)

print("🔄 Weekly reset scheduler started.")
while True:
    schedule.run_pending()
    time.sleep(30)
