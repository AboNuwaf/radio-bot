import os
import json
import logging
import subprocess
import threading
import time
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from pyrogram.errors import RPCError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("radio_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

API_ID = int(os.environ.get("API_ID", 29667286))
API_HASH = os.environ.get("API_HASH", "2dddc2f98e16161cb50e41971f9591be")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8628254857:AAHgx97sZWiPo2CrOMSWDHvt2nyrMmKrJtU")
ADMIN_ID = [6869497898]

DATA_FILE = "user_data.json"

IMAGE_TIMO = "https://i.ibb.co/wFVh6Pws/IMG-20251015-021119-521.jpg"

FFMPEG_TIMEOUT = 30

ST_TIMO = {
    "1": {"name": "إذاعة آيات السكينة", "url": "https://qurango.net/radio/sakeenah"},
    "2": {"name": "إذاعة القرآن من مكة المكرمة", "url": "http://n07.radiojar.com/0tpy1h0kxtzuv?rj-ttl=5&rj-tok=AAABlaaGy1sA0n1Oo_t_c-9DGw"},
    "3": {"name": "إذاعة القرآن من القاهرة", "url": "https://stream.radiojar.com/8s5u5tpdtwzuv"},
    "4": {"name": "إذاعة القرآن من مختلف القراء", "url": "https://backup.qurango.net/radio/mix"},
    "5": {"name": "إذاعة السيرة النبوية", "url": "https://qurango.net/radio/fi_zilal_alsiyra"},
    "6": {"name": "إذاعة الرقية الشرعية 1", "url": "https://qurango.net/radio/roqiah"},
    "7": {"name": "إذاعة الرقية الشرعية 2", "url": "https://backup.qurango.net/radio/roqiah"},
    "8": {"name": "إذاعة الفتوة", "url": "https://qurango.net/radio/fatwa"},
    "9": {"name": "إذاعة الحرم المكي", "url": "http://r7.tarat.com:8004/stream?type=http&nocache=114"},
    "10": {"name": "إذاعة تلاوات خاشعة", "url": "https://qurango.net/radio/salma"},
    "11": {"name": "إذاعة أحمد العجمي", "url": "https://qurango.net/radio/ahmad_alajmy"},
    "12": {"name": "إذاعة إدريس أبكر", "url": "https://qurango.net/radio/idrees_abkr"},
    "13": {"name": "إذاعة عبد الباسط عبد الصمد", "url": "https://qurango.net/radio/abdulbasit_abdulsamad_mojawwad"},
    "14": {"name": "إذاعة عبد الرحمن السديس", "url": "https://qurango.net/radio/abdulrahman_alsudaes"},
    "15": {"name": "إذاعة ماهر المعيقلي", "url": "https://qurango.net/radio/maher_al_meaqli"},
    "16": {"name": "إذاعة محمد اللحيدان", "url": "https://qurango.net/radio/mohammed_allohaidan"},
    "17": {"name": "إذاعة ياسر الدوسري", "url": "https://qurango.net/radio/yasser_aldosari"},
    "18": {"name": "إذاعة مشاري العفاسي", "url": "https://qurango.net/radio/mishary_alafasi"},
    "19": {"name": "إذاعة فارس عباد", "url": "https://qurango.net/radio/fares_abbad"},
    "20": {"name": "إذاعة احمد عامر", "url": "https://qurango.net/radio/ahmed_amer"},
    "21": {"name": "اذاعة العيون الكوشي", "url": "https://qurango.net/radio/aloyoon_alkoshi"},
    "22": {"name": " قناة قران الكريم ", "url": "https://win.holol.com/live/quran/playlist.m3u"},
    "23": {"name": "قناة السنه النبويه  ", "url": "https://win.holol.com/live/sunnah/playlist.m3u8"}
}

app = Client("radio_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

data_lock = threading.Lock()
user_data = {}
user_state = {}

def is_admin(user_id):
    return user_id in ADMIN_ID

def load_data():
    global user_data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            user_data = json.load(f)

def save_data():
    with data_lock:
        with open(DATA_FILE, "w") as f:
            json.dump(user_data, f, ensure_ascii=False, indent=4)

load_data()

def is_ffmpeg_running(pid):
    try:
        output = subprocess.check_output(
            ["ps", "-p", str(pid), "-o", "cmd="],
            timeout=3
        ).decode().strip()
        return "ffmpeg" in output
    except:
        return False

def restart_user_broadcasts(user_id):
    try:
        user_info = user_data.get(user_id, {})
        selected_station = user_info.get('temp_station')        
        if not selected_station:
            return            
        for channel_id, channel_info in user_info.get("channels", {}).items():
            if "process" in channel_info:
                try:
                    pid = channel_info["process"]
                    if is_ffmpeg_running(pid):
                        subprocess.run(["kill", "-9", str(pid)], timeout=5, check=True)
                except Exception as e:
                    logger.error(f"Error stopping process: {e}")                   
            try:
                ffmpeg_cmd = [
                    "ffmpeg", "-re", "-i", selected_station,
                    "-c:v", "libx264", "-preset", "veryfast", "-b:v", "2500k",
                    "-c:a", "aac", "-b:a", "128k",
                    "-f", "flv", channel_info["rtmps_url"]
                ]
                process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                user_data[user_id]["channels"][channel_id]["process"] = process.pid
                logger.info(f"Restarted broadcast for channel {channel_id}")                
            except Exception as e:
                logger.error(f"Error starting broadcast: {e}")                
        save_data()
    except Exception as e:
        logger.error(f"Error in restart_user_broadcasts: {e}")


def restart_all_broadcasts():
    try:
        current_data = user_data.copy()
        for user_id, user_info in current_data.items():
            channels = user_info.get("channels", {})
            selected_station = user_info.get('temp_station')            
            if not selected_station:
                continue                
            for channel_id, info in channels.items():
                try:
                    if "process" in info:
                        if is_ffmpeg_running(info["process"]):
                            subprocess.run(["kill", "-9", str(info["process"])], timeout=5, check=True)
                            
                    ffmpeg_cmd = [
                        "ffmpeg", "-re", "-i", selected_station,
                        "-c:v", "libx264", "-preset", "veryfast", "-b:v", "2500k",
                        "-c:a", "aac", "-b:a", "128k",
                        "-f", "flv", info["rtmps_url"]
                    ]
                    process = subprocess.Popen(
                        ffmpeg_cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    user_data[user_id]["channels"][channel_id]["process"] = process.pid
                    logger.info(f"Updated broadcast for {channel_id}")                    
                except Exception as e:
                    logger.error(f"General error: {str(e)}")                    
        save_data()
    except Exception as e:
        logger.error(f"Auto-update error: {str(e)}")

def scheduled_restart():
    while True:
        logger.info("Performing scheduled restart...")
        restart_all_broadcasts()
        time.sleep(300)

async def send_broadcast_notification(client, chat_id, station_url):
    try:
        station_id = next(k for k, v in ST_TIMO.items() if v["url"] == station_url)
        station_name = ST_TIMO[station_id]["name"]
        await client.send_photo(
            chat_id=chat_id,
            photo=IMAGE_TIMO,
            caption=f"<blockquote> • بدأ بث القرآن الكريم من {station_name}</blockquote>"
        )
    except Exception as e:
        logger.error(f"Notification failed: {str(e)}")

async def notify_new_user(user_id, username, first_name):
    text = (
        f"<blockquote> • مستخدم جديد!\n</blockquote>"
        f"<blockquote> • المعرف: {user_id}\n</blockquote>"
        f"<blockquote> • الاسم: {first_name}\n</blockquote>"
        f"<blockquote> • اليوزر: @{username}</blockquote>"
    )
    await app.send_message(ADMIN_ID[0], text)
    
async def delete_channel(client, message, channel_id):
    user_id = str(message.from_user.id)
    try:
        if channel_id in user_data[user_id]["channels"]:

            if "process" in user_data[user_id]["channels"][channel_id]:
                pid = user_data[user_id]["channels"][channel_id]["process"]
                if is_ffmpeg_running(pid):
                    subprocess.run(["kill", "-9", str(pid)], timeout=5, check=True)

            del user_data[user_id]["channels"][channel_id]
            save_data()
            await message.reply_text(f"<blockquote> • تم حذف القناة بنجاح</blockquote>")
        else:
            await message.reply_text("<blockquote> • القناة غير موجودة في قائمتك</blockquote>")
    except Exception as e:
        logger.error(f"Error deleting channel: {e}")
        await message.reply_text("<blockquote> • حدث خطأ أثناء محاولة الحذف</blockquote>")
    
@app.on_message(filters.command(["الاحصائيات"], "") & filters.private)
async def stats_command(client, message):
    if not is_admin(message.from_user.id):
        return
    total_users = len(user_data)
    total_channels = sum(len(user["channels"]) for user in user_data.values() if "channels" in user)
    
    text = (
        f"<blockquote> • إحصائيات البوت:\n</blockquote>"
        f"<blockquote> • إجمالي المستخدمين: {total_users}\n</blockquote>"
        f"<blockquote> • إجمالي القنوات: {total_channels}</blockquote>"
    )
    await message.reply(text)

@app.on_message(filters.command(["اذاعة للمستخدمين"], "") & filters.private)
async def broadcast_users(client, message):
    if not is_admin(message.from_user.id):
        return
    if len(message.command) < 2:
        await message.reply("<blockquote> • يرجى كتابة الرسالة بعد الأمر مثال:</blockquote>\n<blockquote> • اذاعة للمستخدمين + النص</blockquote>")
        return
    text = " ".join(message.command[1:])
    users = user_data.keys()
    success = 0
    failed = 0
    await message.reply(f"<blockquote> • بدء إذاعة للمستخدمين ({len(users)} مستخدم)...</blockquote>")
    for user_id in users:
        try:
            await app.send_message(int(user_id), text)
            success += 1
        except Exception as e:
            logger.error(f"فشل الإرسال لـ {user_id}: {e}")
            failed += 1
        time.sleep(0.5)
    await message.reply(
        f"<blockquote> • تمت الإذاعة بنجاح:\n</blockquote>"
        f"<blockquote> • نجح: {success}\n</blockquote>"
        f"<blockquote> • فشل: {failed}</blockquote>"
    )

@app.on_message(filters.command(["اذاعة للقنوات"], "") & filters.private)
async def broadcast_channels(client, message):
    if not is_admin(message.from_user.id):
        return
    if len(message.command) < 2:
        await message.reply("<blockquote> • يرجى كتابة الرسالة بعد الأمر مثال:</blockquote>\n<blockquote> • اذاعة للقنوات + نص </blockquote>")
        return
    text = " ".join(message.command[1:])
    channels = set()    
    for user in user_data.values():
        if "channels" in user:
            channels.update(user["channels"].keys())
    success = 0
    failed = 0
    await message.reply(f"<blockquote> • بدء إذاعة للقنوات ({len(channels)} قناة)...</blockquote>")
    for channel_id in channels:
        try:
            await app.send_message(int(channel_id), text)
            success += 1
        except Exception as e:
            logger.error(f"فشل الإرسال لـ {channel_id}: {e}")
            failed += 1
        time.sleep(0.5)
    await message.reply(
        f"<blockquote> • تمت الإذاعة بنجاح:\n</blockquote>"
        f"<blockquote> • نجح: {success}\n</blockquote>"
        f"<blockquote> • فشل: {failed}</blockquote>"
    )

@app.on_message(filters.command(["القنوات"], "") & filters.private)
async def list_channels_command(client, message):
    if not is_admin(message.from_user.id):
        await message.reply("<blockquote> • ليس لديك صلاحية الوصول لهذا الأمر!</blockquote>")
        return

    channels_data = []
    seen_channels = set()
    station_reverse = {v['url']: v['name'] for k, v in ST_TIMO.items()}

    try:
        for user_id, user_info in user_data.items():
            if "channels" in user_info:
                current_station = user_info.get('temp_station', 'غير معروف')
                station_name = station_reverse.get(current_station, 'غير معروف')

                for channel_id, channel_info in user_info["channels"].items():
                    if channel_id not in seen_channels:
                        seen_channels.add(channel_id)
                        username = "غير معروف"
                        broadcast_status = "🔴 متوقف"
                        try:
                            chat = await client.get_chat(int(channel_id))
                            username = f"@{chat.username}" if chat.username else "خاصة/بدون يوزر"
                            invite_link = chat.invite_link if chat.invite_link else "يتطلب صلاحية إنشاء رابط"
                            members = await client.get_chat_members_count(chat.id) if chat.permissions.can_invite_users else "غير متاح"
                            broadcast_status = "🟢 قيد التشغيل" if 'process' in channel_info else "🔴 متوقف"
                            
                            channel_entry = (
                                f"<blockquote> • اسم القناة: {chat.title}\n"
                                f"• اليوزر: {username}\n"
                                f"👥 عدد الأعضاء: {members}\n"
                                f"• المحطة النشطة: {station_name}\n"
                                f"• حالة البث: {broadcast_status}\n</blockquote>"
                                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                            )
                            
                        except Exception as e:
                            logger.error(f"Error getting chat info {channel_id}: {e}")
                            channel_entry = (
                                f"<blockquote> • اسم القناة: {channel_info.get('title', 'غير معروف')}\n"
                                f"• اليوزر: {username}\n"
                                f"• المحطة النشطة: {station_name}\n"
                                f"• حالة البث: {broadcast_status}\n</blockquote>"
                                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                            )
                        
                        channels_data.append(channel_entry)

        if not channels_data:
            await message.reply("<blockquote> • لم تتم إضافة أي قنوات بعد!</blockquote>")
            return

        header = "<blockquote> • تقرير القنوات المفصل:\n</blockquote>"
        full_message = header + "\n".join(channels_data)

        parts = []
        current_part = header
        for entry in channels_data:
            if len(current_part) + len(entry) < 4000:
                current_part += entry
            else:
                parts.append(current_part)
                current_part = header + entry
        parts.append(current_part)

        for part in parts:
            await message.reply(part)
            await asyncio.sleep(1.5)

    except Exception as e:
        logger.error(f"Error in channel list command: {e}")
        await message.reply("<blockquote> • حدث خطأ أثناء توليد التقرير!</blockquote>")
        
@app.on_message(filters.command(["المستخدمين"], "") & filters.private)
async def list_users_command(client, message):
    if not is_admin(message.from_user.id):
        await message.reply("<blockquote> • ليس لديك صلاحية الوصول لهذا الأمر!</blockquote>")
        return

    if not user_data:
        await message.reply("<blockquote> • لا يوجد مستخدمين مسجلين بعد!</blockquote>")
        return

    users_list = []
    for user_id, user_info in user_data.items():
        try:
            user = await client.get_users(int(user_id))
            username = f"@{user.username}" if user.username else "بدون يوزر"
            users_list.append(f"<blockquote> • {username} - {user.first_name} (ID: {user_id})</blockquote>")
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            continue

    if not users_list:
        await message.reply("<blockquote> • لا يوجد مستخدمين مسجلين بعد!</blockquote>")
        return

    header = "<blockquote> • قائمة المستخدمين:\n</blockquote>"
    message_text = header + "\n".join(users_list)

    if len(message_text) > 4096:
        parts = [message_text[i:i+4096] for i in range(0, len(message_text), 4096)]
        for part in parts:
            await message.reply(part)
            await asyncio.sleep(1)
    else:
        await message.reply(message_text)
        

def user_keyboard():
    return ReplyKeyboardMarkup([
        ["إضافة قناة", "قنواتي"],
        ["بدء البث", "إيقاف البث"],
        ["تحديث البثوث", "حذف قناة"],
        ["الخروج"]
    ], resize_keyboard=True)


def admin_keyboard():
    return ReplyKeyboardMarkup([
        ["إضافة قناة", "قنواتي"],
        ["بدء البث", "إيقاف البث"],
        ["تحديث البثوث", "حذف قناة"],
        ["الاحصائيات"],
        ["اذاعة للمستخدمين", "اذاعة للقنوات"],
        ["القنوات", "المستخدمين"],
        ["الخروج"]
    ], resize_keyboard=True)


@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    try:
        user_id = str(message.from_user.id)
        is_new_user = False
        
        if user_id not in user_data:
            user_data[user_id] = {
                "channels": {},
                "temp_station": None,
                "join_date": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            save_data()
            is_new_user = True

        if is_admin(message.from_user.id):
            keyboard = admin_keyboard()
        else:
            keyboard = user_keyboard()

        await message.reply_photo(
            photo=IMAGE_TIMO,
            caption=f"<blockquote>• مرحبا بك {message.from_user.first_name} \n• في بوت راديو القرآن الكريم\n• المقدم من سورس الورفلي</blockquote>",
            reply_markup=keyboard
        )

        if is_new_user:
            await notify_new_user(
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name
            )
            
    except Exception as e:
        logger.error(f"Error in /start: {e}")
        await message.reply_text("حدث خطأ، الرجاء المحاولة لاحقًا")


@app.on_message(filters.text & filters.private)
async def handle_text(client, message):
    user_id = str(message.from_user.id)
    text = message.text.strip()    
    try:
        if text == "إضافة قناة":
            user_state[user_id] = {"step": "awaiting_channel"}
            await message.reply_text(
                "<blockquote> أرسل معرف القناة أو الرابط (مثال: @channel_name أو https://t.me/channel_name)</blockquote>",
                reply_markup=ReplyKeyboardMarkup([[ "إلغاء"]], resize_keyboard=True)
            )       
        elif text == "بدء البث":
            if user_id not in user_data or not user_data[user_id].get("channels"):
                await message.reply_text("<blockquote> • لم تتم إضافة أي قنوات بعد!</blockquote>")
                return
            
            # عرض قائمة الإذاعات أولاً
            ST_TIMO_list = "\n".join([f"<blockquote> {num}. {info['name']}</blockquote>" for num, info in ST_TIMO.items()])
            await message.reply_text(
                f"<blockquote> اختر رقم الإذاعة:\n{ST_TIMO_list}",
                reply_markup=ReplyKeyboardRemove()
            )
            user_state[user_id] = {"step": "awaiting_station_for_broadcast"}
                      
        elif text == "تحديث البثوث":
            restart_all_broadcasts()
            await message.reply_text("<blockquote> تم تحديث البث</blockquote>")              
        elif text == "إيقاف البث":
            if user_id not in user_data or not user_data[user_id].get("channels"):
                await message.reply_text("<blockquote> • لا توجد قنوات مضافة!</blockquote>")
                return            
            stopped = 0
            for channel_id in list(user_data[user_id]["channels"].keys()):
                channel_info = user_data[user_id]["channels"][channel_id]
                if "process" in channel_info:
                    try:
                        pid = channel_info["process"]
                        if is_ffmpeg_running(pid):
                            subprocess.run(["kill", "-9", str(pid)], timeout=5, check=True)
                            stopped += 1
                        del user_data[user_id]["channels"][channel_id]["process"]
                    except Exception as e:
                        logger.error(f"Error stopping broadcast: {e}")            
            save_data()
            await message.reply_text(f"<blockquote> تم إيقاف {stopped} بث</blockquote>")        
        elif text == "قنواتي":
            if user_id not in user_data or not user_data[user_id].get("channels"):
                await message.reply_text("<blockquote> • لا توجد قنوات مضافة!</blockquote>")
                return            
            channels = user_data[user_id]["channels"]
            response = "<blockquote> قنواتي:</blockquote>\n"
            for num, (channel_id, info) in enumerate(channels.items(), 1):
                status = "🟢 نشط" if "process" in info else "🔴 متوقف"
                response += f"<blockquote> {num}. {info['title']} - {status}</blockquote>\n"            
            await message.reply_text(response)     
        elif text == "حذف قناة":
            if user_id not in user_data or not user_data[user_id].get("channels"):
                await message.reply_text("<blockquote> • لا توجد قنوات مضافة للحذف!</blockquote>")
                return     
            channels = user_data[user_id]["channels"]
            channels_list = "\n".join([f"<blockquote> {num+1}. {info['title']}</blockquote>" for num, (_, info) in enumerate(channels.items())])    
            await message.reply_text(
                f"<blockquote> اختر رقم القناة للحذف:</blockquote>\n{channels_list}",
                reply_markup=ReplyKeyboardMarkup([[ "إلغاء"]], resize_keyboard=True)
            )
            user_state[user_id] = {"step": "awaiting_channel_deletion"}
        elif user_state.get(user_id, {}).get("step") == "awaiting_channel_deletion":
            try:
                channels = list(user_data[user_id]["channels"].items())
                choice = int(text) - 1
                if 0 <= choice < len(channels):
                    channel_id, _ = channels[choice]
                    await delete_channel(client, message, channel_id)
                else:
                    await message.reply_text("<blockquote> • رقم غير صحيح!</blockquote>")
            except ValueError:
                await message.reply_text("<blockquote> • الرجاء إدخال رقم صحيح!</blockquote>")
            finally:
                del user_state[user_id]     
        elif text == "الخروج":
            await message.reply_text(
                "تم إغلاق لوحة الأوامر",
                reply_markup=ReplyKeyboardRemove()
            )        
        elif user_state.get(user_id, {}).get("step") == "awaiting_channel":
            try:
                chat = await client.get_chat(text)
                member = await client.get_chat_member(chat.id, "me")                
                if not member.privileges.can_invite_users:
                    raise Exception("<blockquote> البوت يجب أن يكون مشرفاً مع صلاحية إدارة البث المباشر</blockquote>")               
                user_state[user_id] = {
                    "step": "awaiting_rtmps",
                    "temp_channel": {
                        "id": str(chat.id),
                        "title": chat.title
                    }
                }                
                await message.reply_text(
                    f"<blockquote> • تم تحديد القناة {chat.title} \n</blockquote>"
                    "<blockquote> • الآن أرسل رابط RTMPS للبث</blockquote>",
                    reply_markup=ReplyKeyboardMarkup([[ "إلغاء"]], resize_keyboard=True)
                )            
            except Exception as e:
                await message.reply_text(f"خطأ: {str(e)}")
                del user_state[user_id]        
        elif user_state.get(user_id, {}).get("step") == "awaiting_rtmps":
            if not text.startswith("rtmps://"):
                await message.reply_text("<blockquote> • الرابط يجب أن يبدأ بـ rtmps://</blockquote>")
                return            
            channel_data = user_state[user_id]["temp_channel"]
            user_data.setdefault(user_id, {"channels": {}})            
            user_data[user_id]["channels"][channel_data["id"]] = {
                "title": channel_data["title"],
                "rtmps_url": text,
                "chat_id": channel_data["id"]
            }            
            save_data()
            del user_state[user_id]            
            await message.reply_text(
                f"<blockquote> • تمت إعداد القناة بنجاح! \n"
                f"العنوان: {channel_data['title']}\n"
                f"رابط البث: {text}</blockquote>",
                reply_markup=user_keyboard() if not is_admin(int(user_id)) else admin_keyboard()
            )
        elif user_state.get(user_id, {}).get("step") == "awaiting_station_for_broadcast":
            if text not in ST_TIMO:
                await message.reply_text("<blockquote> • رقم إذاعة غير صحيح!</blockquote>")
                return            
            selected_station_url = ST_TIMO[text]['url']
            user_data[user_id]["temp_station"] = selected_station_url
            save_data()
            
            # بعد اختيار الإذاعة، عرض قائمة القنوات
            channels = user_data[user_id]["channels"]
            channels_list = "\n".join([f"<blockquote> {num+1}. {info['title']}</blockquote>" for num, (_, info) in enumerate(channels.items())])            
            await message.reply_text(
                f"<blockquote> تم اختيار {ST_TIMO[text]['name']}\nاختر رقم القناة للبث:</blockquote>\n{channels_list}",
                reply_markup=ReplyKeyboardRemove()
            )
            user_state[user_id] = {"step": "awaiting_channel_choice", "station_url": selected_station_url}
        elif user_state.get(user_id, {}).get("step") == "awaiting_channel_choice":
            channels = list(user_data[user_id]["channels"].items())
            try:
                choice = int(text) - 1
                if choice < 0 or choice >= len(channels):
                    raise ValueError                
                channel_id, channel_info = channels[choice]
                selected_station = user_state[user_id].get('station_url')                
                if not selected_station:
                    await message.reply_text("<blockquote> • لم يتم اختيار إذاعة بعد!</blockquote>")
                    return                
                if "process" in channel_info:
                    try:
                        pid = channel_info["process"]
                        if is_ffmpeg_running(pid):
                            subprocess.run(["kill", "-9", str(pid)], timeout=5, check=True)
                    except Exception as e:
                        logger.error(f"Error stopping process: {e}")                
                ffmpeg_cmd = [
                    "ffmpeg", "-re", "-i", selected_station,
                    "-c:a", "aac", "-f", "flv", channel_info["rtmps_url"]
                ]
                process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                user_data[user_id]["channels"][channel_id]["process"] = process.pid
                save_data()                
                await send_broadcast_notification(client, channel_info['chat_id'], selected_station)
                await message.reply_text(
                    f"<blockquote> • بدأ البث على {channel_info['title']}</blockquote>",
                    reply_markup=user_keyboard() if not is_admin(int(user_id)) else admin_keyboard()
                )            
            except (ValueError, IndexError):
                await message.reply_text("<blockquote> • رقم قناة غير صحيح!</blockquote>")            
            finally:
                del user_state[user_id]
    except Exception as e:
        logger.error(f"Text handling error: {str(e)}")
        await message.reply_text("حدث خطأ، الرجاء المحاولة لاحقًا")

async def main():
    await app.start()
    logger.info("Bot started...")
    threading.Thread(target=scheduled_restart, daemon=True).start()
    await idle()

if __name__ == "__main__":
    logger.info("Starting Radio Bot...")
    app.run()
