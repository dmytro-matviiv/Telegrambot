#!/usr/bin/env python3
import asyncio
import logging
import os
from telegram import Bot

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SOURCE_CHAT = '@rivne_1283'
MESSAGE_ID = 51442

async def main():
    bot_token = os.getenv('BOT_TOKEN')
    channel_id = os.getenv('CHANNEL_ID', '@newstime20')
    if not bot_token:
        logger.error('BOT_TOKEN not set')
        return
    bot = Bot(token=bot_token)
    try:
        me = await bot.get_me()
        logger.info(f"Bot: @{me.username}")
        logger.info(f"Copying {SOURCE_CHAT}/{MESSAGE_ID} -> {channel_id}")
        msg = await bot.copy_message(chat_id=channel_id, from_chat_id=SOURCE_CHAT, message_id=MESSAGE_ID)
        logger.info(f"✅ Copied message_id={msg.message_id}")
    except Exception as e:
        logger.error(f"❌ Copy failed: {e}")

if __name__ == '__main__':
    asyncio.run(main())


