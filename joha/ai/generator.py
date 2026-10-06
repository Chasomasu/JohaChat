from joha.ai.clients import OpenAICompatibleClient
from joha.managers.history_manager import load_history
from joha.config.config_manager import config
from joha.config.cache import cache_result, response_cache
from joha.managers.style_learner import style_learner
from joha.core.message_builder import message_builder
from joha.core.response_postprocessor import post_processor
from joha.config.logger import tprint
import asyncio
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class Generator:
    """核心回复生成器 - 使用统一的 AI 客户端架构，支持动态切换 Provider"""

    def __init__(self):
        self._request_count = 0
        self._error_count = 0
        self._client = None
        self._model = None
        self._init_client()

    def _init_client(self):
        """根据当前配置初始化或更新 AI 客户端"""
        tool_calling_enabled = bool(config.get("tool_calling.enabled", True))
        self._client = OpenAICompatibleClient(
            api_key=config.llm_api_key,
            base_url=config.llm_base_url,
            model=config.llm_model,
            enable_tools=tool_calling_enabled,
        )
        self._model = config.llm_model
        tprint("info", f"[Generator] 已加载 AI 客户端 | {config.get_active_provider_name() or '默认'} | 模型: {self._model}")

        # 注册工具：统一来自 ToolRegistry，LLM 函数名即注册表规范名（search / webpage）
        if tool_calling_enabled:
            from joha.core.tool_registry import get_tool_registry
            registry = get_tool_registry()
            if not registry._initialized:
                registry.auto_discover()
            for tool_def in registry.list_tools_openai():
                fn_name = tool_def["function"]["name"]
                self._client.register_tool(
                    tool_def,
                    lambda args, name=fn_name: registry.call_tool(name, args),
                )

    def switch_provider(self, name: str) -> bool:
        """切换 LLM Provider 并重建客户端

        Args:
            name: Provider 名称（对应 config.json 中 llm.providers 的 name）

        Returns:
            是否切换成功
        """
        if config.switch_provider(name):
            self._init_client()
            return True
        return False

    @property
    def current_model(self) -> str:
        return self._model

    @cache_result(response_cache, ttl=60)
    def _cached_chat(self, model: str, messages: tuple, temperature: float, max_tokens: int,
                     enable_tools: bool = True) -> str:
        """缓存的聊天调用

        enable_tools 参与缓存键，避免启用/禁用工具的结果互相污染
        """
        try:
            result = self._client.call_with_context(
                messages=list(messages),
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
                enable_tools=bool(enable_tools),
            )
            self._request_count += 1
            return result
        except Exception as e:
            raise RuntimeError(f"AI 调用失败: {e}")

    async def chat(self, messages: list, temperature=0.6, max_tokens=1024) -> Optional[str]:
        """异步生成接口"""
        try:
            result = await asyncio.get_running_loop().run_in_executor(
                None,
                self._cached_chat,
                self._model,
                tuple(messages),
                temperature,
                max_tokens,
                bool(self._client.enable_tools)
            )
            return result
        except Exception as e:
            self._error_count += 1
            logger.error(f"生成失败：{e}", exc_info=True)
            tprint("error", f"[AI] 生成失败：{e}")
            return None

    def chat_sync(self, messages: list, temperature=0.6, max_tokens=1024, enable_tools: bool = None) -> Optional[str]:
        """同步生成接口（用于工具调用等场景）
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数
            enable_tools: 是否启用工具，None 表示使用默认配置
        """
        try:
            # 本次调用的工具开关：None 表示跟随客户端默认配置
            # 通过 call_with_context 的参数传递，不修改共享的
            # self._client.enable_tools，避免与并发的 chat() 产生竞态
            effective_enable_tools = (
                self._client.enable_tools if enable_tools is None else enable_tools
            )

            result = self._cached_chat(
                self._model,
                tuple(messages),
                temperature,
                max_tokens,
                bool(effective_enable_tools)
            )

            return result
        except Exception as e:
            self._error_count += 1
            logger.error(f"生成失败：{e}", exc_info=True)
            tprint("error", f"[AI] 生成失败：{e}")
            return None

    def _build_messages(self, question: str, userid: str = None, group_id: Optional[str] = None) -> List[Dict[str, str]]:
        return message_builder.build(
            user_id=userid or "unknown",
            message=question,
            persona_name="joha",
            history=load_history(userid, group_id=group_id) if userid else [],
            include_style=True,
            history_limit=5,
            group_id=group_id,
        )

    async def generate(self, question: str, userid: str = None, group_id: Optional[str] = None) -> str:
        """生成回复"""
        messages = self._build_messages(question, userid, group_id=group_id)
        response = await self.chat(messages)

        # 后处理：过滤不符合人设的内容
        if response:
            response = post_processor.process(response)

        # 学习用户风格
        if userid:
            style_learner.learn_from_message(userid, question)

        return response


generator = Generator()
