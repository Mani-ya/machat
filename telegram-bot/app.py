import os
import requests
from flask import Flask, request, abort

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# زبان انتخابی کاربران
# توجه: فعلاً با ری‌استارت سرور پاک می‌شود.
USER_LANGUAGES = {}


# ==================================================
# 1) متن‌های عمومی ربات
# ==================================================

LANGUAGES = {
    "fa": {
        "welcome": "👋 به ربات Hidegram خوش آمدید!",
        "choose_language": "🌍 Select your language/لطفاً زبان خود را انتخاب کنید:",
        "menu_title": "📚 راهنمای Hidegram",
        "menu_text": "برای مشاهده توضیحات، یکی از کامندهای زیر را انتخاب کنید:",
        "back": "🔙 بازگشت به راهنما",
        "language_changed": "زبان شما تغییر کرد.",
        "unknown": "این بخش پیدا نشد.",
        "language_button": "🌍 تغییر زبان"
    },

    "en": {
        "welcome": "👋 Welcome to Hidegram Bot!",
        "choose_language": "🌍 Please choose your language:",
        "menu_title": "📚 Hidegram Help",
        "menu_text": "Choose one of the commands below to see its details:",
        "back": "🔙 Back to Help",
        "language_changed": "Your language has been changed.",
        "unknown": "This section was not found.",
        "language_button": "🌍 Change language"
    }
}


# ==================================================
# 2) بیست بخش راهنما
# برای تغییر کامند، توضیح یا پاسخ، همین قسمت را ویرایش کن.
# ==================================================

HELP_SECTIONS = {

    "about": {
        "command": "about",
        "title": {"fa": "🌐 درباره Hidegram", "en": "🌐 About Hidegram"},
        "description": {"fa": "معرفی سایت", "en": "About the website"},
        "answer": {
            "fa": "🌐 به Hidegram خوش آمدید!\n\nاینجا توضیحات سایت را بنویس.",
            "en": "🌐 Welcome to Hidegram!\n\nWrite your website introduction here."
        }
    },

    "guide": {
        "command": "guide",
        "title": {"fa": "📖 راهنمای شروع", "en": "📖 Getting Started"},
        "description": {"fa": "نحوه شروع استفاده", "en": "How to get started"},
        "answer": {
            "fa": "📖 راهنمای شروع:\n\nمراحل شروع استفاده از سایت را اینجا بنویس.",
            "en": "📖 Getting Started:\n\nWrite the steps to get started here."
        }
    },

    "features": {
        "command": "features",
        "title": {"fa": "✨ امکانات", "en": "✨ Features"},
        "description": {"fa": "معرفی امکانات سایت", "en": "Website features"},
        "answer": {
            "fa": "✨ امکانات Hidegram:\n\nامکانات سایت را اینجا بنویس.",
            "en": "✨ Hidegram Features:\n\nWrite your website features here."
        }
    },

    "account": {
        "command": "account",
        "title": {"fa": "👤 حساب کاربری", "en": "👤 Account"},
        "description": {"fa": "اطلاعات حساب", "en": "Account information"},
        "answer": {
            "fa": "👤 اطلاعات حساب کاربری:\n\nتوضیحات حساب را اینجا بنویس.",
            "en": "👤 Account Information:\n\nWrite account information here."
        }
    },

    "profile": {
        "command": "profile",
        "title": {"fa": "🪪 پروفایل", "en": "🪪 Profile"},
        "description": {"fa": "راهنمای پروفایل", "en": "Profile guide"},
        "answer": {
            "fa": "🪪 راهنمای پروفایل:\n\nتوضیحات پروفایل را اینجا بنویس.",
            "en": "🪪 Profile Guide:\n\nWrite profile instructions here."
        }
    },

    "privacy": {
        "command": "privacy",
        "title": {"fa": "🔒 حریم خصوصی", "en": "🔒 Privacy"},
        "description": {"fa": "اطلاعات حریم خصوصی", "en": "Privacy information"},
        "answer": {
            "fa": "🔒 حریم خصوصی:\n\nقوانین حریم خصوصی را اینجا بنویس.",
            "en": "🔒 Privacy:\n\nWrite your privacy information here."
        }
    },

    "security": {
        "command": "security",
        "title": {"fa": "🛡 امنیت", "en": "🛡 Security"},
        "description": {"fa": "نکات امنیتی", "en": "Security tips"},
        "answer": {
            "fa": "🛡 امنیت:\n\nنکات امنیتی را اینجا بنویس.",
            "en": "🛡 Security:\n\nWrite security tips here."
        }
    },

    "support": {
        "command": "support",
        "title": {"fa": "🆘 پشتیبانی", "en": "🆘 Support"},
        "description": {"fa": "دریافت پشتیبانی", "en": "Get support"},
        "answer": {
            "fa": "🆘 پشتیبانی:\n\nروش دریافت پشتیبانی را اینجا بنویس.",
            "en": "🆘 Support:\n\nWrite support instructions here."
        }
    },

    "contact": {
        "command": "contact",
        "title": {"fa": "📞 ارتباط با ما", "en": "📞 Contact Us"},
        "description": {"fa": "راه‌های ارتباطی", "en": "Contact details"},
        "answer": {
            "fa": "📞 ارتباط با ما:\n\nراه‌های ارتباطی را اینجا بنویس.",
            "en": "📞 Contact Us:\n\nWrite contact details here."
        }
    },

    "faq": {
        "command": "faq",
        "title": {"fa": "❓ سوالات متداول", "en": "❓ FAQ"},
        "description": {"fa": "پاسخ سوالات رایج", "en": "Common questions"},
        "answer": {
            "fa": "❓ سوالات متداول:\n\nسوالات و پاسخ‌ها را اینجا بنویس.",
            "en": "❓ FAQ:\n\nWrite common questions and answers here."
        }
    },

    "rules": {
        "command": "rules",
        "title": {"fa": "📜 قوانین", "en": "📜 Rules"},
        "description": {"fa": "قوانین استفاده", "en": "Usage rules"},
        "answer": {
            "fa": "📜 قوانین Hidegram:\n\nقوانین سایت را اینجا بنویس.",
            "en": "📜 Hidegram Rules:\n\nWrite your website rules here."
        }
    },

    "terms": {
        "command": "terms",
        "title": {"fa": "📝 شرایط استفاده", "en": "📝 Terms"},
        "description": {"fa": "شرایط و ضوابط", "en": "Terms and conditions"},
        "answer": {
            "fa": "📝 شرایط استفاده:\n\nشرایط استفاده را اینجا بنویس.",
            "en": "📝 Terms of Use:\n\nWrite your terms here."
        }
    },

    "report": {
        "command": "report",
        "title": {"fa": "🚩 گزارش مشکل", "en": "🚩 Report a Problem"},
        "description": {"fa": "گزارش خطا یا مشکل", "en": "Report an issue"},
        "answer": {
            "fa": "🚩 گزارش مشکل:\n\nروش گزارش مشکل را اینجا بنویس.",
            "en": "🚩 Report a Problem:\n\nWrite reporting instructions here."
        }
    },

    "feedback": {
        "command": "feedback",
        "title": {"fa": "💬 پیشنهادها", "en": "💬 Feedback"},
        "description": {"fa": "ارسال پیشنهاد", "en": "Send feedback"},
        "answer": {
            "fa": "💬 پیشنهادها:\n\nروش ارسال پیشنهاد را اینجا بنویس.",
            "en": "💬 Feedback:\n\nWrite feedback instructions here."
        }
    },

    "updates": {
        "command": "updates",
        "title": {"fa": "🆕 بروزرسانی‌ها", "en": "🆕 Updates"},
        "description": {"fa": "آخرین تغییرات", "en": "Latest updates"},
        "answer": {
            "fa": "🆕 بروزرسانی‌ها:\n\nتغییرات جدید سایت را اینجا بنویس.",
            "en": "🆕 Updates:\n\nWrite the latest updates here."
        }
    },

    "website": {
        "command": "website",
        "title": {"fa": "🌍 آدرس سایت", "en": "🌍 Website"},
        "description": {"fa": "لینک ورود به سایت", "en": "Website link"},
        "answer": {
            "fa": "🌍 آدرس سایت:\nhttps://hidegram.de5.net",
            "en": "🌍 Website:\nhttps://hidegram.de5.net"
        }
    },

    "services": {
        "command": "services",
        "title": {"fa": "🧩 خدمات", "en": "🧩 Services"},
        "description": {"fa": "معرفی خدمات", "en": "Available services"},
        "answer": {
            "fa": "🧩 خدمات:\n\nخدمات سایت را اینجا بنویس.",
            "en": "🧩 Services:\n\nWrite your services here."
        }
    },

    "tutorial": {
        "command": "tutorial",
        "title": {"fa": "🎓 آموزش", "en": "🎓 Tutorial"},
        "description": {"fa": "آموزش استفاده از سایت", "en": "How-to tutorials"},
        "answer": {
            "fa": "🎓 آموزش:\n\nمراحل آم
