import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import requests
import json

TOKEN = "MTQ4ODQ1MDc4MzQ1OTY3NjIxMA.G5WL4s.XO3D9bCw15WGyJD82QMzfri_ZDZAkNfRnMHwww"
CHANNEL_ID = 1488451289976275037

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
                if (value
                        and not value.replace(".", "").isdigit()
                        and value not in "월화수목금토일"):
                    names.append(value)

        for i, name in enumerate(names):
            result[f"{i + 1}학년"] = name

    return result

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

async def send_sheet(channel=None):
    if channel is None:
        channel = client.get_channel(CHANNEL_ID)
    data = get_sheet_data()
    message = "\n".join([f"{grade}: {name}" for grade, name in data.items()])
    await channel.send(message)

@client.event
async def on_ready():
    scheduler.add_job(send_sheet, "cron", hour=16, minute=30)
    scheduler.start()
    print(f"봇 실행 중: {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == "!당직":
        await send_sheet(channel=message.channel)

client.run(TOKEN)