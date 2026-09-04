"""
Sovereign AI Workbench — Session Manager

Handles in-memory conversational memory for multi-turn chats.
Provides sliding window truncation so context doesn't explode.

Phase 5: In-memory store (to be upgraded to SQLite/Redis later).
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid

logger = logging.getLogger("sovereign.session_manager")


@dataclass
class ChatMessage:
    """A single message in a conversation session."""
    role: str
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


class SessionManager:
    """Manages chat histories for active sessions."""

    def __init__(self, max_history_messages: int = 20):
        # Maps session_id to list of ChatMessages
        self._sessions: dict[str, list[ChatMessage]] = defaultdict(list)
        self.max_history_messages = max_history_messages

    def create_session(self) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = []
        logger.debug("Created new session: %s", session_id)
        return session_id

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Append a message to a session's history."""
        if not content:
            return
            
        history = self._sessions[session_id]
        history.append(ChatMessage(role=role, content=content))
        
        # Sliding window truncation
        if len(history) > self.max_history_messages:
            # We want to keep the most recent messages.
            # If we enforce a strict max, we might truncate the oldest user message but keep its response.
            # Usually, you'd want to keep complete turns, but simple truncation works for now.
            logger.debug("Truncating session %s to %d messages", session_id, self.max_history_messages)
            self._sessions[session_id] = history[-self.max_history_messages:]

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        """Retrieve the formatted history for a session."""
        if session_id not in self._sessions:
            return []
            
        return [msg.to_dict() for msg in self._sessions[session_id]]
        
    def clear_session(self, session_id: str) -> None:
        """Clear the history of a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]


# Global instance
session_manager = SessionManager()
