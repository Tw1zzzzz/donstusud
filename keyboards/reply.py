"""
Inline keyboards for the bot
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List

from database.models import (
    TICKET_TYPE_MATCH_RESCHEDULE,
    TICKET_TYPE_OPPONENT_COMPLAINT, 
    TICKET_TYPE_HELP_NEEDED,
    TICKET_TYPES,
    TICKET_STATUS_OPEN,
    TICKET_STATUS_IN_PROGRESS,
    TICKET_STATUS_CLOSED,
    Ticket
)


def get_main_menu_keyboard(is_judge: bool = False) -> InlineKeyboardMarkup:
    """Main menu keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📝 Создать жалобу", callback_data="create_ticket")
    )
    
    if is_judge:
        # For judges: only show "All tickets" button, they can use "My tickets" filter there
        builder.row(
            InlineKeyboardButton(text="👨‍⚖️ Все заявки", callback_data="judge_tickets")
        )
    else:
        # For players: show "My tickets" button to see their created tickets
        builder.row(
            InlineKeyboardButton(text="📋 Мои заявки", callback_data="my_tickets")
        )
    
    return builder.as_markup()


def get_ticket_type_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting ticket type"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🔄 " + TICKET_TYPES[TICKET_TYPE_MATCH_RESCHEDULE],
            callback_data=f"ticket_type:{TICKET_TYPE_MATCH_RESCHEDULE}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⚠️ " + TICKET_TYPES[TICKET_TYPE_OPPONENT_COMPLAINT],
            callback_data=f"ticket_type:{TICKET_TYPE_OPPONENT_COMPLAINT}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❓ " + TICKET_TYPES[TICKET_TYPE_HELP_NEEDED],
            callback_data=f"ticket_type:{TICKET_TYPE_HELP_NEEDED}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="back_to_menu")
    )
    
    return builder.as_markup()


def get_confirm_ticket_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for confirming ticket creation"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Отправить", callback_data="confirm_ticket"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_ticket")
    )
    
    return builder.as_markup()


def get_my_tickets_keyboard(tickets: List[Ticket], page: int = 0, per_page: int = 10) -> InlineKeyboardMarkup:
    """Keyboard showing user's tickets with pagination"""
    builder = InlineKeyboardBuilder()
    
    if not tickets:
        builder.row(
            InlineKeyboardButton(text="« Назад в меню", callback_data="back_to_menu")
        )
        return builder.as_markup()
    
    # Calculate pagination
    total_pages = (len(tickets) - 1) // per_page + 1
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(tickets))
    page_tickets = tickets[start_idx:end_idx]
    
    for ticket in page_tickets:
        status_emoji = {
            TICKET_STATUS_OPEN: "🟢",
            TICKET_STATUS_IN_PROGRESS: "🟡",
            TICKET_STATUS_CLOSED: "⚫"
        }.get(ticket.status, "❓")
        
        builder.row(
            InlineKeyboardButton(
                text=f"{status_emoji} #{ticket.id} - {TICKET_TYPES.get(ticket.ticket_type, 'Неизвестно')}",
                callback_data=f"view_my_ticket:{ticket.id}"
            )
        )
    
    # Add pagination buttons if needed
    if total_pages > 1:
        pagination_row = []
        if page > 0:
            pagination_row.append(
                InlineKeyboardButton(text="⬅️ Пред.", callback_data=f"my_tickets_page:{page-1}")
            )
        pagination_row.append(
            InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop")
        )
        if page < total_pages - 1:
            pagination_row.append(
                InlineKeyboardButton(text="След. ➡️", callback_data=f"my_tickets_page:{page+1}")
            )
        builder.row(*pagination_row)
    
    # Add refresh button
    builder.row(
        InlineKeyboardButton(text="🔄 Обновить", callback_data="my_tickets")
    )
    
    builder.row(
        InlineKeyboardButton(text="« Назад в меню", callback_data="back_to_menu")
    )
    
    return builder.as_markup()


def get_ticket_detail_keyboard(ticket: Ticket, is_owner: bool = False) -> InlineKeyboardMarkup:
    """Keyboard for ticket details"""
    builder = InlineKeyboardBuilder()
    
    if is_owner and ticket.status != TICKET_STATUS_CLOSED:
        builder.row(
            InlineKeyboardButton(text="🔒 Закрыть заявку", callback_data=f"close_ticket:{ticket.id}")
        )
    
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="my_tickets")
    )
    
    return builder.as_markup()


def get_judge_tickets_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for judge ticket filters - this IS the main menu for judges"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🟢 Открытые", callback_data="judge_filter:open")
    )
    builder.row(
        InlineKeyboardButton(text="🟡 В работе", callback_data="judge_filter:in_progress")
    )
    builder.row(
        InlineKeyboardButton(text="👨‍⚖️ Мои в работе", callback_data="judge_filter:my_tickets")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Все заявки", callback_data="judge_filter:all")
    )
    # No "Back to menu" button - this IS the main menu for judges
    
    return builder.as_markup()


def get_judge_ticket_list_keyboard(tickets: List[Ticket], filter_type: str, page: int = 0, per_page: int = 10) -> InlineKeyboardMarkup:
    """Keyboard showing tickets list for judges with pagination"""
    builder = InlineKeyboardBuilder()
    
    if not tickets:
        builder.row(
            InlineKeyboardButton(text="« Назад", callback_data="judge_tickets")
        )
        return builder.as_markup()
    
    # Calculate pagination
    total_pages = (len(tickets) - 1) // per_page + 1
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(tickets))
    page_tickets = tickets[start_idx:end_idx]
    
    for ticket in page_tickets:
        status_emoji = {
            TICKET_STATUS_OPEN: "🟢",
            TICKET_STATUS_IN_PROGRESS: "🟡",
            TICKET_STATUS_CLOSED: "⚫"
        }.get(ticket.status, "❓")
        
        builder.row(
            InlineKeyboardButton(
                text=f"{status_emoji} #{ticket.id} - {TICKET_TYPES.get(ticket.ticket_type, 'Неизвестно')}",
                callback_data=f"judge_view_ticket:{ticket.id}"
            )
        )
    
    # Add pagination buttons if needed
    if total_pages > 1:
        pagination_row = []
        if page > 0:
            pagination_row.append(
                InlineKeyboardButton(text="⬅️ Пред.", callback_data=f"judge_page:{filter_type}:{page-1}")
            )
        pagination_row.append(
            InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop")
        )
        if page < total_pages - 1:
            pagination_row.append(
                InlineKeyboardButton(text="След. ➡️", callback_data=f"judge_page:{filter_type}:{page+1}")
            )
        builder.row(*pagination_row)
    
    # Add refresh button
    builder.row(
        InlineKeyboardButton(text="🔄 Обновить", callback_data=f"judge_filter:{filter_type}")
    )
    
    builder.row(
        InlineKeyboardButton(text="« Главное меню", callback_data="back_to_menu")
    )
    
    return builder.as_markup()


def get_judge_ticket_actions_keyboard(ticket: Ticket) -> InlineKeyboardMarkup:
    """Keyboard for judge actions on a ticket"""
    builder = InlineKeyboardBuilder()
    
    if ticket.status == TICKET_STATUS_OPEN:
        builder.row(
            InlineKeyboardButton(text="✋ Взять в работу", callback_data=f"take_ticket:{ticket.id}")
        )
    
    if ticket.status != TICKET_STATUS_CLOSED:
        builder.row(
            InlineKeyboardButton(text="💬 Добавить комментарий", callback_data=f"add_comment:{ticket.id}")
        )
        builder.row(
            InlineKeyboardButton(text="🔒 Закрыть заявку", callback_data=f"judge_close_ticket:{ticket.id}")
        )
    
    builder.row(
        InlineKeyboardButton(text="« Главное меню", callback_data="back_to_menu")
    )
    
    return builder.as_markup()


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Simple back to menu keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="« Назад в меню", callback_data="back_to_menu")
    )
    
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Cancel current operation keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    
    return builder.as_markup()

