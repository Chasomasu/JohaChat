"""core 兼容层：各模块已拆分为 engine / messaging / runtime / commands。

此包仅为向后兼容保留，把旧的 joha.core.* 导入转发到新位置。
新代码请直接使用新包路径：
  engine/    — 编排入口（服务、消息处理）
  messaging/ — 队列合并、消息组装、图像工具、回复后处理
  runtime/   — 应用上下文、工具注册表、热重载
  commands/  — 命令处理
"""
from joha.engine import (
    message_service, MessageService,
    message_handler, MessageHandler, process_merged_message,
)
from joha.messaging import (
    message_builder, MessageBuilder,
    message_queue_manager, MessageQueueManager, MergedMessage, QueuedMessage,
    post_processor, ResponsePostProcessor,
)
from joha.runtime import (
    runtime_context, RuntimeContext,
    tool_registry, get_tool_registry, ToolRegistry,
    hot_reloader, HotReloader,
)
from joha.commands import (
    command_handler, CommandHandler, normalize_fallback_command,
)
from joha.managers import (
    persona_monitor, PersonaStabilityMonitor,
    HistoryCleaner,
)

__all__ = [
    'message_service', 'MessageService',
    'message_handler', 'MessageHandler', 'process_merged_message',
    'message_builder', 'MessageBuilder',
    'message_queue_manager', 'MessageQueueManager', 'MergedMessage', 'QueuedMessage',
    'post_processor', 'ResponsePostProcessor',
    'runtime_context', 'RuntimeContext',
    'tool_registry', 'get_tool_registry', 'ToolRegistry',
    'hot_reloader', 'HotReloader',
    'command_handler', 'CommandHandler', 'normalize_fallback_command',
    'persona_monitor', 'PersonaStabilityMonitor',
    'HistoryCleaner',
]
