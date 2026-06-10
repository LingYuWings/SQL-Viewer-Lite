"""
键盘快捷键管理模块

定义和管理应用程序的键盘快捷键。
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Callable
from dataclasses import dataclass, field

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QShortcut, QWidget
from PyQt5.QtGui import QKeySequence

logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_DIR = Path.home() / ".sql_viewer_lite"
SHORTCUTS_CONFIG_FILE = CONFIG_DIR / "shortcuts.json"


@dataclass
class ShortcutDefinition:
    """快捷键定义"""
    
    # 快捷键标识符
    id: str
    
    # 显示名称
    name: str
    
    # 默认快捷键序列
    default_key: str
    
    # 分组（用于设置界面）
    group: str
    
    # 描述
    description: str = ""
    
    # 是否启用
    enabled: bool = True
    
    def get_key_sequence(self) -> QKeySequence:
        """获取 QKeySequence"""
        return QKeySequence(self.default_key)


# 默认快捷键定义
DEFAULT_SHORTCUTS: Dict[str, ShortcutDefinition] = {
    # 文件操作
    "file.new_connection": ShortcutDefinition(
        id="file.new_connection",
        name="新建连接",
        default_key="Ctrl+N",
        group="文件",
        description="打开新建数据库连接对话框",
    ),
    "file.disconnect": ShortcutDefinition(
        id="file.disconnect",
        name="断开连接",
        default_key="Ctrl+D",
        group="文件",
        description="断开当前数据库连接",
    ),
    "file.exit": ShortcutDefinition(
        id="file.exit",
        name="退出",
        default_key="Alt+F4",
        group="文件",
        description="退出应用程序",
    ),
    
    # 编辑操作
    "edit.copy": ShortcutDefinition(
        id="edit.copy",
        name="复制",
        default_key="Ctrl+C",
        group="编辑",
        description="复制选中内容到剪贴板",
    ),
    "edit.paste": ShortcutDefinition(
        id="edit.paste",
        name="粘贴",
        default_key="Ctrl+V",
        group="编辑",
        description="从剪贴板粘贴内容",
    ),
    "edit.undo": ShortcutDefinition(
        id="edit.undo",
        name="撤销",
        default_key="Ctrl+Z",
        group="编辑",
        description="撤销上一步操作",
    ),
    "edit.redo": ShortcutDefinition(
        id="edit.redo",
        name="重做",
        default_key="Ctrl+Y",
        group="编辑",
        description="重做上一步操作",
    ),
    "edit.select_all": ShortcutDefinition(
        id="edit.select_all",
        name="全选",
        default_key="Ctrl+A",
        group="编辑",
        description="选择所有内容",
    ),
    
    # 视图操作
    "view.refresh": ShortcutDefinition(
        id="view.refresh",
        name="刷新",
        default_key="F5",
        group="视图",
        description="刷新当前数据",
    ),
    "view.toggle_sidebar": ShortcutDefinition(
        id="view.toggle_sidebar",
        name="切换侧边栏",
        default_key="Ctrl+B",
        group="视图",
        description="显示/隐藏侧边栏",
    ),
    
    # 工具操作
    "tools.sql_executor": ShortcutDefinition(
        id="tools.sql_executor",
        name="SQL 执行器",
        default_key="Ctrl+Shift+E",
        group="工具",
        description="打开/关闭 SQL 执行器",
    ),
    "tools.search": ShortcutDefinition(
        id="tools.search",
        name="搜索",
        default_key="Ctrl+F",
        group="工具",
        description="打开搜索对话框",
    ),
    
    # 数据操作
    "data.add_row": ShortcutDefinition(
        id="data.add_row",
        name="新增行",
        default_key="Ctrl+Insert",
        group="数据",
        description="在表格末尾添加新行",
    ),
    "data.delete_row": ShortcutDefinition(
        id="data.delete_row",
        name="删除行",
        default_key="Delete",
        group="数据",
        description="删除选中的行",
    ),
    "data.commit": ShortcutDefinition(
        id="data.commit",
        name="提交更改",
        default_key="Ctrl+S",
        group="数据",
        description="提交所有修改到数据库",
    ),
    "data.rollback": ShortcutDefinition(
        id="data.rollback",
        name="撤销更改",
        default_key="Ctrl+Z",
        group="数据",
        description="撤销所有未提交的修改",
    ),
}


class ShortcutManager(QObject):
    """
    快捷键管理器
    
    管理应用程序的所有键盘快捷键。
    支持自定义快捷键和配置持久化。
    """
    
    # 信号：快捷键被触发
    shortcut_triggered = pyqtSignal(str)  # shortcut_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 快捷键定义
        self._definitions: Dict[str, ShortcutDefinition] = {}
        
        # 活动的快捷键对象
        self._shortcuts: Dict[str, QShortcut] = {}
        
        # 回调函数
        self._callbacks: Dict[str, Callable] = {}
        
        # 初始化默认快捷键
        self._init_defaults()
        
        # 加载自定义配置
        self.load_config()
    
    def _init_defaults(self):
        """初始化默认快捷键定义"""
        for shortcut_id, definition in DEFAULT_SHORTCUTS.items():
            self._definitions[shortcut_id] = ShortcutDefinition(
                id=definition.id,
                name=definition.name,
                default_key=definition.default_key,
                group=definition.group,
                description=definition.description,
                enabled=definition.enabled,
            )
    
    def register_shortcut(
        self, 
        shortcut_id: str, 
        widget: QWidget, 
        callback: Callable,
        key_sequence: Optional[str] = None
    ):
        """
        注册快捷键
        
        Args:
            shortcut_id: 快捷键标识符
            widget: 绑定的控件
            callback: 回调函数
            key_sequence: 自定义快捷键序列（可选）
        """
        if shortcut_id not in self._definitions:
            logger.warning(f"未知的快捷键 ID: {shortcut_id}")
            return
        
        definition = self._definitions[shortcut_id]
        
        # 使用自定义或默认快捷键
        key = key_sequence or definition.default_key
        
        # 创建快捷键对象
        shortcut = QShortcut(QKeySequence(key), widget)
        shortcut.activated.connect(lambda: self._on_shortcut_activated(shortcut_id))
        
        # 存储
        self._shortcuts[shortcut_id] = shortcut
        self._callbacks[shortcut_id] = callback
        
        logger.debug(f"注册快捷键: {shortcut_id} = {key}")
    
    def _on_shortcut_activated(self, shortcut_id: str):
        """快捷键触发处理"""
        if shortcut_id in self._callbacks:
            try:
                self._callbacks[shortcut_id]()
                self.shortcut_triggered.emit(shortcut_id)
            except Exception as e:
                logger.error(f"快捷键 {shortcut_id} 执行失败: {e}")
    
    def get_shortcut_key(self, shortcut_id: str) -> Optional[str]:
        """获取快捷键的当前键序列"""
        if shortcut_id in self._definitions:
            return self._definitions[shortcut_id].default_key
        return None
    
    def set_shortcut_key(self, shortcut_id: str, key_sequence: str):
        """设置快捷键的键序列"""
        if shortcut_id in self._definitions:
            self._definitions[shortcut_id].default_key = key_sequence
            
            # 如果快捷键已注册，更新它
            if shortcut_id in self._shortcuts:
                self._shortcuts[shortcut_id].setKey(QKeySequence(key_sequence))
    
    def get_all_definitions(self) -> Dict[str, ShortcutDefinition]:
        """获取所有快捷键定义"""
        return self._definitions.copy()
    
    def get_definitions_by_group(self) -> Dict[str, list]:
        """按分组获取快捷键定义"""
        groups: Dict[str, list] = {}
        for definition in self._definitions.values():
            if definition.group not in groups:
                groups[definition.group] = []
            groups[definition.group].append(definition)
        return groups
    
    def load_config(self):
        """加载快捷键配置"""
        if not SHORTCUTS_CONFIG_FILE.exists():
            logger.info("快捷键配置文件不存在，使用默认配置")
            return
        
        try:
            with open(SHORTCUTS_CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            for shortcut_id, settings in config.items():
                if shortcut_id in self._definitions:
                    if "key" in settings:
                        self._definitions[shortcut_id].default_key = settings["key"]
                    if "enabled" in settings:
                        self._definitions[shortcut_id].enabled = settings["enabled"]
            
            logger.info(f"加载快捷键配置: {len(config)} 项")
            
        except Exception as e:
            logger.error(f"加载快捷键配置失败: {e}")
    
    def save_config(self):
        """保存快捷键配置"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        config = {}
        for shortcut_id, definition in self._definitions.items():
            config[shortcut_id] = {
                "key": definition.default_key,
                "enabled": definition.enabled,
            }
        
        try:
            with open(SHORTCUTS_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"保存快捷键配置: {len(config)} 项")
            
        except Exception as e:
            logger.error(f"保存快捷键配置失败: {e}")
    
    def reset_to_defaults(self):
        """重置所有快捷键为默认值"""
        for shortcut_id, default in DEFAULT_SHORTCUTS.items():
            if shortcut_id in self._definitions:
                self._definitions[shortcut_id].default_key = default.default_key
                self._definitions[shortcut_id].enabled = default.enabled
        
        # 更新活动的快捷键
        for shortcut_id, shortcut in self._shortcuts.items():
            if shortcut_id in self._definitions:
                key = self._definitions[shortcut_id].default_key
                shortcut.setKey(QKeySequence(key))
        
        logger.info("已重置所有快捷键为默认值")


# 全局快捷键管理器实例
_shortcut_manager: Optional[ShortcutManager] = None


def get_shortcut_manager() -> ShortcutManager:
    """获取快捷键管理器单例"""
    global _shortcut_manager
    if _shortcut_manager is None:
        _shortcut_manager = ShortcutManager()
    return _shortcut_manager


def register_app_shortcuts(main_window):
    """
    注册应用程序的快捷键
    
    Args:
        main_window: 主窗口实例
    """
    manager = get_shortcut_manager()
    
    # 文件操作
    manager.register_shortcut(
        "file.new_connection",
        main_window,
        main_window._on_new_connection
    )
    manager.register_shortcut(
        "file.disconnect",
        main_window,
        main_window._on_disconnect
    )
    manager.register_shortcut(
        "file.exit",
        main_window,
        main_window.close
    )
    
    # 视图操作
    manager.register_shortcut(
        "view.refresh",
        main_window,
        main_window._on_refresh
    )
    
    # 工具操作
    manager.register_shortcut(
        "tools.sql_executor",
        main_window,
        main_window._on_toggle_sql_executor
    )
    
    logger.info("注册应用程序快捷键完成")
