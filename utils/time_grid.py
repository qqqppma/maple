from datetime import datetime, timedelta

def generate_slot_table():
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    days = [base_date + timedelta(days=i) for i in range(7)]
    time_ranges = [
        "00:00~02:00", "02:00~04:00", "04:00~06:00", "06:00~08:00",
        "08:00~10:00", "10:00~12:00", "12:00~14:00", "14:00~16:00",
        "16:00~18:00", "18:00~20:00", "20:00~22:00", "22:00~00:00"
    ]

    slot_table = {}
    for idx, time_label in enumerate(time_ranges):
        row = []
        for day in days:
            hour = (idx * 2) % 24
            slot_time = day.replace(hour=hour).strftime("%Y-%m-%d %H:%M")
            row.append((slot_time, f"slot_{slot_time}"))
        slot_table[time_label] = row

    return slot_table, days