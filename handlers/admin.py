"""
Handlers for admin actions
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
import logging

from database.db import Database
from database.models import User, ROLE_JUDGE, ROLE_PLAYER

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("add_judge"))
async def add_judge(message: Message, user: User, db: Database):
    """Add a judge (admin only)"""
    # Parse command
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ Неверный формат команды!\n\n"
            "Использование: /add_judge @username\n"
            "Пример: /add_judge @ivan"
        )
        return
    
    username = args[1].strip()
    
    # Remove @ if present
    if username.startswith("@"):
        username = username[1:]
    
    # Find user by username
    target_user = await db.get_user_by_username(username)
    
    if not target_user:
        await message.answer(
            f"❌ Пользователь @{username} не найден в базе данных.\n\n"
            "Пользователь должен сначала запустить бота командой /start"
        )
        return
    
    if target_user.role == ROLE_JUDGE:
        await message.answer(
            f"ℹ️ Пользователь @{username} уже является судьей."
        )
        return
    
    # Update role to judge
    await db.update_user_role(target_user.id, ROLE_JUDGE)
    
    await message.answer(
        f"✅ Пользователь @{username} ({target_user.first_name}) назначен судьей!"
    )
    
    # Notify the new judge
    try:
        await message.bot.send_message(
            target_user.id,
            f"🎉 Вы назначены судьей турнира!\n\n"
            f"Теперь у вас есть доступ к панели судьи.\n"
            f"Используйте /start для обновления меню."
        )
    except Exception as e:
        logger.error(f"Failed to notify new judge {target_user.id}: {e}")
    
    logger.info(f"Admin {user.id} added judge {target_user.id} (@{username})")


@router.message(Command("remove_judge"))
async def remove_judge(message: Message, user: User, db: Database):
    """Remove a judge (admin only)"""
    # Parse command
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ Неверный формат команды!\n\n"
            "Использование: /remove_judge @username\n"
            "Пример: /remove_judge @ivan"
        )
        return
    
    username = args[1].strip()
    
    # Remove @ if present
    if username.startswith("@"):
        username = username[1:]
    
    # Find user by username
    target_user = await db.get_user_by_username(username)
    
    if not target_user:
        await message.answer(
            f"❌ Пользователь @{username} не найден в базе данных."
        )
        return
    
    if target_user.role != ROLE_JUDGE:
        await message.answer(
            f"ℹ️ Пользователь @{username} не является судьей."
        )
        return
    
    # Cannot remove yourself
    if target_user.id == user.id:
        await message.answer(
            "❌ Вы не можете снять себя с должности судьи."
        )
        return
    
    # Update role to player
    await db.update_user_role(target_user.id, ROLE_PLAYER)
    
    await message.answer(
        f"✅ Пользователь @{username} ({target_user.first_name}) снят с должности судьи."
    )
    
    # Notify the removed judge
    try:
        await message.bot.send_message(
            target_user.id,
            f"ℹ️ Вы сняты с должности судьи турнира.\n\n"
            f"Используйте /start для обновления меню."
        )
    except Exception as e:
        logger.error(f"Failed to notify removed judge {target_user.id}: {e}")
    
    logger.info(f"Admin {user.id} removed judge {target_user.id} (@{username})")


@router.message(Command("list_judges"))
async def list_judges(message: Message, db: Database):
    """List all judges (admin only)"""
    judges = await db.get_judges()
    
    if not judges:
        await message.answer("ℹ️ Судей пока нет в системе.")
        return
    
    text = f"👨‍⚖️ Список судей ({len(judges)}):\n\n"
    
    for judge in judges:
        username = f"@{judge.username}" if judge.username else "нет username"
        role_emoji = "🔑" if judge.role == "admin" else "👨‍⚖️"
        text += f"{role_emoji} {judge.first_name} ({username})\n"
    
    await message.answer(text)


@router.message(Command("help"))
async def help_command(message: Message, user: User):
    """Show help information"""
    text = "📖 Справка по командам\n\n"
    
    text += "🎮 Команды для всех:\n"
    text += "/start - Главное меню\n"
    text += "/help - Эта справка\n\n"
    
    if user.role == "admin":
        text += "🔑 Команды администратора:\n"
        text += "/add_judge @username - Назначить судью\n"
        text += "/remove_judge @username - Снять судью\n"
        text += "/list_judges - Список всех судей\n"
    
    await message.answer(text)

