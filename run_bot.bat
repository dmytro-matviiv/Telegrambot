@echo off
echo ========================================
echo    Запуск Українського Новинного Бота
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

echo Файл .env знайдено. Запускаємо бота...
echo.
echo Для зупинки бота натисніть Ctrl+C
echo.

REM Запускаємо бота
python main.py

echo.
echo Бот зупинено.
pause 