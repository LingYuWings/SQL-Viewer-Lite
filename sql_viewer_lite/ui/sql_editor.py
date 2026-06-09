"""
SQL 执行器组件

提供 SQL 输入、执行、结果显示功能。
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSplitter,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QDockWidget,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor

from sql_viewer_lite.core.db_connection import get_db_connection

logger = logging.getLogger(__name__)


class SQLHistoryItem:
    """SQL 历史记录项"""

    def __init__(self, sql: str, timestamp: datetime = None, execution_time: float = 0):
        self.sql = sql
        self.timestamp = timestamp or datetime.now()
        self.execution_time = execution_time
        self.row_count = 0

    def __str__(self):
        return f"{self.timestamp.strftime('%H:%M:%S')} | {self.sql[:50]}..."


class SQLEditorWidget(QPlainTextEdit):
    """
    SQL 编辑器控件

    支持等宽字体、Tab 缩进、快捷键执行。
    """

    # 信号：执行查询
    execute_query = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_editor()

    def _init_editor(self):
        """初始化编辑器"""
        # 等宽字体
        font = QFont("Consolas", 12)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)

        # 编辑器设置
        self.setTabStopDistance(40)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

        # 占位提示文本
        self.setPlaceholderText(
            "在此输入 SQL 查询...\n\n提示: 使用 Ctrl+Enter 或点击执行按钮运行查询"
        )

    def keyPressEvent(self, event):
        """按键事件"""
        # Ctrl+Enter 或 Ctrl+E 执行查询
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
            self.execute_query.emit(self.toPlainText())
            return

        super().keyPressEvent(event)


class SQLHistoryWidget(QWidget):
    """
    SQL 历史记录控件
    """

    # 信号：选择历史记录
    history_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._history: List[SQLHistoryItem] = []
        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        header = QLabel("查询历史")
        header.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        layout.addWidget(header)

        # 历史列表
        self._list_widget = QListWidget()
        self._list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._list_widget)

        # 清除按钮
        clear_btn = QPushButton("清除历史")
        clear_btn.clicked.connect(self._clear_history)
        layout.addWidget(clear_btn)

    def add_history(self, item: SQLHistoryItem):
        """添加历史记录"""
        self._history.insert(0, item)

        # 添加到列表
        list_item = QListWidgetItem(str(item))
        list_item.setData(Qt.UserRole, item.sql)
        self._list_widget.insertItem(0, list_item)

        # 限制最多 100 条
        if len(self._history) > 100:
            self._history.pop()
            self._list_widget.takeItem(self._list_widget.count() - 1)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """双击历史记录"""
        sql = item.data(Qt.UserRole)
        if sql:
            self.history_selected.emit(sql)

    def _clear_history(self):
        """清除历史记录"""
        self._history.clear()
        self._list_widget.clear()


class SQLExecutionResult:
    """SQL 执行结果"""

    def __init__(self):
        self.columns: List[str] = []
        self.rows: List[Dict[str, Any]] = []
        self.affected_rows: int = 0
        self.execution_time: float = 0
        self.message: str = ""


class SQLExecutorWidget(QWidget):
    """
    SQL 执行器主组件

    包含 SQL 编辑器、执行按钮、结果表格。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._db_connection = get_db_connection()
        self._result = SQLExecutionResult()

        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # SQL 编辑器
        self._editor = SQLEditorWidget()
        self._editor.setMinimumHeight(120)
        self._editor.execute_query.connect(self._on_execute)
        layout.addWidget(self._editor)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        execute_btn = QPushButton("执行 (Ctrl+Enter)")
        execute_btn.setFixedHeight(36)
        execute_btn.clicked.connect(self._on_execute_click)
        btn_layout.addWidget(execute_btn)

        btn_layout.addStretch()

        # 执行时间显示
        self._time_label = QLabel("")
        self._time_label.setStyleSheet("color: #888888;")
        btn_layout.addWidget(self._time_label)

        layout.addLayout(btn_layout)

        # 分割器：结果表格和历史记录
        splitter = QSplitter(Qt.Horizontal)

        # 结果区域
        result_widget = QWidget()
        result_layout = QVBoxLayout(result_widget)
        result_layout.setContentsMargins(0, 0, 0, 0)

        self._result_label = QLabel("等待执行...")
        result_layout.addWidget(self._result_label)

        self._result_table = QTableWidget()
        self._result_table.setAlternatingRowColors(True)
        self._result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        result_layout.addWidget(self._result_table)

        splitter.addWidget(result_widget)

        # 历史记录
        self._history_widget = SQLHistoryWidget()
        self._history_widget.history_selected.connect(self._on_history_selected)
        splitter.addWidget(self._history_widget)

        splitter.setSizes([600, 200])

        layout.addWidget(splitter)

    def _on_execute_click(self):
        """点击执行按钮"""
        sql = self._editor.toPlainText().strip()
        if sql:
            self._on_execute(sql)

    def _on_execute(self, sql: str):
        """执行 SQL"""
        if not self._db_connection.is_connected:
            QMessageBox.warning(self, "警告", "请先连接到数据库")
            return

        try:
            import time

            start_time = time.time()

            # 执行查询
            result, row_count, message = self._db_connection.execute_query(sql)

            execution_time = time.time() - start_time

            # 更新结果
            self._result.execution_time = execution_time
            self._result.message = message

            if result is not None:
                # SELECT 查询
                self._result.columns = list(result[0].keys()) if result else []
                self._result.rows = result
                self._result.affected_rows = len(result)
                self._display_result(result)
            else:
                # INSERT/UPDATE/DELETE 查询
                self._result.affected_rows = row_count
                self._result_label.setText(f"执行成功，影响 {row_count} 行")
                self._result_table.clear()

            # 更新时间显示
            self._time_label.setText(f"耗时: {execution_time:.3f}s")

            # 添加到历史记录
            history_item = SQLHistoryItem(sql)
            history_item.row_count = self._result.affected_rows
            history_item.execution_time = execution_time
            self._history_widget.add_history(history_item)

        except Exception as e:
            QMessageBox.critical(self, "执行失败", str(e))
            logger.error(f"SQL 执行失败: {e}")

    def _display_result(self, data: List[Dict[str, Any]]):
        """显示查询结果"""
        if not data:
            self._result_label.setText("查询结果为空")
            self._result_table.clear()
            return

        columns = list(data[0].keys())

        self._result_label.setText(f"返回 {len(data)} 行")

        # 设置表格
        self._result_table.setColumnCount(len(columns))
        self._result_table.setHorizontalHeaderLabels(columns)
        self._result_table.setRowCount(len(data))

        for row_idx, row_data in enumerate(data):
            for col_idx, col_name in enumerate(columns):
                value = row_data.get(col_name)
                item = QTableWidgetItem(str(value) if value is not None else "NULL")
                self._result_table.setItem(row_idx, col_idx, item)

        self._result_table.resizeColumnsToContents()

    def _on_history_selected(self, sql: str):
        """选择历史记录"""
        self._editor.setPlainText(sql)

    def set_sql(self, sql: str):
        """设置 SQL 文本"""
        self._editor.setPlainText(sql)


def create_sql_dock_widget(parent=None) -> QDockWidget:
    """创建 SQL 执行器停靠窗口"""
    dock = QDockWidget("SQL 执行器", parent)
    dock.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea)

    executor = SQLExecutorWidget()
    dock.setWidget(executor)

    return dock
