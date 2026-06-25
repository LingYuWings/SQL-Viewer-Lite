"""
国际化模块

提供中英文翻译支持。
"""

import json
import logging
import threading
from pathlib import Path
from typing import Optional, Dict

from PyQt5.QtCore import QTranslator, QLocale

logger = logging.getLogger(__name__)

# 配置目录
CONFIG_DIR = Path.home() / ".sql_viewer_lite"
SETTINGS_FILE = CONFIG_DIR / "settings.json"

# 翻译文件目录
TRANSLATIONS_DIR = Path(__file__).parent.parent / "translations"

# 支持的语言
SUPPORTED_LANGUAGES = {
    "zh_CN": {
        "name": "中文",
        "native": "中文",
    },
    "en_US": {
        "name": "English",
        "native": "English",
    },
}

# 内嵌翻译（不依赖外部 .qm 文件）
TRANSLATIONS = {
    "zh_CN": {
        # 菜单
        "文件(&F)": "文件(&F)",
        "新建连接(&N)": "新建连接(&N)",
        "断开连接(&D)": "断开连接(&D)",
        "退出(&Q)": "退出(&Q)",
        "编辑(&E)": "编辑(&E)",
        "撤销(&U)": "撤销(&U)",
        "重做(&R)": "重做(&R)",
        "复制(&C)": "复制(&C)",
        "粘贴(&V)": "粘贴(&V)",
        "视图(&V)": "视图(&V)",
        "刷新(&R)": "刷新(&R)",
        "侧边栏(&S)": "侧边栏(&S)",
        "状态栏(&T)": "状态栏(&T)",
        "主题(&T)": "主题(&T)",
        "深色主题": "深色主题",
        "浅色主题": "浅色主题",
        "工具(&T)": "工具(&T)",
        "SQL 执行器(&S)": "SQL 执行器(&S)",
        "数据导出(&E)": "数据导出(&E)",
        "设置(&P)": "设置(&P)",
        "帮助(&H)": "帮助(&H)",
        "关于(&A)": "关于(&A)",
        "文档(&D)": "文档(&D)",
        # 按钮
        "测试连接": "测试连接",
        "登录": "登录",
        "取消": "取消",
        "确定": "确定",
        "保存": "保存",
        "删除": "删除",
        "刷新": "刷新",
        "执行": "执行",
        "新增行": "新增行",
        "删除行": "删除行",
        "提交更改": "提交更改",
        "撤销": "撤销",
        # 状态栏
        "未连接": "未连接",
        "已连接": "已连接",
        # 错误消息
        "连接失败": "连接失败",
        "执行失败": "执行失败",
        "加载失败": "加载失败",
        # SQL 执行器
        "SQL 执行器": "SQL 执行器",
        "查询历史": "查询历史",
        "等待执行...": "等待执行...",
    },
    "en_US": {
        # 菜单
        "文件(&F)": "&File",
        "新建连接(&N)": "&New Connection",
        "断开连接(&D)": "&Disconnect",
        "退出(&Q)": "&Quit",
        "编辑(&E)": "&Edit",
        "撤销(&U)": "&Undo",
        "重做(&R)": "&Redo",
        "复制(&C)": "&Copy",
        "粘贴(&V)": "&Paste",
        "视图(&V)": "&View",
        "刷新(&R)": "&Refresh",
        "侧边栏(&S)": "&Sidebar",
        "状态栏(&T)": "Status &Bar",
        "主题(&T)": "&Theme",
        "深色主题": "Dark Theme",
        "浅色主题": "Light Theme",
        "工具(&T)": "&Tools",
        "SQL 执行器(&S)": "&SQL Executor",
        "数据导出(&E)": "Data &Export",
        "设置(&P)": "&Preferences",
        "帮助(&H)": "&Help",
        "关于(&A)": "&About",
        "文档(&D)": "&Documentation",
        # 按钮
        "测试连接": "Test Connection",
        "登录": "Login",
        "取消": "Cancel",
        "确定": "OK",
        "保存": "Save",
        "删除": "Delete",
        "刷新": "Refresh",
        "执行": "Execute",
        "新增行": "Add Row",
        "删除行": "Delete Row",
        "提交更改": "Commit Changes",
        "撤销": "Undo",
        # 状态栏
        "未连接": "Disconnected",
        "已连接": "Connected",
        # 错误消息
        "连接失败": "Connection Failed",
        "执行失败": "Execution Failed",
        "加载失败": "Load Failed",
        # SQL 执行器
        "SQL 执行器": "SQL Executor",
        "查询历史": "Query History",
        "等待执行...": "Waiting to execute...",
    },
}


class I18nManager:
    """
    国际化管理器

    管理应用语言切换和翻译加载。
    """

    def __init__(self):
        self._current_language: str = "zh_CN"
        self._translator: QTranslator = QTranslator()
        self._settings: dict = {}

        # 确保配置目录存在
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # 加载设置
        self._load_settings()

    @property
    def current_language(self) -> str:
        """获取当前语言"""
        return self._current_language

    @property
    def available_languages(self) -> dict:
        """获取可用语言列表"""
        return SUPPORTED_LANGUAGES

    def _load_settings(self):
        """加载设置"""
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    self._settings = json.load(f)
                self._current_language = self._settings.get("language", "zh_CN")
            except Exception as e:
                logger.warning(f"加载国际化设置失败: {e}")

    def _save_settings(self):
        """保存设置"""
        try:
            self._settings["language"] = self._current_language
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存设置失败: {e}")

    def set_language(self, language: str):
        """
        设置语言

        Args:
            language: 语言代码 ('zh_CN' 或 'en_US')
        """
        if language not in SUPPORTED_LANGUAGES:
            logger.error(f"不支持的语言: {language}")
            return

        if language == self._current_language:
            return

        self._current_language = language
        self._save_settings()

        logger.info(f"切换语言: {SUPPORTED_LANGUAGES[language]['name']}")

    def translate(self, text: str) -> str:
        """
        翻译文本

        Args:
            text: 原文

        Returns:
            翻译后的文本
        """
        translations = TRANSLATIONS.get(self._current_language, {})
        return translations.get(text, text)

    def load_translations(self):
        """加载翻译文件（预留接口）"""
        # 检查是否有外部 .qm 文件
        qm_file = TRANSLATIONS_DIR / f"{self._current_language}.qm"
        if qm_file.exists():
            self._translator.load(str(qm_file))


# 全局单例
_i18n_manager: Optional[I18nManager] = None
_singleton_lock = threading.Lock()


def get_i18n_manager() -> I18nManager:
    """获取国际化管理器单例（线程安全）"""
    global _i18n_manager
    if _i18n_manager is None:
        with _singleton_lock:
            if _i18n_manager is None:
                _i18n_manager = I18nManager()
    return _i18n_manager


def tr(text: str) -> str:
    """
    翻译文本（便捷函数）

    Args:
        text: 原文

    Returns:
        翻译后的文本
    """
    return get_i18n_manager().translate(text)
