"""
表结构查看组件

显示表的字段信息、索引、约束等。
"""

import logging
from typing import List, Dict, Any

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QTabWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from sql_viewer_lite.core.db_connection import get_db_connection

logger = logging.getLogger(__name__)


class TableStructureView(QWidget):
    """
    表结构视图

    显示表的字段信息，包括字段名、类型、是否可空、键、默认值、额外信息。
    """

    def __init__(self, database: str, table: str, parent=None):
        super().__init__(parent)
        self._database = database
        self._table = table
        self._db_connection = get_db_connection()

        self._init_ui()
        self._load_structure()

    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        title_label = QLabel(f"表结构: {self._database}.{self._table}")
        title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(title_label)

        # 表格
        self._table_widget = QTableWidget()
        self._table_widget.setAlternatingRowColors(True)
        self._table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self._table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table_widget.horizontalHeader().setStretchLastSection(True)
        self._table_widget.verticalHeader().setDefaultSectionSize(32)
        layout.addWidget(self._table_widget)

    def _load_structure(self):
        """加载表结构"""
        try:
            structure = self._db_connection.get_table_structure(
                self._database, self._table
            )
            self._display_structure(structure)
            logger.info(
                f"加载了表 {self._database}.{self._table} 的结构，共 {len(structure)} 个字段"
            )
        except Exception as e:
            logger.error(f"加载表结构失败: {e}")
            self._display_error(str(e))

    def _display_structure(self, structure: List[Dict[str, Any]]):
        """显示表结构"""
        # 设置列
        columns = ["字段名", "类型", "是否可空", "键", "默认值", "额外信息", "注释"]
        self._table_widget.setColumnCount(len(columns))
        self._table_widget.setHorizontalHeaderLabels(columns)

        # 填充数据
        self._table_widget.setRowCount(len(structure))

        for row_idx, field in enumerate(structure):
            # 字段名
            name_item = QTableWidgetItem(field.get("name", ""))
            name_item.setFont(QFont("Consolas", 10))
            self._table_widget.setItem(row_idx, 0, name_item)

            # 类型
            type_item = QTableWidgetItem(field.get("type", ""))
            type_item.setFont(QFont("Consolas", 10))
            self._table_widget.setItem(row_idx, 1, type_item)

            # 是否可空
            null_value = field.get("null", "")
            null_item = QTableWidgetItem(null_value)
            if null_value == "YES":
                null_item.setForeground(QColor("#4CAF50"))  # 绿色
            else:
                null_item.setForeground(QColor("#F44336"))  # 红色
            self._table_widget.setItem(row_idx, 2, null_item)

            # 键
            key_value = field.get("key", "")
            key_item = QTableWidgetItem(key_value)
            if key_value == "PRI":
                key_item.setForeground(QColor("#FFD700"))  # 金色
                key_item.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
            elif key_value == "UNI":
                key_item.setForeground(QColor("#2196F3"))  # 蓝色
            elif key_value == "MUL":
                key_item.setForeground(QColor("#FF9800"))  # 橙色
            self._table_widget.setItem(row_idx, 3, key_item)

            # 默认值
            default_value = field.get("default", "")
            if default_value is None:
                default_display = "NULL"
                default_item = QTableWidgetItem(default_display)
                default_item.setForeground(QColor("#808080"))
            else:
                default_item = QTableWidgetItem(str(default_value))
            self._table_widget.setItem(row_idx, 4, default_item)

            # 额外信息
            extra_item = QTableWidgetItem(field.get("extra", ""))
            self._table_widget.setItem(row_idx, 5, extra_item)

            # 注释
            comment_item = QTableWidgetItem(field.get("comment", ""))
            self._table_widget.setItem(row_idx, 6, comment_item)

        # 调整列宽
        header = self._table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Stretch)

    def _display_error(self, error_message: str):
        """显示错误信息"""
        self._table_widget.setRowCount(1)
        self._table_widget.setColumnCount(1)
        self._table_widget.setHorizontalHeaderLabels(["错误"])

        error_item = QTableWidgetItem(f"加载表结构失败: {error_message}")
        error_item.setForeground(QColor("#F44336"))
        self._table_widget.setItem(0, 0, error_item)

    def refresh(self):
        """刷新表结构"""
        self._load_structure()


class TableInfoView(QWidget):
    """
    表信息视图

    显示表的基本信息，如行数、引擎、字符集、大小等。
    """

    def __init__(
        self, database: str, table: str, table_info: Dict[str, Any] = None, parent=None
    ):
        super().__init__(parent)
        self._database = database
        self._table = table
        self._table_info = table_info or {}
        self._db_connection = get_db_connection()

        self._init_ui()

        if not self._table_info:
            self._load_table_info()

    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 标题
        title_label = QLabel(f"表信息: {self._database}.{self._table}")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        layout.addWidget(title_label)

        # 信息网格
        info_layout = QVBoxLayout()
        info_layout.setSpacing(12)

        # 表名
        self._add_info_row(info_layout, "表名", self._table)

        # 行数
        self._rows_label = self._add_info_row(info_layout, "行数", "加载中...")

        # 引擎
        self._engine_label = self._add_info_row(info_layout, "引擎", "加载中...")

        # 字符集
        self._charset_label = self._add_info_row(info_layout, "字符集", "加载中...")

        # 大小
        self._size_label = self._add_info_row(info_layout, "数据大小", "加载中...")

        # 注释
        self._comment_label = self._add_info_row(info_layout, "注释", "加载中...")

        layout.addLayout(info_layout)
        layout.addStretch()

        # 更新显示
        if self._table_info:
            self._update_display()

    def _add_info_row(self, layout: QVBoxLayout, label: str, value: str) -> QLabel:
        """添加信息行"""
        row_layout = QHBoxLayout()

        label_widget = QLabel(f"{label}:")
        label_widget.setFixedWidth(100)
        label_widget.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        row_layout.addWidget(label_widget)

        value_widget = QLabel(value)
        value_widget.setFont(QFont("Microsoft YaHei", 11))
        row_layout.addWidget(value_widget)

        row_layout.addStretch()
        layout.addLayout(row_layout)

        return value_widget

    def _load_table_info(self):
        """加载表信息"""
        try:
            tables = self._db_connection.get_tables(self._database)
            for table_info in tables:
                if table_info.get("name") == self._table:
                    self._table_info = table_info
                    self._update_display()
                    break
        except Exception as e:
            logger.error(f"加载表信息失败: {e}")

    def _update_display(self):
        """更新显示"""
        self._rows_label.setText(str(self._table_info.get("rows", "未知")))
        self._engine_label.setText(self._table_info.get("engine", "未知"))
        self._charset_label.setText(self._table_info.get("charset", "未知"))

        # 格式化大小
        size_bytes = self._table_info.get("size", 0)
        if size_bytes < 1024:
            size_str = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            size_str = f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
        self._size_label.setText(size_str)

        self._comment_label.setText(self._table_info.get("comment", "") or "无")

    def refresh(self):
        """刷新表信息"""
        self._load_table_info()
