"""消息队列包 — 数据模型与队列管理器。"""
from .manager import MessageQueueManager
from .models import MergedMessage, QueuedMessage

# 全局消息队列管理器实例（参数从 config.json 的 message_queue 段读取）
message_queue_manager = MessageQueueManager()

__all__ = [
    "MessageQueueManager",
    "message_queue_manager",
    "MergedMessage",
    "QueuedMessage",
]
