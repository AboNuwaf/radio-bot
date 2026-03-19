# ============================================
# 🤖 بوت أثير القرآن
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

# ===== Keep-Alive لـ Railway =====
from flask import Flask as _Flask
_web_app = _Flask(__name__)

@_web_app.route('/')
def _home():
    return '🤖 Atheer Al-Quran Bot شغال!', 200

def _run_web():
    port = int(os.environ.get('PORT', 8080))
    _web_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

threading.Thread(target=_run_web, daemon=True).start()
# ==================================
from pyrogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, BotCommand
from pyrogram.errors import RPCError

os.makedirs("/data", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/data/radio_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

API_ID = 29667286
API_HASH = "2dddc2f98e16161cb50e41971f9591be"
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7795185106:AAGMAOVgGchw-YEKWWHR_DEyBINpGMvOGNY")
OWNER_ID = 6869497898

ADMIN_ID = [OWNER_ID]
ADMIN_PERMISSIONS = {}

ALL_PERMISSIONS = {
    "ban":          "حظر/رفع حظر",
    "broadcast_msg":"إذاعة رسائل",
    "stats":        "إحصائيات",
    "schedule":     "الجدول التلقائي",
    "night_mode":   "الوضع الليلي",
    "daily_report": "تقرير يومي",
    "max_users":    "حد المستخدمين",
    "view_data":    "عرض القنوات/المستخدمين",
    "manage_admins":"رفع/إزالة أدمن",
    "sub_channels": "إدارة الاشتراك الإجباري",
    "notifications":"إشعار الأدمن/القناة",
    "maintenance":  "وضع الصيانة",
    "view_reports": "عرض البلاغات",
    "view_reviews": "عرض التقييمات",
    "manage_feedback": "رد/مسح البلاغات والاقتراحات والتقييمات",
    "backup_restore":  "نسخ احتياطي واستعادة البيانات",
}

def has_perm(user_id: int, perm: str) -> bool:
    if user_id == OWNER_ID:
        return True
    return ADMIN_PERMISSIONS.get(user_id, {}).get(perm, False)

DATA_FILE = "/data/user_data.json"

REQUIRED_CHANNELS = []  # تضاف من البوت بأمر /add_channel

def save_required_channels():
    """حفظ القنوات في ملف احتياطي وفي settings"""
    try:
        channels_json = json.dumps(REQUIRED_CHANNELS, ensure_ascii=False)
        with open("/data/required_channels_backup.json", "w") as f:
            f.write(channels_json)
        save_settings()
    except Exception as e:
        logger.error(f"save_required_channels error: {e}")

def load_required_channels():
    """تحميل القنوات من الملف الاحتياطي أولاً ثم settings"""
    global REQUIRED_CHANNELS
    try:
        # أولاً: من الملف الاحتياطي
        if os.path.exists("/data/required_channels_backup.json"):
            with open("/data/required_channels_backup.json", "r") as f:
                data = json.load(f)
                if data:
                    REQUIRED_CHANNELS = data
                    logger.info(f"✅ تم تحميل {len(REQUIRED_CHANNELS)} قناة اشتراك إجباري")
                    return
        # ثانياً: من settings.json
        if os.path.exists("/data/settings.json"):
            with open("/data/settings.json", "r", encoding="utf-8") as f:
                s = json.load(f)
                channels = s.get("REQUIRED_CHANNELS", [])
                if channels:
                    REQUIRED_CHANNELS = channels
                    logger.info(f"✅ تم تحميل {len(REQUIRED_CHANNELS)} قناة من settings")
                    return
        REQUIRED_CHANNELS = []
    except Exception as e:
        logger.error(f"load_required_channels error: {e}")
        REQUIRED_CHANNELS = []

IMAGE_TIMO = "https://ibb.co/JWfWVPLn"

FFMPEG_TIMEOUT = 30

AUTO_SCHEDULE = {
    "05:00": {"name": "إذاعة أذكار الصباح", "url": "https://qurango.net/radio/athkar_sabah"},
    "06:00": {"name": "إذاعة ياسر الدوسري", "url": "https://qurango.net/radio/yasser_aldosari"},
    "09:00": {"name": "إذاعة تفسير القرآن الكريم", "url": "https://qurango.net/radio/tafseer"},
    "12:00": {"name": "إذاعة ماهر المعيقلي", "url": "https://qurango.net/radio/maher_al_meaqli"},
    "14:00": {"name": "إذاعة سعد الغامدي", "url": "https://qurango.net/radio/saad_alghamdi"},
    "16:00": {"name": "إذاعة المنشاوي - مجود", "url": "https://qurango.net/radio/mohammed_siddiq_alminshawi_mojawwad"},
    "18:00": {"name": "إذاعة أذكار المساء", "url": "https://qurango.net/radio/athkar_masa"},
    "19:00": {"name": "إذاعة مشاري العفاسي", "url": "https://qurango.net/radio/mishary_alafasi"},
    "21:00": {"name": "إذاعة عبد الباسط عبد الصمد - مجود", "url": "https://qurango.net/radio/abdulbasit_abdulsamad_mojawwad"},
    "23:00": {"name": "إذاعة آيات السكينة", "url": "https://qurango.net/radio/sakeenah"},
}

TARAWIH_STATION = {"name": "🕌 إذاعة صلاة التراويح من الحرم المكي", "url": "https://stream.radiojar.com/0tpy1h0kxtzuv"}
tarawih_enabled = True
tarawih_time = None
schedule_disabled = set()
auto_schedule_enabled = False
user_schedule_enabled = {}
max_users_enabled = False
max_users_limit = 100
broadcast_stats = {}
saved_broadcasts = {}
banned_users = set()
all_reports = []  # حفظ كل البلاغات
all_bot_reviews = []  # حفظ كل تقييمات البوت
all_suggestions = []  # حفظ كل الاقتراحات
broadcast_start_times = {}
auto_refresh_enabled = {}
auto_refresh_interval = {}
pending_replies = {}  # {message_id: {"user_id": uid, "type": "report"|"suggest"|"bot_review"|"station_review"}}
daily_report_enabled = False
station_ratings = {}
night_mode_enabled = False
night_mode_start = 23
night_mode_end = 5
NIGHT_MODE_STATIONS = ["1", "30", "31", "10", "6"]
broadcast_notify_enabled = True
channel_notify_enabled = True  # إشعار القناة عند بدء البث
subscription_violations = {}
about_bot_visible = True
ABOUT_BOT_IMAGE = "https://ibb.co/JWfWVPLn"
maintenance_mode = False
MAINTENANCE_IMAGE = "https://i.ibb.co/677DXz1b/1773241798859.png"

ST_TIMO = {
    "1": {"name": "إذاعة آيات السكينة", "url": "https://qurango.net/radio/sakeenah"},
    "2": {"name": "إذاعة القرآن من مكة المكرمة", "url": "https://backup.qurango.net/radio/makkah_live"},
    "3": {"name": "إذاعة القرآن من القاهرة", "url": "https://stream.radiojar.com/8s5u5tpdtwzuv"},
    "4": {"name": "إذاعة القرآن من مختلف القراء", "url": "https://qurango.net/radio/mix"},
    "5": {"name": "إذاعة السيرة النبوية", "url": "https://qurango.net/radio/fi_zilal_alsiyra"},
    "6": {"name": "إذاعة الرقية الشرعية 1", "url": "https://qurango.net/radio/roqiah"},
    "7": {"name": "إذاعة الرقية الشرعية 2", "url": "https://live.mp3quran.net:9936/;"},
    "8": {"name": "إذاعة الفتوة", "url": "https://qurango.net/radio/fatwa"},
    "9": {"name": "إذاعة الحرم المكي", "url": "https://stream.radiojar.com/0tpy1h0kxtzuv"},
    "10": {"name": "إذاعة تلاوات خاشعة", "url": "https://qurango.net/radio/salma"},
    "11": {"name": "إذاعة أحمد العجمي", "url": "https://qurango.net/radio/ahmad_alajmy"},
    "12": {"name": "إذاعة إدريس أبكر", "url": "https://qurango.net/radio/idrees_abkr"},
    "13": {"name": "إذاعة عبد الباسط عبد الصمد - مجود", "url": "https://qurango.net/radio/abdulbasit_abdulsamad_mojawwad"},
    "14": {"name": "إذاعة عبد الرحمن السديس", "url": "https://qurango.net/radio/abdulrahman_alsudaes"},
    "15": {"name": "إذاعة ماهر المعيقلي", "url": "https://qurango.net/radio/maher_al_meaqli"},
    "16": {"name": "إذاعة محمد اللحيدان", "url": "https://qurango.net/radio/mohammed_allohaidan"},
    "17": {"name": "إذاعة ياسر الدوسري", "url": "https://qurango.net/radio/yasser_aldosari"},
    "18": {"name": "إذاعة مشاري العفاسي", "url": "https://qurango.net/radio/mishary_alafasi"},
    "19": {"name": "إذاعة فارس عباد", "url": "https://qurango.net/radio/fares_abbad"},
    "20": {"name": "إذاعة محمد أيوب", "url": "https://backup.qurango.net/radio/mohammed_ayoub"},
    "22": {"name": " قناة قران الكريم ", "url": "https://win.holol.com/live/quran/playlist.m3u"},
    "23": {"name": "قناة السنه النبويه  ", "url": "https://win.holol.com/live/sunnah/playlist.m3u8"},
    "24": {"name": "إذاعة المنشاوي - مجود", "url": "https://qurango.net/radio/mohammed_siddiq_alminshawi_mojawwad"},
    "25": {"name": "إذاعة خالد جليل", "url": "https://qurango.net/radio/khalid_aljileel"},
    "26": {"name": "إذاعة الحصري - مرتل", "url": "https://qurango.net/radio/mahmoud_khalil_alhussary_murattal"},
    "27": {"name": "إذاعة ناصر القطامي", "url": "https://qurango.net/radio/nasser_alqatami"},
    "28": {"name": "إذاعة تفسير القرآن الكريم", "url": "https://qurango.net/radio/tafseer"},
    "29": {"name": "إذاعة سعد الغامدي", "url": "https://qurango.net/radio/saad_alghamdi"},
    "30": {"name": "إذاعة أذكار الصباح", "url": "https://qurango.net/radio/athkar_sabah"},
    "31": {"name": "إذاعة أذكار المساء", "url": "https://qurango.net/radio/athkar_masa"}
}

ST_CATEGORIES = {
    "🎙 القراء": ["11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "24", "25", "26", "27", "29"],
    "🕌 القنوات والمحطات": ["2", "3", "4", "9", "10", "22", "23"],
    "📿 الأذكار والرقية": ["1", "6", "7", "30", "31"],
    "📖 التفسير والسيرة": ["5", "8", "28"],
}

SESSION_STRING = os.environ.get("SESSION_STRING", None)

if SESSION_STRING:
    app = Client("radio_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN,
                 session_string=SESSION_STRING, parse_mode=enums.ParseMode.HTML)
else:
    app = Client("radio_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN,
                 parse_mode=enums.ParseMode.HTML)
_bot_loop = None
data_lock = threading.Lock()
user_data = {}
user_state = {}

def get_station_rating(sid):
    if sid not in station_ratings or station_ratings[sid]["count"] == 0:
        return 0.0
    return round(station_ratings[sid]["total"] / station_ratings[sid]["count"], 1)

def get_station_rating_stars(rating):
    full = int(rating)
    half = 1 if (rating - full) >= 0.5 else 0
    empty = 5 - full - half
    return "⭐" * full + ("✨" if half else "") + "☆" * empty

def get_rating_stars(rating):
    full = int(rating)
    half = 1 if (rating - full) >= 0.5 else 0
    empty = 10 - full - half
    return "⭐" * full + ("✨" if half else "") + "☆" * empty

def fetch_isha_time():
    global tarawih_time
    try:
        import urllib.request, json as _json
        url = "https://api.aladhan.com/v1/timingsByCity?city=Riyadh&country=Saudi%20Arabia&method=4"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = _json.loads(resp.read())
        isha = data["data"]["timings"]["Isha"]
        tarawih_time = isha[:5]
        logger.info(f"Tarawih time fetched: {tarawih_time}")
    except Exception as e:
        logger.error(f"Failed to fetch Isha time: {e}")
        tarawih_time = "20:30"

def tarawih_thread():
    global tarawih_time, tarawih_enabled
    last_triggered = None
    last_fetch_day = None
    while True:
        try:
            today = time.strftime("%Y-%m-%d")
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
                                ffmpeg_cmd = build_ffmpeg_cmd(TARAWIH_STATION["url"], ch_info["rtmps_url"])
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
    night_active = False
    while True:
        hour = int(time.strftime("%H"))
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
                        ffmpeg_cmd = build_ffmpeg_cmd(night_url, channel_info["rtmps_url"])
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
    if channel_id not in broadcast_start_times:
        return "غير معروف"
    elapsed = time.time() - broadcast_start_times[channel_id]
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    return f"{hours} ساعة و {minutes} دقيقة"

def daily_report_thread():
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

BACKUP_CHANNEL_ID = -1003857300451
backup_schedule_enabled = False
backup_schedule_day = 4      # 0=الاثنين ... 4=الجمعة ... 6=الأحد
backup_schedule_time = "08:00"

DAYS_AR = {
    0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء",
    3: "الخميس", 4: "الجمعة", 5: "السبت", 6: "الأحد"
}

def weekly_backup_thread():
    """نسخ احتياطي تلقائي بالجدول المحدد"""
    sent_this_period = False
    while True:
        if backup_schedule_enabled:
            now = time.localtime()
            current_time = time.strftime("%H:%M")
            is_right_day = now.tm_wday == backup_schedule_day
            if is_right_day and current_time == backup_schedule_time and not sent_this_period:
                async def send_auto_backup():
                    try:
                        await app.send_message(
                            BACKUP_CHANNEL_ID,
                            f"<blockquote>📦 نسخة احتياطية تلقائية\n"
                            f"🗓 {time.strftime('%Y-%m-%d %H:%M')}\n"
                            f"👥 المستخدمين: {len(user_data)}\n"
                            f"📢 قنوات الاشتراك: {len(REQUIRED_CHANNELS)}</blockquote>"
                        )
                        files = [
                            ("/data/user_data.json",               "👥 بيانات المستخدمين"),
                            ("/data/settings.json",                "⚙️ الإعدادات"),
                            ("/data/required_channels_backup.json","📢 قنوات الاشتراك الإجباري"),
                        ]
                        for path, label in files:
                            if os.path.exists(path):
                                size_kb = round(os.path.getsize(path) / 1024, 1)
                                await app.send_document(
                                    BACKUP_CHANNEL_ID,
                                    document=path,
                                    caption=f"<blockquote>{label}\n📁 {size_kb} KB</blockquote>"
                                )
                        logger.info("✅ تم إرسال النسخة الاحتياطية التلقائية")
                    except Exception as ex:
                        logger.error(f"Auto backup error: {ex}")
                asyncio.run_coroutine_threadsafe(send_auto_backup(), _bot_loop)
                sent_this_period = True
            elif not is_right_day or current_time != backup_schedule_time:
                sent_this_period = False
        time.sleep(30)

def save_broadcast_state():
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
    # احفظ في ملف
    try:
        with open("/data/broadcast_state.json", "w", encoding="utf-8") as f:
            import json as _json
            _json.dump(saved_broadcasts, f, ensure_ascii=False)
    except Exception as e:
        logger.error(f"save_broadcast_state file error: {e}")

def restore_broadcasts():
    global saved_broadcasts
    # حاول تحمل من الملف لو الذاكرة فاضية
    if not saved_broadcasts:
        try:
            import os as _os
            if _os.path.exists("/data/broadcast_state.json"):
                with open("/data/broadcast_state.json", "r", encoding="utf-8") as f:
                    import json as _json
                    saved_broadcasts = _json.load(f)
        except Exception as e:
            logger.error(f"restore_broadcasts load error: {e}")
    if not saved_broadcasts:
        return
    logger.info(f"Restoring {len(saved_broadcasts)} broadcasts after restart...")
    for channel_id, info in saved_broadcasts.items():
        try:
            ffmpeg_cmd = build_ffmpeg_cmd(info["station"], info["rtmps_url"])
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
    """التحقق من الاشتراك الحقيقي"""
    for channel in REQUIRED_CHANNELS:
        try:
            ch_id = channel["id"]
            try:
                ch_id = int(ch_id)
            except (ValueError, TypeError):
                pass
            member = await client.get_chat_member(ch_id, user_id)
            if member.status.name in ["LEFT", "BANNED", "KICKED", "RESTRICTED"]:
                return channel
            if hasattr(member, 'is_member') and member.is_member is False:
                return channel
        except Exception as e:
            err = str(e).lower()
            if "user_not_participant" in err or "user_id_invalid" in err:
                return channel
            elif "not enough rights" in err or "chat_admin_required" in err:
                pass
            elif "channel_invalid" in err or "chat_id_invalid" in err or "peer_id_invalid" in err:
                pass
            else:
                logger.error(f"check_subscription error for {user_id} in {channel.get('id')}: {e}")
                pass
    return None

async def stop_user_broadcasts(user_id):
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
    while True:
        time.sleep(60)
        try:
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
    global subscription_violations, banned_users
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    unsubscribed = await check_subscription(app, int(uid))
    if not unsubscribed:
        subscription_violations.pop(uid, None)
        return

    subscription_violations[uid] = subscription_violations.get(uid, 0) + 1
    count = subscription_violations[uid]

    stopped = await stop_user_broadcasts(uid)

    if count >= 5:
        banned_users.add(int(uid))
        subscription_violations.pop(uid, None)
        save_settings()
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
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    channel_id = channel["id"]
    channel_url = channel["url"]
    custom_text = channel.get("custom_text", "").strip()

    # نجيب اسم القناة الحقيقي
    channel_name = channel_url  # افتراضي
    try:
        ch_id = int(channel_id) if str(channel_id).lstrip('-').isdigit() else channel_id
        chat = await app.get_chat(ch_id)
        channel_name = chat.title or channel_url
    except Exception:
        pass

    if custom_text:
        text = custom_text + "\n\n‼️| بعد الاشتراك، اضغط تحقق /Check للمتابعة."
    else:
        text = (
            "🚸| عذراً عزيزي.\n"
            "🔰| لاستخدام هذا البوت، يُرجى الاشتراك أولًا في " + channel_name + "\n\n"
            "• نهدف من ذلك إلى نشر الخير والتذكير، ونسأل الله أن يجعل اشتراكك ومتابعتك في ميزان حسناتك.\n\n"
            "- " + channel_url + "\n\n"
            "‼️| بعد الاشتراك، اضغط تحقق /Check للمتابعة."
        )
    await message.reply_text(
        text,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 " + channel_name, url=channel_url)]
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

SETTINGS_ENV_KEY = "BOT_SETTINGS"

def save_settings():
    """حفظ كل إعدادات وبيانات البوت في Railway Environment Variable"""
    try:
        settings = {
            "broadcast_notify_enabled": broadcast_notify_enabled,
            "channel_notify_enabled": channel_notify_enabled,
            "auto_schedule_enabled": auto_schedule_enabled,
            "maintenance_mode": maintenance_mode,
            "night_mode_enabled": night_mode_enabled,
            "night_mode_start": night_mode_start,
            "night_mode_end": night_mode_end,
            "daily_report_enabled": daily_report_enabled,
            "max_users_enabled": max_users_enabled,
            "max_users_limit": max_users_limit,
            "about_bot_visible": about_bot_visible,
            "tarawih_enabled": tarawih_enabled,
            "banned_users": list(banned_users),
            "ADMIN_PERMISSIONS": {str(k): v for k, v in ADMIN_PERMISSIONS.items()},
            "station_ratings": station_ratings,
            "all_reports": all_reports,
            "all_bot_reviews": all_bot_reviews,
            "all_suggestions": all_suggestions,
            "subscription_violations": subscription_violations,
            "user_schedule_enabled": user_schedule_enabled,
            "schedule_disabled": list(schedule_disabled),
            "REQUIRED_CHANNELS": REQUIRED_CHANNELS,
            "auto_refresh_enabled": auto_refresh_enabled,
            "auto_refresh_interval": auto_refresh_interval,
            "pending_replies": {str(k): v for k, v in pending_replies.items()},
            "backup_schedule_enabled": backup_schedule_enabled,
            "backup_schedule_day": backup_schedule_day,
            "backup_schedule_time": backup_schedule_time,
        }
        settings_json = json.dumps(settings, ensure_ascii=False)
        os.environ[SETTINGS_ENV_KEY] = settings_json
        # احتياطي في ملف برضو
        with open("/data/settings.json", "w", encoding="utf-8") as f:
            f.write(settings_json)
    except Exception as e:
        logger.error(f"save_settings error: {e}")

def load_settings():
    """تحميل كل إعدادات وبيانات البوت من Railway Environment Variable أو الملف الاحتياطي"""
    global broadcast_notify_enabled, channel_notify_enabled, auto_schedule_enabled
    global maintenance_mode, night_mode_enabled, night_mode_start, night_mode_end
    global daily_report_enabled, max_users_enabled, max_users_limit, about_bot_visible
    global tarawih_enabled, banned_users, ADMIN_PERMISSIONS, station_ratings
    global all_reports, all_bot_reviews, all_suggestions, subscription_violations
    global user_schedule_enabled, schedule_disabled, REQUIRED_CHANNELS
    global auto_refresh_enabled, auto_refresh_interval
    global pending_replies
    global backup_schedule_enabled, backup_schedule_day, backup_schedule_time
    try:
        # أولاً: جرب من Environment Variable
        val = os.environ.get(SETTINGS_ENV_KEY, "").strip()
        # لو مش موجود: جرب من الملف الاحتياطي
        if not val or val == "{}":
            if os.path.exists("/data/settings.json"):
                with open("/data/settings.json", "r", encoding="utf-8") as f:
                    val = f.read().strip()
        if not val or val == "{}":
            return
        s = json.loads(val)
        broadcast_notify_enabled = s.get("broadcast_notify_enabled", True)
        channel_notify_enabled = s.get("channel_notify_enabled", True)
        auto_schedule_enabled = s.get("auto_schedule_enabled", False)
        maintenance_mode = s.get("maintenance_mode", False)
        night_mode_enabled = s.get("night_mode_enabled", False)
        night_mode_start = s.get("night_mode_start", 23)
        night_mode_end = s.get("night_mode_end", 5)
        daily_report_enabled = s.get("daily_report_enabled", False)
        max_users_enabled = s.get("max_users_enabled", False)
        max_users_limit = s.get("max_users_limit", 100)
        about_bot_visible = s.get("about_bot_visible", True)
        tarawih_enabled = s.get("tarawih_enabled", True)
        banned_users = set(s.get("banned_users", []))
        ADMIN_PERMISSIONS = {int(k): v for k, v in s.get("ADMIN_PERMISSIONS", {}).items()}
        station_ratings = s.get("station_ratings", {})
        all_reports = s.get("all_reports", [])
        all_bot_reviews = s.get("all_bot_reviews", [])
        all_suggestions = s.get("all_suggestions", [])
        subscription_violations = s.get("subscription_violations", {})
        user_schedule_enabled = s.get("user_schedule_enabled", {})
        schedule_disabled = set(s.get("schedule_disabled", []))
        REQUIRED_CHANNELS = s.get("REQUIRED_CHANNELS", [])
        auto_refresh_enabled = s.get("auto_refresh_enabled", {})
        auto_refresh_interval = s.get("auto_refresh_interval", {})
        pending_replies = {int(k): v for k, v in s.get("pending_replies", {}).items()}
        backup_schedule_enabled = s.get("backup_schedule_enabled", False)
        backup_schedule_day = s.get("backup_schedule_day", 4)
        backup_schedule_time = s.get("backup_schedule_time", "08:00")
        logger.info("✅ تم تحميل الإعدادات بنجاح")
    except Exception as e:
        logger.error(f"load_settings error: {e}")

load_data()
load_required_channels()
load_settings()

def is_ffmpeg_running(pid):
    try:
        output = subprocess.check_output(
            ["ps", "-p", str(pid), "-o", "cmd="],
            timeout=3
        ).decode().strip()
        return "ffmpeg" in output
    except:
        return False

def build_ffmpeg_cmd(input_url: str, output_url: str) -> list:
    """بناء أمر ffmpeg — audio only محسّن للاستقرار وجودة الصوت"""
    cmd = ["ffmpeg", "-hide_banner"]

    # reconnect للروابط العادية
    if not input_url.endswith(".m3u") and not input_url.endswith(".m3u8"):
        cmd += [
            "-reconnect", "1",
            "-reconnect_streamed", "1",
            "-reconnect_delay_max", "5",
            "-reconnect_on_network_error", "1",
        ]

    cmd += [
        "-fflags", "+genpts+discardcorrupt",
        "-thread_queue_size", "512",
    ]

    # User-Agent لـ radiojar
    if "radiojar.com" in input_url:
        cmd += ["-user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"]

    # http روابط
    if input_url.startswith("http://"):
        cmd += ["-allowed_extensions", "ALL"]

    cmd += ["-re", "-i", input_url]

    if output_url.startswith("rtmps://"):
        cmd += ["-tls_verify", "0"]

    cmd += [
        "-vn",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-ac", "2",
        "-bufsize", "512k",
        "-maxrate", "192k",
        "-loglevel", "error",
        "-f", "flv", output_url
    ]
    return cmd

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
                ffmpeg_cmd = build_ffmpeg_cmd(selected_station, channel_info["rtmps_url"])
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
                    ffmpeg_cmd = build_ffmpeg_cmd(selected_station, info["rtmps_url"])
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
    from pyrogram.types import InlineKeyboardButton
    def to_arabic_time(t):
        h, m = map(int, t.split(":"))
        period = "صباحاً" if h < 12 else "مساءً"
        h12 = h if h <= 12 else h - 12
        if h12 == 0: h12 = 12
        return f"{h12}:{m:02d} {period}"

    all_entries = []
    for t, s in AUTO_SCHEDULE.items():
        all_entries.append(("schedule", t, s))
    display_tarawih_time = tarawih_time if tarawih_time else "20:30"
    all_entries.append(("tarawih", display_tarawih_time, TARAWIH_STATION))

    all_entries.sort(key=lambda x: x[1])

    buttons = []
    for entry_type, t, s in all_entries:
        ar_time = to_arabic_time(t)
        if entry_type == "schedule":
            is_on = t not in schedule_disabled
            name = s['name'].replace("إذاعة ", "").replace("اذاعة ", "").strip()
            status_icon = "✅" if is_on else "❌"
            toggle_label = "⏹ إيقاف" if is_on else "▶️ تشغيل"
            # صف أول: الوقت والاسم كاملاً
            buttons.append([
                InlineKeyboardButton(f"{status_icon} {ar_time}  |  {name}", callback_data="noop")
            ])
            # صف ثاني: زر التحكم
            buttons.append([
                InlineKeyboardButton(toggle_label,
                    callback_data=f"sched_toggle_{t}_{'on' if not is_on else 'off'}")
            ])
        else:
            name = s['name'].replace("إذاعة ", "").replace("اذاعة ", "").strip()
            status_icon = "✅" if tarawih_enabled else "❌"
            toggle_label = "⏹ إيقاف" if tarawih_enabled else "▶️ تشغيل"
            buttons.append([
                InlineKeyboardButton(f"{status_icon} {ar_time}  |  {name}", callback_data="noop")
            ])
            buttons.append([
                InlineKeyboardButton(toggle_label, callback_data="tarawih_toggle")
            ])
    return buttons

def run_auto_schedule():
    while True:
        current_time = time.strftime("%H:%M")
        if current_time in AUTO_SCHEDULE and current_time not in schedule_disabled:
            station = AUTO_SCHEDULE[current_time]
            switched = False
            for uid, user_info in list(user_data.items()):
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
                        ffmpeg_cmd = build_ffmpeg_cmd(station["url"], channel_info["rtmps_url"])
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
    try:
        msg = "<blockquote>🕐 تم تغيير المحطة تلقائياً إلى:\n" + station_name + "</blockquote>"
        await app.send_message(ADMIN_ID[0], msg)
    except Exception as e:
        logger.error(f"Notify schedule error: {e}")

def watchdog():
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
                            ffmpeg_cmd = build_ffmpeg_cmd(selected_station, channel_info["rtmps_url"])
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
        time.sleep(1800)  # انتظر 30 دقيقة أولاً
        logger.info("Performing scheduled restart...")
        restart_all_broadcasts()

async def send_broadcast_notification(client, chat_id, station_url, user_id=None):
    # تحقق من السويتش العام أولاً
    if not channel_notify_enabled:
        return
    # تحقق من إعداد المستخدم الشخصي
    if user_id and str(user_id) in user_data:
        if not user_data[str(user_id)].get("channel_notify", True):
            return
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
    if not is_admin(message.from_user.id) or not has_perm(message.from_user.id, "stats"):
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
    if not is_admin(message.from_user.id) or not has_perm(message.from_user.id, "broadcast_msg"):
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
    if not is_admin(message.from_user.id) or not has_perm(message.from_user.id, "broadcast_msg"):
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
    if not is_admin(message.from_user.id) or not has_perm(message.from_user.id, "view_data"):
        await message.reply("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
        return

    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    seen_channels = set()
    station_reverse = {v['url']: v['name'] for k, v in ST_TIMO.items()}
    total = 0

    try:
        for uid, user_info in list(user_data.items()):
            if "channels" not in user_info:
                continue

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

                buttons = []
                row = []

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
    if not is_admin(message.from_user.id) or not has_perm(message.from_user.id, "view_data"):
        await message.reply("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
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
        

def user_keyboard(user_id=None):
    user_notify = True
    if user_id and str(user_id) in user_data:
        user_notify = user_data[str(user_id)].get("channel_notify", True)
    notify_btn = "🔔 إشعار قناتي: مفعّل" if user_notify else "🔕 إشعار قناتي: مقفول"
    rows = [
        ["إضافة قناة", "قنواتي"],
        ["بدء البث", "إيقاف البث"],
        ["🔃 تحديث البثوث", "حذف قناة"],
        ["⚙️ الجدول التلقائي"],
        [notify_btn],
        ["🛠 الدعم الفني"],
        ["📞 تواصل مع الأدمن"],
        ["الخروج"]
    ]
    if about_bot_visible:
        rows.insert(-1, ["ℹ️ نبذة عن البوت"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def admin_keyboard(user_id=None):
    uid = str(user_id) if user_id else ""
    uid_int = int(user_id) if user_id else 0
    is_owner = uid_int == OWNER_ID

    def perm(p): return is_owner or has_perm(uid_int, p)

    max_btn = "🔓 حد المستخدمين: مفتوح" if not max_users_enabled else f"🔒 حد المستخدمين: {max_users_limit}"
    report_btn = "📋 التقرير اليومي: مفتوح 🟢" if daily_report_enabled else "📋 التقرير اليومي: مقفول 🔴"
    night_btn = "🌙 الوضع الليلي: مفعّل 🟢" if night_mode_enabled else "🌙 الوضع الليلي: مقفول 🔴"
    notify_btn = "🔔 إشعار الأدمن: مفعّل 🟢" if broadcast_notify_enabled else "🔕 إشعار الأدمن: مقفول 🔴"
    channel_notify_btn = "🔔 إشعار القناة: مفعّل 🟢" if channel_notify_enabled else "🔕 إشعار القناة: مقفول 🔴"
    about_btn = "ℹ️ نبذة عن البوت: ظاهر 🟢" if about_bot_visible else "ℹ️ نبذة عن البوت: مخفي 🔴"
    maintenance_btn = "🔴 الآن: البوت في وضع الصيانة 🔴" if maintenance_mode else "🟢 الآن: البوت يعمل بنجاح 🟢"
    user_notify = True
    if user_id and str(user_id) in user_data:
        user_notify = user_data[str(user_id)].get("channel_notify", True)
    user_notify_btn = "🔔 إشعار قناتي: مفعّل" if user_notify else "🔕 إشعار قناتي: مقفول"

    rows = []

    # وضع الصيانة — للمطور والأدمن المخوّل فقط
    if perm("maintenance"):
        rows.append([maintenance_btn])

    # أزرار البث — للجميع
    rows.append(["إضافة قناة", "قنواتي"])
    rows.append(["بدء البث", "إيقاف البث"])
    rows.append(["🔃 تحديث البثوث", "حذف قناة"])

    # الإحصائيات
    if perm("stats"):
        rows.append(["الاحصائيات", "📊 إحصائيات البث"])

    # الإذاعة للمستخدمين والقنوات
    if perm("broadcast_msg"):
        rows.append(["اذاعة للمستخدمين", "اذاعة للقنوات"])

    # عرض البيانات
    if perm("view_data"):
        rows.append(["القنوات", "المستخدمين"])

    # الجدول التلقائي
    if perm("schedule"):
        rows.append(["⚙️ الجدول التلقائي"])

    # الاشتراك الإجباري
    if perm("sub_channels"):
        rows.append(["📢 الاشتراك الإجباري"])

    # حد المستخدمين + تقرير يومي
    max_row = []
    if perm("max_users"):
        max_row.append(max_btn)
    if perm("daily_report"):
        max_row.append(report_btn)
    if max_row:
        rows.append(max_row)

    # الوضع الليلي
    if perm("night_mode"):
        rows.append([night_btn])

    # إشعار الأدمن — للمخوّل فقط
    if perm("notifications"):
        rows.append([notify_btn])

    # إشعار قناتي — للجميع (كل يوزر يتحكم في قناته هو بس)
    rows.append([user_notify_btn])

    # نبذة عن البوت — للجميع
    rows.append(["ℹ️ نبذة عن البوت", about_btn])

    # الدعم الفني — للجميع
    rows.append(["🛠 الدعم الفني"])

    # حظر/رفع حظر
    if perm("ban"):
        rows.append(["🚫 حظر مستخدم", "✅ رفع الحظر"])

    # رفع/إزالة أدمن
    if perm("manage_admins"):
        rows.append(["➕ رفع أدمن", "➖ إزالة أدمن"])
        rows.append(["👑 إدارة الأدمنز"])

    rows.append(["📞 تواصل مع الأدمن"])

    # نسخ احتياطي — للمطور والأدمن المخوّل
    if perm("backup_restore"):
        rows.append(["📦 نسخ احتياطي"])

    rows.append(["الخروج"])

    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def schedule_keyboard():
    return ReplyKeyboardMarkup([
        ["▶️ تشغيل تلقائي", "⏹ إيقاف تلقائي"],
        ["✏️ تعديل موعد", "🎙 تغيير محطة"],
        ["🔙 رجوع"]
    ], resize_keyboard=True)


async def show_station_categories(message):
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
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    station_ids = ST_CATEGORIES.get(cat_name, [])

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


def build_time_picker_kb(h, m, ttype="sched", old_time=""):
    """بناء Time Picker بأزرار ◀️ ▶️"""
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    h12 = h % 12 or 12
    period = "🌅 صباحاً" if h < 12 else "🌙 مساءً"
    period_cb = "am" if h < 12 else "pm"
    
    buttons = [
        # الساعة
        [InlineKeyboardButton("─── الساعة ───", callback_data="noop")],
        [
            InlineKeyboardButton("◀️", callback_data=f"tp_h_dec_{h}_{m}_{ttype}_{old_time}"),
            InlineKeyboardButton(f"  {h12}  ", callback_data="noop"),
            InlineKeyboardButton("▶️", callback_data=f"tp_h_inc_{h}_{m}_{ttype}_{old_time}"),
        ],
        # الدقيقة
        [InlineKeyboardButton("─── الدقيقة ───", callback_data="noop")],
        [
            InlineKeyboardButton("◀️", callback_data=f"tp_m_dec_{h}_{m}_{ttype}_{old_time}"),
            InlineKeyboardButton(f"  {m:02d}  ", callback_data="noop"),
            InlineKeyboardButton("▶️", callback_data=f"tp_m_inc_{h}_{m}_{ttype}_{old_time}"),
        ],
        # صباح/مساء
        [InlineKeyboardButton(period, callback_data=f"tp_period_{h}_{m}_{ttype}_{old_time}")],
        # تأكيد
        [InlineKeyboardButton(f"✅ تأكيد — {h12}:{m:02d} {period}", callback_data=f"tp_confirm_{h}_{m}_{ttype}_{old_time}")],
    ]
    if ttype == "bsched":
        buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data="backup_schedule")])
    else:
        buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"edit_time_back_{old_time}")])
    return InlineKeyboardMarkup(buttons)

@app.on_callback_query()
async def handle_callback(client, query):
    # Safe access to backup schedule vars
    global backup_schedule_time, backup_schedule_day, backup_schedule_enabled
    global tarawih_enabled
    user_id = str(query.from_user.id)
    data = query.data

    if data == "clear_reviews":
        await query.answer()
        if query.from_user.id != OWNER_ID and not has_perm(query.from_user.id, "view_reviews"):
            return
        all_bot_reviews.clear()
        save_settings()
        await query.edit_message_text("<blockquote>✅ تم مسح كل التقييمات</blockquote>")

    elif data == "clear_reports":
        await query.answer()
        if query.from_user.id != OWNER_ID:
            return
        all_reports.clear()
        save_settings()
        await query.edit_message_text("<blockquote>✅ تم مسح كل البلاغات</blockquote>")

    elif data == "sub_list":
        await query.answer()
        if not REQUIRED_CHANNELS:
            await query.edit_message_text("<blockquote>📋 قائمة الاشتراك الإجباري فارغة.</blockquote>")
            return
        text = "<blockquote>📋 قنوات الاشتراك الإجباري:\n\n"
        for i, ch in enumerate(REQUIRED_CHANNELS, 1):
            preview = ch.get("custom_text", "")
            preview = (preview[:40] + "...") if len(preview) > 40 else (preview if preview else "افتراضي")
            text += f"{i}- {ch['id']}\n📝 النص: {preview}\n\n"
        text += "</blockquote>"
        await query.edit_message_text(text)

    elif data == "sub_add":
        await query.answer()
        user_state[user_id] = {"step": "sub_awaiting_add"}
        await query.edit_message_text(
            "<blockquote>➕ إضافة قناة اشتراك إجباري\n\n"
            "أرسل رابط القناة أو معرفها فقط:\n\n"
            "• https://t.me/Almotawkel_Official\n"
            "• @Almotawkel_Official\n\n"
            "💡 لإضافة نص مخصص اضغط تعديل النص بعد الإضافة</blockquote>"
        )

    elif data == "sub_edit":
        await query.answer()
        if not REQUIRED_CHANNELS:
            await query.edit_message_text("<blockquote>❌ لا توجد قنوات لتعديلها.</blockquote>")
            return
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = [[InlineKeyboardButton(ch["id"], callback_data=f"subedit_{ch['id']}")] for ch in REQUIRED_CHANNELS]
        await query.edit_message_text(
            "<blockquote>✏️ اختر القناة التي تريد تعديل نصها:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("subedit_"):
        ch_id = data[8:]
        await query.answer()
        user_state[user_id] = {"step": "sub_awaiting_edit_text", "edit_channel_id": ch_id}
        await query.edit_message_text(
            f"<blockquote>✏️ تعديل نص {ch_id}\n\n"
            f"أرسل النص الجديد\n"
            f"أو أرسل - لحذف النص المخصص والرجوع للافتراضي</blockquote>"
        )

    elif data == "sub_delete":
        await query.answer()
        if not REQUIRED_CHANNELS:
            await query.edit_message_text("<blockquote>❌ لا توجد قنوات لحذفها.</blockquote>")
            return
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = [[InlineKeyboardButton(f"🗑 {ch['id']}", callback_data=f"subdel_{ch['id']}")] for ch in REQUIRED_CHANNELS]
        await query.edit_message_text(
            "<blockquote>🗑 اختر القناة التي تريد حذفها:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("subdel_"):
        ch_id = data[7:]
        await query.answer()
        REQUIRED_CHANNELS[:] = [ch for ch in REQUIRED_CHANNELS if ch["id"] != ch_id]
        save_required_channels()
        await query.edit_message_text(f"<blockquote>✅ تم حذف {ch_id} بنجاح.</blockquote>")

    elif data.startswith("edit_time_") and not data.startswith("edit_time_back_"):
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        old_time = data[len("edit_time_"):]
        if ":" in old_time:
            _h, _m = map(int, old_time.split(":"))
        else:
            _h, _m = 8, 0
        await query.edit_message_text(
            f"<blockquote>⏰ تعديل موعد البث ({old_time})\n\nاستخدم الأزرار:</blockquote>",
            reply_markup=build_time_picker_kb(_h, _m, "sched", old_time)
        )


    elif data.startswith("edit_station_"):
        target_time = data[13:]
        user_state[user_id] = {"step": "awaiting_new_station_for_schedule", "target_time": target_time}
        await query.answer()
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
        rest = data[10:]
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
        save_settings()
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
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        for cat_name in ST_CATEGORIES:
            count = len(ST_CATEGORIES[cat_name])
            buttons.append([InlineKeyboardButton(f"{cat_name} ({count})", callback_data=f"cat_{cat_name}")])
        await query.edit_message_text(
            "<blockquote>🎙 اختر قسم الإذاعة:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("cat_"):
        cat_name = data[4:]
        await query.answer()
        if cat_name in ST_CATEGORIES:
            if user_id not in user_state:
                user_state[user_id] = {"step": "awaiting_station_for_broadcast"}
            user_state[user_id]["current_cat"] = cat_name
            await show_stations_in_category(query, cat_name)

    elif data.startswith("station_"):
        sid = data[8:]
        if sid not in ST_TIMO:
            await query.answer("❌ محطة غير موجودة", show_alert=True)
            return

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

    elif data == "support_suggest":
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        if query.from_user.id == OWNER_ID or has_perm(query.from_user.id, "view_reports"):
            if not all_suggestions:
                await query.edit_message_text(
                    "<blockquote>💡 الاقتراحات\n\n📭 لا توجد اقتراحات حتى الآن</blockquote>",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 رجوع", callback_data="support_back")]
                    ])
                )
            else:
                text_msg = f"<blockquote>💡 كل الاقتراحات ({len(all_suggestions)} اقتراح)\n\n"
                for i, r in enumerate(all_suggestions, 1):
                    text_msg += (
                        f"{'─'*20}\n"
                        f"#{i} | {r['time']}\n"
                        f"👤 {r['name']} (@{r['username']})\n"
                        f"🆔 {r['user_id']}\n"
                        f"💡 {r['text']}\n\n"
                    )
                text_msg += "</blockquote>"
                buttons = [
                    [InlineKeyboardButton("🗑 مسح كل الاقتراحات", callback_data="clear_suggestions")],
                    [InlineKeyboardButton("🔙 رجوع", callback_data="support_back")]
                ]
                if len(text_msg) > 4000:
                    chunks = [text_msg[i:i+4000] for i in range(0, len(text_msg), 4000)]
                    for chunk in chunks:
                        await query.message.reply_text(chunk)
                    await query.edit_message_text("<blockquote>💡 تم إرسال الاقتراحات أعلاه</blockquote>",
                        reply_markup=InlineKeyboardMarkup(buttons))
                else:
                    await query.edit_message_text(text_msg, reply_markup=InlineKeyboardMarkup(buttons))
        else:
            user_state[user_id] = {"step": "awaiting_suggest"}
            await query.edit_message_text(
                "<blockquote>💡 الاقتراحات\n\n"
                "✍️ اكتب اقتراحك وسيتم إرساله مباشرة للمطور\n\n"
                "• كل اقتراح يساعدنا على تحسين البوت\n"
                "• سيتم مراجعة اقتراحك بعناية\n\n"
                "اكتب اقتراحك الآن 👇</blockquote>"
            )

    elif data == "clear_suggestions":
        if query.from_user.id != OWNER_ID and not has_perm(query.from_user.id, "view_reports"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        all_suggestions.clear()
        save_settings()
        await query.answer("✅ تم مسح كل الاقتراحات")
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await query.edit_message_text(
            "<blockquote>💡 الاقتراحات\n\n📭 لا توجد اقتراحات حتى الآن</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data="support_back")]
            ])
        )

    elif data.startswith("prev_"):
        if not is_admin(int(user_id)) and not has_perm(int(user_id), "manage_feedback"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        await query.answer()
        parts = data[5:].rsplit("_", 1)
        prev_type = parts[0]
        target_uid = parts[1]

        if prev_type == "report":
            items = [r for r in all_reports if r["user_id"] == target_uid]
            emoji, title = "⚠️", "بلاغات"
        elif prev_type == "suggest":
            items = [r for r in all_suggestions if r["user_id"] == target_uid]
            emoji, title = "💡", "اقتراحات"
        elif prev_type == "bot_review":
            items = [r for r in all_bot_reviews if str(r["user_id"]) == target_uid]
            emoji, title = "⭐", "تقييمات البوت"
        elif prev_type == "station_review":
            items = []
            for sid, info in station_ratings.items():
                for uid_r, stars in info.get("users", {}).items():
                    if uid_r == target_uid:
                        items.append({"sid": sid, "stars": stars})
            emoji, title = "🎙", "تقييمات المحطات"
        else:
            items = []
            emoji, title = "📋", "سجل"

        if not items:
            await query.answer(f"📭 لا توجد {title} سابقة لهذا المستخدم", show_alert=True)
            return

        if prev_type == "station_review":
            text_msg = f"<blockquote>{emoji} {title} السابقة للمستخدم {target_uid}\n\n"
            for i, item in enumerate(items, 1):
                sname = ST_TIMO.get(item["sid"], {}).get("name", item["sid"])
                text_msg += f"{i}. {sname} — {'⭐' * item['stars']} ({item['stars']}/5)\n"
        else:
            text_msg = f"<blockquote>{emoji} {title} السابقة للمستخدم {target_uid} ({len(items)} إجمالي)\n\n"
            for i, item in enumerate(items[-5:], 1):
                text_msg += f"{'─'*15}\n#{i} | {item.get('time','')}\n"
                if prev_type == "bot_review":
                    text_msg += f"⭐ {item.get('score',0)}/10\n💬 {item.get('comment','')}\n\n"
                else:
                    text_msg += f"📝 {item.get('text','')}\n\n"
        text_msg += "</blockquote>"

        try:
            await query.message.reply_text(text_msg)
        except Exception as e:
            logger.error(f"prev_ handler error: {e}")
            await query.answer("❌ حدث خطأ", show_alert=True)

    elif data.startswith("admin_reply_"):
        if not is_admin(int(user_id)) and not has_perm(int(user_id), "manage_feedback"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        # استخراج النوع والمستخدم
        parts = data[len("admin_reply_"):].rsplit("_", 1)
        msg_type = parts[0]  # report / suggest / bot_review / station_review
        target_uid = parts[1]
        type_labels = {
            "report": "بلاغ",
            "suggest": "اقتراح",
            "bot_review": "تقييم البوت",
            "station_review": "تقييم المحطة",
        }
        label = type_labels.get(msg_type, "رسالة")
        user_state[user_id] = {
            "step": "awaiting_admin_reply",
            "reply_target_uid": target_uid,
            "reply_type": msg_type,
            "reply_msg_id": query.message.id,
        }
        await query.answer()
        await query.message.reply_text(
            f"<blockquote>↩️ الرد على {label}\n\n"
            f"اكتب ردك الآن وسيصل للمستخدم فوراً 👇</blockquote>",
            reply_markup=ReplyKeyboardMarkup([["❌ إلغاء"]], resize_keyboard=True)
        )

    elif data.startswith("admin_del_"):
        if not is_admin(int(user_id)) and not has_perm(int(user_id), "manage_feedback"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        try:
            # استخراج target_uid من callback_data
            parts = data[len("admin_del_"):].rsplit("_", 1)
            target_uid = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
            msg_id = query.message.id
            # مسح رسالة التأكيد من عند المستخدم
            if target_uid:
                confirm_id = None
                for k, v in pending_replies.items():
                    if str(v.get("user_id")) == str(target_uid) and k == msg_id:
                        confirm_id = v.get("confirm_msg_id")
                        break
                    # بحث بـ user_id بس لو msg_id مش موجود
                    if str(v.get("user_id")) == str(target_uid):
                        confirm_id = v.get("confirm_msg_id")
                if confirm_id:
                    try:
                        await app.delete_messages(target_uid, confirm_id)
                    except Exception as e:
                        logger.error(f"admin_del confirm msg error: {e}")
            # مسح من عند الأدمن
            await query.message.delete()
            await query.answer("🗑 تم المسح")
        except Exception as e:
            logger.error(f"admin_del error: {e}")
            await query.answer("❌ تعذر المسح", show_alert=True)

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
            status_icon = "✅" if is_on else "❌"
            buttons.append([InlineKeyboardButton(f"{status_icon} {perm_name}", callback_data="noop")])
            buttons.append([
                InlineKeyboardButton("تفعيل", callback_data=f"perm_on_{target_id}_{perm_key}"),
                InlineKeyboardButton("إيقاف", callback_data=f"perm_off_{target_id}_{perm_key}"),
            ])
        buttons.append([
            InlineKeyboardButton("✅ تفعيل الكل", callback_data=f"perm_all_on_{target_id}"),
            InlineKeyboardButton("❌ إيقاف الكل", callback_data=f"perm_all_off_{target_id}")
        ])
        await query.edit_message_text(
            f"<blockquote>👑 صلاحيات: {name}\n\n"
            "✅ = مفعّل  |  ❌ = موقوف</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("perm_on_") or data.startswith("perm_off_"):
        if int(user_id) != OWNER_ID:
            await query.answer("❌ للمطور فقط", show_alert=True)
            return
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        parts = data.split("_")
        action = parts[1]
        target_id = int(parts[2])
        perm_key = "_".join(parts[3:])
        new_val = (action == "on")
        if target_id not in ADMIN_PERMISSIONS:
            ADMIN_PERMISSIONS[target_id] = {}
        ADMIN_PERMISSIONS[target_id][perm_key] = new_val
        save_settings()
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
            status_icon = "✅" if is_on else "❌"
            buttons.append([InlineKeyboardButton(f"{status_icon} {pn}", callback_data="noop")])
            buttons.append([
                InlineKeyboardButton("تفعيل", callback_data=f"perm_on_{target_id}_{pk}"),
                InlineKeyboardButton("إيقاف", callback_data=f"perm_off_{target_id}_{pk}"),
            ])
        buttons.append([
            InlineKeyboardButton("✅ تفعيل الكل", callback_data=f"perm_all_on_{target_id}"),
            InlineKeyboardButton("❌ إيقاف الكل", callback_data=f"perm_all_off_{target_id}")
        ])
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
        save_settings()
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
            status_icon = "✅" if is_on else "❌"
            buttons.append([InlineKeyboardButton(f"{status_icon} {pn}", callback_data="noop")])
            buttons.append([
                InlineKeyboardButton("تفعيل", callback_data=f"perm_on_{target_id}_{pk}"),
                InlineKeyboardButton("إيقاف", callback_data=f"perm_off_{target_id}_{pk}"),
            ])
        buttons.append([
            InlineKeyboardButton("✅ تفعيل الكل", callback_data=f"perm_all_on_{target_id}"),
            InlineKeyboardButton("❌ إيقاف الكل", callback_data=f"perm_all_off_{target_id}")
        ])
        await query.answer("✅ تم تفعيل الكل" if new_val else "❌ تم إيقاف الكل")
        await query.edit_message_reply_markup(InlineKeyboardMarkup(buttons))

    elif data == "backup_download":
        if not is_admin(int(user_id)) and not has_perm(int(user_id), "backup_restore"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        await query.answer()
        await query.message.reply_text("<blockquote>📦 جاري إعداد النسخة الاحتياطية...</blockquote>")
        files = [
            ("/data/user_data.json",               "👥 بيانات المستخدمين"),
            ("/data/settings.json",                "⚙️ الإعدادات"),
            ("/data/required_channels_backup.json","📢 قنوات الاشتراك الإجباري"),
        ]
        sent_count = 0
        errors = []
        for path, label in files:
            if os.path.exists(path):
                try:
                    size_kb = round(os.path.getsize(path) / 1024, 1)
                    await app.send_document(
                        int(user_id),
                        document=path,
                        caption=f"<blockquote>{label}\n📁 {size_kb} KB\n🕐 {time.strftime('%Y-%m-%d %H:%M')}</blockquote>"
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Backup send error for {path}: {e}")
                    errors.append(label)
            else:
                logger.warning(f"Backup file not found: {path}")
        if sent_count > 0:
            msg = f"<blockquote>✅ تم إرسال {sent_count} ملف\n\n💡 احفظهم في مكان آمن"
            if errors:
                msg += f"\n\n⚠️ فشل إرسال: {', '.join(errors)}"
            msg += "</blockquote>"
        else:
            msg = "<blockquote>⚠️ لا توجد ملفات احتياطية حتى الآن\n\nسيتم إنشاؤها تلقائياً عند أول استخدام للبوت</blockquote>"
        await query.message.reply_text(msg)

    elif data == "backup_restore_info":
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await query.edit_message_text(
            "<blockquote>📤 استعادة البيانات\n\n"
            "الطريقة:\n"
            "1️⃣ ابعت الملف اللي عايز تستعيده\n"
            "2️⃣ رد عليه بـ /restore\n\n"
            "الملفات المدعومة:\n"
            "• user_data.json\n"
            "• settings.json\n"
            "• required_channels_backup.json</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data="backup_menu")]
            ])
        )

    elif data == "backup_schedule":
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        sched_status = f"✅ {DAYS_AR.get(backup_schedule_day, '')} الساعة {backup_schedule_time}" if backup_schedule_enabled else "❌ موقوف"
        days_buttons = [
            [InlineKeyboardButton(f"{'✅ ' if backup_schedule_day == d else ''}{name}", callback_data=f"bsched_day_{d}")]
            for d, name in DAYS_AR.items()
        ]
        await query.edit_message_text(
            f"<blockquote>⏰ جدول النسخ التلقائي\n\n"
            f"الحالة: {sched_status}\n"
            f"اختر اليوم:</blockquote>",
            reply_markup=InlineKeyboardMarkup(
                days_buttons + [
                    [InlineKeyboardButton("🕐 تغيير الوقت", callback_data="bsched_time")],
                    [InlineKeyboardButton("✅ تفعيل" if not backup_schedule_enabled else "❌ إيقاف",
                                         callback_data="bsched_toggle")],
                    [InlineKeyboardButton("🔙 رجوع", callback_data="backup_menu")],
                ]
            )
        )

    elif data.startswith("bsched_day_"):
        globals()["backup_schedule_day"] = int(data.split("_")[-1])
        await query.answer()
        save_settings()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        sched_status = f"✅ {DAYS_AR.get(backup_schedule_day, '')} الساعة {backup_schedule_time}" if backup_schedule_enabled else "❌ موقوف"
        days_buttons = [
            [InlineKeyboardButton(f"{'✅ ' if backup_schedule_day == d else ''}{name}", callback_data=f"bsched_day_{d}")]
            for d, name in DAYS_AR.items()
        ]
        await query.edit_message_reply_markup(InlineKeyboardMarkup(
            days_buttons + [
                [InlineKeyboardButton("🕐 تغيير الوقت", callback_data="bsched_time")],
                [InlineKeyboardButton("✅ تفعيل" if not backup_schedule_enabled else "❌ إيقاف",
                                     callback_data="bsched_toggle")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="backup_menu")],
            ]
        ))
        await query.answer(f"✅ تم اختيار {DAYS_AR[backup_schedule_day]}")

    elif data == "bsched_toggle":
        globals()["backup_schedule_enabled"] = not backup_schedule_enabled
        await query.answer()
        save_settings()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        sched_status = f"✅ {DAYS_AR.get(backup_schedule_day, '')} الساعة {backup_schedule_time}" if backup_schedule_enabled else "❌ موقوف"
        days_buttons = [
            [InlineKeyboardButton(f"{'✅ ' if backup_schedule_day == d else ''}{name}", callback_data=f"bsched_day_{d}")]
            for d, name in DAYS_AR.items()
        ]
        await query.edit_message_text(
            f"<blockquote>⏰ جدول النسخ التلقائي\n\nالحالة: {sched_status}\nاختر اليوم:</blockquote>",
            reply_markup=InlineKeyboardMarkup(
                days_buttons + [
                    [InlineKeyboardButton("🕐 تغيير الوقت", callback_data="bsched_time")],
                    [InlineKeyboardButton("✅ تفعيل" if not backup_schedule_enabled else "❌ إيقاف",
                                         callback_data="bsched_toggle")],
                    [InlineKeyboardButton("🔙 رجوع", callback_data="backup_menu")],
                ]
            )
        )

    elif data == "bsched_time":
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        _h, _m = map(int, globals().get("backup_schedule_time", "08:00").split(":"))
        await query.edit_message_text(
            "<blockquote>⏰ تغيير وقت النسخ التلقائي\n\nاستخدم الأزرار:</blockquote>",
            reply_markup=build_time_picker_kb(_h, _m, "bsched")
        )


    elif data == "backup_menu":
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        sched_status = f"✅ {DAYS_AR.get(backup_schedule_day, '')} {backup_schedule_time}" if backup_schedule_enabled else "❌ موقوف"
        await query.edit_message_text(
            "<blockquote>📦 النسخ الاحتياطي والاستعادة\n\n"
            f"🔄 النسخ التلقائي: {sched_status}</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📥 تنزيل النسخة الاحتياطية", callback_data="backup_download")],
                [InlineKeyboardButton("📤 استعادة البيانات", callback_data="backup_restore_info")],
                [InlineKeyboardButton("⏰ جدول النسخ التلقائي", callback_data="backup_schedule")],
            ])
        )

    elif data == "refresh_now":
        await query.answer()
        restart_user_broadcasts(user_id)
        await query.edit_message_text("<blockquote>🔃 تم تحديث بثوثك بنجاح ✅</blockquote>")

    elif data == "refresh_auto":
        await query.answer()
        uid = user_id
        current = auto_refresh_enabled.get(uid, False)
        if current:
            auto_refresh_enabled[uid] = False
            save_settings()
            await query.edit_message_text(
                "<blockquote>🔴 تم إيقاف التحديث التلقائي</blockquote>"
            )
        else:
            user_state[uid] = {"step": "awaiting_refresh_interval"}
            await query.edit_message_text(
                "<blockquote>🔄 التحديث التلقائي\n\nاختر المدة بين كل تحديث:</blockquote>"
            )
            await query.message.reply_text(
                "<blockquote>اختر المدة:</blockquote>",
                reply_markup=ReplyKeyboardMarkup([
                    ["15 دقيقة", "30 دقيقة"],
                    ["ساعة", "ساعتين"],
                    ["3 ساعات", "4 ساعات"],
                    ["5 ساعات"],
                    ["إلغاء"]
                ], resize_keyboard=True)
            )


    elif data.startswith("tp_h_dec_") or data.startswith("tp_h_inc_"):
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        try:
            parts = data.split("_")
            action = parts[2]  # dec or inc
            h, m = int(parts[3]), int(parts[4])
            ttype = parts[5] if len(parts) > 5 else "sched"
            old_time = parts[6] if len(parts) > 6 else ""
        except (IndexError, ValueError):
            await query.answer("❌ خطأ في البيانات", show_alert=True)
            return
        if action == "inc":
            h = (h + 1) % 24
        else:
            h = (h - 1) % 24
        h12 = h % 12 or 12
        period = "🌅 صباحاً" if h < 12 else "🌙 مساءً"
        await query.edit_message_reply_markup(build_time_picker_kb(h, m, ttype, old_time))

    elif data.startswith("tp_m_dec_") or data.startswith("tp_m_inc_"):
        await query.answer()
        try:
            parts = data.split("_")
            action = parts[2]
            h, m = int(parts[3]), int(parts[4])
            ttype = parts[5] if len(parts) > 5 else "sched"
            old_time = parts[6] if len(parts) > 6 else ""
        except (IndexError, ValueError):
            await query.answer("❌ خطأ في البيانات", show_alert=True)
            return
        if action == "inc":
            m = (m + 5) % 60
        else:
            m = (m - 5) % 60
        await query.edit_message_reply_markup(build_time_picker_kb(h, m, ttype, old_time))

    elif data.startswith("tp_period_"):
        await query.answer()
        try:
            parts = data.split("_")
            h, m = int(parts[2]), int(parts[3])
            ttype = parts[4] if len(parts) > 4 else "sched"
            old_time = parts[5] if len(parts) > 5 else ""
        except (IndexError, ValueError):
            await query.answer("❌ خطأ في البيانات", show_alert=True)
            return
        # قلب صباح/مساء
        if h < 12:
            h += 12
        else:
            h -= 12
        await query.edit_message_reply_markup(build_time_picker_kb(h, m, ttype, old_time))

    elif data.startswith("tp_confirm_"):
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        try:
            parts = data.split("_")
            h, m = int(parts[2]), int(parts[3])
            ttype = parts[4] if len(parts) > 4 else "sched"
            old_time = parts[5] if len(parts) > 5 else ""
        except (IndexError, ValueError):
            await query.answer("❌ خطأ في البيانات", show_alert=True)
            return
        time_24 = f"{h:02d}:{m:02d}"
        h12 = h % 12 or 12
        period = "صباحاً" if h < 12 else "مساءً"

        if ttype == "bsched":
            globals()["backup_schedule_time"] = time_24
            save_settings()
            sched_status = f"✅ {DAYS_AR.get(globals().get('backup_schedule_day', 4), '')} الساعة {h12}:{m:02d} {period}" if globals().get("backup_schedule_enabled") else "❌ موقوف"
            await query.edit_message_text(
                f"<blockquote>✅ تم تغيير الوقت إلى {h12}:{m:02d} {period}\n\n⏰ جدول النسخ التلقائي\nالحالة: {sched_status}</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 رجوع", callback_data="backup_schedule")]
                ])
            )
        else:
            # جدول البث
            if old_time in AUTO_SCHEDULE:
                AUTO_SCHEDULE[time_24] = AUTO_SCHEDULE.pop(old_time)
                if old_time in schedule_disabled:
                    schedule_disabled.discard(old_time)
                    schedule_disabled.add(time_24)
                save_settings()
            await query.edit_message_text(
                f"<blockquote>✅ تم تغيير الموعد من {old_time} إلى {h12}:{m:02d} {period}</blockquote>"
            )

    elif data.startswith("edit_time_back_"):
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        old_time = data[len("edit_time_back_"):]
        h, m = map(int, old_time.split(":")) if ":" in old_time else (8, 0)
        await query.edit_message_text(
            "<blockquote>⏰ تعديل موعد البث\n\nاستخدم الأزرار لتغيير الوقت:</blockquote>",
            reply_markup=build_time_picker_kb(h, m, "sched", old_time)
        )

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
            ADMIN_PERMISSIONS.pop(target_id, None)
            save_settings()
            try:
                u = await app.get_users(target_id)
                name = u.first_name
                await app.send_message(
                    target_id,
                    "<blockquote>⚠️ تم إزالة صلاحيات الأدمن منك في بوت أثير القرآن</blockquote>"
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
        await query.answer()
        if query.from_user.id == OWNER_ID or has_perm(query.from_user.id, "view_reports"):
            # الأدمن يشوف قسمين: بلاغات + اقتراحات
            reports_count = len(all_reports)
            suggests_count = len(all_suggestions)
            await query.edit_message_text(
                f"<blockquote>💬 مركز البلاغات والاقتراحات\n\n"
                f"⚠️ البلاغات: {reports_count}\n"
                f"💡 الاقتراحات: {suggests_count}</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"⚠️ البلاغات ({reports_count})", callback_data="admin_view_reports")],
                    [InlineKeyboardButton(f"💡 الاقتراحات ({suggests_count})", callback_data="admin_view_suggests")],
                    [InlineKeyboardButton("🔙 رجوع", callback_data="support_back")],
                ])
            )
        else:
            await query.edit_message_text(
                "<blockquote>💬 تواصل مع الدعم الفني\n\nاختر ما تحتاجه:</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⚠️ الإبلاغ عن مشكلة", callback_data="support_report")],
                    [InlineKeyboardButton("💡 الاقتراحات", callback_data="support_suggest")],
                    [InlineKeyboardButton("🔙 رجوع", callback_data="support_back")],
                ])
            )

    elif data == "admin_view_reports":
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await query.answer()
        if query.from_user.id != OWNER_ID and not has_perm(query.from_user.id, "view_reports"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        if not all_reports:
            await query.edit_message_text(
                "<blockquote>⚠️ البلاغات\n\n📭 لا توجد بلاغات حتى الآن</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 رجوع", callback_data="support_contact")]
                ])
            )
            return
        # عرض كل بلاغ مع زر رد وحذف
        await query.edit_message_text(
            f"<blockquote>⚠️ البلاغات ({len(all_reports)} بلاغ)\n\nاختر بلاغاً للتفاعل معه:</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑 مسح كل البلاغات", callback_data="clear_reports")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="support_contact")],
            ])
        )
        # ابعت كل بلاغ كرسالة منفصلة مع أزرار
        for i, r in enumerate(all_reports, 1):
            uid = r.get('user_id', '')
            report_text = (
                f"<blockquote>⚠️ بلاغ #{i}\n"
                f"📅 {r.get('time','')}\n"
                f"👤 {r.get('name','')} (@{r.get('username','')})\n"
                f"🆔 {uid}\n"
                f"📎 النوع: {r.get('type','')}\n"
                f"📝 {r.get('text','')}</blockquote>"
            )
            try:
                sent = await query.message.reply_text(
                    report_text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("↩️ رد", callback_data=f"admin_reply_report_{uid}"),
                         InlineKeyboardButton("🗑 مسح", callback_data=f"admin_del_report_{uid}")],
                        [InlineKeyboardButton("📋 بلاغاته السابقة", callback_data=f"prev_report_{uid}")]
                    ])
                )
                pending_replies[sent.id] = {"user_id": uid, "type": "report"}
                save_settings()
            except Exception as ex:
                logger.error(f"admin_view_reports send error: {ex}")

    elif data == "admin_view_suggests":
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await query.answer()
        if query.from_user.id != OWNER_ID and not has_perm(query.from_user.id, "view_reports"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        if not all_suggestions:
            await query.edit_message_text(
                "<blockquote>💡 الاقتراحات\n\n📭 لا توجد اقتراحات حتى الآن</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 رجوع", callback_data="support_contact")]
                ])
            )
            return
        await query.edit_message_text(
            f"<blockquote>💡 الاقتراحات ({len(all_suggestions)} اقتراح)\n\nاختر اقتراحاً للتفاعل معه:</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑 مسح كل الاقتراحات", callback_data="clear_suggestions")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="support_contact")],
            ])
        )
        for i, r in enumerate(all_suggestions, 1):
            uid = r.get('user_id', '')
            suggest_text = (
                f"<blockquote>💡 اقتراح #{i}\n"
                f"📅 {r.get('time','')}\n"
                f"👤 {r.get('name','')} (@{r.get('username','')})\n"
                f"🆔 {uid}\n"
                f"📝 {r.get('text','')}</blockquote>"
            )
            try:
                sent = await query.message.reply_text(
                    suggest_text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("↩️ رد", callback_data=f"admin_reply_suggest_{uid}"),
                         InlineKeyboardButton("🗑 مسح", callback_data=f"admin_del_suggest_{uid}")],
                        [InlineKeyboardButton("📋 اقتراحاته السابقة", callback_data=f"prev_suggest_{uid}")]
                    ])
                )
                pending_replies[sent.id] = {"user_id": uid, "type": "suggest"}
                save_settings()
            except Exception as ex:
                logger.error(f"admin_view_suggests send error: {ex}")

    elif data == "support_ratings":
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        if query.from_user.id == OWNER_ID or has_perm(query.from_user.id, "view_reviews"):
            reviews_count = len(all_bot_reviews)
            await query.edit_message_text(
                f"<blockquote>⭐ تقييمات البوت ({reviews_count} تقييم)</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🗑 مسح كل التقييمات", callback_data="clear_reviews")],
                    [InlineKeyboardButton("🔙 رجوع", callback_data="support_back")],
                ])
            )
            if not all_bot_reviews:
                await query.message.reply_text("<blockquote>📭 لا توجد تقييمات حتى الآن</blockquote>")
                return
            for i, r in enumerate(all_bot_reviews, 1):
                uid = str(r.get('user_id', ''))
                review_text = (
                    f"<blockquote>⭐ تقييم #{i}\n"
                    f"📅 {r.get('time','')}\n"
                    f"👤 {r.get('name','')} (@{r.get('username','')})\n"
                    f"🆔 {uid}\n"
                    f"⭐ التقييم: {r.get('score',0)}/10\n"
                    f"💬 {r.get('comment','')}</blockquote>"
                )
                try:
                    sent = await query.message.reply_text(
                        review_text,
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("↩️ رد", callback_data=f"admin_reply_bot_review_{uid}"),
                             InlineKeyboardButton("🗑 مسح", callback_data=f"admin_del_bot_review_{uid}")],
                            [InlineKeyboardButton("📋 تقييماته السابقة", callback_data=f"prev_bot_review_{uid}")]
                        ])
                    )
                    pending_replies[sent.id] = {"user_id": uid, "type": "bot_review"}
                    save_settings()
                except Exception as ex:
                    logger.error(f"support_ratings send error: {ex}")
        else:
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
            stars = get_station_rating_stars(r)
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
            stars = get_station_rating_stars(r) if r > 0 else "☆☆☆☆☆"
            buttons.append([InlineKeyboardButton(f"{name}  {stars}", callback_data=f"rate_station_{sid}")])
        buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data="rating_back")])
        await query.edit_message_text(
            f"<blockquote>{cat_name}\nاختر محطة لتقييمها:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

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
            f"التقييم الحالي: {get_station_rating_stars(current)} ({current}/5)\n"
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

    elif data.startswith("give_rate_"):
        parts = data.split("_")
        sid = parts[2]
        stars = int(parts[3])
        uid_str = str(query.from_user.id)
        user_state[user_id] = {
            "step": "awaiting_station_review",
            "rating_station_id": sid,
            "station_stars": stars
        }
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

        if "process" in channel_info:
            try:
                pid = channel_info["process"]
                if is_ffmpeg_running(pid):
                    subprocess.run(["kill", "-9", str(pid)], timeout=5, check=True)
            except Exception as e:
                logger.error(f"Error stopping process: {e}")

        ffmpeg_cmd = build_ffmpeg_cmd(selected_station, channel_info["rtmps_url"])
        logger.info(f"FFmpeg CMD: {' '.join(ffmpeg_cmd)}")
        try:
            stderr_file = open("/data/ffmpeg_error.log", "a")
            stderr_file.write(f"\n{'='*50}\n{time.strftime('%Y-%m-%d %H:%M:%S')}\nCMD: {' '.join(ffmpeg_cmd)}\n")
            stderr_file.flush()
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.DEVNULL,
                stderr=stderr_file
            )
            logger.info(f"FFmpeg PID: {process.pid}")
            user_data[user_id]["channels"][channel_id]["process"] = process.pid
            save_data()
        except Exception as ffmpeg_err:
            logger.error(f"FFmpeg failed to start: {ffmpeg_err}")
            await query.answer(f"❌ فشل تشغيل البث: {ffmpeg_err}", show_alert=True)
            return

        await send_broadcast_notification(client, channel_info['chat_id'], selected_station, user_id)

        station_name_notify = next((v["name"] for v in ST_TIMO.values() if v["url"] == selected_station), "غير معروف")
        if int(user_id) != OWNER_ID and broadcast_notify_enabled:
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


check_cooldown = {}

@app.on_message(filters.command("check") & filters.private)
async def check_command(client, message):
    try:
        user_id = message.from_user.id

        # وضع الصيانة أولاً
        if maintenance_mode and not is_admin(user_id):
            try:
                await message.reply_photo(
                    photo=MAINTENANCE_IMAGE,
                    caption=(
                        "❍─── 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝙰𝚝𝚑𝚎𝚎𝚛 𝙰𝚕-𝚀𝚞𝚛𝚊𝚗 𝙱𝚘𝚝 ───❍\n\n"
                        "⚠️ عذراً عزيزي المستخدم..\n"
                        "البوت الآن في وضع الصيانة لتحديث الخدمات.\n\n"
                        "⏳ يرجى المحاولة مرة أخرى لاحقاً.\n"
                        "────────────────────"
                    ),
                    reply_markup=ReplyKeyboardRemove()
                )
            except Exception:
                await message.reply_text(
                    "⚠️ البوت الآن في وضع الصيانة.\n⏳ يرجى المحاولة مرة أخرى لاحقاً.",
                    reply_markup=ReplyKeyboardRemove()
                )
            return

        last = check_cooldown.get(user_id, 0)
        if time.time() - last < 10:
            remaining = int(10 - (time.time() - last))
            await message.reply_text(
                f"<blockquote>⏳ انتظر {remaining} ثانية قبل إعادة المحاولة</blockquote>"
            )
            return
        check_cooldown[user_id] = time.time()

        unsubscribed = await check_subscription(client, user_id)
        if unsubscribed:
            await send_subscription_message(message, unsubscribed)
        else:
            await message.reply_text(
                "✅ تم التحقق! يمكنك الآن استخدام البوت.",
                reply_markup=user_keyboard(user_id) if not is_admin(user_id) else admin_keyboard(user_id)
            )
    except Exception as e:
        logger.error(f"Check command error: {e}")

@app.on_message(filters.command("backup") & filters.private)
async def backup_command(client, message):
    """أمر /backup — للمطور والأدمن المخوّل فقط"""
    uid = message.from_user.id
    if uid != OWNER_ID and not has_perm(uid, "backup_restore"):
        return
    try:
        await message.reply_text("<blockquote>📦 جاري إعداد النسخة الاحتياطية...</blockquote>")
        files = [
            ("/data/user_data.json",              "👥 بيانات المستخدمين"),
            ("/data/settings.json",               "⚙️ الإعدادات"),
            ("/data/required_channels_backup.json","📢 قنوات الاشتراك الإجباري"),
        ]
        sent_count = 0
        for path, label in files:
            if os.path.exists(path):
                size = os.path.getsize(path)
                size_kb = round(size / 1024, 1)
                await app.send_document(
                    OWNER_ID,
                    document=path,
                    caption=f"<blockquote>{label}\n📁 الحجم: {size_kb} KB\n🕐 {time.strftime('%Y-%m-%d %H:%M')}</blockquote>"
                )
                sent_count += 1
            else:
                await message.reply_text(f"<blockquote>⚠️ الملف غير موجود: {path}</blockquote>")
        await message.reply_text(
            f"<blockquote>✅ تم إرسال {sent_count} ملف بنجاح\n\n"
            "💡 احفظهم في مكان آمن عشان تقدر تستعيد البيانات لو غيرت سيرفر</blockquote>"
        )
    except Exception as e:
        logger.error(f"Backup command error: {e}")
        await message.reply_text(f"<blockquote>❌ حدث خطأ: {e}</blockquote>")

@app.on_message(filters.command("restore") & filters.private)
async def restore_command(client, message):
    """أمر /restore — للمطور والأدمن المخوّل فقط"""
    uid = message.from_user.id
    if uid != OWNER_ID and not has_perm(uid, "backup_restore"):
        return
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.reply_text(
            "<blockquote>📥 طريقة الاستعادة:\n\n"
            "1️⃣ ابعت الملف اللي عايز تستعيده\n"
            "2️⃣ رد عليه بـ /restore\n\n"
            "الملفات المدعومة:\n"
            "• user_data.json\n"
            "• settings.json\n"
            "• required_channels_backup.json</blockquote>"
        )
        return
    try:
        doc = message.reply_to_message.document
        file_name = doc.file_name
        allowed = ["user_data.json", "settings.json", "required_channels_backup.json"]
        if file_name not in allowed:
            await message.reply_text(
                f"<blockquote>❌ الملف '{file_name}' غير مدعوم\n\n"
                f"الملفات المدعومة: {', '.join(allowed)}</blockquote>"
            )
            return
        save_path = f"/data/{file_name}"
        await message.reply_to_message.download(file_name=save_path)
        # reload
        if file_name == "user_data.json":
            load_data()
            await message.reply_text("<blockquote>✅ تم استعادة بيانات المستخدمين بنجاح 🎉</blockquote>")
        elif file_name == "settings.json":
            load_settings()
            await message.reply_text("<blockquote>✅ تم استعادة الإعدادات بنجاح 🎉</blockquote>")
        elif file_name == "required_channels_backup.json":
            load_required_channels()
            await message.reply_text("<blockquote>✅ تم استعادة قنوات الاشتراك الإجباري بنجاح 🎉</blockquote>")
    except Exception as e:
        logger.error(f"Restore command error: {e}")
        await message.reply_text(f"<blockquote>❌ حدث خطأ أثناء الاستعادة: {e}</blockquote>")

@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    try:
        user_id = str(message.from_user.id)
        is_new_user = user_id not in user_data

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

        if is_new_user and not is_admin(message.from_user.id) and max_users_enabled:
            if len(user_data) >= max_users_limit:
                await message.reply_text(
                    "<blockquote>⚠️ عذراً، البوت وصل للحد الأقصى من المستخدمين.\nيرجى التواصل مع الأدمن.</blockquote>"
                )
                return

        if maintenance_mode and not is_admin(message.from_user.id):
            try:
                await message.reply_photo(
                    photo=MAINTENANCE_IMAGE,
                    caption=(
                        "❍─── 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝙰𝚝𝚑𝚎𝚎𝚛 𝙰𝚕-𝚀𝚞𝚛𝚊𝚗 𝙱𝚘𝚝 ───❍\n\n"
                        "⚠️ عذراً عزيزي المستخدم..\n"
                        "البوت الآن في وضع الصيانة لتحديث الخدمات.\n\n"
                        "⏳ يرجى المحاولة مرة أخرى لاحقاً.\n"
                        "────────────────────"
                    ),
                    reply_markup=ReplyKeyboardRemove()
                )
            except Exception:
                await message.reply_text(
                    "❍─── 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝙰𝚝𝚑𝚎𝚎𝚛 𝙰𝚕-𝚀𝚞𝚛𝚊𝚗 𝙱𝚘𝚝 ───❍\n\n"
                    "⚠️ عذراً عزيزي المستخدم..\n"
                    "البوت الآن في وضع الصيانة لتحديث الخدمات.\n\n"
                    "⏳ يرجى المحاولة مرة أخرى لاحقاً.\n"
                    "────────────────────",
                    reply_markup=ReplyKeyboardRemove()
                )
            return

        if not is_admin(message.from_user.id):
            try:
                unsubscribed = await check_subscription(client, message.from_user.id)
                if unsubscribed:
                    await send_subscription_message(message, unsubscribed)
                    return
            except Exception as sub_err:
                logger.error(f"Subscription check error in start: {sub_err}")

        if is_new_user:
            user_data[user_id] = {
                "channels": {},
                "temp_station": None,
                "join_date": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            save_data()

        if is_admin(message.from_user.id):
            keyboard = admin_keyboard(user_id)
        else:
            keyboard = user_keyboard(user_id)

        if is_admin(message.from_user.id):
            caption = (
                "<blockquote>👑 أهلاً بك يا مديرنا الكريم\n"
                "• لوحة تحكم بوت أثير القرآن\n"
                "• المطور: 𝑨𝒃𝒐 𝑵𝒖𝒘𝒂𝒇</blockquote>"
            )
        else:
            caption = (
                "<blockquote>• مرحبا بك " + message.from_user.first_name + "\n"
                "• في بوت أثير القرآن\n"
                "• المقدم من المطور 𝑨𝒃𝒐 𝑵𝒖𝒘𝒂𝒇</blockquote>"
            )
        try:
            await message.reply_photo(
                photo=IMAGE_TIMO,
                caption=caption,
                reply_markup=keyboard
            )
        except Exception:
            await message.reply_text(
                caption,
                reply_markup=keyboard
            )

        if is_new_user:
            await notify_new_user(
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name
            )
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

        if maintenance_mode and not is_admin(int(user_id)):
            try:
                await message.reply_photo(
                    photo=MAINTENANCE_IMAGE,
                    caption=(
                        "❍─── 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝙰𝚝𝚑𝚎𝚎𝚛 𝙰𝚕-𝚀𝚞𝚛𝚊𝚗 𝙱𝚘𝚝 ───❍\n\n"
                        "⚠️ عذراً عزيزي المستخدم..\n"
                        "البوت الآن في وضع الصيانة لتحديث الخدمات.\n\n"
                        "⏳ يرجى المحاولة مرة أخرى لاحقاً.\n"
                        "────────────────────"
                    ),
                    reply_markup=ReplyKeyboardRemove()
                )
            except Exception:
                await message.reply_text(
                    "❍─── 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝙰𝚝𝚑𝚎𝚎𝚛 𝙰𝚕-𝚀𝚞𝚛𝚊𝚗 𝙱𝚘𝚝 ───❍\n\n"
                    "⚠️ عذراً عزيزي المستخدم..\n"
                    "البوت الآن في وضع الصيانة لتحديث الخدمات.\n\n"
                    "⏳ يرجى المحاولة مرة أخرى لاحقاً.\n"
                    "────────────────────",
                    reply_markup=ReplyKeyboardRemove()
                )
            return

        if not is_admin(int(user_id)):
            try:
                unsubscribed = await check_subscription(client, int(user_id))
                if unsubscribed:
                    await send_subscription_message(message, unsubscribed)
                    return
            except Exception as sub_err:
                logger.error(f"Subscription check error: {sub_err}")

        if text == "إضافة قناة":
            user_state[user_id] = {"step": "awaiting_channel"}
            await message.reply_text(
                "<blockquote>📢 إضافة قناة\n\n"
                "أرسل معرف قناتك بصيغة واحدة من الصيغ التالية:\n\n"
                "• @channel\n"
                "• https://t.me/channel\n\n"
                "⚠️ تأكد أن البوت مضاف مشرفاً في القناة أولاً</blockquote>",
                reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
            )       
        elif text == "بدء البث":
            if user_id not in user_data or not user_data[user_id].get("channels"):
                await message.reply_text("<blockquote> • لم تتم إضافة أي قنوات بعد!</blockquote>")
                return
            user_state[user_id] = {"step": "awaiting_station_for_broadcast"}
            await show_station_categories(message)
                      
        elif text == "🔃 تحديث البثوث":
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            uid = user_id
            auto_ref = auto_refresh_enabled.get(uid, False)
            interval = auto_refresh_interval.get(uid, 30)
            auto_status = f"🟢 مفعّل ({interval}د)" if auto_ref else "🔴 موقوف"
            await message.reply_text(
                "<blockquote>🔃 تحديث البثوث\n\nاختر نوع التحديث:</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔃 تحديث الآن", callback_data="refresh_now")],
                    [InlineKeyboardButton(f"🔄 تحديث تلقائي — {auto_status}", callback_data="refresh_auto")],
                ])
            )

        elif text.startswith("🔄 تحديث تلقائي") or text.startswith("🔄 تلقائي:"):
            uid = user_id
            current = auto_refresh_enabled.get(uid, False)
            if current:
                # إيقاف التلقائي
                auto_refresh_enabled[uid] = False
                await message.reply_text(
                    "<blockquote>🔴 تم إيقاف التحديث التلقائي</blockquote>",
                    reply_markup=user_keyboard(user_id) if not is_admin(int(user_id)) else admin_keyboard(user_id)
                )
            else:
                # تشغيل — اسأله عن المدة
                user_state[uid] = {"step": "awaiting_refresh_interval"}
                await message.reply_text(
                    "<blockquote>🔄 التحديث التلقائي\n\n"
                    "اختر المدة بين كل تحديث:</blockquote>",
                    reply_markup=ReplyKeyboardMarkup([
                        ["15 دقيقة", "30 دقيقة"],
                        ["60 دقيقة", "120 دقيقة"],
                        ["إلغاء"]
                    ], resize_keyboard=True)
                )              
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


        elif user_state.get(user_id, {}).get("step") == "awaiting_channel_deletion":
            if text == "إلغاء":
                user_state.pop(user_id, None)
                await message.reply_text("<blockquote>❌ تم إلغاء العملية</blockquote>",
                    reply_markup=user_keyboard(user_id) if not is_admin(int(user_id)) else admin_keyboard(user_id))
                return
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
            save_settings()
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
            save_settings()
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

        elif user_state.get(user_id, {}).get("step") == "sub_awaiting_add":
            rest = text.strip()
            # استخرج المعرف من الرابط أو اليوزر
            channel_input = rest
            if "t.me/" in rest:
                username = rest.split("t.me/")[-1].split("/")[0].split("?")[0]
                channel_input = "@" + username
            elif not rest.startswith("@"):
                channel_input = "@" + rest

            # نحول لـ numeric id
            try:
                chat_obj = await client.get_chat(channel_input)
                channel_id_add = str(chat_obj.id)
                channel_title = chat_obj.title or channel_input
                # رابط الدعوة من اليوزرنيم
                if chat_obj.username:
                    channel_url_add = f"https://t.me/{chat_obj.username}"
                else:
                    channel_url_add = rest  # لو مش عنده يوزرنيم نحفظ اللي بعته
            except Exception as ex:
                logger.error(f"sub_add get_chat error: {ex}")
                await message.reply_text(
                    "<blockquote>❌ تعذر الوصول إلى القناة\n\n"
                    "تأكد أن:\n"
                    "• البوت عضو في القناة\n"
                    "• المعرف أو الرابط صحيح</blockquote>"
                )
                return

            for ch in REQUIRED_CHANNELS:
                if ch["id"] == channel_id_add:
                    await message.reply_text("<blockquote>⚠️ هذه القناة موجودة بالفعل.</blockquote>")
                    user_state.pop(user_id, None)
                    return

            REQUIRED_CHANNELS.append({"id": channel_id_add, "url": channel_url_add, "custom_text": ""})
            save_required_channels()
            user_state.pop(user_id, None)
            await message.reply_text(
                f"<blockquote>✅ تم إضافة القناة بنجاح\n"
                f"📢 {channel_title}\n"
                f"🆔 {channel_id_add}\n\n"
                f"💡 لو عايز تضيف نص مخصص — اضغط تعديل النص من قائمة الاشتراك الإجباري</blockquote>",
                reply_markup=admin_keyboard(user_id)
            )

        elif user_state.get(user_id, {}).get("step") == "sub_awaiting_edit_text":
            ch_id_edit = user_state[user_id].get("edit_channel_id")
            new_text = text.strip()
            if new_text == "-":
                new_text = ""
            found = False
            for ch in REQUIRED_CHANNELS:
                if ch["id"] == ch_id_edit:
                    ch["custom_text"] = new_text
                    found = True
                    break
            user_state.pop(user_id, None)
            if found:
                save_required_channels()
                if new_text:
                    preview = new_text[:50] + "..." if len(new_text) > 50 else new_text
                    await message.reply_text(f"<blockquote>✅ تم تحديث نص {ch_id_edit}\n📝 النص: {preview}</blockquote>", reply_markup=admin_keyboard(user_id))
                else:
                    await message.reply_text(f"<blockquote>✅ تم حذف النص المخصص من {ch_id_edit}</blockquote>", reply_markup=admin_keyboard(user_id))
            else:
                await message.reply_text("<blockquote>❌ لم يتم العثور على القناة</blockquote>", reply_markup=admin_keyboard(user_id))

        elif user_state.get(user_id, {}).get("step") == "awaiting_new_time":
            # هذه الخطوة بقت تُعالج عبر أزرار timepick — لا يُتوقع وصول نص هنا
            pass

        elif user_state.get(user_id, {}).get("step") == "awaiting_new_station_for_schedule":
            target_time = user_state[user_id].get("target_time")
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
            if text == "إلغاء":
                user_state.pop(user_id, None)
                await message.reply_text("<blockquote>❌ تم إلغاء العملية</blockquote>",
                    reply_markup=admin_keyboard(user_id))
                return
            try:
                target_id = int(text)
                if target_id in ADMIN_ID:
                    await message.reply_text(
                        "<blockquote>⚠️ هذا المستخدم أدمن بالفعل</blockquote>",
                        reply_markup=admin_keyboard(user_id)
                    )
                else:
                    ADMIN_ID.append(target_id)
                    ADMIN_PERMISSIONS[target_id] = {}
                    save_settings()
                    user_state.pop(user_id, None)
                    try:
                        u = await app.get_users(target_id)
                        name = u.first_name
                        await app.send_message(
                            target_id,
                            "<blockquote>👑 تهانينا!\n\nتم رفعك أدمناً في بوت أثير القرآن\nبإمكانك الآن الوصول للوحة التحكم الكاملة</blockquote>"
                        )
                    except Exception as e:
                        logger.error(f"promote admin notify error: {e}")
                        name = str(target_id)
                    await message.reply_text(
                        f"<blockquote>✅ تم رفع {name} أدمناً بنجاح 👑</blockquote>",
                        reply_markup=admin_keyboard(user_id)
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
            if not banned_users:
                await message.reply_text(
                    "<blockquote>✅ لا يوجد مستخدمون محظورون حالياً</blockquote>",
                    reply_markup=admin_keyboard(user_id)
                )
                user_state.pop(user_id, None)
                return
            # بناء قائمة المحظورين مع الاسم واليوزر
            banned_lines = []
            for i, uid in enumerate(banned_users, 1):
                try:
                    u = await app.get_users(int(uid))
                    name = u.first_name or "بدون اسم"
                    username = f"@{u.username}" if u.username else "بدون يوزر"
                    banned_lines.append(f"{i}. 👤 {name}\n    🔗 {username}\n    🆔 {uid}")
                except Exception:
                    banned_lines.append(f"{i}. 🆔 {uid}")
            banned_text = "\n\n".join(banned_lines)
            await message.reply_text(
                f"<blockquote>🚫 المحظورون ({len(banned_users)}):\n\n{banned_text}\n\nأرسل ID المستخدم لرفع الحظر عنه</blockquote>",
                reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
            )

        elif user_state.get(user_id, {}).get("step") == "awaiting_ban_id":
            if text == "إلغاء":
                user_state.pop(user_id, None)
                await message.reply_text("<blockquote>❌ تم إلغاء العملية</blockquote>",
                    reply_markup=admin_keyboard(user_id))
                return
            try:
                target_id = int(text.strip())
                banned_users.add(target_id)
                save_settings()
                user_state.pop(user_id, None)
                await message.reply_text(
                    f"<blockquote>🚫 تم حظر المستخدم {target_id} بنجاح</blockquote>",
                    reply_markup=admin_keyboard(user_id)
                )
                try:
                    await app.send_message(target_id, "<blockquote>🚫 تم حظرك من استخدام هذا البوت.</blockquote>")
                except Exception as e:
                    logger.error(f"ban notify error: {e}")
            except ValueError:
                await message.reply_text("<blockquote>❌ يرجى إدخال ID رقمي صحيح</blockquote>")

        elif user_state.get(user_id, {}).get("step") == "awaiting_unban_id":
            if text == "إلغاء":
                user_state.pop(user_id, None)
                await message.reply_text("<blockquote>❌ تم إلغاء العملية</blockquote>",
                    reply_markup=admin_keyboard(user_id))
                return
            try:
                target_id = int(text.strip())
                if target_id in banned_users:
                    banned_users.discard(target_id)
                    save_settings()
                    user_state.pop(user_id, None)
                    await message.reply_text(
                        f"<blockquote>✅ تم رفع الحظر عن المستخدم {target_id}</blockquote>",
                        reply_markup=admin_keyboard(user_id)
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
            total_users = len(user_data)
            total_channels = sum(len(u.get("channels", {})) for u in list(user_data.values()))
            total_stations = len(ST_TIMO)
            caption = (
                "<blockquote>ℹ️ نبذة عن البوت\n\n"
                "🤖 الاسم: أثير القرآن | Atheer Al-Quran\n"
                "📌 الإصدار: 1.0\n"
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
            save_settings()
            status = "ظاهر للمستخدمين 🟢" if about_bot_visible else "مخفي عن المستخدمين 🔴"
            await message.reply_text(
                f"<blockquote>ℹ️ نبذة عن البوت الآن: {status}</blockquote>",
                reply_markup=admin_keyboard(user_id)
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

        elif text == "📦 نسخ احتياطي":
            if not is_admin(int(user_id)) or not has_perm(int(user_id), "backup_restore"):
                await message.reply_text("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
                return
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            sched_status = f"✅ {DAYS_AR.get(backup_schedule_day, '')} {backup_schedule_time}" if backup_schedule_enabled else "❌ موقوف"
            await message.reply_text(
                "<blockquote>📦 النسخ الاحتياطي والاستعادة\n\n"
                f"🔄 النسخ التلقائي: {sched_status}</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📥 تنزيل النسخة الاحتياطية", callback_data="backup_download")],
                    [InlineKeyboardButton("📤 استعادة البيانات", callback_data="backup_restore_info")],
                    [InlineKeyboardButton("⏰ جدول النسخ التلقائي", callback_data="backup_schedule")],
                ])
            )

        elif text.startswith("📋 التقرير اليومي"):
            if not is_admin(int(user_id)) or not has_perm(int(user_id), "daily_report"):
                await message.reply_text("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
                return
            global daily_report_enabled
            daily_report_enabled = not daily_report_enabled
            save_settings()
            status = "مفعّل 🟢" if daily_report_enabled else "موقوف 🔴"
            await message.reply_text(
                "<blockquote>📋 التقرير اليومي الآن: " + status + "\n"
                + ("✅ سيصلك تقرير كل يوم الساعة 8 صباحاً" if daily_report_enabled else "❌ لن يصلك أي تقرير") + "</blockquote>",
                reply_markup=admin_keyboard(user_id)
            )

        elif text.startswith("🌙 الوضع الليلي"):
            if not is_admin(int(user_id)) or not has_perm(int(user_id), "night_mode"):
                await message.reply_text("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
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

        elif text.startswith("🔔 إشعار الأدمن") or text.startswith("🔕 إشعار الأدمن"):
            if not is_admin(int(user_id)) or not has_perm(int(user_id), "notifications"):
                await message.reply_text("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
                return
            global broadcast_notify_enabled
            broadcast_notify_enabled = not broadcast_notify_enabled
            save_settings()
            status = "مفعّل 🟢" if broadcast_notify_enabled else "مقفول 🔴"
            await message.reply_text(
                "<blockquote>🔔 إشعار الأدمن الآن: " + status + "\n"
                + ("✅ ستصلك إشعارات عند تشغيل أي بث" if broadcast_notify_enabled
                   else "🔕 لن تصلك إشعارات عند تشغيل البثوث") + "</blockquote>",
                reply_markup=admin_keyboard(user_id)
            )

        elif text.startswith("🔔 إشعار القناة") or text.startswith("🔕 إشعار القناة"):
            if not is_admin(int(user_id)):
                return
            global channel_notify_enabled
            channel_notify_enabled = not channel_notify_enabled
            save_settings()
            status = "مفعّل 🟢" if channel_notify_enabled else "مقفول 🔴"
            await message.reply_text(
                "<blockquote>🔔 إشعار القناة الآن: " + status + "\n"
                + ("✅ سيُرسل إشعار للقناة عند بدء كل بث" if channel_notify_enabled
                   else "🔕 لن يُرسل إشعار للقناة عند بدء البث") + "</blockquote>",
                reply_markup=admin_keyboard(user_id)
            )

        elif text == "📢 الاشتراك الإجباري":
            if not is_admin(int(user_id)) or not has_perm(int(user_id), "sub_channels"):
                await message.reply_text("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
                return
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            count = len(REQUIRED_CHANNELS)
            await message.reply_text(
                f"<blockquote>📢 إدارة الاشتراك الإجباري\n\n"
                f"عدد القنوات الحالية: {count}</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ إضافة قناة", callback_data="sub_add")],
                    [InlineKeyboardButton("✏️ تعديل نص قناة", callback_data="sub_edit")],
                    [InlineKeyboardButton("🗑 حذف قناة", callback_data="sub_delete")],
                    [InlineKeyboardButton("📋 عرض القنوات", callback_data="sub_list")],
                ])
            )

        elif text.startswith("🔔 إشعار قناتي") or text.startswith("🔕 إشعار قناتي"):
            current = user_data.get(user_id, {}).get("channel_notify", True)
            new_val = not current
            if user_id not in user_data:
                user_data[user_id] = {}
            user_data[user_id]["channel_notify"] = new_val
            save_data()
            status = "مفعّل 🟢" if new_val else "مقفول 🔴"
            await message.reply_text(
                f"<blockquote>🔔 إشعار قناتك الآن: {status}\n"
                + ("✅ سيُرسل إشعار في قناتك عند بدء البث" if new_val
                   else "🔕 لن يُرسل إشعار في قناتك عند بدء البث") + "</blockquote>",
                reply_markup=admin_keyboard(user_id) if is_admin(int(user_id)) else user_keyboard(user_id)
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
            all_bot_reviews.append({
                "user_id": user_id,
                "name": message.from_user.first_name or "غير معروف",
                "username": message.from_user.username or "بدون يوزر",
                "score": score,
                "comment": comment,
                "type": "نصي",
                "time": time.strftime("%Y-%m-%d %H:%M")
            })
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
                from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                sent = await app.send_message(
                    ADMIN_ID[0], rating_msg,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("↩️ رد", callback_data=f"admin_reply_bot_review_{user_id}"),
                         InlineKeyboardButton("🗑 مسح", callback_data=f"admin_del_bot_review_{user_id}")],
                        [InlineKeyboardButton("📋 تقييماته السابقة", callback_data=f"prev_bot_review_{user_id}")]
                    ])
                )
                pending_replies[sent.id] = {"user_id": user_id, "type": "bot_review"}
                save_settings()
            except Exception as e:
                logger.error(f"Bot review send error: {e}")
            user_state.pop(user_id, None)
            _confirm = await message.reply_text(
                "<blockquote>✅ تم إرسال تقييمك بنجاح 🌸</blockquote>",
                reply_markup=user_keyboard(user_id) if not is_admin(int(user_id)) else admin_keyboard(user_id)
            )
            if _confirm: pending_replies[sent.id]["confirm_msg_id"] = _confirm.id
            save_settings()

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
                from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                sent = await app.send_message(
                    ADMIN_ID[0], rating_msg,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("↩️ رد", callback_data=f"admin_reply_station_review_{user_id}"),
                         InlineKeyboardButton("🗑 مسح", callback_data=f"admin_del_station_review_{user_id}")],
                        [InlineKeyboardButton("📋 تقييماته السابقة", callback_data=f"prev_station_review_{user_id}")]
                    ])
                )
                pending_replies[sent.id] = {"user_id": user_id, "type": "station_review"}
                save_settings()
            except Exception as e:
                logger.error(f"Station review send error: {e}")
            user_state.pop(user_id, None)
            new_avg = get_station_rating(sid)
            count = station_ratings.get(sid, {}).get("count", 0)
            _confirm = await message.reply_text(
                f"<blockquote>✅ تم إرسال تقييمك بنجاح 🌸\n\n"
                f"📻 {station_name}\n"
                f"التقييم الجديد: {get_station_rating_stars(new_avg)} ({new_avg}/5)\n"
                f"عدد المقيّمين: {count}</blockquote>",
                reply_markup=user_keyboard(user_id) if not is_admin(int(user_id)) else admin_keyboard(user_id)
            )
            if _confirm: pending_replies[sent.id]["confirm_msg_id"] = _confirm.id
            save_settings()

        elif text == "إرسال بدون صورة" and user_state.get(user_id, {}).get("step") == "awaiting_suggest_photo":
            suggest_text = user_state[user_id].get("suggest_text", "بدون وصف")
            all_suggestions.append({
                "user_id": user_id,
                "name": message.from_user.first_name or "غير معروف",
                "username": message.from_user.username or "بدون يوزر",
                "text": suggest_text,
                "type": "نصي",
                "time": time.strftime("%Y-%m-%d %H:%M")
            })
            save_settings()
            suggest_msg = (
                "<blockquote>💡 اقتراح جديد\n\n"
                "👤 المستخدم: " + user_id + "\n"
                "📛 الاسم: " + (message.from_user.first_name or "غير معروف") + "\n"
                "🔗 اليوزر: @" + (message.from_user.username or "بدون يوزر") + "\n\n"
                "💡 الاقتراح:\n" + suggest_text + "\n"
                "📸 بدون صورة</blockquote>"
            )
            try:
                from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                sent = await app.send_message(
                    ADMIN_ID[0], suggest_msg,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("↩️ رد", callback_data=f"admin_reply_suggest_{user_id}"),
                         InlineKeyboardButton("🗑 مسح", callback_data=f"admin_del_suggest_{user_id}")],
                        [InlineKeyboardButton("📋 اقتراحاته السابقة", callback_data=f"prev_suggest_{user_id}")]
                    ])
                )
                pending_replies[sent.id] = {"user_id": user_id, "type": "suggest"}
                save_settings()
            except Exception as e:
                logger.error(f"Suggest send error: {e}")
            user_state.pop(user_id, None)
            _confirm = await message.reply_text(
                "<blockquote>✅ تم إرسال اقتراحك بنجاح 🌸\nشكراً لمساهمتك في تحسين البوت</blockquote>",
                reply_markup=user_keyboard(user_id) if not is_admin(int(user_id)) else admin_keyboard(user_id)
            )
            if _confirm: pending_replies[sent.id]["confirm_msg_id"] = _confirm.id
            save_settings()

        elif text == "❌ إلغاء" and user_state.get(user_id, {}).get("step") in ("awaiting_bot_review", "awaiting_bot_review_photo", "awaiting_station_review", "awaiting_station_review_photo", "awaiting_report", "awaiting_suggest", "awaiting_suggest_photo", "awaiting_admin_reply"):
            user_state.pop(user_id, None)
            await message.reply_text(
                "<blockquote>❌ تم إلغاء العملية</blockquote>",
                reply_markup=user_keyboard(user_id) if not is_admin(int(user_id)) else admin_keyboard(user_id)
            )

        elif user_state.get(user_id, {}).get("step") == "awaiting_admin_reply":
            if not is_admin(int(user_id)):
                return
            target_uid = user_state[user_id].get("reply_target_uid")
            reply_type = user_state[user_id].get("reply_type", "")
            type_labels = {
                "report": "بلاغك",
                "suggest": "اقتراحك",
                "bot_review": "تقييمك للبوت",
                "station_review": "تقييمك للمحطة",
            }
            label = type_labels.get(reply_type, "رسالتك")
            reply_msg = (
                f"<blockquote>📩 رد من إدارة البوت بخصوص {label}:\n\n"
                f"{text}</blockquote>"
            )
            try:
                await app.send_message(int(target_uid), reply_msg)
                user_state.pop(user_id, None)
                await message.reply_text(
                    "<blockquote>✅ تم إرسال ردك بنجاح</blockquote>",
                    reply_markup=admin_keyboard(user_id)
                )
            except Exception as e:
                logger.error(f"admin reply send error: {e}")
                await message.reply_text(
                    "<blockquote>❌ تعذر إرسال الرد — تأكد أن المستخدم لم يحظر البوت</blockquote>",
                    reply_markup=admin_keyboard(user_id)
                )
                user_state.pop(user_id, None)

        elif user_state.get(user_id, {}).get("step") == "awaiting_suggest":
            suggest_text = text
            user_state[user_id]["suggest_text"] = suggest_text
            user_state[user_id]["step"] = "awaiting_suggest_photo"
            await message.reply_text(
                "<blockquote>✍️ تم استلام اقتراحك\n\n"
                "📸 هل تودّ إرفاق صورة توضيحية؟ (اختياري)</blockquote>",
                reply_markup=ReplyKeyboardMarkup([
                    ["📸 إرسال صورة"],
                    ["إرسال بدون صورة"],
                    ["❌ إلغاء"]
                ], resize_keyboard=True)
            )

        elif user_state.get(user_id, {}).get("step") == "awaiting_report" and text not in ("إرسال بدون صورة", "📸 إرسال صورة", "❌ إلغاء"):
            user_state[user_id]["report_text"] = text
            await message.reply_text(
                "<blockquote>📨 تم استلام بلاغك بنجاح\n\n"
                "سيتم مراجعة مشكلتك والعمل على حلها في أقرب وقت ممكن\n"
                "نقدّر تواصلك ومساعدتك في تحسين البوت 🤍\n\n"
                "📸 هل تودّ إرفاق صورة لتوضيح المشكلة؟ (اختياري)\n"
                "الصورة تساعد المطور على الحل بشكل أسرع 🚀</blockquote>",
                reply_markup=ReplyKeyboardMarkup([["📸 إرسال صورة"], ["إرسال بدون صورة"], ["❌ إلغاء"]], resize_keyboard=True)
            )

        elif text == "📸 إرسال صورة" and user_state.get(user_id, {}).get("step") in ("awaiting_report", "awaiting_bot_review_photo", "awaiting_station_review_photo", "awaiting_suggest_photo"):
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
            all_reports.append({
                "user_id": user_id,
                "name": message.from_user.first_name or "غير معروف",
                "username": message.from_user.username or "بدون يوزر",
                "text": report_text_content,
                "type": "نصي",
                "time": time.strftime("%Y-%m-%d %H:%M")
            })
            try:
                from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                sent = await app.send_message(
                    ADMIN_ID[0], report_msg,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("↩️ رد", callback_data=f"admin_reply_report_{user_id}"),
                         InlineKeyboardButton("🗑 مسح", callback_data=f"admin_del_report_{user_id}")],
                        [InlineKeyboardButton("📋 بلاغاته السابقة", callback_data=f"prev_report_{user_id}")]
                    ])
                )
                pending_replies[sent.id] = {"user_id": user_id, "type": "report"}
                save_settings()
            except Exception as e:
                logger.error(f"Report send error: {e}")
            user_state.pop(user_id, None)
            _confirm = await message.reply_text(
                "<blockquote>✅ تم إرسال بلاغك بنجاح 🌸\nسيتم مراجعته والرد عليك في أقرب وقت</blockquote>",
                reply_markup=user_keyboard(user_id) if not is_admin(int(user_id)) else admin_keyboard(user_id)
            )
            if _confirm: pending_replies[sent.id]["confirm_msg_id"] = _confirm.id
            save_settings()

        elif text.startswith("🔓 حد المستخدمين") or text.startswith("🔒 حد المستخدمين"):
            if not is_admin(int(user_id)) or not has_perm(int(user_id), "max_users"):
                await message.reply_text("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
                return
            global max_users_enabled, max_users_limit
            if max_users_enabled:
                max_users_enabled = False
                save_settings()
                await message.reply_text(
                    "<blockquote>🔓 تم إلغاء تفعيل حد المستخدمين\nالبوت مفتوح للجميع الآن</blockquote>",
                    reply_markup=admin_keyboard(user_id)
                )
            else:
                user_state[user_id] = {"step": "awaiting_max_users"}
                await message.reply_text(
                    "<blockquote>🔒 أرسل الحد الأقصى لعدد المستخدمين (مثال: 50)</blockquote>",
                    reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
                )

        elif user_state.get(user_id, {}).get("step") == "awaiting_max_users":
            if text == "إلغاء":
                user_state.pop(user_id, None)
                await message.reply_text("<blockquote>❌ تم إلغاء العملية</blockquote>",
                    reply_markup=admin_keyboard(user_id))
                return
            try:
                limit = int(text)
                if limit < 1:
                    raise ValueError
                max_users_enabled = True
                max_users_limit = limit
                save_settings()
                user_state.pop(user_id, None)
                await message.reply_text(
                    f"<blockquote>✅ تم تفعيل حد المستخدمين\n🔒 الحد الأقصى: {limit} مستخدم</blockquote>",
                    reply_markup=admin_keyboard(user_id)
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
                    reply_markup=admin_keyboard(user_id)
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
                    reply_markup=admin_keyboard(user_id)
                )
            except ValueError:
                await message.reply_text("<blockquote>❌ أدخل رقم صحيح بين 0 و 23</blockquote>")

        elif text == "🔙 رجوع":
            user_state.pop(user_id, None)
            await message.reply_text(
                "<blockquote>🔙 تم الرجوع للقائمة الرئيسية</blockquote>",
                reply_markup=user_keyboard(user_id) if not is_admin(int(user_id)) else admin_keyboard(user_id)
            )

        elif text.startswith("🟢 الآن: البوت يعمل") or text.startswith("🔴 الآن: البوت في وضع الصيانة"):
            if not is_admin(int(user_id)) or not has_perm(int(user_id), "maintenance"):
                await message.reply_text("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
                return
            maintenance_mode = not maintenance_mode
            save_settings()
            if maintenance_mode:
                await message.reply_text(
                    "<blockquote>🔴 تم تفعيل وضع الصيانة\n\n"
                    "• المستخدمون لن يتمكنوا من استخدام البوت الآن\n"
                    "• أنت كأدمن تستطيع الاستخدام بشكل طبيعي</blockquote>",
                    reply_markup=admin_keyboard(user_id)
                )
            else:
                await message.reply_text(
                    "<blockquote>🟢 تم إيقاف وضع الصيانة\n\n"
                    "• البوت الآن متاح لجميع المستخدمين</blockquote>",
                    reply_markup=admin_keyboard(user_id)
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
        elif user_state.get(user_id, {}).get("step") == "awaiting_refresh_interval":
            minutes_map = {
                "15 دقيقة": 15,
                "30 دقيقة": 30,
                "ساعة": 60,
                "ساعتين": 120,
                "3 ساعات": 180,
                "4 ساعات": 240,
                "5 ساعات": 300,
            }
            if text == "إلغاء":
                user_state.pop(user_id, None)
                await message.reply_text(
                    "<blockquote>❌ تم إلغاء العملية</blockquote>",
                    reply_markup=user_keyboard(user_id) if not is_admin(int(user_id)) else admin_keyboard(user_id)
                )
                return
            if text not in minutes_map:
                await message.reply_text("<blockquote>❌ اختر من الأزرار</blockquote>")
                return
            mins = minutes_map[text]
            auto_refresh_enabled[user_id] = True
            auto_refresh_interval[user_id] = mins
            save_settings()
            user_state.pop(user_id, None)
            hours_text = f"{mins // 60} ساعة" if mins >= 60 else f"{mins} دقيقة"
            await message.reply_text(
                f"<blockquote>✅ تم تفعيل التحديث التلقائي\n⏱ كل {hours_text}</blockquote>",
                reply_markup=user_keyboard(user_id) if not is_admin(int(user_id)) else admin_keyboard(user_id)
            )

        elif user_state.get(user_id, {}).get("step") == "awaiting_channel":
            if text == "إلغاء":
                user_state.pop(user_id, None)
                await message.reply_text(
                    "<blockquote>❌ تم إلغاء العملية</blockquote>",
                    reply_markup=user_keyboard(user_id) if not is_admin(int(user_id)) else admin_keyboard(user_id)
                )
                return
            try:
                # استخراج اليوزرنيم من الرابط لو كان t.me
                channel_input = text.strip()
                if "t.me/" in channel_input:
                    # https://t.me/channel_name أو t.me/channel_name
                    username = channel_input.split("t.me/")[-1].split("/")[0].split("?")[0]
                    channel_input = "@" + username
                chat = await client.get_chat(channel_input)
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
                if any(x in err_msg for x in ['USERNAME_INVALID', 'USERNAME_NOT_OCCUPIED',
                                               'PEER_ID_INVALID', 'ResolveUsername',
                                               'CHANNEL_INVALID', 'The ID/username']):
                    friendly = (
                        "<blockquote>⚠️ تعذّر الوصول إلى القناة\n\n"
                        "تأكد من الخطوات التالية:\n\n"
                        "1️⃣ أضف البوت عضواً في قناتك\n"
                        "2️⃣ ارفعه مشرفاً وفعّل له الصلاحيات التالية:\n"
                        "   • إدارة الرسائل كاملة\n"
                        "   • دعوة مستخدمين عبر رابط\n"
                        "   • إدارة البثوث المباشرة\n"
                        "3️⃣ تأكد أن المعرف صحيح مثال: @channel_name\n\n"
                        "ثم أعد المحاولة 🔄</blockquote>"
                    )
                elif any(x in err_msg for x in ['not enough rights', 'CHAT_ADMIN_REQUIRED',
                                                 'can_invite_users', 'privileges']):
                    friendly = (
                        "<blockquote>⚠️ البوت غير مرفوع مشرفاً أو صلاحياته ناقصة\n\n"
                        "لكي يعمل البث بشكل صحيح:\n\n"
                        "1️⃣ اذهب إلى إعدادات قناتك\n"
                        "2️⃣ أضف البوت كمشرف\n"
                        "3️⃣ فعّل له الصلاحيات التالية:\n"
                        "   • إدارة الرسائل كاملة\n"
                        "   • دعوة مستخدمين عبر رابط\n"
                        "   • إدارة البثوث المباشرة\n\n"
                        "ثم أعد المحاولة 🔄</blockquote>"
                    )
                elif err_msg.startswith('<'):
                    friendly = err_msg
                else:
                    friendly = (
                        "<blockquote>⚠️ تعذّر إضافة القناة\n\n"
                        "تأكد أن البوت مضاف ومرفوع مشرفاً بالصلاحيات التالية:\n"
                        "   • إدارة الرسائل كاملة\n"
                        "   • دعوة مستخدمين عبر رابط\n"
                        "   • إدارة البثوث المباشرة\n\n"
                        "ثم أعد المحاولة 🔄</blockquote>"
                    )
                await message.reply_text(
                    friendly,
                    reply_markup=user_keyboard(user_id) if not is_admin(int(user_id)) else admin_keyboard(user_id)
                )
                user_state.pop(user_id, None)        
        elif user_state.get(user_id, {}).get("step") == "awaiting_rtmps":
            if text == "إلغاء":
                user_state.pop(user_id, None)
                await message.reply_text(
                    "<blockquote>❌ تم إلغاء العملية</blockquote>",
                    reply_markup=user_keyboard(user_id) if not is_admin(int(user_id)) else admin_keyboard(user_id)
                )
                return
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
                reply_markup=user_keyboard(user_id) if not is_admin(int(user_id)) else admin_keyboard(user_id)
            )
        elif user_state.get(user_id, {}).get("step") == "awaiting_station_for_broadcast":
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
                ffmpeg_cmd = build_ffmpeg_cmd(selected_station, channel_info["rtmps_url"])
                process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                user_data[user_id]["channels"][channel_id]["process"] = process.pid
                save_data()                
                await send_broadcast_notification(client, channel_info['chat_id'], selected_station, user_id)
                if int(user_id) != OWNER_ID and broadcast_notify_enabled:
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
                    reply_markup=user_keyboard(user_id) if not is_admin(int(user_id)) else admin_keyboard(user_id)
                )            
            except (ValueError, IndexError):
                await message.reply_text("<blockquote> • رقم قناة غير صحيح!</blockquote>")
                user_state.pop(user_id, None)
    except Exception as e:
        logger.error(f"Text handling error: {str(e)}")
        await message.reply_text("حدث خطأ، الرجاء المحاولة لاحقًا")


@app.on_message(filters.photo & filters.private)
async def handle_photo(client, message):
    user_id = str(message.from_user.id)
    step = user_state.get(user_id, {}).get("step")

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
        all_reports.append({
            "user_id": user_id,
            "name": message.from_user.first_name or "غير معروف",
            "username": message.from_user.username or "بدون يوزر",
            "text": final_text,
            "type": "بصورة",
            "time": time.strftime("%Y-%m-%d %H:%M")
        })
        try:
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            sent = await app.send_photo(
                ADMIN_ID[0], photo=message.photo.file_id, caption=report_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ رد", callback_data=f"admin_reply_report_{user_id}"),
                     InlineKeyboardButton("🗑 مسح", callback_data=f"admin_del_report_{user_id}")],
                    [InlineKeyboardButton("📋 بلاغاته السابقة", callback_data=f"prev_report_{user_id}")]
                ])
            )
            pending_replies[sent.id] = {"user_id": user_id, "type": "report"}
            save_settings()
        except Exception as e:
            logger.error(f"Photo report error: {e}")
        user_state.pop(user_id, None)
        _confirm = await message.reply_text(
            "<blockquote>✅ تم إرسال بلاغك مع الصورة بنجاح 🌸\nسيتم مراجعته والرد عليك في أقرب وقت</blockquote>",
            reply_markup=user_keyboard(user_id) if not is_admin(int(user_id)) else admin_keyboard(user_id)
        )
        if _confirm: pending_replies[sent.id]["confirm_msg_id"] = _confirm.id
        save_settings()

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
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            sent = await app.send_photo(
                ADMIN_ID[0], photo=message.photo.file_id, caption=rating_msg,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ رد", callback_data=f"admin_reply_bot_review_{user_id}"),
                     InlineKeyboardButton("🗑 مسح", callback_data=f"admin_del_bot_review_{user_id}")],
                    [InlineKeyboardButton("📋 تقييماته السابقة", callback_data=f"prev_bot_review_{user_id}")]
                ])
            )
            pending_replies[sent.id] = {"user_id": user_id, "type": "bot_review"}
            save_settings()
        except Exception as e:
            logger.error(f"Bot rating photo error: {e}")
        user_state.pop(user_id, None)
        _confirm = await message.reply_text(
            "<blockquote>✅ تم إرسال تقييمك بنجاح 🌸</blockquote>",
            reply_markup=user_keyboard(user_id) if not is_admin(int(user_id)) else admin_keyboard(user_id)
        )
        if _confirm: pending_replies[sent.id]["confirm_msg_id"] = _confirm.id
        save_settings()

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
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            sent = await app.send_photo(
                ADMIN_ID[0], photo=message.photo.file_id, caption=rating_msg,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ رد", callback_data=f"admin_reply_station_review_{user_id}"),
                     InlineKeyboardButton("🗑 مسح", callback_data=f"admin_del_station_review_{user_id}")],
                    [InlineKeyboardButton("📋 تقييماته السابقة", callback_data=f"prev_station_review_{user_id}")]
                ])
            )
            pending_replies[sent.id] = {"user_id": user_id, "type": "station_review"}
            save_settings()
        except Exception as e:
            logger.error(f"Station rating photo error: {e}")
        user_state.pop(user_id, None)
        _confirm = await message.reply_text(
            f"<blockquote>✅ تم إرسال تقييمك بنجاح 🌸\n\n"
            f"📻 {station_name}\n"
            f"التقييم الجديد: {get_station_rating_stars(new_avg)} ({new_avg}/5)\n"
            f"عدد المقيّمين: {count}</blockquote>",
            reply_markup=user_keyboard(user_id) if not is_admin(int(user_id)) else admin_keyboard(user_id)
        )
        if _confirm: pending_replies[sent.id]["confirm_msg_id"] = _confirm.id
        save_settings()

    elif step == "awaiting_suggest_photo":
        caption_text = message.caption or ""
        suggest_text = user_state[user_id].get("suggest_text", "") or caption_text or "بدون وصف"
        all_suggestions.append({
            "user_id": user_id,
            "name": message.from_user.first_name or "غير معروف",
            "username": message.from_user.username or "بدون يوزر",
            "text": suggest_text,
            "type": "بصورة",
            "time": time.strftime("%Y-%m-%d %H:%M")
        })
        save_settings()
        suggest_caption = (
            "<blockquote>💡 اقتراح جديد\n\n"
            "👤 المستخدم: " + user_id + "\n"
            "📛 الاسم: " + (message.from_user.first_name or "غير معروف") + "\n"
            "🔗 اليوزر: @" + (message.from_user.username or "بدون يوزر") + "\n\n"
            "💡 الاقتراح:\n" + suggest_text + "</blockquote>"
        )
        try:
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            sent = await app.send_photo(
                ADMIN_ID[0], photo=message.photo.file_id, caption=suggest_caption,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ رد", callback_data=f"admin_reply_suggest_{user_id}"),
                     InlineKeyboardButton("🗑 مسح", callback_data=f"admin_del_suggest_{user_id}")],
                    [InlineKeyboardButton("📋 اقتراحاته السابقة", callback_data=f"prev_suggest_{user_id}")]
                ])
            )
            pending_replies[sent.id] = {"user_id": user_id, "type": "suggest"}
            save_settings()
        except Exception as e:
            logger.error(f"Suggest photo error: {e}")
        user_state.pop(user_id, None)
        _confirm = await message.reply_text(
            "<blockquote>✅ تم إرسال اقتراحك مع الصورة بنجاح 🌸\nشكراً لمساهمتك في تحسين البوت</blockquote>",
            reply_markup=user_keyboard(user_id) if not is_admin(int(user_id)) else admin_keyboard(user_id)
        )
        if _confirm: pending_replies[sent.id]["confirm_msg_id"] = _confirm.id
        save_settings()


def auto_refresh_thread():
    last_refresh = {}
    while True:
        try:
            for uid, enabled in list(auto_refresh_enabled.items()):
                if not enabled:
                    continue
                interval_mins = auto_refresh_interval.get(uid, 30)
                last = last_refresh.get(uid, 0)
                if time.time() - last >= interval_mins * 60:
                    restart_user_broadcasts(uid)
                    last_refresh[uid] = time.time()
                    logger.info(f"Auto refresh for user {uid}")
        except Exception as e:
            logger.error(f"auto_refresh_thread error: {e}")
        time.sleep(60)

async def main():
    global _bot_loop
    _bot_loop = asyncio.get_running_loop()
    logger.info("Bot started...")
    # أوامر للجميع
    await app.set_bot_commands([
        BotCommand("start",   "🚀 تشغيل البوت"),
        BotCommand("check",   "✅ التحقق من الاشتراك الإجباري"),
    ])
    # أوامر إضافية للمطور فقط
    try:
        from pyrogram.types import BotCommandScopeChat
        await app.set_bot_commands([
            BotCommand("start",   "🚀 تشغيل البوت"),
            BotCommand("check",   "✅ التحقق من الاشتراك الإجباري"),
            BotCommand("backup",  "📦 تنزيل نسخة احتياطية من البيانات"),
            BotCommand("restore", "📥 استعادة البيانات — رد على الملف بهذا الأمر"),
        ], scope=BotCommandScopeChat(chat_id=OWNER_ID))
        # نفس الأوامر للأدمنز المخوّلين
        for aid in ADMIN_ID:
            if aid != OWNER_ID and has_perm(aid, "backup_restore"):
                try:
                    await app.set_bot_commands([
                        BotCommand("start",   "🚀 تشغيل البوت"),
                        BotCommand("check",   "✅ التحقق من الاشتراك الإجباري"),
                        BotCommand("backup",  "📦 تنزيل نسخة احتياطية من البيانات"),
                        BotCommand("restore", "📥 استعادة البيانات — رد على الملف بهذا الأمر"),
                    ], scope=BotCommandScopeChat(chat_id=aid))
                except Exception:
                    pass
    except Exception as ex:
        logger.error(f"set_bot_commands owner scope error: {ex}")
    restore_broadcasts()
    threading.Thread(target=scheduled_restart, daemon=True).start()
    threading.Thread(target=run_auto_schedule, daemon=True).start()
    threading.Thread(target=watchdog, daemon=True).start()
    threading.Thread(target=daily_report_thread, daemon=True).start()
    threading.Thread(target=weekly_backup_thread, daemon=True).start()
    threading.Thread(target=night_mode_thread, daemon=True).start()
    threading.Thread(target=subscription_watcher_thread, daemon=True).start()
    threading.Thread(target=tarawih_thread, daemon=True).start()
    threading.Thread(target=auto_refresh_thread, daemon=True).start()

async def on_startup():
    await main()

app.on_startup = on_startup



if __name__ == "__main__":
    logger.info("Starting Radio Bot...")
    app.run()