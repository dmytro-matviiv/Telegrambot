import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from telegram import Bot
from telegram.error import TelegramError
from config import (
    BOT_TOKEN, CHANNEL_ID, VIEWS_BOOST_ENABLED, VIEWS_BOOST_INTERVAL,
    VIEWS_BOOST_MIN_VIEWS, VIEWS_BOOST_MAX_VIEWS, VIEWS_BOOST_MAX_POST_AGE,
    VIEWS_BOOST_MAX_CURRENT_VIEWS
)

logger = logging.getLogger(__name__)

class ViewsBooster:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.channel_id = CHANNEL_ID
        self.boosted_posts = set()  # Зберігаємо ID постів, які вже накрутили
        self.boost_interval = VIEWS_BOOST_INTERVAL
        self.max_views_per_boost = VIEWS_BOOST_MAX_VIEWS
        self.min_views_per_boost = VIEWS_BOOST_MIN_VIEWS
        self.max_post_age_hours = VIEWS_BOOST_MAX_POST_AGE
        self.max_current_views = VIEWS_BOOST_MAX_CURRENT_VIEWS
        
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
                        'has_video': bool(message.video)
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
    
    async def boost_post_views(self, post: Dict) -> bool:
        """Накручує перегляди для конкретного поста"""
        try:
            message_id = post['message_id']
            current_views = post.get('views', 0)
            
            # Визначаємо кількість переглядів для накручування
            boost_amount = random.randint(self.min_views_per_boost, self.max_views_per_boost)
            
            # Симулюємо накручування переглядів
            # В реальності тут буде логіка з використанням проксі, різних IP тощо
            await self._simulate_views_boost(message_id, boost_amount)
            
            # Позначаємо пост як оброблений
            self.boosted_posts.add(message_id)
            
            logger.info(f"📈 Накручено {boost_amount} переглядів для поста {message_id} (було: {current_views})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Помилка при накручуванні переглядів: {e}")
            return False
    
    async def _simulate_views_boost(self, message_id: int, amount: int):
        """Симулює накручування переглядів (заглушка)"""
        # В реальній реалізації тут буде:
        # 1. Використання проксі серверів
        # 2. Різні User-Agent
        # 3. Різні IP адреси
        # 4. Затримки між запитами
        
        logger.info(f"🔄 Симуляція накручування {amount} переглядів для поста {message_id}")
        
        # Симулюємо затримку
        await asyncio.sleep(random.uniform(1, 3))
        
        # В реальності тут буде HTTP запит до Telegram API
        # або використання сторонніх сервісів для накручування
        
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
                        
                        # Затримка між накручуваннями
                        await asyncio.sleep(random.uniform(2, 5))
            
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
        logger.info(f"🚀 Запущено моніторинг накручування переглядів (інтервал: {interval} сек)")
        
        while True:
            try:
                logger.info("🔍 Перевіряємо пости для накручування...")
                
                boosted = await self.boost_recent_posts()
                
                if boosted > 0:
                    logger.info(f"📈 Накручено перегляди для {boosted} постів")
                else:
                    logger.info("📊 Немає постів для накручування")
                
                # Чекаємо перед наступною перевіркою
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"❌ Помилка в моніторингу накручування: {e}")
                await asyncio.sleep(60)  # Чекаємо 1 хвилину при помилці
    
    def get_stats(self) -> Dict:
        """Повертає статистику накручування"""
        return {
            'boosted_posts_count': len(self.boosted_posts),
            'boost_interval': self.boost_interval,
            'max_views_per_boost': self.max_views_per_boost,
            'min_views_per_boost': self.min_views_per_boost
        }
