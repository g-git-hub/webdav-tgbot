import logging
import os
import random
import string
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update, Message
from telegram.error import TelegramError
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from webdav3.client import Client
from webdav3.exceptions import WebDavException

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

options = {
    'webdav_hostname': os.environ['WEBDAV_HOSTNAME'],
    'webdav_login': os.environ['WEBDAV_LOGIN'],
    'webdav_password': os.environ['WEBDAV_PASSWORD']
}
webdav_client = Client(options)

CACHE_DIR = Path("./cache")

CACHE_DIR.mkdir(exist_ok=True)

USER_ID = int(os.environ['USER_ID'])


def generate_temp_path():
    random_path = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(16))
    return Path(CACHE_DIR, random_path)


def generate_short_id():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


def get_file(message: Message):
    try:
        return message.photo[-1].file_id or message.document
    except IndexError:
        return message.document


async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Forbidden")
        return
    try:
        file = await context.bot.get_file(get_file(update.message))
    except TelegramError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Couldn't find a file")
        return
    temp_file_path = await file.download_to_drive(generate_temp_path())
    try:
        _, file_ext = os.path.splitext(file.file_path)
        message = (update.message.text or update.message.caption or '').replace(' ', '_')
        file_id = generate_short_id()
        filename = '-'.join(filter(len, [message, str(date.today()), file_id]))
        webdav_client.upload_file(
            f'{os.environ["WEBDAV_UPLOAD_DIR"]}/{filename}{file_ext}', temp_file_path
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=file_id)
    except WebDavException as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Upload failed: " + str(e))
    finally:
        temp_file_path.unlink(missing_ok=True)


if __name__ == '__main__':
    application = ApplicationBuilder().token(os.environ['TELEGRAM_TOKEN']).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    upload_handler = MessageHandler(filters.ATTACHMENT & filters.USER, upload)
    application.add_handler(upload_handler)

    application.run_polling()
