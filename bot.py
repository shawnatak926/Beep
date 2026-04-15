import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import requests
import json
from datetime import datetime

TOKEN = "MTQ4ODQ1MDc4MzQ1OTY3NjIxMA.G65BLL.PqFcICDXtsh9j51GJQd3XlVxn3Z9Iw0Wl-vJJU"
CHANNEL_ID = 1488451289976275037

# ================== 당직표 ==================
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


# ================== 시간표 ==================
def get_timetable_data():
    return {
        "월": ["자율", "한국", "소공", "실영", "웹프", "웹프", "대수"],
        "화": ["체육2", "시스", "자바", "자바", "디자", "디자", "국어"],
        "수": ["자바", "자바", "한국", "체육2", "국어", "대수", "동아"],
        "목": ["시스", "시스", "소공", "소공", "실영", "웹프", "웹프"],
        "금": ["웹프", "한국", "진로", "자바", "대수", "", ""]
    }


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


# ================== 다음 수업 ==================
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


# ================== 수업 종료 알림 ==================
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


# ================== 디스코드 ==================
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
    if message.content == "!시간표" or message.content == "!우성민r":
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


client.run(TOKEN)