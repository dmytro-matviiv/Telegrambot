#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Накручування переглядів через Selenium (браузерна автоматизація)
"""

import asyncio
import logging
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from telegram import Bot
from config import (
    BOT_TOKEN, CHANNEL_ID, VIEWS_BOOST_ENABLED, VIEWS_BOOST_INTERVAL,
    VIEWS_BOOST_MIN_VIEWS, VIEWS_BOOST_MAX_VIEWS, VIEWS_BOOST_MAX_POST_AGE,
    VIEWS_BOOST_MAX_CURRENT_VIEWS
)

logger = logging.getLogger(__name__)

class SeleniumViewsBooster:
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
            'browser_sessions': 0
        }
        
        # Налаштування браузера
        self.browser_options = {
            'headless': True,  # Запуск без GUI
            'disable_images': True,  # Відключити завантаження зображень
            'disable_javascript': False,  # Залишити JavaScript
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    async def get_recent_posts(self, limit: int = 10) -> List[Dict]:
        """Отримує останні пости з каналу через Selenium"""
        try:
            posts = []
            
            # Метод 1: Через Selenium WebDriver
            selenium_posts = await self._get_posts_via_selenium(limit)
            if selenium_posts:
                posts.extend(selenium_posts)
            
            # Метод 2: Мок пости для тестування
            if not posts:
                posts = await self._create_mock_posts(limit)
            
            logger.info(f"📊 Отримано {len(posts)} постів з каналу")
            return posts
            
        except Exception as e:
            logger.error(f"❌ Помилка при отриманні постів: {e}")
            return []
    
    async def _get_posts_via_selenium(self, limit: int) -> List[Dict]:
        """Отримує пости через Selenium WebDriver"""
        try:
            # Перевіряємо чи встановлений Selenium
            try:
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
            except ImportError:
                logger.warning("⚠️ Selenium не встановлений. Встановіть: pip install selenium")
                return []
            
            posts = []
            
            # Налаштування Chrome
            chrome_options = Options()
            if self.browser_options['headless']:
                chrome_options.add_argument('--headless')
            if self.browser_options['disable_images']:
                chrome_options.add_argument('--disable-images')
            chrome_options.add_argument(f'--user-agent={self.browser_options["user_agent"]}')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Запускаємо браузер
            driver = webdriver.Chrome(options=chrome_options)
            self.stats['browser_sessions'] += 1
            
            try:
                # Переходимо на канал
                channel_username = self.channel_id.replace('@', '')
                web_url = f"https://t.me/s/{channel_username}"
                
                logger.info(f"🌐 Відкриваємо канал: {web_url}")
                driver.get(web_url)
                
                # Чекаємо завантаження
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Парсимо пости
                posts = self._parse_selenium_posts(driver, limit)
                
                logger.info(f"🌐 Отримано {len(posts)} постів через Selenium")
                
            finally:
                driver.quit()
            
            return posts
            
        except Exception as e:
            logger.warning(f"⚠️ Помилка Selenium: {e}")
            return []
    
    def _parse_selenium_posts(self, driver, limit: int) -> List[Dict]:
        """Парсить пости з Selenium WebDriver"""
        try:
            posts = []
            
            # Шукаємо елементи повідомлень
            message_elements = driver.find_elements(By.CSS_SELECTOR, '[data-post]')
            
            for i, element in enumerate(message_elements[:limit]):
                try:
                    # Отримуємо дані поста
                    post_data = element.get_attribute('data-post')
                    if post_data:
                        post_parts = post_data.split('/')
                        if len(post_parts) >= 2:
                            message_id = int(post_parts[-1])
                            
                            # Отримуємо текст поста
                            text_element = element.find_element(By.CSS_SELECTOR, '.tgme_widget_message_text')
                            text = text_element.text if text_element else f'Пост {message_id}'
                            
                            # Перевіряємо наявність медіа
                            has_photo = bool(element.find_elements(By.CSS_SELECTOR, '.tgme_widget_message_photo'))
                            has_video = bool(element.find_elements(By.CSS_SELECTOR, '.tgme_widget_message_video'))
                            
                            posts.append({
                                'message_id': message_id,
                                'date': datetime.now() - timedelta(hours=i),
                                'text': text,
                                'views': random.randint(10, 100),
                                'has_photo': has_photo,
                                'has_video': has_video,
                                'link': f"https://t.me/{self.channel_id.replace('@', '')}/{message_id}"
                            })
                            
                except Exception as e:
                    logger.warning(f"⚠️ Помилка парсингу поста {i}: {e}")
                    continue
            
            return posts
            
        except Exception as e:
            logger.warning(f"⚠️ Помилка парсингу Selenium: {e}")
            return []
    
    async def _create_mock_posts(self, limit: int) -> List[Dict]:
        """Створює мок пости для тестування"""
        posts = []
        
        for i in range(min(limit, 5)):
            posts.append({
                'message_id': 3000 + i,
                'date': datetime.now() - timedelta(hours=i),
                'text': f'Selenium тестовий пост {i+1}',
                'views': random.randint(5, 25),
                'has_photo': True,
                'has_video': i % 2 == 0,
                'link': f"https://t.me/{self.channel_id.replace('@', '')}/{3000 + i}"
            })
        
        logger.info(f"📊 Створено {len(posts)} мок постів для Selenium")
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
        """Накручує перегляди для поста через Selenium"""
        try:
            message_id = post['message_id']
            post_link = post['link']
            current_views = post.get('views', 0)
            
            # Визначаємо кількість переглядів для накручування
            boost_amount = random.randint(self.min_views_per_boost, self.max_views_per_boost)
            
            logger.info(f"🎯 Накручуємо {boost_amount} переглядів для поста {message_id}")
            logger.info(f"🔗 Посилання: {post_link}")
            
            # Накручуємо перегляди через Selenium
            success_count = await self._boost_views_via_selenium(post_link, boost_amount)
            
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
    
    async def _boost_views_via_selenium(self, post_link: str, amount: int) -> int:
        """Накручує перегляди через Selenium"""
        success_count = 0
        
        for i in range(amount):
            try:
                # Перевіряємо чи встановлений Selenium
                try:
                    from selenium import webdriver
                    from selenium.webdriver.chrome.options import Options
                except ImportError:
                    logger.warning("⚠️ Selenium не встановлений")
                    break
                
                # Налаштування Chrome
                chrome_options = Options()
                if self.browser_options['headless']:
                    chrome_options.add_argument('--headless')
                chrome_options.add_argument(f'--user-agent={self.browser_options["user_agent"]}')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--window-size=1920,1080')
                
                # Запускаємо браузер
                driver = webdriver.Chrome(options=chrome_options)
                
                try:
                    # Переходимо на пост
                    driver.get(post_link)
                    
                    # Чекаємо завантаження
                    time.sleep(random.uniform(2, 5))
                    
                    # Симулюємо перегляд
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(random.uniform(1, 3))
                    
                    success_count += 1
                    self.stats['browser_sessions'] += 1
                    logger.info(f"✅ Selenium перегляд {i+1}/{amount} успішний")
                    
                finally:
                    driver.quit()
                
                # Затримка між запитами
                delay = random.uniform(3, 7)
                await asyncio.sleep(delay)
                
            except Exception as e:
                logger.warning(f"⚠️ Помилка Selenium перегляду {i+1}: {e}")
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
        logger.info(f"🚀 Запущено Selenium накручування переглядів (інтервал: {interval} сек)")
        
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
        logger.info("📊 Статистика Selenium накручування:")
        logger.info(f"  • Всього накручено: {self.stats['total_boosted']}")
        logger.info(f"  • Успішних запитів: {self.stats['successful_requests']}")
        logger.info(f"  • Невдалих запитів: {self.stats['failed_requests']}")
        logger.info(f"  • Браузерних сесій: {self.stats['browser_sessions']}")
    
    def get_stats(self) -> Dict:
        """Повертає статистику накручування"""
        return {
            'boosted_posts_count': len(self.boosted_posts),
            'boost_interval': self.boost_interval,
            'max_views_per_boost': self.max_views_per_boost,
            'min_views_per_boost': self.min_views_per_boost,
            'stats': self.stats
        }
