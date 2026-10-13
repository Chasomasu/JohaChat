"""
配置模块
YAML 配置管理、日志系统

配置来源：
  - 连接配置：joha/adapter/connection.yaml（YAML）
  - 应用配置：joha/config/config.json（JSON，由 joha.config.config_manager 管理）
  - 决策参数：joha/config/reply_decision.json（JSON，由 joha.decision.reply_decision 管理）

所有配置均来源于文件，不再读取环境变量 / .env。
"""

from __future__ import annotations

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, TypeAlias

import yaml

from joha.adapter.backends import DEFAULT_BACKEND, BackendSpec, get_backend

# ---- 类型别名 ----
YamlConfig: TypeAlias = Dict[str, Any]


class ConfigManager:
    """YAML 配置管理器"""

    def __init__(self, config_path: str | None = None) -> None:
        """初始化配置管理器

        Args:
            config_path: 配置文件路径，默认指向同目录下的 connection.yaml
        """
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "connection.yaml")
        _raw: Path = Path(config_path)
        if not _raw.is_absolute():
            # 相对路径解析到项目根目录
            _raw = Path(__file__).parent.parent / _raw
        self.config_path: Path = _raw
        self.config: YamlConfig = {}
        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded: Any = yaml.safe_load(f)
                    self.config = loaded if isinstance(loaded, dict) else {}
            except Exception as e:
                print(f"[配置] 加载失败: {e}，使用空配置")
                self.config = {}
        else:
            self.config = {}

    def _save_config(self) -> None:
        """保存配置文件"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    self.config,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )
        except Exception as e:
            print(f"[配置] 保存失败: {e}")

    # ---- 通用读写 ----

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持点号分隔路径）

        Args:
            key: 配置键，如 'napcat.ws_url'
            default: 默认值

        Returns:
            配置值
        """
        keys: list[str] = key.split(".")
        value: Any = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default

    def set(self, key: str, value: Any) -> None:
        """设置配置值（支持点号分隔路径）

        Args:
            key: 配置键
            value: 配置值
        """
        keys: list[str] = key.split(".")
        current: Any = self.config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    def save(self) -> None:
        """保存配置到文件"""
        self._save_config()

    def reload(self) -> None:
        """重新加载配置"""
        self._load_config()

    def show(self) -> None:
        """显示当前配置"""
        print("\n" + "=" * 50)
        print("  当前配置")
        print("=" * 50)
        print(
            yaml.dump(
                self.config,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
        )
        print("=" * 50 + "\n")

    # ==================== 后端选择 ====================

    def get_backend_name(self) -> str:
        """获取当前选中的 OneBot 后端名称（连接配置顶层 adapter 字段，缺省为 napcat）"""
        return get_backend(self.get("adapter") or DEFAULT_BACKEND).name

    def set_backend(self, name: str) -> None:
        """切换 OneBot 后端（napcat / snowluma）"""
        self.set("adapter", get_backend(name).name)
        self._save_config()

    def get_backend(self) -> BackendSpec:
        """获取当前后端描述"""
        return get_backend(self.get_backend_name())

    # ==================== OneBot 连接配置（后端感知） ====================

    def get_ws_url(self) -> str:
        """获取当前后端的 WebSocket 正向连接地址"""
        backend = self.get_backend()
        return self.get(f"{backend.config_section}.ws_url") or backend.default_ws_url

    def get_ws_token(self) -> str:
        """获取当前后端的 WebSocket 鉴权 Token"""
        backend = self.get_backend()
        return self.get(f"{backend.config_section}.access_token", "") or ""

    def get_bot_uin(self) -> str:
        """获取当前后端的机器人 QQ 号"""
        backend = self.get_backend()
        return self.get(f"{backend.config_section}.bot_uin", "") or ""

    def set_bot_uin(self, bot_uin: str) -> None:
        """设置当前后端的机器人 QQ 号"""
        self.set(f"{self.get_backend().config_section}.bot_uin", bot_uin)
        self._save_config()

    def set_root(self, root: str) -> None:
        """设置当前后端的根账号"""
        self.set(f"{self.get_backend().config_section}.root", root)
        self._save_config()

    def set_ws_uri(self, ws_uri: str) -> None:
        """设置当前后端的 WebSocket URI"""
        self.set(f"{self.get_backend().config_section}.ws_url", ws_uri)
        self._save_config()

    def set_ws_token(self, ws_token: str) -> None:
        """设置当前后端的 WebSocket Token"""
        self.set(f"{self.get_backend().config_section}.access_token", ws_token)
        self._save_config()

    def set_webui_uri(self, webui_uri: str) -> None:
        """设置当前后端的 WebUI URI"""
        self.set(f"{self.get_backend().config_section}.webui_uri", webui_uri)
        self._save_config()

    def set_webui_token(self, webui_token: str) -> None:
        """设置当前后端的 WebUI Token"""
        self.set(f"{self.get_backend().config_section}.webui_token", webui_token)
        self._save_config()

    # ==================== 日志配置 ====================

    def set_log_level(self, level: str) -> None:
        """设置日志级别"""
        self.set("logging.level", level)
        self._save_config()

    def set_log_dir(self, log_dir: str) -> None:
        """设置日志目录"""
        self.set("logging.log_dir", log_dir)
        self._save_config()

    # ==================== 其他 ====================

    def set_debug(self, debug: bool) -> None:
        """设置调试模式"""
        self.set("settings.debug", debug)
        self._save_config()


# 全局配置实例
config_manager: ConfigManager = ConfigManager()


# ==================== 日志系统 ====================

_logging_setup_done: bool = False


def setup_logging(
    log_level: str | None = None,
    log_dir: str | None = None,
) -> None:
    """设置日志系统（按日期分隔文件，幂等调用）

    日志级别与目录优先取自 connection.yaml 的 logging 段，未配置时使用默认值。

    Args:
        log_level: 日志级别，默认从 YAML 读取
        log_dir: 日志目录，默认从 YAML 读取
    """
    global _logging_setup_done
    if _logging_setup_done:
        return
    _logging_setup_done = True

    level: str = log_level if log_level is not None else config_manager.get("logging.level", "INFO")
    directory: str = log_dir if log_dir is not None else config_manager.get("logging.log_dir", "log")

    # 创建日志目录
    log_path: Path = Path(directory)
    log_path.mkdir(parents=True, exist_ok=True)

    today: str = datetime.now().strftime("%Y-%m-%d")
    log_file: Path = log_path / f"{today}.log"

    # 根日志器
    root: logging.Logger = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 文件处理器
    fh: logging.FileHandler = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(getattr(logging, level.upper(), logging.INFO))
    fh.setFormatter(logging.Formatter(log_format))
    root.addHandler(fh)

    # 控制台处理器
    ch: logging.StreamHandler = logging.StreamHandler()
    ch.setLevel(getattr(logging, level.upper(), logging.INFO))
    ch.setFormatter(logging.Formatter(log_format))
    root.addHandler(ch)

    # 抑制第三方库日志
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """获取日志器

    Args:
        name: 日志器名称

    Returns:
        logging.Logger 实例
    """
    return logging.getLogger(name)
