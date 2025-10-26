"""
Scheduler for automatic ticket closing
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
import logging

from database.db import Database
from database.models import TICKET_STATUS_CLOSED
from config import AUTO_CLOSE_DAYS

logger = logging.getLogger(__name__)


class TicketScheduler:
    """Scheduler for automatic ticket operations"""
    
    def __init__(self, db: Database, bot: Bot):
        self.db = db
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
    
    async def close_old_tickets(self):
        """Close tickets older than AUTO_CLOSE_DAYS"""
        try:
            old_tickets = await self.db.get_old_open_tickets(AUTO_CLOSE_DAYS)
            
            if not old_tickets:
                logger.info("No old tickets to close")
                return
            
            logger.info(f"Found {len(old_tickets)} old tickets to close")
            
            for ticket in old_tickets:
                # Close ticket
                await self.db.update_ticket_status(
                    ticket.id,
                    TICKET_STATUS_CLOSED,
                    closed_by=None  # System closed
                )
                
                # Add system comment
                await self.db.create_comment(
                    ticket.id,
                    ticket.user_id,  # Using user_id as placeholder for system
                    f"Заявка автоматически закрыта через {AUTO_CLOSE_DAYS} дней неактивности"
                )
                
                # Notify ticket owner
                try:
                    await self.bot.send_message(
                        ticket.user_id,
                        f"🔒 Ваша заявка #{ticket.id} автоматически закрыта.\n\n"
                        f"Причина: прошло {AUTO_CLOSE_DAYS} дней с момента создания.\n\n"
                        f"Если проблема не решена, создайте новую заявку."
                    )
                except Exception as e:
                    logger.error(f"Failed to notify ticket owner {ticket.user_id}: {e}")
                
                # Notify judges
                judges = await self.db.get_judges()
                for judge in judges:
                    try:
                        await self.bot.send_message(
                            judge.id,
                            f"🔒 Заявка #{ticket.id} автоматически закрыта системой "
                            f"(неактивна {AUTO_CLOSE_DAYS} дней)"
                        )
                    except Exception as e:
                        logger.error(f"Failed to notify judge {judge.id}: {e}")
                
                logger.info(f"Ticket {ticket.id} automatically closed")
        
        except Exception as e:
            logger.error(f"Error in close_old_tickets: {e}", exc_info=True)
    
    def start(self):
        """Start the scheduler"""
        # Run ticket closing check every hour
        self.scheduler.add_job(
            self.close_old_tickets,
            'interval',
            hours=1,
            id='close_old_tickets',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

