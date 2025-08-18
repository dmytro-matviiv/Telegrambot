#!/usr/bin/env python3
"""
Тест Docker збірки для Українського новинного бота
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Запускає команду та виводить результат"""
    print(f"🔧 {description}...")
    print(f"Команда: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} успішно")
            if result.stdout:
                print(f"Вивід: {result.stdout}")
        else:
            print(f"❌ {description} невдало")
            if result.stderr:
                print(f"Помилка: {result.stderr}")
            if result.stdout:
                print(f"Вивід: {result.stdout}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Помилка виконання команди: {e}")
        return False

def main():
    """Основний функція тестування"""
    print("🐳 Тестування Docker збірки для Українського новинного бота")
    print("=" * 60)
    
    # Перевіряємо наявність Docker
    if not run_command("docker --version", "Перевірка наявності Docker"):
        print("❌ Docker не знайдено. Встановіть Docker Desktop.")
        return False
    
    # Перевіряємо наявність docker-compose
    if not run_command("docker-compose --version", "Перевірка наявності docker-compose"):
        print("❌ docker-compose не знайдено. Встановіть docker-compose.")
        return False
    
    # Перевіряємо файли
    required_files = [
        "requirements-docker-minimal.txt",
        "Dockerfile",
        "docker-compose.yml",
        ".dockerignore"
    ]
    
    print("\n📁 Перевірка необхідних файлів...")
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} не знайдено")
            return False
    
    # Тестуємо збірку Docker образу
    print("\n🔨 Тестування збірки Docker образу...")
    if run_command("docker build -t test-telegram-bot .", "Збірка Docker образу"):
        print("✅ Docker образ успішно зібрано")
        
        # Очищаємо тестовий образ
        run_command("docker rmi test-telegram-bot", "Видалення тестового образу")
    else:
        print("❌ Помилка збірки Docker образу")
        return False
    
    print("\n🎉 Всі тести пройшли успішно!")
    print("\n📋 Для запуску бота використовуйте:")
    print("   docker-compose up --build")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
