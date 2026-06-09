"""
主题管理器模块

提供主题切换、主题偏好持久化功能。
"""

import json
import logging
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSignal, QObject

logger = logging.getLogger(__name__)

# 主题配置目录
CONFIG_DIR = Path.home() / ".sql_viewer_lite"
SETTINGS_FILE = CONFIG_DIR / "settings.json"

# 可用主题
THEMES = {
    "dark": {
        "name": "深色主题",
        "file": "ui/styles/main.qss",
    },
    "light": {
        "name": "浅色主题",
        "file": "ui/styles/light.qss",
    },
}


class ThemeManager(QObject):
    """
    主题管理器

    管理应用主题切换，支持深色/浅色主题。
    """

    # 主题变更信号
    theme_changed = pyqtSignal(str)  # 主题名称

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_theme: str = "dark"
        self._settings: dict = {}

        # 确保配置目录存在
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # 加载设置
        self._load_settings()

    @property
    def current_theme(self) -> str:
        """获取当前主题"""
        return self._current_theme

    @property
    def available_themes(self) -> dict:
        """获取可用主题列表"""
        return THEMES

    def _load_settings(self):
        """加载设置"""
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    self._settings = json.load(f)
                self._current_theme = self._settings.get("theme", "dark")
                logger.debug(f"加载设置: {self._settings}")
            except Exception as e:
                logger.warning(f"加载设置失败: {e}")

    def _save_settings(self):
        """保存设置"""
        try:
            self._settings["theme"] = self._current_theme
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, ensure_ascii=False, indent=2)
            logger.debug(f"保存设置: {self._settings}")
        except Exception as e:
            logger.error(f"保存设置失败: {e}")

    def set_theme(self, theme_name: str):
        """
        设置主题

        Args:
            theme_name: 主题名称 ('dark' 或 'light')
        """
        if theme_name not in THEMES:
            logger.error(f"未知主题: {theme_name}")
            return

        if theme_name == self._current_theme:
            return

        self._current_theme = theme_name
        self._save_settings()

        # 加载新主题
        self._apply_theme()

        # 发送信号
        self.theme_changed.emit(theme_name)

        logger.info(f"切换主题: {THEMES[theme_name]['name']}")

    def _apply_theme(self):
        """应用当前主题"""
        app = QApplication.instance()
        if not app:
            return

        theme_info = THEMES.get(self._current_theme)
        if not theme_info:
            return

        # 构建样式文件路径（相对于 sql_viewer_lite 目录）
        style_path = Path(__file__).parent.parent / theme_info["file"]

        if style_path.exists():
            with open(style_path, "r", encoding="utf-8") as f:
                stylesheet = f.read()
            app.setStyleSheet(stylesheet)
            logger.info(f"应用主题: {theme_info['name']}")
        else:
            logger.warning(f"主题文件不存在: {style_path}")

    def load_theme(self):
        """加载并应用保存的主题"""
        self._apply_theme()

    def toggle_theme(self):
        """切换主题"""
        new_theme = "light" if self._current_theme == "dark" else "dark"
        self.set_theme(new_theme)


# 全局单例
_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """获取主题管理器单例"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
