"""兼容转发：实现已移至 joha.messaging.response_postprocessor。"""
from joha.messaging.response_postprocessor import ResponsePostProcessor, post_processor

__all__ = ["ResponsePostProcessor", "post_processor"]
