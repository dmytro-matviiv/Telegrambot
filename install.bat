@echo off
echo ========================================
echo    Український Новинний Telegram Бот
echo ========================================
echo.
echo Встановлення залежностей...

REM Перевіряємо чи встановлений Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Помилка: Python не знайдено!
    echo Будь ласка, встановіть Python з https://python.org
    pause
    exit /b 1
)

echo Python знайдено. Встановлюємо залежності...

REM Встановлюємо залежності
pip install -r requirements.txt

if errorlevel 1 (
    echo Помилка при встановленні залежностей!
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