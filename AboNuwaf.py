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
    "schedule":     "جدول التشغيل التلقائي",
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

def save_admins():
    """حفظ الأدمنز في ملف احتياطي"""
    try:
        admins = [aid for aid in ADMIN_ID if aid != OWNER_ID]
        with open("/data/admins_backup.json", "w") as f:
            import json as _j
            _j.dump(admins, f)
    except Exception as e:
        logger.error(f"save_admins error: {e}")

def load_admins():
    """تحميل الأدمنز من الملف الاحتياطي"""
    global ADMIN_ID
    try:
        if os.path.exists("/data/admins_backup.json"):
            with open("/data/admins_backup.json", "r") as f:
                import json as _j
                admins = _j.load(f)
                for aid in admins:
                    if aid != OWNER_ID and aid not in ADMIN_ID:
                        ADMIN_ID.append(aid)
            logger.info(f"✅ تم تحميل {len(admins)} أدمن")
    except Exception as e:
        logger.error(f"load_admins error: {e}")

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
channel_schedule_enabled = {}  # {channel_id: True/False}
max_users_enabled = False
max_users_limit = 100
broadcast_stats = {}
saved_broadcasts = {}
banned_users = set()
banned_users_data = {}  # {user_id: {"name": "", "username": "", "date": "", "reason": ""}}
whitelist_users = set()  # مستخدمون معفيون من الحظر  # {user_id: {"name": "", "username": "", "date": "", "reason": ""}}
all_reports = []  # حفظ كل البلاغات
all_bot_reviews = []  # حفظ كل تقييمات البوت
all_suggestions = []  # حفظ كل الاقتراحات
broadcast_start_times = {}
auto_refresh_enabled = {}
auto_refresh_interval = {}
pending_replies = {}  # {message_id: {"user_id": uid, "type": "report"|"suggest"|"bot_review"|"station_review"}}
daily_report_enabled = False
daily_report_time = "08:00"
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
    "2": {"name": "إذاعة خواطر الشيخ الشعراوي", "url": "https://serverkw.quran-uni.com:8202/;"},
    "3": {"name": "إذاعة القرآن من القاهرة", "url": "https://stream.radiojar.com/8s5u5tpdtwzuv"},
    "4": {"name": "إذاعة القرآن من مختلف القراء", "url": "https://qurango.net/radio/mix"},
    "5": {"name": "إذاعة السيرة النبوية", "url": "https://qurango.net/radio/fi_zilal_alsiyra"},
    "6": {"name": "إذاعة الرقية الشرعية 1", "url": "https://qurango.net/radio/roqiah"},
    "7": {"name": "إذاعة الرقية الشرعية 2", "url": "https://ia600104.us.archive.org/33/items/mp-3-128-k_202603/%D8%B1%D9%82%D9%8A%D8%A9%20%D8%B4%D8%B1%D8%B9%D9%8A%D8%A9%20%D9%84%D8%B9%D9%84%D8%A7%D8%AC%20%D8%B9%D9%8A%D9%86%20%D9%88%D8%AD%D8%B3%D8%AF%20%D9%88%20%D8%B3%D8%AD%D8%B1%20%D9%84%D8%B4%D9%8A%D8%AE%20%D8%A3%D9%8A%D9%88%D8%A8%20%D9%85%D8%B5%D8%B9%D8%A8%28MP3_128K%29.mp3"},
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
    "20": {"name": "إذاعة بندر بليله", "url": "https://qurango.net/radio/bandar_balilah"},
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
    "🕌 القنوات والمحطات": ["3", "2", "4", "9", "10", "22", "23"],
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

def egypt_now():
    """التوقيت المصري الحالي"""
    return time.gmtime(time.time() + 7200)

def egypt_strftime(fmt="%Y-%m-%d %I:%M %p"):
    """وقت مصر بصيغة 12 ساعة"""
    return time.strftime(fmt, egypt_now()).replace("AM", "ص").replace("PM", "م")

def egypt_date():
    """تاريخ مصر فقط"""
    return time.strftime("%Y-%m-%d", egypt_now())

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
                current_time = time.strftime("%H:%M", time.gmtime(time.time() + 7200))
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
                                ch_info["station"] = TARAWIH_STATION["url"]
                            except Exception as e:
                                logger.error(f"Tarawih error on {ch_id}: {e}")
                    save_data()
        except Exception as e:
            logger.error(f"Tarawih thread error: {e}")
        time.sleep(30)

def night_mode_thread():
    night_active = False
    while True:
        hour = int(time.strftime("%H", time.gmtime(time.time() + 7200)))
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
                        user_data[user_id]["channels"][channel_id]["station"] = night_url
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
        current_time = time.strftime("%H:%M", time.gmtime(time.time() + 7200))
        if current_time == daily_report_time and not sent_today:
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
                    "⏰ " + egypt_date() + "</blockquote>"
                )
                try:
                    asyncio.run_coroutine_threadsafe(
                        app.send_message(ADMIN_ID[0], report), _bot_loop
                    )
                except Exception as e:
                    logger.error(f"Daily report error: {e}")
            sent_today = True
        elif current_time != daily_report_time:
            sent_today = False
        time.sleep(30)

BACKUP_CHANNEL_ID = "@Data_Bot0"
welcome_text = ""  # نص ترحيب مخصص
user_notes = {}  # {user_id: "ملاحظة"}
deleted_users_archive = []  # أرشيف المستخدمين المحذوفين
archive_display_count = 10  # عدد المستخدمين المعروضين في الأرشيف
backup_on_new_users = False  # backup تلقائي عند عدد معين من المستخدمين
backup_user_threshold = 10   # العدد الافتراضي
backup_last_count = 0        # آخر عدد تم عمل backup عنده
weekly_report_enabled = False  # تقرير أسبوعي
auto_cleanup_enabled = False  # تنظيف تلقائي للمستخدمين غير النشطين
auto_cleanup_days = 30  # عدد الأيام قبل الحذف
weekly_report_day = 4   # 0=الاثنين ... 4=الجمعة
weekly_report_time = "08:00"
broadcast_stop_notify = False  # إشعار لما البث يوقف
broadcast_fail_threshold = 3   # عدد مرات الإيقاف قبل التنبيه
broadcast_fail_count = {}      # {channel_id: count}
backup_schedule_enabled = False
backup_schedule_day = 4      # 0=الاثنين ... 4=الجمعة ... 6=الأحد
backup_schedule_time = "08:00"

DAYS_AR = {
    0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء",
    3: "الخميس", 4: "الجمعة", 5: "السبت", 6: "الأحد"
}


def user_night_mode_thread():
    """جدول الوضع الليلي الشخصي - كل قناة لوحدها"""
    last_triggered = {}  # {channel_id: {time: date}}
    while True:
        try:
            current_time = time.strftime("%H:%M", time.gmtime(time.time() + 7200))
            today = time.strftime("%Y-%m-%d", time.gmtime(time.time() + 7200))
            for uid, user_info in list(user_data.items()):
                if not user_info.get("night_mode_enabled", False):
                    continue
                channels = user_info.get("channels", {})
                for channel_id, channel_info in list(channels.items()):
                    # الجدول الليلي لكل قناة: {time: station_id}
                    ch_night_schedule = channel_info.get("night_schedule", {})
                    if not ch_night_schedule:
                        continue
                    if current_time not in ch_night_schedule:
                        continue
                    # تحقق ما اتشغلتش قبل كده النهارده
                    last = last_triggered.get(channel_id, {})
                    if last.get(current_time) == today:
                        continue
                    sid = ch_night_schedule[current_time]
                    station = ST_TIMO.get(sid)
                    if not station:
                        continue
                    try:
                        if "process" in channel_info:
                            pid = channel_info["process"]
                            if is_ffmpeg_running(pid):
                                subprocess.run(["kill", "-9", str(pid)], timeout=5, check=True)
                        ffmpeg_cmd = build_ffmpeg_cmd(station["url"], channel_info["rtmps_url"])
                        process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        user_data[uid]["channels"][channel_id]["process"] = process.pid
                        user_data[uid]["channels"][channel_id]["station"] = station["url"]
                    except Exception as e:
                        logger.error(f"user_night_mode error: {e}")
                    if channel_id not in last_triggered:
                        last_triggered[channel_id] = {}
                    last_triggered[channel_id][current_time] = today
                    save_data()
                    logger.info(f"Channel {channel_id} night schedule: switched to {station['name']} at {current_time}")
        except Exception as e:
            logger.error(f"user_night_mode_thread error: {e}")
        time.sleep(30)

def weekly_report_thread():
    """تقرير أسبوعي"""
    sent_this_week = False
    while True:
        try:
            if weekly_report_enabled:
                now = time.gmtime(time.time() + 7200)
                current_time = time.strftime("%H:%M", now)
                is_right_day = now.tm_wday == weekly_report_day
                if is_right_day and current_time == weekly_report_time and not sent_this_week:
                    total_users = len(user_data)
                    active_broadcasts = sum(
                        1 for u in list(user_data.values())
                        for ch in list(u.get("channels", {}).values())
                        if "process" in ch
                    )
                    report = (
                        f"<blockquote>📊 التقرير الأسبوعي\n\n"
                        f"👥 إجمالي المستخدمين: {total_users}\n"
                        f"📡 البثوث النشطة: {active_broadcasts}\n"
                        f"🚫 المحظورون: {len(banned_users)}\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"📅 {egypt_strftime()}</blockquote>"
                    )
                    try:
                        asyncio.run_coroutine_threadsafe(
                            app.send_message(ADMIN_ID[0], report), _bot_loop
                        )
                    except Exception as e:
                        logger.error(f"Weekly report error: {e}")
                    sent_this_week = True
                elif not is_right_day or current_time != weekly_report_time:
                    sent_this_week = False
        except Exception as e:
            logger.error(f"weekly_report_thread error: {e}")
        time.sleep(30)

def weekly_backup_thread():
    """نسخ احتياطي تلقائي بالجدول المحدد"""
    sent_this_period = False
    while True:
        try:
            if globals().get("backup_schedule_enabled", False):
                now = time.gmtime(time.time() + 7200)
                current_time = time.strftime("%H:%M", now)
                _bsd = globals().get("backup_schedule_day", 4)
                _bst = globals().get("backup_schedule_time", "08:00")
                is_right_day = now.tm_wday == _bsd
                if is_right_day and current_time == _bst and not sent_this_period:
                    async def send_auto_backup():
                        try:
                            await app.send_message(
                                BACKUP_CHANNEL_ID,
                                f"<blockquote>📦 نسخة احتياطية تلقائية\n\nمن بيانات بوت أثير القرآن | Atheer Al-Quran\n\n"
                                f"🗓 التاريخ: {egypt_strftime()}\n"
                                f"━━━━━━━━━━━━━━━━\n"
                                f"👥 المستخدمين: {len(user_data)}\n"
                                f"📢 قنوات الاشتراك: {len(REQUIRED_CHANNELS)}\n"
                                f"🚫 المحظورون: {len(banned_users)}\n"
                                f"━━━━━━━━━━━━━━━━\n"
                                f"🤖 تم الإرسال تلقائياً</blockquote>"
                            )
                            files = [
                                ("/data/user_data.json",               "👥 بيانات المستخدمين"),
                                ("/data/settings.json",                "⚙️ الإعدادات"),
                                ("/data/required_channels_backup.json","📢 قنوات الاشتراك الإجباري"),
                                ("/data/admins_backup.json",              "👑 الأدمنز"),
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
                elif not is_right_day or current_time != _bst:
                    sent_this_period = False
        except Exception as e:
            logger.error(f"weekly_backup_thread error: {e}")
        time.sleep(10)

def save_broadcast_stats_file():
    """حفظ broadcast_stats في ملف"""
    try:
        with open("/data/broadcast_stats.json", "w", encoding="utf-8") as f:
            import json as _j
            _j.dump(broadcast_stats, f, ensure_ascii=False)
        with open("/data/broadcast_start_times.json", "w", encoding="utf-8") as f:
            _j.dump({k: v for k, v in broadcast_start_times.items()}, f)
    except Exception as e:
        logger.error(f"save_broadcast_stats_file error: {e}")

def load_broadcast_stats_file():
    """تحميل broadcast_stats من ملف"""
    global broadcast_stats, broadcast_start_times
    try:
        import json as _j
        if os.path.exists("/data/broadcast_stats.json"):
            with open("/data/broadcast_stats.json", "r", encoding="utf-8") as f:
                broadcast_stats.update(_j.load(f))
        if os.path.exists("/data/broadcast_start_times.json"):
            with open("/data/broadcast_start_times.json", "r", encoding="utf-8") as f:
                broadcast_start_times.update({k: float(v) for k, v in _j.load(f).items()})
    except Exception as e:
        logger.error(f"load_broadcast_stats_file error: {e}")

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
            # أعد تملية broadcast_stats و broadcast_start_times
            station_name = next((v["name"] for v in ST_TIMO.values() if v["url"] == info["station"]), "غير معروف")
            if channel_id not in broadcast_stats:
                broadcast_stats[channel_id] = {
                    "station": station_name,
                    "start_time": egypt_strftime("%Y-%m-%d %I:%M:%S %p").replace("AM", "ص").replace("PM", "م"),
                    "user_id": info["user_id"]
                }
            if channel_id not in broadcast_start_times:
                broadcast_start_times[channel_id] = time.time()
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
        if int(uid) in whitelist_users:
            subscription_violations.pop(uid, None)
            return
        banned_users.add(int(uid))
        try:
            _u = await app.get_users(int(uid))
            _ban_name = _u.first_name or "غير معروف"
            _ban_username = f"@{_u.username}" if _u.username else "بدون يوزر"
        except Exception:
            _ban_name = "غير معروف"
            _ban_username = "بدون يوزر"
        banned_users_data[str(uid)] = {
            "name": _ban_name,
            "username": _ban_username,
            "date": egypt_strftime(),
            "reason": "تكرار الخروج من قنوات الاشتراك الإجباري"
        }
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
                    [InlineKeyboardButton("💬 تواصل مع الأدمن", url="https://t.me/AboNuwaf",
                disable_web_page_preview=True)],
                    [InlineKeyboardButton("🤖 تواصل عبر البوت", url="https://t.me/AboNuwaf1_bot")]
                ])
            )
        except Exception as e:
            logger.error(f"Ban notify user error: {e}")
        try:
            # جلب بيانات المستخدم
            try:
                user_info = await app.get_users(int(uid))
                user_name = user_info.first_name or "غير معروف"
                if user_info.last_name:
                    user_name += " " + user_info.last_name
                user_username = f"@{user_info.username}" if user_info.username else "بدون يوزر"
            except Exception:
                user_name = "غير معروف"
                user_username = "بدون يوزر"

            # اسم القناة التي خرج منها
            channel_id = unsubscribed.get("id", "غير معروف")
            channel_title = unsubscribed.get("title", None)
            channel_url = unsubscribed.get("url", None)
            if channel_title:
                channel_display = f"{channel_title} ({channel_id})"
            else:
                channel_display = str(channel_id)
            if channel_url:
                channel_display += f"\n🔗 {channel_url}"

            await app.send_message(
                ADMIN_ID[0],
                "<blockquote>🚫 تم حظر مستخدم تلقائياً\n\n"
                "📛 الاسم: " + user_name + "\n"
                "🔗 اليوزر: " + user_username + "\n"
                "👤 ID: " + uid + "\n\n"
                "📢 القناة التي خرج منها:\n" + channel_display + "\n\n"
                "السبب: تكرار الخروج من قنوات الاشتراك الإجباري 5 مرات</blockquote>",
                disable_web_page_preview=True
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
                "تحذير " + str(count,
                disable_web_page_preview=True) + " من 5 — "
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

async def _do_ban(message_or_query, admin_uid, target_id, reason, keyboard_func):
    """تنفيذ الحظر وحفظ البيانات"""
    banned_users.add(target_id)
    try:
        u = await app.get_users(target_id)
        ban_name = u.first_name or "غير معروف"
        ban_username = f"@{u.username}" if u.username else "بدون يوزر"
    except Exception:
        ban_name = "غير معروف"
        ban_username = "بدون يوزر"
    banned_users_data[str(target_id)] = {
        "name": ban_name,
        "username": ban_username,
        "date": egypt_strftime(),
        "reason": reason
    }
    save_settings()
    if hasattr(message_or_query, "reply_text"):
        await message_or_query.reply_text(
            f"<blockquote>🚫 تم حظر المستخدم بنجاح\n\n"
            f"👤 {ban_name}\n"
            f"🔗 {ban_username}\n"
            f"🆔 {target_id}\n"
            f"📝 السبب: {reason}</blockquote>",
            reply_markup=keyboard_func(admin_uid)
        )
    else:
        await message_or_query.edit_message_text(
            f"<blockquote>🚫 تم حظر المستخدم بنجاح\n\n"
            f"👤 {ban_name}\n"
            f"🔗 {ban_username}\n"
            f"🆔 {target_id}\n"
            f"📝 السبب: {reason}</blockquote>"
        )
    try:
        await app.send_message(target_id, "<blockquote>🚫 تم حظرك من استخدام هذا البوت.</blockquote>",
                disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"ban notify error: {e}")

def build_bot_stats_text():
    """بناء نص إحصائيات البوت"""
    total_users = len(user_data)
    total_channels = sum(len(u.get("channels", {})) for u in list(user_data.values()))
    active_broadcasts = sum(
        1 for u in list(user_data.values())
        for ch in list(u.get("channels", {}).values())
        if "process" in ch
    )
    total_stations = len(ST_TIMO)
    return (
        f"<blockquote>"
        f"📊 إحصائيات البوت\n\n"
        f"👥 المستخدمين: {total_users}\n"
        f"📢 القنوات: {total_channels}\n"
        f"📡 البثوث النشطة: {active_broadcasts}\n"
        f"🎙 المحطات المتاحة: {total_stations}\n"
        f"🚫 المحظورون: {len(banned_users)}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📅 {egypt_strftime()}"
        f"</blockquote>"
    )


@app.on_message(filters.service & filters.private)
async def handle_service(client, message):
    pass

async def notify_user_blocked(user_id):
    """إشعار الأدمن لما مستخدم يحظر البوت"""
    try:
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        try:
            u = await app.get_users(int(user_id))
            uname = u.first_name or "غير معروف"
            uusername = f"@{u.username}" if u.username else "بدون يوزر"
            user_link = get_user_link(user_id, u.username if u.username else None)
        except Exception:
            uname = str(user_id)
            uusername = "بدون يوزر"
            user_link = get_user_link(user_id)

        text = (
            f"<blockquote>🚫 مستخدم حظر البوت\n\n"
            f"👤 الاسم: {uname}\n"
            f"🔗 اليوزر: {uusername}\n"
            f"🆔 المعرف: {user_id}\n"
            f"📅 الوقت: {egypt_strftime()}</blockquote>"
        )
        await app.send_message(
            ADMIN_ID[0], text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"👤 {uname}", url=user_link,
                disable_web_page_preview=True)]
            ])
        )
    except Exception as e:
        logger.error(f"notify_user_blocked error: {e}")


_original_send_message = None

async def send_no_preview(chat_id, text, **kwargs):
    """send_message مع إيقاف الـ preview تلقائياً"""
    if 'disable_web_page_preview' not in kwargs:
        kwargs['disable_web_page_preview'] = True
    return await app.send_message(chat_id, text, **kwargs)


# دليل استخدام البوت - الخطوات
GUIDE_STEPS = [
    {
        "title": "📡 طريقة تشغيل البث المباشر في قناتك",
        "text": (
            "• <b>أولاً:</b> قم بإضافة البوت كـ أدمن في قناتك مع جميع الصلاحيات المطلوبة.\n\n"
            "• <b>بعد ذلك:</b> ارجع للبوت واضغط على <b>إضافة قناة</b> ثم أضف رابط قناتك.\n\n"
            "• سيطلب منك البوت إدخال رابط بث مباشر بصيغة <b>RTMPS</b>."
        ),
        "image": None  # ممكن تضيف رابط صورة هنا
    },
]

def get_user_link(user_id, username=None):
    """بناء رابط المستخدم - لو عنده يوزرنيم يستخدمه، غير كده tg://user"""
    if username:
        return f"https://t.me/{username}"
    return f"tg://user?id={user_id}"


def get_inactive_users():
    """جلب المستخدمين غير النشطين - 0 قنوات ومش بيستخدموا البوت"""
    inactive = []
    now = time.time()
    for uid, user_info in list(user_data.items()):
        if int(uid) in [OWNER_ID] + ADMIN_ID:
            continue
        channels = user_info.get("channels", {})
        if len(channels) > 0:
            continue
        join_date_str = user_info.get("join_date", "")
        try:
            # تحويل التاريخ
            join_date = time.mktime(time.strptime(join_date_str[:19], "%Y-%m-%d %I:%M:%S"))
            days_since = (now - join_date) / 86400
            inactive.append({"uid": uid, "days": int(days_since), "join_date": join_date_str})
        except Exception:
            inactive.append({"uid": uid, "days": 999, "join_date": join_date_str})
    return inactive

def cleanup_inactive_users(days_threshold):
    """حذف المستخدمين غير النشطين مع أرشفتهم"""
    global deleted_users_archive
    inactive = get_inactive_users()
    deleted = 0
    for u in inactive:
        if u["days"] >= days_threshold:
            uid = u["uid"]
            user_info = user_data.get(uid, {})
            # أرشفة قبل الحذف
            deleted_users_archive.append({
                "uid": uid,
                "join_date": user_info.get("join_date", "غير معروف"),
                "deleted_date": egypt_strftime(),
                "broadcast_count": user_info.get("broadcast_count", 0),
                "channels_count": len(user_info.get("channels", {})),
                "days_inactive": u["days"]
            })
            user_data.pop(uid, None)
            deleted += 1
    if deleted > 0:
        save_data()
        save_settings()
    return deleted

def auto_cleanup_thread():
    """تنظيف تلقائي يومي"""
    while True:
        try:
            if auto_cleanup_enabled:
                current_time = time.strftime("%H:%M", time.gmtime(time.time() + 7200))
                if current_time == "03:00":
                    deleted = cleanup_inactive_users(auto_cleanup_days)
                    if deleted > 0:
                        logger.info(f"Auto cleanup: deleted {deleted} inactive users")
                        asyncio.run_coroutine_threadsafe(
                            app.send_message(
                                ADMIN_ID[0],
                                f"<blockquote>🧹 تنظيف تلقائي\n\n"
                                f"تم حذف {deleted} مستخدم غير نشط\n"
                                f"(0 قنوات + أكثر من {auto_cleanup_days} يوم)\n"
                                f"📅 {egypt_strftime()}</blockquote>"
                            ), _bot_loop
                        )
        except Exception as e:
            logger.error(f"auto_cleanup_thread error: {e}")
        time.sleep(60)


def build_adv_settings_msg():
    stop_status = "🟢 مفعّل" if broadcast_stop_notify else "🔴 موقوف"
    weekly_status = "🟢 مفعّل" if weekly_report_enabled else "🔴 موقوف"
    backup_status = f"🟢 كل {backup_user_threshold} مستخدم" if backup_on_new_users else "🔴 موقوف"
    cleanup_status = f"🟢 بعد {auto_cleanup_days} يوم" if auto_cleanup_enabled else "🔴 موقوف"
    text = (
        f"<blockquote>⚙️ الإعدادات المتقدمة\n\n"
        f"⏹ إشعار إيقاف البث: {stop_status}\n"
        f"⚠️ تنبيه فشل البث بعد: {broadcast_fail_threshold} مرات\n"
        f"📊 التقرير الأسبوعي: {weekly_status} — {DAYS_AR.get(weekly_report_day, '')} {weekly_report_time}\n"
        f"📦 Backup عند مستخدمين: {backup_status}\n"
        f"🧹 التنظيف التلقائي: {cleanup_status}</blockquote>"
    )
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏹ إشعار الإيقاف: " + ("إيقاف ✅" if broadcast_stop_notify else "تفعيل ❌"), callback_data="toggle_stop_notify")],
        [InlineKeyboardButton(f"⚠️ حد الفشل: {broadcast_fail_threshold} مرات", callback_data="set_fail_threshold")],
        [InlineKeyboardButton("📊 إدارة التقرير الأسبوعي", callback_data="weekly_report_menu")],
        [InlineKeyboardButton("📦 إدارة الـ Backup", callback_data="backup_manage_menu")],
        [InlineKeyboardButton("🧹 إدارة التنظيف", callback_data="cleanup_menu")],
        [InlineKeyboardButton(f"🗃 الأرشيف ({len(deleted_users_archive)})", callback_data="view_archive")],
        [InlineKeyboardButton("✏️ تخصيص رسالة الترحيب", callback_data="set_welcome_text")],
        [InlineKeyboardButton("🏆 أكثر المستخدمين بثاً", callback_data="top_broadcasters")],
    ])
    return text, kb

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
            "daily_report_time": daily_report_time,
            "max_users_enabled": max_users_enabled,
            "max_users_limit": max_users_limit,
            "about_bot_visible": about_bot_visible,
            "tarawih_enabled": tarawih_enabled,
            "banned_users": list(banned_users),
            "banned_users_data": banned_users_data,
            "whitelist_users": list(whitelist_users),
            "ADMIN_PERMISSIONS": {str(k): v for k, v in ADMIN_PERMISSIONS.items()},
            "ADMIN_ID": [aid for aid in ADMIN_ID if aid != OWNER_ID],
            "station_ratings": station_ratings,
            "all_reports": all_reports,
            "all_bot_reviews": all_bot_reviews,
            "all_suggestions": all_suggestions,
            "subscription_violations": subscription_violations,
            "user_schedule_enabled": user_schedule_enabled,
            "channel_schedule_enabled": channel_schedule_enabled,
            "AUTO_SCHEDULE": AUTO_SCHEDULE,
            "schedule_disabled": list(schedule_disabled),
            "REQUIRED_CHANNELS": REQUIRED_CHANNELS,
            "auto_refresh_enabled": auto_refresh_enabled,
            "auto_refresh_interval": auto_refresh_interval,
            "pending_replies": {str(k): v for k, v in pending_replies.items()},
            "backup_schedule_enabled": backup_schedule_enabled,
            "backup_schedule_day": backup_schedule_day,
            "backup_schedule_time": backup_schedule_time,
            "backup_on_new_users": backup_on_new_users,
            "welcome_text": welcome_text,
            "user_notes": user_notes,
            "deleted_users_archive": deleted_users_archive,
            "archive_display_count": archive_display_count,
            "backup_user_threshold": backup_user_threshold,
            "backup_last_count": backup_last_count,
            "weekly_report_enabled": weekly_report_enabled,
            "auto_cleanup_enabled": auto_cleanup_enabled,
            "auto_cleanup_days": auto_cleanup_days,
            "weekly_report_day": weekly_report_day,
            "weekly_report_time": weekly_report_time,
            "broadcast_stop_notify": broadcast_stop_notify,
            "broadcast_fail_threshold": broadcast_fail_threshold,
            "NIGHT_MODE_STATIONS": NIGHT_MODE_STATIONS,
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
    global daily_report_enabled, daily_report_time, max_users_enabled, max_users_limit, about_bot_visible
    global tarawih_enabled, banned_users, banned_users_data, whitelist_users, ADMIN_PERMISSIONS, ADMIN_ID, station_ratings
    global all_reports, all_bot_reviews, all_suggestions, subscription_violations
    global user_schedule_enabled, channel_schedule_enabled, schedule_disabled, REQUIRED_CHANNELS
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
        daily_report_time = s.get("daily_report_time", "08:00")
        max_users_enabled = s.get("max_users_enabled", False)
        max_users_limit = s.get("max_users_limit", 100)
        about_bot_visible = s.get("about_bot_visible", True)
        tarawih_enabled = s.get("tarawih_enabled", True)
        banned_users = set(s.get("banned_users", []))
        banned_users_data = s.get("banned_users_data", {})
        whitelist_users = set(s.get("whitelist_users", []))
        ADMIN_PERMISSIONS = {int(k): v for k, v in s.get("ADMIN_PERMISSIONS", {}).items()}
        saved_admins = [int(x) for x in s.get("ADMIN_ID", [])]
        for aid in saved_admins:
            if aid != OWNER_ID and aid not in ADMIN_ID:
                ADMIN_ID.append(aid)
        station_ratings = s.get("station_ratings", {})
        all_reports = s.get("all_reports", [])
        all_bot_reviews = s.get("all_bot_reviews", [])
        all_suggestions = s.get("all_suggestions", [])
        subscription_violations = s.get("subscription_violations", {})
        user_schedule_enabled = s.get("user_schedule_enabled", {})
        channel_schedule_enabled = s.get("channel_schedule_enabled", {})
        global AUTO_SCHEDULE
        AUTO_SCHEDULE = s.get("AUTO_SCHEDULE", AUTO_SCHEDULE)
        schedule_disabled = set(s.get("schedule_disabled", []))
        REQUIRED_CHANNELS = s.get("REQUIRED_CHANNELS", [])
        auto_refresh_enabled = s.get("auto_refresh_enabled", {})
        auto_refresh_interval = s.get("auto_refresh_interval", {})
        pending_replies = {int(k): v for k, v in s.get("pending_replies", {}).items()}
        backup_schedule_enabled = s.get("backup_schedule_enabled", False)
        backup_schedule_day = s.get("backup_schedule_day", 4)
        backup_schedule_time = s.get("backup_schedule_time", "08:00")
        global backup_on_new_users, backup_user_threshold, weekly_report_enabled, broadcast_stop_notify, broadcast_fail_threshold
        backup_on_new_users = s.get("backup_on_new_users", False)
        backup_user_threshold = s.get("backup_user_threshold", 10)
        global backup_last_count
        backup_last_count = s.get("backup_last_count", 0)
        weekly_report_enabled = s.get("weekly_report_enabled", False)
        global auto_cleanup_enabled, auto_cleanup_days
        auto_cleanup_enabled = s.get("auto_cleanup_enabled", False)
        global welcome_text
        welcome_text = s.get("welcome_text", "")
        global user_notes
        user_notes = s.get("user_notes", {})
        global deleted_users_archive
        deleted_users_archive = s.get("deleted_users_archive", [])
        global archive_display_count
        archive_display_count = s.get("archive_display_count", 10)
        auto_cleanup_days = s.get("auto_cleanup_days", 30)
        global weekly_report_day, weekly_report_time
        weekly_report_day = s.get("weekly_report_day", 4)
        weekly_report_time = s.get("weekly_report_time", "08:00")
        broadcast_stop_notify = s.get("broadcast_stop_notify", False)
        broadcast_fail_threshold = s.get("broadcast_fail_threshold", 3)
        global NIGHT_MODE_STATIONS
        NIGHT_MODE_STATIONS = s.get("NIGHT_MODE_STATIONS", ["1", "30", "31", "10", "6"])
        logger.info("✅ تم تحميل الإعدادات بنجاح")
    except Exception as e:
        logger.error(f"load_settings error: {e}")

load_data()
load_required_channels()
load_settings()
load_admins()
save_admins()  # عشان يتأكد إن الملف موجود دايماً
load_broadcast_stats_file()

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

    # loop للملفات الصوتية من archive.org
    if "archive.org" in input_url and input_url.endswith(".mp3"):
        cmd += ["-stream_loop", "-1"]

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
        for channel_id, channel_info in list(user_info.get("channels", {}).items()):
            selected_station = channel_info.get("station") or user_info.get("temp_station")
            if not selected_station:
                continue
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
                # حفظ station عشان الـ Watchdog ميرجعش للقديمة
                ch_station = user_data[user_id]["channels"][channel_id].get("station")
                if not ch_station:
                    user_data[user_id]["channels"][channel_id]["station"] = user_data[user_id].get("temp_station", "")
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
                    ch_station = user_data[user_id]["channels"][channel_id].get("station")
                    if not ch_station:
                        user_data[user_id]["channels"][channel_id]["station"] = user_data[user_id].get("temp_station", "")
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
        current_time = time.strftime("%H:%M", time.gmtime(time.time() + 7200))
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
                    # تحقق من إعداد الجدول لكل قناة
                    if not channel_schedule_enabled.get(channel_id, True):
                        continue
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
                        user_data[uid]["channels"][channel_id]["station"] = station["url"]
                        user_data[uid]["temp_station"] = station["url"]
                        switched = True
                    except Exception as e:
                        logger.error(f"Auto schedule error: {e}")
            if switched:
                save_data()
                logger.info(f"Auto schedule: switched to {station['name']}")
                # جمع أسماء القنوات اللي اتغيرت فعلاً
                channel_names = []
                for uid, user_info in list(user_data.items()):
                    if is_admin(int(uid)):
                        if not auto_schedule_enabled:
                            continue
                    else:
                        if not user_schedule_enabled.get(uid, False):
                            continue
                    for ch_id, ch_info in user_info.get("channels", {}).items():
                        if not channel_schedule_enabled.get(ch_id, True):
                            continue
                        if "process" in ch_info:
                            ch_title = ch_info.get("title", ch_id)
                            if ch_title not in channel_names:
                                channel_names.append(ch_title)
                asyncio.run_coroutine_threadsafe(
                    notify_schedule_change(station["name"], channel_names), _bot_loop
                )
        time.sleep(60)

async def notify_schedule_change(station_name, channel_names=None):
    try:
        channels_text = ""
        if channel_names:
            channels_text = "📢 القنوات المتأثرة:\n"
            for ch in channel_names:
                channels_text += f"• {ch}\n"
            channels_text += "\n"
        msg = (
            f"<blockquote>🕐 تغيير تلقائي للمحطة\n\n"
            f"🎙 المحطة الجديدة:\n"
            f"• {station_name}\n\n"
            f"{channels_text}"
            f"━━━━━━━━━━━━━━━━\n"
            f"📅 {egypt_strftime()}</blockquote>"
        )
        await app.send_message(ADMIN_ID[0], msg,
                disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Notify schedule error: {e}")

def watchdog():
    while True:
        try:
            for user_id, user_info in list(user_data.items()):
                channels = user_info.get("channels", {})
                for channel_id, channel_info in list(channels.items()):
                    if "process" not in channel_info:
                        continue
                    # استخدم إذاعة القناة المحددة لو موجودة، غير كده استخدم temp_station
                    selected_station = channel_info.get("station") or user_info.get("temp_station")
                    if not selected_station:
                        continue
                    pid = channel_info["process"]
                    if not is_ffmpeg_running(pid):
                        logger.warning(f"Watchdog: ffmpeg stopped for channel {channel_id}, restarting...")
                        # تنبيه لو البث وقف أكتر من X مرات
                        broadcast_fail_count[channel_id] = broadcast_fail_count.get(channel_id, 0) + 1
                        if broadcast_stop_notify and broadcast_fail_count.get(channel_id, 0) >= broadcast_fail_threshold:
                            broadcast_fail_count[channel_id] = 0
                            ch_title = ""
                            for _u, _uinfo in user_data.items():
                                if channel_id in _uinfo.get("channels", {}):
                                    ch_title = _uinfo["channels"][channel_id].get("title", channel_id)
                                    break
                            try:
                                asyncio.run_coroutine_threadsafe(
                                    app.send_message(
                                        ADMIN_ID[0],
                                        f"<blockquote>⚠️ تنبيه: البث وقف {broadcast_fail_threshold} مرات متتالية\n\n"
                                        f"📢 القناة: {ch_title}\n"
                                        f"📅 {egypt_strftime()}\n\n"
                                        f"قد يكون رابط RTMPS به مشكلة</blockquote>"
                                    ), _bot_loop
                                )
                            except Exception:
                                pass
                        try:
                            ffmpeg_cmd = build_ffmpeg_cmd(selected_station, channel_info["rtmps_url"])
                            process = subprocess.Popen(
                                ffmpeg_cmd,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL
                            )
                            user_data[user_id]["channels"][channel_id]["process"] = process.pid
                            # station محفوظة بالفعل في channel_info
                            logger.info(f"Watchdog: restarted ffmpeg for channel {channel_id}")
                        except Exception as e:
                            logger.error(f"Watchdog restart error: {e}")
            save_data()
            save_broadcast_state()  # حفظ حالة البثوث دوري
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
    total_users = len(user_data)
    user_link = get_user_link(user_id, username)
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    text = (
        f"<blockquote>🆕 مستخدم جديد انضم للبوت!\n\n"
        f"👤 الاسم: {first_name}\n"
        f"🔗 اليوزر: {username_display}\n"
        f"🆔 المعرف: {user_id}\n"
        f"📅 التاريخ: {egypt_strftime()}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"👥 إجمالي المستخدمين: {total_users}</blockquote>"
    )
    try:
        await app.send_message(
            ADMIN_ID[0], text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"👤 {first_name}", url=user_link,
                disable_web_page_preview=True)]
            ])
        )
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

            ch_title = user_data[user_id]["channels"][channel_id].get("title", channel_id)
            del user_data[user_id]["channels"][channel_id]
            save_data()
            await message.reply_text(f"<blockquote> • تم حذف القناة بنجاح</blockquote>")
            # إشعار الأدمن
            if broadcast_notify_enabled and int(user_id) != OWNER_ID:
                try:
                    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                    try:
                        u = await app.get_users(int(user_id))
                        uname = u.first_name or "غير معروف"
                        uusername = f"@{u.username}" if u.username else "بدون يوزر"
                        user_link = get_user_link(user_id, u.username if u.username else None)
                    except Exception:
                        uname = str(user_id)
                        uusername = "بدون يوزر"
                        user_link = get_user_link(user_id)
                    notify_text = (
                        f"<blockquote>🗑 مستخدم حذف قناة\n\n"
                        f"👤 الاسم: {uname}\n"
                        f"🔗 اليوزر: {uusername}\n"
                        f"🆔 المعرف: {user_id}\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"📢 القناة المحذوفة: {ch_title}\n"
                        f"📅 الوقت: {egypt_strftime()}</blockquote>"
                    )
                    row = [InlineKeyboardButton(f"👤 {uname}", url=user_link)]
                    await app.send_message(
                        ADMIN_ID[0], notify_text,
                        reply_markup=InlineKeyboardMarkup([row]),
                        disable_web_page_preview=True
                    )
                except Exception as e:
                    logger.error(f"channel delete notify error: {e}")
        else:
            await message.reply_text("<blockquote> • القناة غير موجودة في قائمتك</blockquote>")
    except Exception as e:
        logger.error(f"Error deleting channel: {e}")
        await message.reply_text("<blockquote> • حدث خطأ أثناء محاولة الحذف</blockquote>")
    
@app.on_message(filters.command(["الاحصائيات"], "") & filters.private)
async def stats_command(client, message):
    if not is_admin(message.from_user.id) or not has_perm(message.from_user.id, "stats"):
        return
    await message.reply(build_bot_stats_text())

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
            await app.send_message(int(user_id), text,
                disable_web_page_preview=True)
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
            await app.send_message(int(channel_id), text,
                disable_web_page_preview=True)
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
    try:
        if not is_admin(message.from_user.id) or not has_perm(message.from_user.id, "view_data"):
            await message.reply("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
            return

        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        # حساب الإجماليات
        total = sum(len(u.get("channels", {})) for u in user_data.values())
        active = sum(1 for u in user_data.values() for ch in u.get("channels", {}).values() if "process" in ch)

        await message.reply(
            f"<blockquote>📢 القنوات\n\n"
            f"📊 الإجمالي: {total} قناة\n"
            f"🟢 نشطة: {active}\n"
            f"🔴 متوقفة: {total - active}</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 بحث", callback_data="ch_search")],
                [InlineKeyboardButton("⚡️ تصفية", callback_data="ch_filter")],
                [InlineKeyboardButton("📋 عرض الكل", callback_data="ch_show_all")],
            ])
        )
    except Exception as e:
        logger.error(f"list_channels_command error: {e}")
        await message.reply("<blockquote>❌ حدث خطأ أثناء جلب البيانات</blockquote>")
    return

async def _show_channels(client, message, filter_type="all", search_query=None):
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    seen_channels = set()
    station_reverse = {v['url']: v['name'] for k, v in ST_TIMO.items()}
    total = 0
    filter_labels = {"all": "📋 الكل", "active": "🟢 البث النشط", "inactive": "🔴 البث المتوقف"}
    await message.reply(f"<blockquote>📢 القنوات — {filter_labels.get(filter_type, '')}{' — نتائج: ' + search_query if search_query else ''}</blockquote>")

    try:
        # ترتيب من الأحدث للأقدم
        sorted_users = sorted(
            user_data.items(),
            key=lambda x: x[1].get("join_date", ""),
            reverse=True
        )
        for uid, user_info in sorted_users:
            if "channels" not in user_info:
                continue

            try:
                owner = await client.get_users(int(uid))
                owner_name = owner.first_name or "غير معروف"
                owner_username = f"@{owner.username}" if owner.username else None
                owner_link = get_user_link(uid, owner.username if owner.username else None)
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
                # تطبيق الفلتر
                is_active = "process" in channel_info
                if filter_type == "active" and not is_active:
                    continue
                if filter_type == "inactive" and is_active:
                    continue
                seen_channels.add(channel_id)
                total += 1

                broadcast_status = "🟢 قيد التشغيل" if 'process' in channel_info else "🔴 متوقف"
                ch_title = channel_info.get('title', 'غير معروف')

                buttons = []
                row = []
                channel_url = None

                try:
                    chat = await client.get_chat(int(channel_id))
                    if chat.username:
                        channel_url = f"https://t.me/{chat.username}"
                    elif chat.invite_link:
                        channel_url = chat.invite_link
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
                if channel_url:
                    row.append(InlineKeyboardButton("📢 دخول القناة", url=channel_url))
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
                    + f"\n🆔 المعرف: {channel_id}"
                    + f"\n━━━━━━━━━━━━━━━━"
                    + f"\n📅 {egypt_strftime()}"
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

async def _show_users(client, message, filter_type="all", search_query=None):
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    filter_labels = {"all": "📋 الكل", "active": "✅ النشطين", "banned": "🚫 المحظورين"}
    await message.reply(f"<blockquote>👥 المستخدمين — {filter_labels.get(filter_type, '')}</blockquote>")
    # ترتيب من الأحدث للأقدم
    sorted_users = sorted(
        user_data.items(),
        key=lambda x: x[1].get("join_date", ""),
        reverse=True
    )
    for uid, user_info in sorted_users:
        is_banned = int(uid) in banned_users
        active_broadcasts = sum(1 for ch in user_info.get("channels", {}).values() if "process" in ch)
        # تطبيق الفلتر
        if filter_type == "active" and active_broadcasts == 0:
            continue
        if filter_type == "banned" and not is_banned:
            continue
        try:
            user = await client.get_users(int(uid))
            name = user.first_name or "بدون اسم"
            if user.last_name:
                name += f" {user.last_name}"
            username = f"@{user.username}" if user.username else "بدون يوزر"
            user_link = get_user_link(uid, user.username if user.username else None)
        except Exception as e:
            logger.error(f"Error fetching user {uid}: {e}")
            name = "غير معروف"
            username = "بدون يوزر"
            user_link = None
        channels_count = len(user_info.get("channels", {}))
        join_date = user_info.get("join_date", "غير معروف")
        broadcast_count = user_info.get("broadcast_count", 0)
        last_seen = user_info.get("last_seen", "غير معروف")
        broadcast_status = f"🟢 {active_broadcasts} بث نشط" if active_broadcasts > 0 else "🔴 لا يوجد بث"
        text_msg = (
            f"<blockquote>"
            f"👤 {name}\n"
            f"🔗 {username}\n"
            f"🆔 {uid}\n"
            f"📅 الانضمام: {join_date}\n"
            f"📢 القنوات: {channels_count}\n"
            f"📡 البث: {broadcast_status}\n"
            f"🎙 إجمالي البثوث: {broadcast_count}\n"
            f"👁 آخر نشاط: {last_seen}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"{'🚫 محظور' if is_banned else '✅ نشط'}"
            f"</blockquote>"
        )
        buttons = []
        row = []
        if user_link:
            row.append(InlineKeyboardButton(f"👤 {name}", url=user_link))
        if is_banned:
            row.append(InlineKeyboardButton("✅ رفع الحظر", callback_data=f"unban_{uid}"))
        else:
            row.append(InlineKeyboardButton("🚫 حظر", callback_data=f"quick_ban_{uid}"))
        if row:
            buttons.append(row)
        await message.reply(
            text_msg,
            reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
        )
        await asyncio.sleep(0.4)
        
@app.on_message(filters.command(["المستخدمين"], "") & filters.private)
async def list_users_command(client, message):
    try:
        if not is_admin(message.from_user.id) or not has_perm(message.from_user.id, "view_data"):
            await message.reply("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
            return

        if not user_data:
            await message.reply("<blockquote> • لا يوجد مستخدمين مسجلين بعد!</blockquote>")
            return

        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        total = len(user_data)
        active = sum(1 for u in user_data.values() for ch in u.get("channels", {}).values() if "process" in ch)

        await message.reply(
            f"<blockquote>👥 المستخدمين\n\n"
            f"📊 الإجمالي: {total} مستخدم\n"
            f"🟢 لديهم بث نشط: {active}\n"
            f"🚫 المحظورون: {len(banned_users)}</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 بحث", callback_data="usr_search")],
                [InlineKeyboardButton("⚡️ تصفية", callback_data="usr_filter")],
                [InlineKeyboardButton("📋 عرض الكل", callback_data="usr_show_all")],
            ])
        )
    except Exception as e:
        logger.error(f"list_users_command error: {e}")
        await message.reply("<blockquote>❌ حدث خطأ أثناء جلب البيانات</blockquote>")
    return

async def _old_list_users(client, message):
    total = len(user_data)
    await message.reply(f"<blockquote>👥 إجمالي المستخدمين: {total}</blockquote>")

    for uid, user_info in list(user_data.items()):
        try:
            user = await client.get_users(int(uid))
            name = user.first_name or "بدون اسم"
            if user.last_name:
                name += f" {user.last_name}"
            username = f"@{user.username}" if user.username else "بدون يوزر"
            user_link = get_user_link(uid, u.username if u.username else None)
        except Exception as e:
            logger.error(f"Error fetching user {uid}: {e}")
            name = "غير معروف"
            username = "بدون يوزر"
            user_link = None

        channels_count = len(user_info.get("channels", {}))
        active_broadcasts = sum(1 for ch in user_info.get("channels", {}).values() if "process" in ch)
        join_date = user_info.get("join_date", "غير معروف")
        broadcast_status = f"🟢 {active_broadcasts} بث نشط" if active_broadcasts > 0 else "🔴 لا يوجد بث"
        is_banned = int(uid) in banned_users

        text = (
            f"<blockquote>"
            f"👤 {name}\n"
            f"🔗 {username}\n"
            f"🆔 {uid}\n"
            f"📅 الانضمام: {join_date}\n"
            f"📢 القنوات: {channels_count}\n"
            f"📡 البث: {broadcast_status}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"{'🚫 الحالة: محظور' if is_banned else '✅ الحالة: نشط'}"
            f"</blockquote>"
        )

        buttons = []
        row = []
        if user_link:
            row.append(InlineKeyboardButton(f"👤 {name}", url=user_link))
        if is_banned:
            row.append(InlineKeyboardButton("✅ رفع الحظر", callback_data=f"unban_{uid}"))
        else:
            row.append(InlineKeyboardButton("🚫 حظر", callback_data=f"quick_ban_{uid}"))
        if row:
            buttons.append(row)

        await message.reply(
            text,
            reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
        )
        await asyncio.sleep(0.4)
        

def user_keyboard(user_id=None):
    user_notify = True
    if user_id and str(user_id) in user_data:
        user_notify = user_data[str(user_id)].get("channel_notify", True)
    notify_btn = "🔔 إشعار قناتي: مفعّل" if user_notify else "🔕 إشعار قناتي: مقفول"
    # زر الوضع الليلي الشخصي
    user_night = False
    if user_id and str(user_id) in user_data:
        user_night = user_data[str(user_id)].get("night_mode_enabled", False)
    night_btn = "🌙 الوضع الليلي: مفعّل ✅" if user_night else "🌙 الوضع الليلي: موقوف ❌"

    rows = [
        ["إضافة قناة", "قنواتي"],
        ["بدء البث", "إيقاف البث"],
        ["🔃 تحديث البثوث", "حذف قناة"],
        ["⚙️ الجدول والمواعيد"],
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
        rows.append(["📊 الإحصائيات"])

    # الإذاعة للمستخدمين والقنوات
    if perm("broadcast_msg"):
        rows.append(["📢 الإذاعة"])

    # عرض البيانات
    if perm("view_data"):
        rows.append(["القنوات", "المستخدمين"])

    # جدول التشغيل التلقائي + الوضع الليلي في زرار واحد
    if perm("schedule") or perm("night_mode"):
        rows.append(["⚙️ الجدول والمواعيد"])

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

    # إشعار الأدمن وإشعار قناتي جنب بعض
    if perm("notifications"):
        rows.append([user_notify_btn, notify_btn])
    else:
        rows.append([user_notify_btn])

    # نبذة عن البوت — للجميع
    rows.append(["ℹ️ نبذة عن البوت", about_btn])

    # الدعم الفني — للجميع
    rows.append(["🛠 الدعم الفني"])

    # إدارة الأدمنز + الحظر في صف واحد
    ban_perm = perm("ban")
    admin_perm = perm("manage_admins")
    if admin_perm and ban_perm:
        rows.append(["👑 إدارة الأدمنز", "🚫 إدارة الحظر"])
    elif admin_perm:
        rows.append(["👑 إدارة الأدمنز"])
    elif ban_perm:
        rows.append(["🚫 إدارة الحظر"])

    rows.append(["📞 تواصل مع الأدمن"])

    # نسخ احتياطي — للمطور والأدمن المخوّل
    if perm("backup_restore"):
        rows.append(["📦 نسخ احتياطي"])
        rows.append(["⚙️ إعدادات متقدمة"])

    rows.append(["الخروج"])

    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def schedule_keyboard():
    return ReplyKeyboardMarkup([
        ["▶️ تشغيل تلقائي", "⏹ إيقاف تلقائي"],
        ["✏️ تعديل موعد", "🎙 تغيير محطة"],
        ["➕ إضافة محطة", "🗑 حذف محطة"],
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
    # Safe access to global vars
    global backup_schedule_time, backup_schedule_day, backup_schedule_enabled
    global all_suggestions, all_reports, all_bot_reviews
    global tarawih_enabled
    global daily_report_time, weekly_report_time, weekly_report_enabled, weekly_report_day
    global auto_cleanup_enabled, broadcast_stop_notify, backup_on_new_users
    global deleted_users_archive, auto_cleanup_days, archive_display_count
    global broadcast_fail_threshold, backup_user_threshold, backup_last_count
    global whitelist_users, channel_schedule_enabled, user_notes, welcome_text
    global NIGHT_MODE_STATIONS, AUTO_SCHEDULE, broadcast_fail_count, night_mode_enabled
    user_id = str(query.from_user.id)
    data = query.data

    # تحديث آخر نشاط عند الضغط على أي زرار
    if user_id in user_data:
        user_data[user_id]["last_seen"] = egypt_strftime()

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
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        if not REQUIRED_CHANNELS:
            await query.edit_message_text("<blockquote>📋 قائمة الاشتراك الإجباري فارغة.</blockquote>")
            return
        await query.edit_message_text(
            f"<blockquote>📋 قنوات الاشتراك الإجباري ({len(REQUIRED_CHANNELS)} قناة)</blockquote>"
        )
        for i, ch in enumerate(REQUIRED_CHANNELS, 1):
            preview = ch.get("custom_text", "")
            preview = (preview[:40] + "...") if len(preview) > 40 else (preview if preview else "افتراضي")
            ch_name = ch.get("url", ch["id"])
            ch_url = ch.get("url", "")
            members_text = "غير متاح"
            adder_name = ""
            adder_username = ""
            adder_url = ""

            try:
                ch_id = int(ch["id"]) if str(ch["id"]).lstrip('-').isdigit() else ch["id"]
                chat_obj = await app.get_chat(ch_id)
                ch_name = chat_obj.title or ch_name
                if chat_obj.username:
                    ch_url = f"https://t.me/{chat_obj.username}"
                if chat_obj.members_count:
                    members_text = str(chat_obj.members_count)
            except Exception:
                pass

            added_by = ch.get("added_by", "")
            if added_by:
                try:
                    adder = await app.get_users(int(added_by))
                    adder_name = adder.first_name or str(added_by)
                    adder_username = f"(@{adder.username})" if adder.username else ""
                    adder_url = f"https://t.me/{adder.username}" if adder.username else ""
                except Exception:
                    adder_name = str(added_by)

            # بناء النص
            text = f"<blockquote>📡 {ch_name}\n👥 الأعضاء: {members_text}\n"
            if adder_name:
                text += f"👤 أضافها: {adder_name} {adder_username}\n"
            text += f"📝 النص: {preview}\n"
            text += f"🔗 الرابط: {ch_url if ch_url else 'غير متاح'}\n"
            text += f"🆔 المعرف: {ch['id']}\n"
            text += f"━━━━━━━━━━━━━━━━\n"
            added_date = ch.get('added_date', 'غير معروف')
            text += f"📅 تاريخ الإضافة: {added_date}</blockquote>"

            # بناء الأزرار
            row = []
            if adder_url:
                row.append(InlineKeyboardButton(f"👤 {adder_name}", url=adder_url))
            if ch_url:
                row.append(InlineKeyboardButton("📢 دخول القناة", url=ch_url))
            
            await query.message.reply_text(
                text,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([row]) if row else None
            )

    elif data == "sub_add":
        await query.answer()
        user_state[user_id] = {"step": "sub_awaiting_add"}
        await query.edit_message_text(
            "<blockquote>➕ إضافة قناة اشتراك إجباري\n\n"
            "أرسل رابط القناة أو معرفها فقط:\n\n"
            "• https://t.me/channel_name\n"
            "• @channel_name\n\n"
            "📝 يوجد نص افتراضي يظهر تلقائياً للمستخدمين\n"
            "💡 لإضافة نص مخصص اضغط تعديل النص بعد الإضافة</blockquote>",
            disable_web_page_preview=True
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

    elif data == "night_manage_stations":
        await query.answer()
        if not is_admin(int(user_id)):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        for sid in NIGHT_MODE_STATIONS:
            if sid in ST_TIMO:
                name = ST_TIMO[sid]["name"].replace("إذاعة ", "").replace("اذاعة ", "").strip()
                buttons.append([InlineKeyboardButton(f"🗑 {name}", callback_data=f"night_del_station_{sid}")])
        buttons.append([InlineKeyboardButton("➕ إضافة محطة ليلية", callback_data="night_add_station")])
        buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data="night_toggle")])
        await query.edit_message_text(
            f"<blockquote>📻 المحطات الليلية ({len(NIGHT_MODE_STATIONS)} محطة)\n\n"
            f"اضغط على المحطة لحذفها أو أضف محطة جديدة:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "night_add_station":
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        for cat_name, station_ids in ST_CATEGORIES.items():
            buttons.append([InlineKeyboardButton(cat_name, callback_data=f"night_add_cat_{cat_name}")])
        await query.edit_message_text(
            "<blockquote>➕ إضافة محطة ليلية\n\nاختر القسم:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("night_add_cat_"):
        cat_name = data[len("night_add_cat_"):]
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        station_ids = ST_CATEGORIES.get(cat_name, [])
        buttons = []
        row = []
        for i, sid in enumerate(station_ids, 1):
            name = ST_TIMO[sid]["name"].replace("إذاعة ", "").replace("اذاعة ", "").replace("قناة ", "").strip()
            already = "✅ " if sid in NIGHT_MODE_STATIONS else ""
            row.append(InlineKeyboardButton(f"{already}{name}", callback_data=f"night_add_pick_{sid}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data="night_manage_stations")])
        await query.edit_message_text(
            f"<blockquote>➕ {cat_name}\n\nاختر المحطة (✅ = موجودة بالفعل):</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("night_add_pick_"):
        sid = data[len("night_add_pick_"):]
        await query.answer()
        if sid in NIGHT_MODE_STATIONS:
            await query.answer("⚠️ المحطة موجودة بالفعل", show_alert=True)
            return
        NIGHT_MODE_STATIONS.append(sid)
        save_settings()
        station_name = ST_TIMO.get(sid, {}).get("name", sid)
        await query.edit_message_text(
            f"<blockquote>✅ تم إضافة {station_name} للمحطات الليلية</blockquote>"
        )

    elif data.startswith("night_del_station_"):
        sid = data[len("night_del_station_"):]
        await query.answer()
        if len(NIGHT_MODE_STATIONS) <= 1:
            await query.answer("⚠️ لازم يكون في محطة واحدة على الأقل", show_alert=True)
            return
        if sid in NIGHT_MODE_STATIONS:
            NIGHT_MODE_STATIONS.remove(sid)
            save_settings()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        for s in NIGHT_MODE_STATIONS:
            if s in ST_TIMO:
                name = ST_TIMO[s]["name"].replace("إذاعة ", "").replace("اذاعة ", "").strip()
                buttons.append([InlineKeyboardButton(f"🗑 {name}", callback_data=f"night_del_station_{s}")])
        buttons.append([InlineKeyboardButton("➕ إضافة محطة ليلية", callback_data="night_add_station")])
        station_name = ST_TIMO.get(sid, {}).get("name", sid)
        await query.edit_message_text(
            f"<blockquote>✅ تم حذف {station_name}\n\n"
            f"📻 المحطات الليلية ({len(NIGHT_MODE_STATIONS)} محطة):</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "night_toggle":
        if not is_admin(int(user_id)):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
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
            parts = data[len("admin_del_"):].rsplit("_", 1)
            dtype = parts[0] if len(parts) > 1 else ""
            target_uid = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
            msg_id = query.message.id

            # مسح من القائمة المناسبة
            if target_uid:
                if "suggest" in dtype:
                    all_suggestions = [s for s in all_suggestions if str(s.get("user_id")) != str(target_uid)]
                    save_settings()
                elif "report" in dtype:
                    all_reports = [r for r in all_reports if str(r.get("user_id")) != str(target_uid)]
                    save_settings()
                elif "review" in dtype:
                    all_bot_reviews = [r for r in all_bot_reviews if str(r.get("user_id")) != str(target_uid)]
                    save_settings()

                # مسح رسالة التأكيد من عند المستخدم
                confirm_id = None
                for k, v in pending_replies.items():
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
                                ("/data/admins_backup.json",              "👑 الأدمنز"),
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
                        caption=f"<blockquote>{label}\n📁 {size_kb} KB\n🕐 {egypt_strftime()}</blockquote>"
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
        _bse = globals().get("backup_schedule_enabled", False)
        _bsd = globals().get("backup_schedule_day", 4)
        _bst = globals().get("backup_schedule_time", "08:00")
        sched_status = f"✅ {DAYS_AR.get(_bsd, '')} الساعة {_bst}" if _bse else "❌ موقوف"
        await query.edit_message_text(
            f"<blockquote>⏰ جدول النسخ التلقائي\n\n"
            f"الحالة: {sched_status}</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 إرسال الآن", callback_data="bsched_send_now")],
                [InlineKeyboardButton("⚙️ تعديل المواعيد", callback_data="bsched_settings")],
                [InlineKeyboardButton("✅ تفعيل" if not _bse else "❌ إيقاف", callback_data="bsched_toggle")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="backup_menu")],
            ])
        )

    elif data == "bsched_send_now":
        await query.answer()
        await query.message.reply_text("<blockquote>📦 جاري إرسال النسخة الاحتياطية...</blockquote>")
        try:
            await app.send_message(
                BACKUP_CHANNEL_ID,
                f"<blockquote>📦 نسخة احتياطية يدوية\n\n"
                f"من بيانات بوت أثير القرآن | Atheer Al-Quran\n\n"
                f"🗓 التاريخ: {egypt_strftime()}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"👥 المستخدمين: {len(user_data)}\n"
                f"📢 قنوات الاشتراك: {len(REQUIRED_CHANNELS)}\n"
                f"🚫 المحظورون: {len(banned_users)}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"👤 تم الإرسال يدوياً</blockquote>"
            )
            files = [
                ("/data/user_data.json",               "👥 بيانات المستخدمين"),
                ("/data/settings.json",                "⚙️ الإعدادات"),
                ("/data/required_channels_backup.json","📢 قنوات الاشتراك الإجباري"),
                                ("/data/admins_backup.json",              "👑 الأدمنز"),
            ]
            for path, label in files:
                if os.path.exists(path):
                    size_kb = round(os.path.getsize(path) / 1024, 1)
                    await app.send_document(
                        BACKUP_CHANNEL_ID,
                        document=path,
                        caption=f"<blockquote>{label}\n📁 {size_kb} KB</blockquote>"
                    )
            await query.message.reply_text("<blockquote>✅ تم الإرسال بنجاح</blockquote>")
        except Exception as ex:
            await query.message.reply_text(f"<blockquote>❌ خطأ: {ex}</blockquote>")

    elif data == "bsched_settings":
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        _bsd = globals().get("backup_schedule_day", 4)
        _bst = globals().get("backup_schedule_time", "08:00")
        _bse = globals().get("backup_schedule_enabled", False)
        days_buttons = [
            [InlineKeyboardButton(f"{'✅ ' if _bsd == d else ''}{name}", callback_data=f"bsched_day_{d}")]
            for d, name in DAYS_AR.items()
        ]
        await query.edit_message_text(
            f"<blockquote>⚙️ تعديل المواعيد\n\nاليوم: {DAYS_AR.get(_bsd, '')}\nالوقت: {_bst}\n\nاختر اليوم:</blockquote>",
            reply_markup=InlineKeyboardMarkup(
                days_buttons + [
                    [InlineKeyboardButton("🕐 تغيير الوقت", callback_data="bsched_time")],
                    [InlineKeyboardButton("🔙 رجوع", callback_data="backup_schedule")],
                ]
            )
        )

    elif data.startswith("bsched_day_"):
        globals()["backup_schedule_day"] = int(data.split("_")[-1])
        await query.answer()
        save_settings()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        _bsd = globals().get("backup_schedule_day", 4)
        _bst = globals().get("backup_schedule_time", "08:00")
        days_buttons = [
            [InlineKeyboardButton(f"{'✅ ' if _bsd == d else ''}{name}", callback_data=f"bsched_day_{d}")]
            for d, name in DAYS_AR.items()
        ]
        await query.edit_message_reply_markup(InlineKeyboardMarkup(
            days_buttons + [
                [InlineKeyboardButton("🕐 تغيير الوقت", callback_data="bsched_time")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="backup_schedule")],
            ]
        ))
        await query.answer(f"✅ تم اختيار {DAYS_AR[globals().get('backup_schedule_day', 4)]}")

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
        elif ttype == "unight_start":
            uid = old_time  # old_time carries uid for user night mode
            if uid in user_data:
                user_data[uid]["night_mode_start"] = time_24
                save_data()
            await query.edit_message_text(
                f"<blockquote>✅ تم تغيير وقت البداية إلى {h12}:{m:02d} {period}</blockquote>"
            )
        elif ttype == "unight_end":
            uid = old_time
            if uid in user_data:
                user_data[uid]["night_mode_end"] = time_24
                save_data()
            await query.edit_message_text(
                f"<blockquote>✅ تم تغيير وقت النهاية إلى {h12}:{m:02d} {period}</blockquote>"
            )
        elif ttype == "daily_report":
            daily_report_time = time_24
            save_settings()
            await query.edit_message_text(
                f"<blockquote>✅ تم تغيير وقت التقرير اليومي إلى {h12}:{m:02d} {period}</blockquote>"
            )
        elif ttype == "wreport":
            weekly_report_time = time_24
            save_settings()
            await query.edit_message_text(
                f"<blockquote>✅ تم تغيير وقت التقرير الأسبوعي\n"
                f"📅 {DAYS_AR.get(weekly_report_day, '')} الساعة {h12}:{m:02d} {period}</blockquote>"
            )
        elif ttype == "unight_sched":
            # old_time = uid_chid_sid
            parts = old_time.split("_", 2)
            _uid = parts[0]
            _ch_id = parts[1] if len(parts) > 1 else ""
            _sid = parts[2] if len(parts) > 2 else "1"
            if _uid in user_data and _ch_id in user_data[_uid].get("channels", {}):
                if "night_schedule" not in user_data[_uid]["channels"][_ch_id]:
                    user_data[_uid]["channels"][_ch_id]["night_schedule"] = {}
                user_data[_uid]["channels"][_ch_id]["night_schedule"][time_24] = _sid
                save_data()
            station_name = ST_TIMO.get(_sid, {}).get("name", _sid)
            ch_title = user_data.get(_uid, {}).get("channels", {}).get(_ch_id, {}).get("title", _ch_id)
            await query.edit_message_text(
                f"<blockquote>✅ تم إضافة الموعد الليلي\n\n"
                f"📢 القناة: {ch_title}\n"
                f"🎙 {station_name}\n"
                f"⏰ الساعة {h12}:{m:02d} {period}</blockquote>"
            )
        elif ttype == "sched_add":
            sid = old_time  # old_time carries station id
            if sid in ST_TIMO:
                if time_24 in AUTO_SCHEDULE:
                    await query.edit_message_text(
                        f"<blockquote>⚠️ يوجد محطة بالفعل في الساعة {h12}:{m:02d} {period}\n"
                        f"اختر وقتاً آخر</blockquote>"
                    )
                else:
                    AUTO_SCHEDULE[time_24] = {"name": ST_TIMO[sid]["name"], "url": ST_TIMO[sid]["url"]}
                    save_settings()
                    await query.edit_message_text(
                        f"<blockquote>✅ تم إضافة المحطة للجدول\n\n"
                        f"🎙 {ST_TIMO[sid]['name']}\n"
                        f"⏰ الساعة {h12}:{m:02d} {period}</blockquote>"
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


    elif data == "open_auto_schedule":
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        if is_admin(int(user_id)):
            is_active = auto_schedule_enabled
        else:
            is_active = user_schedule_enabled.get(user_id, False)
        status = "✅ مفعل" if is_active else "❌ متوقف"
        buttons = build_schedule_buttons()
        await query.edit_message_text(
            f"<blockquote>📅 جدول التشغيل التلقائي\nالحالة: {status}\n\n"
            "✅ = مفعّل  |  ❌ = موقوف</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
        )
        await query.message.reply_text(
            "<blockquote>اضغط تشغيل أو إيقاف لكل محطة 👆</blockquote>",
            reply_markup=schedule_keyboard()
        )
        channels = user_data.get(user_id, {}).get("channels", {})
        if channels:
            ch_buttons = []
            for ch_id, ch_info in list(channels.items()):
                ch_enabled = channel_schedule_enabled.get(ch_id, True)
                status_icon = "✅" if ch_enabled else "❌"
                ch_buttons.append([InlineKeyboardButton(
                    f"{status_icon} {ch_info.get('title', ch_id)}",
                    callback_data=f"ch_sched_toggle_{ch_id}"
                )])
            await query.message.reply_text(
                "<blockquote>📢 الجدول لكل قناة:\n✅ مفعّل | ❌ موقوف</blockquote>",
                reply_markup=InlineKeyboardMarkup(ch_buttons)
            )

    elif data.startswith("open_night_mode_"):
        uid = data[len("open_night_mode_"):]
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        u_night = user_data.get(uid, {}).get("night_mode_enabled", False)
        status = "✅ مفعّل" if u_night else "❌ موقوف"
        channels = user_data.get(uid, {}).get("channels", {})
        await query.edit_message_text(
            f"<blockquote>🌙 الوضع الليلي\n\n"
            f"الحالة: {status}\n\n"
            f"اختر القناة لإدارة جدولها الليلي:</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ تفعيل" if not u_night else "❌ إيقاف",
                                     callback_data=f"unight_toggle_{uid}")],
            ] + [
                [InlineKeyboardButton(f"📢 {ch_info.get('title', ch_id)}", callback_data=f"unight_ch_{uid}_{ch_id}")]
                for ch_id, ch_info in list(channels.items())
            ])
        )

    elif data.startswith("unight_ch_"):
        rest = data[len("unight_ch_"):]
        parts = rest.split("_", 1)
        uid = parts[0]
        ch_id = parts[1] if len(parts) > 1 else ""
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        ch_info = user_data.get(uid, {}).get("channels", {}).get(ch_id, {})
        ch_title = ch_info.get("title", ch_id)
        night_schedule = ch_info.get("night_schedule", {})
        def to_ar_time(t):
            try:
                h, m = map(int, t.split(":"))
                period = "صباحاً" if h < 12 else "مساءً"
                h12 = h % 12 or 12
                return f"{h12}:{m:02d} {period}"
            except:
                return t
        schedule_text = ""
        if night_schedule:
            for t, sid in sorted(night_schedule.items()):
                sname = ST_TIMO.get(sid, {}).get("name", sid).replace("إذاعة ", "").strip()
                schedule_text += f"• {to_ar_time(t)} ← {sname}\n"
        else:
            schedule_text = "• لا يوجد جدول ليلي بعد"
        await query.edit_message_text(
            f"<blockquote>🌙 الجدول الليلي\n📢 {ch_title}\n\n{schedule_text}</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ إضافة موعد", callback_data=f"unight_add_sched_{uid}_{ch_id}")],
                [InlineKeyboardButton("🗑 حذف موعد", callback_data=f"unight_del_sched_{uid}_{ch_id}")],
                [InlineKeyboardButton("🔙 رجوع", callback_data=f"unight_back_{uid}")],
            ])
        )

    elif data.startswith("unight_add_sched_"):
        rest = data[len("unight_add_sched_"):]
        parts = rest.split("_", 1)
        uid = parts[0]
        ch_id = parts[1] if len(parts) > 1 else ""
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        for cat_name in ST_CATEGORIES.keys():
            buttons.append([InlineKeyboardButton(cat_name, callback_data=f"unight_sched_cat_{uid}_{ch_id}_{cat_name}")])
        await query.edit_message_text(
            "<blockquote>➕ إضافة موعد ليلي\n\nاختر القسم:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("unight_sched_cat_"):
        rest = data[len("unight_sched_cat_"):]
        parts = rest.split("_", 2)
        uid = parts[0]
        ch_id = parts[1] if len(parts) > 1 else ""
        cat = parts[2] if len(parts) > 2 else ""
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        station_ids = ST_CATEGORIES.get(cat, [])
        buttons = []
        row = []
        for i, sid in enumerate(station_ids, 1):
            name = ST_TIMO[sid]["name"].replace("إذاعة ", "").replace("اذاعة ", "").replace("قناة ", "").strip()
            row.append(InlineKeyboardButton(f"{name}", callback_data=f"unight_sched_pick_{uid}_{ch_id}_{sid}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        await query.edit_message_text(
            f"<blockquote>➕ {cat}\n\nاختر المحطة:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("unight_sched_pick_"):
        rest = data[len("unight_sched_pick_"):]
        parts = rest.split("_", 2)
        uid = parts[0]
        ch_id = parts[1] if len(parts) > 1 else ""
        sid = parts[2] if len(parts) > 2 else "1"
        await query.answer()
        station_name = ST_TIMO.get(sid, {}).get("name", sid)
        h, m = 23, 0
        await query.edit_message_text(
            f"<blockquote>➕ {station_name}\n\nاختر وقت التشغيل:</blockquote>",
            reply_markup=build_time_picker_kb(h, m, f"unight_sched", f"{uid}_{ch_id}_{sid}")
        )

    elif data.startswith("unight_del_sched_"):
        rest = data[len("unight_del_sched_"):]
        parts = rest.split("_", 1)
        uid = parts[0]
        ch_id = parts[1] if len(parts) > 1 else ""
        await query.answer()
        ch_info = user_data.get(uid, {}).get("channels", {}).get(ch_id, {})
        night_schedule = ch_info.get("night_schedule", {})
        if not night_schedule:
            await query.edit_message_text("<blockquote>❌ الجدول الليلي فارغ</blockquote>")
            return
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        def to_ar_time(t):
            try:
                h, m = map(int, t.split(":"))
                period = "صباحاً" if h < 12 else "مساءً"
                h12 = h % 12 or 12
                return f"{h12}:{m:02d} {period}"
            except:
                return t
        buttons = []
        for t, sid in sorted(night_schedule.items()):
            sname = ST_TIMO.get(sid, {}).get("name", sid).replace("إذاعة ", "").strip()
            buttons.append([InlineKeyboardButton(f"🗑 {to_ar_time(t)} ← {sname}", callback_data=f"unight_del_entry_{uid}_{ch_id}_{t}")])
        await query.edit_message_text(
            "<blockquote>🗑 اختر الموعد لحذفه:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("unight_del_entry_"):
        rest = data[len("unight_del_entry_"):]
        parts = rest.split("_", 2)
        uid = parts[0]
        ch_id = parts[1] if len(parts) > 1 else ""
        t = parts[2] if len(parts) > 2 else ""
        await query.answer()
        night_schedule = user_data.get(uid, {}).get("channels", {}).get(ch_id, {}).get("night_schedule", {})
        if t in night_schedule:
            del night_schedule[t]
            user_data[uid]["channels"][ch_id]["night_schedule"] = night_schedule
            save_data()
        await query.edit_message_text(
            f"<blockquote>✅ تم حذف الموعد {t} من الجدول الليلي</blockquote>"
        )

    elif data.startswith("unight_manage_stations_"):
        uid = data[len("unight_manage_stations_"):]
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        u_station_id = user_data.get(uid, {}).get("night_mode_station", "1")
        u_night_stations = user_data.get(uid, {}).get("night_mode_stations", [u_station_id])
        buttons = []
        for sid in u_night_stations:
            if sid in ST_TIMO:
                name = ST_TIMO[sid]["name"].replace("إذاعة ", "").replace("اذاعة ", "").strip()
                buttons.append([InlineKeyboardButton(f"🗑 {name}", callback_data=f"unight_del_station_{uid}_{sid}")])
        buttons.append([InlineKeyboardButton("➕ إضافة محطة ليلية", callback_data=f"unight_add_station_{uid}")])
        buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"unight_back_{uid}")])
        await query.edit_message_text(
            f"<blockquote>🌙 المحطات الليلية ({len(u_night_stations)} محطة)\n\n"
            f"اضغط على المحطة لحذفها أو أضف محطة جديدة:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("unight_add_station_"):
        uid = data[len("unight_add_station_"):]
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        for cat_name in ST_CATEGORIES.keys():
            buttons.append([InlineKeyboardButton(cat_name, callback_data=f"unight_add_cat_{uid}_{cat_name}")])
        buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"unight_manage_stations_{uid}")])
        await query.edit_message_text(
            "<blockquote>➕ إضافة محطة ليلية\n\nاختر القسم:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("unight_add_cat_"):
        rest = data[len("unight_add_cat_"):]
        parts = rest.split("_", 1)
        uid = parts[0]
        cat = parts[1] if len(parts) > 1 else ""
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        station_ids = ST_CATEGORIES.get(cat, [])
        u_station_id = user_data.get(uid, {}).get("night_mode_station", "1")
        u_night_stations = user_data.get(uid, {}).get("night_mode_stations", [u_station_id])
        buttons = []
        row = []
        for i, sid in enumerate(station_ids, 1):
            name = ST_TIMO[sid]["name"].replace("إذاعة ", "").replace("اذاعة ", "").replace("قناة ", "").strip()
            already = "✅ " if sid in u_night_stations else ""
            row.append(InlineKeyboardButton(f"{already}{name}", callback_data=f"unight_add_pick_{uid}_{sid}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"unight_add_station_{uid}")])
        await query.edit_message_text(
            f"<blockquote>➕ {cat}\n\nاختر المحطة (✅ = موجودة بالفعل):</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("unight_add_pick_"):
        rest = data[len("unight_add_pick_"):]
        parts = rest.split("_", 1)
        uid = parts[0]
        sid = parts[1] if len(parts) > 1 else "1"
        await query.answer()
        u_station_id = user_data.get(uid, {}).get("night_mode_station", "1")
        u_night_stations = user_data.get(uid, {}).get("night_mode_stations", [u_station_id])
        if sid in u_night_stations:
            await query.answer("⚠️ المحطة موجودة بالفعل", show_alert=True)
            return
        u_night_stations.append(sid)
        user_data[uid]["night_mode_stations"] = u_night_stations
        save_data()
        station_name = ST_TIMO.get(sid, {}).get("name", sid)
        await query.edit_message_text(
            f"<blockquote>✅ تم إضافة {station_name} للمحطات الليلية</blockquote>"
        )

    elif data.startswith("unight_del_station_"):
        rest = data[len("unight_del_station_"):]
        parts = rest.split("_", 1)
        uid = parts[0]
        sid = parts[1] if len(parts) > 1 else ""
        await query.answer()
        u_station_id = user_data.get(uid, {}).get("night_mode_station", "1")
        u_night_stations = user_data.get(uid, {}).get("night_mode_stations", [u_station_id])
        if len(u_night_stations) <= 1:
            await query.answer("⚠️ لازم يكون في محطة واحدة على الأقل", show_alert=True)
            return
        if sid in u_night_stations:
            u_night_stations.remove(sid)
            user_data[uid]["night_mode_stations"] = u_night_stations
            save_data()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        for s in u_night_stations:
            if s in ST_TIMO:
                name = ST_TIMO[s]["name"].replace("إذاعة ", "").replace("اذاعة ", "").strip()
                buttons.append([InlineKeyboardButton(f"🗑 {name}", callback_data=f"unight_del_station_{uid}_{s}")])
        buttons.append([InlineKeyboardButton("➕ إضافة محطة ليلية", callback_data=f"unight_add_station_{uid}")])
        station_name = ST_TIMO.get(sid, {}).get("name", sid)
        await query.edit_message_text(
            f"<blockquote>✅ تم حذف {station_name}\n\n"
            f"🌙 المحطات الليلية ({len(u_night_stations)} محطة):</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("unight_toggle_"):
        await query.answer()
        uid = data[len("unight_toggle_"):]
        if uid not in user_data:
            await query.answer("❌ خطأ", show_alert=True)
            return
        current = user_data[uid].get("night_mode_enabled", False)
        user_data[uid]["night_mode_enabled"] = not current
        save_data()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        u_night = user_data[uid]["night_mode_enabled"]
        u_start = user_data[uid].get("night_mode_start", "23:00")
        u_end = user_data[uid].get("night_mode_end", "05:00")
        u_station_id = user_data[uid].get("night_mode_station", "1")
        u_night_stations = user_data[uid].get("night_mode_stations", [u_station_id])
        u_station_name = "\n".join([f"• {ST_TIMO.get(s, {}).get('name', s)}" for s in u_night_stations])
        def to_ar_time(t):
            try:
                h, m = map(int, t.split(":"))
                period = "صباحاً" if h < 12 else "مساءً"
                h12 = h % 12 or 12
                return f"{h12}:{m:02d} {period}"
            except: return t
        status = "✅ مفعّل" if u_night else "❌ موقوف"
        await query.edit_message_text(
            f"<blockquote>🌙 الوضع الليلي\n\nالحالة: {status}\n"
            f"⏰ البداية: {to_ar_time(u_start)}\n"
            f"⏰ النهاية: {to_ar_time(u_end)}\n"
            f"🎙 المحطة: {u_station_name}</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ تفعيل" if not u_night else "❌ إيقاف",
                                     callback_data=f"unight_toggle_{uid}")],
                [InlineKeyboardButton("⏰ وقت البداية", callback_data=f"unight_start_{uid}"),
                 InlineKeyboardButton("⏰ وقت النهاية", callback_data=f"unight_end_{uid}")],
                [InlineKeyboardButton("🎙 إدارة المحطات الليلية", callback_data=f"unight_manage_stations_{uid}")],
            ])
        )

    elif data.startswith("unight_start_") or data.startswith("unight_end_"):
        await query.answer()
        is_start = data.startswith("unight_start_")
        uid = data[len("unight_start_"):] if is_start else data[len("unight_end_"):]
        ttype = "unight_start" if is_start else "unight_end"
        current_time = user_data.get(uid, {}).get("night_mode_start" if is_start else "night_mode_end", "23:00" if is_start else "05:00")
        _h, _m = map(int, current_time.split(":"))
        label = "وقت البداية" if is_start else "وقت النهاية"
        await query.edit_message_text(
            f"<blockquote>⏰ تغيير {label}\n\nاستخدم الأزرار:</blockquote>",
            reply_markup=build_time_picker_kb(_h, _m, ttype, uid)
        )

    elif data.startswith("unight_station_"):
        await query.answer()
        uid = data[len("unight_station_"):]
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        # عرض أقسام المحطات
        cat_buttons = [
            [InlineKeyboardButton(cat, callback_data=f"unight_cat_{uid}_{cat}")]
            for cat in ST_CATEGORIES.keys()
        ]
        cat_buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"unight_back_{uid}")])
        await query.edit_message_text(
            "<blockquote>🎙 اختر قسم الإذاعة:</blockquote>",
            reply_markup=InlineKeyboardMarkup(cat_buttons)
        )

    elif data.startswith("unight_cat_"):
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        rest = data[len("unight_cat_"):]
        # uid is first part, cat is rest
        # format: unight_cat_{uid}_{cat}
        parts = rest.split("_", 1)
        uid = parts[0]
        cat = parts[1] if len(parts) > 1 else ""
        station_ids = ST_CATEGORIES.get(cat, [])
        station_buttons = [
            [InlineKeyboardButton(ST_TIMO[sid]["name"], callback_data=f"unight_pick_{uid}_{sid}")]
            for sid in station_ids if sid in ST_TIMO
        ]
        station_buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"unight_station_{uid}")])
        await query.edit_message_text(
            f"<blockquote>🎙 اختر الإذاعة من {cat}:</blockquote>",
            reply_markup=InlineKeyboardMarkup(station_buttons)
        )

    elif data.startswith("unight_pick_"):
        await query.answer()
        rest = data[len("unight_pick_"):]
        parts = rest.split("_", 1)
        uid = parts[0]
        sid = parts[1] if len(parts) > 1 else "1"
        if uid in user_data:
            user_data[uid]["night_mode_station"] = sid
            save_data()
        station_name = ST_TIMO.get(sid, {}).get("name", "")
        await query.edit_message_text(
            f"<blockquote>✅ تم تغيير المحطة إلى:\n🎙 {station_name}</blockquote>"
        )

    elif data.startswith("unight_back_"):
        await query.answer()
        uid = data[len("unight_back_"):]
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        u_night = user_data.get(uid, {}).get("night_mode_enabled", False)
        u_start = user_data.get(uid, {}).get("night_mode_start", "23:00")
        u_end = user_data.get(uid, {}).get("night_mode_end", "05:00")
        u_station_id = user_data.get(uid, {}).get("night_mode_station", "1")
        u_station_name = ST_TIMO.get(u_station_id, {}).get("name", "إذاعة آيات السكينة")
        def to_ar_time(t):
            try:
                h, m = map(int, t.split(":"))
                period = "صباحاً" if h < 12 else "مساءً"
                h12 = h % 12 or 12
                return f"{h12}:{m:02d} {period}"
            except: return t
        status = "✅ مفعّل" if u_night else "❌ موقوف"
        await query.edit_message_text(
            f"<blockquote>🌙 الوضع الليلي\n\nالحالة: {status}\n"
            f"⏰ البداية: {to_ar_time(u_start)}\n"
            f"⏰ النهاية: {to_ar_time(u_end)}\n"
            f"🎙 المحطة: {u_station_name}</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ تفعيل" if not u_night else "❌ إيقاف",
                                     callback_data=f"unight_toggle_{uid}")],
                [InlineKeyboardButton("⏰ وقت البداية", callback_data=f"unight_start_{uid}"),
                 InlineKeyboardButton("⏰ وقت النهاية", callback_data=f"unight_end_{uid}")],
                [InlineKeyboardButton("🎙 إدارة المحطات الليلية", callback_data=f"unight_manage_stations_{uid}")],
            ])
        )

    elif data == "stats_bot":
        await query.answer()
        if not is_admin(int(user_id)) or not has_perm(int(user_id), "stats"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await query.edit_message_text(
            build_bot_stats_text(),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 تحديث", callback_data="stats_bot")],
                [InlineKeyboardButton("📡 إحصائيات البث", callback_data="stats_broadcast")],
            ])
        )

    elif data == "stats_broadcast":
        await query.answer()
        active = []
        # كل مستخدم يشوف قنواته بس
        users_to_check = [(user_id, user_data.get(user_id, {}))]
        
        for uid, uinfo in users_to_check:
            for ch_id, ch_info in uinfo.get("channels", {}).items():
                if "process" in ch_info and is_ffmpeg_running(ch_info["process"]):
                    station_url = ch_info.get("station", uinfo.get("temp_station", ""))
                    station_name = next((v["name"] for v in ST_TIMO.values() if v["url"] == station_url), "غير معروف")
                    active.append({
                        "channel": ch_info.get("title", ch_id),
                        "station": station_name,
                        "ch_id": ch_id,
                    })
        if not active:
            await query.edit_message_text("<blockquote>📡 لا توجد بثوث نشطة حالياً</blockquote>")
            return
        stats_text = "<blockquote>📡 إحصائيات البث:\n\n"
        for a in active:
            duration = get_broadcast_duration(a["ch_id"])
            start_time = broadcast_stats.get(a["ch_id"], {}).get("start_time", "غير معروف")
            stats_text += f"📢 {a['channel']}\n🎙 {a['station']}\n⏰ بدأ: {start_time}\n⏱ المدة: {duration}\n▬▬▬▬▬▬▬▬▬▬\n"
        stats_text += "</blockquote>"
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await query.edit_message_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 تحديث", callback_data="stats_broadcast")],
                [InlineKeyboardButton("🤖 إحصائيات البوت", callback_data="stats_bot")],
            ])
        )

    elif data == "broadcast_users_menu":
        await query.answer()
        if not is_admin(int(user_id)) or not has_perm(int(user_id), "broadcast_msg"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        total = len(user_data)
        user_state[user_id] = {"step": "awaiting_broadcast_users_text"}
        await query.edit_message_text(
            f"<blockquote>📢 إذاعة للمستخدمين\n\n"
            f"👥 عدد المستخدمين: {total}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"✍️ اكتب الرسالة التي تريد إرسالها\n"
            f"وستصل لجميع المستخدمين فوراً 👇</blockquote>"
        )
        await query.message.reply_text(
            "<blockquote>اكتب رسالتك الآن 👇</blockquote>",
            reply_markup=ReplyKeyboardMarkup([["❌ إلغاء"]], resize_keyboard=True)
        )

    elif data == "broadcast_channels_menu":
        await query.answer()
        if not is_admin(int(user_id)) or not has_perm(int(user_id), "broadcast_msg"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        channels = set()
        for u in list(user_data.values()):
            if "channels" in u:
                channels.update(u["channels"].keys())
        user_state[user_id] = {"step": "awaiting_broadcast_channels_text"}
        await query.edit_message_text(
            f"<blockquote>📣 إذاعة للقنوات\n\n"
            f"📢 عدد القنوات: {len(channels)}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"✍️ اكتب الرسالة التي تريد إرسالها\n"
            f"وستصل لجميع القنوات فوراً 👇</blockquote>"
        )
        await query.message.reply_text(
            "<blockquote>اكتب رسالتك الآن 👇</blockquote>",
            reply_markup=ReplyKeyboardMarkup([["❌ إلغاء"]], resize_keyboard=True)
        )

    elif data.startswith("myc_details_"):
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        channel_id = data[len("myc_details_"):]
        uid = user_id
        if uid not in user_data or channel_id not in user_data[uid].get("channels", {}):
            await query.answer("❌ القناة غير موجودة", show_alert=True)
            return
        info = user_data[uid]["channels"][channel_id]
        status = "🟢 نشط" if "process" in info else "🔴 متوقف"
        station_url = user_data[uid].get("temp_station", "")
        station_name = next((v["name"] for v in ST_TIMO.values() if v["url"] == station_url), "لا يوجد")
        duration = get_broadcast_duration(channel_id) if "process" in info else "—"
        ch_url = None
        members = "غير متاح"
        try:
            chat = await app.get_chat(int(channel_id))
            if chat.username:
                ch_url = f"https://t.me/{chat.username}"
            elif chat.invite_link:
                ch_url = chat.invite_link
            try:
                members = await app.get_chat_members_count(int(channel_id))
            except Exception:
                pass
        except Exception:
            pass
        text_msg = (
            f"<blockquote>"
            f"📢 {info['title']}\n"
            f"👥 الأعضاء: {members}\n"
            f"📡 البث: {status}\n"
            f"🎙 المحطة: {station_name}\n"
            f"⏱ مدة البث: {duration}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🆔 المعرف: {channel_id}"
            f"</blockquote>"
        )
        row = []
        if ch_url:
            row.append(InlineKeyboardButton("📢 دخول القناة", url=ch_url))
        row.append(InlineKeyboardButton("🗑 حذف القناة", callback_data=f"del_confirm_{channel_id}"))
        await query.message.reply_text(
            text_msg,
            reply_markup=InlineKeyboardMarkup([row])
        )

    elif data.startswith("del_confirm_"):
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        channel_id = data[len("del_confirm_"):]
        uid = user_id
        info = user_data.get(uid, {}).get("channels", {}).get(channel_id, {})
        ch_title = info.get("title", channel_id)
        await query.edit_message_reply_markup(
            InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ نعم، احذف", callback_data=f"del_channel_{channel_id}"),
                 InlineKeyboardButton("❌ إلغاء", callback_data="del_channel_cancel")]
            ])
        )

    elif data.startswith("del_channel_"):
        await query.answer()
        ch_id = data[len("del_channel_"):]
        if ch_id == "cancel":
            await query.edit_message_text("<blockquote>❌ تم إلغاء العملية</blockquote>")
            return
        uid = user_id
        if uid in user_data and ch_id in user_data[uid].get("channels", {}):
            if "process" in user_data[uid]["channels"][ch_id]:
                pid = user_data[uid]["channels"][ch_id]["process"]
                try:
                    if is_ffmpeg_running(pid):
                        subprocess.run(["kill", "-9", str(pid)], timeout=5, check=True)
                except Exception as e:
                    logger.error(f"del_channel kill error: {e}")
            ch_title = user_data[uid]["channels"][ch_id].get("title", ch_id)
            del user_data[uid]["channels"][ch_id]
            save_data()
            await query.edit_message_text(
                f"<blockquote>✅ تم حذف القناة بنجاح\n📢 {ch_title}</blockquote>"
            )
        else:
            await query.edit_message_text("<blockquote>❌ القناة غير موجودة</blockquote>")

    elif data == "ban_user_menu":
        await query.answer()
        if not is_admin(int(user_id)) or not has_perm(int(user_id), "ban"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        user_state[user_id] = {"step": "awaiting_ban_id"}
        await query.edit_message_text(
            "<blockquote>🚫 حظر مستخدم\n\nأرسل ID المستخدم الذي تريد حظره:</blockquote>"
        )
        await query.message.reply_text(
            "<blockquote>أرسل الـ ID 👇</blockquote>",
            reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
        )

    elif data == "unban_user_menu":
        await query.answer()
        if not is_admin(int(user_id)) or not has_perm(int(user_id), "ban"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        if not banned_users:
            await query.edit_message_text("<blockquote>✅ لا يوجد مستخدمون محظورون حالياً</blockquote>")
            return
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await query.edit_message_text(f"<blockquote>🚫 المحظورون ({len(banned_users)})</blockquote>")
        for uid in list(banned_users):
            try:
                u = await app.get_users(int(uid))
                name = u.first_name or "بدون اسم"
                username = f"@{u.username}" if u.username else "بدون يوزر"
            except Exception:
                name = "غير معروف"
                username = "بدون يوزر"
            data_info = banned_users_data.get(str(uid), {})
            ban_date = data_info.get("date", "غير معروف")
            ban_reason = data_info.get("reason", "حظر يدوي")
            text_msg = (
                f"<blockquote>🚫 مستخدم محظور\n\n"
                f"👤 الاسم: {name}\n"
                f"🔗 اليوزر: {username}\n"
                f"🆔 الـ ID: {uid}\n"
                f"📅 تاريخ الحظر: {ban_date}\n"
                f"📝 السبب: {ban_reason}</blockquote>"
            )
            await query.message.reply_text(
                text_msg,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ رفع الحظر", callback_data=f"unban_{uid}")]
                ])
            )
            await asyncio.sleep(0.3)

    elif data == "whitelist_menu":
        await query.answer()
        if not is_admin(int(user_id)) or not has_perm(int(user_id), "ban"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await query.edit_message_text(
            f"<blockquote>🛡 قائمة الإعفاء من الحظر\n\n"
            f"👥 عدد المعفيين: {len(whitelist_users)}\n\n"
            f"المستخدمون في هذه القائمة لن يتم حظرهم تلقائياً أو يدوياً</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ إضافة للإعفاء", callback_data="whitelist_add")],
                [InlineKeyboardButton("➖ إزالة من الإعفاء", callback_data="whitelist_remove")],
                [InlineKeyboardButton("📋 عرض القائمة", callback_data="whitelist_view")],
            ])
        )

    elif data == "set_welcome_text":
        await query.answer()
        current = welcome_text or "الافتراضي"
        user_state[user_id] = {"step": "awaiting_welcome_text"}
        await query.edit_message_text(
            f"<blockquote>✏️ تخصيص رسالة الترحيب\n\n"
            f"النص الحالي:\n{current}\n\n"
            f"يمكنك استخدام {{name}} لاسم المستخدم\n"
            f"أرسل - للرجوع للنص الافتراضي</blockquote>"
        )
        await query.message.reply_text(
            "<blockquote>اكتب النص الجديد 👇</blockquote>",
            reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
        )

    elif data == "top_broadcasters":
        await query.answer()
        sorted_users = sorted(
            user_data.items(),
            key=lambda x: x[1].get("broadcast_count", 0),
            reverse=True
        )[:10]
        text_msg = "<blockquote>🏆 أكثر المستخدمين بثاً\n\n"
        for i, (uid, uinfo) in enumerate(sorted_users, 1):
            count = uinfo.get("broadcast_count", 0)
            if count == 0:
                break
            try:
                u = await app.get_users(int(uid))
                name = u.first_name or uid
            except Exception:
                name = uid
            text_msg += f"{i}. {name} — {count} بث\n"
        text_msg += "</blockquote>"
        await query.edit_message_text(text_msg)

    elif data == "weekly_report_menu":
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        weekly_status = "🟢 مفعّل" if weekly_report_enabled else "🔴 موقوف"
        await query.edit_message_text(
            f"<blockquote>📊 إدارة التقرير الأسبوعي\n\n"
            f"الحالة: {weekly_status}\n"
            f"اليوم: {DAYS_AR.get(weekly_report_day, '')}\n"
            f"الوقت: {weekly_report_time}</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 التقرير: " + ("إيقاف ✅" if weekly_report_enabled else "تفعيل ❌"), callback_data="toggle_weekly_report")],
                [InlineKeyboardButton("📅 تعديل الموعد", callback_data="set_weekly_report_sched")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="adv_settings_back")],
            ])
        )

    elif data == "backup_manage_menu":
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        backup_status = f"🟢 كل {backup_user_threshold} مستخدم" if backup_on_new_users else "🔴 موقوف"
        await query.edit_message_text(
            f"<blockquote>📦 إدارة الـ Backup\n\n"
            f"الحالة: {backup_status}</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📦 Backup: " + ("إيقاف ✅" if backup_on_new_users else "تفعيل ❌"), callback_data="toggle_backup_threshold")],
                [InlineKeyboardButton(f"🔢 عدد المستخدمين: {backup_user_threshold}", callback_data="set_backup_threshold")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="adv_settings_back")],
            ])
        )

    elif data == "adv_settings_back":
        await query.answer()
        _txt, _kb = build_adv_settings_msg()
        await query.edit_message_text(_txt, reply_markup=_kb)

    elif data == "cleanup_menu":
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        cleanup_status = f"🟢 بعد {auto_cleanup_days} يوم" if auto_cleanup_enabled else "🔴 موقوف"
        await query.edit_message_text(
            f"<blockquote>🧹 إدارة التنظيف\n\n"
            f"التنظيف التلقائي: {cleanup_status}\n"
            f"الأرشيف: {len(deleted_users_archive)} مستخدم</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🧹 التلقائي: " + ("إيقاف ✅" if auto_cleanup_enabled else "تفعيل ❌"), callback_data="toggle_auto_cleanup")],
                [InlineKeyboardButton(f"📅 حذف بعد: {auto_cleanup_days} يوم", callback_data="set_cleanup_days")],
                [InlineKeyboardButton("🗑 تنظيف يدوي الآن", callback_data="manual_cleanup")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="adv_settings_back")],
            ])
        )

    elif data == "toggle_auto_cleanup":
        await query.answer()
        auto_cleanup_enabled = not auto_cleanup_enabled
        save_settings()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        cleanup_status = f"🟢 بعد {auto_cleanup_days} يوم" if auto_cleanup_enabled else "🔴 موقوف"
        await query.edit_message_text(
            f"<blockquote>🧹 إدارة التنظيف\n\nالتنظيف التلقائي: {cleanup_status}\nالأرشيف: {len(deleted_users_archive)} مستخدم</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🧹 التلقائي: " + ("إيقاف ✅" if auto_cleanup_enabled else "تفعيل ❌"), callback_data="toggle_auto_cleanup")],
                [InlineKeyboardButton(f"📅 حذف بعد: {auto_cleanup_days} يوم", callback_data="set_cleanup_days")],
                [InlineKeyboardButton("🗑 تنظيف يدوي الآن", callback_data="manual_cleanup")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="adv_settings_back")],
            ])
        )

    elif data == "set_cleanup_days":
        await query.answer()
        user_state[user_id] = {"step": "awaiting_cleanup_days"}
        await query.edit_message_text(
            f"<blockquote>📅 تغيير مدة الحذف\n\nالمدة الحالية: {auto_cleanup_days} يوم\n\nاكتب عدد الأيام:</blockquote>"
        )
        await query.message.reply_text(
            "<blockquote>اكتب العدد 👇</blockquote>",
            reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
        )

    elif data == "manual_cleanup":
        await query.answer()
        inactive = get_inactive_users()
        if not inactive:
            await query.answer("✅ لا يوجد مستخدمون غير نشطين", show_alert=True)
            return
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        # عرض أسماء المستخدمين قبل الحذف
        users_text = ""
        for u in inactive[:15]:  # أول 15
            try:
                uu = await app.get_users(int(u["uid"]))
                name = uu.first_name or "غير معروف"
                username = f"@{uu.username}" if uu.username else "بدون يوزر"
            except Exception:
                name = "غير معروف"
                username = "بدون يوزر"
            users_text += f"• {name} ({username}) — {u['days']} يوم\n"
        if len(inactive) > 15:
            users_text += f"... و{len(inactive) - 15} آخرين\n"
        await query.edit_message_text(
            f"<blockquote>🗑 التنظيف اليدوي\n\n"
            f"👥 المستخدمون غير النشطين: {len(inactive)}\n\n"
            f"{users_text}\n"
            f"هل تريد حذفهم جميعاً؟</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"✅ حذف الكل ({len(inactive)} مستخدم)", callback_data="confirm_manual_cleanup")],
                [InlineKeyboardButton("❌ إلغاء", callback_data="noop")],
            ])
        )

    elif data == "view_archive":
        await query.answer()
        if not deleted_users_archive:
            await query.answer("📂 الأرشيف فارغ", show_alert=True)
            return
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        text_msg = f"<blockquote>🗃 أرشيف المستخدمين المحذوفين\n({len(deleted_users_archive)} مستخدم)\n\n"
        for u in deleted_users_archive[-archive_display_count:]:
            text_msg += (
                f"🆔 {u['uid']}\n"
                f"📅 انضم: {u['join_date']}\n"
                f"🗑 حذف: {u['deleted_date']}\n"
                f"🎙 بثوث: {u['broadcast_count']}\n"
                f"━━━━━━━━━━━\n"
            )
        text_msg += "</blockquote>"
        await query.edit_message_text(
            text_msg,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("♻️ استعادة مستخدم", callback_data="restore_user")],
                [InlineKeyboardButton(f"🔢 عرض: {archive_display_count} مستخدم", callback_data="set_archive_count")],
                [InlineKeyboardButton("🗑 مسح الأرشيف", callback_data="clear_archive")],
            ])
        )

    elif data == "set_archive_count":
        await query.answer()
        user_state[user_id] = {"step": "awaiting_archive_count"}
        await query.edit_message_text(
            f"<blockquote>🔢 تغيير عدد المستخدمين المعروضين\n\nالعدد الحالي: {archive_display_count}\n\nاكتب العدد الجديد:</blockquote>"
        )
        await query.message.reply_text(
            "<blockquote>اكتب العدد 👇</blockquote>",
            reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
        )

    elif data == "restore_user":
        await query.answer()
        user_state[user_id] = {"step": "awaiting_restore_uid"}
        await query.edit_message_text(
            "<blockquote>♻️ استعادة مستخدم\n\nأرسل ID المستخدم للاستعادة:</blockquote>"
        )
        await query.message.reply_text(
            "<blockquote>أرسل الـ ID 👇</blockquote>",
            reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
        )

    elif data == "clear_archive":
        await query.answer()
        deleted_users_archive.clear()
        save_settings()
        await query.edit_message_text("<blockquote>✅ تم مسح الأرشيف</blockquote>")

    elif data == "confirm_manual_cleanup":
        await query.answer()
        deleted = cleanup_inactive_users(0)
        await query.edit_message_text(
            f"<blockquote>✅ تم الحذف\n\n"
            f"🗑 تم حذف {deleted} مستخدم غير نشط\n"
            f"📅 {egypt_strftime()}</blockquote>"
        )

    elif data == "guide_menu":
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await query.message.reply_text(
            "<blockquote>📖 كيفية استخدام البوت\n\nاختر الموضوع الذي تريد التعلم عنه:</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📡 طريقة تشغيل البث المباشر", callback_data="guide_0_0")],
            ])
        )
        # حذف رسالة الصورة (رسالة البوت نفسه)
        try:
            await client.delete_messages(
                chat_id=query.message.chat.id,
                message_ids=query.message.id
            )
        except Exception:
            pass

    elif data == "guide_soon":
        await query.answer("🔜 قريباً!", show_alert=True)

    elif data.startswith("guide_"):
        await query.answer()
        parts = data.split("_")
        topic = int(parts[1])
        step = int(parts[2])
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        steps = GUIDE_STEPS

        if step >= len(steps):
            await query.answer("✅ انتهى الشرح!", show_alert=True)
            return

        current = steps[step]
        total = len(steps)

        nav_buttons = []
        if step > 0:
            nav_buttons.append(InlineKeyboardButton("◀️ السابق", callback_data=f"guide_{topic}_{step-1}"))
        nav_buttons.append(InlineKeyboardButton(f"📄 {step+1}/{total}", callback_data="noop"))
        if step < total - 1:
            nav_buttons.append(InlineKeyboardButton("التالي ▶️", callback_data=f"guide_{topic}_{step+1}"))

        kb = InlineKeyboardMarkup([nav_buttons])

        text_msg = (
            f"<blockquote>{current['title']}\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"{current['text']}</blockquote>"
        )

        if current.get("image"):
            try:
                await query.edit_message_text(text_msg, reply_markup=kb)
            except Exception:
                await query.message.reply_text(text_msg, reply_markup=kb)
        else:
            try:
                await query.edit_message_text(text_msg, reply_markup=kb)
            except Exception:
                await query.message.reply_text(text_msg, reply_markup=kb)

    elif data == "ch_search":
        await query.answer()
        if not is_admin(int(user_id)) or not has_perm(int(user_id), "view_data"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        user_state[user_id] = {"step": "awaiting_ch_search"}
        await query.edit_message_text(
            "<blockquote>🔍 بحث في القنوات\n\nاكتب اسم القناة أو ID الصاحب:</blockquote>"
        )
        await query.message.reply_text(
            "<blockquote>اكتب للبحث 👇</blockquote>",
            reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
        )

    elif data == "usr_search":
        await query.answer()
        if not is_admin(int(user_id)) or not has_perm(int(user_id), "view_data"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        user_state[user_id] = {"step": "awaiting_usr_search"}
        await query.edit_message_text(
            "<blockquote>🔍 بحث في المستخدمين\n\nاكتب الاسم أو اليوزر أو الـ ID:</blockquote>"
        )
        await query.message.reply_text(
            "<blockquote>اكتب للبحث 👇</blockquote>",
            reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
        )

    elif data in ["ch_show_all", "ch_filter_active", "ch_filter_inactive"]:
        await query.answer()
        if not is_admin(int(user_id)) or not has_perm(int(user_id), "view_data"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        filter_type = "all" if data == "ch_show_all" else ("active" if data == "ch_filter_active" else "inactive")
        await query.edit_message_text("<blockquote>⏳ جاري التحميل...</blockquote>")
        await _show_channels(client, query.message, filter_type=filter_type)

    elif data in ["usr_show_all", "usr_filter_active", "usr_filter_banned"]:
        await query.answer()
        if not is_admin(int(user_id)) or not has_perm(int(user_id), "view_data"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        filter_type = "all" if data == "usr_show_all" else ("active" if data == "usr_filter_active" else "banned")
        await query.edit_message_text("<blockquote>⏳ جاري التحميل...</blockquote>")
        await _show_users(client, query.message, filter_type=filter_type)

    elif data == "ch_filter":
        await query.answer()
        if not is_admin(int(user_id)) or not has_perm(int(user_id), "view_data"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await query.edit_message_reply_markup(
            InlineKeyboardMarkup([
                [InlineKeyboardButton("🟢 البث النشط", callback_data="ch_filter_active")],
                [InlineKeyboardButton("🔴 البث المتوقف", callback_data="ch_filter_inactive")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="ch_back")],
            ])
        )

    elif data == "usr_filter":
        await query.answer()
        if not is_admin(int(user_id)) or not has_perm(int(user_id), "view_data"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await query.edit_message_reply_markup(
            InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ المستخدمين النشطين", callback_data="usr_filter_active")],
                [InlineKeyboardButton("🚫 المحظورين", callback_data="usr_filter_banned")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="usr_back")],
            ])
        )

    elif data == "ch_back":
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        total = sum(len(u.get("channels", {})) for u in user_data.values())
        active = sum(1 for u in user_data.values() for ch in u.get("channels", {}).values() if "process" in ch)
        await query.edit_message_text(
            f"<blockquote>📢 القنوات\n\n"
            f"📊 الإجمالي: {total} قناة\n"
            f"🟢 نشطة: {active}\n"
            f"🔴 متوقفة: {total - active}</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 بحث", callback_data="ch_search")],
                [InlineKeyboardButton("⚡️ تصفية", callback_data="ch_filter")],
                [InlineKeyboardButton("📋 عرض الكل", callback_data="ch_show_all")],
            ])
        )

    elif data == "usr_back":
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        total = len(user_data)
        active = sum(1 for u in user_data.values() for ch in u.get("channels", {}).values() if "process" in ch)
        await query.edit_message_text(
            f"<blockquote>👥 المستخدمين\n\n"
            f"📊 الإجمالي: {total} مستخدم\n"
            f"🟢 لديهم بث نشط: {active}\n"
            f"🚫 المحظورون: {len(banned_users)}</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 بحث", callback_data="usr_search")],
                [InlineKeyboardButton("⚡️ تصفية", callback_data="usr_filter")],
                [InlineKeyboardButton("📋 عرض الكل", callback_data="usr_show_all")],
            ])
        )

    elif data == "toggle_stop_notify":
        await query.answer()
        broadcast_stop_notify = not broadcast_stop_notify
        save_settings()
        _txt, _kb = build_adv_settings_msg()
        await query.edit_message_text(_txt, reply_markup=_kb)

    elif data == "toggle_weekly_report":
        await query.answer()
        weekly_report_enabled = not weekly_report_enabled
        save_settings()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        weekly_status = "🟢 مفعّل" if weekly_report_enabled else "🔴 موقوف"
        await query.edit_message_text(
            f"<blockquote>📊 إدارة التقرير الأسبوعي\n\nالحالة: {weekly_status}\nاليوم: {DAYS_AR.get(weekly_report_day, '')}\nالوقت: {weekly_report_time}</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 التقرير: " + ("إيقاف ✅" if weekly_report_enabled else "تفعيل ❌"), callback_data="toggle_weekly_report")],
                [InlineKeyboardButton("📅 تعديل الموعد", callback_data="set_weekly_report_sched")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="adv_settings_back")],
            ])
        )

    elif data == "set_weekly_report_sched":
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        days_buttons = [
            [InlineKeyboardButton(f"{'✅ ' if weekly_report_day == d else ''}{name}", callback_data=f"wreport_day_{d}")]
            for d, name in DAYS_AR.items()
        ]
        await query.edit_message_text(
            f"<blockquote>📅 موعد التقرير الأسبوعي\n\nاليوم: {DAYS_AR.get(weekly_report_day, '')}\nالوقت: {weekly_report_time}\n\nاختر اليوم:</blockquote>",
            reply_markup=InlineKeyboardMarkup(
                days_buttons + [
                    [InlineKeyboardButton("🕐 تغيير الوقت", callback_data="wreport_time")],
                ]
            )
        )

    elif data.startswith("wreport_day_"):
        await query.answer()
        weekly_report_day = int(data.split("_")[-1])
        save_settings()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        days_buttons = [
            [InlineKeyboardButton(f"{'✅ ' if weekly_report_day == d else ''}{name}", callback_data=f"wreport_day_{d}")]
            for d, name in DAYS_AR.items()
        ]
        await query.edit_message_reply_markup(InlineKeyboardMarkup(
            days_buttons + [[InlineKeyboardButton("🕐 تغيير الوقت", callback_data="wreport_time")]]
        ))
        await query.answer(f"✅ تم اختيار {DAYS_AR[weekly_report_day]}")

    elif data == "wreport_time":
        await query.answer()
        _h, _m = map(int, weekly_report_time.split(":"))
        await query.edit_message_text(
            "<blockquote>🕐 تغيير وقت التقرير الأسبوعي\n\nاستخدم الأزرار:</blockquote>",
            reply_markup=build_time_picker_kb(_h, _m, "wreport", weekly_report_time)
        )

    elif data == "toggle_backup_threshold":
        await query.answer()
        backup_on_new_users = not backup_on_new_users
        save_settings()
        await query.answer("✅ تم " + ("تفعيل" if backup_on_new_users else "إيقاف") + " الـ Backup التلقائي")

    elif data == "set_backup_threshold":
        await query.answer()
        user_state[user_id] = {"step": "awaiting_backup_threshold"}
        await query.edit_message_text(
            f"<blockquote>🔢 تغيير عدد المستخدمين للـ Backup\n\nالعدد الحالي: {backup_user_threshold}\n\nاكتب العدد الجديد:</blockquote>"
        )
        await query.message.reply_text(
            "<blockquote>اكتب العدد 👇</blockquote>",
            reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
        )

    elif data == "set_fail_threshold":
        await query.answer()
        user_state[user_id] = {"step": "awaiting_fail_threshold"}
        await query.edit_message_text(
            f"<blockquote>⚠️ تغيير حد الفشل\n\nالحد الحالي: {broadcast_fail_threshold} مرات\n\nاكتب العدد الجديد:</blockquote>"
        )
        await query.message.reply_text(
            "<blockquote>اكتب العدد 👇</blockquote>",
            reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
        )

    elif data.startswith("user_stats_"):
        uid = data[len("user_stats_"):]
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        user_info = user_data.get(uid, {})
        try:
            u = await app.get_users(int(uid))
            name = u.first_name or "غير معروف"
            username = f"@{u.username}" if u.username else "بدون يوزر"
            user_link = get_user_link(uid, u.username if u.username else None)
        except Exception:
            name = "غير معروف"
            username = "بدون يوزر"
            user_link = None
        channels = user_info.get("channels", {})
        active = sum(1 for ch in channels.values() if "process" in ch)
        broadcast_count = user_info.get("broadcast_count", 0)
        join_date = user_info.get("join_date", "غير معروف")
        last_seen = user_info.get("last_seen", "غير معروف")
        last_broadcast = user_info.get("last_broadcast", "لم يبث بعد")
        is_banned = int(uid) in banned_users
        note = user_notes.get(uid, "لا توجد ملاحظات")
        stations_used = set()
        for ch in channels.values():
            s = ch.get("station", "")
            if s:
                sname = next((v["name"] for v in ST_TIMO.values() if v["url"] == s), None)
                if sname:
                    stations_used.add(sname.replace("إذاعة ", "").strip())
        stations_text = "\n".join([f"• {s}" for s in stations_used]) if stations_used else "لا يوجد"
        text_msg = (
            f"<blockquote>📊 إحصائيات المستخدم\n\n"
            f"👤 الاسم: {name}\n"
            f"🔗 اليوزر: {username}\n"
            f"🆔 المعرف: {uid}\n"
            f"📅 تاريخ الانضمام: {join_date}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📢 القنوات: {len(channels)}\n"
            f"🟢 البثوث النشطة: {active}\n"
            f"🎙 إجمالي البثوث: {broadcast_count}\n"
            f"🕐 آخر بث: {last_broadcast}\n"
            f"👁 آخر نشاط: {last_seen}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📻 المحطات المستخدمة:\n{stations_text}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📝 ملاحظة: {note}\n"
            f"{'🚫 محظور' if is_banned else '✅ نشط'}</blockquote>"
        )
        row1 = []
        if user_link:
            row1.append(InlineKeyboardButton(f"👤 {name}", url=user_link))
        if is_banned:
            row1.append(InlineKeyboardButton("✅ رفع الحظر", callback_data=f"unban_{uid}"))
        else:
            row1.append(InlineKeyboardButton("🚫 حظر", callback_data=f"quick_ban_{uid}"))
        await query.edit_message_text(
            text_msg,
            reply_markup=InlineKeyboardMarkup([
                row1,
                [InlineKeyboardButton("📝 تعديل الملاحظة", callback_data=f"add_note_{uid}")],
                [InlineKeyboardButton("💬 إرسال رسالة", callback_data=f"send_msg_{uid}")],
            ])
        )

    elif data.startswith("view_note_"):
        uid = data[len("view_note_"):]
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        note = user_notes.get(uid, "")
        if not note:
            await query.answer("📄 لا توجد ملاحظات لهذا المستخدم", show_alert=True)
            return
        await query.edit_message_text(
            f"<blockquote>📝 ملاحظة المستخدم {uid}\n\n{note}</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ تعديل", callback_data=f"add_note_{uid}")],
                [InlineKeyboardButton("🗑 حذف", callback_data=f"del_note_{uid}")],
            ])
        )

    elif data.startswith("send_msg_"):
        uid = data[len("send_msg_"):]
        await query.answer()
        user_state[user_id] = {"step": "awaiting_send_msg", "target_uid": uid}
        try:
            u = await app.get_users(int(uid))
            target_name = u.first_name or uid
        except Exception:
            target_name = uid
        await query.edit_message_text(
            f"<blockquote>💬 إرسال رسالة لـ {target_name}\n\nاكتب الرسالة:</blockquote>"
        )
        await query.message.reply_text(
            "<blockquote>اكتب الرسالة 👇</blockquote>",
            reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
        )

    elif data.startswith("add_note_"):
        uid = data[len("add_note_"):]
        await query.answer()
        user_state[user_id] = {"step": "awaiting_user_note", "note_uid": uid}
        current_note = user_notes.get(uid, "لا توجد ملاحظات")
        await query.edit_message_text(
            f"<blockquote>📝 إضافة ملاحظة\n\nالملاحظة الحالية:\n{current_note}\n\nاكتب الملاحظة الجديدة:\n(أرسل - للحذف)</blockquote>"
        )
        await query.message.reply_text(
            "<blockquote>اكتب الملاحظة 👇</blockquote>",
            reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
        )

    elif data.startswith("del_note_"):
        uid = data[len("del_note_"):]
        await query.answer()
        user_notes.pop(uid, None)
        save_settings()
        await query.edit_message_text("<blockquote>✅ تم حذف الملاحظة</blockquote>")

    elif data == "edit_admin_perms":
        await query.answer()
        if int(user_id) != OWNER_ID:
            await query.answer("❌ للمطور فقط", show_alert=True)
            return
        admins_list = [aid for aid in ADMIN_ID if aid != OWNER_ID]
        if not admins_list:
            await query.answer("❌ لا يوجد أدمنز مضافون", show_alert=True)
            return
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        for aid in admins_list:
            try:
                u = await app.get_users(aid)
                label = f"⚙️ {u.first_name}"
            except Exception:
                label = f"⚙️ {aid}"
            buttons.append([InlineKeyboardButton(label, callback_data=f"manage_admin_{aid}")])
        await query.edit_message_text(
            "<blockquote>⚙️ تعديل الصلاحيات\n\nاختر الأدمن:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "promote_admin_btn":
        await query.answer()
        if int(user_id) != OWNER_ID:
            await query.answer("❌ للمطور فقط", show_alert=True)
            return
        user_state[user_id] = {"step": "awaiting_promote_id"}
        await query.edit_message_text(
            "<blockquote>✨ تعيين أدمن جديد\n\nأرسل ID المستخدم:</blockquote>"
        )
        await query.message.reply_text(
            "<blockquote>أرسل الـ ID 👇</blockquote>",
            reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
        )

    elif data == "demote_admin_btn":
        await query.answer()
        if int(user_id) != OWNER_ID:
            await query.answer("❌ للمطور فقط", show_alert=True)
            return
        admins_list = [aid for aid in ADMIN_ID if aid != OWNER_ID]
        if not admins_list:
            await query.answer("❌ لا يوجد أدمنز", show_alert=True)
            return
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        for aid in admins_list:
            try:
                u = await app.get_users(aid)
                label = f"🗑 {u.first_name}"
            except Exception:
                label = f"🗑 {aid}"
            buttons.append([InlineKeyboardButton(label, callback_data=f"demote_{aid}")])
        await query.edit_message_text(
            "<blockquote>🗑 إقالة أدمن\n\nاختر الأدمن:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "whitelist_add":
        await query.answer()
        if not is_admin(int(user_id)) or not has_perm(int(user_id), "ban"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        user_state[user_id] = {"step": "awaiting_whitelist_add"}
        await query.edit_message_text(
            "<blockquote>➕ إضافة مستخدم لقائمة الإعفاء\n\nأرسل ID المستخدم:</blockquote>"
        )
        await query.message.reply_text(
            "<blockquote>أرسل الـ ID 👇</blockquote>",
            reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
        )

    elif data == "whitelist_remove":
        await query.answer()
        if not is_admin(int(user_id)) or not has_perm(int(user_id), "ban"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        if not whitelist_users:
            await query.edit_message_text("<blockquote>📋 قائمة الإعفاء فارغة</blockquote>")
            return
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        for uid in list(whitelist_users):
            try:
                u = await app.get_users(int(uid))
                label = f"➖ {u.first_name} ({uid})"
            except Exception:
                label = f"➖ {uid}"
            buttons.append([InlineKeyboardButton(label, callback_data=f"whitelist_del_{uid}")])
        await query.edit_message_text(
            "<blockquote>➖ اختر المستخدم لإزالته من الإعفاء:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "whitelist_view":
        await query.answer()
        if not whitelist_users:
            await query.edit_message_text("<blockquote>🛡 قائمة الإعفاء فارغة حالياً</blockquote>")
            return
        text_msg = f"<blockquote>🛡 قائمة الإعفاء ({len(whitelist_users)} مستخدم)\n\n"
        for uid in list(whitelist_users):
            try:
                u = await app.get_users(int(uid))
                name = u.first_name or "غير معروف"
                username = f"@{u.username}" if u.username else "بدون يوزر"
                text_msg += f"👤 {name} | {username} | {uid}\n"
            except Exception:
                text_msg += f"🆔 {uid}\n"
        text_msg += "</blockquote>"
        await query.edit_message_text(text_msg)

    elif data.startswith("whitelist_del_"):
        await query.answer()
        target_id = int(data[len("whitelist_del_"):])
        whitelist_users.discard(target_id)
        save_settings()
        await query.edit_message_text(
            f"<blockquote>✅ تم إزالة {target_id} من قائمة الإعفاء</blockquote>"
        )

    elif data.startswith("quick_ban_"):
        await query.answer()
        if not is_admin(int(user_id)) or not has_perm(int(user_id), "ban"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        target_id = int(data[10:])
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        await query.edit_message_reply_markup(
            InlineKeyboardMarkup([
                [InlineKeyboardButton("🔴 سبام", callback_data=f"ban_reason_سبام_{target_id}")],
                [InlineKeyboardButton("⚠️ إساءة", callback_data=f"ban_reason_إساءة_{target_id}")],
                [InlineKeyboardButton("🚫 انتهاك القوانين", callback_data=f"ban_reason_انتهاك القوانين_{target_id}")],
                [InlineKeyboardButton("✏️ شيء آخر", callback_data=f"ban_reason_other_{target_id}")],
                [InlineKeyboardButton("❌ إلغاء", callback_data=f"ban_reason_cancel_{target_id}")]
            ])
        )

    elif data.startswith("ban_reason_"):
        await query.answer()
        rest = data[len("ban_reason_"):]
        if rest.startswith("cancel_"):
            user_state.pop(user_id, None)
            await query.edit_message_text("<blockquote>❌ تم إلغاء الحظر</blockquote>")
            return
        if rest.startswith("other_"):
            target_id = int(rest[6:])
            user_state[user_id] = {"step": "awaiting_ban_custom_reason", "ban_target_id": target_id}
            await query.edit_message_text(
                "<blockquote>✏️ اكتب سبب الحظر:</blockquote>",
                reply_markup=None
            )
            await query.message.reply_text(
                "<blockquote>اكتب السبب الآن 👇</blockquote>",
                reply_markup=ReplyKeyboardMarkup([["إلغاء"]], resize_keyboard=True)
            )
            return
        # سبب جاهز
        parts = rest.rsplit("_", 1)
        reason = parts[0]
        target_id = int(parts[1])
        await _do_ban(query, user_id, target_id, reason, admin_keyboard)
        user_state.pop(user_id, None)

    elif data.startswith("unban_"):
        await query.answer()
        if not is_admin(int(user_id)) or not has_perm(int(user_id), "ban"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        target_id = int(data[6:])
        if target_id in banned_users:
            banned_users.discard(target_id)
            banned_users_data.pop(str(target_id), None)
            save_settings()
            try:
                await app.send_message(target_id, "<blockquote>✅ تم رفع الحظر عنك، يمكنك استخدام البوت الآن.</blockquote>",
                disable_web_page_preview=True)
            except Exception as e:
                logger.error(f"unban notify error: {e}")
            await query.edit_message_text(
                f"<blockquote>✅ تم رفع الحظر عن المستخدم {target_id} بنجاح</blockquote>"
            )
        else:
            await query.answer("❌ هذا المستخدم غير محظور", show_alert=True)

    elif data == "daily_report_time":
        await query.answer()
        if not is_admin(int(user_id)) or not has_perm(int(user_id), "daily_report"):
            await query.answer("❌ غير مصرح", show_alert=True)
            return
        h, m = map(int, daily_report_time.split(":"))
        await query.edit_message_text(
            "<blockquote>🕐 تغيير وقت التقرير اليومي\n\nاستخدم الأزرار:</blockquote>",
            reply_markup=build_time_picker_kb(h, m, "daily_report", daily_report_time)
        )

    elif data.startswith("sched_add_cat_"):
        cat_name = data[len("sched_add_cat_"):]
        await query.answer()
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        station_ids = ST_CATEGORIES.get(cat_name, [])
        buttons = []
        row = []
        for i, sid in enumerate(station_ids, 1):
            name = ST_TIMO[sid]["name"].replace("إذاعة ", "").replace("اذاعة ", "").replace("قناة ", "").strip()
            row.append(InlineKeyboardButton(f"{i}. {name}", callback_data=f"sched_add_pick_{sid}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        await query.edit_message_text(
            f"<blockquote>➕ إضافة محطة — {cat_name}\n\nاختر المحطة:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("sched_add_pick_"):
        sid = data[len("sched_add_pick_"):]
        await query.answer()
        if sid not in ST_TIMO:
            await query.answer("❌ محطة غير موجودة", show_alert=True)
            return
        user_state[user_id] = {"step": "awaiting_sched_add_time", "sched_add_sid": sid}
        station_name = ST_TIMO[sid]["name"]
        h, m = 8, 0
        await query.edit_message_text(
            f"<blockquote>➕ إضافة: {station_name}\n\nاختر الوقت:</blockquote>",
            reply_markup=build_time_picker_kb(h, m, "sched_add", sid)
        )

    elif data.startswith("sched_del_"):
        t = data[len("sched_del_"):]
        await query.answer()
        if t in AUTO_SCHEDULE:
            del AUTO_SCHEDULE[t]
            schedule_disabled.discard(t)
            save_settings()
            await query.edit_message_text(
                f"<blockquote>✅ تم حذف محطة الساعة {t} من الجدول</blockquote>"
            )
        else:
            await query.answer("❌ الموعد غير موجود", show_alert=True)

    elif data.startswith("ch_sched_toggle_"):
        await query.answer()
        ch_id = data[len("ch_sched_toggle_"):]
        current = channel_schedule_enabled.get(ch_id, True)
        channel_schedule_enabled[ch_id] = not current
        save_settings()
        new_status = "✅ مفعّل" if not current else "❌ موقوف"
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        # تحديث الأزرار
        channels = user_data.get(user_id, {}).get("channels", {})
        ch_buttons = []
        for cid, ch_info in list(channels.items()):
            ch_enabled = channel_schedule_enabled.get(cid, True)
            status_icon = "✅" if ch_enabled else "❌"
            ch_buttons.append([InlineKeyboardButton(
                f"{status_icon} {ch_info.get('title', cid)}",
                callback_data=f"ch_sched_toggle_{cid}"
            )])
        await query.edit_message_reply_markup(InlineKeyboardMarkup(ch_buttons))
        await query.answer(f"الجدول: {new_status}")

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
            save_admins()
            try:
                u = await app.get_users(target_id)
                name = u.first_name
                await app.send_message(
                    target_id,
                    "<blockquote>⚠️ تم إزالة صلاحيات الأدمن منك في بوت أثير القرآن</blockquote>",
                disable_web_page_preview=True
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
        # إشعار الأدمن بفتح الدعم الفني
        if not is_admin(int(user_id)) and broadcast_notify_enabled:
            try:
                try:
                    _su = await app.get_users(int(user_id))
                    _sname = _su.first_name or "غير معروف"
                    _susername = f"@{_su.username}" if _su.username else "بدون يوزر"
                    _slink = get_user_link(user_id, _su.username if _su.username else None)
                except Exception:
                    _sname = str(user_id)
                    _susername = "بدون يوزر"
                    _slink = get_user_link(user_id)
                support_notify = (
                    f"<blockquote>🛠 مستخدم فتح الدعم الفني\n\n"
                    f"👤 الاسم: {_sname}\n"
                    f"🔗 اليوزر: {_susername}\n"
                    f"🆔 المعرف: {user_id}\n"
                    f"📅 الوقت: {egypt_strftime()}</blockquote>"
                )
                await app.send_message(
                    ADMIN_ID[0], support_notify,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(f"👤 {_sname}", url=_slink)],
                        [InlineKeyboardButton("💬 إرسال رسالة", callback_data=f"send_msg_{user_id}")]
                    ]),
                    disable_web_page_preview=True
                )
            except Exception as e:
                logger.error(f"support notify error: {e}")
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

        if "process" in channel_info and is_ffmpeg_running(channel_info["process"]):
            await query.answer(
                "📡 عذرًا، يوجد بث مُفعل حاليًا على هذه القناة\n• يرجى إيقاف البث أولًا قبل تغيير الإذاعة.",
                show_alert=True
            )
            return

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
            user_data[user_id]["channels"][channel_id]["station"] = selected_station
            user_data[user_id]["temp_station"] = selected_station
            # عداد البثوث
            user_data[user_id]["broadcast_count"] = user_data[user_id].get("broadcast_count", 0) + 1
            user_data[user_id]["last_broadcast"] = egypt_strftime()
            save_data()
        except Exception as ffmpeg_err:
            logger.error(f"FFmpeg failed to start: {ffmpeg_err}")
            await query.answer(f"❌ فشل تشغيل البث: {ffmpeg_err}", show_alert=True)
            return

        await send_broadcast_notification(client, channel_info['chat_id'], selected_station, user_id)

        station_name_notify = next((v["name"] for v in ST_TIMO.values() if v["url"] == selected_station), "غير معروف")
        if int(user_id) != OWNER_ID and broadcast_notify_enabled:
            try:
                from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                try:
                    u = await app.get_users(int(user_id))
                    uname = u.first_name or "غير معروف"
                    uusername = f"@{u.username}" if u.username else "بدون يوزر"
                    user_link = get_user_link(user_id, u.username if u.username else None)
                except Exception:
                    uname = str(user_id)
                    uusername = "بدون يوزر"
                    user_link = get_user_link(user_id)

                ch_url = None
                try:
                    chat = await app.get_chat(int(channel_id))
                    if chat.username:
                        ch_url = f"https://t.me/{chat.username}"
                    elif chat.invite_link:
                        ch_url = chat.invite_link
                except Exception:
                    pass

                text_notify = (
                    f"<blockquote>📡 مستخدم بدأ البث\n\n"
                    f"👤 الاسم: {uname}\n"
                    f"🔗 اليوزر: {uusername}\n"
                    f"🆔 المعرف: {user_id}\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"📢 القناة: {channel_info['title']}\n"
                    f"🎙 المحطة: {station_name_notify}\n"
                    f"📅 الوقت: {egypt_strftime()}</blockquote>"
                )
                row = [InlineKeyboardButton(f"👤 {uname}", url=user_link)]
                if ch_url:
                    row.append(InlineKeyboardButton("📢 دخول القناة", url=ch_url))
                await app.send_message(
                    ADMIN_ID[0], text_notify,
                    reply_markup=InlineKeyboardMarkup([row]),
                    disable_web_page_preview=True
                )
                # إرسال نسخة لقناة الأدمن
                try:
                    await app.send_message(
                        BACKUP_CHANNEL_ID, text_notify,
                        reply_markup=InlineKeyboardMarkup([row]),
                        disable_web_page_preview=True
                    )
                except Exception as e:
                    logger.error(f"broadcast notify channel error: {e}")
            except Exception as e:
                logger.error(f"broadcast notify admin error: {e}")
        broadcast_stats[channel_id] = {
            "station": station_name_notify,
            "start_time": egypt_strftime("%Y-%m-%d %I:%M:%S %p").replace("AM", "ص").replace("PM", "م"),
            "user_id": user_id
        }
        broadcast_start_times[channel_id] = time.time()
        save_broadcast_state()
        save_broadcast_stats_file()
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

@app.on_message(filters.command("checkrefresh") & filters.private)
async def checkrefresh_command(client, message):
    if message.from_user.id != OWNER_ID:
        return
    uid = str(OWNER_ID)
    enabled = auto_refresh_enabled.get(uid, False)
    interval = auto_refresh_interval.get(uid, 30)
    station = user_data.get(uid, {}).get("temp_station", "None")
    channels = user_data.get(uid, {}).get("channels", {})
    active = sum(1 for c in channels.values() if "process" in c)
    await message.reply_text(
        f"<blockquote>🔍 فحص التحديث التلقائي\n\n"
        f"مفعّل: {'✅' if enabled else '❌'}\n"
        f"الفترة: {interval} دقيقة\n"
        f"المحطة: {station[:50] if station else 'None'}\n"
        f"القنوات النشطة: {active}\n"
        f"إجمالي auto_refresh_enabled: {auto_refresh_enabled}</blockquote>"
    )

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
                                ("/data/admins_backup.json",              "👑 الأدمنز"),
        ]
        sent_count = 0
        for path, label in files:
            if os.path.exists(path):
                size = os.path.getsize(path)
                size_kb = round(size / 1024, 1)
                await app.send_document(
                    OWNER_ID,
                    document=path,
                    caption=f"<blockquote>{label}\n📁 الحجم: {size_kb} KB\n🕐 {egypt_strftime()}</blockquote>"
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
    global backup_last_count
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
                "join_date": egypt_strftime("%Y-%m-%d %I:%M:%S %p").replace("AM", "ص").replace("PM", "م")
            }
            save_data()
            # backup تلقائي عند عدد معين
            if backup_on_new_users:
                current_count = len(user_data)
                if current_count - backup_last_count >= backup_user_threshold:
                    backup_last_count = current_count
                    async def send_threshold_backup():
                        try:
                            await app.send_message(
                                BACKUP_CHANNEL_ID,
                                f"<blockquote>📦 نسخة احتياطية تلقائية\n"
                                f"السبب: وصل عدد المستخدمين لـ {current_count}\n"
                                f"📅 {egypt_strftime()}</blockquote>"
                            )
                            files = [
                                ("/data/user_data.json", "👥 بيانات المستخدمين"),
                                ("/data/settings.json", "⚙️ الإعدادات"),
                            ]
                            for path, label in files:
                                if os.path.exists(path):
                                    await app.send_document(BACKUP_CHANNEL_ID, document=path,
                                        caption=f"<blockquote>{label}</blockquote>")
                        except Exception as ex:
                            logger.error(f"Threshold backup error: {ex}")
                    asyncio.run_coroutine_threadsafe(send_threshold_backup(), _bot_loop)

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
            if welcome_text:
                custom = welcome_text.replace("{name}", message.from_user.first_name)
                caption = f"<blockquote>{custom}</blockquote>"
            else:
                caption = (
                    "<blockquote>• مرحبا بك " + message.from_user.first_name + "\n"
                    "• في بوت أثير القرآن\n"
                    "• المقدم من المطور 𝑨𝒃𝒐 𝑵𝒖𝒘𝒂𝒇</blockquote>"
                )
        # إضافة زرار الشرح للمستخدمين فقط
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        guide_btn = None
        if not is_admin(message.from_user.id):
            guide_btn = InlineKeyboardMarkup([
                [InlineKeyboardButton("📖 كيفية استخدام البوت", callback_data="guide_menu")]
            ])
        try:
            await message.reply_photo(
                photo=IMAGE_TIMO,
                caption=caption,
                reply_markup=guide_btn if guide_btn else keyboard
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

            
    except Exception as e:
        logger.error(f"Error in /start: {e}")
        await message.reply_text("حدث خطأ، الرجاء المحاولة لاحقًا")


@app.on_message(filters.text & filters.private)
async def handle_text(client, message):
    global max_users_enabled, max_users_limit, daily_report_enabled, night_mode_enabled
    global broadcast_notify_enabled, night_mode_start, night_mode_end, about_bot_visible
    global auto_schedule_enabled, maintenance_mode, broadcast_notify_enabled
    global welcome_text, auto_cleanup_days, archive_display_count, broadcast_fail_threshold
    global backup_user_threshold, auto_cleanup_enabled, broadcast_stop_notify
    global weekly_report_enabled, weekly_report_day, weekly_report_time
    global backup_on_new_users, backup_last_count, whitelist_users, user_notes
    global deleted_users_archive, broadcast_fail_count, daily_report_enabled
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
                "• @channel_name\n"
                "• https://t.me/channel_name\n\n"
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
                        # إشعار إيقاف البث
                        if broadcast_stop_notify and int(user_id) != OWNER_ID:
                            try:
                                from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                                try:
                                    _su = await app.get_users(int(user_id))
                                    _sname = _su.first_name or "غير معروف"
                                    _susername = f"@{_su.username}" if _su.username else "بدون يوزر"
                                    _slink = get_user_link(user_id, _su.username if _su.username else None)
                                except Exception:
                                    _sname = str(user_id)
                                    _susername = "بدون يوزر"
                                    _slink = get_user_link(user_id)
                                stop_text = (
                                    f"<blockquote>⏹ مستخدم أوقف البث\n\n"
                                    f"👤 الاسم: {_sname}\n"
                                    f"🔗 اليوزر: {_susername}\n"
                                    f"🆔 المعرف: {user_id}\n"
                                    f"━━━━━━━━━━━━━━━━\n"
                                    f"📢 القناة: {channel_info.get('title', channel_id)}\n"
                                    f"📅 الوقت: {egypt_strftime()}</blockquote>"
                                )
                                from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                                _srow = [InlineKeyboardButton(f"👤 {_sname}", url=_slink)]
                                await app.send_message(
                                    ADMIN_ID[0], stop_text,
                                    reply_markup=InlineKeyboardMarkup([_srow]),
                                    disable_web_page_preview=True
                                )
                            except Exception:
                                pass
                    except Exception as e:
                        logger.error(f"Error stopping broadcast: {e}")            
            save_data()
            if stopped > 0:
                await message.reply_text(
                    f"<blockquote>⏹ تم إيقاف البث بنجاح\n\n"
                    f"📢 القنوات المتوقفة: {stopped}\n"
                    f"📅 الوقت: {egypt_strftime()}</blockquote>"
                )
            else:
                await message.reply_text("<blockquote>ℹ️ لا يوجد بث نشط حالياً</blockquote>")
        elif text == "قنواتي":
            if user_id not in user_data or not user_data[user_id].get("channels"):
                await message.reply_text("<blockquote> • لا توجد قنوات مضافة!</blockquote>")
                return
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            channels = user_data[user_id]["channels"]
            total = len(channels)
            active = sum(1 for ch in channels.values() if "process" in ch)
            station_url = user_data[user_id].get("temp_station", "")
            station_name = next((v["name"] for v in ST_TIMO.values() if v["url"] == station_url), "لا يوجد")
            buttons = []
            for channel_id, info in list(channels.items()):
                status_icon = "🟢" if "process" in info else "🔴"
                buttons.append([InlineKeyboardButton(
                    f"{status_icon} {info['title']}",
                    callback_data=f"myc_details_{channel_id}"
                )])
            await message.reply_text(
                f"<blockquote>📢 قنواتي\n\n"
                f"📊 الإجمالي: {total} قناة\n"
                f"🟢 نشطة: {active}\n"
                f"🔴 متوقفة: {total - active}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"🎙 المحطة الحالية: {station_name}</blockquote>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )     


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
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            channels = user_data[user_id]["channels"]
            buttons = [
                [InlineKeyboardButton(f"🗑 {info['title']}", callback_data=f"del_channel_{ch_id}")]
                for ch_id, info in list(channels.items())
            ]
            buttons.append([InlineKeyboardButton("❌ إلغاء", callback_data="del_channel_cancel")])
            await message.reply_text(
                "<blockquote>🗑 اختر القناة التي تريد حذفها:</blockquote>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        elif text == "⚙️ الجدول والمواعيد":
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            uid = user_id
            u_night = user_data.get(uid, {}).get("night_mode_enabled", False)
            if is_admin(int(user_id)):
                is_active = auto_schedule_enabled
            else:
                is_active = user_schedule_enabled.get(user_id, False)
            sched_status = "✅ مفعّل" if is_active else "❌ موقوف"
            night_status = "✅ مفعّل" if u_night else "❌ موقوف"
            await message.reply_text(
                f"<blockquote>⚙️ الجدول والمواعيد\n\n"
                f"📅 جدول التشغيل التلقائي: {sched_status}\n"
                f"🌙 الوضع الليلي: {night_status}</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📅 جدول التشغيل التلقائي", callback_data="open_auto_schedule")],
                    [InlineKeyboardButton("🌙 الوضع الليلي", callback_data=f"open_night_mode_{uid}")],
                ])
            )

        elif text == "⚙️ جدول التشغيل التلقائي":
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            if is_admin(int(user_id)):
                is_active = auto_schedule_enabled
            else:
                is_active = user_schedule_enabled.get(user_id, False)
            status = "✅ مفعل" if is_active else "❌ متوقف"
            buttons = build_schedule_buttons()
            await message.reply_text(
                f"<blockquote>⚙️ جدول التشغيل التلقائي\nالحالة: {status}\n\n"
                "✅ = مفعّل  |  ❌ = موقوف\n\n"
                "✏️ تعديل موعد — لتغيير وقت إذاعة\n"
                "🎙 تغيير محطة — لتغيير محطة وقت معين</blockquote>",
                reply_markup=InlineKeyboardMarkup(buttons) if buttons else schedule_keyboard()
            )
            await message.reply_text(
                "<blockquote>اضغط تشغيل أو إيقاف لكل محطة 👆</blockquote>",
                reply_markup=schedule_keyboard()
            )
            # عرض القنوات مع تحكم الجدول لكل واحدة
            channels = user_data.get(user_id, {}).get("channels", {})
            if channels:
                ch_buttons = []
                for ch_id, ch_info in list(channels.items()):
                    ch_enabled = channel_schedule_enabled.get(ch_id, True)
                    status_icon = "✅" if ch_enabled else "❌"
                    ch_buttons.append([InlineKeyboardButton(
                        f"{status_icon} {ch_info.get('title', ch_id)}",
                        callback_data=f"ch_sched_toggle_{ch_id}"
                    )])
                await message.reply_text(
                    "<blockquote>📢 الجدول لكل قناة:\n✅ مفعّل | ❌ موقوف</blockquote>",
                    reply_markup=InlineKeyboardMarkup(ch_buttons)
                )

        elif text.startswith("🌙 الوضع الليلي"):
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            uid = user_id
            u_night = user_data.get(uid, {}).get("night_mode_enabled", False)
            status = "✅ مفعّل" if u_night else "❌ موقوف"
            channels = user_data.get(uid, {}).get("channels", {})
            await message.reply_text(
                f"<blockquote>🌙 الوضع الليلي\n\n"
                f"الحالة: {status}\n\n"
                f"اختر القناة لإدارة جدولها الليلي:</blockquote>",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("✅ تفعيل" if not u_night else "❌ إيقاف",
                                         callback_data=f"unight_toggle_{uid}")]] +
                    [[InlineKeyboardButton(f"📢 {ch_info.get('title', ch_id)}", callback_data=f"unight_ch_{uid}_{ch_id}")]
                     for ch_id, ch_info in list(channels.items())]
                )
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
                "<blockquote>✅ تم تفعيل جدول التشغيل التلقائي على قنواتك</blockquote>",
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
                "<blockquote>❌ تم إيقاف جدول التشغيل التلقائي على قنواتك</blockquote>",
                reply_markup=schedule_keyboard()
            )


        elif text == "➕ إضافة محطة":
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            # عرض أقسام المحطات للاختيار
            buttons = []
            for cat_name, station_ids in ST_CATEGORIES.items():
                buttons.append([InlineKeyboardButton(cat_name, callback_data=f"sched_add_cat_{cat_name}")])
            await message.reply_text(
                "<blockquote>➕ إضافة محطة للجدول التلقائي\n\nاختر القسم:</blockquote>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        elif text == "🗑 حذف محطة":
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            if not AUTO_SCHEDULE:
                await message.reply_text("<blockquote>❌ الجدول فارغ</blockquote>")
                return
            buttons = []
            for t, s in list(AUTO_SCHEDULE.items()):
                name = s['name'].replace("إذاعة ", "").replace("اذاعة ", "").strip()
                buttons.append([InlineKeyboardButton(f"🗑 {t} — {name}", callback_data=f"sched_del_{t}")])
            await message.reply_text(
                "<blockquote>🗑 اختر المحطة التي تريد حذفها من الجدول:</blockquote>",
                reply_markup=InlineKeyboardMarkup(buttons)
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

            added_date = egypt_strftime()
            REQUIRED_CHANNELS.append({"id": channel_id_add, "url": channel_url_add, "title": channel_title, "custom_text": "", "added_by": str(user_id), "added_date": added_date})
            save_required_channels()
            user_state.pop(user_id, None)
            await message.reply_text(
                f"<blockquote>✅ تم إضافة القناة بنجاح\n"
                f"📢 {channel_title}\n"
                f"🆔 {channel_id_add}\n\n"
                f"📝 يوجد نص افتراضي يظهر تلقائياً للمستخدمين\n"
                f"💡 لو عايز تغيره — اضغط تعديل النص من قائمة الاشتراك الإجباري</blockquote>",
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
        elif text == "📊 الإحصائيات":
            if not is_admin(int(user_id)) or not has_perm(int(user_id), "stats"):
                await message.reply_text("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
                return
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            await message.reply_text(
                "<blockquote>📊 الإحصائيات\n\nاختر نوع الإحصائيات:</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🤖 إحصائيات البوت", callback_data="stats_bot"),
                        InlineKeyboardButton("📡 إحصائيات البث", callback_data="stats_broadcast"),
                    ]
                ])
            )

        elif text == "📢 الإذاعة":
            if not is_admin(int(user_id)) or not has_perm(int(user_id), "broadcast_msg"):
                await message.reply_text("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
                return
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            await message.reply_text(
                "<blockquote>📢 الإذاعة\n\nاختر نوع الإذاعة:</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("👥 للمستخدمين", callback_data="broadcast_users_menu"),
                        InlineKeyboardButton("📣 للقنوات", callback_data="broadcast_channels_menu"),
                    ]
                ])
            )

        elif text == "📊 إحصائيات البث":
            # لو أدمن يعرض الكل، لو مستخدم عادي يعرض قنواته بس
            active = []
            # كل مستخدم يشوف قنواته بس
            users_to_check = [(user_id, user_data.get(user_id, {}))]
            for uid, uinfo in users_to_check:
                for ch_id, ch_info in uinfo.get("channels", {}).items():
                    if "process" in ch_info and is_ffmpeg_running(ch_info["process"]):
                        station_url = ch_info.get("station", uinfo.get("temp_station", ""))
                        station_name = next((v["name"] for v in ST_TIMO.values() if v["url"] == station_url), "غير معروف")
                        active.append({
                            "channel_id": ch_id,
                            "channel": ch_info.get("title", ch_id),
                            "station": station_name,
                            "user_id": uid,
                        })
            if not active:
                await message.reply_text("<blockquote>📊 لا توجد بثوث نشطة حالياً</blockquote>")
                return
            stats_text = "<blockquote>📊 إحصائيات البث:\n\n"
            for a in active:
                ch_id = a["channel_id"]
                duration = get_broadcast_duration(ch_id)
                start_time = broadcast_stats.get(ch_id, {}).get("start_time", "غير معروف")
                stats_text += f"📡 اسم القناة: {a['channel']}\n"
                stats_text += f"🎙 المحطة: {a['station']}\n"
                stats_text += f"⏰ بدأ: {start_time}\n"
                stats_text += f"⏱ المدة: {duration}\n"
                stats_text += "▬▬▬▬▬▬▬▬▬▬\n"
            stats_text += "</blockquote>"
            await message.reply_text(stats_text)

        elif text == "👑 إدارة الأدمنز":
            if int(user_id) != OWNER_ID:
                await message.reply_text("<blockquote>❌ هذا الأمر للمطور فقط</blockquote>")
                return
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            admins_list = [aid for aid in ADMIN_ID if aid != OWNER_ID]
            buttons = []
            for aid in admins_list:
                try:
                    u = await app.get_users(aid)
                    label = f"👤 {u.first_name}"
                except Exception as e:
                    logger.error(f"get_users error for admin {aid}: {e}")
                    label = f"👤 {aid}"
                buttons.append([InlineKeyboardButton(label, callback_data=f"manage_admin_{aid}")])
            total_admins = len(admins_list)
            await message.reply_text(
                f"<blockquote>👑 إدارة الأدمنز\n\n"
                f"👥 عدد الأدمنز: {total_admins}\n\n"
                f"{'اختر أدمناً لتعديل صلاحياته:' if admins_list else 'لا يوجد أدمنز مضافون بعد'}</blockquote>",
                reply_markup=InlineKeyboardMarkup(
                    buttons + [
                        [InlineKeyboardButton("🛡 تعيين أدمن جديد", callback_data="promote_admin_btn")],
                        [InlineKeyboardButton("🗑 إقالة أدمن", callback_data="demote_admin_btn")],
                        [InlineKeyboardButton("⚙️ تعديل الصلاحيات", callback_data="edit_admin_perms")],
                    ]
                )
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
                    save_admins()
                    user_state.pop(user_id, None)
                    try:
                        u = await app.get_users(target_id)
                        name = u.first_name
                        await app.send_message(
                            target_id,
                            "<blockquote>👑 تهانينا!\n\nتم رفعك أدمناً في بوت أثير القرآن\nبإمكانك الآن الوصول للوحة التحكم الكاملة</blockquote>",
                disable_web_page_preview=True
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


        elif text == "🛡 قائمة الإعفاء":
            if not is_admin(int(user_id)) or not has_perm(int(user_id), "ban"):
                await message.reply_text("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
                return
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            await message.reply_text(
                f"<blockquote>🛡 قائمة الإعفاء من الحظر\n\n"
                f"👥 عدد المعفيين: {len(whitelist_users)}\n\n"
                f"المستخدمون في هذه القائمة لن يتم حظرهم تلقائياً\nولا يمكن حظرهم يدوياً</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ إضافة للإعفاء", callback_data="whitelist_add")],
                    [InlineKeyboardButton("➖ إزالة من الإعفاء", callback_data="whitelist_remove")],
                    [InlineKeyboardButton("📋 عرض القائمة", callback_data="whitelist_view")],
                ])
            )


        elif user_state.get(user_id, {}).get("step") == "awaiting_archive_count":
            if text == "إلغاء":
                user_state.pop(user_id, None)
                await message.reply_text("<blockquote>❌ تم إلغاء</blockquote>", reply_markup=admin_keyboard(user_id))
                return
            try:
                num = int(text.strip())
                if num < 1:
                    raise ValueError
                archive_display_count = num
                save_settings()
                user_state.pop(user_id, None)
                await message.reply_text(
                    f"<blockquote>✅ سيتم عرض {num} مستخدم في الأرشيف</blockquote>",
                    reply_markup=admin_keyboard(user_id)
                )
            except ValueError:
                await message.reply_text("<blockquote>❌ أدخل رقم صحيح أكبر من 0</blockquote>")

        elif user_state.get(user_id, {}).get("step") == "awaiting_restore_uid":
            if text == "إلغاء":
                user_state.pop(user_id, None)
                await message.reply_text("<blockquote>❌ تم إلغاء</blockquote>", reply_markup=admin_keyboard(user_id))
                return
            try:
                target_uid = text.strip()
                archived = next((u for u in deleted_users_archive if u["uid"] == target_uid), None)
                if not archived:
                    await message.reply_text("<blockquote>❌ المستخدم غير موجود في الأرشيف</blockquote>")
                    return
                # استعادة المستخدم
                user_data[target_uid] = {
                    "channels": {},
                    "temp_station": None,
                    "join_date": archived.get("join_date", egypt_strftime()),
                    "broadcast_count": archived.get("broadcast_count", 0)
                }
                deleted_users_archive.remove(archived)
                save_data()
                save_settings()
                user_state.pop(user_id, None)
                await message.reply_text(
                    f"<blockquote>✅ تم استعادة المستخدم {target_uid}\n\n"
                    f"📅 تاريخ انضمامه الأصلي: {archived.get('join_date', 'غير معروف')}</blockquote>",
                    reply_markup=admin_keyboard(user_id)
                )
            except Exception as e:
                await message.reply_text(f"<blockquote>❌ خطأ: {e}</blockquote>")

        elif user_state.get(user_id, {}).get("step") == "awaiting_send_msg":
            if text == "إلغاء":
                user_state.pop(user_id, None)
                await message.reply_text("<blockquote>❌ تم إلغاء</blockquote>", reply_markup=admin_keyboard(user_id))
                return
            target_uid = user_state[user_id].get("target_uid")
            user_state.pop(user_id, None)
            try:
                await app.send_message(
                    int(target_uid),
                    f"<blockquote>📨 رسالة من الأدمن\n\n{text}</blockquote>"
                )
                await message.reply_text(
                    f"<blockquote>✅ تم إرسال الرسالة بنجاح</blockquote>",
                    reply_markup=admin_keyboard(user_id)
                )
            except Exception as e:
                await message.reply_text(
                    f"<blockquote>❌ فشل الإرسال: {e}</blockquote>",
                    reply_markup=admin_keyboard(user_id)
                )

        elif user_state.get(user_id, {}).get("step") == "awaiting_user_note":
            if text == "إلغاء":
                user_state.pop(user_id, None)
                await message.reply_text("<blockquote>❌ تم إلغاء</blockquote>", reply_markup=admin_keyboard(user_id))
                return
            note_uid = user_state[user_id].get("note_uid")
            user_state.pop(user_id, None)
            if text.strip() == "-":
                user_notes.pop(note_uid, None)
                await message.reply_text("<blockquote>✅ تم حذف الملاحظة</blockquote>", reply_markup=admin_keyboard(user_id))
            else:
                user_notes[note_uid] = text.strip()
                await message.reply_text(
                    f"<blockquote>✅ تم حفظ الملاحظة\n\n📝 {text.strip()}</blockquote>",
                    reply_markup=admin_keyboard(user_id)
                )
            save_settings()

        elif user_state.get(user_id, {}).get("step") == "awaiting_welcome_text":
            if text == "إلغاء":
                user_state.pop(user_id, None)
                await message.reply_text("<blockquote>❌ تم إلغاء</blockquote>", reply_markup=admin_keyboard(user_id))
                return
            if text.strip() == "-":
                welcome_text = ""
                await message.reply_text("<blockquote>✅ تم الرجوع للنص الافتراضي</blockquote>", reply_markup=admin_keyboard(user_id))
            else:
                welcome_text = text.strip()
                preview = welcome_text.replace("{name}", "محمد")
                await message.reply_text(
                    f"<blockquote>✅ تم تغيير رسالة الترحيب\n\nمعاينة:\n{preview}</blockquote>",
                    reply_markup=admin_keyboard(user_id)
                )
            save_settings()
            user_state.pop(user_id, None)

        elif user_state.get(user_id, {}).get("step") == "awaiting_cleanup_days":
            if text == "إلغاء":
                user_state.pop(user_id, None)
                await message.reply_text("<blockquote>❌ تم إلغاء</blockquote>", reply_markup=admin_keyboard(user_id))
                return
            try:
                num = int(text.strip())
                if num < 1:
                    raise ValueError
                auto_cleanup_days = num
                save_settings()
                user_state.pop(user_id, None)
                await message.reply_text(
                    f"<blockquote>✅ سيتم حذف المستخدمين غير النشطين بعد {num} يوم</blockquote>",
                    reply_markup=admin_keyboard(user_id)
                )
            except ValueError:
                await message.reply_text("<blockquote>❌ أدخل رقم صحيح أكبر من 0</blockquote>")

        elif user_state.get(user_id, {}).get("step") == "awaiting_backup_threshold":
            if text == "إلغاء":
                user_state.pop(user_id, None)
                await message.reply_text("<blockquote>❌ تم إلغاء</blockquote>", reply_markup=admin_keyboard(user_id))
                return
            try:
                num = int(text.strip())
                if num < 1:
                    raise ValueError
                backup_user_threshold = num
                save_settings()
                user_state.pop(user_id, None)
                await message.reply_text(
                    f"<blockquote>✅ تم تغيير العدد لـ {num} مستخدم</blockquote>",
                    reply_markup=admin_keyboard(user_id)
                )
            except ValueError:
                await message.reply_text("<blockquote>❌ أدخل رقم صحيح أكبر من 0</blockquote>")

        elif user_state.get(user_id, {}).get("step") == "awaiting_fail_threshold":
            if text == "إلغاء":
                user_state.pop(user_id, None)
                await message.reply_text("<blockquote>❌ تم إلغاء</blockquote>", reply_markup=admin_keyboard(user_id))
                return
            try:
                num = int(text.strip())
                if num < 1:
                    raise ValueError
                broadcast_fail_threshold = num
                save_settings()
                user_state.pop(user_id, None)
                await message.reply_text(
                    f"<blockquote>✅ تم تغيير حد الفشل لـ {num} مرات</blockquote>",
                    reply_markup=admin_keyboard(user_id)
                )
            except ValueError:
                await message.reply_text("<blockquote>❌ أدخل رقم صحيح أكبر من 0</blockquote>")

        elif user_state.get(user_id, {}).get("step") == "awaiting_whitelist_add":
            if text == "إلغاء":
                user_state.pop(user_id, None)
                await message.reply_text("<blockquote>❌ تم إلغاء العملية</blockquote>",
                    reply_markup=admin_keyboard(user_id))
                return
            try:
                target_id = int(text.strip())
                whitelist_users.add(target_id)
                save_settings()
                user_state.pop(user_id, None)
                try:
                    u = await app.get_users(target_id)
                    name = u.first_name or str(target_id)
                except Exception:
                    name = str(target_id)
                await message.reply_text(
                    f"<blockquote>✅ تم إضافة {name} لقائمة الإعفاء\n🛡 لن يتم حظره تلقائياً أو يدوياً</blockquote>",
                    reply_markup=admin_keyboard(user_id)
                )
            except ValueError:
                await message.reply_text("<blockquote>❌ أدخل ID رقمي صحيح</blockquote>")


        elif text == "⚙️ إعدادات متقدمة":
            if int(user_id) != OWNER_ID:
                await message.reply_text("<blockquote>❌ هذا الأمر للمطور فقط</blockquote>")
                return
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            _txt, _kb = build_adv_settings_msg()
            await message.reply_text(_txt, reply_markup=_kb)

        elif text == "🚫 إدارة الحظر":
            if not is_admin(int(user_id)) or not has_perm(int(user_id), "ban"):
                await message.reply_text("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
                return
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            await message.reply_text(
                f"<blockquote>🚫 إدارة الحظر\n\n"
                f"🚫 المحظورون: {len(banned_users)}\n"
                f"🛡 المعفيون: {len(whitelist_users)}</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚫 حظر مستخدم", callback_data="ban_user_menu")],
                    [InlineKeyboardButton("✅ رفع الحظر", callback_data="unban_user_menu")],
                    [InlineKeyboardButton("🛡 قائمة الإعفاء", callback_data="whitelist_menu")],
                ])
            )

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
                await message.reply_text(
                    "<blockquote>✅ لا يوجد مستخدمون محظورون حالياً</blockquote>",
                    reply_markup=admin_keyboard(user_id)
                )
                return
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            await message.reply_text(
                f"<blockquote>🚫 المحظورون ({len(banned_users)})</blockquote>",
                reply_markup=admin_keyboard(user_id)
            )
            for uid in list(banned_users):
                try:
                    u = await app.get_users(int(uid))
                    name = u.first_name or "بدون اسم"
                    username = f"@{u.username}" if u.username else "بدون يوزر"
                except Exception:
                    name = "غير معروف"
                    username = "بدون يوزر"
                data = banned_users_data.get(str(uid), {})
                ban_date = data.get("date", "غير معروف")
                ban_reason = data.get("reason", "حظر يدوي")
                text_msg = (
                    f"<blockquote>🚫 مستخدم محظور\n\n"
                    f"👤 الاسم: {name}\n"
                    f"🔗 اليوزر: {username}\n"
                    f"🆔 الـ ID: {uid}\n"
                    f"📅 تاريخ الحظر: {ban_date}\n"
                    f"📝 السبب: {ban_reason}</blockquote>"
                )
                await message.reply_text(
                    text_msg,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ رفع الحظر", callback_data=f"unban_{uid}")]
                    ])
                )
                await asyncio.sleep(0.3)

        elif user_state.get(user_id, {}).get("step") == "awaiting_ban_id":
            if text == "إلغاء":
                user_state.pop(user_id, None)
                await message.reply_text("<blockquote>❌ تم إلغاء العملية</blockquote>",
                    reply_markup=admin_keyboard(user_id))
                return
            try:
                target_id = int(text.strip())
                if target_id in whitelist_users:
                    await message.reply_text(
                        f"<blockquote>⚠️ هذا المستخدم معفى من الحظر\nلا يمكن حظره إلا بإزالته من قائمة الإعفاء أولاً</blockquote>",
                        reply_markup=admin_keyboard(user_id)
                    )
                    return
                # حفظ الـ ID وانتظار السبب
                user_state[user_id] = {"step": "awaiting_ban_reason", "ban_target_id": target_id}
                from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                await message.reply_text(
                    f"<blockquote>🚫 حظر المستخدم {target_id}\n\nاختر سبب الحظر:</blockquote>",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔴 سبام", callback_data=f"ban_reason_سبام_{target_id}")],
                        [InlineKeyboardButton("⚠️ إساءة", callback_data=f"ban_reason_إساءة_{target_id}")],
                        [InlineKeyboardButton("🚫 انتهاك القوانين", callback_data=f"ban_reason_انتهاك القوانين_{target_id}")],
                        [InlineKeyboardButton("✏️ شيء آخر", callback_data=f"ban_reason_other_{target_id}")],
                        [InlineKeyboardButton("❌ إلغاء", callback_data=f"ban_reason_cancel_{target_id}")]
                    ])
                )
            except ValueError:
                await message.reply_text("<blockquote>❌ يرجى إدخال ID رقمي صحيح</blockquote>")

        elif user_state.get(user_id, {}).get("step") == "awaiting_broadcast_users_text":
            if text in ("إلغاء", "❌ إلغاء"):
                user_state.pop(user_id, None)
                await message.reply_text("<blockquote>❌ تم إلغاء العملية</blockquote>", reply_markup=admin_keyboard(user_id))
                return
            users = list(user_data.keys())
            success = 0
            failed = 0
            prog_msg = await message.reply_text(
                f"<blockquote>📤 جاري الإذاعة...\n"
                f"👥 المستخدمين: {len(users)}\n"
                f"⏳ يرجى الانتظار...</blockquote>"
            )
            for uid in users:
                try:
                    await app.send_message(int(uid), text,
                disable_web_page_preview=True)
                    success += 1
                except Exception as e:
                    err = str(e).lower()
                    if "user is deactivated" in err or "peer id invalid" in err or "blocked" in err:
                        await notify_user_blocked(uid)
                    failed += 1
                await asyncio.sleep(0.5)
            user_state.pop(user_id, None)
            try:
                await prog_msg.delete()
            except Exception:
                pass
            await message.reply_text(
                f"<blockquote>✅ تمت الإذاعة بنجاح\n\n"
                f"👥 المستخدمين: {len(users)}\n"
                f"✅ وصلت: {success}\n"
                f"❌ فشلت: {failed}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"📅 {egypt_strftime()}</blockquote>",
                reply_markup=admin_keyboard(user_id)
            )

        elif user_state.get(user_id, {}).get("step") == "awaiting_broadcast_channels_text":
            if text in ("إلغاء", "❌ إلغاء"):
                user_state.pop(user_id, None)
                await message.reply_text("<blockquote>❌ تم إلغاء العملية</blockquote>", reply_markup=admin_keyboard(user_id))
                return
            channels = set()
            for u in list(user_data.values()):
                if "channels" in u:
                    channels.update(u["channels"].keys())
            success = 0
            failed = 0
            prog_msg = await message.reply_text(
                f"<blockquote>📤 جاري الإذاعة...\n"
                f"📢 القنوات: {len(channels)}\n"
                f"⏳ يرجى الانتظار...</blockquote>"
            )
            for ch_id in channels:
                try:
                    await app.send_message(int(ch_id), text,
                disable_web_page_preview=True)
                    success += 1
                except Exception as e:
                    err = str(e).lower()
                    if "user is deactivated" in err or "peer id invalid" in err or "blocked" in err:
                        await notify_user_blocked(ch_id)
                    failed += 1
                await asyncio.sleep(0.5)
            user_state.pop(user_id, None)
            try:
                await prog_msg.delete()
            except Exception:
                pass
            await message.reply_text(
                f"<blockquote>✅ تمت الإذاعة بنجاح\n\n"
                f"📢 القنوات: {len(channels)}\n"
                f"✅ وصلت: {success}\n"
                f"❌ فشلت: {failed}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"📅 {egypt_strftime()}</blockquote>",
                reply_markup=admin_keyboard(user_id)
            )

        elif user_state.get(user_id, {}).get("step") == "awaiting_usr_search":
            if text == "إلغاء":
                user_state.pop(user_id, None)
                await message.reply_text("<blockquote>❌ تم إلغاء البحث</blockquote>", reply_markup=admin_keyboard(user_id))
                return
            user_state.pop(user_id, None)
            await message.reply_text(f"<blockquote>🔍 نتائج البحث عن: {text}</blockquote>", reply_markup=admin_keyboard(user_id))
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            found = False
            for uid, user_info in list(user_data.items()):
                try:
                    u = await client.get_users(int(uid))
                    name = u.first_name or "غير معروف"
                    username = f"@{u.username}" if u.username else "بدون يوزر"
                except Exception:
                    name = "غير معروف"
                    username = "بدون يوزر"
                    u = None
                # بحث في الاسم واليوزر والـ ID
                if (text.lower() in name.lower() or
                    text.lower() in username.lower() or
                    text in str(uid)):
                    found = True
                    is_banned = int(uid) in banned_users
                    active_broadcasts = sum(1 for ch in user_info.get("channels", {}).values() if "process" in ch)
                    channels_count = len(user_info.get("channels", {}))
                    join_date = user_info.get("join_date", "غير معروف")
                    broadcast_status = f"🟢 {active_broadcasts} بث نشط" if active_broadcasts > 0 else "🔴 لا يوجد بث"
                    user_link = get_user_link(uid, u.username if u and u.username else None)
                    text_msg = (
                        f"<blockquote>"
                        f"👤 {name}\n"
                        f"🔗 {username}\n"
                        f"🆔 {uid}\n"
                        f"📅 الانضمام: {join_date}\n"
                        f"📢 القنوات: {channels_count}\n"
                        f"📡 البث: {broadcast_status}\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"{'🚫 محظور' if is_banned else '✅ نشط'}"
                        f"</blockquote>"
                    )
                    row = []
                    if user_link:
                        row.append(InlineKeyboardButton(f"👤 {name}", url=user_link))
                    if is_banned:
                        row.append(InlineKeyboardButton("✅ رفع الحظر", callback_data=f"unban_{uid}"))
                    else:
                        row.append(InlineKeyboardButton("🚫 حظر", callback_data=f"quick_ban_{uid}"))
                    await message.reply_text(
                        text_msg,
                        reply_markup=InlineKeyboardMarkup([row]) if row else None
                    )
                    await asyncio.sleep(0.3)
            if not found:
                await message.reply_text(f"<blockquote>❌ لم يتم العثور على نتائج لـ: {text}</blockquote>")

        elif user_state.get(user_id, {}).get("step") == "awaiting_ch_search":
            if text == "إلغاء":
                user_state.pop(user_id, None)
                await message.reply_text("<blockquote>❌ تم إلغاء البحث</blockquote>", reply_markup=admin_keyboard(user_id))
                return
            user_state.pop(user_id, None)
            await message.reply_text(f"<blockquote>🔍 نتائج البحث عن: {text}</blockquote>", reply_markup=admin_keyboard(user_id))
            # بحث في القنوات
            found = False
            for uid, user_info in list(user_data.items()):
                for ch_id, ch_info in list(user_info.get("channels", {}).items()):
                    ch_title = ch_info.get("title", "")
                    if text.lower() in ch_title.lower() or text in str(uid) or text in ch_id:
                        found = True
                        try:
                            owner = await client.get_users(int(uid))
                            owner_name = owner.first_name or "غير معروف"
                            owner_username = f"@{owner.username}" if owner.username else None
                            owner_link = get_user_link(uid, owner.username if owner.username else None)
                        except Exception:
                            owner_name = "غير معروف"
                            owner_username = None
                            owner_link = None
                        station_url = user_info.get("temp_station", "")
                        station_name = next((v["name"] for v in ST_TIMO.values() if v["url"] == station_url), "لا يوجد")
                        broadcast_status = "🟢 قيد التشغيل" if "process" in ch_info else "🔴 متوقف"
                        ch_url = None
                        members = "غير متاح"
                        try:
                            chat = await client.get_chat(int(ch_id))
                            if chat.username:
                                ch_url = f"https://t.me/{chat.username}"
                            elif chat.invite_link:
                                ch_url = chat.invite_link
                            try:
                                members = await client.get_chat_members_count(int(ch_id))
                            except Exception:
                                pass
                        except Exception:
                            pass
                        text_msg = (
                            f"<blockquote>📢 <b>{ch_info.get('title', ch_id)}</b>\n"
                            f"👥 الأعضاء: {members}\n"
                            f"🎙 المحطة: {station_name}\n"
                            f"📡 البث: {broadcast_status}\n"
                            f"👤 الصاحب: {owner_name}"
                            + (f"  ({owner_username})" if owner_username else "")
                            + f"\n🆔 المعرف: {ch_id}"
                            + f"\n━━━━━━━━━━━━━━━━"
                            + f"\n📅 {egypt_strftime()}"
                            + "</blockquote>"
                        )
                        row = []
                        if owner_link:
                            row.append(InlineKeyboardButton(f"👤 {owner_name}", url=owner_link))
                        if ch_url:
                            row.append(InlineKeyboardButton("📢 دخول القناة", url=ch_url))
                        await message.reply_text(
                            text_msg,
                            reply_markup=InlineKeyboardMarkup([row]) if row else None
                        )
                        await asyncio.sleep(0.4)
            if not found:
                await message.reply_text(f"<blockquote>❌ لم يتم العثور على نتائج لـ: {text}</blockquote>")

        elif user_state.get(user_id, {}).get("step") == "awaiting_ban_custom_reason":
            if text == "إلغاء":
                user_state.pop(user_id, None)
                await message.reply_text("<blockquote>❌ تم إلغاء العملية</blockquote>",
                    reply_markup=admin_keyboard(user_id))
                return
            target_id = user_state[user_id].get("ban_target_id")
            custom_reason = text.strip()
            await _do_ban(message, user_id, target_id, custom_reason, admin_keyboard)
            user_state.pop(user_id, None)



        elif text == "ℹ️ نبذة عن البوت":
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            total_users = len(user_data)
            total_channels = sum(len(u.get("channels", {})) for u in list(user_data.values()))
            total_stations = len(ST_TIMO)
            active_broadcasts = sum(
                1 for u in list(user_data.values())
                for ch in list(u.get("channels", {}).values())
                if "process" in ch
            )
            caption = (
                "<blockquote>ℹ️ نبذة عن البوت\n\n"
                "🤖 الاسم: أثير القرآن | Atheer Al-Quran\n"
                "📌 الإصدار: 1.0\n"
                "👨‍💻 المطور: 𝑨𝒃𝒐 𝑵𝒖𝒘𝒂𝒇\n"
                "━━━━━━━━━━━━━━━━\n"
                "📊 الإحصائيات:\n"
                f"👥 المستخدمين: {total_users}\n"
                f"📢 القنوات: {total_channels}\n"
                f"📡 البثوث النشطة: {active_broadcasts}\n"
                f"🎙 المحطات المتاحة: {total_stations}\n"
                "━━━━━━━━━━━━━━━━\n"
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
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            daily_report_enabled = not daily_report_enabled
            save_settings()
            status = "مفعّل 🟢" if daily_report_enabled else "موقوف 🔴"
            h, m = map(int, daily_report_time.split(":"))
            h12 = h % 12 or 12
            period = "ص" if h < 12 else "م"
            await message.reply_text(
                f"<blockquote>📋 التقرير اليومي الآن: {status}\n"
                + (f"✅ سيصلك تقرير كل يوم الساعة {h12}:{m:02d} {period}" if daily_report_enabled else "❌ لن يصلك أي تقرير") + "</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🕐 تغيير وقت التقرير", callback_data="daily_report_time")]
                ])
            )

        elif text.startswith("🌙 الوضع الليلي"):
            if not is_admin(int(user_id)) or not has_perm(int(user_id), "night_mode"):
                await message.reply_text("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
                return
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            status = "مفعّل 🟢" if night_mode_enabled else "مقفول 🔴"
            night_stations_text = "\n".join([f"• {ST_TIMO[s]['name']}" for s in NIGHT_MODE_STATIONS if s in ST_TIMO])
            await message.reply_text(
                "<blockquote>🌙 الوضع الليلي\n\n"
                "الحالة: " + status + "\n"
                "⏰ من: " + str(night_mode_start) + ":00 حتى " + str(night_mode_end) + ":00\n\n"
                "📻 المحطات الليلية:\n"
                + night_stations_text + "</blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "⏹ إيقاف الوضع الليلي" if night_mode_enabled else "▶️ تشغيل الوضع الليلي",
                        callback_data="night_toggle"
                    )],
                    [InlineKeyboardButton("🕐 تغيير وقت البداية", callback_data="night_set_start")],
                    [InlineKeyboardButton("🕔 تغيير وقت النهاية", callback_data="night_set_end")],
                    [InlineKeyboardButton("📻 إدارة المحطات الليلية", callback_data="night_manage_stations")],
                ])
            )

        elif text.startswith("🔔 إشعار الأدمن") or text.startswith("🔕 إشعار الأدمن"):
            if not is_admin(int(user_id)) or not has_perm(int(user_id), "notifications"):
                await message.reply_text("<blockquote>❌ ليس لديك صلاحية هذا الأمر</blockquote>")
                return
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
                "time": egypt_strftime()
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
                        [InlineKeyboardButton("↩️ رد", callback_data=f"admin_reply_bot_review_{user_id}",
                disable_web_page_preview=True),
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
                        [InlineKeyboardButton("↩️ رد", callback_data=f"admin_reply_station_review_{user_id}",
                disable_web_page_preview=True),
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
                "time": egypt_strftime()
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
                        [InlineKeyboardButton("↩️ رد", callback_data=f"admin_reply_suggest_{user_id}",
                disable_web_page_preview=True),
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
                await app.send_message(int(target_uid), reply_msg,
                disable_web_page_preview=True)
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
            _r_name = message.from_user.first_name or "غير معروف"
            _r_username = message.from_user.username
            _r_link = get_user_link(user_id, _r_username)
            _r_username_display = f"@{_r_username}" if _r_username else "بدون يوزر"
            report_msg = (
                f"<blockquote>🚨 بلاغ جديد\n\n"
                f"👤 الاسم: {_r_name}\n"
                f"🔗 اليوزر: {_r_username_display}\n"
                f"🆔 المعرف: {user_id}\n"
                f"📅 الوقت: {egypt_strftime()}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"📝 المشكلة:\n{report_text_content}</blockquote>"
            )
            all_reports.append({
                "user_id": user_id,
                "name": message.from_user.first_name or "غير معروف",
                "username": message.from_user.username or "بدون يوزر",
                "text": report_text_content,
                "type": "نصي",
                "time": egypt_strftime()
            })
            try:
                from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                _r_row = []
                if _r_link:
                    _r_row.append(InlineKeyboardButton(f"👤 {_r_name}", url=_r_link))
                sent = await app.send_message(
                    ADMIN_ID[0], report_msg,
                    reply_markup=InlineKeyboardMarkup([
                        _r_row if _r_row else [],
                        [InlineKeyboardButton("↩️ رد", callback_data=f"admin_reply_report_{user_id}"),
                         InlineKeyboardButton("🗑 مسح", callback_data=f"admin_del_report_{user_id}")],
                        [InlineKeyboardButton("📋 بلاغاته السابقة", callback_data=f"prev_report_{user_id}"),
                         InlineKeyboardButton("📝 إضافة ملاحظة", callback_data=f"add_note_{user_id}")]
                    ]),
                    disable_web_page_preview=True
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
            # إشعار الأدمن بإضافة قناة جديدة
            if broadcast_notify_enabled and int(user_id) != OWNER_ID:
                try:
                    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                    try:
                        u = await app.get_users(int(user_id))
                        uname = u.first_name or "غير معروف"
                        uusername = f"@{u.username}" if u.username else "بدون يوزر"
                        user_link = get_user_link(user_id, u.username if u.username else None)
                    except Exception:
                        uname = str(user_id)
                        uusername = "بدون يوزر"
                        user_link = get_user_link(user_id)
                    ch_url = None
                    try:
                        chat = await app.get_chat(int(channel_data["id"]))
                        if chat.username:
                            ch_url = f"https://t.me/{chat.username}"
                        elif chat.invite_link:
                            ch_url = chat.invite_link
                    except Exception:
                        pass
                    notify_text = (
                        f"<blockquote>📢 مستخدم أضاف قناة جديدة\n\n"
                        f"👤 الاسم: {uname}\n"
                        f"🔗 اليوزر: {uusername}\n"
                        f"🆔 المعرف: {user_id}\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"📢 القناة: {channel_data['title']}\n"
                        f"📅 الوقت: {egypt_strftime()}</blockquote>"
                    )
                    row = [InlineKeyboardButton(f"👤 {uname}", url=user_link)]
                    if ch_url:
                        row.append(InlineKeyboardButton("📢 دخول القناة", url=ch_url))
                    await app.send_message(
                        ADMIN_ID[0], notify_text,
                        reply_markup=InlineKeyboardMarkup([row]),
                        disable_web_page_preview=True
                    )
                except Exception as e:
                    logger.error(f"channel add notify error: {e}")
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
                user_data[user_id]["channels"][channel_id]["station"] = selected_station
                save_data()                
                await send_broadcast_notification(client, channel_info['chat_id'], selected_station, user_id)
                if int(user_id) != OWNER_ID and broadcast_notify_enabled:
                    try:
                        station_name_notify = next((v["name"] for v in ST_TIMO.values() if v["url"] == selected_station), "غير معروف")
                        await app.send_message(
                            ADMIN_ID[0],
                            "<blockquote>📢 مستخدم بدأ البث\n"
                            "👤 المستخدم: " + str(user_id,
                disable_web_page_preview=True) + "\n"
                            "📡 القناة: " + channel_info['title'] + "\n"
                            "🎙 المحطة: " + station_name_notify + "</blockquote>"
                        )
                    except Exception as e:
                        logger.error(f"broadcast notify admin error: {e}")
                station_name_stat = next((v["name"] for v in ST_TIMO.values() if v["url"] == selected_station), "غير معروف")
                broadcast_stats[channel_id] = {
                    "station": station_name_stat,
                    "start_time": egypt_strftime("%Y-%m-%d %I:%M:%S %p").replace("AM", "ص").replace("PM", "م"),
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
            "time": egypt_strftime()
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
            "time": egypt_strftime()
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
    await asyncio.sleep(5)
    logger.info("Attempting to restore broadcasts...")
    restore_broadcasts()
    logger.info(f"Restore complete. Active broadcasts: {sum(1 for u in user_data.values() for c in u.get('channels', {}).values() if 'process' in c)}")
    threading.Thread(target=scheduled_restart, daemon=True).start()
    threading.Thread(target=run_auto_schedule, daemon=True).start()
    threading.Thread(target=watchdog, daemon=True).start()
    threading.Thread(target=daily_report_thread, daemon=True).start()
    threading.Thread(target=weekly_backup_thread, daemon=True).start()
    threading.Thread(target=weekly_report_thread, daemon=True).start()
    threading.Thread(target=auto_cleanup_thread, daemon=True).start()
    threading.Thread(target=user_night_mode_thread, daemon=True).start()
    threading.Thread(target=night_mode_thread, daemon=True).start()
    threading.Thread(target=subscription_watcher_thread, daemon=True).start()
    threading.Thread(target=tarawih_thread, daemon=True).start()
    threading.Thread(target=auto_refresh_thread, daemon=True).start()

async def on_startup():
    await main()

app.on_startup = on_startup



if __name__ == "__main__":
    logger.info("Starting Radio Bot...")
    
    async def run_bot():
        async with app:
            await main()
            await asyncio.Event().wait()
    
    app.run(run_bot())