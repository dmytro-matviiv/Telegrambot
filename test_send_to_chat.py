#!/usr/bin/env python3
import asyncio
import os
import logging
from telegram import Bot

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CHAT = os.getenv('TEST_CHAT', '@GlobalNOChat')
TEXT = '🧪 Тестове повідомлення від бота: зв\'язок із групою встановлено.'

async def main():
    token = os.getenv('BOT_TOKEN')
    if not token:
        print('ERR: BOT_TOKEN not set')
        return
    bot = Bot(token=token)
    me = await bot.get_me()
    logging.info(f"Bot ready: @{me.username}")
    try:
        msg = await bot.send_message(chat_id=CHAT, text=TEXT, parse_mode='HTML', disable_web_page_preview=True)
        logging.info(f"Sent message_id={msg.message_id} to {CHAT}")
    except Exception as e:
        logging.error(f"Send failed: {e}")

if __name__ == '__main__':
    asyncio.run(main())


