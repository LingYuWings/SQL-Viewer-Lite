"""
虚拟滚动表格视图

基于 QTableView 的高性能数据表格，支持大数据量虚拟滚动。
"""

import logging
from typing import Optional, List, Callable

from PyQt5.QtWidgets import (
    QTableView,
    QHeaderView,
    QAbstractItemView,
    QStyledItemDelegate,
)
from PyQt5.QtCore import Qt, pyqtSignal, QModelIndex, QItemSelectionModel
from PyQt5.QtGui import QFont, QColor, QBrush

from sql_viewer_lite.ui.data_table_model import DataTableModel

logger = logging.getLogger(__name__)


class VirtualTableView(QTableView):
    """
    虚拟滚动表格视图
    
    继承 QTableView，提供高性能数据展示。
    配合 DataTableModel 使用，支持大数据量虚拟滚动。
    
    特性：
    - 虚拟滚动：只渲染可见行
    - 行选择支持
    - 自适应列宽
    - 懒加载触发（滚动到底部时）
    """
    
    # 信号：滚动到底部，用于触发懒加载
    scroll_to_bottom = pyqtSignal()
    
    # 信号：单元格被双击
    cell_double_clicked = pyqtSignal(int, int)  # row, column
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 创建并设置模型
        self._model = DataTableModel(self)
        self.setModel(self._model)
        
        # 状态
        self._is_loading = False
        self._columns: List[str] = []
        
        self._init_view()
    
    def _init_view(self):
        """初始化视图配置"""
        # 选择模式：整行选择
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        # 表头配置
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSortIndicatorShown(True)
        
        # 行号列
        vertical_header = self.verticalHeader()
        vertical_header.setDefaultSectionSize(32)
        vertical_header.setMinimumSectionSize(24)
        
        # 网格线
        self.setShowGrid(True)
        
        # 交替行颜色
        self.setAlternatingRowColors(True)
        
        # 滚动条配置
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 连接信号
        self.verticalScrollBar().valueChanged.connect(self._on_scroll)
        self.doubleClicked.connect(self._on_double_clicked)
    
    # ─── 公共接口 ──────────────────────────────────────────────
    
    @property
    def model(self) -> DataTableModel:
        """获取数据模型"""
        return self._model
    
    def set_columns(self, columns: List[str], column_types: dict = None):
        """
        设置列
        
        Args:
            columns: 列名列表
            column_types: 列类型字典
        """
        self._columns = columns
        self._model.set_columns(columns, column_types)
        
        # 自适应列宽
        self._resize_columns()
        
        logger.debug(f"设置 {len(columns)} 列")
    
    def set_data(self, rows: list, total_rows: int, start_index: int = 0):
        """
        设置数据
        
        Args:
            rows: 行数据列表
            total_rows: 总行数
            start_index: 起始行索引
        """
        self._model.set_data(rows, total_rows, start_index)
        self._resize_columns()
    
    def append_data(self, rows: list, start_index: int):
        """
        追加数据（用于懒加载）
        
        Args:
            rows: 行数据列表
            start_index: 起始行索引
        """
        self._model.append_data(rows, start_index)
    
    def clear(self):
        """清除所有数据"""
        self._model.clear()
    
    def set_loading(self, loading: bool):
        """设置加载状态"""
        self._is_loading = loading
        self.setEnabled(not loading)
    
    # ─── 选择操作 ──────────────────────────────────────────────
    
    def get_selected_rows(self) -> List[int]:
        """
        获取选中的行索引列表
        
        Returns:
            选中的行索引列表（已排序）
        """
        selection = self.selectionModel().selectedRows()
        return sorted([index.row() for index in selection])
    
    def get_selected_row(self) -> Optional[int]:
        """
        获取单个选中的行索引
        
        Returns:
            选中的行索引，如果没有选中或多选则返回 None
        """
        rows = self.get_selected_rows()
        if len(rows) == 1:
            return rows[0]
        return None
    
    def select_row(self, row: int):
        """选中指定行"""
        index = self._model.index(row, 0)
        self.setCurrentIndex(index)
        self.selectRow(row)
    
    def select_all(self):
        """全选"""
        self.selectAll()
    
    def clear_selection(self):
        """清除选择"""
        self.clearSelection()
    
    # ─── 列操作 ──────────────────────────────────────────────
    
    def _resize_columns(self):
        """自适应列宽"""
        if not self._columns:
            return
        
        header = self.horizontalHeader()
        for i in range(len(self._columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        # 最后一列拉伸
        if len(self._columns) > 0:
            header.setSectionResizeMode(len(self._columns) - 1, QHeaderView.Stretch)
    
    # ─── 滚动处理 ──────────────────────────────────────────────
    
    def _on_scroll(self, value: int):
        """滚动事件处理"""
        if self._is_loading:
            return
        
        scrollbar = self.verticalScrollBar()
        if value == scrollbar.maximum():
            # 滚动到底部，触发懒加载
            logger.debug("滚动到底部，触发懒加载")
            self.scroll_to_bottom.emit()
    
    def scroll_to_row(self, row: int):
        """滚动到指定行"""
        index = self._model.index(row, 0)
        if index.isValid():
            self.scrollTo(index, QAbstractItemView.EnsureVisible)
    
    # ─── 事件处理 ──────────────────────────────────────────────
    
    def _on_double_clicked(self, index: QModelIndex):
        """双击事件处理"""
        if index.isValid():
            self.cell_double_clicked.emit(index.row(), index.column())
    
    def keyPressEvent(self, event):
        """按键事件处理"""
        # Ctrl+C: 复制
        if event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            self._copy_selection()
            return
        
        # Ctrl+A: 全选
        if event.key() == Qt.Key_A and event.modifiers() == Qt.ControlModifier:
            self.select_all()
            return
        
        # Delete: 删除选中行（标记）
        if event.key() == Qt.Key_Delete:
            self._delete_selection()
            return
        
        super().keyPressEvent(event)
    
    def _copy_selection(self):
        """复制选中内容到剪贴板"""
        from PyQt5.QtWidgets import QApplication
        
        selection = self.selectionModel().selectedIndexes()
        if not selection:
            return
        
        # 按行分组
        rows = {}
        for index in selection:
            row = index.row()
            if row not in rows:
                rows[row] = {}
            rows[row][index.column()] = index.data(Qt.DisplayRole)
        
        # 构建制表符分隔的文本
        lines = []
        for row in sorted(rows.keys()):
            cells = []
            for col in sorted(rows[row].keys()):
                value = rows[row][col]
                cells.append(str(value) if value is not None else "NULL")
            lines.append("\t".join(cells))
        
        text = "\n".join(lines)
        QApplication.clipboard().setText(text)
        
        logger.debug(f"复制 {len(rows)} 行到剪贴板")
    
    def _delete_selection(self):
        """删除选中行（标记）"""
        rows = self.get_selected_rows()
        if not rows:
            return
        
        # 通过模型标记删除
        for row in rows:
            self._model.mark_deleted(row)
        
        logger.debug(f"标记删除 {len(rows)} 行")
