"""WebSocket connection manager for real-time communication.

This module manages WebSocket connections, handles message broadcasting,
and maintains the registry of active connections mapped to user emails.

**Validates: Requirements 4.1, 5.3, 5.5**
"""

import logging
from datetime import datetime
from typing import Dict

from fastapi import WebSocket

# Configure logging
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections with user authentication.

    This class maintains an in-memory registry of active WebSocket connections
    mapped to user email addresses. It handles connection lifecycle events
    (connect, disconnect) and broadcasts messages to all connected clients.

    Attributes:
        active_connections: Dictionary mapping user emails to WebSocket connections
    """

    def __init__(self):
        """Initialize the connection manager with an empty connection registry."""
        self.active_connections: Dict[str, WebSocket] = {}
        logger.info("ConnectionManager initialized")

    async def connect(self, websocket: WebSocket, email: str) -> None:
        """Accept a WebSocket connection and register the user.

        Args:
            websocket: The WebSocket connection to accept
            email: User's email address extracted from JWT token

        **Validates: Requirement 4.1** - Associates validated JWT email with connection
        **Validates: Requirement 5.3** - Maintains in-memory registry of connections
        """
        await websocket.accept()
        self.active_connections[email] = websocket
        logger.info(
                "WebSocket user connected",
                extra={
                    "user_email": email,
                    "total_connections": len(self.active_connections),
                },
            )

    def disconnect(self, email: str) -> None:
        """Remove a connection from the registry.

        Args:
            email: User's email address to disconnect

        **Validates: Requirement 5.3** - Removes connection from registry
        """
        if email in self.active_connections:
            self.active_connections.pop(email)
            logger.info(
                "WebSocket user disconnected",
                extra={
                    "user_email": email,
                    "total_connections": len(self.active_connections),
                },
            )
        else:
            logger.warning(f"Attempted to disconnect non-existent connection: {email}")

    async def broadcast(self, message: dict, sender_email: str) -> None:
        """Broadcast a message to all connected users except the sender.

        This method sends the message to all active connections and automatically
        cleans up any dead connections that fail to receive the message.

        Args:
            message: Dictionary containing the message data to broadcast
            sender_email: Email of the user sending the message (excluded from broadcast)

        **Validates: Requirement 5.5** - Broadcasts messages and cleans up dead connections
        """
        dead_connections = []

        # Add timestamp to message if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()

        # Broadcast to all connections except sender
        for email, connection in self.active_connections.items():
            if email != sender_email:
                try:
                    await connection.send_json(message)
                    logger.debug(f"Message sent to {email}")
                except Exception as e:
                    logger.error(
                    "WebSocket broadcast failed",
                    extra={
                        "target_email": email,
                        "error": str(e),
                    },
                )
                    dead_connections.append(email)

        # Clean up dead connections
        for email in dead_connections:
            self.disconnect(email)
            logger.warning(f"Removed dead connection: {email}")

        if dead_connections:
            logger.info(f"Cleaned up {len(dead_connections)} dead connection(s)")
