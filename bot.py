import os
import google.generativeai as genai
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatAction, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import mimetypes
import sys
import types
import datetime
import json
import random
import requests
from typing import Dict, List

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

# --- USER DATABASE (in-memory) ---
USER_DATA = {}  # {user_id: {"history": [], "last_seen": date, "count": int, "language": "uz"}}

# ==================== MULTI-LANGUAGE SUPPORT ====================

LANGUAGES = {
    "uz": {
        "name": "🇺🇿 O'zbek",
        "code": "uz",
        "main_menu": {
            "lessons": "📚 Darslar",
            "ai_chat": "🤖 AI Chat",
            "profile": "🎯 Mening Profilim",
            "achievements": "🏆 Yutuqlar",
            "useful": "💡 Foydali",
            "settings": "⚙️ Sozlamalar",
            "help": "ℹ️ Yordam",
            "admin": "👨‍💻 Admin"
        },
        "messages": {
            "welcome": "👋 Xush kelibsiz! Tilni tanlang",
            "language_set": "✅ Til muvaffaqiyatli o'zgartirildi: {}",
            "not_subscribed": "⚠️ Botdan foydalanish uchun avval kanalga qo'shiling!",
            "daily_limit": "⚠️ Bugun siz AI bilan {} marta suhbat limitidan oshdingiz!",
            "not_admin": "⚠️ Siz admin emassiz!",
            "voice_processing": ["🎵 Ovozli xabaringiz qayta ishlanmoqda...", "🔊 Ovozingizni eshitdim...", "🎤 Ovozli xabar tahlil qilinmoqda..."]
        }
    },
    "en": {
        "name": "🇺🇸 English",
        "code": "en",
        "main_menu": {
            "lessons": "📚 Lessons",
            "ai_chat": "🤖 AI Chat",
            "profile": "🎯 My Profile",
            "achievements": "🏆 Achievements",
            "useful": "💡 Useful",
            "settings": "⚙️ Settings",
            "help": "ℹ️ Help",
            "admin": "👨‍💻 Admin"
        },
        "messages": {
            "welcome": "👋 Welcome! Choose your language",
            "language_set": "✅ Language successfully changed to: {}",
            "not_subscribed": "⚠️ Please subscribe to the channel to use the bot!",
            "daily_limit": "⚠️ You've exceeded the daily limit of {} AI conversations!",
            "not_admin": "⚠️ You are not an admin!",
            "voice_processing": ["🎵 Processing your voice message...", "🔊 Heard your voice...", "🎤 Analyzing voice message..."]
        }
    },
    "ru": {
        "name": "🇷🇺 Русский",
        "code": "ru",
        "main_menu": {
            "lessons": "📚 Уроки",
            "ai_chat": "🤖 AI Чат",
            "profile": "🎯 Мой Профиль",
            "achievements": "🏆 Достижения",
            "useful": "💡 Полезное",
            "settings": "⚙️ Настройки",
            "help": "ℹ️ Помощь",
            "admin": "👨‍💻 Админ"
        },
        "messages": {
            "welcome": "👋 Добро пожаловать! Выберите язык",
            "language_set": "✅ Язык успешно изменен на: {}",
            "not_subscribed": "⚠️ Подпишитесь на канал чтобы использовать бота!",
            "daily_limit": "⚠️ Вы превысили дневной лимит в {} AI разговоров!",
            "not_admin": "⚠️ Вы не администратор!",
            "voice_processing": ["🎵 Обрабатываю ваше голосовое сообщение...", "🔊 Услышал ваш голос...", "🎤 Анализирую голосовое сообщение..."]
        }
    },
    "ko": {
        "name": "🇰🇷 한국어",
        "code": "ko",
        "main_menu": {
            "lessons": "📚 수업",
            "ai_chat": "🤖 AI 채팅",
            "profile": "🎯 내 프로필",
            "achievements": "🏆 업적",
            "useful": "💡 유용한",
            "settings": "⚙️ 설정",
            "help": "ℹ️ 도움말",
            "admin": "👨‍💻 관리자"
        },
        "messages": {
            "welcome": "👋 환영합니다! 언어를 선택하세요",
            "language_set": "✅ 언어가 성공적으로 변경되었습니다: {}",
            "not_subscribed": "⚠️ 봇을 사용하려면 채널에 가입하세요!",
            "daily_limit": "⚠️ 일일 AI 대화 한도 {}회를 초과했습니다!",
            "not_admin": "⚠️ 관리자가 아닙니다!",
            "voice_processing": ["🎵 음성 메시지를 처리 중입니다...", "🔊 목소리를 들었습니다...", "🎤 음성 메시지를 분석 중입니다..."]
        }
    },
    "es": {
        "name": "🇪🇸 Español",
        "code": "es",
        "main_menu": {
            "lessons": "📚 Lecciones",
            "ai_chat": "🤖 Chat IA",
            "profile": "🎯 Mi Perfil",
            "achievements": "🏆 Logros",
            "useful": "💡 Útil",
            "settings": "⚙️ Configuración",
            "help": "ℹ️ Ayuda",
            "admin": "👨‍💻 Admin"
        },
        "messages": {
            "welcome": "👋 ¡Bienvenido! Elige tu idioma",
            "language_set": "✅ Idioma cambiado exitosamente a: {}",
            "not_subscribed": "⚠️ ¡Suscríbete al canal para usar el bot!",
            "daily_limit": "⚠️ ¡Has excedido el límite diario de {} conversaciones con IA!",
            "not_admin": "⚠️ ¡No eres administrador!",
            "voice_processing": ["🎵 Procesando tu mensaje de voz...", "🔊 Escuché tu voz...", "🎤 Analizando mensaje de voz..."]
        }
    },
    "ar": {
        "name": "🇸🇦 العربية",
        "code": "ar",
        "main_menu": {
            "lessons": "📚 الدروس",
            "ai_chat": "🤖 الدردشة الذكية",
            "profile": "🎯 ملفي",
            "achievements": "🏆 الإنجازات",
            "useful": "💡 مفيد",
            "settings": "⚙️ الإعدادات",
            "help": "ℹ️ المساعدة",
            "admin": "👨‍💻 المسؤول"
        },
        "messages": {
            "welcome": "👋 أهلاً وسهلاً! اختر لغتك",
            "language_set": "✅ تم تغيير اللغة بنجاح إلى: {}",
            "not_subscribed": "⚠️ يرجى الاشتراك في القناة لاستخدام البوت!",
            "daily_limit": "⚠️ لقد تجاوزت الحد اليومي البالغ {} محادثة ذكية!",
            "not_admin": "⚠️ لست مسؤولاً!",
            "voice_processing": ["🎵 جاري معالجة رسالتك الصوتية...", "🔊 سمعت صوتك...", "🎤 جاري تحليل الرسالة الصوتية..."]
        }
    },
    "fr": {
        "name": "🇫🇷 Français",
        "code": "fr",
        "main_menu": {
            "lessons": "📚 Leçons",
            "ai_chat": "🤖 Chat IA",
            "profile": "🎯 Mon Profil",
            "achievements": "🏆 Réalisations",
            "useful": "💡 Utile",
            "settings": "⚙️ Paramètres",
            "help": "ℹ️ Aide",
            "admin": "👨‍💻 Admin"
        },
        "messages": {
            "welcome": "👋 Bienvenue! Choisissez votre langue",
            "language_set": "✅ Langue changée avec succès en: {}",
            "not_subscribed": "⚠️ Veuillez vous abonner à la chaîne pour utiliser le bot!",
            "daily_limit": "⚠️ Vous avez dépassé la limite quotidienne de {} conversations IA!",
            "not_admin": "⚠️ Vous n'êtes pas administrateur!",
            "voice_processing": ["🎵 Traitement de votre message vocal...", "🔊 J'ai entendu votre voix...", "🎤 Analyse du message vocal..."]
        }
    },
    "ja": {
        "name": "🇯🇵 日本語",
        "code": "ja",
        "main_menu": {
            "lessons": "📚 レッスン",
            "ai_chat": "🤖 AIチャット",
            "profile": "🎯 マイプロフィール",
            "achievements": "🏆 実績",
            "useful": "💡 便利",
            "settings": "⚙️ 設定",
            "help": "ℹ️ ヘルプ",
            "admin": "👨‍💻 管理者"
        },
        "messages": {
            "welcome": "👋 ようこそ！言語を選択してください",
            "language_set": "✅ 言語が正常に変更されました: {}",
            "not_subscribed": "⚠️ ボットを使用するにはチャンネルに登録してください！",
            "daily_limit": "⚠️ 1日のAI会話制限{}회를 초과했습니다!",
            "not_admin": "⚠️ 管理者ではありません！",
            "voice_processing": ["🎵 音声メッセージを処理中...", "🔊 あなたの声を聞きました...", "🎤 音声メッセージを分析中..."]
        }
    },
    "pt": {
        "name": "🇵🇹 Português",
        "code": "pt",
        "main_menu": {
            "lessons": "📚 Lições",
            "ai_chat": "🤖 Chat IA",
            "profile": "🎯 Meu Perfil",
            "achievements": "🏆 Conquistas",
            "useful": "💡 Útil",
            "settings": "⚙️ Configurações",
            "help": "ℹ️ Ajuda",
            "admin": "👨‍💻 Admin"
        },
        "messages": {
            "welcome": "👋 Bem-vindo! Escolha seu idioma",
            "language_set": "✅ Idioma alterado com sucesso para: {}",
            "not_subscribed": "⚠️ Inscreva-se no canal para usar o bot!",
            "daily_limit": "⚠️ Você excedeu o limite diário de {} conversas com IA!",
            "not_admin": "⚠️ Você não é um administrador!",
            "voice_processing": ["🎵 Processando sua mensagem de voz...", "🔊 Ouvi sua voz...", "🎤 Analisando mensagem de voz..."]
        }
    }
}

def get_user_language(user_id: int) -> str:
    """Get user's language preference"""
    return USER_DATA.get(user_id, {}).get("language", "uz")

def get_text(user_id: int, text_key: str, format_args=None) -> str:
    """Get translated text for user"""
    lang_code = get_user_language(user_id)
    lang_data = LANGUAGES.get(lang_code, LANGUAGES["uz"])
    
    if format_args:
        return lang_data["messages"].get(text_key, text_key).format(*format_args)
    return lang_data["messages"].get(text_key, text_key)

# ==================== YOUTUBE LESSONS DATABASE ====================

YOUTUBE_LESSONS = {
    "uz": {
        "1_5": {
            "title": "📚 1-5 darslar: Python asoslari",
            "videos": [
                {"title": "1-dars: Python kirish va o'rnatish", "url": "https://youtu.be/kqtD5dpn9C8"},
                {"title": "2-dars: O'zgaruvchilar va ma'lumot turlari", "url": "https://youtu.be/WvhQhj4n6b8"},
                {"title": "3-dars: Operatorlar va ifodalar", "url": "https://youtu.be/7lmCu8wz8ro"},
                {"title": "4-dars: String metodlari", "url": "https://youtu.be/7lmCu8wz8ro"},
                {"title": "5-dars: Ro'yxatlar (Lists)", "url": "https://youtu.be/7lmCu8wz8ro"}
            ]
        },
        "6_10": {
            "title": "📚 6-10 darslar: Dasturiy mantik",
            "videos": [
                {"title": "6-dars: Shart operatorlari (if-else)", "url": "https://youtu.be/7lmCu8wz8ro"},
                {"title": "7-dars: Tsikllar (Loops)", "url": "https://youtu.be/7lmCu8wz8ro"},
                {"title": "8-dars: Funksiyalar", "url": "https://youtu.be/7lmCu8wz8ro"},
                {"title": "9-dars: Lug'atlar (Dictionaries)", "url": "https://youtu.be/7lmCu8wz8ro"},
                {"title": "10-dars: To'plamlar (Sets)", "url": "https://youtu.be/7lmCu8wz8ro"}
            ]
        },
        "11_15": {
            "title": "📚 11-15 darslar: OOP asoslari",
            "videos": [
                {"title": "11-dars: Klass va obyekt", "url": "https://youtu.be/7lmCu8wz8ro"},
                {"title": "12-dars: Meros olish", "url": "https://youtu.be/7lmCu8wz8ro"},
                {"title": "13-dars: Polimorfizm", "url": "https://youtu.be/7lmCu8wz8ro"},
                {"title": "14-dars: Encapsulation", "url": "https://youtu.be/7lmCu8wz8ro"},
                {"title": "15-dars: Abstract class", "url": "https://youtu.be/7lmCu8wz8ro"}
            ]
        }
    },
    "en": {
        "1_5": {
            "title": "📚 Lessons 1-5: Python Basics",
            "videos": [
                {"title": "Lesson 1: Python Introduction", "url": "https://youtu.be/kqtD5dpn9C8"},
                {"title": "Lesson 2: Variables & Data Types", "url": "https://youtu.be/WvhQhj4n6b8"},
                {"title": "Lesson 3: Operators", "url": "https://youtu.be/7lmCu8wz8ro"},
                {"title": "Lesson 4: String Methods", "url": "https://youtu.be/7lmCu8wz8ro"},
                {"title": "Lesson 5: Lists", "url": "https://youtu.be/7lmCu8wz8ro"}
            ]
        },
        "6_10": {
            "title": "📚 Lessons 6-10: Programming Logic",
            "videos": [
                {"title": "Lesson 6: If-Else Statements", "url": "https://youtu.be/7lmCu8wz8ro"},
                {"title": "Lesson 7: Loops", "url": "https://youtu.be/7lmCu8wz8ro"},
                {"title": "Lesson 8: Functions", "url": "https://youtu.be/7lmCu8wz8ro"},
                {"title": "Lesson 9: Dictionaries", "url": "https://youtu.be/7lmCu8wz8ro"},
                {"title": "Lesson 10: Sets", "url": "https://youtu.be/7lmCu8wz8ro"}
            ]
        }
    },
    "ru": {
        "1_5": {
            "title": "📚 Уроки 1-5: Основы Python",
            "videos": [
                {"title": "Урок 1: Введение и установка", "url": "https://youtu.be/kqtD5dpn9C8"},
                {"title": "Урок 2: Переменные и типы данных", "url": "https://youtu.be/WvhQhj4n6b8"},
                {"title": "Урок 3: Операторы и выражения", "url": "https://youtu.be/7lmCu8wz8ro"},
                {"title": "Урок 4: Методы строк", "url": "https://youtu.be/7lmCu8wz8ro"},
                {"title": "Урок 5: Списки", "url": "https://youtu.be/7lmCu8wz8ro"}
            ]
        }
    }
}

# ==================== ENHANCED MENU SYSTEM ====================

def get_main_menu_keyboard(user_id: int):
    """Create the main menu with user's language"""
    lang_code = get_user_language(user_id)
    lang_data = LANGUAGES.get(lang_code, LANGUAGES["uz"])
    menu = lang_data["main_menu"]
    
    keyboard = [
        [KeyboardButton(menu["lessons"]), KeyboardButton(menu["ai_chat"])],
        [KeyboardButton(menu["profile"]), KeyboardButton(menu["achievements"])],
        [KeyboardButton(menu["useful"]), KeyboardButton(menu["settings"])],
        [KeyboardButton(menu["help"]), KeyboardButton(menu["admin"])]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder=menu["help"])

def get_language_keyboard():
    """Create language selection keyboard"""
    keyboard = []
    languages_list = list(LANGUAGES.values())
    
    for i in range(0, len(languages_list), 3):
        row = []
        for lang in languages_list[i:i+3]:
            row.append(InlineKeyboardButton(lang["name"], callback_data=f"set_lang_{lang['code']}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_lessons_menu_keyboard(user_id: int):
    """Create lessons menu with organized blocks"""
    lang_code = get_user_language(user_id)
    back_text = "🔙 Asosiy menyu" if lang_code == "uz" else "🔙 Main Menu"
    
    keyboard = [
        [
            InlineKeyboardButton("1-5 dars", callback_data="lessons_1_5"),
            InlineKeyboardButton("6-10 dars", callback_data="lessons_6_10")
        ],
        [
            InlineKeyboardButton("11-15 dars", callback_data="lessons_11_15"),
            InlineKeyboardButton("16-20 dars", callback_data="lessons_16_20")
        ],
        [
            InlineKeyboardButton("21-25 dars", callback_data="lessons_21_25"),
            InlineKeyboardButton("26-30 dars", callback_data="lessons_26_30")
        ],
        [
            InlineKeyboardButton("31-35 dars", callback_data="lessons_31_35"),
            InlineKeyboardButton("36-40 dars", callback_data="lessons_36_40")
        ],
        [
            InlineKeyboardButton("📊 Test topshiriqlar", callback_data="lessons_tests"),
            InlineKeyboardButton("🎓 Certificate", callback_data="lessons_certificate")
        ],
        [InlineKeyboardButton(back_text, callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_settings_menu_keyboard(user_id: int):
    """Settings menu in user's language"""
    lang_code = get_user_language(user_id)
    back_text = "🔙 Asosiy menyu" if lang_code == "uz" else "🔙 Main Menu"
    
    keyboard = [
        [
            InlineKeyboardButton("🌐 Til sozlamalari", callback_data="set_language"),
            InlineKeyboardButton("🔔 Bildirishnomalar", callback_data="set_notifications")
        ],
        [
            InlineKeyboardButton("📏 Oʻlchov birliklari", callback_data="set_units"),
            InlineKeyboardButton("🎨 Mavzu", callback_data="set_theme")
        ],
        [
            InlineKeyboardButton("📊 Statistikani tozalash", callback_data="clear_stats"),
            InlineKeyboardButton("🔄 Chat tarixini tozalash", callback_data="clear_history")
        ],
        [InlineKeyboardButton(back_text, callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_subscription_keyboard():
    """Kanalga a'zo bo'lish tugmalari"""
    keyboard = [
        [InlineKeyboardButton("✅ Kanalga qo'shilish", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ A'zo bo'ldim", callback_data="check_subscription")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== ENHANCED AI PROMPTS FOR MULTI-LANGUAGE ====================

AI_PROMPTS = {
    "uz": """
Siz Pirmaxmatov AI - @pirmaxmatov tomonidan yaratilgan yordamchi assistantsiz.
Siz o'zbek tilida savollarga javob berasiz va quyidagi sohalarda yordam berasiz:
- Ta'lim va o'qish
- Texnologiya va dasturlash
- Kundalik hayot masalalari
- Ijodiy g'oyalar
- Muammolarni yechish

Javoblaringiz qisqa, ammo foydali (2-5 gap) bo'lsin.
Do'stona va yaqin munosabatda bo'ling.
O'zbek madaniyatiga mos tushunarli bo'ling.
Amaliy va bajarish mumkin bo'lsin.
""",
    "en": """
You are Pirmaxmatov AI - a helpful assistant created by @pirmaxmatov.
You respond in English and help with:
- Education and learning
- Technology and programming
- Daily life advice
- Creative ideas
- Problem solving

Keep responses concise but helpful (2-5 sentences ideal).
Be friendly and approachable.
Use clear, practical language.
Provide actionable advice.
""",
    "ru": """
Вы Pirmaxmatov AI - помощник, созданный @pirmaxmatov.
Вы отвечаете на русском и помогаете с:
- Образованием и обучением
- Технологиями и программированием
- Советами по повседневной жизни
- Творческими идеями
- Решением проблем

Давайте краткие, но полезные ответы (2-5 предложений).
Будьте дружелюбны и доступны.
Используйте понятный, практичный язык.
Предоставляйте действенные советы.
""",
    "ko": """
당신은 @pirmaxmatov가 만든 도움이 되는 어시스턴트 Pirmaxmatov AI입니다.
한국어로 응답하며 다음을 도와줍니다:
- 교육 및 학습
- 기술 및 프로그래밍
- 일상 생활 조언
- 창의적인 아이디어
- 문제 해결

답변은 간결하지만 도움이 되도록 하세요(2-5문장).
친근하고 접근하기 쉽게.
명확하고 실용적인 언어를 사용하세요.
실행 가능한 조언을 제공하세요.
""",
    "es": """
Eres Pirmaxmatov AI - un asistente útil creado por @pirmaxmatov.
Respondes en español y ayudas con:
- Educación y aprendizaje
- Tecnología y programación
- Consejos de vida diaria
- Ideas creativas
- Resolución de problemas

Mantén las respuestas concisas pero útiles (2-5 oraciones ideal).
Sé amigable y accesible.
Usa lenguaje claro y práctico.
Proporciona consejos accionables.
""",
    "ar": """
أنت Pirmaxmatov AI - مساعد مفيد تم إنشاؤه بواسطة @pirmaxmatov.
تستجيب باللغة العربية وتساعد في:
- التعليم والتعلم
- التكنولوجيا والبرمجة
- نصائح الحياة اليومية
- الأفكار الإبداعية
- حل المشكلات

اجعل الردود موجزة ولكن مفيدة (2-5 جمل مثالي).
كن ودودًا وسهل الوصول.
استخدم لغة واضحة وعملية.
قدم نصائح قابلة للتنفيذ.
""",
    "fr": """
Vous êtes Pirmaxmatov AI - un assistant utile créé par @pirmaxmatov.
Vous répondez en français et aidez avec:
- Éducation et apprentissage
- Technologie et programmation
- Conseils de vie quotidienne
- Idées créatives
- Résolution de problèmes

Gardez les réponses concises mais utiles (2-5 phrases idéal).
Soyez amical et abordable.
Utilisez un langage clair et pratique.
Fournissez des conseils actionnables.
""",
    "ja": """
あなたは@ pirmaxmatovによって作成された役立つアシスタント、Pirmaxmatov AIです。
日本語で応答し、以下を支援します：
- 教育と学習
- テクノロジーとプログラミング
- 日常生活のアドバイス
- 創造的なアイデア
- 問題解決

回答は簡潔だが役立つものにしてください（理想的には2〜5文）。
フレンドリーで親しみやすいです。
明確で実用的な言語を使用してください。
実行可能なアドバイスを提供してください。
""",
    "pt": """
Você é o Pirmaxmatov AI - um assistente útil criado por @pirmaxmatov.
Você responde em português e ajuda com:
- Educação e aprendizagem
- Tecnologia e programação
- Conselhos de vida diária
- Ideias criativas
- Resolução de problemas

Mantenha as respostas concisas, mas úteis (2-5 frases ideal).
Seja amigável e acessível.
Use linguagem clara e prática.
Forneça conselhos acionáveis.
"""
}

# ==================== USER LEVELS & ACHIEVEMENTS ====================

USER_LEVELS = {
    1: "🟢 Beginner",
    5: "🔵 Active User", 
    10: "🟣 Regular",
    20: "🟡 Pro",
    50: "🟠 Expert",
    100: "🔴 Master"
}

def calculate_user_level(message_count: int) -> int:
    if message_count >= 100: return 6
    elif message_count >= 50: return 5
    elif message_count >= 20: return 4
    elif message_count >= 10: return 3
    elif message_count >= 5: return 2
    else: return 1

def optimize_chat_history(history: List[str]) -> List[str]:
    MAX_HISTORY_LENGTH = 15
    if len(history) > MAX_HISTORY_LENGTH * 2:
        optimized = history[:2] + history[-(MAX_HISTORY_LENGTH*2-2):]
        return optimized
    return history

def get_user_profile(user_id: int) -> str:
    user_record = USER_DATA.get(user_id, {})
    message_count = user_record.get("count", 0)
    level = calculate_user_level(message_count)
    level_name = USER_LEVELS.get(level, "🟢 Beginner")
    lang_code = get_user_language(user_id)
    
    profile_texts = {
        "uz": f"""👤 **Foydalanuvchi Profili**

📊 Daraja: {level_name} (Level {level})
💬 Bugungi xabarlar: {message_count}/200
📈 Jami suhbatlar: {len(user_record.get('history', []))//2}
🌐 Til: {LANGUAGES[lang_code]['name']}

🎯 Yutuqlar: {len(user_record.get('achievements', []))} ta
        """,
        "en": f"""👤 **User Profile**

📊 Level: {level_name} (Level {level})
💬 Today's messages: {message_count}/200
📈 Total conversations: {len(user_record.get('history', []))//2}
🌐 Language: {LANGUAGES[lang_code]['name']}

🎯 Achievements: {len(user_record.get('achievements', []))}
        """
    }
    
    return profile_texts.get(lang_code, profile_texts["uz"])

def get_achievements_text(user_id: int):
    user_record = USER_DATA.get(user_id, {})
    achievements = user_record.get("achievements", [])
    lang_code = get_user_language(user_id)
    
    achievement_texts = {
        "uz": "🏆 **Sizning yutuqlaringiz:**\n\n",
        "en": "🏆 **Your Achievements:**\n\n"
    }
    
    if achievements:
        achievement_text = achievement_texts.get(lang_code, achievement_texts["uz"])
        achievement_text += "\n".join(f"• {ach}" for ach in achievements)
    else:
        achievement_text = "🎯 Hali yutuqlaringiz yo'q! Faolroq bo'ling!" if lang_code == "uz" else "🎯 No achievements yet! Be more active!"
    
    return achievement_text

# ==================== CORE HANDLERS ====================

def is_subscribed(update: Update, context: CallbackContext):
    try:
        user_id = update.effective_user.id
        status = context.bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ["member", "administrator", "creator"]
    except Exception:
        return False

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    USER_DATA.setdefault(user_id, {
        "history": [], 
        "last_seen": datetime.date.today(), 
        "count": 0, 
        "achievements": [], 
        "language": "uz"
    })
    
    user_record = USER_DATA[user_id]
    if "first_chat" not in user_record.get("achievements", []):
        user_record.setdefault("achievements", []).append("first_chat")
    
    if not is_subscribed(update, context):
        update.message.reply_text(
            get_text(user_id, "welcome"),
            reply_markup=get_subscription_keyboard()
        )
        return
    
    # Show language selection
    update.message.reply_text(
        get_text(user_id, "welcome"),
        reply_markup=get_language_keyboard()
    )

def show_main_menu_message(update, user_id):
    """Show main menu message in user's language"""
    lang_code = get_user_language(user_id)
    welcome_texts = {
        "uz": f"✅ Siz allaqachon {CHANNEL_USERNAME} a'zosisiz!\n\n🚀 **Yangi tizimli interfeys:**",
        "en": f"✅ You're already subscribed to {CHANNEL_USERNAME}!\n\n🚀 **New organized interface:**",
        "ru": f"✅ Вы уже подписаны на {CHANNEL_USERNAME}!\n\n🚀 **Новый организованный интерфейс:**",
        "ko": f"✅ 이미 {CHANNEL_USERNAME}에 가입하셨습니다!\n\n🚀 **새로운 체계적인 인터페이스:**",
        "es": f"✅ ¡Ya estás suscrito a {CHANNEL_USERNAME}!\n\n🚀 **Nueva interfaz organizada:**",
        "ar": f"✅ أنت مشترك بالفعل في {CHANNEL_USERNAME}!\n\n🚀 **واجهة منظمة جديدة:**",
        "fr": f"✅ Vous êtes déjà abonné à {CHANNEL_USERNAME}!\n\n🚀 **Nouvelle interface organisée:**",
        "ja": f"✅ あなたはすでに {CHANNEL_USERNAME} に登録しています!\n\n🚀 **新しい整理されたインターフェース:**",
        "pt": f"✅ Você já está inscrito em {CHANNEL_USERNAME}!\n\n🚀 **Nova interface organizada:**"
    }
    
    welcome_text = welcome_texts.get(lang_code, welcome_texts["uz"])
    
    if hasattr(update, 'message'):
        update.message.reply_text(welcome_text, reply_markup=get_main_menu_keyboard(user_id))
    else:
        update.edit_message_text(welcome_text, reply_markup=get_main_menu_keyboard(user_id))

def check_subscription_handler(update: Update, context: CallbackContext):
    """A'zo bo'ldim tugmasi bosilganda"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if is_subscribed(update, context):
        # Agar haqiqatan a'zo bo'lsa, til tanlashni ko'rsatish
        query.edit_message_text(
            get_text(user_id, "welcome"),
            reply_markup=get_language_keyboard()
        )
    else:
        # Agar a'zo bo'lmagan bo'lsa, qayta so'rash
        query.edit_message_text(
            "❌ Hali kanalga a'zo bo'lmagansiz! Iltimos, quyidagi kanalga a'zo bo'ling va 'A'zo bo'ldim' tugmasini bosing:",
            reply_markup=get_subscription_keyboard()
        )

def handle_language_selection(update: Update, context: CallbackContext, lang_code: str):
    """Tilni o'zgartirish"""
    query = update.callback_query
    user_id = query.from_user.id
    
    USER_DATA.setdefault(user_id, {
        "history": [], 
        "last_seen": datetime.date.today(), 
        "count": 0, 
        "achievements": [], 
        "language": lang_code
    })
    USER_DATA[user_id]["language"] = lang_code
    
    query.edit_message_text(
        get_text(user_id, "language_set", [LANGUAGES[lang_code]["name"]])
    )
    show_main_menu_message(update, user_id)

def handle_lessons_with_videos(update: Update, lesson_key: str):
    """YouTube darslarini ko'rsatish"""
    query = update.callback_query
    user_id = query.from_user.id
    lang_code = get_user_language(user_id)
    
    lessons_data = YOUTUBE_LESSONS.get(lang_code, YOUTUBE_LESSONS["uz"])
    lesson = lessons_data.get(lesson_key)
    
    if not lesson:
        lesson = YOUTUBE_LESSONS["uz"].get(lesson_key, YOUTUBE_LESSONS["uz"]["1_5"])
    
    response_text = f"{lesson['title']}\n\n"
    
    for i, video in enumerate(lesson.get("videos", []), 1):
        response_text += f"{i}. [{video['title']}]({video['url']})\n"
    
    response_text += f"\n📚 **Darslar davom etadi...**\n🤖 @pirmaxmatov AI"
    
    query.edit_message_text(
        response_text,
        reply_markup=get_lessons_menu_keyboard(user_id),
        parse_mode='Markdown',
        disable_web_page_preview=False
    )

def button_handler(update: Update, context: CallbackContext):
    """Barcha tugma bosishlarni boshqarish"""
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # A'zo bo'ldim tekshirish
    if data == "check_subscription":
        check_subscription_handler(update, context)
        return
    
    # Til sozlash
    if data.startswith("set_lang_"):
        lang_code = data.replace("set_lang_", "")
        handle_language_selection(update, context, lang_code)
        return
    
    # Darslar
    if data.startswith("lessons_") and data not in ["lessons_tests", "lessons_certificate"]:
        handle_lessons_with_videos(update, data.replace("lessons_", ""))
        return
    
    # Asosiy menyu
    if data == "main_menu":
        show_main_menu_message(update, user_id)
    
    # Boshqa handlerlar...
    elif data == "set_language":
        query.edit_message_text(
            "🌍 **Tilni tanlang / Choose language:**",
            reply_markup=get_language_keyboard()
        )
    elif data == "lessons_tests":
        query.edit_message_text(
            "📊 **Test topshiriqlar tez orada!**\n\nHozircha darslarni ko'rib chiqing.",
            reply_markup=get_lessons_menu_keyboard(user_id)
        )
    elif data == "lessons_certificate":
        query.edit_message_text(
            "🎓 **Sertifikat olish imkoniyati tez orada!**",
            reply_markup=get_lessons_menu_keyboard(user_id)
        )
    else:
        query.edit_message_text(
            f"🚀 **{data} funksiyasi tez orada ishga tushadi!**\n\nBoshqa bo'limlardan foydalaning.",
            reply_markup=get_lessons_menu_keyboard(user_id)
        )

def handle_text_message(update: Update, context: CallbackContext):
    """Handle text messages with menu system"""
    user_id = update.effective_user.id
    user_text = update.message.text.strip()
    lang_code = get_user_language(user_id)
    
    # Get menu texts in user's language
    menu_texts = LANGUAGES.get(lang_code, LANGUAGES["uz"])["main_menu"]
    
    if user_text == menu_texts["lessons"]:
        update.message.reply_text(
            "📚 **Darslar bo'limi**\n\nQuyidagi dars bloklaridan birini tanlang:",
            reply_markup=get_lessons_menu_keyboard(user_id)
        )
    elif user_text == menu_texts["ai_chat"]:
        update.message.reply_text(
            "🤖 **AI Chat rejimi**\n\nEndi siz AI bilan suhbatlashishingiz mumkin!\nIstalgan savolingizni yuboring.",
            reply_markup=get_main_menu_keyboard(user_id)
        )
    elif user_text == menu_texts["profile"]:
        profile_text = get_user_profile(user_id)
        update.message.reply_text(profile_text, reply_markup=get_main_menu_keyboard(user_id))
    elif user_text == menu_texts["achievements"]:
        achievements_text = get_achievements_text(user_id)
        update.message.reply_text(achievements_text, reply_markup=get_main_menu_keyboard(user_id))
    elif user_text == menu_texts["settings"]:
        update.message.reply_text(
            "⚙️ **Sozlamalar**\n\nBot sozlamalarini o'zgartiring:",
            reply_markup=get_settings_menu_keyboard(user_id)
        )
    elif user_text == menu_texts["help"]:
        show_help(update, user_id)
    elif user_text == menu_texts["admin"]:
        if user_id in ADMINS:
            show_admin_menu(update, user_id)
        else:
            update.message.reply_text(get_text(user_id, "not_admin"), reply_markup=get_main_menu_keyboard(user_id))
    else:
        handle_ai_chat(update, context)

def show_help(update: Update, user_id: int):
    """Show help in user's language"""
    lang_code = get_user_language(user_id)
    
    help_texts = {
        "uz": """
🎯 **Botdan foydalanish boʻyicha yoʻriqnoma:**

📚 **Darslar** - Tizimli bilim olish
• 1-40 gacha boʻlgan darslar
• YouTube video darslar
• Test topshiriqlari

🤖 **AI Chat** - Sun'iy intellekt
• Har qanday savolga javob
• Kundalik 200 ta xabar limiti
• 9 xil til qo'llab-quvvatlashi

🎯 **Mening Profilim** - Shaxsiy statistika
• Darajalar tizimi
• Faollik ko'rsatkichlari
• Yutuqlar ro'yxati

⚙️ **Sozlamalar** - Shaxsiylashtirish
• Til sozlamalari (9 ta til)
• Mavzu tanlash
• Statistikani tozalash

🌍 **Tillar:** O'zbek, English, Русский, 한국어, Español, العربية, Français, 日本語, Português

🤖 @pirmaxmatov tomonidan yaratilgan
        """,
        "en": """
🎯 **User Guide:**

📚 **Lessons** - Systematic learning
• Lessons 1-40
• YouTube video lessons
• Test assignments

🤖 **AI Chat** - Artificial Intelligence
• Answers to any questions
• Daily 200 message limit
• Supports 9 languages

🎯 **My Profile** - Personal statistics
• Level system
• Activity indicators
• Achievements list

⚙️ **Settings** - Personalization
• Language settings (9 languages)
• Theme selection
• Clear statistics

🌍 **Languages:** Uzbek, English, Russian, Korean, Spanish, Arabic, French, Japanese, Portuguese

🤖 Created by @pirmaxmatov
        """
    }
    
    help_text = help_texts.get(lang_code, help_texts["uz"])
    update.message.reply_text(help_text, reply_markup=get_main_menu_keyboard(user_id))

def show_admin_menu(update: Update, user_id: int):
    """Show admin menu"""
    admin_text = "👨‍💻 **Admin Panel**\n\n"
    admin_text += "/stats - Bot statistikasi\n"
    admin_text += "/broadcast - Xabar yuborish\n"
    admin_text += "/top - Top foydalanuvchilar\n"
    
    update.message.reply_text(admin_text, reply_markup=get_main_menu_keyboard(user_id))

def handle_ai_chat(update: Update, context: CallbackContext):
    """Handle AI chat messages with language support"""
    user_id = update.effective_user.id
    today = datetime.date.today()
    user_record = USER_DATA.setdefault(user_id, {
        "history": [], 
        "last_seen": today, 
        "count": 0, 
        "achievements": [], 
        "language": "uz"
    })

    if not is_subscribed(update, context):
        update.message.reply_text(
            get_text(user_id, "not_subscribed"),
            reply_markup=get_subscription_keyboard()
        )
        return

    # Reset count if new day
    if user_record["last_seen"] != today:
        user_record["count"] = 0
        user_record["last_seen"] = today

    DAILY_LIMIT = 200
    if user_record["count"] >= DAILY_LIMIT:
        update.message.reply_text(get_text(user_id, "daily_limit", [DAILY_LIMIT]))
        return

    user_text = update.message.text.strip()
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    # AI RESPONSE with language-specific prompt
    try:
        lang_code = get_user_language(user_id)
        ai_prompt = AI_PROMPTS.get(lang_code, AI_PROMPTS["uz"])
        
        optimized_history = optimize_chat_history(user_record["history"])
        full_prompt = f"{ai_prompt}\n\nConversation:\n{' '.join(optimized_history[-6:])}\n\nUser: {user_text}\nAssistant:"
        
        response = model.generate_content(full_prompt)
        ai_text = response.text.strip()
        
        # Add signature in user's language
        signatures = {
            "uz": "\n\n🤖 @pirmaxmatov AI",
            "en": "\n\n🤖 @pirmaxmatov AI", 
            "ru": "\n\n🤖 @pirmaxmatov AI",
            "ko": "\n\n🤖 @pirmaxmatov AI",
            "es": "\n\n🤖 @pirmaxmatov AI",
            "ar": "\n\n🤖 @pirmaxmatov AI",
            "fr": "\n\n🤖 @pirmaxmatov AI",
            "ja": "\n\n🤖 @pirmaxmatov AI",
            "pt": "\n\n🤖 @pirmaxmatov AI"
        }
        
        ai_text += signatures.get(lang_code, signatures["uz"])
        
        update.message.reply_text(ai_text, reply_markup=get_main_menu_keyboard(user_id))
        
        # Update history
        user_record["history"].append(f"User: {user_text}")
        user_record["history"].append(f"AI: {ai_text}")
        user_record["history"] = optimize_chat_history(user_record["history"])
        user_record["count"] += 1
        
    except Exception as e:
        error_text = f"⚠️ Xato: {e}" if get_user_language(user_id) == "uz" else f"⚠️ Error: {e}"
        update.message.reply_text(error_text, reply_markup=get_main_menu_keyboard(user_id))

def handle_voice_message(update: Update, context: CallbackContext):
    """Handle voice messages in user's language"""
    user_id = update.effective_user.id
    
    if not is_subscribed(update, context):
        update.message.reply_text(
            get_text(user_id, "not_subscribed"),
            reply_markup=get_subscription_keyboard()
        )
        return
    
    voice_responses = get_text(user_id, "voice_processing")
    if isinstance(voice_responses, str):
        voice_responses = [voice_responses]
    
    voice_response = random.choice(voice_responses)
    update.message.reply_text(voice_response, reply_markup=get_main_menu_keyboard(user_id))
    
    # Add voice achievement
    user_record = USER_DATA.setdefault(user_id, {
        "history": [], 
        "last_seen": datetime.date.today(), 
        "count": 0, 
        "achievements": []
    })
    if "voice_user" not in user_record.get("achievements", []):
        user_record.setdefault("achievements", []).append("voice_user")
        achievement_text = "🎉 Yangi yutuq: 🎤 Ovozli xabar yuboruvchi!" if get_user_language(user_id) == "uz" else "🎉 New achievement: 🎤 Voice message sender!"
        update.message.reply_text(achievement_text, reply_markup=get_main_menu_keyboard(user_id))

# ==================== ADMIN COMMANDS ====================

def stats_command(update: Update, context: CallbackContext):
    if update.effective_user.id not in ADMINS:
        update.message.reply_text(get_text(update.effective_user.id, "not_admin"))
        return
    
    total_users = len(USER_DATA)
    active_today = sum(1 for uid, data in USER_DATA.items() 
                      if data.get("last_seen") == datetime.date.today())
    total_messages = sum(data.get("count", 0) for data in USER_DATA.values())
    
    # Language distribution
    lang_dist = {}
    for data in USER_DATA.values():
        lang = data.get("language", "uz")
        lang_dist[lang] = lang_dist.get(lang, 0) + 1
    
    stats_text = f"📊 **Bot Statistikasi**\n\n"
    stats_text += f"👥 Jami foydalanuvchilar: {total_users}\n"
    stats_text += f"🟢 Bugun faol: {active_today}\n"
    stats_text += f"💬 Bugun xabarlar: {total_messages}\n\n"
    stats_text += f"🌍 Tillar bo'yicha:\n"
    for lang, count in sorted(lang_dist.items()):
        lang_name = LANGUAGES.get(lang, {}).get("name", lang)
        stats_text += f"  {lang_name}: {count} ta\n"
    
    update.message.reply_text(stats_text)

def top_command(update: Update, context: CallbackContext):
    if update.effective_user.id not in ADMINS:
        update.message.reply_text(get_text(update.effective_user.id, "not_admin"))
        return
    
    top_users = sorted(USER_DATA.items(), key=lambda x: x[1].get("count", 0), reverse=True)[:10]
    
    top_text = "🏆 **Top 10 Faol Foydalanuvchilar:**\n\n"
    for i, (user_id, data) in enumerate(top_users, 1):
        level = calculate_user_level(data.get("count", 0))
        level_name = USER_LEVELS.get(level, "🟢 Beginner")
        top_text += f"{i}. ID {user_id}: {data.get('count', 0)} xabar - {level_name}\n"
    
    update.message.reply_text(top_text)

def broadcast_command(update: Update, context: CallbackContext):
    if update.effective_user.id not in ADMINS:
        update.message.reply_text(get_text(update.effective_user.id, "not_admin"))
        return
    
    if not context.args:
        update.message.reply_text("ℹ️ Foydalanish: /broadcast [xabar matni]")
        return
        
    message = " ".join(context.args)
    sent_count = 0
    
    for uid in USER_DATA:
        try:
            context.bot.send_message(chat_id=uid, text=f"📢 Admindan xabar:\n{message}")
            sent_count += 1
        except:
            continue
    
    update.message.reply_text(f"✅ Xabar {sent_count} ta foydalanuvchiga yuborildi.")

# ==================== MAIN FUNCTION ====================

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stats", stats_command))
    dp.add_handler(CommandHandler("broadcast", broadcast_command, pass_args=True))
    dp.add_handler(CommandHandler("top", top_command))
    
    # Message handlers
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text_message))
    dp.add_handler(MessageHandler(Filters.voice, handle_voice_message))

    print("🚀🤖 MULTI-LANGUAGE Chatbot ishga tushdi...")
    print("✨ Yangi imkoniyatlar:")
    print("   • ✅ Kanal tekshirish tizimi")
    print("   • 🌍 9 xil til qo'llab-quvvatlashi") 
    print("   • 📚 REAL YouTube darslar")
    print("   • 🎯 Avtomatik menyu ko'rsatish")
    print("   • 🤖 Gemini AI integratsiyasi")
    print("   • 📊 Foydalanuvchi statistikasi")
    print("   • 🏆 Yutuqlar tizimi")
    print("   • 👨‍💻 Admin panel")
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()