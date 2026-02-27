"""
FeedbackForge Session Management
=================================

Session management with Redis for conversation persistence.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SessionManager:
    """Manage conversation sessions with Redis backend."""

    def __init__(self, redis_client, ttl: int = 3600):
        """
        Initialize session manager.

        Args:
            redis_client: Redis client instance
            ttl: Time-to-live for sessions in seconds (default: 1 hour)
        """
        self.redis = redis_client
        self.ttl = ttl

    async def save_session(
        self,
        thread_id: str,
        messages: List[Dict],
        user_id: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Save conversation session to Redis.

        Args:
            thread_id: Unique session identifier
            messages: List of conversation messages
            user_id: User ID who owns this session
            metadata: Optional metadata (title, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Always store user_id in metadata for consistency
            metadata = metadata or {}
            metadata["user_id"] = user_id

            session_data = {
                "thread_id": thread_id,
                "user_id": user_id,
                "messages": messages,
                "metadata": metadata,
                "updated_at": datetime.now().isoformat(),
                "created_at": metadata.get("created_at", datetime.now().isoformat()),
            }

            # Use user_id in key for isolation: session:{user_id}:{thread_id}
            key = f"session:{user_id}:{thread_id}"
            await self.redis.setex(
                key,
                self.ttl,
                json.dumps(session_data)
            )

            logger.info(f"Saved session {thread_id} for user {user_id} with {len(messages)} messages")
            return True

        except Exception as e:
            logger.error(f"Failed to save session {thread_id}: {e}")
            return False

    async def load_session(self, thread_id: str, user_id: str) -> Optional[Dict]:
        """
        Load conversation session from Redis.

        Args:
            thread_id: Session identifier
            user_id: User ID requesting the session (for ownership verification)

        Returns:
            Session data dict or None if not found or unauthorized
        """
        try:
            # Use user_id in key for isolation and security
            key = f"session:{user_id}:{thread_id}"
            data = await self.redis.get(key)

            if data:
                session = json.loads(data)
                # Verify ownership (double-check)
                if session.get("user_id") != user_id:
                    logger.warning(f"User {user_id} attempted to access session {thread_id} owned by {session.get('user_id')}")
                    return None

                logger.info(f"Loaded session {thread_id} for user {user_id} with {len(session.get('messages', []))} messages")
                return session

            logger.debug(f"Session {thread_id} not found for user {user_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to load session {thread_id}: {e}")
            return None

    async def list_sessions(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        List active sessions for a specific user.

        Args:
            user_id: User ID to list sessions for (required)
            limit: Maximum number of sessions to return

        Returns:
            List of session metadata (sorted by updated_at, newest first)
        """
        try:
            # Pattern to match only this user's sessions
            pattern = f"session:{user_id}:*"
            keys = []

            # Scan for keys (more efficient than KEYS for production)
            async for key in self.redis.scan_iter(match=pattern, count=100):
                keys.append(key)
                if len(keys) >= limit:
                    break

            sessions = []
            for key in keys:
                data = await self.redis.get(key)
                if data:
                    session = json.loads(data)
                    # Verify ownership (security check)
                    if session.get("user_id") != user_id:
                        logger.warning(f"Found session with mismatched user_id in key {key}")
                        continue

                    # Return summary only (not full messages)
                    sessions.append({
                        "thread_id": session["thread_id"],
                        "message_count": len(session.get("messages", [])),
                        "metadata": session.get("metadata", {}),
                        "updated_at": session.get("updated_at"),
                        "created_at": session.get("created_at"),
                    })

            # Sort by updated_at (newest first)
            sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

            logger.info(f"Listed {len(sessions)} sessions for user {user_id}")
            return sessions[:limit]

        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []

    async def delete_session(self, thread_id: str, user_id: str) -> bool:
        """
        Delete a session from Redis.

        Args:
            thread_id: Session identifier
            user_id: User ID (for ownership verification)

        Returns:
            True if deleted, False otherwise
        """
        try:
            # Use user_id in key for security
            key = f"session:{user_id}:{thread_id}"
            result = await self.redis.delete(key)

            if result:
                logger.info(f"Deleted session {thread_id} for user {user_id}")
                return True
            else:
                logger.debug(f"Session {thread_id} not found for user {user_id}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete session {thread_id}: {e}")
            return False

    async def update_metadata(
        self,
        thread_id: str,
        user_id: str,
        metadata: Dict
    ) -> bool:
        """
        Update session metadata without touching messages.

        Args:
            thread_id: Session identifier
            user_id: User ID (for ownership verification)
            metadata: New metadata to merge

        Returns:
            True if successful, False otherwise
        """
        try:
            session = await self.load_session(thread_id, user_id)
            if not session:
                return False

            # Merge metadata
            session["metadata"].update(metadata)
            session["updated_at"] = datetime.now().isoformat()

            # Save back
            return await self.save_session(
                thread_id,
                session["messages"],
                user_id,
                session["metadata"]
            )

        except Exception as e:
            logger.error(f"Failed to update metadata for {thread_id}: {e}")
            return False


class InMemorySessionManager:
    """Fallback in-memory session manager when Redis is not available."""

    def __init__(self, ttl: int = 3600):
        # Store sessions by user_id and thread_id: {user_id: {thread_id: session_data}}
        self.sessions: Dict[str, Dict[str, Dict]] = {}
        self.ttl = ttl

    async def save_session(
        self,
        thread_id: str,
        messages: List[Dict],
        user_id: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Save session to memory."""
        try:
            # Always store user_id in metadata
            metadata = metadata or {}
            metadata["user_id"] = user_id

            # Initialize user's session dict if needed
            if user_id not in self.sessions:
                self.sessions[user_id] = {}

            self.sessions[user_id][thread_id] = {
                "thread_id": thread_id,
                "user_id": user_id,
                "messages": messages,
                "metadata": metadata,
                "updated_at": datetime.now().isoformat(),
                "created_at": metadata.get("created_at", datetime.now().isoformat()),
            }
            logger.info(f"Saved session {thread_id} for user {user_id} to memory")
            return True
        except Exception as e:
            logger.error(f"Failed to save session to memory: {e}")
            return False

    async def load_session(self, thread_id: str, user_id: str) -> Optional[Dict]:
        """Load session from memory."""
        user_sessions = self.sessions.get(user_id, {})
        session = user_sessions.get(thread_id)

        # Verify ownership
        if session and session.get("user_id") != user_id:
            logger.warning(f"User {user_id} attempted to access session {thread_id} owned by {session.get('user_id')}")
            return None

        return session

    async def list_sessions(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """List sessions from memory for a specific user."""
        user_sessions = self.sessions.get(user_id, {})
        sessions = []

        for session in user_sessions.values():
            sessions.append({
                "thread_id": session["thread_id"],
                "message_count": len(session.get("messages", [])),
                "metadata": session.get("metadata", {}),
                "updated_at": session.get("updated_at"),
                "created_at": session.get("created_at"),
            })

        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return sessions[:limit]

    async def delete_session(self, thread_id: str, user_id: str) -> bool:
        """Delete session from memory."""
        user_sessions = self.sessions.get(user_id, {})
        if thread_id in user_sessions:
            del user_sessions[thread_id]
            logger.info(f"Deleted session {thread_id} for user {user_id} from memory")
            return True
        return False

    async def update_metadata(
        self,
        thread_id: str,
        user_id: str,
        metadata: Dict
    ) -> bool:
        """Update session metadata in memory."""
        user_sessions = self.sessions.get(user_id, {})
        if thread_id in user_sessions:
            user_sessions[thread_id]["metadata"].update(metadata)
            user_sessions[thread_id]["updated_at"] = datetime.now().isoformat()
            return True
        return False
