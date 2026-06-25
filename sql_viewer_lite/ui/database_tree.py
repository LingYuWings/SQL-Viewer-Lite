"""
数据库树形控件模块

显示数据库和表的层级结构，类似命令行文件树风格。
"""

import logging
from typing import List, Dict

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from sql_viewer_lite.core.db_connection import get_db_connection

logger = logging.getLogger(__name__)


class DatabaseTreeWidget(QWidget):
    """
    数据库树形控件

    显示数据库和表的层级结构，类似命令行文件树风格。
    """

    # 信号：表被选中
    table_selected = pyqtSignal(str, str)  # database, table

    def __init__(self, parent=None):
        super().__init__(parent)
        self._db_connection = get_db_connection()
        self._all_items: List[Dict] = []  # 存储所有项目用于过滤

        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 搜索框
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("搜索数据库/表...")
        self._search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self._search_input)

        # 树形控件
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setAnimated(True)
        self._tree.setIndentation(20)
        self._tree.setRootIsDecorated(True)
        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._tree.itemExpanded.connect(self._on_item_expanded)

        # 设置样式：显示树线
        self._tree.setStyleSheet("""
            QTreeWidget {
                font-family: "Consolas", "Cascadia Code", "Courier New", monospace;
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 2px 0;
            }
        """)

        layout.addWidget(self._tree)

    def load_databases(self, databases: List[str]):
        """
        加载数据库列表

        Args:
            databases: 数据库名称列表
        """
        self._tree.clear()
        self._all_items.clear()

        for i, db_name in enumerate(databases):
            is_last = (i == len(databases) - 1)
            prefix = "└── " if is_last else "├── "

            # 创建数据库节点
            db_item = QTreeWidgetItem(self._tree)
            db_item.setText(0, f"{prefix}📁 {db_name}")
            db_item.setData(0, Qt.UserRole, {"type": "database", "name": db_name})

            # 添加占位子节点（懒加载）
            placeholder = QTreeWidgetItem(db_item)
            placeholder.setText(0, "    ⏳ 加载中...")
            placeholder.setData(0, Qt.UserRole, {"type": "placeholder"})

            self._all_items.append({
                "type": "database",
                "name": db_name,
                "item": db_item,
            })

        logger.info(f"加载了 {len(databases)} 个数据库到树形控件")

    def _on_item_expanded(self, item: QTreeWidgetItem):
        """项目展开事件"""
        data = item.data(0, Qt.UserRole)
        if not data or data.get("type") != "database":
            return

        # 检查是否是占位子节点
        if item.childCount() == 1:
            child = item.child(0)
            child_data = child.data(0, Qt.UserRole)
            if child_data and child_data.get("type") == "placeholder":
                # 加载表列表
                db_name = data["name"]
                self._load_tables(item, db_name)

    def _load_tables(self, db_item: QTreeWidgetItem, database: str):
        """加载表列表"""
        try:
            # 移除占位子节点
            db_item.takeChild(0)

            # 获取表列表
            tables = self._db_connection.get_tables(database)

            for i, table_info in enumerate(tables):
                table_name = table_info["name"]
                rows = table_info.get("rows", 0)
                engine = table_info.get("engine", "")
                is_last = (i == len(tables) - 1)

                # 构建树线前缀
                prefix = "    └── " if is_last else "    ├── "

                # 创建表节点
                table_item = QTreeWidgetItem(db_item)
                table_item.setText(0, f"{prefix}📋 {table_name}")
                table_item.setData(0, Qt.UserRole, {
                    "type": "table",
                    "database": database,
                    "name": table_name,
                    "info": table_info,
                })

                # 设置 Tooltip
                tooltip = f"表名: {table_name}\n行数: {rows}\n引擎: {engine}"
                table_item.setToolTip(0, tooltip)

                self._all_items.append({
                    "type": "table",
                    "database": database,
                    "name": table_name,
                    "item": table_item,
                })

            # 添加统计信息
            count_item = QTreeWidgetItem(db_item)
            count_item.setText(0, f"    📊 共 {len(tables)} 个表")
            count_item.setData(0, Qt.UserRole, {"type": "info"})
            count_item.setForeground(0, QColor("#888888"))

            logger.info(f"数据库 {database} 加载了 {len(tables)} 个表")

        except Exception as e:
            logger.error(f"加载表列表失败: {e}")
            # 添加错误提示节点
            error_item = QTreeWidgetItem(db_item)
            error_item.setText(0, f"    ❌ 加载失败: {e}")
            error_item.setData(0, Qt.UserRole, {"type": "error"})

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """项目双击事件"""
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        if data.get("type") == "table":
            database = data["database"]
            table = data["name"]
            logger.info(f"双击表: {database}.{table}")
            self.table_selected.emit(database, table)

    def _on_search_changed(self, text: str):
        """搜索文本变更"""
        search_text = text.strip().lower()

        if not search_text:
            # 显示所有项目
            for item_data in self._all_items:
                item = item_data["item"]
                item.setHidden(False)
            return

        # 过滤项目
        for item_data in self._all_items:
            item = item_data["item"]
            name = item_data["name"].lower()

            if search_text in name:
                item.setHidden(False)
                # 如果是表节点，显示其父数据库节点
                if item_data["type"] == "table":
                    parent = item.parent()
                    if parent:
                        parent.setHidden(False)
                        parent.setExpanded(True)
            else:
                # 数据库节点如果有匹配的子表则显示
                if item_data["type"] == "database":
                    has_matching_child = False
                    for child_data in self._all_items:
                        if (child_data["type"] == "table" and
                            child_data["database"] == item_data["name"] and
                            search_text in child_data["name"].lower()):
                            has_matching_child = True
                            break
                    item.setHidden(not has_matching_child)
                    if has_matching_child:
                        item.setExpanded(True)
                else:
                    item.setHidden(True)

    def refresh(self):
        """刷新数据库列表"""
        if self._db_connection.is_connected:
            try:
                databases = self._db_connection.get_databases()
                self.load_databases(databases)
            except Exception as e:
                logger.error(f"刷新数据库列表失败: {e}")
