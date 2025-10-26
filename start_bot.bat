@echo off
chcp 65001 >nul
echo ============================================================
echo        БЕЗОПАСНЫЙ ЗАПУСК CS2 JUDGE BOT
echo ============================================================
echo.

REM Активируем виртуальное окружение
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo ОШИБКА: Виртуальное окружение не найдено!
    echo Запустите: python _create_venv.py
    pause
    exit /b 1
)

REM Запускаем скрипт безопасного запуска
python start_bot_safe.py

pause

