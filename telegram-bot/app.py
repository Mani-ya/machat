import os
import requests
from flask import Flask, request, abort

app = Flask(__name__)

# اطلاعات محرمانه ربات از تنظیمات Render خوانده می‌شوند
BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ==================================
# بخش‌های راهنمای Hidegram
# برای افزودن راهنمای جدید، این قسمت را ویرایش کن
# ==================================

HELP_SECTIONS = {
    "intro": {
        "title": "🌐 معرفی Hidegram",
        "text": (
            "👋 به Hidegram خوش آمدید!\n\n"
            "Hidegram یک وب‌اپلیکیشن است که می‌توانید "
            "از امکانات آن استفاده کنید.\n\n"
            "🌐 آدرس سایت:\n"
            "https://hidegram.de5.net"
        )
    },

    "start": {
        "title": "🚀 نحوه شروع کار",
        "text": (
            "🚀 نحوه شروع استفاده از Hidegram:\n\n"
            "1️⃣ وارد وب‌اپ شوید.\n"
            "2️⃣ امکانات موجود را مشاهده کنید.\n"
            "3️⃣ بخش موردنظر خود را انتخاب کنید.\n\n"
            "موفق باشید! ❤️"
        )
    }
}


# ==================================
# ارتباط با تلگرام
# ==================================

def telegram(method, data):
    response = requests.post(
        f"{BASE_URL}/{method}",
        json=data,
        timeout=15
    )
    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(result)

    return result


# ==================================
# نمایش منوی راهنما
# ==================================

def show_menu(chat_id):

    keyboard = []

    for key, section in HELP_SECTIONS.items():

        keyboard.append([{
            "text": section["title"],
            "callback_data": f"help:{key}"
        }])

    telegram("sendMessage", {
        "chat_id": chat_id,
        "text": (
            "📚 راهنمای استفاده از Hidegram\n\n"
            "سلام! 👋\n"
            "برای مشاهده توضیحات هر بخش، "
            "یکی از گزینه‌های زیر را انتخاب کنید:"
        ),
        "reply_markup": {
            "inline_keyboard": keyboard
        }
    })


# ==================================
# مدیریت پیام‌ها و دکمه‌ها
# ==================================

def handle_update(update):

    message = update.get("message")

    # دستورات /start و /help
    if message and message.get("text"):

        chat_id = message["chat"]["id"]

        command = (
            message["text"].split()[0].split("@")[0]
        )

        if command in ("/start", "/help"):

            show_menu(chat_id)

            return

    # کلیک روی دکمه‌های راهنما
    callback = update.get("callback_query")

    if callback:

        telegram("answerCallbackQuery", {
            "callback_query_id": callback["id"]
        })

        chat_id = callback["message"]["chat"]["id"]

        data = callback.get("data", "")

        # بازگشت به منوی اصلی
        if data == "menu":

            show_menu(chat_id)

            return

        # نمایش توضیحات هر بخش
        if data.startswith("help:"):

            key = data.split(":", 1)[1]

            section = HELP_SECTIONS.get(key)

            if section:

                telegram("sendMessage", {
                    "chat_id": chat_id,
                    "text": section["text"],
                    "reply_markup": {
                        "inline_keyboard": [[
                            {
                                "text": "🔙 بازگشت به راهنما",
                                "callback_data": "menu"
                            }
                        ]]
                    }
                })


# ==================================
# دریافت Webhook تلگرام
# ==================================

@app.route("/webhook", methods=["POST"])
def webhook():

    if request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    ) != WEBHOOK_SECRET:

        abort(403)

    update = request.get_json(silent=True) or {}

    try:
        handle_update(update)

    except Exception:
        app.logger.exception(
            "Error processing Telegram update"
        )

    return "OK", 200


# ==================================
# صفحه بررسی وضعیت ربات
# ==================================

@app.route("/", methods=["GET"])
def home():

    return "Hidegram Bot is running!"


# ==================================
# ثبت خودکار Webhook
# ==================================

def setup_webhook():

    base_url = os.environ.get("RENDER_EXTERNAL_URL")

    if base_url:

        telegram("setWebhook", {
            "url": f"{base_url}/webhook",
            "secret_token": WEBHOOK_SECRET
        })

        app.logger.info("Hidegram webhook registered")


setup_webhook()
