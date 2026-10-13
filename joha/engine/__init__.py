"""应用编排层：消息引擎与消息处理器。

依赖方向：engine → messaging（队列 / 组装 / 后处理）→ 更底层模块。
messaging 等下层包不得反向导入本包。
"""
from .service import MessageService, message_service
from .message_handler import MessageHandler, message_handler, process_merged_message

__all__ = [
    "MessageService",
    "message_service",
    "MessageHandler",
    "message_handler",
    "process_merged_message",
]
