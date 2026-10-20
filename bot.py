import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from openai import AsyncOpenAI

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL")

MODELS = {
    "deepseek": "deepseek/deepseek-chat-v3-0324:free",
    "gemini": "google/gemini-2.0-flash-exp:free",
}

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY,
)

history = {}
user_model = {}
MAX_HISTORY = 10

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Я ИИ-помощник.\n"
        "Просто напиши вопрос.\n\n"
        "/model — выбрать модель (deepseek / gemini)\n"
        "/reset — очистить историю"
    )

@dp.message(Command("reset"))
async def reset(message: types.Message):
    history.pop(message.from_user.id, None)
    await message.answer("История очищена.")

@dp.message(Command("model"))
async def choose_model(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        current = user_model.get(message.from_user.id, DEFAULT_MODEL)
        await message.answer(
            f"Текущая модель: {current}\n\n"
            "Сменить: /model deepseek или /model gemini"
        )
        return
    choice = args[1].lower()
    if choice not in MODELS:
        await message.answer("Доступно: deepseek, gemini")
        return
    user_model[message.from_user.id] = MODELS[choice]
    await message.answer(f"Модель: {choice} ✅")

@dp.message()
async def chat(message: types.Message):
    user_id = message.from_user.id
    model = user_model.get(user_id, DEFAULT_MODEL)

    if user_id not in history:
        history[user_id] = [
            {"role": "system", "content": "Ты полезный помощник. Отвечай кратко и по делу."}
        ]

    history[user_id].append({"role": "user", "content": message.text})

    if len(history[user_id]) > MAX_HISTORY + 1:
        history[user_id] = [history[user_id][0]] + history[user_id][-MAX_HISTORY:]

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=history[user_id],
        )
        answer = response.choices[0].message.content
        history[user_id].append({"role": "assistant", "content": answer})
        await message.answer(answer)
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())