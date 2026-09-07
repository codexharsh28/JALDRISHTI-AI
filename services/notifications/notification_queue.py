"""
Asynchronous Notification Job Queue and Dispatch Worker for JALDRISHTI AI.
"""

from typing import Dict, Any, List, Optional, Tuple
import asyncio
from datetime import datetime, timezone
import time
import logging
from collections import deque

from services.notifications.notification_types import (
    NotificationMessage,
    NotificationDeliveryStatus,
    NotificationChannel,
    DeliveryRecord
)
from services.notifications.providers.base_provider import NotificationProvider
from services.notifications.providers.sms_provider import MockSMSSink, MSG91Provider
from services.notifications.providers.push_provider import MockPushSink, FCMPushProvider
from services.notifications.providers.in_app_provider import in_app_provider

logger = logging.getLogger(__name__)

class NotificationQueueWorker:
    """
    Background job queue that dispatches notification messages with retries,
    exponential backoff, delivery metrics, and provider failover.
    """

    def __init__(
        self,
        use_mock_providers: bool = True
    ):
        self.use_mock_providers = use_mock_providers
        self._queue: asyncio.Queue[NotificationMessage] = asyncio.Queue()
        self._delivery_history: deque = deque(maxlen=1000)
        self._is_running = False
        self._worker_task: Optional[asyncio.Task] = None

        # Provider configurations
        self.mock_sms_sink = MockSMSSink()
        self.msg91_provider = MSG91Provider()
        self.mock_push_sink = MockPushSink()
        self.fcm_provider = FCMPushProvider()
        self.in_app_provider = in_app_provider

        # Metrics counters
        self.metrics = {
            "total_queued": 0,
            "total_sent": 0,
            "total_delivered": 0,
            "total_failed": 0,
            "total_retried": 0,
            "latencies_ms": []
        }

    async def enqueue(self, message: NotificationMessage) -> None:
        """Enqueues a message for background dispatch."""
        self.metrics["total_queued"] += 1
        await self._queue.put(message)
        logger.info(f"[NOTIF_QUEUE] Enqueued notification {message.notification_id} for user {message.user_id} via {message.channel.value}")

    async def start_worker(self) -> None:
        """Starts background dispatch loop."""
        self._is_running = True
        while self._is_running:
            try:
                message = await self._queue.get()
                await self._process_message(message)
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[NOTIF_QUEUE] Error in dispatch worker loop: {e}")
                await asyncio.sleep(0.5)

    async def _process_message(self, message: NotificationMessage) -> None:
        """Dispatches single notification with retry and provider selection."""
        message.status = NotificationDeliveryStatus.PROCESSING
        t_start = time.perf_counter()

        provider = self._select_provider(message.channel)
        message.provider_name = provider.provider_name

        try:
            status, msg_id, err = await provider.send_notification(message)
            t_latency = (time.perf_counter() - t_start) * 1000.0

            message.status = status
            message.provider_message_id = msg_id
            message.delivery_latency_ms = round(t_latency, 2)
            message.error_message = err

            # Track metrics
            if status in [NotificationDeliveryStatus.SENT, NotificationDeliveryStatus.DELIVERED]:
                self.metrics["total_sent"] += 1
                if status == NotificationDeliveryStatus.DELIVERED:
                    self.metrics["total_delivered"] += 1
                self.metrics["latencies_ms"].append(t_latency)
                if len(self.metrics["latencies_ms"]) > 500:
                    self.metrics["latencies_ms"].pop(0)
            else:
                # Handle retries with exponential backoff
                if message.retry_count < message.max_retries:
                    message.retry_count += 1
                    message.status = NotificationDeliveryStatus.RETRYING
                    self.metrics["total_retried"] += 1
                    backoff_delay = 0.5 * (2 ** (message.retry_count - 1))
                    logger.warning(f"[NOTIF_QUEUE] Retrying {message.notification_id} in {backoff_delay}s (Attempt {message.retry_count}/{message.max_retries})")
                    await asyncio.sleep(backoff_delay)
                    await self._queue.put(message)
                    return
                else:
                    self.metrics["total_failed"] += 1
                    message.status = NotificationDeliveryStatus.FAILED

            # Record delivery audit in memory and database
            record = DeliveryRecord(
                notification_id=message.notification_id,
                user_id=message.user_id,
                channel=message.channel,
                provider=provider.provider_name,
                status=message.status,
                latency_ms=round(t_latency, 2),
                error_details=err
            )
            self._delivery_history.append(record)
            try:
                from services.notifications.db.repositories import NotificationRepository
                NotificationRepository.record_notification(message)
                NotificationRepository.record_delivery_attempt(record)
            except Exception as dbe:
                logger.warning(f"[NOTIF_QUEUE] Failed recording delivery to repository: {dbe}")

        except Exception as e:
            logger.error(f"[NOTIF_QUEUE] Unhandled exception sending {message.notification_id}: {e}")
            self.metrics["total_failed"] += 1
            message.status = NotificationDeliveryStatus.FAILED
            message.error_message = str(e)

    def _select_provider(self, channel: NotificationChannel) -> NotificationProvider:
        """Selects primary or mock provider based on configuration and channel."""
        if channel == NotificationChannel.IN_APP:
            return self.in_app_provider
        elif channel == NotificationChannel.SMS:
            if not self.use_mock_providers and self.msg91_provider.is_configured:
                return self.msg91_provider
            return self.mock_sms_sink
        elif channel == NotificationChannel.PUSH:
            if not self.use_mock_providers and self.fcm_provider.is_configured:
                return self.fcm_provider
            return self.mock_push_sink
        else:
            return self.in_app_provider

    def get_metrics_summary(self) -> Dict[str, Any]:
        total = self.metrics["total_sent"] + self.metrics["total_failed"]
        deliv_rate = (self.metrics["total_delivered"] / max(1, self.metrics["total_sent"])) * 100.0 if self.metrics["total_sent"] > 0 else 100.0
        fail_rate = (self.metrics["total_failed"] / max(1, total)) * 100.0 if total > 0 else 0.0
        
        latencies = self.metrics["latencies_ms"]
        median_lat = float(sorted(latencies)[len(latencies) // 2]) if latencies else 0.0
        p95_lat = float(sorted(latencies)[int(len(latencies) * 0.95)]) if latencies else 0.0

        return {
            "queue_depth": self._queue.qsize(),
            "total_queued": self.metrics["total_queued"],
            "total_sent": self.metrics["total_sent"],
            "total_delivered": self.metrics["total_delivered"],
            "total_failed": self.metrics["total_failed"],
            "total_retried": self.metrics["total_retried"],
            "delivery_rate_pct": round(deliv_rate, 1),
            "failure_rate_pct": round(fail_rate, 1),
            "median_latency_ms": round(median_lat, 1),
            "p95_latency_ms": round(p95_lat, 1),
            "mock_mode": self.use_mock_providers
        }

    def get_recent_deliveries(self, limit: int = 50) -> List[DeliveryRecord]:
        return list(reversed(list(self._delivery_history)))[:limit]

# Global singleton instance
notification_queue = NotificationQueueWorker()
