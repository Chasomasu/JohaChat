"""消息队列数据模型"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class QueuedMessage:
    """队列中的消息"""
    user_id: str
    group_id: str
    message: str
    timestamp: float
    images: List[str] = field(default_factory=list)
    is_at_bot: bool = False
    reply_to_bot: bool = False
    is_pure_sticker_or_image: bool = False


@dataclass
class MergedMessage:
    """合并后的消息"""
    user_id: str
    group_id: str
    messages: List[str]  # 原始消息列表
    merged_text: str     # 合并后的文本
    timestamp: float     # 第一条消息的时间
    last_timestamp: float  # 最后一条消息的时间
    images: List[str] = field(default_factory=list)
    is_at_bot: bool = False
    reply_to_bot: bool = False
    is_pure_sticker_or_image: bool = False

    @property
    def duration(self) -> float:
        """消息持续时间（秒）"""
        return self.last_timestamp - self.timestamp

    @property
    def count(self) -> int:
        """消息数量"""
        return len(self.messages)
