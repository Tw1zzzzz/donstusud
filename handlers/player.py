"""
Handlers for player actions
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
import logging

from database.db import Database
from database.models import User, TICKET_TYPES, TICKET_STATUSES, ROLE_JUDGE, ROLE_ADMIN
from keyboards.reply import (
    get_main_menu_keyboard,
    get_ticket_type_keyboard,
    get_confirm_ticket_keyboard,
    get_my_tickets_keyboard,
    get_ticket_detail_keyboard,
    get_back_to_menu_keyboard
)
from states.forms import TicketForm
from config import MAX_DESCRIPTION_LENGTH

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, user: User, db: Database):
    """Handle /start command"""
    is_judge = user.role in [ROLE_JUDGE, ROLE_ADMIN]
    
    if is_judge:
        # For judges: show tickets menu directly
        from keyboards.reply import get_judge_tickets_keyboard
        
        welcome_text = f"👋 Приветствуем тебя в саппорт боте Всероссийского турнира по фиджитал-спорту «Фиджитал — всем»\n\n"
        
        if user.role == ROLE_ADMIN:
            welcome_text += "🔑 Вы - администратор бота.\n"
        else:
            welcome_text += "👨‍⚖️ Вы - судья турнира.\n"
        
        welcome_text += "\n📋 Панель судьи\n\nВыберите фильтр для просмотра заявок:"
        
        await message.answer(
            welcome_text,
            reply_markup=get_judge_tickets_keyboard()
        )
    else:
        # For players: show regular menu
        welcome_text = f"👋 Приветствуем тебя в саппорт боте Всероссийского турнира по фиджитал-спорту «Фиджитал — всем»\n\n"
        welcome_text += "Вы можете:\n📝 Создать жалобу\n📋 Посмотреть свои заявки\n"
        
        await message.answer(
            welcome_text,
            reply_markup=get_main_menu_keyboard(is_judge=False)
        )


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, user: User, state: FSMContext):
    """Return to main menu"""
    await state.clear()
    
    is_judge = user.role in [ROLE_JUDGE, ROLE_ADMIN]
    
    if is_judge:
        # For judges: return to tickets filter menu
        from keyboards.reply import get_judge_tickets_keyboard
        await callback.message.edit_text(
            "👨‍⚖️ Панель судьи\n\nВыберите фильтр для просмотра заявок:",
            reply_markup=get_judge_tickets_keyboard()
        )
    else:
        # For players: return to main menu
        await callback.message.edit_text(
            "🏠 Главное меню\n\nВыберите действие:",
            reply_markup=get_main_menu_keyboard(is_judge=False)
        )
    
    await callback.answer()


@router.callback_query(F.data == "create_ticket")
async def create_ticket_start(callback: CallbackQuery, state: FSMContext):
    """Start ticket creation process"""
    await state.set_state(TicketForm.choosing_type)
    
    await callback.message.edit_text(
        "📝 Создание жалобы\n\n"
        "Выберите тип жалобы:",
        reply_markup=get_ticket_type_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ticket_type:"), TicketForm.choosing_type)
async def ticket_type_selected(callback: CallbackQuery, state: FSMContext):
    """Handle ticket type selection"""
    ticket_type = callback.data.split(":")[1]
    
    await state.update_data(ticket_type=ticket_type)
    await state.set_state(TicketForm.entering_description)
    
    type_name = TICKET_TYPES.get(ticket_type, "Неизвестный тип")
    
    await callback.message.edit_text(
        f"📝 Тип жалобы: {type_name}\n\n"
        f"Опишите вашу проблему (максимум {MAX_DESCRIPTION_LENGTH} символов):",
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()


@router.message(TicketForm.entering_description)
async def ticket_description_entered(message: Message, state: FSMContext):
    """Handle ticket description input"""
    description = message.text.strip()
    
    # Validate description length
    if len(description) > MAX_DESCRIPTION_LENGTH:
        await message.answer(
            f"❌ Описание слишком длинное! Максимум {MAX_DESCRIPTION_LENGTH} символов.\n"
            f"Ваше описание: {len(description)} символов.\n\n"
            "Пожалуйста, сократите описание и отправьте снова."
        )
        return
    
    if len(description) < 10:
        await message.answer(
            "❌ Описание слишком короткое! Минимум 10 символов.\n\n"
            "Пожалуйста, опишите проблему подробнее."
        )
        return
    
    await state.update_data(description=description)
    await state.set_state(TicketForm.confirming)
    
    # Get stored data
    data = await state.get_data()
    ticket_type = data.get("ticket_type")
    type_name = TICKET_TYPES.get(ticket_type, "Неизвестный тип")
    
    await message.answer(
        "✅ Проверьте данные перед отправкой:\n\n"
        f"📌 Тип: {type_name}\n"
        f"📝 Описание: {description}\n\n"
        "Отправить заявку?",
        reply_markup=get_confirm_ticket_keyboard()
    )


@router.callback_query(F.data == "confirm_ticket", TicketForm.confirming)
async def confirm_ticket(callback: CallbackQuery, user: User, db: Database, state: FSMContext):
    """Confirm and create ticket"""
    data = await state.get_data()
    ticket_type = data.get("ticket_type")
    description = data.get("description")
    
    # Create ticket
    ticket = await db.create_ticket(user.id, ticket_type, description)
    
    await state.clear()
    
    type_name = TICKET_TYPES.get(ticket_type, "Неизвестный тип")
    
    await callback.message.edit_text(
        f"✅ Заявка #{ticket.id} успешно создана!\n\n"
        f"📌 Тип: {type_name}\n"
        f"📝 Описание: {description}\n\n"
        "Судья свяжется с вами в ближайшее время.",
        reply_markup=get_back_to_menu_keyboard()
    )
    
    # Notify judges
    judges = await db.get_judges()
    for judge in judges:
        try:
            await callback.bot.send_message(
                judge.id,
                f"🔔 Новая заявка #{ticket.id}\n\n"
                f"👤 От: {user.first_name} (@{user.username or 'нет username'})\n"
                f"📌 Тип: {type_name}\n"
                f"📝 Описание: {description}"
            )
        except Exception as e:
            logger.error(f"Failed to notify judge {judge.id}: {e}")
    
    await callback.answer("✅ Заявка создана!")


@router.callback_query(F.data == "cancel_ticket")
async def cancel_ticket(callback: CallbackQuery, state: FSMContext):
    """Cancel ticket creation"""
    await state.clear()
    
    await callback.message.edit_text(
        "❌ Создание заявки отменено.",
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "my_tickets")
async def show_my_tickets(callback: CallbackQuery, user: User, db: Database):
    """Show user's tickets"""
    tickets = await db.get_user_tickets(user.id)
    
    try:
        if not tickets:
            await callback.message.edit_text(
                "📋 У вас пока нет заявок.\n\n"
                "Создайте новую заявку, если у вас возникла проблема.",
                reply_markup=get_back_to_menu_keyboard()
            )
        else:
            await callback.message.edit_text(
                f"📋 Ваши заявки ({len(tickets)}):\n\n"
                "Выберите заявку для просмотра:",
                reply_markup=get_my_tickets_keyboard(tickets, page=0)
            )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer("Список заявок не изменился")
            return
        else:
            raise
    
    await callback.answer()


@router.callback_query(F.data.startswith("my_tickets_page:"))
async def my_tickets_pagination(callback: CallbackQuery, user: User, db: Database):
    """Handle pagination for my tickets"""
    page = int(callback.data.split(":")[1])
    
    tickets = await db.get_user_tickets(user.id)
    
    try:
        await callback.message.edit_text(
            f"📋 Ваши заявки ({len(tickets)}):\n\n"
            "Выберите заявку для просмотра:",
            reply_markup=get_my_tickets_keyboard(tickets, page=page)
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer("Страница не изменилась")
            return
        else:
            raise
    
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    """Handle noop callback (pagination indicator)"""
    await callback.answer()


@router.callback_query(F.data.startswith("view_my_ticket:"))
async def view_my_ticket(callback: CallbackQuery, user: User, db: Database):
    """View ticket details"""
    ticket_id = int(callback.data.split(":")[1])
    
    ticket = await db.get_ticket(ticket_id)
    
    if not ticket or ticket.user_id != user.id:
        await callback.answer("❌ Заявка не найдена", show_alert=True)
        return
    
    # Get comments
    comments = await db.get_ticket_comments(ticket_id)
    
    # Get assigned judge info
    judge_info = ""
    if ticket.judge_id:
        assigned_judge = await db.get_user(ticket.judge_id)
        if assigned_judge:
            judge_info = f"👨‍⚖️ Судья: {assigned_judge.first_name}\n"
    
    type_name = TICKET_TYPES.get(ticket.ticket_type, "Неизвестно")
    status_name = TICKET_STATUSES.get(ticket.status, "Неизвестно")
    
    text = (
        f"📋 Заявка #{ticket.id}\n\n"
        f"📌 Тип: {type_name}\n"
        f"📊 Статус: {status_name}\n"
        f"{judge_info}"
        f"📅 Создана: {ticket.created_at}\n"
        f"📝 Описание:\n{ticket.description}\n"
    )
    
    if comments:
        text += f"\n💬 Комментарии судей ({len(comments)}):\n"
        for comment in comments:
            judge = await db.get_user(comment.judge_id)
            judge_name = judge.first_name if judge else "Судья"
            text += f"\n• {judge_name}: {comment.text}\n  ({comment.created_at})"
    
    if ticket.closed_at:
        text += f"\n\n🔒 Закрыта: {ticket.closed_at}"
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_ticket_detail_keyboard(ticket, is_owner=True)
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer("Заявка не изменилась")
            return
        else:
            raise
    await callback.answer()


@router.callback_query(F.data.startswith("close_ticket:"))
async def close_ticket(callback: CallbackQuery, user: User, db: Database):
    """Close ticket by owner"""
    ticket_id = int(callback.data.split(":")[1])
    
    ticket = await db.get_ticket(ticket_id)
    
    if not ticket or ticket.user_id != user.id:
        await callback.answer("❌ Заявка не найдена", show_alert=True)
        return
    
    if ticket.status == "closed":
        await callback.answer("❌ Заявка уже закрыта", show_alert=True)
        return
    
    # Close ticket
    await db.update_ticket_status(ticket_id, "closed", user.id)
    
    await callback.message.edit_text(
        f"✅ Заявка #{ticket_id} закрыта.",
        reply_markup=get_back_to_menu_keyboard()
    )
    
    # Notify judges
    judges = await db.get_judges()
    for judge in judges:
        try:
            await callback.bot.send_message(
                judge.id,
                f"🔒 Заявка #{ticket_id} закрыта игроком {user.first_name}"
            )
        except Exception as e:
            logger.error(f"Failed to notify judge {judge.id}: {e}")
    
    await callback.answer("✅ Заявка закрыта")

