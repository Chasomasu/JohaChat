"""兼容转发：实现已移至 joha.messaging.message_queue。"""
from joha.messaging.message_queue import (
    MessageQueueManager,
    message_queue_manager,
    MergedMessage,
    QueuedMessage,
)

__all__ = [
    "MessageQueueManager",
    "message_queue_manager",
    "MergedMessage",
    "QueuedMessage",
]
