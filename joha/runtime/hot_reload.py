"""
热重载模块
监控 joha 目录下的文件变化，自动重新加载修改的模块
"""
import sys
import importlib
import logging
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


class ModuleReloader:
    """模块热重载器"""

    def __init__(self, watch_dir: str = "joha"):
        self.watch_dir = Path(watch_dir)
        self._loaded_modules: dict[str, object] = {}
        self._file_to_module: dict[str, str] = {}

    def _get_module_name(self, file_path: str) -> str | None:
        """将文件路径转换为模块名"""
        path = Path(file_path)
        if not path.suffix == '.py':
            return None

        try:
            rel_path = path.relative_to(self.watch_dir.parent)
        except ValueError:
            return None

        module_parts = list(rel_path.parts)
        if module_parts[-1] == '__init__.py':
            module_parts = module_parts[:-1]
        else:
            module_parts[-1] = module_parts[-1].replace('.py', '')

        return '.'.join(module_parts)

    def _reload_module(self, module_name: str) -> bool:
        """重新加载指定模块"""
        try:
            if module_name in sys.modules:
                module = sys.modules[module_name]
                importlib.reload(module)
                logger.info(f"[热重载] 已重载模块: {module_name}")
                return True
            else:
                logger.warning(f"[热重载] 模块未加载，跳过: {module_name}")
                return False
        except Exception as e:
            logger.error(f"[热重载] 重载模块失败 {module_name}: {e}")
            return False


class FileChangeHandler(FileSystemEventHandler):
    """文件变化处理器"""

    def __init__(self, reloader: ModuleReloader):
        self.reloader = reloader
        self._pending_changes: set[str] = set()

    def on_modified(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
        if not file_path.endswith('.py'):
            return

        if file_path in self._pending_changes:
            return

        self._pending_changes.add(file_path)

        module_name = self.reloader._get_module_name(file_path)
        if module_name:
            logger.info(f"[热重载] 检测到文件变化: {file_path}")
            self.reloader._reload_module(module_name)

        self._pending_changes.discard(file_path)

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.py'):
            logger.info(f"[热重载] 检测到新文件: {event.src_path}")


class HotReloader:
    """热重载管理器"""

    def __init__(self, watch_dir: str = "joha"):
        self.watch_dir = Path(watch_dir).absolute()
        self.reloader = ModuleReloader(str(self.watch_dir))
        self.handler = FileChangeHandler(self.reloader)
        self.observer = Observer()
        self._started = False

    def start(self):
        """启动文件监控"""
        if self._started:
            logger.warning("[热重载] 已在运行")
            return

        try:
            self.observer.schedule(
                self.handler,
                str(self.watch_dir),
                recursive=True
            )
            self.observer.start()
            self._started = True
            logger.info(f"[热重载] 已启动，监控目录: {self.watch_dir}")
        except Exception as e:
            logger.error(f"[热重载] 启动失败: {e}")

    def stop(self):
        """停止文件监控"""
        if not self._started:
            return

        try:
            self.observer.stop()
            self.observer.join()
            self._started = False
            logger.info("[热重载] 已停止")
        except Exception as e:
            logger.error(f"[热重载] 停止失败: {e}")

    @property
    def running(self) -> bool:
        return self._started

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


hot_reloader = HotReloader(watch_dir="joha")
