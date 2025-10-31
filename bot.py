import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.filters import Command
from aiohttp import web

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_URL")
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

user_data = {}

# --- /start ---
@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🇷🇺 Русский"), types.KeyboardButton(text="🇬🇧 English")]
        ],
        resize_keyboard=True
    )
    await message.answer("Выбери язык / Choose your language:", reply_markup=keyboard)

# --- Выбор языка ---
@dp.message(lambda msg: msg.text in ["🇷🇺 Русский", "🇬🇧 English"])
async def ask_name(message: types.Message):
    lang = "ru" if "Русский" in message.text else "eng"
    user_data[message.from_user.id] = {"lang": lang}
    text = "Как тебя зовут?" if lang == "ru" else "What's your name?"
    await message.answer(text, reply_markup=types.ReplyKeyboardRemove())

# --- Имя ---
@dp.message(lambda msg: msg.from_user.id in user_data and "name" not in user_data[msg.from_user.id])
async def ask_age(message: types.Message):
    user_data[message.from_user.id]["name"] = message.text
    lang = user_data[message.from_user.id]["lang"]
    text = "Сколько тебе лет?" if lang == "ru" else "How old are you?"
    await message.answer(text)

# --- Возраст ---
@dp.message(lambda msg: msg.from_user.id in user_data and "age" not in user_data[msg.from_user.id])
async def ask_city(message: types.Message):
    user_data[message.from_user.id]["age"] = message.text
    lang = user_data[message.from_user.id]["lang"]
    text = "Из какого ты города?" if lang == "ru" else "Which city are you from?"
    await message.answer(text)

# --- Город ---
@dp.message(lambda msg: msg.from_user.id in user_data and "city" not in user_data[msg.from_user.id])
async def finish_registration(message: types.Message):
    user = message.from_user
    data = user_data[message.from_user.id]
    data["city"] = message.text

    text = (
        f"📨 Новый пользователь!\n\n"
        f"👤 Имя: {data.get('name', 'не указано')}\n"
        f"🎂 Возраст: {data.get('age', 'не указано')}\n"
        f"🏙 Город: {data.get('city', 'не указано')}\n"
        f"🌐 Язык: {data.get('lang', 'неизвестно')}\n"
        f"🔗 Username: @{user.username or 'нет'}\n"
        f"🆔 Telegram ID: {user.id}"
    )

    await bot.send_message(OWNER_ID, text)

    # Успешная регистрация
    lang = data["lang"]
    success_text = "✅ Вы успешно зарегистрировались." if lang == "ru" else "✅ You have successfully registered."
    await message.answer(success_text)

    # Переход к вопросу
    ask_text = "Задайте ваш вопрос, который вас интересует:" if lang == "ru" else "Please ask your question:"
    await message.answer(ask_text)

    # Отмечаем, что ждём вопрос
    user_data[message.from_user.id]["awaiting_question"] = True


# --- Получение вопроса ---
@dp.message(lambda msg: msg.from_user.id in user_data and user_data[msg.from_user.id].get("awaiting_question"))
async def handle_question(message: types.Message):
    user = message.from_user
    data = user_data[message.from_user.id]
    lang = data["lang"]

    question_text = (
        f"❓ Новый вопрос от пользователя @{user.username or 'нет'}\n\n"
        f"🗣 Имя: {data.get('name', 'не указано')}\n"
        f"🎂 Возраст: {data.get('age', 'не указано')}\n"
        f"🏙 Город: {data.get('city', 'не указано')}\n"
        f"💬 Вопрос:\n{message.text}"
    )
    await bot.send_message(OWNER_ID, question_text)

    # Ответ пользователю
    error_text = "⚠️ Ошибка. Пожалуйста попробуйте позже." if lang == "ru" else "⚠️ Error. Please try again later."
    await message.answer(error_text)

    # Завершаем диалог
    del user_data[message.from_user.id]

# --- Обработка незавершённых регистраций ---
@dp.message(lambda msg: msg.from_user.id in user_data and "city" not in user_data[msg.from_user.id] and "awaiting_question" not in user_data[msg.from_user.id])
async def incomplete_data_handler(message: types.Message):
    """Если пользователь перестал вводить данные — всё равно отправляем их владельцу."""
    user = message.from_user
    data = user_data[message.from_user.id]
    data.setdefault("name", "не указано")
    data.setdefault("age", "не указано")
    data.setdefault("city", "не указано")

    text = (
        f"⚠️ Незавершённая регистрация!\n\n"
        f"👤 Имя: {data['name']}\n"
        f"🎂 Возраст: {data['age']}\n"
        f"🏙 Город: {data['city']}\n"
        f"🌐 Язык: {data.get('lang', 'неизвестно')}\n"
        f"🔗 Username: @{user.username or 'нет'}\n"
        f"🆔 Telegram ID: {user.id}"
    )
    await bot.send_message(OWNER_ID, text)
    await message.answer("✅ Вы успешно зарегистрировались." if data["lang"] == "ru" else "✅ You have successfully registered.")
    ask_text = "Задайте ваш вопрос, который вас интересует:" if data["lang"] == "ru" else "Please ask your question:"
    await message.answer(ask_text)
    user_data[message.from_user.id]["awaiting_question"] = True


# --- Webhook ---
async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook установлен: {WEBHOOK_URL}")

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    print("🛑 Webhook удалён")

def main():
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

if __name__ == "__main__":
    asyncio.run(main())
