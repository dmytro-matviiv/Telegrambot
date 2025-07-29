import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
import logging
import feedparser
from news_collector import NewsCollector
from config import NEWS_SOURCES

logger = logging.getLogger(__name__)

class AdvancedNewsCollector(NewsCollector):
    """Розширений збирач новин з додатковими можливостями"""
    
    def __init__(self):
        super().__init__()
        
        # Додаткові джерела новин
        self.additional_sources = {
            'ukrinform': {
                'name': 'Укрінформ',
                'url': 'https://www.ukrinform.ua/rss',
                'website': 'https://www.ukrinform.ua'
            },
            'interfax_ua': {
                'name': 'Інтерфакс-Україна',
                'url': 'https://interfax.com.ua/rss',
                'website': 'https://interfax.com.ua'
            },
            'unian': {
                'name': 'УНІАН',
                'url': 'https://www.unian.ua/rss',
                'website': 'https://www.unian.ua'
            }
        }

    def get_news_from_ukrinform(self) -> List[Dict]:
        """Спеціальний збирач для Укрінформ"""
        news_list = []
        try:
            logger.info("Збираємо новини з Укрінформ")
            
            # Спробуємо різні RSS URL
            rss_urls = [
                'https://www.ukrinform.ua/rss',
                'https://www.ukrinform.ua/rss/ukr',
                'https://www.ukrinform.ua/rss/eng'
            ]
            
            for rss_url in rss_urls:
                try:
                    response = self.session.get(rss_url, timeout=10)
                    if response.status_code == 200:
                        feed = feedparser.parse(response.content)
                        if feed.entries:
                            for entry in feed.entries[:5]:
                                news_id = f"ukrinform_{entry.get('id', entry.get('link', ''))}"
                                
                                if news_id in self.published_news:
                                    continue
                                
                                news_item = {
                                    'id': news_id,
                                    'title': entry.get('title', ''),
                                    'description': entry.get('summary', ''),
                                    'full_text': self.get_full_article_text(entry.get('link', '')),
                                    'link': entry.get('link', ''),
                                    'image_url': self.extract_image_url(entry, entry.get('link', '')),
                                    'source': 'Укрінформ',
                                    'source_key': 'ukrinform',
                                    'published': entry.get('published', ''),
                                    'timestamp': datetime.now().isoformat()
                                }
                                
                                news_list.append(news_item)
                            break
                except Exception as e:
                    logger.warning(f"Помилка при отриманні RSS з {rss_url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Помилка при зборі новин з Укрінформ: {e}")
        
        return news_list

    def get_news_from_government_websites(self) -> List[Dict]:
        """Збирає новини з державних веб-сайтів без RSS"""
        news_list = []
        
        government_sites = {
            'minfin': {
                'name': 'Міністерство фінансів',
                'url': 'https://mof.gov.ua/uk/news',
                'selectors': {
                    'news_container': '.news-list',
                    'news_item': '.news-item',
                    'title': '.news-title',
                    'link': 'a',
                    'date': '.news-date'
                }
            },
            'minjust': {
                'name': 'Міністерство юстиції',
                'url': 'https://minjust.gov.ua/news',
                'selectors': {
                    'news_container': '.news-list',
                    'news_item': '.news-item',
                    'title': '.news-title',
                    'link': 'a',
                    'date': '.news-date'
                }
            }
        }
        
        for site_key, site_info in government_sites.items():
            try:
                logger.info(f"Збираємо новини з {site_info['name']}")
                
                response = self.session.get(site_info['url'], timeout=15)
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                selectors = site_info['selectors']
                
                # Шукаємо контейнер з новинами
                news_container = soup.select_one(selectors['news_container'])
                if not news_container:
                    continue
                
                # Знаходимо всі новини
                news_items = news_container.select(selectors['news_item'])
                
                for item in news_items[:10]:  # Останні 10 новин
                    try:
                        title_elem = item.select_one(selectors['title'])
                        link_elem = item.select_one(selectors['link'])
                        
                        if not title_elem or not link_elem:
                            continue
                        
                        title = title_elem.get_text(strip=True)
                        link = link_elem.get('href', '')
                        
                        # Перетворюємо відносне посилання в абсолютне
                        if link.startswith('/'):
                            link = f"https://{site_info['url'].split('/')[2]}{link}"
                        
                        news_id = f"{site_key}_{link}"
                        
                        if news_id in self.published_news:
                            continue
                        
                        news_item = {
                            'id': news_id,
                            'title': title,
                            'description': '',
                            'full_text': self.get_full_article_text(link),
                            'link': link,
                            'image_url': '',
                            'source': site_info['name'],
                            'source_key': site_key,
                            'published': '',
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        news_list.append(news_item)
                        
                    except Exception as e:
                        logger.error(f"Помилка при обробці новини з {site_info['name']}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Помилка при зборі новин з {site_info['name']}: {e}")
        
        return news_list

    def collect_all_news_advanced(self) -> List[Dict]:
        """Розширений збір новин з усіх джерел"""
        all_news = []
        
        # Збираємо з базових RSS джерел
        logger.info("Збираємо новини з основних RSS джерел...")
        basic_news = super().collect_all_news()
        all_news.extend(basic_news)
        
        # Збираємо з додаткових RSS джерел
        logger.info("Збираємо новини з додаткових RSS джерел...")
        for source_key, source_info in self.additional_sources.items():
            try:
                news = self.get_news_from_rss(source_key, source_info)
                all_news.extend(news)
                time.sleep(2)
            except Exception as e:
                logger.error(f"Помилка при зборі новин з {source_key}: {e}")
        
        # Збираємо з державних веб-сайтів
        logger.info("Збираємо новини з державних веб-сайтів...")
        government_news = self.get_news_from_government_websites()
        all_news.extend(government_news)
        
        # Сортуємо за часом публікації
        all_news.sort(key=lambda x: x.get('published', ''), reverse=True)
        
        logger.info(f"Всього зібрано {len(all_news)} новин")
        return all_news

    def filter_news_by_keywords(self, news_list: List[Dict], keywords: List[str]) -> List[Dict]:
        """Фільтрує новини за ключовими словами"""
        filtered_news = []
        
        for news in news_list:
            title = news.get('title', '').lower()
            description = news.get('description', '').lower()
            full_text = news.get('full_text', '').lower()
            
            text_to_search = f"{title} {description} {full_text}"
            
            for keyword in keywords:
                if keyword.lower() in text_to_search:
                    filtered_news.append(news)
                    break
        
        return filtered_news

    def remove_duplicates(self, news_list: List[Dict]) -> List[Dict]:
        """Видаляє дублікати новин за заголовком та початком тексту"""
        seen_titles = set()
        seen_texts = set()
        unique_news = []
        
        for news in news_list:
            title = news.get('title', '').strip().lower()
            text = (news.get('full_text') or news.get('description') or '').strip().lower()[:100]
            key = (title, text)
            if title and key not in seen_titles and text and text not in seen_texts:
                seen_titles.add(key)
                seen_texts.add(text)
                unique_news.append(news)
        
        return unique_news

    def get_news_statistics(self) -> Dict:
        """Повертає статистику збору новин"""
        stats = {
            'total_sources': len(NEWS_SOURCES) + len(self.additional_sources),
            'published_news_count': len(self.published_news),
            'last_check': datetime.now().isoformat()
        }
        
        return stats 