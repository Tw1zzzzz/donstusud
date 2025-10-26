"""
Authentication and authorization middleware
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser, Message, CallbackQuery
import time
import logging

from database.db import Database
from database.models import ROLE_JUDGE, ROLE_ADMIN

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    """
    Middleware for user authentication and registration
    """
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Get Telegram user from event
        tg_user: TgUser = None
        if isinstance(event, Message):
            tg_user = event.from_user
        elif isinstance(event, CallbackQuery):
            tg_user = event.from_user
        
        if not tg_user:
            return await handler(event, data)
        
        # Get or create user in database
        user = await self.db.get_user(tg_user.id)
        if not user:
            user = await self.db.create_user(
                tg_user.id,
                tg_user.username,
                tg_user.first_name
            )
        
        # Add user to data for handlers
        data["user"] = user
        data["db"] = self.db
        
        return await handler(event, data)


class RoleMiddleware(BaseMiddleware):
    """
    Middleware for role-based access control
    """
    
    def __init__(self, required_role: str):
        super().__init__()
        self.required_role = required_role
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("user")
        
        if not user:
            logger.warning("RoleMiddleware: User not found in data")
            return
        
        # Check role
        if self.required_role == ROLE_JUDGE:
            # Judges and admins can access judge features
            if user.role not in [ROLE_JUDGE, ROLE_ADMIN]:
                if isinstance(event, Message):
                    await event.answer("❌ У вас нет доступа к этой функции")
                elif isinstance(event, CallbackQuery):
                    await event.answer("❌ У вас нет доступа к этой функции", show_alert=True)
                return
        elif self.required_role == ROLE_ADMIN:
            # Only admins can access admin features
            if user.role != ROLE_ADMIN:
                if isinstance(event, Message):
                    await event.answer("❌ Только администраторы могут использовать эту команду")
                elif isinstance(event, CallbackQuery):
                    await event.answer("❌ Только администраторы могут использовать эту команду", show_alert=True)
                return
        
        return await handler(event, data)


class RateLimitMiddleware(BaseMiddleware):
    """
    Rate limiting middleware to prevent spam
    """
    
    def __init__(self, max_requests: int, period: int):
        super().__init__()
        self.max_requests = max_requests
        self.period = period
        self.user_requests: Dict[int, list] = {}
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Get user ID
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        
        if not user_id:
            return await handler(event, data)
        
        current_time = time.time()
        
        # Initialize user request history
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        
        # Remove old requests
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if current_time - req_time < self.period
        ]
        
        # Check rate limit
        if len(self.user_requests[user_id]) >= self.max_requests:
            if isinstance(event, Message):
                await event.answer("⏳ Слишком много запросов. Пожалуйста, подождите немного.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⏳ Слишком много запросов. Подождите немного.", show_alert=True)
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return
        
        # Add current request
        self.user_requests[user_id].append(current_time)
        
        return await handler(event, data)

