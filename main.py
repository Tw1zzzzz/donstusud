"""
CS2 Judge Bot - Main entry point
Telegram bot for handling player complaints during CS2 tournaments
"""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, DB_PATH, RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_PERIOD, LOG_LEVEL
from database.db import Database
from middlewares.auth import AuthMiddleware, RoleMiddleware, RateLimitMiddleware
from database.models import ROLE_JUDGE, ROLE_ADMIN
from utils.scheduler import TicketScheduler

# Import handlers
from handlers import player, judge, admin

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to start the bot"""
    logger.info("Starting CS2 Judge Bot...")
    
    # Initialize database
    db = Database(DB_PATH)
    await db.init_db()
    logger.info("Database initialized")
    
    # Initialize bot and dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Register middlewares
    # Auth middleware for all handlers
    dp.message.middleware(AuthMiddleware(db))
    dp.callback_query.middleware(AuthMiddleware(db))
    
    # Rate limiting middleware
    dp.message.middleware(RateLimitMiddleware(RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_PERIOD))
    dp.callback_query.middleware(RateLimitMiddleware(RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_PERIOD))
    
    # Register player handlers (available to all users)
    dp.include_router(player.router)
    
    # Register judge handlers with role check
    judge.router.message.middleware(RoleMiddleware(ROLE_JUDGE))
    judge.router.callback_query.middleware(RoleMiddleware(ROLE_JUDGE))
    dp.include_router(judge.router)
    
    # Register admin handlers with role check
    admin.router.message.middleware(RoleMiddleware(ROLE_ADMIN))
    dp.include_router(admin.router)
    
    # Initialize and start scheduler
    scheduler = TicketScheduler(db, bot)
    scheduler.start()
    logger.info("Scheduler started")
    
    try:
        # Start polling
        logger.info("Bot started successfully!")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        # Cleanup
        scheduler.stop()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

