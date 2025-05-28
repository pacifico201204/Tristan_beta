import discord
import json
import os
import requests
import random
from datetime import datetime
from pytz import timezone

from keep_alive import keep_alive
keep_alive()

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
TRIGGERS_FILE = 'triggers.json'
POINTS_FILE = 'points.json'
ATTENDANCE_FILE = 'attendance.json'
VN_TZ = timezone("Asia/Ho_Chi_Minh")
default_triggers = {
    'chào mày bot': 'Chào {user}!',
    'hello bot': 'Hello {user}!',
    'bot đâu rồi': 'Tôi đây {user}!',
    'hi bot': 'Hi {user}!',
    'bot ngu': 'Không dám đâu {user}, tôi đang học hỏi thêm!',
    'bitcoin': '__fetch_btc__'
}

# Load hoặc tạo triggers
if os.path.exists(TRIGGERS_FILE):
    with open(TRIGGERS_FILE, 'r', encoding='utf-8') as f:
        triggers = json.load(f)
else:
    triggers = default_triggers.copy()
    with open(TRIGGERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(triggers, f, ensure_ascii=False, indent=2)

def save_triggers():
    with open(TRIGGERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(triggers, f, ensure_ascii=False, indent=2)

# Load hoặc tạo điểm
if os.path.exists(POINTS_FILE):
    with open(POINTS_FILE, 'r', encoding='utf-8') as f:
        points = json.load(f)
else:
    points = {}
    with open(POINTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(points, f, ensure_ascii=False, indent=2)

def save_points():
    with open(POINTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(points, f, ensure_ascii=False, indent=2)

# Load hoặc tạo bảng điểm danh
if os.path.exists(ATTENDANCE_FILE):
    with open(ATTENDANCE_FILE, 'r', encoding='utf-8') as f:
        attendance = json.load(f)
else:
    attendance = []
    with open(ATTENDANCE_FILE, 'w', encoding='utf-8') as f:
        json.dump(attendance, f, ensure_ascii=False, indent=2)

def save_attendance():
    with open(ATTENDANCE_FILE, 'w', encoding='utf-8') as f:
        json.dump(attendance, f, ensure_ascii=False, indent=2)

# Setup Discord client
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)
wa_spam_counter = {}

@client.event
async def on_ready():
    print(f'🤖 Bot đã hoạt động: {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    msg = message.content.lower()
    user_id = str(message.author.id)
    username = f"con vợ {message.author.name}"

    if user_id not in points:
        points[user_id] = {'username': username, 'xuan': 0, 'cucnung': 0, 'qualo': 0}
    else:
        points[user_id]['username'] = username

    # Điểm danh
    if msg.startswith('!xuất'):
        now = datetime.now(VN_TZ).strftime("%H:%M:%S - %d/%m/%Y")
        entry = {
            'user_id': user_id,
            'username': username,
            'time': now
        }
        attendance.append(entry)
        points[user_id]['qualo'] = points[user_id].get('qualo', 0) + 1
        save_points()
        save_attendance()
        await message.channel.send(f'🧴 {username} đã xuất lúc {now} và nhận được 1 **quả lọ**! (Tổng: {points[user_id]["qualo"]} quả lọ)')
        return

    if msg.startswith('!check xuất'):
        if not attendance:
            await message.channel.send("📂 Chưa có ai xuất.")
        else:
            last_entries = attendance[-5:]
            result = "\n".join([f'• {e["username"]} → {e["time"]}' for e in last_entries])
            await message.channel.send(f'📋 Danh sách xuất gần nhất:\n{result}')
        return

    if msg.startswith('!check lọ'):
        sorted_users = sorted(points.items(), key=lambda x: x[1].get('qualo', 0), reverse=True)
        lines = [f'🏅 {user_data["username"]} → {user_data.get("qualo", 0)} lọ' for _, user_data in sorted_users if user_data.get("qualo", 0) > 0]
        if lines:
            await message.channel.send("📊 Bảng xếp hạng lọ:\n" + "\n".join(lines))
        else:
            await message.channel.send("📂 Chưa ai có quả lọ nào cả.")
        return

    if msg == '$wa':
        wa_spam_counter[user_id] = wa_spam_counter.get(user_id, 0) + 1
        if wa_spam_counter[user_id] >= 3:
            await message.channel.send("con vợ claim được gì ngon chưa vậy")
            wa_spam_counter[user_id] = 0
    else:
        wa_spam_counter[user_id] = 0

    if msg.startswith('!roll'):
        roll = random.randint(1, 6)
        result = f'🎲 {username} đổ được số **{roll}**.'

        if roll % 2 == 0:
            points[user_id]['cucnung'] += 1
            result += f' ➕ Nhận 1 điểm **cực nứng**! (Tổng: {points[user_id]["cucnung"]})'
        else:
            points[user_id]['xuan'] += 1
            result += f' ➕ Nhận 1 điểm **tích xuân**! (Tổng: {points[user_id]["xuan"]})'

        save_points()
        await message.channel.send(result)
        return

    if msg.startswith('!check xuân'):
        await message.channel.send(f'🧾 {username} hiện có {points[user_id].get("xuan", 0)} điểm tích xuân.')
        return

    if msg.startswith('!check cực nứng') or msg.startswith('!check nứng'):
        await message.channel.send(f'🔥 {username} hiện có {points[user_id].get("cucnung", 0)} điểm cực nứng.')
        return

    if msg.startswith('!add '):
        try:
            _, rest = message.content.split(' ', 1)
            trigger, response = [s.strip() for s in rest.split('|', 1)]
            triggers[trigger.lower()] = response
            save_triggers()
            await message.channel.send(f'✅ Đã thêm trigger: **{trigger}** → **{response}**')
        except ValueError:
            await message.channel.send('❌ Sai cú pháp. Dùng: `!add trigger | response`')
        return

    if msg.startswith('!remove '):
        trigger = msg[len('!remove '):].strip().lower()
        if trigger in triggers:
            del triggers[trigger]
            save_triggers()
            await message.channel.send(f'🗑️ Đã xoá trigger: **{trigger}**')
        else:
            await message.channel.send('⚠️ Trigger không tồn tại.')
        return

    if msg == '!list':
        if triggers:
            lines = '\n'.join(f'• **{k}** → **{v}**' for k, v in triggers.items())
            await message.channel.send(lines)
        else:
            await message.channel.send('📂 Chưa có trigger nào.')
        return

    for trigger, response in triggers.items():
        if trigger in msg:
            if response == '__fetch_btc__':
                try:
                    url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd'
                    res = requests.get(url)
                    price = res.json()['bitcoin']['usd']
                    await message.channel.send(f'💰 Giá Bitcoin hiện tại: ${price} USD')
                except Exception as e:
                    await message.channel.send(f'⚠️ Không lấy được giá BTC: {e}')
            else:
                await message.channel.send(response.replace('{user}', message.author.mention))
            break

client.run(TOKEN)
