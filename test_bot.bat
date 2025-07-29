@echo off
echo ========================================
echo    Тестування Українського Новинного Бота
echo ========================================
echo.

REM Перевіряємо чи існує файл .env
if not exist ".env" (
    echo Помилка: Файл .env не знайдено!
    echo Будь ласка, створіть файл .env на основі env_example.txt
    echo та налаштуйте BOT_TOKEN та CHANNEL_ID
    pause
    exit /b 1
)

echo Файл .env знайдено. Запускаємо тестування...
echo.

REM Запускаємо тестування
python test_bot.py

echo.
echo Тестування завершено.
pause 