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

# 1️⃣ Выбор языка
@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🇷🇺 Русский"), types.KeyboardButton(text="🇬🇧 English")]
        ],
        resize_keyboard=True
    )
    await message.answer("Выбери язык / Choose your language:", reply_markup=keyboard)

# 2️⃣ Получаем имя
@dp.message(lambda msg: msg.text in ["🇷🇺 Русский", "🇬🇧 English"])
async def ask_name(message: types.Message):
    lang = "ru" if "Русский" in message.text else "eng"
    user_data[message.from_user.id] = {"lang": lang}
    text = "Как тебя зовут?" if lang == "ru" else "What's your name?"
    await message.answer(text, reply_markup=types.ReplyKeyboardRemove())

# 3️⃣ Имя → возраст
@dp.message(lambda msg: msg.from_user.id in user_data and "name" not in user_data[msg.from_user.id])
async def ask_age(message: types.Message):
    user_data[message.from_user.id]["name"] = message.text
    lang = user_data[message.from_user.id]["lang"]
    text = "Сколько тебе лет?" if lang == "ru" else "How old are you?"
    await message.answer(text)

# 4️⃣ Возраст → город
@dp.message(lambda msg: msg.from_user.id in user_data and "age" not in user_data[msg.from_user.id])
async def ask_city(message: types.Message):
    user_data[message.from_user.id]["age"] = message.text
    lang = user_data[message.from_user.id]["lang"]
    text = "Из какого ты города?" if lang == "ru" else "Which city are you from?"
    await message.answer(text)

# 5️⃣ Отправляем данные владельцу
@dp.message(lambda msg: msg.from_user.id in user_data and "city" not in user_data[msg.from_user.id])
async def finish(message: types.Message):
    user = message.from_user
    data = user_data[message.from_user.id]
    data["city"] = message.text

    text = (
        f"📨 Новый пользователь!\n\n"
        f"👤 Имя: {data['name']}\n"
        f"🎂 Возраст: {data['age']}\n"
        f"🏙 Город: {data['city']}\n"
        f"🌐 Язык: {data['lang']}\n"
        f"🔗 Username: @{user.username or 'нет'}\n"
        f"🆔 Telegram ID: {user.id}"
    )

    await bot.send_message(OWNER_ID, text)
    await message.answer("✅ Спасибо! Данные отправлены.")

    del user_data[message.from_user.id]

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
