"""
Database models and schema definitions
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """User model"""
    id: int
    username: Optional[str]
    first_name: str
    role: str  # player, judge, admin
    created_at: datetime
    
    
@dataclass
class Ticket:
    """Ticket (complaint) model"""
    id: int
    user_id: int
    ticket_type: str  # match_reschedule, opponent_complaint, help_needed
    description: str
    status: str  # open, in_progress, closed
    created_at: datetime
    closed_at: Optional[datetime]
    closed_by: Optional[int]
    judge_id: Optional[int] = None  # Judge assigned to the ticket
    
    
@dataclass
class Comment:
    """Comment model for judge notes on tickets"""
    id: int
    ticket_id: int
    judge_id: int
    text: str
    created_at: datetime


# Ticket type constants
TICKET_TYPE_MATCH_RESCHEDULE = "match_reschedule"
TICKET_TYPE_OPPONENT_COMPLAINT = "opponent_complaint"
TICKET_TYPE_HELP_NEEDED = "help_needed"

TICKET_TYPES = {
    TICKET_TYPE_MATCH_RESCHEDULE: "Перенос матча",
    TICKET_TYPE_OPPONENT_COMPLAINT: "Жалоба на соперников",
    TICKET_TYPE_HELP_NEEDED: "Помощь в проблеме"
}

# Ticket status constants
TICKET_STATUS_OPEN = "open"
TICKET_STATUS_IN_PROGRESS = "in_progress"
TICKET_STATUS_CLOSED = "closed"

TICKET_STATUSES = {
    TICKET_STATUS_OPEN: "Открыта",
    TICKET_STATUS_IN_PROGRESS: "В работе",
    TICKET_STATUS_CLOSED: "Закрыта"
}

# User role constants
ROLE_PLAYER = "player"
ROLE_JUDGE = "judge"
ROLE_ADMIN = "admin"

