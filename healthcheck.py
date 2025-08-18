#!/usr/bin/env python3
"""
Простий health check для Railway
"""

import os
import sys

def main():
    """Перевіряє чи бот може запуститися"""
    try:
        # Перевіряємо наявність необхідних змінних середовища
        required_env_vars = ['BOT_TOKEN', 'CHANNEL_ID']
        missing_vars = []
        
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Відсутні змінні середовища: {', '.join(missing_vars)}")
            sys.exit(1)
        
        # Перевіряємо імпорт основних модулів
        try:
            from main import NewsBot
            print("✅ Основний бот успішно імпортується")
        except Exception as e:
            print(f"❌ Помилка імпорту основного бота: {e}")
            sys.exit(1)
        
        # Перевіряємо імпорт монітора тривог
        try:
            from air_alerts_monitor import AirAlertsMonitor
            print("✅ Монітор тривог успішно імпортується")
        except Exception as e:
            print(f"❌ Помилка імпорту монітора тривог: {e}")
            sys.exit(1)
        
        # Перевіряємо імпорт збору новин
        try:
            from news_collector import NewsCollector
            print("✅ Збір новин успішно імпортується")
        except Exception as e:
            print(f"❌ Помилка імпорту збору новин: {e}")
            sys.exit(1)
        
        print("✅ Всі перевірки пройшли успішно")
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Критична помилка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
