"""
Constitutional AIOps - WebSocket Manager

Real-time event broadcasting for incidents, actions, and system updates.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
from weakref import WeakSet

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """WebSocket event types."""

    # Connection events
    CONNECTED = "connected"
    PING = "ping"
    PONG = "pong"

    # Incident events
    INCIDENT_CREATED = "incident.created"
    INCIDENT_UPDATED = "incident.updated"
    INCIDENT_RESOLVED = "incident.resolved"
    INCIDENT_DELETED = "incident.deleted"

    # Action events
    ACTION_CREATED = "action.created"
    ACTION_APPROVED = "action.approved"
    ACTION_REJECTED = "action.rejected"
    ACTION_EXECUTED = "action.executed"
    ACTION_FAILED = "action.failed"

    # Analysis events
    RCA_STARTED = "rca.started"
    RCA_COMPLETED = "rca.completed"
    REMEDIATION_PLANNED = "remediation.planned"

    # System events
    SYSTEM_HEALTH = "system.health"
    AGENT_STATUS = "agent.status"
    ALERT = "alert"


@dataclass
class WebSocketEvent:
    """WebSocket event structure."""

    event_type: EventType
    payload: dict
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps({
            "type": self.event_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
        })

    @classmethod
    def from_json(cls, data: str) -> "WebSocketEvent":
        """Create event from JSON string."""
        parsed = json.loads(data)
        return cls(
            event_type=EventType(parsed["type"]),
            payload=parsed.get("payload", {}),
            timestamp=datetime.fromisoformat(parsed.get("timestamp", datetime.utcnow().isoformat())),
            correlation_id=parsed.get("correlation_id"),
        )


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts events.

    Features:
    - Connection tracking with client metadata
    - Room-based subscriptions (by incident, service, etc.)
    - Event broadcasting with filtering
    - Automatic cleanup on disconnect
    - Heartbeat/ping-pong for connection health
    """

    def __init__(self):
        # Active connections with metadata
        self._connections: dict[WebSocket, dict] = {}
        # Room-based subscriptions
        self._rooms: dict[str, WeakSet[WebSocket]] = {}
        # Event handlers
        self._handlers: dict[EventType, list[Callable]] = {}
        # Background tasks
        self._tasks: list[asyncio.Task] = []
        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        client_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
            client_id: Optional client identifier
            metadata: Optional client metadata

        Returns:
            Connection ID
        """
        await websocket.accept()

        connection_id = client_id or f"client_{id(websocket)}"

        async with self._lock:
            self._connections[websocket] = {
                "id": connection_id,
                "connected_at": datetime.utcnow(),
                "metadata": metadata or {},
                "rooms": set(),
            }

        logger.info(f"WebSocket connected: {connection_id}")

        # Send welcome message
        await self.send_personal(
            websocket,
            WebSocketEvent(
                event_type=EventType.CONNECTED,
                payload={
                    "connection_id": connection_id,
                    "message": "Connected to Constitutional AIOps real-time updates",
                },
            ),
        )

        return connection_id

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        async with self._lock:
            if websocket in self._connections:
                conn_info = self._connections[websocket]

                # Remove from all rooms
                for room in conn_info.get("rooms", set()):
                    if room in self._rooms:
                        self._rooms[room].discard(websocket)

                del self._connections[websocket]
                logger.info(f"WebSocket disconnected: {conn_info['id']}")

    async def subscribe(self, websocket: WebSocket, room: str):
        """Subscribe a connection to a room."""
        async with self._lock:
            if room not in self._rooms:
                self._rooms[room] = WeakSet()

            self._rooms[room].add(websocket)

            if websocket in self._connections:
                self._connections[websocket]["rooms"].add(room)

        logger.debug(f"Client subscribed to room: {room}")

    async def unsubscribe(self, websocket: WebSocket, room: str):
        """Unsubscribe a connection from a room."""
        async with self._lock:
            if room in self._rooms:
                self._rooms[room].discard(websocket)

            if websocket in self._connections:
                self._connections[websocket]["rooms"].discard(room)

    async def send_personal(self, websocket: WebSocket, event: WebSocketEvent):
        """Send event to a specific connection."""
        try:
            await websocket.send_text(event.to_json())
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")
            await self.disconnect(websocket)

    async def broadcast(
        self,
        event: WebSocketEvent,
        exclude: Optional[WebSocket] = None,
    ):
        """
        Broadcast event to all connected clients.

        Args:
            event: Event to broadcast
            exclude: Optional connection to exclude
        """
        disconnected = []

        for websocket in list(self._connections.keys()):
            if websocket == exclude:
                continue

            try:
                await websocket.send_text(event.to_json())
            except Exception as e:
                logger.warning(f"Failed to broadcast to client: {e}")
                disconnected.append(websocket)

        # Clean up disconnected clients
        for ws in disconnected:
            await self.disconnect(ws)

    async def broadcast_to_room(
        self,
        room: str,
        event: WebSocketEvent,
        exclude: Optional[WebSocket] = None,
    ):
        """
        Broadcast event to all connections in a room.

        Args:
            room: Room name
            event: Event to broadcast
            exclude: Optional connection to exclude
        """
        if room not in self._rooms:
            return

        disconnected = []

        for websocket in list(self._rooms[room]):
            if websocket == exclude:
                continue

            try:
                await websocket.send_text(event.to_json())
            except Exception as e:
                logger.warning(f"Failed to broadcast to room {room}: {e}")
                disconnected.append(websocket)

        # Clean up disconnected clients
        for ws in disconnected:
            await self.disconnect(ws)

    async def handle_message(self, websocket: WebSocket, data: str):
        """
        Handle incoming WebSocket message.

        Args:
            websocket: Source connection
            data: Raw message data
        """
        try:
            event = WebSocketEvent.from_json(data)

            # Handle built-in events
            if event.event_type == EventType.PING:
                await self.send_personal(
                    websocket,
                    WebSocketEvent(event_type=EventType.PONG, payload={}),
                )
                return

            # Handle subscriptions
            if event.event_type.value == "subscribe":
                room = event.payload.get("room")
                if room:
                    await self.subscribe(websocket, room)
                return

            if event.event_type.value == "unsubscribe":
                room = event.payload.get("room")
                if room:
                    await self.unsubscribe(websocket, room)
                return

            # Call registered handlers
            if event.event_type in self._handlers:
                for handler in self._handlers[event.event_type]:
                    try:
                        await handler(websocket, event)
                    except Exception as e:
                        logger.error(f"Handler error for {event.event_type}: {e}")

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON received: {data[:100]}")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")

    def on_event(self, event_type: EventType):
        """Decorator to register event handler."""
        def decorator(func: Callable):
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(func)
            return func
        return decorator

    @property
    def connection_count(self) -> int:
        """Number of active connections."""
        return len(self._connections)

    @property
    def connections_info(self) -> list[dict]:
        """Information about all connections."""
        return [
            {
                "id": info["id"],
                "connected_at": info["connected_at"].isoformat(),
                "rooms": list(info["rooms"]),
                "metadata": info.get("metadata", {}),
            }
            for info in self._connections.values()
        ]


# Global connection manager instance
manager = ConnectionManager()


# Convenience functions for broadcasting events
async def broadcast_incident_created(incident: dict):
    """Broadcast incident creation event."""
    await manager.broadcast(
        WebSocketEvent(
            event_type=EventType.INCIDENT_CREATED,
            payload=incident,
        )
    )


async def broadcast_incident_updated(incident: dict):
    """Broadcast incident update event."""
    event = WebSocketEvent(
        event_type=EventType.INCIDENT_UPDATED,
        payload=incident,
    )
    await manager.broadcast(event)

    # Also broadcast to incident-specific room
    await manager.broadcast_to_room(f"incident:{incident.get('id')}", event)


async def broadcast_incident_resolved(incident_id: str, resolution: dict):
    """Broadcast incident resolution event."""
    event = WebSocketEvent(
        event_type=EventType.INCIDENT_RESOLVED,
        payload={"incident_id": incident_id, **resolution},
    )
    await manager.broadcast(event)
    await manager.broadcast_to_room(f"incident:{incident_id}", event)


async def broadcast_action_created(action: dict):
    """Broadcast action creation event."""
    await manager.broadcast(
        WebSocketEvent(
            event_type=EventType.ACTION_CREATED,
            payload=action,
        )
    )


async def broadcast_action_approved(action: dict):
    """Broadcast action approval event."""
    event = WebSocketEvent(
        event_type=EventType.ACTION_APPROVED,
        payload=action,
    )
    await manager.broadcast(event)

    # Also broadcast to incident room if linked
    if action.get("incident_id"):
        await manager.broadcast_to_room(f"incident:{action['incident_id']}", event)


async def broadcast_action_rejected(action: dict, reason: str):
    """Broadcast action rejection event."""
    event = WebSocketEvent(
        event_type=EventType.ACTION_REJECTED,
        payload={**action, "rejection_reason": reason},
    )
    await manager.broadcast(event)


async def broadcast_action_executed(action: dict, result: dict):
    """Broadcast action execution event."""
    event = WebSocketEvent(
        event_type=EventType.ACTION_EXECUTED,
        payload={**action, "result": result},
    )
    await manager.broadcast(event)


async def broadcast_rca_started(incident_id: str):
    """Broadcast RCA analysis started event."""
    event = WebSocketEvent(
        event_type=EventType.RCA_STARTED,
        payload={"incident_id": incident_id},
    )
    await manager.broadcast(event)
    await manager.broadcast_to_room(f"incident:{incident_id}", event)


async def broadcast_rca_completed(incident_id: str, rca_result: dict):
    """Broadcast RCA analysis completed event."""
    event = WebSocketEvent(
        event_type=EventType.RCA_COMPLETED,
        payload={"incident_id": incident_id, "result": rca_result},
    )
    await manager.broadcast(event)
    await manager.broadcast_to_room(f"incident:{incident_id}", event)


async def broadcast_system_health(health: dict):
    """Broadcast system health update."""
    await manager.broadcast(
        WebSocketEvent(
            event_type=EventType.SYSTEM_HEALTH,
            payload=health,
        )
    )


async def broadcast_alert(alert: dict):
    """Broadcast system alert."""
    await manager.broadcast(
        WebSocketEvent(
            event_type=EventType.ALERT,
            payload=alert,
        )
    )
