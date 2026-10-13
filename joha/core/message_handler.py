"""兼容转发：实现已移至 joha.engine.message_handler。"""
from joha.engine.message_handler import (
    MessageHandler,
    message_handler,
    process_merged_message,
)

__all__ = ["MessageHandler", "message_handler", "process_merged_message"]
