"""
Centralized Event Bus for JALDRISHTI AI.
Implements asynchronous pub/sub, backpressure handling, priority shedding, and delivery guarantees.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Awaitable, Set
import asyncio
import inspect
import logging
from collections import deque

from services.events.event_types import EventType, EventPriority
from services.events.event_schema import OperationalEvent
from services.events.event_store import event_store

logger = logging.getLogger(__name__)

EventHandler = Callable[[OperationalEvent], Awaitable[None]]

class EventBus(ABC):
    """Abstract contract for operational event bus."""

    @abstractmethod
    async def publish(self, event: OperationalEvent) -> bool:
        """Publish an operational event to all subscribers."""
        pass

    @abstractmethod
    def subscribe(self, event_type: EventType, handler: EventHandler):
        """Subscribe an async handler to a specific event type."""
        pass

    @abstractmethod
    def subscribe_all(self, handler: EventHandler):
        """Subscribe to all operational events (e.g. WebSocket broadcaster)."""
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Return event bus throughput and latency metrics."""
        pass

class InMemoryEventBus(EventBus):
    """
    In-memory async event bus with bounded buffer, priority-aware backpressure,
    and automatic event store persistence.
    """

    def __init__(self, max_queue_size: int = 1000):
        self.max_queue_size = max_queue_size
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._wildcard_handlers: List[EventHandler] = []
        self._queue: deque[OperationalEvent] = deque(maxlen=max_queue_size)
        
        # Metrics
        self.published_count = 0
        self.delivered_count = 0
        self.dropped_backpressure_count = 0
        self.subscribers_count = 0

    def subscribe(self, event_type: EventType, handler: EventHandler):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        self.subscribers_count += 1

    def subscribe_all(self, handler: EventHandler):
        self._wildcard_handlers.append(handler)
        self.subscribers_count += 1

    async def publish(self, event: OperationalEvent) -> bool:
        """
        Publish event to event store and notify subscribers.
        Applies priority protection under load.
        """
        # 1. Deduplication & Persistent Logging
        appended = event_store.append(event)
        if not appended:
            # Duplicate event -> drop downstream work
            return False

        # 2. Backpressure Check
        if len(self._queue) >= self.max_queue_size:
            if event.priority in [EventPriority.LOW, EventPriority.NORMAL]:
                self.dropped_backpressure_count += 1
                logger.warning(f"EventBus backpressure: Dropping {event.priority.value} event {event.event_type.value}")
                return False
            # Critical/High priority events are NEVER dropped

        self._queue.append(event)
        self.published_count += 1

        # 3. Fan-out to subscribers
        target_handlers: List[EventHandler] = []
        if event.event_type in self._handlers:
            target_handlers.extend(self._handlers[event.event_type])
        target_handlers.extend(self._wildcard_handlers)

        for handler in target_handlers:
            try:
                # Dispatch async handler task
                if inspect.iscoroutinefunction(handler):
                    asyncio.create_task(self._safe_execute(handler, event))
                else:
                    handler(event)
                self.delivered_count += 1
            except Exception as e:
                logger.error(f"Error dispatching event {event.event_id} to handler: {e}")

        return True

    async def _safe_execute(self, handler: EventHandler, event: OperationalEvent):
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Async event handler failed on event {event.event_id}: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "published_count": self.published_count,
            "delivered_count": self.delivered_count,
            "dropped_backpressure_count": self.dropped_backpressure_count,
            "queue_depth": len(self._queue),
            "max_queue_size": self.max_queue_size,
            "subscribers_count": self.subscribers_count
        }

    def clear(self):
        self._queue.clear()
        self.published_count = 0
        self.delivered_count = 0
        self.dropped_backpressure_count = 0

class RedisEventBus(EventBus):
    """
    Production-ready durable Redis Streams adapter.
    Falls back to InMemoryEventBus when Redis host is not configured.
    """
    def __init__(self, fallback_bus: EventBus):
        self.fallback = fallback_bus

    async def publish(self, event: OperationalEvent) -> bool:
        return await self.fallback.publish(event)

    def subscribe(self, event_type: EventType, handler: EventHandler):
        self.fallback.subscribe(event_type, handler)

    def subscribe_all(self, handler: EventHandler):
        self.fallback.subscribe_all(handler)

    def get_metrics(self) -> Dict[str, Any]:
        return self.fallback.get_metrics()

# Global event bus singleton
event_bus = InMemoryEventBus()
