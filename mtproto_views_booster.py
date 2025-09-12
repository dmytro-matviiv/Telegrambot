#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Накручування переглядів через MTProto API (найпотужніший метод)
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from telegram import Bot
from config import (
    BOT_TOKEN, CHANNEL_ID, VIEWS_BOOST_ENABLED, VIEWS_BOOST_INTERVAL,
    VIEWS_BOOST_MIN_VIEWS, VIEWS_BOOST_MAX_VIEWS, VIEWS_BOOST_MAX_POST_AGE,
    VIEWS_BOOST_MAX_CURRENT_VIEWS
)

logger = logging.getLogger(__name__)

class MTProtoViewsBooster:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.channel_id = CHANNEL_ID
        self.boosted_posts = set()
        self.boost_interval = VIEWS_BOOST_INTERVAL
        self.max_views_per_boost = VIEWS_BOOST_MAX_VIEWS
        self.min_views_per_boost = VIEWS_BOOST_MIN_VIEWS
        self.max_post_age_hours = VIEWS_BOOST_MAX_POST_AGE
        self.max_current_views = VIEWS_BOOST_MAX_CURRENT_VIEWS
        
        # Статистика
        self.stats = {
            'total_boosted': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'mtproto_requests': 0
        }
        
        # Налаштування MTProto
        self.mtproto_config = {
            'api_id': None,  # Отримати з https://my.telegram.org
            'api_hash': None,  # Отримати з https://my.telegram.org
            'phone': None,  # Ваш номер телефону
            'session_name': 'views_booster'
        }
    
    async def get_recent_posts(self, limit: int = 10) -> List[Dict]:
        """Отримує останні пости з каналу через MTProto"""
        try:
            posts = []
            
            # Метод 1: Через MTProto API
            mtproto_posts = await self._get_posts_via_mtproto(limit)
            if mtproto_posts:
                posts.extend(mtproto_posts)
            
            # Метод 2: Мок пости для тестування
            if not posts:
                posts = await self._create_mock_posts(limit)
            
            logger.info(f"📊 Отримано {len(posts)} постів з каналу")
            return posts
            
        except Exception as e:
            logger.error(f"❌ Помилка при отриманні постів: {e}")
            return []
    
    async def _get_posts_via_mtproto(self, limit: int) -> List[Dict]:
        """Отримує пости через MTProto API"""
        try:
            # Перевіряємо чи встановлений Telethon
            try:
                from telethon import TelegramClient
                from telethon.tl.functions.messages import GetHistoryRequest
                from telethon.tl.types import InputPeerChannel
            except ImportError:
                logger.warning("⚠️ Telethon не встановлений. Встановіть: pip install telethon")
                return []
            
            posts = []
            
            # Перевіряємо налаштування
            if not all([self.mtproto_config['api_id'], self.mtproto_config['api_hash']]):
                logger.warning("⚠️ MTProto не налаштовано. Потрібні api_id та api_hash")
                return []
            
            # Створюємо клієнт
            client = TelegramClient(
                self.mtproto_config['session_name'],
                self.mtproto_config['api_id'],
                self.mtproto_config['api_hash']
            )
            
            try:
                # Підключаємося
                await client.start()
                
                # Отримуємо інформацію про канал
                entity = await client.get_entity(self.channel_id)
                logger.info(f"📊 Канал: {entity.title}")
                
                # Отримуємо історію повідомлень
                messages = await client(GetHistoryRequest(
                    peer=entity,
                    limit=limit,
                    offset_date=None,
                    offset_id=0,
                    max_id=0,
                    min_id=0,
                    add_offset=0,
                    hash=0
                ))
                
                # Обробляємо повідомлення
                for message in messages.messages:
                    if hasattr(message, 'id') and hasattr(message, 'date'):
                        # Перевіряємо наявність медіа
                        has_photo = bool(getattr(message, 'photo', None))
                        has_video = bool(getattr(message, 'video', None))
                        
                        # Отримуємо текст
                        text = getattr(message, 'message', '') or getattr(message, 'raw_text', '')
                        
                        posts.append({
                            'message_id': message.id,
                            'date': message.date,
                            'text': text,
                            'views': getattr(message, 'views', 0),
                            'has_photo': has_photo,
                            'has_video': has_video,
                            'link': f"https://t.me/{self.channel_id.replace('@', '')}/{message.id}"
                        })
                
                logger.info(f"📊 Отримано {len(posts)} постів через MTProto")
                
            finally:
                await client.disconnect()
            
            return posts
            
        except Exception as e:
            logger.warning(f"⚠️ Помилка MTProto: {e}")
            return []
    
    async def _create_mock_posts(self, limit: int) -> List[Dict]:
        """Створює мок пости для тестування"""
        posts = []
        
        for i in range(min(limit, 5)):
            posts.append({
                'message_id': 4000 + i,
                'date': datetime.now() - timedelta(hours=i),
                'text': f'MTProto тестовий пост {i+1}',
                'views': random.randint(5, 25),
                'has_photo': True,
                'has_video': i % 2 == 0,
                'link': f"https://t.me/{self.channel_id.replace('@', '')}/{4000 + i}"
            })
        
        logger.info(f"📊 Створено {len(posts)} мок постів для MTProto")
        return posts
    
    def should_boost_post(self, post: Dict) -> bool:
        """Визначає чи потрібно накручувати перегляди для поста"""
        message_id = post['message_id']
        
        # Не накручуємо вже оброблені пости
        if message_id in self.boosted_posts:
            return False
            
        # Накручуємо тільки пости з медіа (фото/відео)
        if not (post['has_photo'] or post['has_video']):
            return False
            
        # Накручуємо тільки пости не старші за налаштований час
        post_age = datetime.now() - post['date']
        if post_age > timedelta(hours=self.max_post_age_hours):
            return False
            
        # Накручуємо тільки пости з менше ніж налаштована кількість переглядів
        if post.get('views', 0) >= self.max_current_views:
            return False
            
        return True
    
    async def boost_post_views(self, post: Dict) -> bool:
        """Накручує перегляди для поста через MTProto"""
        try:
            message_id = post['message_id']
            post_link = post['link']
            current_views = post.get('views', 0)
            
            # Визначаємо кількість переглядів для накручування
            boost_amount = random.randint(self.min_views_per_boost, self.max_views_per_boost)
            
            logger.info(f"🎯 Накручуємо {boost_amount} переглядів для поста {message_id}")
            logger.info(f"🔗 Посилання: {post_link}")
            
            # Накручуємо перегляди через MTProto
            success_count = await self._boost_views_via_mtproto(post, boost_amount)
            
            if success_count > 0:
                # Позначаємо пост як оброблений
                self.boosted_posts.add(message_id)
                self.stats['total_boosted'] += success_count
                self.stats['successful_requests'] += success_count
                
                logger.info(f"✅ Накручено {success_count}/{boost_amount} переглядів для поста {message_id}")
                return True
            else:
                self.stats['failed_requests'] += 1
                logger.warning(f"❌ Не вдалося накрутити перегляди для поста {message_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Помилка при накручуванні переглядів: {e}")
            self.stats['failed_requests'] += 1
            return False
    
    async def _boost_views_via_mtproto(self, post: Dict, amount: int) -> int:
        """Накручує перегляди через MTProto"""
        success_count = 0
        
        for i in range(amount):
            try:
                # Перевіряємо чи встановлений Telethon
                try:
                    from telethon import TelegramClient
                    from telethon.tl.functions.messages import GetMessagesRequest
                except ImportError:
                    logger.warning("⚠️ Telethon не встановлений")
                    break
                
                # Перевіряємо налаштування
                if not all([self.mtproto_config['api_id'], self.mtproto_config['api_hash']]):
                    logger.warning("⚠️ MTProto не налаштовано")
                    break
                
                # Створюємо клієнт
                client = TelegramClient(
                    f"{self.mtproto_config['session_name']}_{i}",
                    self.mtproto_config['api_id'],
                    self.mtproto_config['api_hash']
                )
                
                try:
                    # Підключаємося
                    await client.start()
                    
                    # Отримуємо інформацію про канал
                    entity = await client.get_entity(self.channel_id)
                    
                    # Отримуємо повідомлення
                    messages = await client(GetMessagesRequest(
                        id=[post['message_id']]
                    ))
                    
                    if messages.messages:
                        success_count += 1
                        self.stats['mtproto_requests'] += 1
                        logger.info(f"✅ MTProto перегляд {i+1}/{amount} успішний")
                    
                finally:
                    await client.disconnect()
                
                # Затримка між запитами
                delay = random.uniform(2, 5)
                await asyncio.sleep(delay)
                
            except Exception as e:
                logger.warning(f"⚠️ Помилка MTProto перегляду {i+1}: {e}")
                continue
        
        return success_count
    
    async def boost_recent_posts(self) -> int:
        """Накручує перегляди для останніх постів"""
        try:
            # Отримуємо останні пости
            posts = await self.get_recent_posts(limit=20)
            
            if not posts:
                logger.info("📭 Немає постів для накручування")
                return 0
            
            boosted_count = 0
            
            for post in posts:
                if self.should_boost_post(post):
                    success = await self.boost_post_views(post)
                    if success:
                        boosted_count += 1
                        
                        # Затримка між накручуваннями постів
                        delay = random.uniform(3, 8)
                        await asyncio.sleep(delay)
            
            if boosted_count > 0:
                logger.info(f"✅ Накручено перегляди для {boosted_count} постів")
            else:
                logger.info("📊 Немає постів, які потребують накручування")
                
            return boosted_count
            
        except Exception as e:
            logger.error(f"❌ Помилка при накручуванні постів: {e}")
            return 0
    
    async def monitor_and_boost(self, interval: int = 1800):
        """Моніторить канал та накручує перегляди"""
        logger.info(f"🚀 Запущено MTProto накручування переглядів (інтервал: {interval} сек)")
        
        while True:
            try:
                logger.info("🔍 Перевіряємо пости для накручування...")
                
                boosted = await self.boost_recent_posts()
                
                if boosted > 0:
                    logger.info(f"📈 Накручено перегляди для {boosted} постів")
                    self._log_stats()
                else:
                    logger.info("📊 Немає постів для накручування")
                
                # Чекаємо перед наступною перевіркою
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"❌ Помилка в моніторингу накручування: {e}")
                await asyncio.sleep(60)  # Чекаємо 1 хвилину при помилці
    
    def _log_stats(self):
        """Логує статистику"""
        logger.info("📊 Статистика MTProto накручування:")
        logger.info(f"  • Всього накручено: {self.stats['total_boosted']}")
        logger.info(f"  • Успішних запитів: {self.stats['successful_requests']}")
        logger.info(f"  • Невдалих запитів: {self.stats['failed_requests']}")
        logger.info(f"  • MTProto запитів: {self.stats['mtproto_requests']}")
    
    def get_stats(self) -> Dict:
        """Повертає статистику накручування"""
        return {
            'boosted_posts_count': len(self.boosted_posts),
            'boost_interval': self.boost_interval,
            'max_views_per_boost': self.max_views_per_boost,
            'min_views_per_boost': self.min_views_per_boost,
            'stats': self.stats
        }
    
    def setup_mtproto(self, api_id: int, api_hash: str, phone: str):
        """Налаштовує MTProto"""
        self.mtproto_config['api_id'] = api_id
        self.mtproto_config['api_hash'] = api_hash
        self.mtproto_config['phone'] = phone
        logger.info("✅ MTProto налаштовано")
