from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import asyncio


TOKEN = "8315087330:AAH6VNsvsQHYL-SadlVBPMzc51arGYszJkk"
ADMIN_ID = 8212948557

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()
router = Router()
dp.include_router(router)

# Состояния
class Form(StatesGroup):
    language = State()
    name = State()
    age = State()
    city = State()

# Кнопки выбора языка
language_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🇷🇺 Русский"), KeyboardButton(text="🇬🇧 English")]
    ],
    resize_keyboard=True
)

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await message.answer("Выберите язык / Choose your language:", reply_markup=language_kb)
    await state.set_state(Form.language)

@router.message(Form.language)
async def set_language(message: Message, state: FSMContext):
    lang = message.text.lower()
    if "рус" in lang:
        await state.update_data(language="ru")
        await message.answer("Введите ваше имя:", reply_markup=None)
    elif "eng" in lang or "english" in lang:
        await state.update_data(language="en")
        await message.answer("Enter your name:", reply_markup=None)
    else:
        await message.answer("Пожалуйста, выберите язык кнопкой.")
        return
    await state.set_state(Form.name)

@router.message(Form.name)
async def set_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    data = await state.get_data()
    if data["language"] == "ru":
        await message.answer("Введите ваш возраст:")
    else:
        await message.answer("Enter your age:")
    await state.set_state(Form.age)

@router.message(Form.age)
async def set_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    data = await state.get_data()
    if data["language"] == "ru":
        await message.answer("Введите ваш город:")
    else:
        await message.answer("Enter your city:")
    await state.set_state(Form.city)

@router.message(Form.city)
async def set_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    data = await state.get_data()
    username = f"@{message.from_user.username}" if message.from_user.username else "—"
    
    # Формирование текста
    if data["language"] == "ru":
        text = (
            f"📝 Новая анкета:\n\n"
            f"Имя: {data['name']}\n"
            f"Возраст: {data['age']}\n"
            f"Город: {data['city']}\n"
            f"Username: {username}"
        )
        await message.answer("Спасибо! Ваши данные отправлены.")
    else:
        text = (
            f"📝 New submission:\n\n"
            f"Name: {data['name']}\n"
            f"Age: {data['age']}\n"
            f"City: {data['city']}\n"
            f"Username: {username}"
        )
        await message.answer("Thank you! Your data has been sent.")
    
    # Отправка данных админу
    await bot.send_message(ADMIN_ID, text)
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
