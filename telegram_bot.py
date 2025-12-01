# telegram_bot.py
# ربات توزیع حرفه‌ای wifi_tool.exe | نسخه نهایی طلایی ۲۰۲۵
# قابلیت‌ها:
#   • دکمه یک‌بار مصرف (هر کاربر فقط یک‌بار)
#   • آمار دقیق: کل – امروز – این هفته
#   • اعلان فوری هر دانلود به کانال
#   • گزارش خودکار روزانه (۰۰:۰۵) و هفتگی (دوشنبه ۰۰:۱۰)
#   • لاگ کامل + جلوگیری از دانلود مجدد
#   • فارسی، زیبا و پایدار

import os
import json
import logging
from datetime import datetime, date, time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ==================== تنظیمات ====================
BOT_TOKEN   = "YOUR_BOT_TOKEN_HERE"           # توکن ربات خود را اینجا بگذارید
CHANNEL_ID  = "@YourChannelHere"              # @YourChannel یا -100xxxxxxxxxx (کانال اعلان)

DOCUMENTS_FOLDER = r"C:\Users\M\Downloads\Python"
MAIN_FILE_NAME   = "wifi_tool.exe"
MAIN_FILE_PATH   = os.path.join(DOCUMENTS_FOLDER, MAIN_FILE_NAME)

STATS_FILE        = "stats.json"
USED_BUTTONS_FILE = "used_buttons.txt"
# ================================================

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ——— بارگذاری آمار ———
def load_stats():
    default = {"total": 0, "today": 0, "week": 0, "last_reset": str(date.today())}
    if not os.path.exists(STATS_FILE):
        return default
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # تضمین وجود کلیدها
            for k, v in default.items():
                if k not in data:
                    data[k] = v
            return data
    except:
        return default

def save_stats():
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

stats = load_stats()

# ——— ریست روزانه و هفتگی ———
def check_and_reset_stats():
    today = str(date.today())
    if stats["last_reset"] != today:
        stats["today"] = 0
        if date.today().weekday() == 0:  # دوشنبه
            stats["week"] = 0
        stats["last_reset"] = today
        save_stats()

check_and_reset_stats()

# ——— دکمه‌های یک‌بار مصرف ———
used_buttons = set()
if os.path.exists(USED_BUTTONS_FILE):
    with open(USED_BUTTONS_FILE, "r", encoding="utf-8") as f:
        used_buttons = {line.strip() for line in f if line.strip()}

def mark_button_used(key: str):
    used_buttons.add(key)
    with open(USED_BUTTONS_FILE, "a", encoding="utf-8") as f:
        f.write(key + "\n")

# ——— ارسال پیام به کانال ———
async def send_to_channel(context: ContextTypes.DEFAULT_TYPE, text: str):
    if not CHANNEL_ID:
        return
    try:
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.warning(f"ارسال به کانال ناموفق: {e}")

# ——— گزارش‌ها ———
async def daily_report(context: ContextTypes.DEFAULT_TYPE):
    txt = f"""
آمار دانلود امروز <b>{date.today():%Y/%m/%d}</b>

<b>{stats['today']} نفر</b> فایل را دریافت کردند

کل دانلودها: <b>{stats['total']}</b> نفر
    """
    await send_to_channel(context, txt.strip())

async def weekly_report(context: ContextTypes.DEFAULT_TYPE):
    txt = f"""
آمار هفتگی دانلود

<b>{stats['week']} نفر</b> در این هفته فایل را دریافت کردند

کل دانلودها تا الان: <b>{stats['total']}</b> نفر

هفته جدید، موفقیت‌های جدید!
    """
    await send_to_channel(context, txt.strip())

# ——— اعلان هر دانلود ———
async def notify_download(context: ContextTypes.DEFAULT_TYPE, user):
    name = user.full_name
    username = f"@{user.username}" if user.username else "ندارد"
    txt = f"""
دانلود جدید!

<b>{}</b>
{}
آیدی: <code>{}</code>
ساعت: <code>{}</code>

تعداد کل دانلود: <b>{}</b> نفر
    """.format(
        name,
        username,
        user.id,
        datetime.now().strftime("%H:%M:%S"),
        stats["total"]
    )
    await send_to_channel(context, txt.strip())

# ——— دکمه یک‌بار مصرف ———
def create_button():
    uniq = datetime.now().strftime("%Y%m%d%H%M%S%f")
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("دریافت فایل wifi_tool.exe", callback_data=f"get_{uniq}")
    ]])
    return keyboard, uniq

# ——— دستورات ———
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard, _ = create_button()

    text = f"""
سلام <b>{user.first_name}</b> عزیز!

فایل قدرتمند و امن آماده تحویل است:
<b>{MAIN_FILE_NAME}</b>

تعداد دانلود تا الان: <b>{stats['total']}</b> نفر

برای دریافت فایل روی دکمه زیر کلیک کن
(هر نفر فقط یک‌بار می‌تواند دانلود کند)
    """
    await update.message.reply_html(text.strip(), reply_markup=keyboard)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("get_"):
        return

    uniq = query.data[4:]
    user_key = f"{query.from_user.id}_{uniq}"

    if user_key in used_buttons:
        await query.edit_message_text("این دکمه قبلاً استفاده شده است!\nبرای دکمه جدید دوباره /start بزنید")
        return

    await query.edit_message_text("در حال ارسال فایل… لطفاً چند لحظه صبر کنید")
    await deliver_file(query, context, query.from_user, user_key)

async def deliver_file(query, context: ContextTypes.DEFAULT_TYPE, user, user_key):
    global stats

    if not os.path.isfile(MAIN_FILE_PATH):
        await query.edit_message_text("فایل در سرور موجود نیست! با پشتیبانی تماس بگیرید.")
        return

    try:
        size_mb = os.path.getsize(MAIN_FILE_PATH) / (1024 * 1024)
        with open(MAIN_FILE_PATH, "rb") as f:
            await context.bot.send_document(
                chat_id=query.message.chat.id,
                document=f,
                filename=MAIN_FILE_NAME,
                caption=f"wifi_tool.exe\nحجم: {size_mb:.1f} مگابایت\n\nبا موفقیت ارسال شد!",
                timeout=1800,
            )

        # بروزرسانی آمار
        stats["total"] += 1
        stats["today"] += 1
        stats["week"] += 1
        save_stats()

        # ثبت دکمه
        mark_button_used(user_key)

        # ارسال به کانال
        await notify_download(context, user)

        await query.message.reply_html(f"فایل با موفقیت ارسال شد!\nشما نفر <b>{stats['total']}</b> هستید")

    except Exception as e:
        logger.error(f"خطا در ارسال فایل: {e}")
        await query.edit_message_text("خطایی رخ داد. دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.")

# ——— دستور آمار (اختیاری) ———
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        f"<b>آمار دانلود</b>\n\n"
        f"کل: <b>{stats['total']}</b>\n"
        f"امروز: <b>{stats['today']}</b>\n"
        f"این هفته: <b>{stats['week']}</b>"
    )

# ——— اجرای ربات ———
def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN.strip():
        print("خطا: توکن ربات وارد نشده است!")
        return

    print("ربات در حال راه‌اندازی...")
    print(f"فایل اصلی: {MAIN_FILE_PATH}")
    print(f"دانلودهای کل: {stats['total']}")
    print(f"کانال اعلان: {CHANNEL_ID if CHANNEL_ID != '@YourChannelHere' else 'غیرفعال'}")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button_callback))

    # گزارش‌های زمان‌بندی شده
    jq = app.job_queue
    jq.run_daily(daily_report, time=time(0, 5))           # هر روز ۰۰:۰۵
    jq.run_daily(weekly_report, time=time(0, 10), days=(0,))  # دوشنبه‌ها ۰۰:۱۰

    print("\nربات با موفقیت اجرا شد! منتظر کاربران...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()