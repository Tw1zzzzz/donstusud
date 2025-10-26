@echo off
REM 🔄 Скрипт обновления Telegram бота (Windows)

chcp 65001 > nul
echo ═══════════════════════════════════════
echo    🔄 Обновление DonsTusud Bot (Windows)
echo ═══════════════════════════════════════
echo.

set PROJECT_DIR=%USERPROFILE%\donstusud

REM Проверка существования проекта
if not exist "%PROJECT_DIR%" (
    echo ❌ Проект не найден в %PROJECT_DIR%
    echo    Сначала выполните деплой: deploy.bat
    pause
    exit /b 1
)

cd /d "%PROJECT_DIR%"

echo 📦 Шаг 1/6: Проверка обновлений...
git fetch origin
if %errorlevel% neq 0 (
    echo ❌ Ошибка проверки обновлений
    pause
    exit /b 1
)

REM Проверка наличия новых коммитов
for /f %%i in ('git rev-list HEAD...origin/master --count') do set UPDATE_COUNT=%%i
if "%UPDATE_COUNT%"=="0" (
    echo ✅ Вы используете последнюю версию!
    choice /C YN /M "Продолжить обновление зависимостей"
    if errorlevel 2 (
        echo ℹ️  Обновление отменено
        pause
        exit /b 0
    )
) else (
    echo 📥 Найдено новых коммитов: %UPDATE_COUNT%
)
echo.

echo 📦 Шаг 2/6: Создание резервной копии...
set BACKUP_DIR=%PROJECT_DIR%\backups
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM Получаем текущую дату и время
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set TIMESTAMP=%dt:~0,8%_%dt:~8,6%

REM Бэкап базы данных
if exist "bot.db" (
    copy /Y bot.db "%BACKUP_DIR%\bot_%TIMESTAMP%.db" >nul
    echo ✅ База данных сохранена: backups\bot_%TIMESTAMP%.db
)

REM Бэкап конфигурации
if exist ".env" (
    copy /Y .env "%BACKUP_DIR%\.env_%TIMESTAMP%" >nul
    echo ✅ Конфигурация сохранена
)
echo.

echo 📦 Шаг 3/6: Остановка бота...
REM Завершаем процессы Python, связанные с main.py
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *main.py*" 2>nul | find /I "python.exe" >nul
if %errorlevel% equ 0 (
    taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *main.py*" >nul 2>&1
    echo ✅ Бот остановлен
) else (
    echo ℹ️  Бот не запущен
)
timeout /t 2 /nobreak >nul
echo.

echo 📦 Шаг 4/6: Получение обновлений...
git pull origin master
if %errorlevel% neq 0 (
    echo ❌ Ошибка получения обновлений
    echo    Возможно, есть локальные изменения. Попробуйте:
    echo    git stash
    echo    git pull origin master
    pause
    exit /b 1
)
echo ✅ Код обновлен
echo.

echo 📦 Шаг 5/6: Обновление зависимостей...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt --upgrade
if %errorlevel% neq 0 (
    echo ❌ Ошибка обновления зависимостей
    pause
    exit /b 1
)
echo ✅ Зависимости обновлены
echo.

echo 📦 Шаг 6/6: Проверка конфигурации...
if not exist ".env" (
    echo ⚠️  Файл .env не найден!
    if exist "config.py.example" (
        echo    Создаю из примера...
        copy config.py.example config.py >nul
    )
)
echo ✅ Конфигурация проверена
echo.

echo ═══════════════════════════════════════
echo    ✅ Обновление завершено!
echo ═══════════════════════════════════════
echo.
echo 📋 Следующие шаги:
echo.
echo 1. Запустите бота:
echo    - Используйте ярлык на рабочем столе
echo    - Или: "%PROJECT_DIR%\start_bot.bat"
echo.
echo 2. Для отката к предыдущей версии:
echo    copy "%BACKUP_DIR%\bot_%TIMESTAMP%.db" bot.db
echo.
echo 3. Просмотр логов:
echo    notepad bot.log
echo.
echo ═══════════════════════════════════════
echo.

choice /C YN /M "Запустить бота сейчас"
if errorlevel 1 if not errorlevel 2 (
    start "" "%PROJECT_DIR%\start_bot.bat"
)

pause

