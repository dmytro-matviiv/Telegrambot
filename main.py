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

class NewsBot:
    def __init__(self):
        self.publisher = TelegramPublisher()
        self.news_collector = NewsCollector()  # Не передаємо publisher
        self.alerts_monitor = AirAlertsMonitor(self.publisher)
        self.memorial_scheduler = MemorialMessageScheduler(self.publisher)
        self.content_scheduler = ContentScheduler(self.publisher, self.news_collector)
        self.group_scheduler = GroupEngagementScheduler(self.publisher.bot)

    async def start(self):
        """Запускає бота"""
        try:
            # Запускаємо health check сервер
            health_server = start_health_server()
            
            if not health_server:
                logging.warning("⚠️ Health check сервер не запущено")
            
            logging.info("🚀 Запускаємо бота...")
            
            # Запускаємо всі компоненти
            await asyncio.gather(
                self.run_news_collector(),
                self.alerts_monitor.monitor(),
                self.memorial_scheduler.monitor_memorial_schedule(),
                self.content_scheduler.monitor_schedule(),
                self.group_scheduler.monitor()
            )
            
        except Exception as e:
            logging.error(f"❌ Помилка запуску бота: {e}")
            raise
        finally:
            # Закриваємо aiohttp сесію
            if hasattr(self.publisher, 'session') and self.publisher.session:
                await self.publisher.session.close()
                logging.info("🔒 aiohttp сесію закрито")

    async def run_news_collector(self):
        """Запускає збір новин"""
        try:
            while True:
                # Збираємо новини
                all_news = self.news_collector.collect_all_news()
                
                if all_news:
                    logging.info(f"📰 Знайдено {len(all_news)} нових новин")
                    
                    # Публікуємо новини через publisher
                    for news in all_news[:1]:  # Публікуємо по одній новині
                        try:
                            await self.publisher.publish_news(news)
                            # Позначаємо як опубліковану
                            news_id = f"{news['source_key']}_{news['id']}"
                            self.news_collector.mark_as_published(news_id, news['source_key'])
                            logging.info(f"✅ Опубліковано новину: {news['title'][:50]}...")
                        except Exception as e:
                            logging.error(f"❌ Помилка публікації новини: {e}")
                else:
                    logging.info("📭 Нові новини не знайдено")
                
                # Чекаємо перед наступною перевіркою
                await asyncio.sleep(3500)  # 58 хвилин
                
        except Exception as e:
            logging.error(f"❌ Помилка в зборі новин: {e}")
            raise

async def main():
    """Головна функція"""
    if not BOT_TOKEN:
        logging.error("❌ BOT_TOKEN не заданий!")
        return
    
    if not CHANNEL_ID:
        logging.error("❌ CHANNEL_ID не заданий!")
        return
    
    bot = NewsBot()
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Бот зупинено користувачем")
    except Exception as e:
        logging.error(f"❌ Критична помилка: {e}")