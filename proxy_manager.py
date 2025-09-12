иimport asyncio
import aiohttp
import logging
import random
from typing import List, Dict, Optional
import json
import os

logger = logging.getLogger(__name__)

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.working_proxies = []
        self.failed_proxies = set()
        self.current_proxy_index = 0
        
    def load_proxies_from_file(self, file_path: str = "proxies.txt"):
        """Завантажує проксі з файлу"""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Файл проксі {file_path} не знайдено")
                return
                
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Підтримуємо формати: ip:port, ip:port:user:pass, http://ip:port
                    if '://' in line:
                        self.proxies.append(line)
                    else:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            if len(parts) == 2:
                                # ip:port
                                self.proxies.append(f"http://{parts[0]}:{parts[1]}")
                            elif len(parts) == 4:
                                # ip:port:user:pass
                                self.proxies.append(f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}")
                            
            logger.info(f"Завантажено {len(self.proxies)} проксі з файлу")
            
        except Exception as e:
            logger.error(f"Помилка завантаження проксі: {e}")
    
    def add_proxy(self, proxy: str):
        """Додає проксі вручну"""
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            logger.info(f"Додано проксі: {proxy}")
    
    def get_random_proxy(self) -> Optional[str]:
        """Повертає випадковий робочий проксі"""
        if not self.working_proxies:
            return None
        return random.choice(self.working_proxies)
    
    def get_next_proxy(self) -> Optional[str]:
        """Повертає наступний проксі по черзі"""
        if not self.working_proxies:
            return None
            
        proxy = self.working_proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.working_proxies)
        return proxy
    
    async def test_proxy(self, proxy: str) -> bool:
        """Тестує проксі на працездатність"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            connector = aiohttp.TCPConnector(limit=1)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                async with session.get(
                    'http://httpbin.org/ip',
                    proxy=proxy
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Проксі {proxy} працює, IP: {data.get('origin', 'unknown')}")
                        return True
                    else:
                        logger.warning(f"❌ Проксі {proxy} повернув статус {response.status}")
                        return False
                        
        except Exception as e:
            logger.warning(f"❌ Проксі {proxy} не працює: {e}")
            return False
    
    async def test_all_proxies(self):
        """Тестує всі проксі та зберігає робочі"""
        if not self.proxies:
            logger.warning("Немає проксі для тестування")
            return
            
        logger.info(f"Тестуємо {len(self.proxies)} проксі...")
        
        tasks = []
        for proxy in self.proxies:
            if proxy not in self.failed_proxies:
                tasks.append(self._test_single_proxy(proxy))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        working_count = sum(1 for result in results if result is True)
        logger.info(f"Знайдено {working_count} робочих проксі з {len(tasks)}")
    
    async def _test_single_proxy(self, proxy: str) -> bool:
        """Тестує один проксі"""
        try:
            is_working = await self.test_proxy(proxy)
            if is_working:
                if proxy not in self.working_proxies:
                    self.working_proxies.append(proxy)
            else:
                self.failed_proxies.add(proxy)
            return is_working
        except Exception as e:
            logger.error(f"Помилка тестування проксі {proxy}: {e}")
            self.failed_proxies.add(proxy)
            return False
    
    def get_stats(self) -> Dict:
        """Повертає статистику проксі"""
        return {
            'total_proxies': len(self.proxies),
            'working_proxies': len(self.working_proxies),
            'failed_proxies': len(self.failed_proxies),
            'success_rate': len(self.working_proxies) / len(self.proxies) * 100 if self.proxies else 0
        }
    
    def save_working_proxies(self, file_path: str = "working_proxies.txt"):
        """Зберігає робочі проксі в файл"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for proxy in self.working_proxies:
                    f.write(f"{proxy}\n")
            logger.info(f"Збережено {len(self.working_proxies)} робочих проксі в {file_path}")
        except Exception as e:
            logger.error(f"Помилка збереження проксі: {e}")
    
    def load_working_proxies(self, file_path: str = "working_proxies.txt"):
        """Завантажує робочі проксі з файлу"""
        try:
            if not os.path.exists(file_path):
                return
                
            with open(file_path, 'r', encoding='utf-8') as f:
                self.working_proxies = [line.strip() for line in f.readlines() if line.strip()]
            
            logger.info(f"Завантажено {len(self.working_proxies)} робочих проксі")
        except Exception as e:
            logger.error(f"Помилка завантаження робочих проксі: {e}")
