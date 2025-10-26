# 🚀 Руководство по деплою и обновлению бота

Этот документ описывает процесс развертывания и обновления Telegram бота для судейской системы донских игр на сервере.

## 📋 Содержание

- [Подготовка к деплою](#подготовка-к-деплою)
- [Деплой на Linux](#деплой-на-linux)
- [Деплой на Windows](#деплой-на-windows)
- [Обновление бота](#обновление-бота)
- [Управление ботом](#управление-бота)
- [Решение проблем](#решение-проблем)

---

## 🛠️ Подготовка к деплою

### Требования

- **Python 3.8+**
- **Git**
- **Доступ к интернету**
- **Telegram Bot Token** (получить у [@BotFather](https://t.me/BotFather))

### Linux

```bash
# Установка зависимостей (Ubuntu/Debian)
sudo apt update
sudo apt install python3 python3-venv python3-pip git -y

# Для CentOS/RHEL
sudo yum install python3 python3-pip git -y
```

### Windows

1. Скачайте и установите [Python 3.8+](https://www.python.org/downloads/)
   - ✅ Отметьте "Add Python to PATH" при установке
2. Скачайте и установите [Git](https://git-scm.com/download/win)

---

## 🐧 Деплой на Linux

### Вариант 1: Автоматический деплой (Рекомендуется)

```bash
# Скачайте скрипт деплоя
curl -O https://raw.githubusercontent.com/Tw1zzzzz/donstusud/master/deploy.sh

# Дайте права на выполнение
chmod +x deploy.sh

# Запустите деплой
./deploy.sh

# Для установки systemd сервиса (автозапуск)
sudo ./deploy.sh
```

### Вариант 2: Ручной деплой

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/Tw1zzzzz/donstusud.git
cd donstusud

# 2. Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# 3. Установите зависимости
pip install -r requirements.txt

# 4. Настройте конфигурацию
nano .env
# Добавьте: BOT_TOKEN=ваш_токен_от_BotFather

# 5. Запустите бота
python main.py
```

### Настройка systemd сервиса

Для автоматического запуска бота при старте системы:

```bash
sudo nano /etc/systemd/system/donstusud-bot.service
```

Содержимое файла:

```ini
[Unit]
Description=DonsTusud Telegram Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/donstusud
Environment="PATH=/home/YOUR_USERNAME/donstusud/venv/bin"
ExecStart=/home/YOUR_USERNAME/donstusud/venv/bin/python /home/YOUR_USERNAME/donstusud/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Замените `YOUR_USERNAME` на ваше имя пользователя.

Активируйте сервис:

```bash
sudo systemctl daemon-reload
sudo systemctl enable donstusud-bot
sudo systemctl start donstusud-bot
```

---

## 🪟 Деплой на Windows

### Вариант 1: Автоматический деплой (Рекомендуется)

1. Скачайте [deploy.bat](https://raw.githubusercontent.com/Tw1zzzzz/donstusud/master/deploy.bat)
2. Запустите файл двойным кликом
3. Следуйте инструкциям на экране
4. Отредактируйте `.env` файл и добавьте BOT_TOKEN
5. Используйте ярлык на рабочем столе для запуска бота

### Вариант 2: Ручной деплой

```powershell
# 1. Клонируйте репозиторий
git clone https://github.com/Tw1zzzzz/donstusud.git
cd donstusud

# 2. Создайте виртуальное окружение
python -m venv venv
venv\Scripts\activate

# 3. Установите зависимости
pip install -r requirements.txt

# 4. Настройте конфигурацию
notepad .env
# Добавьте: BOT_TOKEN=ваш_токен_от_BotFather

# 5. Запустите бота
python main.py
```

---

## 🔄 Обновление бота

### Linux

#### Автоматическое обновление

```bash
cd ~/donstusud
./update.sh
```

Скрипт автоматически:
- ✅ Проверит наличие обновлений
- ✅ Создаст резервную копию базы данных
- ✅ Остановит бота
- ✅ Скачает обновления
- ✅ Обновит зависимости
- ✅ Запустит бота

#### Ручное обновление

```bash
cd ~/donstusud

# Остановите бота
sudo systemctl stop donstusud-bot
# или нажмите Ctrl+C если запущен вручную

# Сделайте резервную копию
cp bot.db bot_backup_$(date +%Y%m%d).db

# Получите обновления
git pull origin master

# Активируйте venv и обновите зависимости
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Запустите бота
sudo systemctl start donstusud-bot
# или python main.py
```

### Windows

#### Автоматическое обновление

1. Запустите `update.bat` из папки проекта
2. Следуйте инструкциям на экране
3. Бот автоматически перезапустится

#### Ручное обновление

```powershell
cd C:\Users\YOUR_USERNAME\donstusud

# Остановите бота (Ctrl+C в окне бота)

# Сделайте резервную копию
copy bot.db bot_backup.db

# Получите обновления
git pull origin master

# Активируйте venv и обновите зависимости
venv\Scripts\activate
pip install -r requirements.txt --upgrade

# Запустите бота
python main.py
```

---

## 🎮 Управление ботом

### Linux (с systemd)

```bash
# Запустить бота
sudo systemctl start donstusud-bot

# Остановить бота
sudo systemctl stop donstusud-bot

# Перезапустить бота
sudo systemctl restart donstusud-bot

# Статус бота
sudo systemctl status donstusud-bot

# Просмотр логов (в реальном времени)
sudo journalctl -u donstusud-bot -f

# Последние 50 строк логов
sudo journalctl -u donstusud-bot -n 50

# Отключить автозапуск
sudo systemctl disable donstusud-bot

# Включить автозапуск
sudo systemctl enable donstusud-bot
```

### Windows

```powershell
# Запуск бота
start_bot.bat
# или используйте ярлык на рабочем столе

# Остановка бота
# Нажмите Ctrl+C в окне бота

# Просмотр логов
notepad bot.log
```

---

## 🔧 Решение проблем

### Бот не запускается

**Проблема:** Ошибка "BOT_TOKEN is not set"

**Решение:**
```bash
# Проверьте наличие .env файла
ls -la .env

# Убедитесь, что BOT_TOKEN указан
cat .env | grep BOT_TOKEN

# Отредактируйте файл
nano .env
```

### Ошибка подключения к Telegram

**Проблема:** "Error: Connection refused" или "Timeout"

**Решение:**
- Проверьте интернет-соединение
- Убедитесь, что Telegram API не заблокирован файрволом
- Попробуйте использовать прокси (настраивается в `config.py`)

### База данных заблокирована

**Проблема:** "database is locked"

**Решение:**
```bash
# Остановите все процессы бота
sudo systemctl stop donstusud-bot
# или
pkill -f "python.*main.py"

# Проверьте, нет ли других процессов
ps aux | grep main.py

# Запустите бота снова
sudo systemctl start donstusud-bot
```

### Systemd сервис не запускается

**Проблема:** Сервис в состоянии "failed"

**Решение:**
```bash
# Посмотрите детали ошибки
sudo journalctl -u donstusud-bot -n 50 --no-pager

# Проверьте права доступа
ls -la ~/donstusud

# Проверьте наличие виртуального окружения
ls -la ~/donstusud/venv/bin/python

# Попробуйте запустить вручную для диагностики
cd ~/donstusud
source venv/bin/activate
python main.py
```

### Обновление не работает

**Проблема:** Git выдает ошибку при `git pull`

**Решение:**
```bash
# Сохраните локальные изменения
git stash

# Обновите
git pull origin master

# Верните изменения (если нужно)
git stash pop

# Если есть конфликты
git status
# Разрешите конфликты вручную
```

### Проблемы с зависимостями

**Проблема:** Ошибки при установке пакетов

**Решение:**
```bash
# Linux: Установите необходимые системные пакеты
sudo apt install python3-dev build-essential

# Обновите pip
pip install --upgrade pip

# Переустановите зависимости
pip install -r requirements.txt --force-reinstall
```

---

## 📊 Мониторинг

### Проверка работы бота

```bash
# Логи бота
tail -f bot.log

# Проверка процесса (Linux)
ps aux | grep "python.*main.py"

# Проверка сетевых соединений
netstat -an | grep ESTABLISHED | grep python
```

### Резервное копирование

```bash
# Создание резервной копии (Linux)
mkdir -p ~/backups
cp ~/donstusud/bot.db ~/backups/bot_$(date +%Y%m%d_%H%M%S).db

# Автоматическое резервное копирование (cron)
# Добавьте в crontab (crontab -e):
0 2 * * * cp ~/donstusud/bot.db ~/backups/bot_$(date +\%Y\%m\%d).db

# Восстановление из резервной копии
cp ~/backups/bot_20250101.db ~/donstusud/bot.db
```

---

## 🔐 Безопасность

### Рекомендации

1. **Никогда не публикуйте BOT_TOKEN в открытом виде**
2. **Регулярно делайте резервные копии базы данных**
3. **Используйте HTTPS для подключения к серверу**
4. **Ограничьте доступ к серверу (используйте firewall)**
5. **Регулярно обновляйте зависимости**

### Проверка безопасности

```bash
# Проверка прав доступа к .env
ls -la .env
# Должно быть: -rw-r----- (640) или -rw------- (600)

# Установка правильных прав
chmod 600 .env

# Проверка версий пакетов на уязвимости
pip list --outdated
```

---

## 📞 Поддержка

Если у вас возникли проблемы:

1. Проверьте [FAQ](FAQ.md)
2. Просмотрите [Issues на GitHub](https://github.com/Tw1zzzzz/donstusud/issues)
3. Создайте новый Issue с описанием проблемы

---

## 📝 Дополнительные ресурсы

- [README](README.md) - Основная документация
- [QUICKSTART](QUICKSTART.md) - Быстрый старт
- [TESTING_GUIDE](TESTING_GUIDE.md) - Руководство по тестированию
- [ARCHITECTURE](ARCHITECTURE.md) - Архитектура проекта

---

**Версия документа:** 1.0  
**Последнее обновление:** 26.10.2025

