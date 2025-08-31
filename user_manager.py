import json
import logging
import os
from typing import Dict, List, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)

class UserManager:
    def __init__(self, users_file: str = 'users.json'):
        self.users_file = users_file
        self.users = self._load_users()
    
    def _load_users(self) -> Dict:
        """Завантажує користувачів з файлу"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Створюємо файл з базовою структурою
                default_users = {}
                self._save_users(default_users)
                return default_users
        except Exception as e:
            logger.error(f"Помилка завантаження користувачів: {e}")
            return {}
    
    def _save_users(self, users: Dict):
        """Зберігає користувачів у файл"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Помилка збереження користувачів: {e}")
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None) -> bool:
        """Додає нового користувача"""
        try:
            if str(user_id) not in self.users:
                self.users[str(user_id)] = {
                    'user_id': user_id,
                    'username': username,
                    'first_name': first_name,
                    'subscriptions': {
                        'alerts': True,      # Тривоги
                        'news': True,        # Новини
                        'memorial': True     # Меморіальні повідомлення
                    },
                    'created_at': datetime.now().isoformat(),
                    'last_activity': datetime.now().isoformat()
                }
                self._save_users(self.users)
                logger.info(f"Додано нового користувача: {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Помилка додавання користувача: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Отримує інформацію про користувача"""
        return self.users.get(str(user_id))
    
    def update_user_activity(self, user_id: int):
        """Оновлює час останньої активності користувача"""
        try:
            if str(user_id) in self.users:
                self.users[str(user_id)]['last_activity'] = datetime.now().isoformat()
                self._save_users(self.users)
        except Exception as e:
            logger.error(f"Помилка оновлення активності користувача: {e}")
    
    def update_subscription(self, user_id: int, subscription_type: str, enabled: bool) -> bool:
        """Оновлює налаштування підписки користувача"""
        try:
            if str(user_id) in self.users:
                if subscription_type in self.users[str(user_id)]['subscriptions']:
                    self.users[str(user_id)]['subscriptions'][subscription_type] = enabled
                    self.users[str(user_id)]['last_activity'] = datetime.now().isoformat()
                    self._save_users(self.users)
                    logger.info(f"Оновлено підписку {subscription_type} для користувача {user_id}: {enabled}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Помилка оновлення підписки: {e}")
            return False
    
    def get_subscribers(self, subscription_type: str) -> List[int]:
        """Отримує список користувачів, підписаних на конкретний тип повідомлень"""
        try:
            subscribers = []
            for user_id, user_data in self.users.items():
                if user_data.get('subscriptions', {}).get(subscription_type, False):
                    subscribers.append(int(user_id))
            return subscribers
        except Exception as e:
            logger.error(f"Помилка отримання підписників: {e}")
            return []
    
    def get_user_subscriptions(self, user_id: int) -> Dict[str, bool]:
        """Отримує налаштування підписок користувача"""
        try:
            user = self.get_user(user_id)
            if user:
                return user.get('subscriptions', {})
            return {}
        except Exception as e:
            logger.error(f"Помилка отримання підписок користувача: {e}")
            return {}
    
    def get_all_users(self) -> List[int]:
        """Отримує список всіх користувачів"""
        try:
            return [int(user_id) for user_id in self.users.keys()]
        except Exception as e:
            logger.error(f"Помилка отримання всіх користувачів: {e}")
            return []
    
    def remove_user(self, user_id: int) -> bool:
        """Видаляє користувача"""
        try:
            if str(user_id) in self.users:
                del self.users[str(user_id)]
                self._save_users(self.users)
                logger.info(f"Видалено користувача: {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Помилка видалення користувача: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Отримує статистику користувачів"""
        try:
            total_users = len(self.users)
            alerts_subscribers = len(self.get_subscribers('alerts'))
            news_subscribers = len(self.get_subscribers('news'))
            memorial_subscribers = len(self.get_subscribers('memorial'))
            
            return {
                'total_users': total_users,
                'alerts_subscribers': alerts_subscribers,
                'news_subscribers': news_subscribers,
                'memorial_subscribers': memorial_subscribers
            }
        except Exception as e:
            logger.error(f"Помилка отримання статистики: {e}")
            return {}
