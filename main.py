#!/usr/bin/env python3
"""
SQL-Viewer Lite - 主程序入口

轻量级 MySQL 数据查看与编辑工具
"""

import sys
import logging
from pathlib import Path

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from sql_viewer_lite.ui.main_window import MainWindow
from sql_viewer_lite.utils.theme_manager import get_theme_manager
from sql_viewer_lite.utils.shortcuts import register_app_shortcuts


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_style_path() -> Path:
    """获取 QSS 样式文件路径"""
    return Path(__file__).parent / "sql_viewer_lite" / "ui" / "styles" / "main.qss"


def load_stylesheet() -> str:
    """加载 QSS 样式表"""
    style_path = get_style_path()
    if style_path.exists():
        with open(style_path, "r", encoding="utf-8") as f:
            return f.read()
    logger.warning(f"样式文件不存在: {style_path}")
    return ""


def main():
    """主函数"""
    logger.info("启动 SQL-Viewer Lite")

    # 启用高 DPI 缩放（必须在 QApplication 创建之前）
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # 创建应用
    app = QApplication(sys.argv)

    # 设置默认字体（启用抗锯齿）
    default_font = QFont("Microsoft YaHei", 10)
    default_font.setStyleHint(QFont.SansSerif)
    default_font.setHintingPreference(QFont.PreferFullHinting)
    app.setFont(default_font)

    app.setApplicationName("SQL-Viewer Lite")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("SQL-Viewer Lite")

    # 初始化主题管理器并加载保存的主题
    theme_manager = get_theme_manager()
    theme_manager.load_theme()

    # 创建并显示主窗口
    window = MainWindow()

    # 同步主题菜单状态
    window._update_theme_menu_state(theme_manager.current_theme)

    # 注册键盘快捷键
    register_app_shortcuts(window)

    window.show()

    logger.info("主窗口显示")

    # 运行应用
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
