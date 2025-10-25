import os
import google.generativeai as genai
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import mimetypes
import sys
import types

imghdr = types.ModuleType("imghdr")

def what(file, h=None):
    kind = mimetypes.guess_type(file)[0]
    if kind and "image" in kind:
        return kind.split("/")[-1]
    return None

imghdr.what = what
sys.modules["imghdr"] = imghdr

# .env fayldan yuklash
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

# Gemini API sozlash
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("models/gemini-2.5-flash")

# Kanal ma'lumotlari
CHANNEL_USERNAME = "@pirmaxmatovs"
CHANNEL_LINK = "https://t.me/pirmaxmatovs"

# Foydalanuvchi a’zomi-yo‘qmi tekshiruvchi funksiya
def is_subscribed(update: Update, context: CallbackContext):
    try:
        user_id = update.effective_user.id
        chat_member = context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

# /start komandasi
def start(update: Update, context: CallbackContext):
    if not is_subscribed(update, context):
        keyboard = [[InlineKeyboardButton("✅ Kanalga qo‘shilish", url=CHANNEL_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            f"👋 Salom! Men bilan gaplashishdan oldin {CHANNEL_USERNAME} kanaliga qo‘shiling!",
            reply_markup=reply_markup
        )
    else:
        update.message.reply_text("✅ Siz kanal a’zosisiz, endi savol berishingiz mumkin!")

# Asosiy handler
def handle_message(update: Update, context: CallbackContext):
    if not is_subscribed(update, context):
        keyboard = [[InlineKeyboardButton("✅ Kanalga qo‘shilish", url=CHANNEL_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            "⚠️ Botdan foydalanish uchun avval kanalga qo‘shiling!",
            reply_markup=reply_markup
        )
        return

    user_text = update.message.text.strip().lower()
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # --- SPECIAL JAVOBLAR ---
    # "Sen kimsan?" turidagi savollar
    if any(word in user_text for word in ["kimsan", "who are you", "кто ты", "kimliging"]):
        response_text = "I am a chatbot created by Pirmaxmatov Og’abek (@pirmaxmatov) 🤖 | t.me/pirmaxmatov"
        update.message.reply_text(response_text)
        return

    # "Creator kim?" turidagi savollar
    if any(word in user_text for word in ["creator", "yaratgan", "yaratuvching", "создатель", "yaratuvchi"]):
        response_text = "I am a chatbot created by Pirmaxmatov Og’abek (@pirmaxmatov) 🤖 | t.me/pirmaxmatov"
        update.message.reply_text(response_text)
        return

    # --- ODDIY AI JAVOB ---
    try:
        response = model.generate_content(
            f"Foydalanuvchi: {user_text}\n\nJavobni foydalanuvchi yozgan tilida yozing."
        )
        ai_text = (response.text or "").strip()
        final_text = ai_text + "\n\n🤖 Bot made by @pirmaxmatov"
        update.message.reply_text(final_text)

    except Exception as e:
        update.message.reply_text(
            f"⚠️ Xato: {e}\n\n🤖 Bot made by @pirmaxmatov"
        )

# Asosiy funksiya
def main():
    if not TELEGRAM_TOKEN:
        print("❌ Xato: TELEGRAM_TOKEN topilmadi. .env faylni tekshiring!")
        return

    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    print("🤖 Chatbot ishga tushdi... Endi Telegram’da sinab ko‘ring!")

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
