"""
统一消息构建器

三层记忆架构：
- 第一层：群对话记忆（group_conversation）— 群聊时加载完整对话流
- 第二层：群长期记忆（group_memory）— 摘要 + 话题 + 事实
- 第三层：用户画像/风格（style_learner）— 始终加载
"""
from typing import List, Dict, Optional

from joha.managers.personas import get_persona, get_persona_by_group
from joha.managers.history_manager import history_manager
from joha.managers.style_learner import style_learner
from joha.managers.group_conversation import group_conversation
from joha.managers.group_memory import group_memory_manager
from joha.config.logger import tprint


class MessageBuilder:

    def __init__(self):
        self.tool_registry = None

    def build(
        self,
        user_id: str,
        message: str,
        images: list = None,
        persona_name: str = "joha",
        history: list = None,
        include_style: bool = True,
        history_limit: int = 10,
        group_id: Optional[str] = None,
    ) -> List[Dict]:
        images = images or []

        persona = self._resolve_persona(group_id, persona_name)
        system_prompt = persona.get("system_prompt",
            "你是一个真实的大学生，说话自然随意，像普通人聊天。回复简短自然，不超过20字。")

        # 检测用户是否称呼了AI的名字，如果是则强化自我认同
        if self._check_name_call(message):
            system_prompt += "\n\n【重要】用户正在称呼你的名字！你必须以第一人称明确回应自己的身份，表现出自我认同。例如：'对啊，我就是joha/马苏'、'嗯，我在呢'等自然的回应方式。"

        # 检测是否为合并消息（多条消息）
        if '\n' in message:
            message_lines = [line.strip() for line in message.split('\n') if line.strip()]
            if len(message_lines) > 1:
                system_prompt += f"\n\n【注意】用户连续发送了{len(message_lines)}条消息，这些是同一时间段内的连续发言。请综合考虑所有消息的语境进行回复，不要逐条回应。"

        if include_style:
            style_prompt = style_learner.get_user_style_prompt(user_id)
            if style_prompt:
                system_prompt += "\n\n" + style_prompt

        # 工具调用说明：具体工具的名称/参数/用途由 function-calling schema 提供，
        # 此处只补充"何时该用工具"的行为引导，避免与 schema 重复描述
        if self.tool_registry and self.tool_registry.get_tool_names():
            system_prompt += "\n\n【可用工具】需要实时信息或网页内容时请直接调用工具，不要仅凭记忆回答。"

        context_messages = [{"role": "system", "content": system_prompt}]

        # 第二层：群长期记忆
        if group_id:
            memory_block = group_memory_manager.get_memory_block(str(group_id))
            if memory_block:
                context_messages.insert(1, {"role": "system", "content": memory_block})

        # 第一层：群对话记忆（已包含各用户发言 + 机器人回复的完整对话流）
        has_group_context = False
        if group_id:
            conv_context = group_conversation.get_context(str(group_id), limit=history_limit)
            if conv_context:
                context_messages.extend(conv_context)
                has_group_context = True

        # 第三层：用户历史（仅在无群对话记忆时补充，避免与第一层重复注入）
        if not has_group_context:
            if history is None:
                history = history_manager.load_history(user_id, group_id=group_id)
            if isinstance(history, list):
                for h in history[-history_limit:]:
                    if isinstance(h, dict):
                        if h.get("message"):
                            context_messages.append({"role": "user", "content": h["message"]})

        # 当前消息
        if images:
            content_parts = []
            prompt_text = message if message else "看看这张图，用一句话描述你觉得有趣的地方"
            content_parts.append({"type": "text", "text": prompt_text})
            for img_url in images:
                content_parts.append({"type": "image_url", "image_url": {"url": img_url}})
            context_messages.append({"role": "user", "content": content_parts})
        else:
            context_messages.append({"role": "user", "content": message})

        return context_messages

    def _resolve_persona(self, group_id: Optional[str], persona_name: str) -> dict:
        """按群选择人设：默认人设(joha)在绑定群时按群绑定解析，其余按名称取"""
        if group_id and persona_name == "joha":
            return get_persona_by_group(group_id)
        return get_persona(persona_name)

    def _check_name_call(self, message: str) -> bool:
        """检测用户是否称呼了AI的名字"""
        if not message:
            return False

        from joha.decision.reply_decision import reply_cfg
        bot_names = reply_cfg.bot_nicknames

        message_lower = message.lower()
        for name in bot_names:
            if name.lower() in message_lower:
                return True

        return False


message_builder = MessageBuilder()
