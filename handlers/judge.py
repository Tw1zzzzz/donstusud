"""
Handlers for judge actions
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
import logging

from database.db import Database
from database.models import (
    User, TICKET_TYPES, TICKET_STATUSES,
    TICKET_STATUS_OPEN, TICKET_STATUS_IN_PROGRESS,
    TICKET_STATUS_CLOSED
)
from keyboards.reply import (
    get_judge_tickets_keyboard,
    get_judge_ticket_list_keyboard,
    get_judge_ticket_actions_keyboard,
    get_cancel_keyboard,
    get_back_to_menu_keyboard
)
from states.forms import CommentForm
from config import MAX_COMMENT_LENGTH

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "judge_tickets")
async def judge_tickets_menu(callback: CallbackQuery):
    """Show judge tickets menu"""
    await callback.message.edit_text(
        "👨‍⚖️ Панель судьи\n\n"
        "Выберите фильтр для просмотра заявок:",
        reply_markup=get_judge_tickets_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("judge_filter:"))
async def judge_filter_tickets(callback: CallbackQuery, user: User, db: Database):
    """Filter tickets for judges"""
    filter_type = callback.data.split(":")[1]
    
    # Get tickets based on filter
    if filter_type == "open":
        tickets = await db.get_all_tickets(TICKET_STATUS_OPEN)
        filter_name = "Открытые"
    elif filter_type == "in_progress":
        tickets = await db.get_all_tickets(TICKET_STATUS_IN_PROGRESS)
        filter_name = "В работе"
    elif filter_type == "my_tickets":
        tickets = await db.get_judge_tickets(user.id, TICKET_STATUS_IN_PROGRESS)
        filter_name = "Мои в работе"
    else:  # all
        tickets = await db.get_all_tickets()
        filter_name = "Все"
    
    if not tickets:
        try:
            await callback.message.edit_text(
                f"📋 {filter_name} заявки\n\n"
                "Нет заявок в этой категории.",
                reply_markup=get_judge_tickets_keyboard()
            )
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback.answer("Список заявок не изменился")
            else:
                raise
    else:
        try:
            await callback.message.edit_text(
                f"📋 {filter_name} заявки ({len(tickets)}):\n\n"
                "Выберите заявку для просмотра:",
                reply_markup=get_judge_ticket_list_keyboard(tickets, filter_type, page=0)
            )
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback.answer("Список заявок не изменился")
            else:
                raise
    
    await callback.answer()


@router.callback_query(F.data.startswith("judge_page:"))
async def judge_tickets_pagination(callback: CallbackQuery, user: User, db: Database):
    """Handle pagination for judge tickets"""
    parts = callback.data.split(":")
    filter_type = parts[1]
    page = int(parts[2])
    
    # Get tickets based on filter
    if filter_type == "open":
        tickets = await db.get_all_tickets(TICKET_STATUS_OPEN)
        filter_name = "Открытые"
    elif filter_type == "in_progress":
        tickets = await db.get_all_tickets(TICKET_STATUS_IN_PROGRESS)
        filter_name = "В работе"
    elif filter_type == "my_tickets":
        tickets = await db.get_judge_tickets(user.id, TICKET_STATUS_IN_PROGRESS)
        filter_name = "Мои в работе"
    else:  # all
        tickets = await db.get_all_tickets()
        filter_name = "Все"
    
    try:
        await callback.message.edit_text(
            f"📋 {filter_name} заявки ({len(tickets)}):\n\n"
            "Выберите заявку для просмотра:",
            reply_markup=get_judge_ticket_list_keyboard(tickets, filter_type, page=page)
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer("Страница не изменилась")
        else:
            raise
    
    await callback.answer()


@router.callback_query(F.data.startswith("judge_view_ticket:"))
async def judge_view_ticket(callback: CallbackQuery, db: Database):
    """View ticket details as judge"""
    ticket_id = int(callback.data.split(":")[1])
    
    ticket = await db.get_ticket(ticket_id)
    
    if not ticket:
        await callback.answer("❌ Заявка не найдена", show_alert=True)
        return
    
    # Get ticket owner
    owner = await db.get_user(ticket.user_id)
    owner_name = owner.first_name if owner else "Неизвестный"
    owner_username = f"@{owner.username}" if owner and owner.username else "нет username"
    
    # Get assigned judge
    judge_info = ""
    if ticket.judge_id:
        assigned_judge = await db.get_user(ticket.judge_id)
        if assigned_judge:
            judge_info = f"👨‍⚖️ Судья: {assigned_judge.first_name}\n"
    
    # Get comments
    comments = await db.get_ticket_comments(ticket_id)
    
    type_name = TICKET_TYPES.get(ticket.ticket_type, "Неизвестно")
    status_name = TICKET_STATUSES.get(ticket.status, "Неизвестно")
    
    text = (
        f"📋 Заявка #{ticket.id}\n\n"
        f"👤 Игрок: {owner_name} ({owner_username})\n"
        f"📞 Контакт: {owner_username}\n"
        f"{judge_info}\n"
        f"📌 Тип: {type_name}\n"
        f"📊 Статус: {status_name}\n"
        f"📅 Создана: {ticket.created_at}\n"
        f"📝 Описание:\n{ticket.description}\n"
    )
    
    if comments:
        text += f"\n💬 Комментарии ({len(comments)}):\n"
        for comment in comments:
            judge = await db.get_user(comment.judge_id)
            judge_name = judge.first_name if judge else "Судья"
            text += f"\n• {judge_name}: {comment.text}\n  ({comment.created_at})"
    
    if ticket.closed_at:
        closer = await db.get_user(ticket.closed_by) if ticket.closed_by else None
        closer_name = closer.first_name if closer else "Система"
        text += f"\n\n🔒 Закрыта: {ticket.closed_at}\n   Кем: {closer_name}"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_judge_ticket_actions_keyboard(ticket)
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer("Заявка не изменилась")
        else:
            raise
    await callback.answer()


@router.callback_query(F.data.startswith("take_ticket:"))
async def take_ticket(callback: CallbackQuery, user: User, db: Database):
    """Take ticket into work"""
    ticket_id = int(callback.data.split(":")[1])
    
    ticket = await db.get_ticket(ticket_id)
    
    if not ticket:
        await callback.answer("❌ Заявка не найдена", show_alert=True)
        return
    
    if ticket.status != TICKET_STATUS_OPEN:
        await callback.answer("❌ Заявка уже взята в работу", show_alert=True)
        return
    
    # Update status and assign judge
    await db.update_ticket_status(ticket_id, TICKET_STATUS_IN_PROGRESS, judge_id=user.id)
    
    # Add automatic comment
    await db.create_comment(
        ticket_id,
        user.id,
        f"Заявка взята в работу судьей {user.first_name}"
    )
    
    # Notify ticket owner
    owner = await db.get_user(ticket.user_id)
    if owner:
        try:
            await callback.bot.send_message(
                owner.id,
                f"🟡 Ваша заявка #{ticket_id} взята в работу судьей {user.first_name}"
            )
        except Exception as e:
            logger.error(f"Failed to notify ticket owner {owner.id}: {e}")
    
    await callback.answer("✅ Заявка взята в работу")
    
    # Refresh ticket view
    await judge_view_ticket(callback, db)


@router.callback_query(F.data.startswith("add_comment:"))
async def start_add_comment(callback: CallbackQuery, state: FSMContext):
    """Start adding comment to ticket"""
    ticket_id = int(callback.data.split(":")[1])
    
    await state.update_data(comment_ticket_id=ticket_id)
    await state.set_state(CommentForm.entering_comment)
    
    await callback.message.edit_text(
        f"💬 Добавление комментария к заявке #{ticket_id}\n\n"
        f"Введите ваш комментарий (максимум {MAX_COMMENT_LENGTH} символов):",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(CommentForm.entering_comment)
async def comment_entered(message: Message, user: User, db: Database, state: FSMContext):
    """Handle comment input"""
    comment_text = message.text.strip()
    
    # Validate comment length
    if len(comment_text) > MAX_COMMENT_LENGTH:
        await message.answer(
            f"❌ Комментарий слишком длинный! Максимум {MAX_COMMENT_LENGTH} символов.\n"
            f"Ваш комментарий: {len(comment_text)} символов.\n\n"
            "Пожалуйста, сократите комментарий и отправьте снова."
        )
        return
    
    if len(comment_text) < 3:
        await message.answer(
            "❌ Комментарий слишком короткий! Минимум 3 символа."
        )
        return
    
    # Get ticket ID from state
    data = await state.get_data()
    ticket_id = data.get("comment_ticket_id")
    
    # Create comment
    await db.create_comment(ticket_id, user.id, comment_text)
    
    await state.clear()
    
    # Notify ticket owner
    ticket = await db.get_ticket(ticket_id)
    if ticket:
        owner = await db.get_user(ticket.user_id)
        if owner:
            try:
                await message.bot.send_message(
                    owner.id,
                    f"💬 Новый комментарий к вашей заявке #{ticket_id}\n\n"
                    f"Судья {user.first_name}: {comment_text}"
                )
            except Exception as e:
                logger.error(f"Failed to notify ticket owner {owner.id}: {e}")
    
    from keyboards.reply import get_judge_ticket_actions_keyboard
    
    await message.answer(
        f"✅ Комментарий добавлен к заявке #{ticket_id}",
        reply_markup=get_judge_ticket_actions_keyboard(ticket) if ticket else get_back_to_menu_keyboard()
    )


@router.callback_query(F.data == "cancel", CommentForm.entering_comment)
async def cancel_comment(callback: CallbackQuery, db: Database, state: FSMContext):
    """Cancel adding comment"""
    data = await state.get_data()
    ticket_id = data.get("comment_ticket_id")
    
    await state.clear()
    
    # Return to ticket view if we have ticket_id
    if ticket_id:
        ticket = await db.get_ticket(ticket_id)
        if ticket:
            from keyboards.reply import get_judge_ticket_actions_keyboard
            await callback.message.edit_text(
                "❌ Добавление комментария отменено.",
                reply_markup=get_judge_ticket_actions_keyboard(ticket)
            )
            await callback.answer()
            return
    
    # Fallback to menu
    from keyboards.reply import get_back_to_menu_keyboard
    await callback.message.edit_text(
        "❌ Добавление комментария отменено.",
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("judge_close_ticket:"))
async def judge_close_ticket(callback: CallbackQuery, user: User, db: Database):
    """Close ticket as judge"""
    ticket_id = int(callback.data.split(":")[1])
    
    ticket = await db.get_ticket(ticket_id)
    
    if not ticket:
        await callback.answer("❌ Заявка не найдена", show_alert=True)
        return
    
    if ticket.status == TICKET_STATUS_CLOSED:
        await callback.answer("❌ Заявка уже закрыта", show_alert=True)
        return
    
    # Close ticket
    await db.update_ticket_status(ticket_id, TICKET_STATUS_CLOSED, user.id)
    
    # Add automatic comment
    await db.create_comment(
        ticket_id,
        user.id,
        f"Заявка закрыта судьей {user.first_name}"
    )
    
    # Notify ticket owner
    owner = await db.get_user(ticket.user_id)
    if owner:
        try:
            await callback.bot.send_message(
                owner.id,
                f"🔒 Ваша заявка #{ticket_id} закрыта судьей {user.first_name}"
            )
        except Exception as e:
            logger.error(f"Failed to notify ticket owner {owner.id}: {e}")
    
    await callback.message.edit_text(
        f"✅ Заявка #{ticket_id} закрыта."
    )
    await callback.answer("✅ Заявка закрыта")

