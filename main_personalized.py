import asyncio
import logging
import os
from config import BOT_TOKEN, CHANNEL_ID
from news_collector import NewsCollector
from telegram_publisher import TelegramPublisher
from air_alerts_monitor import AirAlertsMonitor
from memorial_messages import MemorialMessageScheduler
from content_scheduler import ContentScheduler
from group_engagement_scheduler import GroupEngagementScheduler
from personalized_bot import PersonalizedBot
from user_manager import UserManager
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Простий HTTP сервер для health check
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Вимкнути логування HTTP запитів
        pass

def start_health_server():
    """Запускає HTTP сервер для health check"""
    try:
        # Знаходимо вільний порт
        port = int(os.getenv('PORT', 8000))
        
        # Створюємо сервер
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        
        logging.info(f"🚀 Health check сервер запущено на порту {port}")
        
        # Запускаємо сервер в окремому потоці
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        return server
    except Exception as e:
        logging.error(f"❌ Помилка запуску health check сервера: {e}")
        return None

class PersonalizedNewsBot:
    def __init__(self):
        self.publisher = TelegramPublisher()
        self.news_collector = NewsCollector()
        self.alerts_monitor = AirAlertsMonitor(self.publisher)
        self.memorial_scheduler = MemorialMessageScheduler(self.publisher)
        self.content_scheduler = ContentScheduler(self.publisher, self.news_collector)
        self.group_scheduler = GroupEngagementScheduler(self.publisher.bot)
        
        # Ініціалізуємо персоналізованого бота
        self.personalized_bot = PersonalizedBot(BOT_TOKEN)
        self.user_manager = UserManager()

    async def start(self):
        """Запускає бота"""
        try:
            # Запускаємо health check сервер
            health_server = start_health_server()
            
            if not health_server:
                logging.warning("⚠️ Health check сервер не запущено")
            
            logging.info("🚀 Запускаємо персоналізованого бота...")
            
            # Запускаємо всі компоненти
            await asyncio.gather(
                self.run_news_collector(),
                self.run_alerts_monitor(),
                self.run_memorial_scheduler(),
                self.run_content_scheduler(),
                self.run_personalized_bot()
            )
            
        except Exception as e:
            logging.error(f"❌ Помилка запуску бота: {e}")
            raise
        finally:
            # Закриваємо aiohttp сесію
            if hasattr(self.publisher, 'session') and self.publisher.session:
                await self.publisher.session.close()
                logging.info("🔒 aiohttp сесію закрито")

    async def run_personalized_bot(self):
        """Запускає персоналізованого бота"""
        try:
            await self.personalized_bot.start()
        except Exception as e:
            logging.error(f"❌ Помилка запуску персоналізованого бота: {e}")
            raise

    async def run_news_collector(self):
        """Запускає збір новин з персоналізацією"""
        try:
            while True:
                # Збираємо новини
                all_news = self.news_collector.collect_all_news()
                
                if all_news:
                    logging.info(f"📰 Знайдено {len(all_news)} нових новин")
                    
                    # Отримуємо всіх користувачів
                    all_users = self.user_manager.get_all_users()
                    
                    # Публікуємо новини через персоналізованого бота
                    for news in all_news[:1]:  # Публікуємо по одній новині
                        try:
                            # Надсилаємо новину користувачам
                            success_count, error_count = await self.personalized_bot.send_news_to_users(
                                news_item=news,
                                user_ids=all_users
                            )
                            
                            logging.info(f"✅ Опубліковано новину: {news['title'][:50]}... "
                                        f"(успішно: {success_count}, помилок: {error_count})")
                            
                            # Позначаємо як опубліковану
                            news_id = f"{news['source_key']}_{news['id']}"
                            self.news_collector.mark_as_published(news_id, news['source_key'])
                            
                        except Exception as e:
                            logging.error(f"❌ Помилка публікації новини: {e}")
                else:
                    logging.info("📭 Нові новини не знайдено")
                
                # Чекаємо перед наступною перевіркою
                await asyncio.sleep(3600)  # 1 година
                
        except Exception as e:
            logging.error(f"❌ Помилка в зборі новин: {e}")
            raise

    async def run_alerts_monitor(self):
        """Запускає моніторинг тривог з персоналізацією"""
        try:
            while True:
                # Отримуємо поточні тривоги
                current_alerts = await self.alerts_monitor.get_current_alerts()
                
                if current_alerts:
                    # Отримуємо всіх користувачів
                    all_users = self.user_manager.get_all_users()
                    
                    # Форматуємо повідомлення про тривоги
                    alert_message = self.format_alerts_message(current_alerts)
                    
                    # Надсилаємо тривоги користувачам
                    success_count, error_count = await self.personalized_bot.send_alert_to_users(
                        alert_message=alert_message,
                        user_ids=all_users
                    )
                    
                    logging.info(f"🚨 Надіслано тривоги користувачам "
                                f"(успішно: {success_count}, помилок: {error_count})")
                
                # Чекаємо перед наступною перевіркою
                await asyncio.sleep(60)  # 1 хвилина
                
        except Exception as e:
            logging.error(f"❌ Помилка в моніторингу тривог: {e}")
            raise

    async def run_memorial_scheduler(self):
        """Запускає меморіальний планувальник з персоналізацією"""
        try:
            while True:
                # Перевіряємо чи потрібно надіслати меморіальне повідомлення
                memorial_message = await self.memorial_scheduler.check_memorial_schedule()
                
                if memorial_message:
                    # Отримуємо всіх користувачів
                    all_users = self.user_manager.get_all_users()
                    
                    # Надсилаємо меморіальне повідомлення користувачам
                    success_count, error_count = await self.personalized_bot.send_memorial_to_users(
                        memorial_message=memorial_message,
                        user_ids=all_users
                    )
                    
                    logging.info(f"🕯️ Надіслано меморіальне повідомлення користувачам "
                                f"(успішно: {success_count}, помилок: {error_count})")
                
                # Чекаємо перед наступною перевіркою
                await asyncio.sleep(3600)  # 1 година
                
        except Exception as e:
            logging.error(f"❌ Помилка в меморіальному планувальнику: {e}")
            raise

    async def run_content_scheduler(self):
        """Запускає планувальник контенту"""
        try:
            while True:
                # Запускаємо планувальник контенту
                await self.content_scheduler.monitor_schedule()
                await asyncio.sleep(3600)  # 1 година
        except Exception as e:
            logging.error(f"❌ Помилка в планувальнику контенту: {e}")
            raise

    def format_alerts_message(self, alerts):
        """Форматує повідомлення про тривоги"""
        if not alerts:
            return ""
        
        message = "🚨 <b>ПОВІТРЯНА ТРИВОГА!</b>\n\n"
        
        if isinstance(alerts, list):
            for alert in alerts:
                if isinstance(alert, dict):
                    region = alert.get('region', 'Невідома область')
                    message += f"📍 {region}\n"
                else:
                    message += f"📍 {alert}\n"
        else:
            message += f"📍 {alerts}\n"
        
        message += "\n⚠️ Бережіть себе! Слідуйте інструкціям МНС."
        
        return message

async def main():
    """Головна функція"""
    if not BOT_TOKEN:
        logging.error("❌ BOT_TOKEN не заданий!")
        return
    
    bot = PersonalizedNewsBot()
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Бот зупинено користувачем")
    except Exception as e:
        logging.error(f"❌ Критична помилка: {e}")
