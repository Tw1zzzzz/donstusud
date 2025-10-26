"""
Database operations using aiosqlite
"""
import aiosqlite
from datetime import datetime
from typing import Optional, List
import logging

from database.models import (
    User, Ticket, Comment,
    ROLE_PLAYER, ROLE_ADMIN,
    TICKET_STATUS_OPEN, TICKET_STATUS_CLOSED
)

logger = logging.getLogger(__name__)


class Database:
    """Database class for managing SQLite operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    async def init_db(self):
        """Initialize database schema"""
        async with aiosqlite.connect(self.db_path) as db:
            # Create users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'player',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create tickets table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    ticket_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    closed_by INTEGER,
                    judge_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (closed_by) REFERENCES users(id),
                    FOREIGN KEY (judge_id) REFERENCES users(id)
                )
            """)
            
            # Create comments table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER NOT NULL,
                    judge_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ticket_id) REFERENCES tickets(id),
                    FOREIGN KEY (judge_id) REFERENCES users(id)
                )
            """)
            
            # Create indexes for performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_tickets_user_id ON tickets(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_tickets_judge_id ON tickets(judge_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_comments_ticket_id ON comments(ticket_id)")
            
            # Migration: Add judge_id column if it doesn't exist
            # Check if judge_id column exists
            cursor = await db.execute("PRAGMA table_info(tickets)")
            columns = [row[1] for row in await cursor.fetchall()]
            
            if 'judge_id' not in columns:
                logger.info("Column 'judge_id' not found, adding it now...")
                await db.execute("ALTER TABLE tickets ADD COLUMN judge_id INTEGER")
                logger.info("Successfully added judge_id column to tickets table")
            
            await db.commit()
            logger.info("Database initialized successfully")
    
    # User operations
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User(**dict(row))
                return None
    
    async def create_user(self, user_id: int, username: Optional[str], first_name: str) -> User:
        """Create new user. First user becomes admin."""
        async with aiosqlite.connect(self.db_path) as db:
            # Check if this is the first user
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                count = (await cursor.fetchone())[0]
                role = ROLE_ADMIN if count == 0 else ROLE_PLAYER
            
            await db.execute(
                "INSERT INTO users (id, username, first_name, role) VALUES (?, ?, ?, ?)",
                (user_id, username, first_name, role)
            )
            await db.commit()
            
            user = await self.get_user(user_id)
            logger.info(f"User created: {user_id} ({username}) with role {role}")
            return user
    
    async def update_user_role(self, user_id: int, role: str) -> bool:
        """Update user role"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET role = ? WHERE id = ?",
                (role, user_id)
            )
            await db.commit()
            logger.info(f"User {user_id} role updated to {role}")
            return True
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User(**dict(row))
                return None
    
    async def get_judges(self) -> List[User]:
        """Get all judges and admins"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE role IN ('judge', 'admin') ORDER BY created_at"
            ) as cursor:
                rows = await cursor.fetchall()
                return [User(**dict(row)) for row in rows]
    
    # Ticket operations
    async def create_ticket(
        self, user_id: int, ticket_type: str, description: str
    ) -> Ticket:
        """Create new ticket"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO tickets (user_id, ticket_type, description) VALUES (?, ?, ?)",
                (user_id, ticket_type, description)
            )
            await db.commit()
            ticket_id = cursor.lastrowid
            
            ticket = await self.get_ticket(ticket_id)
            logger.info(f"Ticket created: {ticket_id} by user {user_id}")
            return ticket
    
    async def get_ticket(self, ticket_id: int) -> Optional[Ticket]:
        """Get ticket by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Ticket(**dict(row))
                return None
    
    async def get_user_tickets(self, user_id: int, status: Optional[str] = None) -> List[Ticket]:
        """Get all tickets for a user, optionally filtered by status"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if status:
                query = "SELECT * FROM tickets WHERE user_id = ? AND status = ? ORDER BY created_at DESC"
                params = (user_id, status)
            else:
                query = "SELECT * FROM tickets WHERE user_id = ? ORDER BY created_at DESC"
                params = (user_id,)
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [Ticket(**dict(row)) for row in rows]
    
    async def get_all_tickets(self, status: Optional[str] = None) -> List[Ticket]:
        """Get all tickets, optionally filtered by status"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if status:
                query = "SELECT * FROM tickets WHERE status = ? ORDER BY created_at DESC"
                params = (status,)
            else:
                query = "SELECT * FROM tickets ORDER BY created_at DESC"
                params = ()
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [Ticket(**dict(row)) for row in rows]
    
    async def get_judge_tickets(self, judge_id: int, status: Optional[str] = None) -> List[Ticket]:
        """Get all tickets assigned to a specific judge, optionally filtered by status"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if status:
                query = "SELECT * FROM tickets WHERE judge_id = ? AND status = ? ORDER BY created_at DESC"
                params = (judge_id, status)
            else:
                query = "SELECT * FROM tickets WHERE judge_id = ? ORDER BY created_at DESC"
                params = (judge_id,)
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [Ticket(**dict(row)) for row in rows]
    
    async def update_ticket_status(
        self, ticket_id: int, status: str, closed_by: Optional[int] = None, judge_id: Optional[int] = None
    ) -> bool:
        """Update ticket status and optionally assign judge"""
        async with aiosqlite.connect(self.db_path) as db:
            closed_at = datetime.now() if status == TICKET_STATUS_CLOSED else None
            if judge_id is not None:
                await db.execute(
                    "UPDATE tickets SET status = ?, closed_at = ?, closed_by = ?, judge_id = ? WHERE id = ?",
                    (status, closed_at, closed_by, judge_id, ticket_id)
                )
            else:
                await db.execute(
                    "UPDATE tickets SET status = ?, closed_at = ?, closed_by = ? WHERE id = ?",
                    (status, closed_at, closed_by, ticket_id)
                )
            await db.commit()
            logger.info(f"Ticket {ticket_id} status updated to {status}")
            return True
    
    async def get_old_open_tickets(self, days: int) -> List[Ticket]:
        """Get tickets older than specified days that are still open or in progress"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM tickets 
                WHERE status IN ('open', 'in_progress') 
                AND datetime(created_at) <= datetime('now', '-' || ? || ' days')
                """,
                (days,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [Ticket(**dict(row)) for row in rows]
    
    # Comment operations
    async def create_comment(self, ticket_id: int, judge_id: int, text: str) -> Comment:
        """Create new comment on ticket"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO comments (ticket_id, judge_id, text) VALUES (?, ?, ?)",
                (ticket_id, judge_id, text)
            )
            await db.commit()
            comment_id = cursor.lastrowid
            
            comment = await self.get_comment(comment_id)
            logger.info(f"Comment created: {comment_id} on ticket {ticket_id}")
            return comment
    
    async def get_comment(self, comment_id: int) -> Optional[Comment]:
        """Get comment by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM comments WHERE id = ?", (comment_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Comment(**dict(row))
                return None
    
    async def get_ticket_comments(self, ticket_id: int) -> List[Comment]:
        """Get all comments for a ticket"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM comments WHERE ticket_id = ? ORDER BY created_at ASC",
                (ticket_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [Comment(**dict(row)) for row in rows]

