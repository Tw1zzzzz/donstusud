# 🪟 Деплой на Windows - Пошаговая инструкция

## Вариант 1: Быстрый деплой (Рекомендуется)

### Шаг 1: Установка зависимостей

1. Установите [Python 3.8+](https://www.python.org/downloads/)
   - ✅ При установке отметьте "Add Python to PATH"
   
2. Установите [Git для Windows](https://git-scm.com/download/win)
   - Используйте настройки по умолчанию

### Шаг 2: Клонирование проекта

Откройте PowerShell или CMD и выполните:

```powershell
cd %USERPROFILE%\Documents
git clone https://github.com/Tw1zzzzz/donstusud.git
cd donstusud
```

### Шаг 3: Создание виртуального окружения

```powershell
python -m venv venv
venv\Scripts\activate.bat
```

### Шаг 4: Установка зависимостей

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Шаг 5: Настройка конфигурации

Создайте файл `.env` в папке проекта:

```
BOT_TOKEN=ваш_токен_от_BotFather
DB_PATH=bot.db
AUTO_CLOSE_DAYS=3
RATE_LIMIT_MAX_REQUESTS=10
RATE_LIMIT_PERIOD=60
LOG_LEVEL=INFO
```

### Шаг 6: Запуск бота

```powershell
python main.py
```

или используйте готовый скрипт:

```powershell
start_bot.bat
```

---

## Вариант 2: Автоматический скрипт

Создайте файл `auto_deploy.bat` со следующим содержимым:

```batch
@echo off
chcp 65001 > nul
echo Начинаем установку бота...
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python не установлен!
    echo Скачайте с: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Проверка Git
git --version >nul 2>&1
if errorlevel 1 (
    echo Git не установлен!
    echo Скачайте с: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo Клонирование репозитория...
cd %USERPROFILE%\Documents
git clone https://github.com/Tw1zzzzz/donstusud.git
cd donstusud

echo Создание виртуального окружения...
python -m venv venv

echo Установка зависимостей...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ===================================
echo Установка завершена!
echo ===================================
echo.
echo ВАЖНО: Отредактируйте файл .env
echo и добавьте ваш BOT_TOKEN
echo.
pause
```

Запустите этот файл, и он автоматически выполнит все шаги установки.

---

## Обновление бота на Windows

Создайте файл `auto_update.bat`:

```batch
@echo off
chcp 65001 > nul
echo Обновление бота...
echo.

cd %USERPROFILE%\Documents\donstusud

echo Создание резервной копии...
if not exist backups mkdir backups
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set TIMESTAMP=%dt:~0,8%_%dt:~8,6%
copy bot.db backups\bot_%TIMESTAMP%.db

echo Получение обновлений...
git pull origin master

echo Обновление зависимостей...
call venv\Scripts\activate.bat
pip install -r requirements.txt --upgrade

echo.
echo Обновление завершено!
echo Запустите бота через start_bot.bat
echo.
pause
```

---

## Автозапуск бота при старте Windows

### Метод 1: Через планировщик задач

1. Откройте "Планировщик заданий" (Task Scheduler)
2. Создайте базовую задачу:
   - Имя: "DonsTusud Bot"
   - Триггер: При входе в систему
   - Действие: Запустить программу
   - Программа: `%USERPROFILE%\Documents\donstusud\start_bot.bat`
3. В дополнительных параметрах:
   - ✅ Запускать с наивысшими правами
   - ✅ Запускать независимо от того, вошел ли пользователь в систему

### Метод 2: Папка автозагрузки

Создайте ярлык `start_bot.bat` и поместите его в:

```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
```

---

## Управление ботом

### Запуск

```powershell
cd %USERPROFILE%\Documents\donstusud
start_bot.bat
```

### Остановка

Нажмите `Ctrl+C` в окне бота

### Просмотр логов

```powershell
notepad %USERPROFILE%\Documents\donstusud\bot.log
```

---

## Решение проблем

### "python не является внутренней командой"

**Решение:** Python не добавлен в PATH. Переустановите Python с галочкой "Add Python to PATH"

### "Не удается загрузить файл, выполнение скриптов отключено"

**Решение:** Разрешите выполнение скриптов PowerShell:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Ошибка при клонировании репозитория

**Решение:** Проверьте подключение к интернету и убедитесь, что Git установлен правильно.

---

## Создание Windows Service

Для продвинутых пользователей - создание службы Windows:

1. Установите `nssm` (Non-Sucking Service Manager):
   - Скачайте с https://nssm.cc/download
   - Распакуйте в `C:\nssm`

2. Создайте службу:

```powershell
cd C:\nssm\win64
nssm install DonsTusudBot "%USERPROFILE%\Documents\donstusud\venv\Scripts\python.exe" "%USERPROFILE%\Documents\donstusud\main.py"
nssm set DonsTusudBot AppDirectory "%USERPROFILE%\Documents\donstusud"
nssm set DonsTusudBot DisplayName "DonsTusud Telegram Bot"
nssm set DonsTusudBot Description "Telegram bot for судейская система"
nssm set DonsTusudBot Start SERVICE_AUTO_START
nssm start DonsTusudBot
```

3. Управление службой:

```powershell
# Запуск
nssm start DonsTusudBot

# Остановка
nssm stop DonsTusudBot

# Статус
nssm status DonsTusudBot

# Удаление
nssm remove DonsTusudBot confirm
```

---

## Полезные команды

```powershell
# Проверка версии Python
python --version

# Проверка версии Git
git --version

# Список установленных пакетов
pip list

# Проверка обновлений пакетов
pip list --outdated

# Активация виртуального окружения
venv\Scripts\activate.bat

# Деактивация виртуального окружения
deactivate
```

---

**Готово!** Теперь ваш бот установлен и готов к работе на Windows.

