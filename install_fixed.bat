@echo off
echo ========================================
echo    Український Новинний Telegram Бот
echo ========================================
echo.
echo Встановлення залежностей (виправлена версія)...

REM Перевіряємо чи встановлений Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Помилка: Python не знайдено!
    echo Будь ласка, встановіть Python з https://python.org
    pause
    exit /b 1
)

echo Python знайдено. Встановлюємо залежності...

REM Оновлюємо pip до останньої версії
echo Оновлюємо pip...
python -m pip install --upgrade pip

REM Встановлюємо Pillow окремо з попередньо скомпільованими колесами
echo Встановлюємо Pillow...
pip install --only-binary=all Pillow

REM Встановлюємо інші залежності
echo Встановлюємо інші залежності...
pip install python-telegram-bot==20.7 requests==2.31.0 beautifulsoup4==4.12.2 feedparser==6.0.10 python-dotenv==1.0.0 aiohttp==3.9.1 asyncio==3.4.3 schedule==1.2.0

if errorlevel 1 (
    echo Помилка при встановленні залежностей!
    echo Спробуйте встановити Microsoft Visual C++ Build Tools
    echo або використайте: pip install --only-binary=all -r requirements.txt
    pause
    exit /b 1
)

echo.
echo ========================================
echo Залежності встановлено успішно!
echo ========================================
echo.
echo Наступні кроки:
echo 1. Створіть файл .env на основі env_example.txt
echo 2. Налаштуйте BOT_TOKEN та CHANNEL_ID
echo 3. Запустіть test_bot.py для перевірки
echo 4. Запустіть main.py для роботи бота
echo.
pause 