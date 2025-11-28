import logging
import os
import random
from pathlib import Path
from typing import List, Set

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
IGNORED_USERS_FILE = DATA_DIR / "ignored_users.txt"
SPECIAL_USERS_FILE = DATA_DIR / "special_users.txt"
SPECIAL_PHRASES_FILE = DATA_DIR / "special_phrases.txt"
FALLBACK_SPECIAL_PHRASES = ["окак-патруль подлетает"]
TRIGGER = "окак"
RESPONSE_CHANCE = 0.15


def _read_list(path: Path) -> List[str]:
    if not path.exists():
        return []
    return [
        line.strip().lstrip("@")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def load_ignored_users() -> Set[str]:
    return set(_read_list(IGNORED_USERS_FILE))


def load_special_users() -> Set[str]:
    return set(_read_list(SPECIAL_USERS_FILE))


def load_special_phrases() -> List[str]:
    phrases = _read_list(SPECIAL_PHRASES_FILE)
    return phrases or FALLBACK_SPECIAL_PHRASES


def normalize_username(update: Update) -> str:
    user = update.effective_user
    if not user:
        return ""
    if user.username:
        return user.username.lower()
    return str(user.id)


def message_contains_trigger(update: Update) -> bool:
    text = (update.message.text or "").casefold()
    return TRIGGER in text


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not message_contains_trigger(update):
        return

    username = normalize_username(update)
    ignored_users = load_ignored_users()
    if username in ignored_users:
        logging.debug("Skip reply: %s in ignored list", username)
        return

    special_users = load_special_users()
    special_phrases = load_special_phrases()
    if username in special_users:
        phrase = random.choice(special_phrases)
    else:
        if random.random() >= RESPONSE_CHANCE:
            logging.debug("Skip reply: chance miss for user %s", username)
            return
        phrase = TRIGGER

    await update.message.reply_text(phrase)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN environment variable.")

    application = ApplicationBuilder().token(token).build()
    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    )
    logging.info("Bot started")
    application.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
