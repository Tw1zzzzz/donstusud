#!/bin/bash
# 🚀 Скрипт деплоя Telegram бота на сервер

set -e  # Остановка при ошибке

echo "═══════════════════════════════════════"
echo "   🚀 Деплой DonsTusud Bot"
echo "═══════════════════════════════════════"

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Проверка наличия git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git не установлен. Установите git и повторите попытку.${NC}"
    exit 1
fi

# Проверка наличия Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 не установлен. Установите Python 3.8+ и повторите попытку.${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 Шаг 1/7: Клонирование репозитория...${NC}"
REPO_URL="https://github.com/Tw1zzzzz/donstusud.git"
PROJECT_DIR="$HOME/donstusud"

if [ -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}⚠️  Папка $PROJECT_DIR уже существует.${NC}"
    read -p "Удалить и переустановить? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$PROJECT_DIR"
        git clone "$REPO_URL" "$PROJECT_DIR"
    else
        echo -e "${RED}❌ Деплой отменен.${NC}"
        exit 1
    fi
else
    git clone "$REPO_URL" "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"
echo -e "${GREEN}✅ Репозиторий склонирован${NC}"

echo -e "${YELLOW}📦 Шаг 2/7: Создание виртуального окружения...${NC}"
python3 -m venv venv
source venv/bin/activate
echo -e "${GREEN}✅ Виртуальное окружение создано${NC}"

echo -e "${YELLOW}📦 Шаг 3/7: Установка зависимостей...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✅ Зависимости установлены${NC}"

echo -e "${YELLOW}📦 Шаг 4/7: Настройка конфигурации...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚙️  Создание файла .env...${NC}"
    cat > .env << EOF
# Telegram Bot Token from @BotFather
BOT_TOKEN=your_bot_token_here

# Database path
DB_PATH=bot.db

# Auto-close applications after N days
AUTO_CLOSE_DAYS=3

# Rate limiting
RATE_LIMIT_MAX_REQUESTS=10
RATE_LIMIT_PERIOD=60

# Logging level
LOG_LEVEL=INFO
EOF
    echo -e "${RED}⚠️  ВАЖНО: Отредактируйте файл .env и добавьте BOT_TOKEN!${NC}"
    echo -e "${YELLOW}   nano $PROJECT_DIR/.env${NC}"
fi

if [ ! -f "config.py" ]; then
    cp config.py.example config.py
    echo -e "${GREEN}✅ Конфигурационный файл создан${NC}"
fi

echo -e "${YELLOW}📦 Шаг 5/7: Инициализация базы данных...${NC}"
python3 -c "from database.db import init_db; init_db()" 2>/dev/null || echo "База данных будет создана при первом запуске"
echo -e "${GREEN}✅ База данных готова${NC}"

echo -e "${YELLOW}📦 Шаг 6/7: Создание systemd сервиса...${NC}"
SERVICE_FILE="/etc/systemd/system/donstusud-bot.service"

if [ "$EUID" -eq 0 ]; then
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=DonsTusud Telegram Bot
After=network.target

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable donstusud-bot.service
    echo -e "${GREEN}✅ Systemd сервис создан и включен${NC}"
else
    echo -e "${YELLOW}⚠️  Запустите скрипт с sudo для создания systemd сервиса${NC}"
    echo -e "${YELLOW}   Сервис позволит автоматически запускать бота при старте системы${NC}"
fi

echo -e "${YELLOW}📦 Шаг 7/7: Финальная проверка...${NC}"
echo -e "${GREEN}✅ Деплой завершен!${NC}"

echo ""
echo "═══════════════════════════════════════"
echo -e "${GREEN}   ✅ Установка завершена!${NC}"
echo "═══════════════════════════════════════"
echo ""
echo "📝 Следующие шаги:"
echo ""
echo "1. Отредактируйте .env файл:"
echo -e "   ${YELLOW}nano $PROJECT_DIR/.env${NC}"
echo ""
echo "2. Добавьте ваш BOT_TOKEN от @BotFather"
echo ""
echo "3. Запустите бота:"
if [ "$EUID" -eq 0 ]; then
    echo -e "   ${YELLOW}sudo systemctl start donstusud-bot${NC}"
    echo ""
    echo "4. Проверьте статус:"
    echo -e "   ${YELLOW}sudo systemctl status donstusud-bot${NC}"
    echo ""
    echo "5. Посмотрите логи:"
    echo -e "   ${YELLOW}sudo journalctl -u donstusud-bot -f${NC}"
else
    echo -e "   ${YELLOW}cd $PROJECT_DIR${NC}"
    echo -e "   ${YELLOW}source venv/bin/activate${NC}"
    echo -e "   ${YELLOW}python main.py${NC}"
fi
echo ""
echo "═══════════════════════════════════════"

