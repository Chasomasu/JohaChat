"""
消息处理器 v2.0 - 处理群消息
支持上下文感知和群组状态追踪
集成消息队列进行智能合并
适配 RqhBot SDK 事件模型

工作流程：
1. 提取消息内容（文本 + 图片）
2. 记录群组状态
3. 处理斜杠命令
4. 提取消息元数据（@、回复等）
5. 加入消息队列（智能合并）
6. 调用服务层处理
7. 发送回复
"""
import re
from typing import Optional

from joha.adapter import GroupMessageEvent
from .service import message_service
from joha.commands import command_handler, normalize_fallback_command
from joha.runtime.runtime_context import runtime_context
from joha.messaging.message_queue import message_queue_manager, MergedMessage
from joha.messaging.image_utils import extract_images_from_sdk_event
from joha.config.logger import johalog_logger, tprint
from joha.decision.group_state import group_state_manager


async def process_merged_message(merged_msg: MergedMessage, bot_api) -> Optional[str]:
    """处理合并后的消息：调用服务层生成回复 + 发送

    供正常消息路径和过期队列后台任务共用。
    """
    # 1. 调用服务层生成回复
    response = await message_service.process_message(
        userid=merged_msg.user_id,
        message=merged_msg.merged_text,
        group_id=merged_msg.group_id,
        is_at_bot=merged_msg.is_at_bot,
        reply_to_bot=merged_msg.reply_to_bot,
        is_pure_sticker_or_image=merged_msg.is_pure_sticker_or_image,
        images=merged_msg.images,
        merged_text=merged_msg.merged_text,
        merged_messages=merged_msg.messages,
        is_merged=merged_msg.count > 1,
    )

    # 2. 发送回复
    if response:
        try:
            group_id = str(merged_msg.group_id)
            # 检测工具返回中是否包含截图路径
            screenshot_match = re.search(r'📁\s*(.+\.png)', response)

            # 捕获发送结果以提取 message_id，用于后续 reply_to_bot 快速判定
            if screenshot_match:
                screenshot_path = screenshot_match.group(1).strip()
                send_result = await bot_api.send_group_message(
                    group_id=int(group_id),
                    message=response,
                    image_path=screenshot_path,
                )
            else:
                send_result = await bot_api.send_group_message(group_id=int(group_id), message=response)

            # 提取消息 ID 并注册到群组状态，供 reply_to_bot 本地快速判定
            sent_msg_id = 0
            if isinstance(send_result, dict):
                sent_msg_id = send_result.get("message_id", 0)

            # 记录机器人回复到群组状态
            group_state_manager.record_bot_reply(group_id=group_id, text=response, msg_id=sent_msg_id)
        except Exception as e:
            tprint("error", f"发送消息失败: {e}")

    return response


class MessageHandler:
    """
    消息处理器
    
    工作流程：
    1. 提取消息内容（文本 + 图片）
    2. 记录群组状态
    3. 处理斜杠命令
    4. 提取消息元数据（@、回复等）
    5. 加入消息队列（智能合并）
    6. 调用服务层处理
    7. 发送回复
    """

    @staticmethod
    async def process_group_message(event: GroupMessageEvent, bot_api):
        """
        处理群消息（集成消息队列）

        Args:
            event: SDK 群消息事件
            bot_api: BotAPI 对象
        """
        # 1. 提取消息内容
        actual_message = event.message.plain_text.strip()
        userid = event.user_id
        group_id = str(event.group_id)
        
        # 提取图片
        image_urls = extract_images_from_sdk_event(event)

        # 既没有文字也没有图片，直接跳过
        if not actual_message and not image_urls:
            return

        # 2. 记录群消息到状态追踪器（用于决策模型）
        group_state_manager.record_message(
            group_id=group_id,
            user_id=str(userid),
            text=actual_message or "[图片]",
            is_bot=False
        )

        # 3. 处理斜杠命令
        fallback_command = normalize_fallback_command(actual_message)
        if fallback_command:
            handled = await command_handler.handle_command(fallback_command, str(userid), event.group_id, bot_api)
            if handled is not None or actual_message.startswith("/"):
                return

        # 4. 提取消息元数据
        is_at_bot = False
        reply_to_bot = False
        is_pure_sticker_or_image = (len(image_urls) > 0 and not actual_message)

        # 检查是否@机器人（从 SDK 事件解析的 at_user_ids）
        if event.at_user_ids:
            is_at_bot = runtime_context.bot_uin in event.at_user_ids

        # 检查是否回复机器人消息
        # 优先查本地 recent_bot_msg_ids（O(1) 集合查找，零 API 开销）；
        # 仅当本地未命中时才回退到 get_message API
        if event.reply_message_id is not None:
            if group_state_manager.is_bot_message(group_id, event.reply_message_id):
                reply_to_bot = True
            else:
                try:
                    reply_data = await bot_api.get_message(event.reply_message_id)
                    if isinstance(reply_data, dict):
                        reply_sender = reply_data.get("sender", {}) or reply_data.get("data", {}).get("sender", {})
                        reply_user_id = reply_sender.get("user_id", 0)
                        if int(reply_user_id) == runtime_context.bot_uin:
                            reply_to_bot = True
                except Exception:
                    pass

        # 5. 使用消息队列处理（智能合并）
        merged_msg = await message_queue_manager.add_message(
            user_id=str(userid),
            group_id=group_id,
            message=actual_message,
            images=image_urls,
            is_at_bot=is_at_bot,
            reply_to_bot=reply_to_bot,
            is_pure_sticker_or_image=is_pure_sticker_or_image,
        )
        
        # 如果返回了合并消息，则处理；否则等待更多消息
        if merged_msg:
            await process_merged_message(merged_msg, bot_api)


# 全局处理器实例
message_handler = MessageHandler()
