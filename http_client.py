import asyncio
import aiohttp
import logging
import random
import json
from typing import Dict, Optional, List
from proxy_manager import ProxyManager

logger = logging.getLogger(__name__)

class HTTPClient:
    def __init__(self, proxy_manager: ProxyManager):
        self.proxy_manager = proxy_manager
        self.session = None
        self.user_agents = [
            # Chrome
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            
            # Firefox
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0',
            
            # Safari
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
            
            # Edge
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            
            # Mobile
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
        ]
        
        self.headers_templates = {
            'desktop': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,uk;q=0.8,ru;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            },
            'mobile': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,uk;q=0.8,ru;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            }
        }
    
    async def create_session(self, proxy: Optional[str] = None):
        """Створює нову HTTP сесію з проксі"""
        try:
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            
            timeout = aiohttp.ClientTimeout(
                total=30,
                connect=10,
                sock_read=10
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
            
            logger.info(f"Створено HTTP сесію з проксі: {proxy or 'без проксі'}")
            return True
            
        except Exception as e:
            logger.error(f"Помилка створення HTTP сесії: {e}")
            return False
    
    async def close_session(self):
        """Закриває HTTP сесію"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("HTTP сесію закрито")
    
    def get_random_headers(self, device_type: str = 'desktop') -> Dict[str, str]:
        """Генерує випадкові заголовки"""
        user_agent = random.choice(self.user_agents)
        headers = self.headers_templates.get(device_type, self.headers_templates['desktop']).copy()
        headers['User-Agent'] = user_agent
        
        # Додаємо випадкові заголовки
        if random.choice([True, False]):
            headers['X-Forwarded-For'] = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        
        if random.choice([True, False]):
            headers['X-Real-IP'] = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        
        return headers
    
    async def make_request(self, url: str, method: str = 'GET', 
                          headers: Optional[Dict] = None, 
                          data: Optional[Dict] = None,
                          proxy: Optional[str] = None,
                          retries: int = 3) -> Optional[aiohttp.ClientResponse]:
        """Робить HTTP запит з retry логікою"""
        
        if not self.session:
            await self.create_session(proxy)
        
        for attempt in range(retries):
            try:
                # Вибираємо проксі якщо не вказано
                current_proxy = proxy or self.proxy_manager.get_next_proxy()
                
                # Генеруємо заголовки якщо не вказано
                current_headers = headers or self.get_random_headers()
                
                logger.info(f"Запит {method} {url} (спроба {attempt + 1}/{retries})")
                if current_proxy:
                    logger.info(f"Використовуємо проксі: {current_proxy}")
                
                async with self.session.request(
                    method=method,
                    url=url,
                    headers=current_headers,
                    data=data,
                    proxy=current_proxy
                ) as response:
                    
                    if response.status == 200:
                        logger.info(f"✅ Успішний запит: {response.status}")
                        return response
                    else:
                        logger.warning(f"⚠️ Неочікуваний статус: {response.status}")
                        if attempt < retries - 1:
                            await asyncio.sleep(random.uniform(1, 3))
                            continue
                        return response
                        
            except asyncio.TimeoutError:
                logger.warning(f"⏰ Таймаут запиту (спроба {attempt + 1}/{retries})")
                if attempt < retries - 1:
                    await asyncio.sleep(random.uniform(2, 5))
                    continue
                    
            except aiohttp.ClientError as e:
                logger.warning(f"🌐 Помилка клієнта: {e} (спроба {attempt + 1}/{retries})")
                if attempt < retries - 1:
                    await asyncio.sleep(random.uniform(1, 3))
                    continue
                    
            except Exception as e:
                logger.error(f"❌ Неочікувана помилка: {e} (спроба {attempt + 1}/{retries})")
                if attempt < retries - 1:
                    await asyncio.sleep(random.uniform(2, 5))
                    continue
        
        logger.error(f"❌ Всі спроби вичерпано для {url}")
        return None
    
    async def get(self, url: str, **kwargs) -> Optional[aiohttp.ClientResponse]:
        """GET запит"""
        return await self.make_request(url, 'GET', **kwargs)
    
    async def post(self, url: str, **kwargs) -> Optional[aiohttp.ClientResponse]:
        """POST запит"""
        return await self.make_request(url, 'POST', **kwargs)
    
    async def __aenter__(self):
        await self.create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()
