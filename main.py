import asyncio
import logging
import os
from config import BOT_TOKEN, CHANNEL_ID
from news_collector import NewsCollector
from telegram_publisher import TelegramPublisher
from air_alerts_monitor import AirAlertsMonitor
from memorial_messages import MemorialMessageScheduler
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
        self.news_collector = NewsCollector(self.publisher)
        self.alerts_monitor = AirAlertsMonitor(self.publisher)
        self.memorial_scheduler = MemorialMessageScheduler(self.publisher)

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
                self.news_collector.start(),
                self.alerts_monitor.monitor(),
                self.memorial_scheduler.start()
            )
            
        except Exception as e:
            logging.error(f"❌ Помилка запуску бота: {e}")
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