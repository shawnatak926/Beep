import base64
import json
import os
import time
from datetime import datetime
from urllib.parse import quote

import discord
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

if not TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN 환경변수가 필요합니다.")

if CHANNEL_ID == 0:
    raise ValueError("DISCORD_CHANNEL_ID 환경변수가 필요합니다.")

COMCI_BASE_URL = "http://comci.net:4082"
COMCI_SCHOOL_NAME = "대구소프트웨어고등학교"
COMCI_TARGET_GRADE = 2
COMCI_TARGET_CLASS = 3
COMCI_CACHE_TTL_SECONDS = 300

_comci_cache = {
    "expires_at": 0.0,
    "school_code": None,
    "data": None,
}

def get_sheet_data():
    url = "https://docs.google.com/spreadsheets/d/1NBGqXzb-VrFiZUu0y4t7qIWeg69HQjDFgHN8RMOQr8s/gviz/tq?tqx=out:json&gid=1166955981"

    response = requests.get(url).text
    json_str = response[response.index("{"):response.rindex("}") + 1]
    data = json.loads(json_str)

    rows = data["table"]["rows"]
    result = {}

    for row in rows:
        names = []
        for cell in row["c"]:
            if cell and cell.get("v") is not None:
                value = str(cell["v"])
                if value and not value.replace(".", "").isdigit() and value not in "월화수목금토일":
                    names.append(value)

        for i, name in enumerate(names):
            result[f"{i + 1}학년"] = name

    return result


async def send_sheet(channel):
    data = get_sheet_data()
    message = "\n".join([f"{grade}: {name}" for grade, name in data.items()])
    await channel.send(message)


def get_fallback_timetable_data():
    return {
        "월": ["자율", "확통", "디자", "디자", "국어", "체육2", "한국"],
        "화": ["확통", "네트", "네트", "한국", "자바2", "자바2", "직영"],
        "수": ["확통", "웹프", "웹프", "웹프", "직영", "국어", "동아"],
        "목": ["체육2", "진로", "자바2", "자바2", "인모", "인모", "인모"],
        "금": ["웹프", "웹프", "네트", "네트", "한국", "", ""]
    }


def _clean_comci_response(response):
    return response.content.decode("utf-8", "ignore").split("\x00")[0]


def _extract_cell_value(cell):
    if cell is None:
        return 0

    if isinstance(cell, str):
        cell = cell.lstrip(">")
        if not cell:
            return 0

    try:
        return int(cell)
    except (TypeError, ValueError):
        return 0


def _decode_subject_name(cell, subjects):
    value = _extract_cell_value(cell)
    if value <= 0:
        return ""

    subject_index = value // 1000
    if 0 <= subject_index < len(subjects):
        return subjects[subject_index]
    return ""


def _find_school_code():
    if _comci_cache["school_code"] is not None:
        return _comci_cache["school_code"]

    encoded_name = quote(COMCI_SCHOOL_NAME.encode("euc-kr"))
    response = requests.get(
        f"{COMCI_BASE_URL}/36179?17384l{encoded_name}",
        timeout=10,
    )
    response.raise_for_status()
    payload = json.loads(_clean_comci_response(response))

    for school in payload.get("학교검색", []):
        if len(school) >= 4 and school[2] == COMCI_SCHOOL_NAME:
            _comci_cache["school_code"] = school[3]
            return school[3]

    raise ValueError(f"{COMCI_SCHOOL_NAME} 학교 코드를 찾을 수 없습니다.")


def _fetch_comci_data():
    now = time.time()
    if _comci_cache["data"] and _comci_cache["expires_at"] > now:
        return _comci_cache["data"]

    school_code = _find_school_code()
    payload = f"73629_{school_code}_0_1"
    encoded_payload = base64.b64encode(payload.encode()).decode()
    response = requests.get(f"{COMCI_BASE_URL}/36179?{encoded_payload}", timeout=10)
    response.raise_for_status()
    data = json.loads(_clean_comci_response(response))

    _comci_cache["data"] = data
    _comci_cache["expires_at"] = now + COMCI_CACHE_TTL_SECONDS
    return data


def get_timetable_data():
    fallback = get_fallback_timetable_data()

    try:
        data = _fetch_comci_data()
        subjects = data["자료492"]
        raw_timetable = data["자료481"][COMCI_TARGET_GRADE][COMCI_TARGET_CLASS]
        days = ["월", "화", "수", "목", "금"]

        timetable = {}
        for day_index, day_name in enumerate(days, start=1):
            day_rows = raw_timetable[day_index]
            period_count = day_rows[0]
            periods = []
            for period_index in range(1, period_count + 1):
                periods.append(_decode_subject_name(day_rows[period_index], subjects))
            while len(periods) < 7:
                periods.append("")
            timetable[day_name] = periods[:7]

        return timetable
    except Exception as exc:
        print(f"컴시간 조회 실패, 기본 시간표 사용: {exc}")
        return fallback


def format_timetable_table():
    timetable = get_timetable_data()

    days = ["월", "화", "수", "목", "금"]
    periods = ["1교시", "2교시", "3교시", "4교시", "5교시", "6교시", "7교시"]

    header = "교시  " + "  ".join([f"{d:^6}" for d in days])
    lines = [header]

    for i, period in enumerate(periods):
        row = f"{period:<4} "
        for day in days:
            subject = timetable[day][i] if i < len(timetable[day]) else ""
            row += f"{subject:^6} "
        lines.append(row)

    return "```" + "\n".join(lines) + "```"


def get_next_class():
    timetable = get_timetable_data()
    days = ["월", "화", "수", "목", "금"]

    today = datetime.now().weekday()
    if today >= 5:
        return "🏫 주말에는 수업 없음"

    schedule = [
        ("1교시", "08:50", "09:40"),
        ("2교시", "09:50", "10:40"),
        ("3교시", "10:50", "11:40"),
        ("4교시", "11:50", "12:40"),
        ("5교시", "13:30", "14:20"),
        ("6교시", "14:30", "15:20"),
        ("7교시", "15:30", "16:20"),
    ]

    now = datetime.now().time()

    for i, (_, start, _) in enumerate(schedule):
        start_t = datetime.strptime(start, "%H:%M").time()

        if now < start_t:
            subject = timetable[days[today]][i]
            if subject == "":
                return f"📭 다음은 {i+1}교시 → 공강"
            return f"📚 다음은 {i+1}교시 → {subject}"

    return "🏫 오늘 수업 끝!"


def get_current_and_next_class():
    """Returns current class and next class info"""
    timetable = get_timetable_data()
    days = ["월", "화", "수", "목", "금"]

    today = datetime.now().weekday()
    if today >= 5:
        return None

    schedule = [
        ("1 교시", "08:50", "09:40"),
        ("2 교시", "09:50", "10:40"),
        ("3 교시", "10:50", "11:40"),
        ("4 교시", "11:50", "12:40"),
        ("5 교시", "13:30", "14:20"),
        ("6 교시", "14:30", "15:20"),
        ("7 교시", "15:30", "16:20"),
    ]

    now = datetime.now().time()

    for i, (_, start, end) in enumerate(schedule):
        start_t = datetime.strptime(start, "%H:%M").time()
        end_t = datetime.strptime(end, "%H:%M").time()

        if start_t <= now < end_t:
            current_subject = timetable[days[today]][i]
            next_subject = None
            next_period = i + 2

            if i + 1 < len(timetable[days[today]]):
                next_subject = timetable[days[today]][i + 1]

            return {
                "current_period": i + 1,
                "current_subject": current_subject,
                "next_period": next_period,
                "next_subject": next_subject,
                "is_last": next_subject is None or next_subject == ""
            }

    return None


async def send_class_end_notification(channel):
    """Send notification when class ends or before first period"""
    now = datetime.now().time()
    first_period_start = datetime.strptime("08:50", "%H:%M").time()

    # 8:40 AM - announce first period
    if now.hour == 8 and now.minute < 45:
        timetable = get_timetable_data()
        days = ["월", "화", "수", "목", "금"]
        today = datetime.now().weekday()

        if today < 5:
            first_subject = timetable[days[today]][0]
            message = f"📚 1 교시 시작! → {first_subject}"
            await channel.send(message)
        return

    info = get_current_and_next_class()

    if info is None:
        return

    if info["is_last"]:
        message = f"🔔 {info['current_period']}교시 ({info['current_subject']}) 종료!\n🏫 오늘 수업 끝!"
    else:
        message = f"🔔 {info['current_period']}교시 ({info['current_subject']}) 종료!\n📚 다음 {info['next_period']}교시: {info['next_subject']}"

    await channel.send(message)


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
scheduler = AsyncIOScheduler(timezone="Asia/Seoul")


@client.event
async def on_ready():
    channel = client.get_channel(CHANNEL_ID)
    scheduler.add_job(send_sheet, "cron", hour=16, minute=30, args=[channel])

    # Schedule class end notifications for each period
    class_end_times = [
        (8, 40),   # Before 1 교시
        (9, 40),   # 1 교시 ends
        (10, 40),  # 2 교시 ends
        (11, 40),  # 3 교시 ends
        (12, 40),  # 4 교시 ends
        (14, 20),  # 5 교시 ends
        (15, 20),  # 6 교시 ends
        (16, 20),  # 7 교시 ends
    ]

    for hour, minute in class_end_times:
        scheduler.add_job(send_class_end_notification, "cron", hour=hour, minute=minute, args=[channel])

    scheduler.start()
    print(f"봇 실행 중: {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # 📋 당직표
    if message.content == "!당직":
        await send_sheet(message.channel)

    # 📚 시간표 (표)
    if message.content == "!시간표" or message.content == "!우성민":
        await message.channel.send("📚 2-3 시간표\n" + format_timetable_table())
        await message.channel.send(get_next_class())


    # ⏭️ 다음 수업
    if message.content == "!다음수업":
        await message.channel.send(get_next_class())

    if message.content == "!다음시간":
        await message.channel.send(get_next_class())

    # 🧹 전체 삭제
    if message.content.startswith("!clear"):
        if not message.author.guild_permissions.manage_messages:
            await message.channel.send("❌ 권한 없음")
            return

        try:
            amount = int(message.content.split()[1])
            await message.channel.purge(limit=amount + 1)
        except:
            await message.channel.send("사용법: !clear 10")

    # 👤 이름으로 삭제
    if message.content.startswith("!clean"):
        if not message.author.guild_permissions.manage_messages:
            await message.channel.send("❌ 권한 없음")
            return

        parts = message.content.split()
        if len(parts) < 3:
            await message.channel.send("사용법: !clean 이름 10")
            return

        name = parts[1]

        try:
            amount = int(parts[2])
        except:
            await message.channel.send("숫자를 입력하세요")
            return

        member = None
        for m in message.guild.members:
            if name in m.display_name or name in m.name:
                member = m
                break

        if member is None:
            await message.channel.send("❌ 유저를 찾을 수 없음")
            return

        def check(msg):
            return msg.author == member

        deleted = await message.channel.purge(limit=amount, check=check)
        await message.channel.send(f"🧹 {member.display_name} {len(deleted)}개 삭제", delete_after=3)


if __name__ == "__main__":
    client.run(TOKEN)
