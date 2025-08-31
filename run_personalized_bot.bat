@echo off
echo ========================================
echo    Персоналізований Telegram Бот
echo ========================================
echo.

REM Перевіряємо чи існує віртуальне середовище
if exist "venv\Scripts\activate.bat" (
    echo Активація віртуального середовища...
    call venv\Scripts\activate.bat
) else if exist "venv310\Scripts\activate.bat" (
    echo Активація віртуального середовища...
    call venv310\Scripts\activate.bat
) else (
    echo Віртуальне середовище не знайдено, використовуємо системний Python
)

echo.
echo Запуск персоналізованого бота...
echo Натисніть Ctrl+C для зупинки
echo.

python main_personalized.py

echo.
echo Бот зупинено.
pause
