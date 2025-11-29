import asyncio
import logging
import os
import random
from pathlib import Path
from typing import List, Set

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatType
from aiogram.types import Message
from config import BOT_TOKEN

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
SPECIAL_PHRASES_FILE = DATA_DIR / "special_phrases.txt"
FALLBACK_SPECIAL_PHRASES = ["окак-патруль подлетает"]
TRIGGER = "окак"
RESPONSE_CHANCE = 0.15

# Список игнорируемых пользователей (юзернеймы или ID)
IGNORED_USERS: List[str] = []

# Список специальных пользователей (всегда получают ответ)
SPECIAL_USERS: List[str] = []


def _read_list(path: Path) -> List[str]:
    if not path.exists():
        return []
    return [
        line.strip().lstrip("@")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def load_ignored_users() -> Set[str]:
    # Храним юзернеймы/ID в нижнем регистре для надёжного сравнения
    return {u.strip().lstrip("@").lower() for u in IGNORED_USERS if u.strip()}


def load_special_users() -> Set[str]:
    # Храним юзернеймы/ID в нижнем регистре для надёжного сравнения
    return {u.strip().lstrip("@").lower() for u in SPECIAL_USERS if u.strip()}


def load_special_phrases() -> List[str]:
    phrases = _read_list(SPECIAL_PHRASES_FILE)
    return phrases or FALLBACK_SPECIAL_PHRASES


def normalize_username(message: Message) -> str:
    user = message.from_user
    if not user:
        return ""
    if user.username:
        return user.username.lower()
    return str(user.id)


async def handle_message(message: Message) -> None:
    username = normalize_username(message)
    ignored_users = load_ignored_users()
    special_users = load_special_users()
    special_phrases = load_special_phrases()

    if username in ignored_users:
        return

    if username in special_users:
        phrase = random.choice(special_phrases)
    else:
        if random.random() >= RESPONSE_CHANCE:
            return
        phrase = TRIGGER

    await message.reply(phrase)


async def main() -> None:
    logging.basicConfig(
        level=logging.ERROR,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    if not BOT_TOKEN:
        raise RuntimeError("Укажите реальный токен в файле config.py")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    # Обрабатываем любые текстовые сообщения во всех чатах
    dp.message.register(handle_message, F.text)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
