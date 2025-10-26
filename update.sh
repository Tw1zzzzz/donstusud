#!/bin/bash
# 🔄 Скрипт обновления Telegram бота

set -e  # Остановка при ошибке

echo "═══════════════════════════════════════"
echo "   🔄 Обновление DonsTusud Bot"
echo "═══════════════════════════════════════"

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_DIR="$HOME/donstusud"
SERVICE_NAME="donstusud-bot.service"

# Проверка существования проекта
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ Проект не найден в $PROJECT_DIR${NC}"
    echo -e "${YELLOW}   Сначала выполните деплой: ./deploy.sh${NC}"
    exit 1
fi

cd "$PROJECT_DIR"

echo -e "${YELLOW}📦 Шаг 1/6: Проверка обновлений...${NC}"
git fetch origin

LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})

if [ "$LOCAL" = "$REMOTE" ]; then
    echo -e "${GREEN}✅ Вы используете последнюю версию!${NC}"
    read -p "Продолжить обновление зависимостей? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}ℹ️  Обновление отменено${NC}"
        exit 0
    fi
else
    echo -e "${YELLOW}📥 Найдены новые изменения${NC}"
fi

echo -e "${YELLOW}📦 Шаг 2/6: Создание резервной копии...${NC}"
BACKUP_DIR="$PROJECT_DIR/backups"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Бэкап базы данных
if [ -f "bot.db" ]; then
    cp bot.db "$BACKUP_DIR/bot_${TIMESTAMP}.db"
    echo -e "${GREEN}✅ База данных сохранена: backups/bot_${TIMESTAMP}.db${NC}"
fi

# Бэкап конфигурации
if [ -f ".env" ]; then
    cp .env "$BACKUP_DIR/.env_${TIMESTAMP}"
    echo -e "${GREEN}✅ Конфигурация сохранена${NC}"
fi

echo -e "${YELLOW}📦 Шаг 3/6: Остановка бота...${NC}"
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    if [ "$EUID" -eq 0 ]; then
        systemctl stop "$SERVICE_NAME"
        echo -e "${GREEN}✅ Бот остановлен (systemd)${NC}"
    else
        sudo systemctl stop "$SERVICE_NAME"
        echo -e "${GREEN}✅ Бот остановлен (systemd)${NC}"
    fi
else
    # Попытка остановить через kill
    BOT_PID=$(ps aux | grep "[p]ython.*main.py" | awk '{print $2}')
    if [ ! -z "$BOT_PID" ]; then
        kill "$BOT_PID" 2>/dev/null || sudo kill "$BOT_PID"
        echo -e "${GREEN}✅ Бот остановлен (PID: $BOT_PID)${NC}"
    else
        echo -e "${BLUE}ℹ️  Бот не запущен${NC}"
    fi
fi

sleep 2

echo -e "${YELLOW}📦 Шаг 4/6: Получение обновлений...${NC}"
git pull origin master
echo -e "${GREEN}✅ Код обновлен${NC}"

echo -e "${YELLOW}📦 Шаг 5/6: Обновление зависимостей...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --upgrade
echo -e "${GREEN}✅ Зависимости обновлены${NC}"

echo -e "${YELLOW}📦 Шаг 6/6: Запуск бота...${NC}"
if systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
    if [ "$EUID" -eq 0 ]; then
        systemctl start "$SERVICE_NAME"
    else
        sudo systemctl start "$SERVICE_NAME"
    fi
    echo -e "${GREEN}✅ Бот запущен (systemd)${NC}"
    
    # Проверка статуса
    sleep 2
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "${GREEN}✅ Бот работает нормально${NC}"
    else
        echo -e "${RED}❌ Ошибка запуска. Проверьте логи:${NC}"
        echo -e "${YELLOW}   sudo journalctl -u $SERVICE_NAME -n 50${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Systemd сервис не настроен${NC}"
    echo -e "${YELLOW}   Запустите бота вручную:${NC}"
    echo -e "${YELLOW}   cd $PROJECT_DIR && source venv/bin/activate && python main.py${NC}"
fi

echo ""
echo "═══════════════════════════════════════"
echo -e "${GREEN}   ✅ Обновление завершено!${NC}"
echo "═══════════════════════════════════════"
echo ""
echo "📋 Полезные команды:"
echo ""
echo "Статус бота:"
echo -e "   ${YELLOW}sudo systemctl status $SERVICE_NAME${NC}"
echo ""
echo "Логи в реальном времени:"
echo -e "   ${YELLOW}sudo journalctl -u $SERVICE_NAME -f${NC}"
echo ""
echo "Последние 50 строк логов:"
echo -e "   ${YELLOW}sudo journalctl -u $SERVICE_NAME -n 50${NC}"
echo ""
echo "Перезапуск бота:"
echo -e "   ${YELLOW}sudo systemctl restart $SERVICE_NAME${NC}"
echo ""
echo "Восстановить из резервной копии:"
echo -e "   ${YELLOW}cp $BACKUP_DIR/bot_${TIMESTAMP}.db bot.db${NC}"
echo ""
echo "═══════════════════════════════════════"

