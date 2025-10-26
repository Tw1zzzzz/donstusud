"""
FSM States for bot conversations
"""
from aiogram.fsm.state import State, StatesGroup


class TicketForm(StatesGroup):
    """States for creating a new ticket"""
    choosing_type = State()
    entering_description = State()
    confirming = State()


class CommentForm(StatesGroup):
    """States for adding a comment to a ticket"""
    entering_comment = State()

