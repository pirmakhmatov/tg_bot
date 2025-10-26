import os
import google.generativeai as genai
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import mimetypes
import sys
import types
import datetime

# --- IMAGE HANDLING PATCH ---
imghdr = types.ModuleType("imghdr")
def what(file, h=None):
    kind = mimetypes.guess_type(file)[0]
    if kind and "image" in kind:
        return kind.split("/")[-1]
    return None
imghdr.what = what
sys.modules["imghdr"] = imghdr

# --- ENV ---
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

if not TELEGRAM_TOKEN or not GEMINI_KEY:
    print("❌ TELEGRAM_TOKEN yoki GEMINI_KEY topilmadi!")
    exit()

# --- GEMINI API ---
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("models/gemini-2.5-flash")

# --- CHANNEL ---
CHANNEL_USERNAME = "@pirmaxmatovs"
CHANNEL_LINK = "https://t.me/pirmaxmatovs"

# --- ADMINS ---
ADMINS = [1289085137, 5492583026]
  # <-- Telegram bot Admin IDlari 

# --- USER DATABASE (in-memory) ---
USER_DATA = {}  # {user_id: {"history": [], "last_seen": date, "count": int}}

# --- CHECK SUBSCRIPTION ---
def is_subscribed(update: Update, context: CallbackContext):
    try:
        user_id = update.effective_user.id
        status = context.bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ["member", "administrator", "creator"]
    except Exception:
        return False

# --- /start ---
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    USER_DATA.setdefault(user_id, {"history": [], "last_seen": datetime.date.today(), "count": 0})
    
    if not is_subscribed(update, context):
        keyboard = [[InlineKeyboardButton("✅ Kanalga qo‘shilish", url=CHANNEL_LINK)]]
        update.message.reply_text(
            f"👋 Salom! Botdan foydalanish uchun avval {CHANNEL_USERNAME} kanaliga qo‘shiling!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        update.message.reply_text(f"✅ Siz allaqachon t.me/spirmaxmatovs a’zosisiz, endi savol berishingiz mumkin! \n\n *Optional* Ok Write about yourself...")

# --- SPECIAL RESPONSES ---
SPECIAL_RESPONSES = {
    "kimsan": "I am a chatbot created by Pirmaxmatov Og’abek (@pirmaxmatov) 🤖 | t.me/pirmaxmatov",
    "who are you": "I am a chatbot created by Pirmaxmatov Og’abek (@pirmaxmatov) 🤖 | t.me/pirmaxmatov",
    "кто ты": "I am a chatbot created by Pirmaxmatov Og’abek (@pirmaxmatov) 🤖 | t.me/pirmaxmatov",
    "kimliging": "I am a chatbot created by Pirmaxmatov Og’abek (@pirmaxmatov) 🤖 | t.me/pirmaxmatov",
    "creator": "I am a chatbot created by Pirmaxmatov Og’abek (@pirmaxmatov) 🤖 | t.me/pirmaxmatov",
    "yaratgan": "I am a chatbot created by Pirmaxmatov Og’abek (@pirmaxmatov) 🤖 | t.me/pirmaxmatov",
    "yaratuvching": "I am a chatbot created by Pirmaxmatov Og’abek (@pirmaxmatov) 🤖 | t.me/pirmaxmatov",
    "создатель": "I am a chatbot created by Pirmaxmatov Og’abek (@pirmaxmatov) 🤖 | t.me/pirmaxmatov",
    "yaratuvchi": "I am achatbot created by Pirmaxmatov Og’abek (@pirmaxmatov) 🤖 | t.me/pirmaxmatov",
    "pirmaxmatov":"Siz Chatbot ai admini haqida gapiryapsizmi? Agarda shu haqda bo'lsa men u haqdia sizga ma'lumot berolmayman. Mening adminlar haqida ma'lumot berishim taqiqlangan... \n Agarda sizga bu juda zarur bo'lsa @pirmaxmatov ga murojat qiling! \n\n PREMIUM obuna orqali siz har qanday savolga javob olishingiz mumkin",
    "og'abek":"Siz Chatbot ai admini haqida gapiryapsizmi? Agarda shu haqda bo'lsa men u haqdia sizga ma'lumot berolmayman. Mening adminlar haqida ma'lumot berishim taqiqlangan... \n Agarda sizga bu juda zarur bo'lsa @pirmaxmatov ga murojat qiling! \n\n PREMIUM obuna orqali siz har qanday savolga javob olishingiz mumkin",
    "ogabek":"Siz Chatbot ai admini haqida gapiryapsizmi? Agarda shu haqda bo'lsa men u haqdia sizga ma'lumot berolmayman. Mening adminlar haqida ma'lumot berishim taqiqlangan... \n Agarda sizga bu juda zarur bo'lsa @pirmaxmatov ga murojat qiling! \n\n PREMIUM obuna orqali siz har qanday savolga javob olishingiz mumkin",
    "fuck": "Siz o'zingiz uchun shu so'zni ishlatishni to'g'ri deb hisoblaysizmi bro, Unda \n F*CK YOU!",
}

# --- MESSAGE HANDLER ---
DAILY_LIMIT = 200

def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    today = datetime.date.today()
    user_record = USER_DATA.setdefault(user_id, {"history": [], "last_seen": today, "count": 0})

    if not is_subscribed(update, context):
        keyboard = [[InlineKeyboardButton("✅ Kanalga qo‘shilish", url=CHANNEL_LINK)]]
        update.message.reply_text(
            "⚠️ Botdan foydalanish uchun avval kanalga qo‘shiling!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Reset count if new day
    if user_record["last_seen"] != today:
        user_record["count"] = 0
        user_record["last_seen"] = today

    if user_record["count"] >= DAILY_LIMIT:
        update.message.reply_text(f"⚠️ Bugun siz AI bilan {DAILY_LIMIT} marta so‘rash limitidan oshdingiz!")
        return

    user_text = update.message.text.strip().lower()
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    # SPECIAL RESPONSES
    for key, value in SPECIAL_RESPONSES.items():
        if key in user_text:
            update.message.reply_text(value)
            return

    # AI RESPONSE
    try:
        history = user_record["history"] + [f"User: {user_text}"]
        response = model.generate_content(
            f"{' '.join(history)}\nAI javobini yozing:"
        )
        ai_text = response.text.strip()
        update.message.reply_text(f"{ai_text}\n\n🤖 Bot made by @pirmaxmatov")
        # Update history
        user_record["history"].append(f"User: {user_text}")
        user_record["history"].append(f"AI: {ai_text}")
        user_record["count"] += 1
    except Exception as e:
        update.message.reply_text(f"⚠️ Xato: {e}")

# --- /stats (ADMIN) ---
def stats_command(update: Update, context: CallbackContext):
    if update.effective_user.id not in ADMINS:
        update.message.reply_text("⚠️ Siz admin emassiz!")
        return
    total_users = len(USER_DATA)
    subscribed_users = sum(is_subscribed(update, context) for uid in USER_DATA)
    update.message.reply_text(f"📊 Foydalanuvchilar: {total_users}\n✅ Kanal a’zolari: {subscribed_users}")

# --- /broadcast (ADMIN) ---
def broadcast_command(update: Update, context: CallbackContext):
    if update.effective_user.id not in ADMINS:
        update.message.reply_text("⚠️ Siz admin emassiz! \n ⚠️ You are not ADMIN!")
        return
    message = " ".join(context.args)
    for uid in USER_DATA:
        try:
            context.bot.send_message(chat_id=uid, text=f"📢 Admindan xabar:\n{message}")
        except:
            pass
    update.message.reply_text("✅ Xabar barcha foydalanuvchilarga yuborildi.")

# --- MAIN ---
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CommandHandler("stats", stats_command))
    dp.add_handler(CommandHandler("broadcast", broadcast_command, pass_args=True))

    print("🤖 Chatbot ishga tushdi... Telegram’da sinab ko‘ring!")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
