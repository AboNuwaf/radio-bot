# ============================================
# 🤖 بوت راديو القرآن الكريم
# 👤 تطوير: 𝑨𝒃𝒐 𝑵𝒖𝒘𝒂𝒇
# 📲 تيليجرام: @AboNuwaf
# 🔒 جميع الحقوق محفوظة © 2026
# ============================================

import os
import json
import logging
import subprocess
import threading
import time
import asyncio
from pyrogram import Client, filters, idle, enums
from pyrogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, BotCommand
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
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7795185106:AAGNWU0FuYzUTkRJf1yt5XiDcGI2bumDkxo")
OWNER_ID = 6869497898          # المطور الأصلي — لا يمكن إزالته
ADMIN_ID = [OWNER_ID]          # قائمة الأدمنز (تُعدَّل ديناميكياً)

# الصلاحيات المتاحة لكل أدمن — المطور له كل الصلاحيات دايماً
ADMIN_PERMISSIONS = {}  # {user_id: {perm: True/False}}

ALL_PERMISSIONS = {
    "broadcast":    "بدء/إيقاف البث",
    "ban":          "حظر/رفع حظر",
    "broadcast_msg":"إذاعة رسائل",
    "stats":        "إحصائيات",
    "schedule":     "الجدول التلقائي",
    "night_mode":   "الوضع الليلي",
    "daily_report": "تقرير يومي",
    "max_users":    "حد المستخدمين",
    "view_data":    "عرض القنوات/المستخدمين",
    "manage_admins":"رفع/إزالة أدمن",
}

def has_perm(user_id: int, perm: str) -> bool:
    """التحقق من صلاحية معينة — المطور له كل الصلاحيات"""
    if user_id == OWNER_ID:
        return True
    return ADMIN_PERMISSIONS.get(user_id, {}).get(perm, False)

DATA_FILE = "user_data.json"

# قنوات الاشتراك الإجباري
REQUIRED_CHANNELS = [
    {"id": "@Almotawkel_Official", "url": "https://t.me/Almotawkel_Official"},
    {"id": "@quran_Yb", "url": "https://t.me/quran_Yb"},
]

IMAGE_TIMO = "https://i.ibb.co/JWfWVPLn/image.jpg"

FFMPEG_TIMEOUT = 30

# جدول التشغيل التلقائي
AUTO_SCHEDULE = {
    "05:00": {"name": "إذاعة أذكار الصباح", "url": "https://qurango.net/radio/athkar_sabah"},
    "06:00": {"name": "إذاعة ياسر الدوسري", "url": "https://qurango.net/radio/yasser_aldosari"},
    "09:00": {"name": "إذاعة تفسير القرآن الكريم", "url": "https://qurango.net/radio/tafseer"},
    "12:00": {"name": "إذاعة ماهر المعيقلي", "url": "https://qurango.net/radio/maher_al_meaqli"},
    "14:00": {"name": "إذاعة سعد الغامدي", "url": "https://qurango.net/radio/saad_alghamdi"},
    "16:00": {"name": "إذاعة المنشاوي - مرتل", "url": "http://live.mp3quran.net:9826"},
    "18:00": {"name": "إذاعة أذكار المساء", "url": "https://qurango.net/radio/athkar_masa"},
    "19:00": {"name": "إذاعة مشاري العفاسي", "url": "https://qurango.net/radio/mishary_alafasi"},
    "21:00": {"name": "إذاعة عبد الباسط عبد الصمد", "url": "https://qurango.net/radio/abdulbasit_abdulsamad_mojawwad"},
    "23:00": {"name": "إذاعة آيات السكينة", "url": "https://qurango.net/radio/sakeenah"},
}

# محطة التراويح — تشتغل تلقائياً عند وقت صلاة العشاء بتوقيت السعودية
TARAWIH_STATION = {"name": "🕌 إذاعة صلاة التراويح من الحرم المكي", "url": "http://n07.radiojar.com/0tpy1h0kxtzuv?rj-ttl=5&rj-tok=AAABlaaGy1sA0n1Oo_t_c-9DGw"}
tarawih_enabled = True           # تشغيل/إيقاف التراويح
tarawih_time = None              # وقت العشاء (يُجلب تلقائياً كل يوم)
schedule_disabled = set()        # المحطات الموقوفة من الجدول {time_key}

auto_schedule_enabled = False    # للأدمن (global)
user_schedule_enabled = {}       # {user_id: True/False} لكل مستخدم

# إعدادات الخصائص الجديدة
max_users_enabled = False       # تفعيل حد أقصى للمستخدمين
max_users_limit = 100           # الحد الأقصى للمستخدمين
broadcast_stats = {}            # إحصائيات البث لكل قناة
saved_broadcasts = {}           # البثوث المحفوظة للاسترجاع
banned_users = set()            # قائمة المحظورين
broadcast_start_times = {}      # وقت بدء كل بث لحساب المدة
daily_report_enabled = False    # تفعيل/إيقاف التقرير اليومي
station_ratings = {}            # تقييمات المحطات {station_id: {"total": 0, "count": 0, "users": {}}}
night_mode_enabled = False      # الوضع الليلي
night_mode_start = 23           # بداية الوضع الليلي (ساعة)
night_mode_end = 5              # نهاية الوضع الليلي (ساعة)
NIGHT_MODE_STATIONS = ["1", "30", "31", "10", "6"]  # محطات الوضع الليلي (هادية)
broadcast_notify_enabled = True # إشعار الأدمن عند تشغيل محطة
subscription_violations = {}    # عداد مخالفات الاشتراك {user_id: count}
about_bot_visible = True        # إظهار/إخفاء "نبذة عن البوت" للمستخدمين
ABOUT_BOT_IMAGE = "https://ibb.co/JWfWVPLn"  # صورة نبذة عن البوت
maintenance_mode = False        # وضع الصيانة — يمنع غير الأدمن من الاستخدام
MAINTENANCE_IMAGE = "https://ibb.co/nsmph6Hp"  # صورة وضع الصيانة

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
    "23": {"name": "قناة السنه النبويه  ", "url": "https://win.holol.com/live/sunnah/playlist.m3u8"},
    "24": {"name": "إذاعة المنشاوي - مرتل", "url": "http://live.mp3quran.net:9826"},
    "25": {"name": "إذاعة خالد الجليل", "url": "https://qurango.net/radio/khalid_aljileel"},
    "26": {"name": "إذاعة محمود الحصري - مرتل", "url": "http://live.mp3quran.net:9958"},
    "27": {"name": "إذاعة ناصر القطامي", "url": "https://qurango.net/radio/nasser_alqatami"},
    "28": {"name": "إذاعة تفسير القرآن الكريم", "url": "https://qurango.net/radio/tafseer"},
    "29": {"name": "إذاعة سعد الغامدي", "url": "https://qurango.net/radio/saad_alghamdi"},
    "30": {"name": "إذاعة أذكار الصباح", "url": "https://qurango.net/radio/athkar_sabah"},
    "31": {"name": "إذاعة أذكار المساء", "url": "https://qurango.net/radio/athkar_masa"}
}

# أقسام الإذاعات
ST_CATEGORIES = {
    "🎙 القراء": ["11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "24", "25", "26", "27", "29"],
    "🕌 القنوات والمحطات": ["2", "3", "4", "9", "10", "22", "23"],
    "📿 الأذكار والرقية": ["1", "6", "7", "30", "31"],
    "📖 التفسير والسيرة": ["5", "8", "28"],
}

app = Client("radio_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, parse_mode=enums.ParseMode.HTML)
_bot_loop = None  # يُعيَّن في main() لاستخدامه في الـ threads

data_lock = threading.Lock()
user_data = {}
user_state = {}

def get_station_rating(sid):
    """حساب متوسط تقييم محطة"""
    if sid not in station_ratings or station_ratings[sid]["count"] == 0:
        return 0.0
    return round(station_ratings[sid]["total"] / station_ratings[sid]["count"], 1)

def get_rating_stars(rating):
    """تحويل الرقم لنجوم"""
    full = int(rating)
    half = 1 if (rating - full) >= 0.5 else 0
    empty = 5 - full - half
    return "⭐" * full + ("✨" if half else "") + "☆" * empty

def fetch_isha_time():
    """جلب وقت صلاة العشاء في الرياض تلقائياً"""
    global tarawih_time
    try:
        import urllib.request, json as _json
        url = "https://api.aladhan.com/v1/timingsByCity?city=Riyadh&country=Saudi%20Arabia&method=4"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = _json.loads(resp.read())
        isha = data["data"]["timings"]["Isha"]
        # تحويل من 12ساعة لـ 24ساعة لو لازم
        tarawih_time = isha[:5]
        logger.info(f"Tarawih time fetched: {tarawih_time}")
    except Exception as e:
        logger.error(f"Failed to fetch Isha time: {e}")
        tarawih_time = "20:30"  # وقت افتراضي لو فشل الجلب

def tarawih_thread():
    """thread التراويح — يشغل إذاعة الحرم المكي عند وقت العشاء"""
    global tarawih_time, tarawih_enabled
    last_triggered = None
    last_fetch_day = None
    while True:
        try:
            today = time.strftime("%Y-%m-%d")
            # جلب وقت العشاء مرة يومياً
            if last_fetch_day != today:
                fetch_isha_time()
                last_fetch_day = today

            if tarawih_enabled and tarawih_time:
                current_time = time.strftime("%H:%M")
                if current_time == tarawih_time and last_triggered != today:
                    last_triggered = today
                    logger.info(f"Tarawih starting at {tarawih_time}")
                    for uid, uinfo in list(user_data.items()):
                        for ch_id, ch_info in list(uinfo.get("channels", {}).items()):
                            try:
                                if "process" in ch_info:
                                    pid = ch_info["process"]
                                    if is_ffmpeg_running(pid):
                                        subprocess.run(["kill", "-9", str(pid)], timeout=5, check=True)
                                ffmpeg_cmd = [
                                    "ffmpeg", "-re", "-i", TARAWIH_STATION["url"],
                                    "-vn", "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                                    "-f", "flv", ch_info["rtmps_url"]
                                ]
                                process = subprocess.Popen(
                                    ffmpeg_cmd,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL
                                )
                                ch_info["process"] = process.pid
                            except Exception as e:
                                logger.error(f"Tarawih error on {ch_id}: {e}")
                    save_data()
        except Exception as e:
            logger.error(f"Tarawih thread error: {e}")
        time.sleep(30)

def night_mode_thread():
    """الوضع الليلي — يشغل محطات هادية بعد منتصف الليل تلقائياً"""
    night_active = False
    while True:
        hour = int(time.strftime("%H"))
        # الوضع الليلي من 11 مساءً لـ 5 صباحاً
        is_night = (hour >= night_mode_start) or (hour < night_mode_end)
        if night_mode_enabled and is_night and not night_active:
            night_active = True
            night_url = ST_TIMO[NIGHT_MODE_STATIONS[0]]["url"]
            logger.info("Night mode activated — switching to calm stations")
            for user_id, user_info in list(user_data.items()):
                station = user_info.get("temp_station")
                if not station:
                    continue
                for channel_id, channel_info in list(user_info.get("channels", {}).items()):
                    if "process" not in channel_info:
                        continue
                    try:
                        pid = channel_info["process"]
                        if is_ffmpeg_running(pid):
                            subprocess.run(["kill", "-9", str(pid)], timeout=5, check=True)
                        ffmpeg_cmd = [
                            "ffmpeg", "-re", "-i", night_url,
                            "-vn", "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                            "-f", "flv", channel_info["rtmps_url"]
                        ]
                        process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        user_data[user_id]["channels"][channel_id]["process"] = process.pid
                    except Exception as e:
                        logger.error(f"Night mode error: {e}")
            save_data()
            try:
                asyncio.run_coroutine_threadsafe(
                    app.send_message(ADMIN_ID[0],
                        "<blockquote>🌙 تم تفعيل الوضع الليلي تلقائياً\n"
                        "• تم التحويل إلى: " + ST_TIMO[NIGHT_MODE_STATIONS[0]]["name"] + "</blockquote>"
                    ), _bot_loop
                )
            except Exception as e:
                logger.error(f"Night mode notify error: {e}")
        elif not is_night:
            night_active = False
        time.sleep(60)

def get_broadcast_duration(channel_id):
    """حساب مدة البث بالساعات والدقائق"""
    if channel_id not in broadcast_start_times:
        return "غير معروف"
    elapsed = time.time() - broadcast_start_times[channel_id]
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    return f"{hours} ساعة و {minutes} دقيقة"

def daily_report_thread():
    """إرسال تقرير يومي للأدمن الساعة 8 صباحاً إذا كان مفعلاً"""
    sent_today = False
    while True:
        current_time = time.strftime("%H:%M")
        if current_time == "08:00" and not sent_today:
            if daily_report_enabled:
                total_users = len(user_data)
                active_broadcasts = sum(
                    1 for u in list(user_data.values())
                    for ch in list(u.get("channels", {}).values())
                    if "process" in ch
                )
                report = (
                    "<blockquote>📊 التقرير اليومي\n\n"
                    "👥 إجمالي المستخدمين: " + str(total_users) + "\n"
                    "📡 البثوث النشطة: " + str(active_broadcasts) + "\n"
                    "🚫 المحظورون: " + str(len(banned_users)) + "\n"
                    "⏰ " + time.strftime("%Y-%m-%d") + "</blockquote>"
                )
                try:
                    asyncio.run_coroutine_threadsafe(
                        app.send_message(ADMIN_ID[0], report), _bot_loop
                    )
                except Exception as e:
                    logger.error(f"Daily report error: {e}")
            sent_today = True
        elif current_time != "08:00":
            sent_today = False
        time.sleep(30)

def save_broadcast_state():
    """حفظ حالة البثوث الحالية للاسترجاع بعد restart"""
    global saved_broadcasts
    saved_broadcasts = {}
    for user_id, user_info in list(user_data.items()):
        station = user_info.get("temp_station")
        if not station:
            continue
        channels = user_info.get("channels", {})
        for channel_id, channel_info in list(channels.items()):
            if "process" in channel_info:
                saved_broadcasts[channel_id] = {
                    "user_id": user_id,
                    "station": station,
                    "rtmps_url": channel_info["rtmps_url"]
                }

def restore_broadcasts():
    """استرجاع البثوث بعد restart"""
    if not saved_broadcasts:
        return
    logger.info(f"Restoring {len(saved_broadcasts)} broadcasts after restart...")
    for channel_id, info in saved_broadcasts.items():
        try:
            ffmpeg_cmd = [
                "ffmpeg", "-re", "-i", info["station"],
                "-vn",
                "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                "-f", "flv", info["rtmps_url"]
            ]
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            user_data[info["user_id"]]["channels"][channel_id]["process"] = process.pid
            logger.info(f"Restored broadcast for channel {channel_id}")
        except Exception as e:
            logger.error(f"Error restoring broadcast: {e}")
    save_data()

async def check_subscription(client, user_id):
    """يتحقق من اشتراك المستخدم ويرجع القناة الأولى اللي مش مشترك فيها"""
    for channel in REQUIRED_CHANNELS:
        try:
            member = await client.get_chat_member(channel["id"], user_id)
            if member.status.name in ["LEFT", "BANNED", "KICKED"]:
                return channel
        except Exception:
            pass
    return None

async def stop_user_broadcasts(user_id):
    """إيقاف كل بثوث المستخدم"""
    uid = str(user_id)
    if uid not in user_data:
        return []
    stopped = []
    for channel_id, channel_info in list(user_data[uid].get("channels", {}).items()):
        if "process" in channel_info:
            try:
                pid = channel_info["process"]
                if is_ffmpeg_running(pid):
                    subprocess.run(["kill", "-9", str(pid)], timeout=5, check=True)
            except Exception as e:
                logger.error(f"stop_user_broadcasts kill error: {e}")
            channel_info.pop("process", None)
            stopped.append(channel_info.get("title", channel_id))
    if stopped:
        save_data()
    return stopped

def subscription_watcher_thread():
    """مراقب الاشتراك الإجباري — يتحقق كل دقيقة من كل المستخدمين النشطين"""
    while True:
        time.sleep(60)
        try:
            # جلب المستخدمين اللي عندهم بث نشط
            active_users = []
            for uid, uinfo in list(user_data.items()):
                for ch_id, ch_info in list(uinfo.get("channels", {}).items()):
                    if "process" in ch_info:
                        active_users.append(uid)
                        break

            for uid in active_users:
                if int(uid) in banned_users:
                    continue
                future = asyncio.run_coroutine_threadsafe(
                    _check_and_punish(uid), _bot_loop
                )
                try:
                    future.result(timeout=15)
                except Exception as e:
                    logger.error(f"Subscription watcher future error: {e}")
        except Exception as e:
            logger.error(f"Subscription watcher error: {e}")

async def _check_and_punish(uid):
    """تحقق من اشتراك مستخدم نشط وعاقبه لو خرج"""
    global subscription_violations, banned_users
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    unsubscribed = await check_subscription(app, int(uid))
    if not unsubscribed:
        # مشترك — صفّر المخالفات
        subscription_violations.pop(uid, None)
        return

    # زوّد المخالفات
    subscription_violations[uid] = subscription_violations.get(uid, 0) + 1
    count = subscription_violations[uid]

    # وقف البث
    stopped = await stop_user_broadcasts(uid)

    if count >= 5:
        # حظر تلقائي
        banned_users.add(int(uid))
        subscription_violations.pop(uid, None)
        try:
            await app.send_message(
                int(uid),
                "<blockquote>🚫 تم حظرك تلقائياً\n\n"
                "السبب: تكرار الخروج من قنوات الاشتراك الإجباري\n"
                "عدد المخالفات: 5 مخالفات\n\n"
                "لفك الحظر تواصل مع المطور:</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💬 تواصل مع الأدمن", url="https://t.me/AboNuwaf")],
                    [InlineKeyboardButton("🤖 تواصل عبر البوت", url="https://t.me/AboNuwaf1_bot")]
                ])
            )
        except Exception as e:
            logger.error(f"Ban notify user error: {e}")
        try:
            await app.send_message(
                ADMIN_ID[0],
                "<blockquote>🚫 تم حظر مستخدم تلقائياً\n"
                "👤 ID: " + uid + "\n"
                "السبب: تكرار الخروج من قنوات الاشتراك الإجباري 5 مرات</blockquote>"
            )
        except Exception as e:
            logger.error(f"Ban notify admin error: {e}")
    else:
        # تحذير مع قطع البث
        remaining = 5 - count
        ch_names = "، ".join(stopped) if stopped else "قنواتك"
        try:
            await app.send_message(
                int(uid),
                "<blockquote>⚠️ تم إيقاف البث\n\n"
                "السبب: خروجك من قناة الاشتراك الإجباري\n"
                "القناة: " + unsubscribed["id"] + "\n\n"
                "القنوات الموقوفة: " + ch_names + "\n\n"
                "تحذير " + str(count) + " من 5 — "
                "بعد " + str(remaining) + " مخالفة"
                + (" أخرى" if remaining > 1 else "") +
                " سيتم حظرك تلقائياً\n\n"
                "اشترك في القناة وأعد تشغيل البث:</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📢 اشترك الآن", url=unsubscribed["url"])]
                ])
            )
        except Exception as e:
            logger.error(f"Warn user error: {e}")

async def send_subscription_message(message, channel):
    """يبعت رسالة الاشتراك الإجباري"""
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    channel_name = channel["id"].replace("@", "")
    channel_id = channel["id"]
    channel_url = channel["url"]
    text = (
        "🚸| عذراً عزيزي.\n"
        "🔰| لاستخدام هذا البوت، يُرجى الاشتراك أولًا في " + channel_id + "\n\n"
        "• نهدف من ذلك إلى نشر الخير والتذكير، ونسأل الله أن يجعل اشتراكك ومتابعتك في ميزان حسناتك.\n\n"
        "- " + channel_url + "\n\n"
        "‼️| بعد الاشتراك، اضغط /check للمتابعة."
    )
    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 اشترك الآن", url=channel["url"])]
        ])
    )

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
        for channel_id, channel_info in list(user_info.get("channels", {}).items()):
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
                    "-vn",
                    "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
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
        import copy
        current_data = copy.deepcopy(user_data)
        for user_id, user_info in current_data.items():
            channels = user_info.get("channels", {})
            selected_station = user_info.get('temp_station')            
            if not selected_station:
                continue                
            for channel_id, info in list(channels.items()):
                try:
                    if "process" in info:
                        if is_ffmpeg_running(info["process"]):
                            subprocess.run(["kill", "-9", str(info["process"])], timeout=5, check=True)
                    ffmpeg_cmd = [
                        "ffmpeg", "-re", "-i", selected_station,
                        "-vn",
                        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
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


def build_schedule_buttons():
    """بناء أزرار الجدول مرتبة بالوقت مع إدراج التراويح في مكانها الصحيح"""
    from pyrogram.types import InlineKeyboardButton
    def to_arabic_time(t):
        h, m = map(int, t.split(":"))
        period = "صباحاً" if h < 12 else "مساءً"
        h12 = h if h <= 12 else h - 12
        if h12 == 0: h12 = 12
        return f"{h12}:{m:02d} {period}"

    # دمج الجدول العادي مع التراويح
    all_entries = []
    for t, s in AUTO_SCHEDULE.items():
        all_entries.append(("schedule", t, s))
    if tarawih_time:
        all_entries.append(("tarawih", tarawih_time, TARAWIH_STATION))

    # ترتيب حسب الوقت
    all_entries.sort(key=lambda x: x[1])

    buttons = []
    for entry_type, t, s in all_entries:
        ar_time = to_arabic_time(t)
        if entry_type == "schedule":
            is_on = t not in schedule_disabled
            name = s['name'].replace("إذاعة ", "").replace("اذاعة ", "").strip()
            buttons.append([
                InlineKeyboardButton(f"{'✅' if is_on else '❌'} {ar_time} — {name}", callback_data="noop"),
                InlineKeyboardButton("تشغيل" if not is_on else "إيقاف",
                    callback_data=f"sched_toggle_{t}_{'on' if not is_on else 'off'}")
            ])
        else:
            name = s['name'].replace("إذاعة ", "").replace("اذاعة ", "").strip()
            buttons.append([
                InlineKeyboardButton(f"{'✅' if tarawih_enabled else '❌'} {ar_time} — {name}", callback_data="noop"),
                InlineKeyboardButton("تشغيل" if not tarawih_enabled else "إيقاف", callback_data="tarawih_toggle")
            ])
    return buttons

def run_auto_schedule():
    """تشغيل الجدول التلقائي — كل مستخدم على قنواته فقط"""
    while True:
        current_time = time.strftime("%H:%M")
        if current_time in AUTO_SCHEDULE and current_time not in schedule_disabled:
            station = AUTO_SCHEDULE[current_time]
            switched = False
            for uid, user_info in list(user_data.items()):
                # الأدمن يشتغل لو auto_schedule_enabled، المستخدم لو فعّله هو
                if is_admin(int(uid)):
                    if not auto_schedule_enabled:
                        continue
                else:
                    if not user_schedule_enabled.get(uid, False):
                        continue
                channels = user_info.get("channels", {})
                if not channels:
                    continue
                for channel_id, channel_info in list(channels.items()):
                    try:
                        if "process" in channel_info:
                            pid = channel_info["process"]
                            if is_ffmpeg_running(pid):
                                subprocess.run(["kill", "-9", str(pid)], timeout=5, check=True)
                        ffmpeg_cmd = [
                            "ffmpeg", "-re", "-i", station["url"],
                            "-vn",
                            "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                            "-f", "flv", channel_info["rtmps_url"]
                        ]
                        process = subprocess.Popen(
                            ffmpeg_cmd,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        user_data[uid]["channels"][channel_id]["process"] = process.pid
                        switched = True
                    except Exception as e:
                        logger.error(f"Auto schedule error: {e}")
            if switched:
                save_data()
                logger.info(f"Auto schedule: switched to {station['name']}")
                asyncio.run_coroutine_threadsafe(
                    notify_schedule_change(station["name"]), _bot_loop
                )
        time.sleep(60)

async def notify_schedule_change(station_name):
    """إرسال إشعار للأدمن عند تغيير المحطة تلقائياً"""
    try:
        msg = "<blockquote>🕐 تم تغيير المحطة تلقائياً إلى:\n" + station_name + "</blockquote>"
        await app.send_message(ADMIN_ID[0], msg)
    except Exception as e:
        logger.error(f"Notify schedule error: {e}")

def watchdog():
    """مراقب تلقائي يتحقق من الـ ffmpeg كل 30 ثانية ويعيد تشغيله لو وقف"""
    while True:
        try:
            for user_id, user_info in list(user_data.items()):
                selected_station = user_info.get("temp_station")
                if not selected_station:
                    continue
                channels = user_info.get("channels", {})
                for channel_id, channel_info in list(channels.items()):
                    if "process" not in channel_info:
                        continue
                    pid = channel_info["process"]
                    if not is_ffmpeg_running(pid):
                        logger.warning(f"Watchdog: ffmpeg stopped for channel {channel_id}, restarting...")
                        try:
                            ffmpeg_cmd = [
                                "ffmpeg", "-re", "-i", selected_station,
                                "-vn",
                                "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                                "-f", "flv", channel_info["rtmps_url"]
                            ]
                            process = subprocess.Popen(
                                ffmpeg_cmd,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL
                            )
                            user_data[user_id]["channels"][channel_id]["process"] = process.pid
                            logger.info(f"Watchdog: restarted ffmpeg for channel {channel_id}")
                        except Exception as e:
                            logger.error(f"Watchdog restart error: {e}")
            save_data()
        except Exception as e:
            logger.error(f"Watchdog error: {e}")
        time.sleep(30)

def scheduled_restart():
    while True:
        logger.info("Performing scheduled restart...")
        restart_all_broadcasts()
        time.sleep(300)

async def send_broadcast_notification(client, chat_id, station_url):
    try:
        station_id = next((k for k, v in ST_TIMO.items() if v["url"] == station_url), None)
        if not station_id:
            logger.warning(f"Station URL not found in ST_TIMO: {station_url}")
            return
        station_name = ST_TIMO[station_id]["name"]
        await client.send_photo(
            chat_id=chat_id,
            photo=IMAGE_TIMO,
            caption=f"<blockquote> • بدأ بث القرآن الكريم من {station_name}</blockquote>"
        )
    except Exception as e:
        logger.error(f"Notification failed: {str(e)}")

async def notify_new_user(user_id, username, first_name):
    username_display = f"@{username}" if username else "بدون يوزر"
    text = (
        f"<blockquote> • مستخدم جديد!\n</blockquote>"
        f"<blockquote> • المعرف: {user_id}\n</blockquote>"
        f"<blockquote> • الاسم: {first_name}\n</blockquote>"
        f"<blockquote> • اليوزر: {username_display}</blockquote>"
    )
    try:
        await app.send_message(ADMIN_ID[0], text)
    except Exception as e:
        logger.error(f"notify_new_user error: {e}")
    
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
    total_channels = sum(len(user["channels"]) for user in list(user_data.values()) if "channels" in user)
    
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
    users = list(user_data.keys())
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
        await asyncio.sleep(0.5)
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
    for user in list(user_data.values()):
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
        await asyncio.sleep(0.5)
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

    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    seen_channels = set()
    station_reverse = {v['url']: v['name'] for k, v in ST_TIMO.items()}
    total = 0

    try:
        for uid, user_info in list(user_data.items()):
            if "channels" not in user_info:
                continue

            # جلب بيانات صاحب القناة
            try:
                owner = await client.get_users(int(uid))
                owner_name = owner.first_name or "غير معروف"
                owner_username = f"@{owner.username}" if owner.username else None
                owner_link = f"tg://user?id={uid}"
            except Exception as e:
                logger.error(f"get_users error for {uid}: {e}")
                owner_name = user_info.get("name", "غير معروف")
                owner_username = None
                owner_link = None

            current_station = user_info.get('temp_station', '')
            station_name = station_reverse.get(current_station, 'لا يوجد')

            for channel_id, channel_info in list(user_info["channels"].items()):
                if channel_id in seen_channels:
                    continue
                seen_channels.add(channel_id)
                total += 1

                broadcast_status = "🟢 قيد التشغيل" if 'process' in channel_info else "🔴 متوقف"
                ch_title = channel_info.get('title', 'غير معروف')

                # بناء أزرار كل قناة
                buttons = []
                row = []

                # زرار دخول القناة
                try:
                    chat = await client.get_chat(int(channel_id))
                    if chat.username:
                        row.append(InlineKeyboardButton("📢 دخول القناة", url=f"https://t.me/{chat.username}"))
                    elif chat.invite_link:
                        row.append(InlineKeyboardButton("📢 دخول القناة", url=chat.invite_link))
                    ch_title = chat.title or ch_title
                    members = "غير متاح"
                    try:
                        members = await client.get_chat_members_count(int(channel_id))
                    except Exception:
                        pass
                except Exception as e:
                    logger.error(f"get_chat error for {channel_id}: {e}")
                    members = "غير متاح"

                # زرار الأكونت صاحب القناة
                if owner_link:
                    row.append(InlineKeyboardButton(f"👤 {owner_name}", url=owner_link))
                if row:
                    buttons.append(row)

                text = (
                    "<blockquote>"
                    f"📢 <b>{ch_title}</b>\n"
                    f"👥 الأعضاء: {members}\n"
                    f"🎙 المحطة: {station_name}\n"
                    f"📡 البث: {broadcast_status}\n"
                    f"👤 الصاحب: {owner_name}"
                    + (f"  ({owner_username})" if owner_username else "")
                    + "</blockquote>"
                )

                await message.reply(
                    text,
                    reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
                )
                await asyncio.sleep(0.5)

        if total == 0:
            await message.reply("<blockquote> • لم تتم إضافة أي قنوات بعد!</blockquote>")
        else:
            await message.reply(f"<blockquote>📊 إجمالي القنوات: {total}</blockquote>")

    except Exception as e:
        logger.error(f"Error in channel list command: {e}")
        await message.reply("<blockquote> • حدث خطأ أثناء جلب القنوات!</blockquote>")
        
@app.on_message(filters.command(["المستخدمين"], "") & filters.private)
async def list_users_command(client, message):
    if not is_admin(message.from_user.id):
        await message.reply("<blockquote> • ليس لديك صلاحية الوصول لهذا الأمر!</blockquote>")
        return

    if not user_data:
        await message.reply("<blockquote> • لا يوجد مستخدمين مسجلين بعد!</blockquote>")
        return

    users_list = []
    for user_id, user_info in list(user_data.items()):
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
    rows = [
        ["إضافة قناة", "قنواتي"],
        ["بدء البث", "إيقاف البث"],
        ["تحديث البثوث", "حذف قناة"],
        ["⚙️ الجدول التلقائي"],
        ["🛠 الدعم الفني"],
        ["📞 تواصل مع الأدمن"],
        ["الخروج"]
    ]
    if about_bot_visible:
        rows.insert(-1, ["ℹ️ نبذة عن البوت"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def admin_keyboard():
    max_btn = "🔓 حد المستخدمين: مفتوح" if not max_users_enabled else f"🔒 حد المستخدمين: {max_users_limit}"
    report_btn = "📋 التقرير اليومي: مفتوح 🟢" if daily_report_enabled else "📋 التقرير اليومي: مقفول 🔴"
    night_btn = "🌙 الوضع الليلي: مفعّل 🟢" if night_mode_enabled else "🌙 الوضع الليلي: مقفول 🔴"
    notify_btn = "🔔 إشعار المحطات: مفعّل 🟢" if broadcast_notify_enabled else "🔕 إشعار المحطات: مقفول 🔴"
    about_btn = "ℹ️ نبذة عن البوت: ظاهر 🟢" if about_bot_visible else "ℹ️ نبذة عن البوت: مخفي 🔴"
    maintenance_btn = "🔴 الآن: البوت في وضع الصيانة 🔴" if maintenance_mode else "🟢 الآن: البوت يعمل بنجاح 🟢"
    return ReplyKeyboardMarkup([
        [maintenance_btn],
        ["إضافة قناة", "قنواتي"],
        ["بدء البث", "إيقاف البث"],
        ["تحديث البثوث", "حذف قناة"],
        ["الاحصائيات", "📊 إحصائيات البث"],
        ["اذاعة للمستخدمين", "اذاعة للقنوات"],
        ["القنوات", "المستخدمين"],
        ["⚙️ الجدول التلقائي"],
        [max_btn],
        [report_btn],
        [night_btn],
        [notify_btn],
        [about_btn],
        ["ℹ️ نبذة عن البوت"],
        ["🛠 الدعم الفني"],
        ["🚫 حظر مستخدم", "✅ رفع الحظر"],
        ["➕ رفع أدمن", "➖ إزالة أدمن"],
        ["👑 إدارة الأدمنز"],
        ["📞 تواصل مع الأدمن"],
        ["الخروج"]
    ], resize_keyboard=True)

def schedule_keyboard():
    return ReplyKeyboardMarkup([
        ["▶️ تشغيل تلقائي", "⏹ إيقاف تلقائي"],
        ["✏️ تعديل موعد", "🎙 تغيير محطة"],
        ["🔙 رجوع"]
    ], resize_keyboard=True)


async def show_station_categories(message):
    """عرض الأقسام فقط كأزرار — لما تضغط قسم يظهر محتواه"""
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for cat_name, station_ids in ST_CATEGORIES.items():
        count = len(station_ids)
        label = "محطة" if count == 1 else "محطات"
        buttons.append([InlineKeyboardButton(f"{cat_name}  ({count} {label})", callback_data=f"cat_{cat_name}")])
    await message.reply_text(
        "<blockquote>🎙 اختر قسم الإذاعة:</blockquote>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def show_stations_in_category(query, cat_name):
    """عرض المحطات داخل القسم كأزرار — تضغط أو تكتب رقمها"""
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    station_ids = ST_CATEGORIES.get(cat_name, [])

    # بناء النص مع الأرقام
    text = f"<blockquote>{cat_name}\n\n"
    buttons = []
    row = []
    for i, sid in enumerate(station_ids, 1):
        name = ST_TIMO[sid]["name"].replace("إذاعة ", "").replace("اذاعة ", "").replace("قناة ", "").strip()
        text += f"{i}. {name}\n"
        row.append(InlineKeyboardButton(f"{i}. {name}", callback_data=f"station_{sid}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    text += "\nاضغط على المحطة أو اكتب رقمها:</blockquote>"
    buttons.append([InlineKeyboardButton("🔙 رجوع للأقسام", callback_data="cat_back")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query()
async def handle_callback(client, query):
    global tarawih_enabled
    user_id = str(query.from_user.id)
    data = query.data

    # ===== الوضع الليلي =====
    # ===== تعديل الجدول التلقائي =====
    if data.startswith("edit_time_"):
        old_time = data[10:]
        user_state[user_id] = {"step": "awaiting_new_time", "old_time": old_time}
        await query.answer()
        station_name = AUTO_SCHEDULE.get(old_time, {}).get("name", "")
        await query.edit_message_text(
            f"<blockquote>✏️ تعديل موعد\n\n"
            f"الوقت الحالي: {old_time}\n"
            f"المحطة: {station_name}\n\n"
            f"أرسل الوقت الجديد بهذا الشكل:\n07:30</blockquote>"
        )

    elif data.startswith("edit_station_"):
        target_time = data[13:]
        user_state[user_id] = {"step": "awaiting_new_station_for_schedule", "target_time": target_time}
        await query.answer()
        # عرض قائمة المحطات بأرقام
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        for cat_name, station_ids in ST_CATEGORIES.items():
            buttons.append([InlineKeyboardButton(cat_name, callback_data=f"sched_cat_{target_time}_{cat_name}")])
        current = AUTO_SCHEDULE.get(target_time, {}).get("name", "")
        await query.edit_message_text(
            f"<blockquote>🎙 تغيير محطة الساعة {target_time}\n"
            f"المحطة الحالية: {current}\n\n"
            f"اختر القسم:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("sched_cat_"):
        # sched_cat_{time}_{cat_name}
        rest = data[10:]
        # الوقت هو أول جزء HH:MM
        target_time = rest[:5]
        cat_name = rest[6:]
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        station_ids = ST_CATEGORIES.get(cat_name, [])
        buttons = []
        row = []
        for i, sid in enumerate(station_ids, 1):
            name = ST_TIMO[sid]["name"].replace("إذاعة ", "").replace("اذاعة ", "").strip()
            row.append(InlineKeyboardButton(f"{i}. {name}", callback_data=f"sched_pick_{target_time}_{sid}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        await query.edit_message_text(
            f"<blockquote>🎙 اختر المحطة للساعة {target_time}:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("sched_pick_"):
        # sched_pick_{time}_{sid}
        rest = data[11:]
        target_time = rest[:5]
        sid = rest[6:]
        if sid in ST_TIMO and target_time in AUTO_SCHEDULE:
            AUTO_SCHEDULE[target_time] = {"name": ST_TIMO[sid]["name"], "url": ST_TIMO[sid]["url"]}
            user_state.pop(user_id, None)
            await query.edit_message_text(
                f"<blockquote>✅ تم تغيير محطة الساعة {target_time}\n"
                f"إلى: {ST_TIMO[sid]['name']}</blockquote>"
            )
        else:
            await query.answer("❌ حدث خطأ", show_alert=True)

    elif data == "night_toggle":
        if not is_admin(int(user_id)):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        global night_mode_enabled
        night_mode_enabled = not night_mode_enabled
        status = "مفعّل 🟢" if night_mode_enabled else "مقفول 🔴"
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await query.edit_message_text(
            "<blockquote>🌙 الوضع الليلي\n\n"
            "الحالة: " + status + "\n"
            "⏰ من: " + str(night_mode_start) + ":00 حتى " + str(night_mode_end) + ":00</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "⏹ إيقاف الوضع الليلي" if night_mode_enabled else "▶️ تشغيل الوضع الليلي",
                    callback_data="night_toggle"
                )],
                [InlineKeyboardButton("🕐 تغيير وقت البداية", callback_data="night_set_start")],
                [InlineKeyboardButton("🕔 تغيير وقت النهاية", callback_data="night_set_end")],
            ])
        )
        await query.answer("✅ تم " + ("تفعيل" if night_mode_enabled else "إيقاف") + " الوضع الليلي")

    elif data == "night_set_start":
        if not is_admin(int(user_id)):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        user_state[user_id] = {"step": "awaiting_night_start"}
        await query.answer()
        await query.message.reply_text(
            "<blockquote>🕐 أرسل ساعة بداية الوضع الليلي (0-23)\nمثال: 23 تعني 11 مساءً</blockquote>",
            reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
        )

    elif data == "night_set_end":
        if not is_admin(int(user_id)):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        user_state[user_id] = {"step": "awaiting_night_end"}
        await query.answer()
        await query.message.reply_text(
            "<blockquote>🕔 أرسل ساعة نهاية الوضع الليلي (0-23)\nمثال: 5 تعني 5 صباحاً</blockquote>",
            reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
        )
    elif data == "cat_back":
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        for cat_name in ST_CATEGORIES:
            count = len(ST_CATEGORIES[cat_name])
            buttons.append([InlineKeyboardButton(f"{cat_name} ({count})", callback_data=f"cat_{cat_name}")])
        await query.edit_message_text(
            "<blockquote>🎙 اختر قسم الإذاعة:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # اختيار قسم
    elif data.startswith("cat_"):
        cat_name = data[4:]
        if cat_name in ST_CATEGORIES:
            # حفظ القسم الحالي في user_state
            if user_id not in user_state:
                user_state[user_id] = {"step": "awaiting_station_for_broadcast"}
            user_state[user_id]["current_cat"] = cat_name
            await show_stations_in_category(query, cat_name)

    # اختيار محطة
    elif data.startswith("station_"):
        sid = data[8:]
        if sid not in ST_TIMO:
            await query.answer("❌ محطة غير موجودة", show_alert=True)
            return

        # التحقق أن المستخدم في خطوة اختيار محطة
        if user_state.get(user_id, {}).get("step") != "awaiting_station_for_broadcast":
            await query.answer("❌ اضغط بدء البث أولاً", show_alert=True)
            return

        selected_station_url = ST_TIMO[sid]["url"]
        station_name = ST_TIMO[sid]["name"]
        if user_id not in user_data:
            await query.answer("❌ لم يتم تسجيلك، أرسل /start أولاً", show_alert=True)
            return
        user_data[user_id]["temp_station"] = selected_station_url
        save_data()

        # عرض قائمة القنوات
        channels = user_data[user_id]["channels"]
        if not channels:
            await query.answer("❌ لا توجد قنوات مضافة!", show_alert=True)
            return

        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        ch_buttons = []
        for num, (ch_id, ch_info) in enumerate(list(channels.items())):
            status = "🟢" if "process" in ch_info else "🔴"
            ch_buttons.append([InlineKeyboardButton(
                f"{status} {ch_info['title']}",
                callback_data=f"broadcast_{ch_id}"
            )])

        await query.edit_message_text(
            f"<blockquote>✅ تم اختيار: {station_name}\n\nاختر القناة للبث:</blockquote>",
            reply_markup=InlineKeyboardMarkup(ch_buttons)
        )
        user_state[user_id] = {"step": "awaiting_channel_choice", "station_url": selected_station_url}

    # عرض الأعلى تقييماً
    # ===== مركز الدعم الفني =====
    elif data == "support_report":
        user_state[user_id] = {"step": "awaiting_report"}
        await query.answer()
        await query.edit_message_text(
            "<blockquote>⚠️ الإبلاغ عن مشكلة\n\n"
            "📝 اكتب وصف المشكلة (إجباري)\n"
            "📸 إضافة صورة (اختياري) — إرفاق صورة يساعد على حل المشكلة أسرع\n\n"
            "• سيتم إرسال بلاغك مباشرة للمطور\n"
            "• سيتم الرد عليك في أقرب وقت\n\n"
            "اكتب مشكلتك الآن 👇</blockquote>"
        )

    elif data == "support_rate_bot":
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await query.edit_message_text(
            "<blockquote>⭐ تقييم البوت\n\nكم تعطي البوت من 10؟</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("1", callback_data="bot_rate_1"),
                 InlineKeyboardButton("2", callback_data="bot_rate_2"),
                 InlineKeyboardButton("3", callback_data="bot_rate_3"),
                 InlineKeyboardButton("4", callback_data="bot_rate_4"),
                 InlineKeyboardButton("5", callback_data="bot_rate_5")],
                [InlineKeyboardButton("6", callback_data="bot_rate_6"),
                 InlineKeyboardButton("7", callback_data="bot_rate_7"),
                 InlineKeyboardButton("8", callback_data="bot_rate_8"),
                 InlineKeyboardButton("9", callback_data="bot_rate_9"),
                 InlineKeyboardButton("10", callback_data="bot_rate_10")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="ratings_back")]
            ])
        )

    elif data.startswith("bot_rate_") and not data.startswith("bot_rate_skip_"):
        score = int(data[9:])
        user_state[user_id] = {"step": "awaiting_bot_review", "bot_rating_stars": score}
        await query.answer()
        await query.edit_message_text(
            "<blockquote>⭐ تقييمك: " + str(score) + "/10\n\n"
            "✍️ اكتب تعليقك على البوت (إجباري)\n"
            "أرسل نصك الآن 👇</blockquote>"
        )

    elif data == "support_rate_stations":
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        for cat_name in ST_CATEGORIES:
            buttons.append([InlineKeyboardButton(cat_name, callback_data=f"rate_cat_{cat_name}")])
        buttons.append([InlineKeyboardButton("🏆 الأعلى تقييماً", callback_data="top_rated")])
        buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data="support_back")])
        await query.edit_message_text(
            "<blockquote>🎙 تقييم المحطات\n\nاختر قسماً لتقييم محطاته:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("sched_toggle_"):
        parts = data.split("_")
        t = parts[2]
        action = parts[3]
        if action == "off":
            schedule_disabled.add(t)
            status = "❌ موقوف"
        else:
            schedule_disabled.discard(t)
            status = "✅ مفعّل"
        station_name = AUTO_SCHEDULE.get(t, {}).get("name", t)
        await query.answer(f"{station_name}: {status}")
        from pyrogram.types import InlineKeyboardMarkup
        await query.edit_message_reply_markup(InlineKeyboardMarkup(build_schedule_buttons()))

    elif data == "tarawih_toggle":
        tarawih_enabled = not tarawih_enabled
        status = "✅ مفعّل" if tarawih_enabled else "❌ موقوف"
        await query.answer(f"🕌 التراويح: {status}")
        from pyrogram.types import InlineKeyboardMarkup
        await query.edit_message_reply_markup(InlineKeyboardMarkup(build_schedule_buttons()))

    elif data.startswith("manage_admin_"):
        if int(user_id) != OWNER_ID:
            await query.answer("❌ للمطور فقط", show_alert=True)
            return
        target_id = int(data[13:])
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        try:
            u = await app.get_users(target_id)
            name = u.first_name
        except Exception as e:
            logger.error(f"get_users error for admin {target_id}: {e}")
            name = str(target_id)
        perms = ADMIN_PERMISSIONS.get(target_id, {})
        buttons = []
        for perm_key, perm_name in ALL_PERMISSIONS.items():
            is_on = perms.get(perm_key, False)
            buttons.append([
                InlineKeyboardButton(perm_name, callback_data="noop"),
                InlineKeyboardButton("✅ تفعيل" if is_on else "🔘 تفعيل", callback_data=f"perm_on_{target_id}_{perm_key}"),
                InlineKeyboardButton("🔘 إيقاف" if is_on else "❌ إيقاف", callback_data=f"perm_off_{target_id}_{perm_key}"),
            ])
        buttons.append([InlineKeyboardButton("✅ تفعيل الكل", callback_data=f"perm_all_on_{target_id}"),
                        InlineKeyboardButton("❌ إيقاف الكل", callback_data=f"perm_all_off_{target_id}")])
        await query.edit_message_text(
            f"<blockquote>👑 صلاحيات: {name}\n\nاختر الصلاحية وفعّل أو أوقف:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("perm_on_") or data.startswith("perm_off_"):
        if int(user_id) != OWNER_ID:
            await query.answer("❌ للمطور فقط", show_alert=True)
            return
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        parts = data.split("_")
        # perm_on_{target_id}_{perm_key} أو perm_off_{target_id}_{perm_key}
        action = parts[1]          # on أو off
        target_id = int(parts[2])
        perm_key = "_".join(parts[3:])
        new_val = (action == "on")
        if target_id not in ADMIN_PERMISSIONS:
            ADMIN_PERMISSIONS[target_id] = {}
        ADMIN_PERMISSIONS[target_id][perm_key] = new_val
        # إعادة رسم الشاشة
        try:
            u = await app.get_users(target_id)
            name = u.first_name
        except Exception as e:
            logger.error(f"get_users perm error: {e}")
            name = str(target_id)
        perms = ADMIN_PERMISSIONS.get(target_id, {})
        buttons = []
        for pk, pn in ALL_PERMISSIONS.items():
            is_on = perms.get(pk, False)
            buttons.append([
                InlineKeyboardButton(("✅ " if is_on else "❌ ") + pn, callback_data="noop"),
                InlineKeyboardButton("تفعيل" , callback_data=f"perm_on_{target_id}_{pk}"),
                InlineKeyboardButton("إيقاف", callback_data=f"perm_off_{target_id}_{pk}"),
            ])
        buttons.append([InlineKeyboardButton("✅ تفعيل الكل", callback_data=f"perm_all_on_{target_id}"),
                        InlineKeyboardButton("❌ إيقاف الكل", callback_data=f"perm_all_off_{target_id}")])
        status = "✅ مفعّل" if new_val else "❌ موقوف"
        await query.answer(f"{ALL_PERMISSIONS.get(perm_key, perm_key)}: {status}")
        await query.edit_message_reply_markup(InlineKeyboardMarkup(buttons))

    elif data.startswith("perm_all_on_") or data.startswith("perm_all_off_"):
        if int(user_id) != OWNER_ID:
            await query.answer("❌ للمطور فقط", show_alert=True)
            return
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        action = "on" if "all_on" in data else "off"
        target_id = int(data.split("_")[-1])
        new_val = (action == "on")
        ADMIN_PERMISSIONS[target_id] = {pk: new_val for pk in ALL_PERMISSIONS}
        try:
            u = await app.get_users(target_id)
            name = u.first_name
        except Exception as e:
            logger.error(f"get_users perm_all error: {e}")
            name = str(target_id)
        perms = ADMIN_PERMISSIONS[target_id]
        buttons = []
        for pk, pn in ALL_PERMISSIONS.items():
            is_on = perms.get(pk, False)
            buttons.append([
                InlineKeyboardButton(("✅ " if is_on else "❌ ") + pn, callback_data="noop"),
                InlineKeyboardButton("تفعيل" , callback_data=f"perm_on_{target_id}_{pk}"),
                InlineKeyboardButton("إيقاف", callback_data=f"perm_off_{target_id}_{pk}"),
            ])
        buttons.append([InlineKeyboardButton("✅ تفعيل الكل", callback_data=f"perm_all_on_{target_id}"),
                        InlineKeyboardButton("❌ إيقاف الكل", callback_data=f"perm_all_off_{target_id}")])
        await query.answer("✅ تم تفعيل الكل" if new_val else "❌ تم إيقاف الكل")
        await query.edit_message_reply_markup(InlineKeyboardMarkup(buttons))

    elif data == "noop":
        await query.answer()

    elif data.startswith("demote_"):
        if int(user_id) != OWNER_ID:
            await query.answer("❌ للمطور فقط", show_alert=True)
            return
        target_id = int(data[7:])
        if target_id == OWNER_ID:
            await query.answer("❌ لا يمكن إزالة المطور", show_alert=True)
            return
        if target_id in ADMIN_ID:
            ADMIN_ID.remove(target_id)
            try:
                u = await app.get_users(target_id)
                name = u.first_name
                await app.send_message(
                    target_id,
                    "<blockquote>⚠️ تم إزالة صلاحيات الأدمن منك في بوت راديو القرآن الكريم</blockquote>"
                )
            except Exception as e:
                logger.error(f"demote notify error: {e}")
                name = str(target_id)
            await query.edit_message_text(
                f"<blockquote>✅ تم إزالة {name} من الأدمنز</blockquote>"
            )
        else:
            await query.answer("❌ هذا المستخدم ليس أدمناً", show_alert=True)

    elif data == "support_back":
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await query.edit_message_text(
            "<blockquote>🛠 مركز الدعم الفني\n\nاختر ما تحتاجه:</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 تواصل مع الدعم الفني", callback_data="support_contact")],
                [InlineKeyboardButton("⭐ قسم التقييمات", callback_data="support_ratings")],
            ])
        )

    elif data == "support_contact":
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await query.edit_message_text(
            "<blockquote>💬 تواصل مع الدعم الفني\n\nاختر ما تحتاجه:</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⚠️ الإبلاغ عن مشكلة", callback_data="support_report")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="support_back")],
            ])
        )

    elif data == "support_ratings":
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await query.edit_message_text(
            "<blockquote>⭐ قسم التقييمات\n\nاختر نوع التقييم:</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ تقييم البوت", callback_data="support_rate_bot")],
                [InlineKeyboardButton("🎙 تقييم المحطات", callback_data="support_rate_stations")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="support_back")],
            ])
        )

    elif data == "ratings_back":
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await query.edit_message_text(
            "<blockquote>⭐ قسم التقييمات\n\nاختر نوع التقييم:</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ تقييم البوت", callback_data="support_rate_bot")],
                [InlineKeyboardButton("🎙 تقييم المحطات", callback_data="support_rate_stations")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="support_back")],
            ])
        )

    elif data == "top_rated":
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        rated = []
        for sid, info in ST_TIMO.items():
            r = get_station_rating(sid)
            count = station_ratings.get(sid, {}).get("count", 0)
            if count > 0:
                rated.append((sid, info["name"], r, count))
        rated.sort(key=lambda x: x[2], reverse=True)
        if not rated:
            await query.answer("لا توجد تقييمات بعد!", show_alert=True)
            return
        text = "<blockquote>🏆 الأعلى تقييماً:\n\n"
        for i, (sid, name, r, count) in enumerate(rated[:10], 1):
            stars = get_rating_stars(r)
            text += f"{i}. {name}\n{stars} ({r}/5) — {count} تقييم\n\n"
        text += "</blockquote>"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="rating_back")]
        ]))

    elif data == "rating_back":
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        for cat_name in ST_CATEGORIES:
            buttons.append([InlineKeyboardButton(cat_name, callback_data=f"rate_cat_{cat_name}")])
        buttons.append([InlineKeyboardButton("🏆 الأعلى تقييماً", callback_data="top_rated")])
        await query.edit_message_text(
            "<blockquote>⭐ نظام تقييم المحطات\n\naختر قسماً لتقييم محطاته</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # اختيار قسم للتقييم
    elif data.startswith("rate_cat_"):
        cat_name = data[9:]
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        if cat_name not in ST_CATEGORIES:
            await query.answer("قسم غير موجود", show_alert=True)
            return
        station_ids = ST_CATEGORIES[cat_name]
        buttons = []
        for sid in station_ids:
            name = ST_TIMO[sid]["name"].replace("إذاعة ", "").replace("اذاعة ", "").replace("قناة ", "").strip()
            r = get_station_rating(sid)
            stars = get_rating_stars(r) if r > 0 else "☆☆☆☆☆"
            buttons.append([InlineKeyboardButton(f"{name}  {stars}", callback_data=f"rate_station_{sid}")])
        buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data="rating_back")])
        await query.edit_message_text(
            f"<blockquote>{cat_name}\nاختر محطة لتقييمها:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # اختيار محطة للتقييم — عرض النجوم
    elif data.startswith("rate_station_"):
        sid = data[13:]
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        if sid not in ST_TIMO:
            await query.answer("محطة غير موجودة", show_alert=True)
            return
        name = ST_TIMO[sid]["name"]
        current = get_station_rating(sid)
        count = station_ratings.get(sid, {}).get("count", 0)
        user_prev = station_ratings.get(sid, {}).get("users", {}).get(str(query.from_user.id), 0)
        text = (
            f"<blockquote>⭐ تقييم: {name}\n\n"
            f"التقييم الحالي: {get_rating_stars(current)} ({current}/5)\n"
            f"عدد المقيّمين: {count}\n"
            + (f"تقييمك السابق: {'⭐' * user_prev}\n" if user_prev else "") +
            "\nاختر تقييمك:</blockquote>"
        )
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⭐1", callback_data=f"give_rate_{sid}_1"),
             InlineKeyboardButton("⭐2", callback_data=f"give_rate_{sid}_2"),
             InlineKeyboardButton("⭐3", callback_data=f"give_rate_{sid}_3"),
             InlineKeyboardButton("⭐4", callback_data=f"give_rate_{sid}_4"),
             InlineKeyboardButton("⭐5", callback_data=f"give_rate_{sid}_5")],
            [InlineKeyboardButton("🔙 رجوع", callback_data=f"rate_cat_" + next((c for c, ids in ST_CATEGORIES.items() if sid in ids), ""))]
        ]))

    # إعطاء تقييم — بعد النجوم يطلب نص إجباري
    elif data.startswith("give_rate_"):
        parts = data.split("_")
        sid = parts[2]
        stars = int(parts[3])
        uid_str = str(query.from_user.id)
        # حفظ النجوم في user_state وانتظار النص
        user_state[user_id] = {
            "step": "awaiting_station_review",
            "rating_station_id": sid,
            "station_stars": stars
        }
        # تسجيل التقييم العددي فوراً
        if sid not in station_ratings:
            station_ratings[sid] = {"total": 0, "count": 0, "users": {}}
        prev = station_ratings[sid]["users"].get(uid_str, 0)
        if prev:
            station_ratings[sid]["total"] -= prev
            station_ratings[sid]["count"] -= 1
        station_ratings[sid]["total"] += stars
        station_ratings[sid]["count"] += 1
        station_ratings[sid]["users"][uid_str] = stars
        name = ST_TIMO[sid]["name"]
        await query.answer(f"✅ تم تسجيل تقييمك: {'⭐' * stars}", show_alert=True)
        await query.edit_message_text(
            f"<blockquote>⭐ تقييمك: {'⭐' * stars}\n\n"
            f"📻 {name}\n\n"
            "✍️ اكتب تعليقك على المحطة (إجباري)\n"
            "أرسل نصك الآن 👇</blockquote>"
        )
    elif data.startswith("broadcast_"):
        channel_id = data[10:]
        selected_station = user_state.get(user_id, {}).get("station_url")

        if not selected_station:
            await query.answer("❌ اختر الإذاعة أولاً", show_alert=True)
            return

        if user_id not in user_data or channel_id not in user_data[user_id].get("channels", {}):
            await query.answer("❌ القناة غير موجودة", show_alert=True)
            return

        channel_info = user_data[user_id]["channels"][channel_id]

        # إيقاف البث القديم لو موجود
        if "process" in channel_info:
            try:
                pid = channel_info["process"]
                if is_ffmpeg_running(pid):
                    subprocess.run(["kill", "-9", str(pid)], timeout=5, check=True)
            except Exception as e:
                logger.error(f"Error stopping process: {e}")

        # بدء البث
        ffmpeg_cmd = [
            "ffmpeg", "-re", "-i", selected_station,
            "-vn",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
            "-f", "flv", channel_info["rtmps_url"]
        ]
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        user_data[user_id]["channels"][channel_id]["process"] = process.pid
        save_data()

        await send_broadcast_notification(client, channel_info['chat_id'], selected_station)

        # إشعار الأدمن
        station_name_notify = next((v["name"] for v in ST_TIMO.values() if v["url"] == selected_station), "غير معروف")
        if not is_admin(int(user_id)) and broadcast_notify_enabled:
            try:
                await app.send_message(
                    ADMIN_ID[0],
                    "<blockquote>📢 مستخدم بدأ البث\n"
                    "👤 المستخدم: " + str(user_id) + "\n"
                    "📡 القناة: " + channel_info['title'] + "\n"
                    "🎙 المحطة: " + station_name_notify + "</blockquote>"
                )
            except Exception as e:
                logger.error(f"broadcast notify admin error: {e}")
        broadcast_stats[channel_id] = {
            "station": station_name_notify,
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user_id
        }
        broadcast_start_times[channel_id] = time.time()
        save_broadcast_state()
        _station_display = station_name_notify

        if user_id in user_state:
            user_state.pop(user_id, None)

        await query.edit_message_text(
            f"<blockquote>✅ بدأ البث بنجاح!\n"
            f"📡 القناة: {channel_info['title']}\n"
            f"🎙 المحطة: {_station_display}</blockquote>"
        )
        await query.answer("✅ بدأ البث!")


check_cooldown = {}  # حماية /check من الرشق {user_id: last_time}

@app.on_message(filters.command("check") & filters.private)
async def check_command(client, message):
    try:
        user_id = message.from_user.id
        now = time.time()

        # rate limit — مرة كل 10 ثواني
        last = check_cooldown.get(user_id, 0)
        if now - last < 10:
            remaining = int(10 - (now - last))
            await message.reply_text(
                f"<blockquote>⏳ انتظر {remaining} ثانية قبل إعادة المحاولة</blockquote>"
            )
            return
        check_cooldown[user_id] = now

        unsubscribed = await check_subscription(client, user_id)
        if unsubscribed:
            await send_subscription_message(message, unsubscribed)
        else:
            await message.reply_text(
                "✅ تم التحقق! يمكنك الآن استخدام البوت.",
                reply_markup=user_keyboard() if not is_admin(user_id) else admin_keyboard()
            )
    except Exception as e:
        logger.error(f"Check command error: {e}")

@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    try:
        user_id = str(message.from_user.id)
        is_new_user = user_id not in user_data

        # التحقق من الحظر أولاً قبل إضافة المستخدم
        if int(user_id) in banned_users:
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            await message.reply_text(
                "<blockquote>🚫 تم حظرك من استخدام هذا البوت\n\n"
                "لفك الحظر تواصل مع المطور:</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💬 تواصل مع الأدمن", url="https://t.me/AboNuwaf")],
                    [InlineKeyboardButton("🤖 تواصل عبر البوت", url="https://t.me/AboNuwaf1_bot")]
                ])
            )
            return

        # التحقق من الحد الأقصى للمستخدمين (قبل إضافة المستخدم الجديد)
        if is_new_user and not is_admin(message.from_user.id) and max_users_enabled:
            if len(user_data) >= max_users_limit:
                await message.reply_text(
                    "<blockquote>⚠️ عذراً، البوت وصل للحد الأقصى من المستخدمين.\nيرجى التواصل مع الأدمن.</blockquote>"
                )
                return

        # التحقق من الاشتراك
        if not is_admin(message.from_user.id):
            unsubscribed = await check_subscription(client, message.from_user.id)
            if unsubscribed:
                await send_subscription_message(message, unsubscribed)
                return

        # التحقق من وضع الصيانة
        if maintenance_mode and not is_admin(message.from_user.id):
            try:
                await message.reply_photo(
                    photo=MAINTENANCE_IMAGE,
                    caption=(
                        "❍─── 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝚀𝚞𝚛𝚊𝚗 𝙰𝚝𝚑𝚎𝚎𝚛 𝙱𝙾𝚃 ───❍\n\n"
                        "⚠️ عذراً عزيزي المستخدم..\n"
                        "البوت الآن في وضع الصيانة لتحديث الخدمات.\n\n"
                        "⏳ يرجى المحاولة مرة أخرى لاحقاً.\n"
                        "────────────────────"
                    )
                )
            except Exception:
                await message.reply_text(
                    "❍─── 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝚀𝚞𝚛𝚊𝚗 𝙰𝚝𝚑𝚎𝚎𝚛 𝙱𝙾𝚃 ───❍\n\n"
                    "⚠️ عذراً عزيزي المستخدم..\n"
                    "البوت الآن في وضع الصيانة لتحديث الخدمات.\n\n"
                    "⏳ يرجى المحاولة مرة أخرى لاحقاً.\n"
                    "────────────────────"
                )
            return

        # إضافة المستخدم الجديد بعد اجتياز كل الفحوصات
        if is_new_user:
            user_data[user_id] = {
                "channels": {},
                "temp_station": None,
                "join_date": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            save_data()

        if is_admin(message.from_user.id):
            keyboard = admin_keyboard()
        else:
            keyboard = user_keyboard()

        if is_admin(message.from_user.id):
            caption = (
                "<blockquote>👑 أهلاً بك يا مديرنا الكريم\n"
                "• لوحة تحكم بوت راديو القرآن الكريم\n"
                "• المطور: 𝑨𝒃𝒐 𝑵𝒖𝒘𝒂𝒇</blockquote>"
            )
        else:
            caption = (
                "<blockquote>• مرحبا بك " + message.from_user.first_name + "\n"
                "• في بوت راديو القرآن الكريم\n"
                "• المقدم من المطور 𝑨𝒃𝒐 𝑵𝒖𝒘𝒂𝒇</blockquote>"
            )
        await message.reply_photo(
            photo=IMAGE_TIMO,
            caption=caption,
            reply_markup=keyboard
        )

        if is_new_user:
            await notify_new_user(
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name
            )
            # شرح الأنظمة للمستخدم الجديد
            await asyncio.sleep(1)
            await message.reply_text(
                "<blockquote>📖 دليل استخدام البوت\n\n"
                "🎙 بدء البث\n"
                "اختر قسم الإذاعة ثم المحطة التي تريدها وابدأ البث على قناتك مباشرةً\n\n"
                "⭐ تقييم المحطات\n"
                "قيّم أي محطة من 1 إلى 5 نجوم وساعد المستخدمين الآخرين في اختيار الأفضل\n\n"
                "🌙 الوضع الليلي\n"
                "من 11 مساءً حتى 5 صباحاً يتحول البث تلقائياً إلى محطات هادية مثل آيات السكينة والأذكار\n\n"
                "🔴 الإبلاغ عن مشكلة\n"
                "واجهت مشكلة؟ اضغط الزرار وأرسل وصفاً أو صورة وسيصلنا بلاغك فوراً\n\n"
                "بالتوفيق 🤍</blockquote>"
            )
            
    except Exception as e:
        logger.error(f"Error in /start: {e}")
        await message.reply_text("حدث خطأ، الرجاء المحاولة لاحقًا")


@app.on_message(filters.text & filters.private)
async def handle_text(client, message):
    global max_users_enabled, max_users_limit, daily_report_enabled, night_mode_enabled
    global broadcast_notify_enabled, night_mode_start, night_mode_end, about_bot_visible
    global auto_schedule_enabled, maintenance_mode
    user_id = str(message.from_user.id)
    text = message.text.strip()
    try:
        # التحقق من الحظر
        if int(user_id) in banned_users:
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            await message.reply_text(
                "<blockquote>🚫 تم حظرك من استخدام هذا البوت\n\n"
                "لفك الحظر تواصل مع المطور:</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💬 تواصل مع الأدمن", url="https://t.me/AboNuwaf")],
                    [InlineKeyboardButton("🤖 تواصل عبر البوت", url="https://t.me/AboNuwaf1_bot")]
                ])
            )
            return

        # التحقق من الاشتراك لكل رسالة
        if not is_admin(int(user_id)):
            unsubscribed = await check_subscription(client, int(user_id))
            if unsubscribed:
                await send_subscription_message(message, unsubscribed)
                return

        # التحقق من وضع الصيانة
        if maintenance_mode and not is_admin(int(user_id)):
            try:
                await message.reply_photo(
                    photo=MAINTENANCE_IMAGE,
                    caption=(
                        "❍─── 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝚀𝚞𝚛𝚊𝚗 𝙰𝚝𝚑𝚎𝚎𝚛 𝙱𝙾𝚃 ───❍\n\n"
                        "⚠️ عذراً عزيزي المستخدم..\n"
                        "البوت الآن في وضع الصيانة لتحديث الخدمات.\n\n"
                        "⏳ يرجى المحاولة مرة أخرى لاحقاً.\n"
                        "────────────────────"
                    )
                )
            except Exception:
                await message.reply_text(
                    "❍─── 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝚀𝚞𝚛𝚊𝚗 𝙰𝚝𝚑𝚎𝚎𝚛 𝙱𝙾𝚃 ───❍\n\n"
                    "⚠️ عذراً عزيزي المستخدم..\n"
                    "البوت الآن في وضع الصيانة لتحديث الخدمات.\n\n"
                    "⏳ يرجى المحاولة مرة أخرى لاحقاً.\n"
                    "────────────────────"
                )
            return

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
            user_state[user_id] = {"step": "awaiting_station_for_broadcast"}
            await show_station_categories(message)
                      
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
                        user_data[user_id]["channels"][channel_id].pop("process", None)
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
            for num, (channel_id, info) in enumerate(list(channels.items()), 1):
                status = "🟢 نشط" if "process" in info else "🔴 متوقف"
                response += f"<blockquote> {num}. {info['title']} - {status}</blockquote>\n"            
            await message.reply_text(response)     
        elif text == "حذف قناة":
            if user_id not in user_data or not user_data[user_id].get("channels"):
                await message.reply_text("<blockquote> • لا توجد قنوات مضافة للحذف!</blockquote>")
                return     
            channels = user_data[user_id]["channels"]
            channels_list = "\n".join([f"<blockquote> {num+1}. {info['title']}</blockquote>" for num, (_, info) in enumerate(list(channels.items()))])    
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
                user_state.pop(user_id, None)
        elif text == "⚙️ الجدول التلقائي":
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            if is_admin(int(user_id)):
                is_active = auto_schedule_enabled
            else:
                is_active = user_schedule_enabled.get(user_id, False)
            status = "✅ مفعل" if is_active else "❌ متوقف"
            buttons = build_schedule_buttons()
            await message.reply_text(
                f"<blockquote>⚙️ الجدول التلقائي\nالحالة: {status}\n\n"
                "✅ = مفعّل  |  ❌ = موقوف\n\n"
                "✏️ تعديل موعد — لتغيير وقت إذاعة\n"
                "🎙 تغيير محطة — لتغيير محطة وقت معين</blockquote>",
                reply_markup=InlineKeyboardMarkup(buttons) if buttons else schedule_keyboard()
            )
            await message.reply_text(
                "<blockquote>اضغط تشغيل أو إيقاف لكل محطة 👆</blockquote>",
                reply_markup=schedule_keyboard()
            )

        elif text == "▶️ تشغيل تلقائي":
            if is_admin(int(user_id)):
                if not has_perm(int(user_id), "schedule"):
                    await message.reply_text("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
                    return
                auto_schedule_enabled = True
            else:
                user_schedule_enabled[user_id] = True
            await message.reply_text(
                "<blockquote>✅ تم تفعيل الجدول التلقائي على قنواتك</blockquote>",
                reply_markup=schedule_keyboard()
            )

        elif text == "⏹ إيقاف تلقائي":
            if is_admin(int(user_id)):
                if not has_perm(int(user_id), "schedule"):
                    await message.reply_text("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
                    return
                auto_schedule_enabled = False
            else:
                user_schedule_enabled[user_id] = False
            await message.reply_text(
                "<blockquote>❌ تم إيقاف الجدول التلقائي على قنواتك</blockquote>",
                reply_markup=schedule_keyboard()
            )

        elif text == "✏️ تعديل موعد":
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            buttons = []
            for i, (t, s) in enumerate(AUTO_SCHEDULE.items(), 1):
                name = s['name'].replace("إذاعة ", "").replace("اذاعة ", "").strip()
                buttons.append([InlineKeyboardButton(f"{i}. {t} — {name}", callback_data=f"edit_time_{t}")])
            await message.reply_text(
                "<blockquote>✏️ اختر الوقت الذي تريد تعديله:</blockquote>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        elif text == "🎙 تغيير محطة":
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            buttons = []
            for i, (t, s) in enumerate(AUTO_SCHEDULE.items(), 1):
                name = s['name'].replace("إذاعة ", "").replace("اذاعة ", "").strip()
                buttons.append([InlineKeyboardButton(f"{i}. {t} — {name}", callback_data=f"edit_station_{t}")])
            await message.reply_text(
                "<blockquote>🎙 اختر الوقت الذي تريد تغيير محطته:</blockquote>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        elif user_state.get(user_id, {}).get("step") == "awaiting_new_time":
            old_time = user_state[user_id].get("old_time")
            # التحقق من صيغة الوقت HH:MM
            import re
            if not re.match(r"^\d{2}:\d{2}$", text):
                await message.reply_text("<blockquote>❌ صيغة غير صحيحة\nأرسل الوقت بهذا الشكل: 07:30</blockquote>")
                return
            if old_time and old_time in AUTO_SCHEDULE:
                station_data = AUTO_SCHEDULE.pop(old_time)
                AUTO_SCHEDULE[text] = station_data
                # إعادة ترتيب حسب الوقت
                AUTO_SCHEDULE.update(dict(sorted(AUTO_SCHEDULE.items())))
                user_state.pop(user_id, None)
                await message.reply_text(
                    f"<blockquote>✅ تم تغيير الموعد\nمن: {old_time}\nإلى: {text}</blockquote>",
                    reply_markup=schedule_keyboard()
                )
            else:
                await message.reply_text("<blockquote>❌ حدث خطأ، حاول مجدداً</blockquote>")
                user_state.pop(user_id, None)

        elif user_state.get(user_id, {}).get("step") == "awaiting_new_station_for_schedule":
            target_time = user_state[user_id].get("target_time")
            # البحث عن المحطة بالرقم أو الاسم
            sid = None
            try:
                idx = int(text) - 1
                keys = list(ST_TIMO.keys())
                if 0 <= idx < len(keys):
                    sid = keys[idx]
            except ValueError:
                for k, v in ST_TIMO.items():
                    if text in v["name"]:
                        sid = k
                        break
            if sid and target_time and target_time in AUTO_SCHEDULE:
                AUTO_SCHEDULE[target_time] = {"name": ST_TIMO[sid]["name"], "url": ST_TIMO[sid]["url"]}
                user_state.pop(user_id, None)
                await message.reply_text(
                    f"<blockquote>✅ تم تغيير محطة {target_time}\nإلى: {ST_TIMO[sid]['name']}</blockquote>",
                    reply_markup=schedule_keyboard()
                )
            else:
                await message.reply_text("<blockquote>❌ رقم أو اسم محطة غير صحيح، حاول مجدداً</blockquote>")
        elif text == "📊 إحصائيات البث":
            if not is_admin(int(user_id)) or not has_perm(int(user_id), "stats"):
                await message.reply_text("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
                return
            if not broadcast_stats:
                await message.reply_text("<blockquote>📊 لا توجد بثوث نشطة حالياً</blockquote>")
                return
            stats_text = "<blockquote>📊 إحصائيات البث:\n\n"
            for ch_id, stat in broadcast_stats.items():
                duration = get_broadcast_duration(ch_id)
                stats_text += "📡 القناة: " + str(ch_id) + "\n"
                stats_text += "🎙 المحطة: " + stat.get("station", "غير معروف") + "\n"
                stats_text += "⏰ بدأ: " + stat.get("start_time", "غير معروف") + "\n"
                stats_text += "⏱ المدة: " + duration + "\n"
                stats_text += "▬▬▬▬▬▬▬▬▬▬\n"
            stats_text += "</blockquote>"
            await message.reply_text(stats_text)

        elif text == "👑 إدارة الأدمنز":
            if int(user_id) != OWNER_ID:
                await message.reply_text("<blockquote>❌ هذا الأمر للمطور فقط</blockquote>")
                return
            admins_list = [aid for aid in ADMIN_ID if aid != OWNER_ID]
            if not admins_list:
                await message.reply_text("<blockquote>❌ لا يوجد أدمنز مضافون حالياً\nاستخدم ➕ رفع أدمن أولاً</blockquote>")
                return
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            buttons = []
            for aid in admins_list:
                try:
                    u = await app.get_users(aid)
                    label = f"👤 {u.first_name}"
                except Exception as e:
                    logger.error(f"get_users error for admin {aid}: {e}")
                    label = f"👤 {aid}"
                buttons.append([InlineKeyboardButton(label, callback_data=f"manage_admin_{aid}")])
            await message.reply_text(
                "<blockquote>👑 إدارة الأدمنز\n\nاختر أدمناً لتعديل صلاحياته:</blockquote>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        elif text == "➕ رفع أدمن":
            if int(user_id) != OWNER_ID:
                await message.reply_text("<blockquote>❌ هذا الأمر للمطور فقط</blockquote>")
                return
            user_state[user_id] = {"step": "awaiting_promote_id"}
            await message.reply_text(
                "<blockquote>➕ رفع أدمن\n\nأرسل ID المستخدم الذي تريد رفعه أدمناً</blockquote>",
                reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
            )

        elif text == "➖ إزالة أدمن":
            if int(user_id) != OWNER_ID:
                await message.reply_text("<blockquote>❌ هذا الأمر للمطور فقط</blockquote>")
                return
            # عرض قائمة الأدمنز الحاليين
            admins_list = [aid for aid in ADMIN_ID if aid != OWNER_ID]
            if not admins_list:
                await message.reply_text("<blockquote>❌ لا يوجد أدمنز مضافون حالياً</blockquote>")
                return
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            buttons = []
            for aid in admins_list:
                try:
                    u = await app.get_users(aid)
                    label = f"{u.first_name} ({aid})"
                except Exception as e:
                    logger.error(f"get_users error for admin {aid}: {e}")
                    label = str(aid)
                buttons.append([InlineKeyboardButton(f"➖ {label}", callback_data=f"demote_{aid}")])
            await message.reply_text(
                "<blockquote>➖ اختر الأدمن الذي تريد إزالته:</blockquote>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        elif user_state.get(user_id, {}).get("step") == "awaiting_promote_id":
            if int(user_id) != OWNER_ID:
                return
            try:
                target_id = int(text)
                if target_id in ADMIN_ID:
                    await message.reply_text(
                        "<blockquote>⚠️ هذا المستخدم أدمن بالفعل</blockquote>",
                        reply_markup=admin_keyboard()
                    )
                else:
                    ADMIN_ID.append(target_id)
                    user_state.pop(user_id, None)
                    try:
                        u = await app.get_users(target_id)
                        name = u.first_name
                        # إشعار الأدمن الجديد
                        await app.send_message(
                            target_id,
                            "<blockquote>👑 تهانينا!\n\nتم رفعك أدمناً في بوت راديو القرآن الكريم\nبإمكانك الآن الوصول للوحة التحكم الكاملة</blockquote>"
                        )
                    except Exception as e:
                        logger.error(f"promote admin notify error: {e}")
                        name = str(target_id)
                    await message.reply_text(
                        f"<blockquote>✅ تم رفع {name} أدمناً بنجاح 👑</blockquote>",
                        reply_markup=admin_keyboard()
                    )
            except ValueError:
                await message.reply_text("<blockquote>❌ أدخل ID رقمي صحيح</blockquote>")

        elif text == "🚫 حظر مستخدم":
            if not is_admin(int(user_id)) or not has_perm(int(user_id), "ban"):
                await message.reply_text("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
                return
            user_state[user_id] = {"step": "awaiting_ban_id"}
            await message.reply_text(
                "<blockquote>🚫 أرسل ID المستخدم الذي تريد حظره</blockquote>",
                reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
            )

        elif text == "✅ رفع الحظر":
            if not is_admin(int(user_id)) or not has_perm(int(user_id), "ban"):
                await message.reply_text("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
                return
            if not banned_users:
                await message.reply_text("<blockquote>✅ لا يوجد مستخدمون محظورون حالياً</blockquote>")
                return
            user_state[user_id] = {"step": "awaiting_unban_id"}
            banned_list = "\n".join([f"• {uid}" for uid in banned_users])
            await message.reply_text(
                "<blockquote>🚫 المحظورون:\n" + banned_list + "\n\nأرسل ID المستخدم لرفع الحظر عنه</blockquote>",
                reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
            )

        elif user_state.get(user_id, {}).get("step") == "awaiting_ban_id":
            try:
                target_id = int(text.strip())
                banned_users.add(target_id)
                user_state.pop(user_id, None)
                await message.reply_text(
                    f"<blockquote>🚫 تم حظر المستخدم {target_id} بنجاح</blockquote>",
                    reply_markup=admin_keyboard()
                )
                try:
                    await app.send_message(target_id, "<blockquote>🚫 تم حظرك من استخدام هذا البوت.</blockquote>")
                except Exception as e:
                    logger.error(f"ban notify error: {e}")
            except ValueError:
                await message.reply_text("<blockquote>❌ يرجى إدخال ID رقمي صحيح</blockquote>")

        elif user_state.get(user_id, {}).get("step") == "awaiting_unban_id":
            try:
                target_id = int(text.strip())
                if target_id in banned_users:
                    banned_users.discard(target_id)
                    user_state.pop(user_id, None)
                    await message.reply_text(
                        f"<blockquote>✅ تم رفع الحظر عن المستخدم {target_id}</blockquote>",
                        reply_markup=admin_keyboard()
                    )
                    try:
                        await app.send_message(target_id, "<blockquote>✅ تم رفع الحظر عنك، يمكنك استخدام البوت الآن.</blockquote>")
                    except Exception as e:
                        logger.error(f"unban notify error: {e}")
                else:
                    await message.reply_text("<blockquote>❌ هذا المستخدم غير محظور</blockquote>")
                    user_state.pop(user_id, None)
            except ValueError:
                await message.reply_text("<blockquote>❌ يرجى إدخال ID رقمي صحيح</blockquote>")

        elif text == "ℹ️ نبذة عن البوت":
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            # حساب الإحصائيات
            total_users = len(user_data)
            total_channels = sum(len(u.get("channels", {})) for u in list(user_data.values()))
            total_stations = len(ST_TIMO)
            caption = (
                "<blockquote>ℹ️ نبذة عن البوت\n\n"
                "🤖 الاسم: بوت راديو القرآن الكريم\n"
                "📌 الإصدار: 2.0\n"
                "👨‍💻 المطور: 𝑨𝒃𝒐 𝑵𝒖𝒘𝒂𝒇\n\n"
                "📊 الإحصائيات:\n"
                f"👥 المستخدمين: {total_users}\n"
                f"📢 القنوات: {total_channels}\n"
                f"🎙 المحطات المتاحة: {total_stations}\n\n"
                "🔗 تواصل مع المطور: @AboNuwaf</blockquote>"
            )
            try:
                await message.reply_photo(
                    photo=ABOUT_BOT_IMAGE,
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("💬 تواصل مع الأدمن", url="https://t.me/AboNuwaf")],
                        [InlineKeyboardButton("🤖 تواصل عبر البوت", url="https://t.me/AboNuwaf1_bot")]
                    ])
                )
            except Exception as e:
                logger.error(f"About bot error: {e}")
                await message.reply_text(caption)

        elif text.startswith("ℹ️ نبذة عن البوت:"):
            if not is_admin(int(user_id)):
                return
            global about_bot_visible
            about_bot_visible = not about_bot_visible
            status = "ظاهر للمستخدمين 🟢" if about_bot_visible else "مخفي عن المستخدمين 🔴"
            await message.reply_text(
                f"<blockquote>ℹ️ نبذة عن البوت الآن: {status}</blockquote>",
                reply_markup=admin_keyboard()
            )

        elif text == "📞 تواصل مع الأدمن":
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            await message.reply_text(
                "<blockquote>📞 تواصل مع الأدمن\n\nاختر طريقة التواصل:</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💬 تواصل مع الأدمن", url="https://t.me/AboNuwaf")],
                    [InlineKeyboardButton("🤖 تواصل عبر البوت", url="https://t.me/AboNuwaf1_bot")]
                ])
            )

        elif text.startswith("📋 التقرير اليومي"):
            if not is_admin(int(user_id)):
                return
            global daily_report_enabled
            daily_report_enabled = not daily_report_enabled
            status = "مفعّل 🟢" if daily_report_enabled else "موقوف 🔴"
            await message.reply_text(
                "<blockquote>📋 التقرير اليومي الآن: " + status + "\n"
                + ("✅ سيصلك تقرير كل يوم الساعة 8 صباحاً" if daily_report_enabled else "❌ لن يصلك أي تقرير") + "</blockquote>",
                reply_markup=admin_keyboard()
            )

        elif text.startswith("🌙 الوضع الليلي"):
            if not is_admin(int(user_id)):
                return
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            status = "مفعّل 🟢" if night_mode_enabled else "مقفول 🔴"
            await message.reply_text(
                "<blockquote>🌙 الوضع الليلي\n\n"
                "الحالة: " + status + "\n"
                "⏰ من: " + str(night_mode_start) + ":00 حتى " + str(night_mode_end) + ":00\n\n"
                "المحطات الليلية:\n"
                + "\n".join(["• " + ST_TIMO[s]["name"] for s in NIGHT_MODE_STATIONS]) + "</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "⏹ إيقاف الوضع الليلي" if night_mode_enabled else "▶️ تشغيل الوضع الليلي",
                        callback_data="night_toggle"
                    )],
                    [InlineKeyboardButton("🕐 تغيير وقت البداية", callback_data="night_set_start")],
                    [InlineKeyboardButton("🕔 تغيير وقت النهاية", callback_data="night_set_end")],
                ])
            )

        elif text.startswith("🔔 إشعار المحطات") or text.startswith("🔕 إشعار المحطات"):
            if not is_admin(int(user_id)):
                return
            global broadcast_notify_enabled
            broadcast_notify_enabled = not broadcast_notify_enabled
            status = "مفعّل 🟢" if broadcast_notify_enabled else "مقفول 🔴"
            await message.reply_text(
                "<blockquote>🔔 إشعار المحطات الآن: " + status + "\n"
                + ("✅ ستصلك إشعارات عند تشغيل أي محطة" if broadcast_notify_enabled
                   else "🔕 لن تصلك إشعارات عند تشغيل المحطات") + "</blockquote>",
                reply_markup=admin_keyboard()
            )

        elif text == "🛠 الدعم الفني":
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            await message.reply_text(
                "<blockquote>🛠 مركز الدعم الفني\n\nاختر ما تحتاجه:</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💬 تواصل مع الدعم الفني", callback_data="support_contact")],
                    [InlineKeyboardButton("⭐ قسم التقييمات", callback_data="support_ratings")],
                ])
            )

        elif user_state.get(user_id, {}).get("step") == "awaiting_bot_review":
            # نص تقييم البوت (إجباري)
            user_state[user_id]["bot_review_text"] = text
            user_state[user_id]["step"] = "awaiting_bot_review_photo"
            await message.reply_text(
                "<blockquote>✍️ تم استلام تعليقك\n\n"
                "📸 هل تودّ إرفاق صورة؟ (اختياري)</blockquote>",
                reply_markup=ReplyKeyboardMarkup([
                    ["📸 إرسال صورة"],
                    ["إرسال بدون صورة"],
                    ["❌ إلغاء"]
                ], resize_keyboard=True)
            )

        elif user_state.get(user_id, {}).get("step") == "awaiting_station_review":
            # نص تقييم المحطة (إجباري)
            user_state[user_id]["station_review_text"] = text
            user_state[user_id]["step"] = "awaiting_station_review_photo"
            await message.reply_text(
                "<blockquote>✍️ تم استلام تعليقك\n\n"
                "📸 هل تودّ إرفاق صورة؟ (اختياري)</blockquote>",
                reply_markup=ReplyKeyboardMarkup([
                    ["📸 إرسال صورة"],
                    ["إرسال بدون صورة"],
                    ["❌ إلغاء"]
                ], resize_keyboard=True)
            )

        elif text == "إرسال بدون صورة" and user_state.get(user_id, {}).get("step") == "awaiting_bot_review_photo":
            score = user_state[user_id].get("bot_rating_stars", 0)
            comment = user_state[user_id].get("bot_review_text", "بدون تعليق")
            rating_msg = (
                "<blockquote>⭐ تقييم جديد للبوت\n\n"
                "👤 المستخدم: " + user_id + "\n"
                "📛 الاسم: " + (message.from_user.first_name or "غير معروف") + "\n"
                "🔗 اليوزر: @" + (message.from_user.username or "بدون يوزر") + "\n"
                "⭐ التقييم: " + str(score) + "/10\n"
                "💬 التعليق: " + comment + "\n"
                "📸 بدون صورة</blockquote>"
            )
            try:
                await app.send_message(ADMIN_ID[0], rating_msg)
            except Exception as e:
                logger.error(f"Bot review send error: {e}")
            user_state.pop(user_id, None)
            await message.reply_text(
                "<blockquote>✅ تم إرسال تقييمك بنجاح 🌸</blockquote>",
                reply_markup=user_keyboard() if not is_admin(int(user_id)) else admin_keyboard()
            )

        elif text == "إرسال بدون صورة" and user_state.get(user_id, {}).get("step") == "awaiting_station_review_photo":
            sid = user_state[user_id].get("rating_station_id", "")
            stars = user_state[user_id].get("station_stars", 0)
            comment = user_state[user_id].get("station_review_text", "بدون تعليق")
            station_name = ST_TIMO.get(sid, {}).get("name", sid)
            rating_msg = (
                "<blockquote>🎙 تقييم جديد للمحطة\n\n"
                "👤 المستخدم: " + user_id + "\n"
                "📛 الاسم: " + (message.from_user.first_name or "غير معروف") + "\n"
                "🔗 اليوزر: @" + (message.from_user.username or "بدون يوزر") + "\n"
                "📻 المحطة: " + station_name + "\n"
                "⭐ التقييم: " + str(stars) + "/5\n"
                "💬 التعليق: " + comment + "\n"
                "📸 بدون صورة</blockquote>"
            )
            try:
                await app.send_message(ADMIN_ID[0], rating_msg)
            except Exception as e:
                logger.error(f"Station review send error: {e}")
            user_state.pop(user_id, None)
            await message.reply_text(
                "<blockquote>✅ تم إرسال تقييمك بنجاح 🌸</blockquote>",
                reply_markup=user_keyboard() if not is_admin(int(user_id)) else admin_keyboard()
            )

        elif text == "❌ إلغاء" and user_state.get(user_id, {}).get("step") in ("awaiting_bot_review", "awaiting_bot_review_photo", "awaiting_station_review", "awaiting_station_review_photo", "awaiting_report"):
            user_state.pop(user_id, None)
            await message.reply_text(
                "<blockquote>❌ تم إلغاء التقييم</blockquote>",
                reply_markup=user_keyboard() if not is_admin(int(user_id)) else admin_keyboard()
            )

        elif user_state.get(user_id, {}).get("step") == "awaiting_report":
            # حفظ النص وانتظار الصورة أو الإرسال المباشر
            user_state[user_id]["report_text"] = text
            await message.reply_text(
                "<blockquote>📨 تم استلام بلاغك بنجاح\n\n"
                "سيتم مراجعة مشكلتك والعمل على حلها في أقرب وقت ممكن\n"
                "نقدّر تواصلك ومساعدتك في تحسين البوت 🤍\n\n"
                "📸 هل تودّ إرفاق صورة لتوضيح المشكلة؟ (اختياري)\n"
                "الصورة تساعد المطور على الحل بشكل أسرع 🚀</blockquote>",
                reply_markup=ReplyKeyboardMarkup([["📸 إرسال صورة"], ["إرسال بدون صورة"], ["❌ إلغاء"]], resize_keyboard=True)
            )

        elif text == "📸 إرسال صورة" and user_state.get(user_id, {}).get("step") in ("awaiting_report", "awaiting_bot_review_photo", "awaiting_station_review_photo"):
            await message.reply_text(
                "<blockquote>📸 أرسل الصورة الآن</blockquote>",
                reply_markup=ReplyKeyboardMarkup([["❌ إلغاء"]], resize_keyboard=True)
            )

        elif text == "إرسال بدون صورة" and user_state.get(user_id, {}).get("step") == "awaiting_report":
            report_text_content = user_state[user_id].get("report_text", "بدون وصف")
            report_msg = (
                "<blockquote>⚠️ بلاغ جديد عن مشكلة\n\n"
                "👤 المستخدم: " + user_id + "\n"
                "📛 الاسم: " + (message.from_user.first_name or "غير معروف") + "\n"
                "🔗 اليوزر: @" + (message.from_user.username or "بدون يوزر") + "\n\n"
                "📝 المشكلة:\n" + report_text_content + "\n\n"
                "📸 بدون صورة</blockquote>"
            )
            try:
                await app.send_message(ADMIN_ID[0], report_msg)
            except Exception as e:
                logger.error(f"Report send error: {e}")
            user_state.pop(user_id, None)
            await message.reply_text(
                "<blockquote>✅ تم إرسال بلاغك بنجاح 🌸\nسيتم مراجعته والرد عليك في أقرب وقت</blockquote>",
                reply_markup=user_keyboard() if not is_admin(int(user_id)) else admin_keyboard()
            )

        elif text.startswith("🔓 حد المستخدمين") or text.startswith("🔒 حد المستخدمين"):
            if not is_admin(int(user_id)) or not has_perm(int(user_id), "max_users"):
                await message.reply_text("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
                return
            global max_users_enabled, max_users_limit
            if max_users_enabled:
                max_users_enabled = False
                await message.reply_text(
                    "<blockquote>🔓 تم إلغاء تفعيل حد المستخدمين\nالبوت مفتوح للجميع الآن</blockquote>",
                    reply_markup=admin_keyboard()
                )
            else:
                user_state[user_id] = {"step": "awaiting_max_users"}
                await message.reply_text(
                    "<blockquote>🔒 أرسل الحد الأقصى لعدد المستخدمين (مثال: 50)</blockquote>",
                    reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
                )

        elif user_state.get(user_id, {}).get("step") == "awaiting_max_users":
            try:
                limit = int(text)
                if limit < 1:
                    raise ValueError
                max_users_enabled = True
                max_users_limit = limit
                user_state.pop(user_id, None)
                await message.reply_text(
                    f"<blockquote>✅ تم تفعيل حد المستخدمين\n🔒 الحد الأقصى: {limit} مستخدم</blockquote>",
                    reply_markup=admin_keyboard()
                )
            except ValueError:
                await message.reply_text("<blockquote>❌ يرجى إدخال رقم صحيح أكبر من 0</blockquote>")

        elif user_state.get(user_id, {}).get("step") == "awaiting_night_start":
            try:
                hour = int(text)
                if not 0 <= hour <= 23:
                    raise ValueError
                night_mode_start = hour
                user_state.pop(user_id, None)
                await message.reply_text(
                    f"<blockquote>✅ تم تغيير وقت بداية الوضع الليلي\n🕐 البداية: {hour}:00\n🕔 النهاية: {night_mode_end}:00</blockquote>",
                    reply_markup=admin_keyboard()
                )
            except ValueError:
                await message.reply_text("<blockquote>❌ أدخل رقم صحيح بين 0 و 23</blockquote>")

        elif user_state.get(user_id, {}).get("step") == "awaiting_night_end":
            try:
                hour = int(text)
                if not 0 <= hour <= 23:
                    raise ValueError
                night_mode_end = hour
                user_state.pop(user_id, None)
                await message.reply_text(
                    f"<blockquote>✅ تم تغيير وقت نهاية الوضع الليلي\n🕐 البداية: {night_mode_start}:00\n🕔 النهاية: {hour}:00</blockquote>",
                    reply_markup=admin_keyboard()
                )
            except ValueError:
                await message.reply_text("<blockquote>❌ أدخل رقم صحيح بين 0 و 23</blockquote>")

        elif text == "🔙 رجوع":
            if not is_admin(int(user_id)):
                return
            await message.reply_text(
                "<blockquote>🔙 تم الرجوع للقائمة الرئيسية</blockquote>",
                reply_markup=admin_keyboard()
            )

        elif text.startswith("🟢 الآن: البوت يعمل") or text.startswith("🔴 الآن: البوت في وضع الصيانة"):
            if not is_admin(int(user_id)):
                return
            maintenance_mode = not maintenance_mode
            if maintenance_mode:
                await message.reply_text(
                    "<blockquote>🔴 تم تفعيل وضع الصيانة\n\n"
                    "• المستخدمون لن يتمكنوا من استخدام البوت الآن\n"
                    "• أنت كأدمن تستطيع الاستخدام بشكل طبيعي</blockquote>",
                    reply_markup=admin_keyboard()
                )
            else:
                await message.reply_text(
                    "<blockquote>🟢 تم إيقاف وضع الصيانة\n\n"
                    "• البوت الآن متاح لجميع المستخدمين</blockquote>",
                    reply_markup=admin_keyboard()
                )

        elif text == "الخروج":
            first_name = message.from_user.first_name or "أخي الكريم"
            await message.reply_text(
                "<blockquote>👋 وداعاً " + first_name + "\n\n"
                "نسأل الله أن يجعل هذا الوقت شاهداً لنا يوم القيامة\n"
                "ويجعله وإياكم في ميزان حسناتنا 🤍\n\n"
                "﴿ وَتَزَوَّدُوا فَإِنَّ خَيْرَ الزَّادِ التَّقْوَىٰ ﴾</blockquote>",
                reply_markup=ReplyKeyboardRemove()
            )        
        elif user_state.get(user_id, {}).get("step") == "awaiting_channel":
            try:
                chat = await client.get_chat(text)
                member = await client.get_chat_member(chat.id, "me")                
                if not member.privileges or not member.privileges.can_invite_users:
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
                err_msg = str(e)
                # لو الرسالة HTML خليها، لو لا حطها في blockquote
                if not err_msg.startswith('<'):
                    err_msg = f"<blockquote>❌ {err_msg}</blockquote>"
                await message.reply_text(err_msg)
                user_state.pop(user_id, None)        
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
            user_state.pop(user_id, None)            
            await message.reply_text(
                f"<blockquote> • تمت إعداد القناة بنجاح! \n"
                f"العنوان: {channel_data['title']}\n"
                f"رابط البث: {text}</blockquote>",
                reply_markup=user_keyboard() if not is_admin(int(user_id)) else admin_keyboard()
            )
        elif user_state.get(user_id, {}).get("step") == "awaiting_station_for_broadcast":
            # لو المستخدم كتب رقم وهو داخل قسم معين
            current_cat = user_state[user_id].get("current_cat")
            if current_cat and current_cat in ST_CATEGORIES:
                station_ids = ST_CATEGORIES[current_cat]
                try:
                    idx = int(text) - 1
                    if 0 <= idx < len(station_ids):
                        sid = station_ids[idx]
                        selected_station_url = ST_TIMO[sid]['url']
                        station_name = ST_TIMO[sid]['name']
                        user_data[user_id]["temp_station"] = selected_station_url
                        save_data()
                        channels = user_data[user_id]["channels"]
                        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                        ch_buttons = []
                        for ch_id, ch_info in list(channels.items()):
                            status = "🟢" if "process" in ch_info else "🔴"
                            ch_buttons.append([InlineKeyboardButton(
                                f"{status} {ch_info['title']}",
                                callback_data=f"broadcast_{ch_id}"
                            )])
                        await message.reply_text(
                            f"<blockquote>✅ تم اختيار: {station_name}\n\nاختر القناة للبث:</blockquote>",
                            reply_markup=InlineKeyboardMarkup(ch_buttons)
                        )
                        user_state[user_id] = {"step": "awaiting_channel_choice", "station_url": selected_station_url}
                    else:
                        await message.reply_text("<blockquote>❌ رقم غير صحيح، اضغط على الزرار أو اكتب رقم صحيح</blockquote>")
                except ValueError:
                    await message.reply_text("<blockquote>❌ اكتب رقم صحيح</blockquote>")
            else:
                await message.reply_text("<blockquote>❌ اختر قسماً أولاً من الأزرار</blockquote>")
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
                    "-vn",
                    "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                    "-f", "flv", channel_info["rtmps_url"]
                ]
                process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                user_data[user_id]["channels"][channel_id]["process"] = process.pid
                save_data()                
                await send_broadcast_notification(client, channel_info['chat_id'], selected_station)
                # إشعار الأدمن
                if not is_admin(int(user_id)) and broadcast_notify_enabled:
                    try:
                        station_name_notify = next((v["name"] for v in ST_TIMO.values() if v["url"] == selected_station), "غير معروف")
                        await app.send_message(
                            ADMIN_ID[0],
                            "<blockquote>📢 مستخدم بدأ البث\n"
                            "👤 المستخدم: " + str(user_id) + "\n"
                            "📡 القناة: " + channel_info['title'] + "\n"
                            "🎙 المحطة: " + station_name_notify + "</blockquote>"
                        )
                    except Exception as e:
                        logger.error(f"broadcast notify admin error: {e}")
                station_name_stat = next((v["name"] for v in ST_TIMO.values() if v["url"] == selected_station), "غير معروف")
                broadcast_stats[channel_id] = {
                    "station": station_name_stat,
                    "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "user_id": user_id
                }
                broadcast_start_times[channel_id] = time.time()
                save_broadcast_state()
                user_state.pop(user_id, None)
                await message.reply_text(
                    f"<blockquote> • بدأ البث على {channel_info['title']}</blockquote>",
                    reply_markup=user_keyboard() if not is_admin(int(user_id)) else admin_keyboard()
                )            
            except (ValueError, IndexError):
                await message.reply_text("<blockquote> • رقم قناة غير صحيح!</blockquote>")
                user_state.pop(user_id, None)
    except Exception as e:
        logger.error(f"Text handling error: {str(e)}")
        await message.reply_text("حدث خطأ، الرجاء المحاولة لاحقًا")


@app.on_message(filters.photo & filters.private)
async def handle_photo(client, message):
    """استقبال الصور — للبلاغات وتقييمات البوت والمحطات"""
    user_id = str(message.from_user.id)
    step = user_state.get(user_id, {}).get("step")

    # صورة بلاغ مشكلة
    if step == "awaiting_report":
        saved_text = user_state[user_id].get("report_text", "")
        caption_text = message.caption or ""
        final_text = saved_text or caption_text or "بدون وصف"
        report_text = (
            "<blockquote>⚠️ بلاغ جديد عن مشكلة\n\n"
            "👤 المستخدم: " + user_id + "\n"
            "📛 الاسم: " + (message.from_user.first_name or "غير معروف") + "\n"
            "🔗 اليوزر: @" + (message.from_user.username or "بدون يوزر") + "\n\n"
            "📝 المشكلة:\n" + final_text + "</blockquote>"
        )
        try:
            await app.send_photo(ADMIN_ID[0], photo=message.photo.file_id, caption=report_text)
        except Exception as e:
            logger.error(f"Photo report error: {e}")
        user_state.pop(user_id, None)
        await message.reply_text(
            "<blockquote>✅ تم إرسال بلاغك مع الصورة بنجاح 🌸\nسيتم مراجعته والرد عليك في أقرب وقت</blockquote>",
            reply_markup=user_keyboard() if not is_admin(int(user_id)) else admin_keyboard()
        )

    # صورة تقييم البوت
    elif step == "awaiting_bot_review_photo":
        score = user_state[user_id].get("bot_rating_stars", 0)
        comment = user_state[user_id].get("bot_review_text", "بدون تعليق")
        rating_msg = (
            "<blockquote>⭐ تقييم جديد للبوت\n\n"
            "👤 المستخدم: " + user_id + "\n"
            "📛 الاسم: " + (message.from_user.first_name or "غير معروف") + "\n"
            "🔗 اليوزر: @" + (message.from_user.username or "بدون يوزر") + "\n"
            "⭐ التقييم: " + str(score) + "/10\n"
            "💬 التعليق: " + comment + "</blockquote>"
        )
        try:
            await app.send_photo(ADMIN_ID[0], photo=message.photo.file_id, caption=rating_msg)
        except Exception as e:
            logger.error(f"Bot rating photo error: {e}")
        user_state.pop(user_id, None)
        await message.reply_text(
            "<blockquote>✅ تم إرسال تقييمك بنجاح 🌸</blockquote>",
            reply_markup=user_keyboard() if not is_admin(int(user_id)) else admin_keyboard()
        )

    # صورة تقييم المحطة
    elif step == "awaiting_station_review_photo":
        sid = user_state[user_id].get("rating_station_id", "")
        stars = user_state[user_id].get("station_stars", 0)
        comment = user_state[user_id].get("station_review_text", "بدون تعليق")
        station_name = ST_TIMO.get(sid, {}).get("name", sid)
        new_avg = get_station_rating(sid)
        count = station_ratings.get(sid, {}).get("count", 0)
        rating_msg = (
            "<blockquote>🎙 تقييم جديد للمحطة\n\n"
            "👤 المستخدم: " + user_id + "\n"
            "📛 الاسم: " + (message.from_user.first_name or "غير معروف") + "\n"
            "🔗 اليوزر: @" + (message.from_user.username or "بدون يوزر") + "\n"
            "📻 المحطة: " + station_name + "\n"
            "⭐ التقييم: " + str(stars) + "/5\n"
            "💬 التعليق: " + comment + "</blockquote>"
        )
        try:
            await app.send_photo(ADMIN_ID[0], photo=message.photo.file_id, caption=rating_msg)
        except Exception as e:
            logger.error(f"Station rating photo error: {e}")
        user_state.pop(user_id, None)
        await message.reply_text(
            f"<blockquote>✅ تم إرسال تقييمك بنجاح 🌸\n\n"
            f"📻 {station_name}\n"
            f"التقييم الجديد: {get_rating_stars(new_avg)} ({new_avg}/5)\n"
            f"عدد المقيّمين: {count}</blockquote>",
            reply_markup=user_keyboard() if not is_admin(int(user_id)) else admin_keyboard()
        )


async def main():
    global _bot_loop
    _bot_loop = asyncio.get_running_loop()
    await app.start()
    logger.info("Bot started...")
    await app.set_bot_commands([
        BotCommand("start", "🚀 تشغيل البوت"),
        BotCommand("check", "✅ التحقق من الاشتراك"),
    ])
    restore_broadcasts()
    threading.Thread(target=scheduled_restart, daemon=True).start()
    threading.Thread(target=run_auto_schedule, daemon=True).start()
    threading.Thread(target=watchdog, daemon=True).start()
    threading.Thread(target=daily_report_thread, daemon=True).start()
    threading.Thread(target=night_mode_thread, daemon=True).start()
    threading.Thread(target=subscription_watcher_thread, daemon=True).start()
    threading.Thread(target=tarawih_thread, daemon=True).start()
    await idle()

if __name__ == "__main__":
    logger.info("Starting Radio Bot...")
    asyncio.run(main())
