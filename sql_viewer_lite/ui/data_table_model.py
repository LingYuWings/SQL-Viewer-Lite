"""
数据表格模型

基于 QAbstractTableModel 的虚拟滚动数据模型，支持大数据量高效显示。
"""

import logging
from typing import Optional, List, Dict, Any, Set, Tuple
from dataclasses import dataclass, field

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex

logger = logging.getLogger(__name__)


class DataTableModel(QAbstractTableModel):
    """
    数据表格模型
    
    继承 QAbstractTableModel，提供虚拟滚动支持。
    只加载和管理当前可见区域的数据，支持大数据量高效显示。
    
    特性：
    - 内存高效：只存储已加载的数据行
    - 支持编辑：通过 DiffTracker 跟踪修改
    - 支持排序和筛选（通过 SQL）
    - 线程安全：数据加载在主线程，SQL 执行可在后台线程
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 列元数据
        self._columns: List[str] = []
        self._column_types: Dict[str, str] = {}  # 列名 → 类型
        
        # 数据存储：{row_index: {col_name: value}}
        self._data_cache: Dict[int, Dict[str, Any]] = {}
        
        # 编辑状态跟踪
        self._modified_cells: Dict[Tuple[int, str], Any] = {}  # {(row, col): original_value}
        self._new_rows: Set[int] = set()
        self._deleted_rows: Set[int] = set()
        
        # 元信息
        self._total_rows: int = 0
        self._loaded_row_start: int = -1
        self._loaded_row_end: int = -1
    
    # ─── QAbstractTableModel 必须实现的方法 ──────────────────────
    
    def rowCount(self, parent=QModelIndex()) -> int:
        """返回行数"""
        if parent.isValid():
            return 0
        return self._total_rows
    
    def columnCount(self, parent=QModelIndex()) -> int:
        """返回列数"""
        if parent.isValid():
            return 0
        return len(self._columns)
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """
        返回数据
        
        支持的角色：
        - Qt.DisplayRole: 显示文本
        - Qt.EditRole: 编辑文本
        - Qt.UserRole: 原始值
        - Qt.BackgroundRole: 背景色（用于编辑状态高亮）
        - Qt.ForegroundRole: 前景色（用于 NULL 值显示）
        - Qt.FontRole: 字体（用于 NULL 值斜体）
        - Qt.ToolTipRole: 工具提示
        """
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()
        
        if col >= len(self._columns):
            return None
        
        col_name = self._columns[col]
        
        # 获取行数据
        row_data = self._data_cache.get(row)
        if row_data is None:
            return None
        
        value = row_data.get(col_name)
        
        # 根据角色返回
        if role in (Qt.DisplayRole, Qt.EditRole):
            if value is None:
                return "NULL" if role == Qt.DisplayRole else ""
            return str(value)
        
        elif role == Qt.UserRole:
            return value  # 返回原始值
        
        elif role == Qt.BackgroundRole:
            # 编辑状态高亮
            key = (row, col_name)
            if key in self._modified_cells:
                from PyQt5.QtGui import QColor
                return QColor(255, 255, 200)  # 浅黄色 - 已修改
            elif row in self._new_rows:
                from PyQt5.QtGui import QColor
                return QColor(200, 255, 200)  # 浅绿色 - 新增行
            elif row in self._deleted_rows:
                from PyQt5.QtGui import QColor
                return QColor(255, 200, 200)  # 浅红色 - 删除行
        
        elif role == Qt.ForegroundRole:
            # NULL 值灰色显示
            if value is None:
                from PyQt5.QtGui import QColor
                return QColor(128, 128, 128)
        
        elif role == Qt.FontRole:
            # NULL 值斜体
            if value is None:
                from PyQt5.QtGui import QFont
                return QFont("Microsoft YaHei", 10, QFont.StyleItalic)
        
        elif role == Qt.ToolTipRole:
            if value is None:
                return "NULL"
            return str(value)
        
        return None
    
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        """
        设置数据
        
        支持编辑单元格并跟踪修改。
        """
        if not index.isValid() or role != Qt.EditRole:
            return False
        
        row = index.row()
        col = index.column()
        
        if col >= len(self._columns):
            return False
        
        col_name = self._columns[col]
        row_data = self._data_cache.get(row)
        if row_data is None:
            return False
        
        old_value = row_data.get(col_name)
        
        # 转换显示值回原始值
        if value == "NULL":
            new_value = None
        elif value == "":
            new_value = ""
        else:
            # 尝试保持原始类型
            if old_value is not None:
                try:
                    new_value = type(old_value)(value)
                except (ValueError, TypeError):
                    new_value = value
            else:
                new_value = value
        
        # 比较是否真的改变
        if old_value == new_value:
            return False
        
        # 更新缓存
        row_data[col_name] = new_value
        
        # 跟踪修改
        key = (row, col_name)
        if key in self._modified_cells:
            # 如果改回原值，移除跟踪
            if self._modified_cells[key] == new_value:
                del self._modified_cells[key]
            else:
                self._modified_cells[key] = new_value
        else:
            self._modified_cells[key] = new_value
        
        # 通知视图更新
        self.dataChanged.emit(index, index, [role])
        return True
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        """返回表头数据"""
        if role != Qt.DisplayRole:
            return None
        
        if orientation == Qt.Horizontal:
            if 0 <= section < len(self._columns):
                return self._columns[section]
        elif orientation == Qt.Vertical:
            return section + 1  # 行号从 1 开始
        
        return None
    
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """返回项目标志"""
        if not index.isValid():
            return Qt.NoItemFlags
        
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        
        # 删除的行不可编辑
        if index.row() in self._deleted_rows:
            return flags
        
        # 支持编辑
        flags |= Qt.ItemIsEditable
        
        return flags
    
    # ─── 数据加载方法 ──────────────────────────────────────────
    
    def set_columns(self, columns: List[str], column_types: Dict[str, str] = None):
        """
        设置列元数据
        
        Args:
            columns: 列名列表
            column_types: 列类型字典，可选
        """
        self.beginResetModel()
        self._columns = columns
        self._column_types = column_types or {}
        self.endResetModel()
        
        logger.debug(f"设置列: {len(columns)} 列")
    
    def set_data(self, rows: List[Dict[str, Any]], total_rows: int, 
                 start_index: int = 0):
        """
        设置数据
        
        Args:
            rows: 行数据列表，每个元素是 {col_name: value}
            total_rows: 总行数（用于分页）
            start_index: 起始行索引
        """
        self.beginResetModel()
        
        # 清除旧数据
        self._data_cache.clear()
        
        # 加载新数据
        for i, row_data in enumerate(rows):
            self._data_cache[start_index + i] = row_data
        
        self._total_rows = total_rows
        self._loaded_row_start = start_index
        self._loaded_row_end = start_index + len(rows) - 1
        
        self.endResetModel()
        
        logger.debug(
            f"加载数据: {len(rows)} 行, "
            f"总行数 {total_rows}, "
            f"范围 [{start_index}, {self._loaded_row_end}]"
        )
    
    def append_data(self, rows: List[Dict[str, Any]], start_index: int):
        """
        追加数据（用于懒加载）
        
        Args:
            rows: 行数据列表
            start_index: 起始行索引
        """
        if not rows:
            return
        
        first_row = start_index
        last_row = start_index + len(rows) - 1
        
        # 通知视图即将插入行
        self.beginInsertRows(QModelIndex(), first_row, last_row)
        
        for i, row_data in enumerate(rows):
            self._data_cache[start_index + i] = row_data
        
        self._loaded_row_end = max(self._loaded_row_end, last_row)
        
        self.endInsertRows()
        
        logger.debug(f"追加数据: {len(rows)} 行, 范围 [{first_row}, {last_row}]")
    
    def clear(self):
        """清除所有数据"""
        self.beginResetModel()
        self._data_cache.clear()
        self._total_rows = 0
        self._loaded_row_start = -1
        self._loaded_row_end = -1
        self.endResetModel()
    
    # ─── 编辑状态管理 ──────────────────────────────────────────
    
    def has_changes(self) -> bool:
        """是否有未提交的更改"""
        return bool(self._modified_cells or self._new_rows or self._deleted_rows)
    
    def get_modified_cells(self) -> Dict[Tuple[int, str], Any]:
        """获取所有修改的单元格"""
        return self._modified_cells.copy()
    
    def get_new_rows(self) -> Set[int]:
        """获取新增行索引"""
        return self._new_rows.copy()
    
    def get_deleted_rows(self) -> Set[int]:
        """获取删除行索引"""
        return self._deleted_rows.copy()
    
    def add_new_row(self) -> int:
        """
        添加新行
        
        Returns:
            新行的索引
        """
        new_row = self._total_rows
        self._total_rows += 1
        
        # 通知视图插入行
        self.beginInsertRows(QModelIndex(), new_row, new_row)
        
        # 初始化空行
        self._data_cache[new_row] = {col: None for col in self._columns}
        self._new_rows.add(new_row)
        
        self.endInsertRows()
        
        logger.debug(f"添加新行: {new_row}")
        return new_row
    
    def mark_deleted(self, row: int):
        """
        标记行为删除
        
        Args:
            row: 行索引
        """
        if row in self._new_rows:
            # 新增行直接移除
            self._new_rows.discard(row)
            self.beginRemoveRows(QModelIndex(), row, row)
            del self._data_cache[row]
            self._total_rows -= 1
            self.endRemoveRows()
        else:
            self._deleted_rows.add(row)
            # 通知视图更新（用于高亮显示）
            left = self.index(row, 0)
            right = self.index(row, len(self._columns) - 1)
            self.dataChanged.emit(left, right)
        
        logger.debug(f"标记删除行: {row}")
    
    def unmark_deleted(self, row: int):
        """取消删除标记"""
        if row in self._deleted_rows:
            self._deleted_rows.discard(row)
            # 通知视图更新
            left = self.index(row, 0)
            right = self.index(row, len(self._columns) - 1)
            self.dataChanged.emit(left, right)
    
    def clear_changes(self):
        """清除所有编辑状态"""
        self._modified_cells.clear()
        self._new_rows.clear()
        self._deleted_rows.clear()
        
        # 通知视图刷新
        if self._total_rows > 0:
            left = self.index(0, 0)
            right = self.index(self._total_rows - 1, len(self._columns) - 1)
            self.dataChanged.emit(left, right)
    
    # ─── 查询方法 ──────────────────────────────────────────────
    
    def get_row_data(self, row: int) -> Optional[Dict[str, Any]]:
        """获取指定行的数据"""
        return self._data_cache.get(row)
    
    def get_cell_value(self, row: int, col_name: str) -> Any:
        """获取单元格值"""
        row_data = self._data_cache.get(row)
        if row_data:
            return row_data.get(col_name)
        return None
    
    def is_row_loaded(self, row: int) -> bool:
        """检查行是否已加载"""
        return row in self._data_cache
    
    def get_loaded_range(self) -> Tuple[int, int]:
        """获取已加载的数据范围"""
        return self._loaded_row_start, self._loaded_row_end
    
    def get_total_rows(self) -> int:
        """获取总行数"""
        return self._total_rows
