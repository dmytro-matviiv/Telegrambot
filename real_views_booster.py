import asyncio
import logging
import random
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from telegram import Bot
from telegram.error import TelegramError
from proxy_manager import ProxyManager
from http_client import HTTPClient
from config import (
    BOT_TOKEN, CHANNEL_ID, VIEWS_BOOST_ENABLED, VIEWS_BOOST_INTERVAL,
    VIEWS_BOOST_MIN_VIEWS, VIEWS_BOOST_MAX_VIEWS, VIEWS_BOOST_MAX_POST_AGE,
    VIEWS_BOOST_MAX_CURRENT_VIEWS
)

logger = logging.getLogger(__name__)

class RealViewsBooster:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.channel_id = CHANNEL_ID
        self.boosted_posts = set()
        self.boost_interval = VIEWS_BOOST_INTERVAL
        self.max_views_per_boost = VIEWS_BOOST_MAX_VIEWS
        self.min_views_per_boost = VIEWS_BOOST_MIN_VIEWS
        self.max_post_age_hours = VIEWS_BOOST_MAX_POST_AGE
        self.max_current_views = VIEWS_BOOST_MAX_CURRENT_VIEWS
        
        # Ініціалізуємо менеджери
        self.proxy_manager = ProxyManager()
        self.http_client = HTTPClient(self.proxy_manager)
        
        # Telegram Web URLs
        self.telegram_web_urls = [
            'https://web.telegram.org/k/',
            'https://web.telegram.org/a/',
            'https://web.telegram.org/z/'
        ]
        
        # Статистика
        self.stats = {
            'total_boosted': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'proxy_rotations': 0
        }
    
    async def initialize(self):
        """Ініціалізує накручувач"""
        try:
            logger.info("🚀 Ініціалізація реального накручування переглядів...")
            
            # Завантажуємо проксі
            self.proxy_manager.load_proxies_from_file("proxies.txt")
            self.proxy_manager.load_working_proxies("working_proxies.txt")
            
            # Якщо немає робочих проксі, тестуємо всі
            if not self.proxy_manager.working_proxies:
                logger.info("🔍 Тестуємо проксі сервери...")
                await self.proxy_manager.test_all_proxies()
                self.proxy_manager.save_working_proxies()
            
            # Створюємо HTTP клієнт
            await self.http_client.create_session()
            
            stats = self.proxy_manager.get_stats()
            logger.info(f"📊 Проксі статистика: {stats['working_proxies']}/{stats['total_proxies']} робочих")
            
            if stats['working_proxies'] == 0:
                logger.warning("⚠️ Немає робочих проксі! Накручування може не працювати.")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Помилка ініціалізації: {e}")
            return False
    
    async def get_recent_posts(self, limit: int = 10) -> List[Dict]:
        """Отримує останні пости з каналу"""
        try:
            posts = []
            async for message in self.bot.iter_history(chat_id=self.channel_id, limit=limit):
                if message.message_id and not message.forward_from:
                    posts.append({
                        'message_id': message.message_id,
                        'date': message.date,
                        'text': message.text or message.caption or '',
                        'views': getattr(message, 'views', 0),
                        'has_photo': bool(message.photo),
                        'has_video': bool(message.video),
                        'link': f"https://t.me/{self.channel_id.replace('@', '')}/{message.message_id}"
                    })
            
            logger.info(f"📊 Отримано {len(posts)} постів з каналу")
            return posts
            
        except Exception as e:
            logger.error(f"❌ Помилка при отриманні постів: {e}")
            return []
    
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
    
    async def boost_post_views_real(self, post: Dict) -> bool:
        """Реально накручує перегляди для поста"""
        try:
            message_id = post['message_id']
            post_link = post['link']
            current_views = post.get('views', 0)
            
            # Визначаємо кількість переглядів для накручування
            boost_amount = random.randint(self.min_views_per_boost, self.max_views_per_boost)
            
            logger.info(f"🎯 Накручуємо {boost_amount} переглядів для поста {message_id}")
            logger.info(f"🔗 Посилання: {post_link}")
            
            # Накручуємо перегляди
            success_count = await self._boost_views_for_post(post_link, boost_amount)
            
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
    
    async def _boost_views_for_post(self, post_link: str, amount: int) -> int:
        """Накручує перегляди для конкретного поста"""
        success_count = 0
        
        for i in range(amount):
            try:
                # Вибираємо випадковий Telegram Web URL
                web_url = random.choice(self.telegram_web_urls)
                
                # Формуємо URL для перегляду поста
                view_url = f"{web_url}#{post_link}"
                
                # Робимо запит
                response = await self.http_client.get(view_url)
                
                if response and response.status == 200:
                    success_count += 1
                    logger.info(f"✅ Перегляд {i+1}/{amount} успішний")
                else:
                    logger.warning(f"⚠️ Перегляд {i+1}/{amount} невдалий")
                
                # Затримка між запитами
                delay = random.uniform(2, 5)
                await asyncio.sleep(delay)
                
                # Періодично змінюємо проксі
                if i % 10 == 0 and i > 0:
                    await self._rotate_proxy()
                
            except Exception as e:
                logger.warning(f"⚠️ Помилка перегляду {i+1}: {e}")
                continue
        
        return success_count
    
    async def _rotate_proxy(self):
        """Змінює проксі сервер"""
        try:
            old_proxy = self.http_client.session._connector._proxy
            new_proxy = self.proxy_manager.get_next_proxy()
            
            if new_proxy and new_proxy != old_proxy:
                await self.http_client.close_session()
                await self.http_client.create_session(new_proxy)
                self.stats['proxy_rotations'] += 1
                logger.info(f"🔄 Змінено проксі: {new_proxy}")
        except Exception as e:
            logger.warning(f"⚠️ Помилка зміни проксі: {e}")
    
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
                    success = await self.boost_post_views_real(post)
                    if success:
                        boosted_count += 1
                        
                        # Затримка між накручуваннями постів
                        delay = random.uniform(5, 10)
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
        logger.info(f"🚀 Запущено реальне накручування переглядів (інтервал: {interval} сек)")
        
        # Ініціалізуємо
        if not await self.initialize():
            logger.error("❌ Не вдалося ініціалізувати накручувач")
            return
        
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
        logger.info("📊 Статистика накручування:")
        logger.info(f"  • Всього накручено: {self.stats['total_boosted']}")
        logger.info(f"  • Успішних запитів: {self.stats['successful_requests']}")
        logger.info(f"  • Невдалих запитів: {self.stats['failed_requests']}")
        logger.info(f"  • Змін проксі: {self.stats['proxy_rotations']}")
        
        proxy_stats = self.proxy_manager.get_stats()
        logger.info(f"  • Робочих проксі: {proxy_stats['working_proxies']}/{proxy_stats['total_proxies']}")
    
    def get_stats(self) -> Dict:
        """Повертає статистику накручування"""
        return {
            'boosted_posts_count': len(self.boosted_posts),
            'boost_interval': self.boost_interval,
            'max_views_per_boost': self.max_views_per_boost,
            'min_views_per_boost': self.min_views_per_boost,
            'stats': self.stats,
            'proxy_stats': self.proxy_manager.get_stats()
        }
    
    async def cleanup(self):
        """Очищає ресурси"""
        await self.http_client.close_session()
        logger.info("🧹 Ресурси очищено")
