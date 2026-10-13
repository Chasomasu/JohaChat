"""命令系统：命令处理器与别名归一化。"""
from .commands import (
    FALLBACK_COMMAND_ALIASES,
    CommandHandler,
    add_admin,
    command_handler,
    format_duration,
    format_top_groups,
    get_admin_list_str,
    is_admin,
    normalize_fallback_command,
    remove_admin,
)

__all__ = [
    "command_handler",
    "CommandHandler",
    "is_admin",
    "add_admin",
    "remove_admin",
    "get_admin_list_str",
    "format_duration",
    "format_top_groups",
    "normalize_fallback_command",
    "FALLBACK_COMMAND_ALIASES",
]
