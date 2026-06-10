"""
数据表格视图组件

提供数据表格展示、分页、排序、筛选、编辑功能。
使用 VirtualTableView + DataTableModel 实现虚拟滚动。
"""

import logging
from typing import Optional, List, Dict, Any, Set, Tuple
from dataclasses import dataclass, field

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QPushButton,
    QLabel,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QMessageBox,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QBrush

from sql_viewer_lite.core.db_connection import get_db_connection, QueryError
from sql_viewer_lite.core.db_worker import ProcessWorker, get_worker_manager
from sql_viewer_lite.ui.virtual_table_view import VirtualTableView
from sql_viewer_lite.ui.data_table_model import DataTableModel

logger = logging.getLogger(__name__)

# 分页大小选项
PAGE_SIZES = [100, 200, 500, 1000, 2000]

# 编辑状态颜色
EDITED_COLOR = QColor(255, 255, 200)  # 浅黄色
NEW_ROW_COLOR = QColor(200, 255, 200)  # 浅绿色
DELETED_COLOR = QColor(255, 200, 200)  # 浅红色


@dataclass
class CellDiff:
    """单元格差异"""

    row: int
    column: str
    original_value: Any
    new_value: Any


@dataclass
class RowDiff:
    """行差异（新增行）"""

    row_index: int
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiffTracker:
    """
    差异追踪器

    记录所有修改、新增、删除操作。
    """

    # 修改的单元格: {(row, column): CellDiff}
    modified_cells: Dict[Tuple[int, str], CellDiff] = field(default_factory=dict)

    # 新增的行: {row_index: RowDiff}
    new_rows: Dict[int, RowDiff] = field(default_factory=dict)

    # 删除的行: set of row indices
    deleted_rows: Set[int] = field(default_factory=set)

    def clear(self):
        """清除所有差异"""
        self.modified_cells.clear()
        self.new_rows.clear()
        self.deleted_rows.clear()

    def has_changes(self) -> bool:
        """是否有未提交的更改"""
        return bool(self.modified_cells or self.new_rows or self.deleted_rows)

    def add_modification(
        self, row: int, column: str, original_value: Any, new_value: Any
    ):
        """添加修改记录"""
        key = (row, column)
        if key in self.modified_cells:
            # 更新现有记录
            diff = self.modified_cells[key]
            diff.new_value = new_value
            # 如果改回原值，移除记录
            if diff.original_value == new_value:
                del self.modified_cells[key]
        else:
            self.modified_cells[key] = CellDiff(
                row=row,
                column=column,
                original_value=original_value,
                new_value=new_value,
            )

    def add_new_row(self, row_index: int, data: Dict[str, Any] = None):
        """添加新行记录"""
        self.new_rows[row_index] = RowDiff(row_index=row_index, data=data or {})

    def mark_deleted(self, row_index: int):
        """标记行删除"""
        if row_index in self.new_rows:
            # 如果是新增行，直接移除
            del self.new_rows[row_index]
        else:
            self.deleted_rows.add(row_index)

    def get_modifications_for_row(self, row: int) -> List[CellDiff]:
        """获取指定行的所有修改"""
        return [diff for (r, _), diff in self.modified_cells.items() if r == row]


class FilterWidget(QWidget):
    """
    列筛选控件

    在表格上方显示，用于输入筛选条件。
    支持多列筛选，使用 QScrollArea 防止拥挤。
    """

    # 信号：筛选条件变更
    filter_changed = pyqtSignal()

    def __init__(self, columns: List[str], parent=None):
        super().__init__(parent)
        self._columns = columns
        self._filters: Dict[str, QLineEdit] = {}

        self._init_ui()
        self.setFixedHeight(36)

    def _init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFixedHeight(32)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:horizontal {
                height: 8px;
            }
        """)

        # 内容容器
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(4, 2, 4, 2)
        content_layout.setSpacing(6)

        # 为每列创建筛选输入框
        for col in self._columns:
            # 创建筛选组
            filter_group = QWidget()
            group_layout = QHBoxLayout(filter_group)
            group_layout.setContentsMargins(0, 0, 0, 0)
            group_layout.setSpacing(2)

            label = QLabel(f"{col[:15]}{'...' if len(col) > 15 else ''}:")
            label.setFixedWidth(100)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            label.setToolTip(col)
            group_layout.addWidget(label)

            filter_input = QLineEdit()
            filter_input.setPlaceholderText("筛选...")
            filter_input.setFixedWidth(100)
            filter_input.textChanged.connect(self._on_filter_changed)
            group_layout.addWidget(filter_input)

            self._filters[col] = filter_input
            content_layout.addWidget(filter_group)

        # 添加弹性空间
        content_layout.addStretch()

        # 清除筛选按钮
        clear_btn = QPushButton("清除筛选")
        clear_btn.setFixedWidth(70)
        clear_btn.setFixedHeight(24)
        clear_btn.clicked.connect(self._clear_filters)
        content_layout.addWidget(clear_btn)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def _on_filter_changed(self):
        """筛选条件变更"""
        self.filter_changed.emit()

    def _clear_filters(self):
        """清除所有筛选条件"""
        for filter_input in self._filters.values():
            filter_input.clear()

    def get_filters(self) -> Dict[str, str]:
        """
        获取筛选条件

        Returns:
            字典，键为列名，值为筛选关键字
        """
        filters = {}
        for col, filter_input in self._filters.items():
            text = filter_input.text().strip()
            if text:
                filters[col] = text
        return filters


class PaginationWidget(QWidget):
    """
    分页控件

    显示翻页按钮和页码信息。
    """

    # 信号：页码变更
    page_changed = pyqtSignal(int)  # 新页码
    page_size_changed = pyqtSignal(int)  # 新每页行数

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_page = 1
        self._total_pages = 1
        self._total_rows = 0
        self._page_size = 500

        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # 每页行数
        layout.addWidget(QLabel("每页:"))
        self._page_size_combo = QComboBox()
        for size in PAGE_SIZES:
            self._page_size_combo.addItem(str(size), size)
        self._page_size_combo.setCurrentText(str(self._page_size))
        self._page_size_combo.currentIndexChanged.connect(self._on_page_size_changed)
        layout.addWidget(self._page_size_combo)

        layout.addSpacing(16)

        # 翻页按钮
        self._first_btn = QPushButton("首页")
        self._first_btn.setFixedWidth(60)
        self._first_btn.clicked.connect(self._on_first_page)
        layout.addWidget(self._first_btn)

        self._prev_btn = QPushButton("上一页")
        self._prev_btn.setFixedWidth(70)
        self._prev_btn.clicked.connect(self._on_prev_page)
        layout.addWidget(self._prev_btn)

        # 页码输入
        layout.addWidget(QLabel("第"))
        self._page_spin = QSpinBox()
        self._page_spin.setMinimum(1)
        self._page_spin.setMaximum(1)
        self._page_spin.setFixedWidth(60)
        self._page_spin.editingFinished.connect(self._on_page_spin_changed)
        layout.addWidget(self._page_spin)

        self._total_pages_label = QLabel("/ 1 页")
        layout.addWidget(self._total_pages_label)

        self._next_btn = QPushButton("下一页")
        self._next_btn.setFixedWidth(70)
        self._next_btn.clicked.connect(self._on_next_page)
        layout.addWidget(self._next_btn)

        self._last_btn = QPushButton("末页")
        self._last_btn.setFixedWidth(60)
        self._last_btn.clicked.connect(self._on_last_page)
        layout.addWidget(self._last_btn)

        layout.addSpacing(16)

        # 总行数
        self._total_rows_label = QLabel("共 0 行")
        layout.addWidget(self._total_rows_label)

        # 添加弹性空间
        layout.addStretch()

    def set_total_rows(self, total_rows: int):
        """设置总行数"""
        self._total_rows = total_rows
        self._total_pages = max(
            1, (total_rows + self._page_size - 1) // self._page_size
        )
        self._update_ui()

    def set_current_page(self, page: int):
        """设置当前页码"""
        self._current_page = max(1, min(page, self._total_pages))
        self._update_ui()

    def get_current_page(self) -> int:
        """获取当前页码"""
        return self._current_page

    def get_page_size(self) -> int:
        """获取每页行数"""
        return self._page_size

    def get_offset(self) -> int:
        """获取当前页的偏移量"""
        return (self._current_page - 1) * self._page_size

    def _update_ui(self):
        """更新界面显示"""
        self._page_spin.setMaximum(self._total_pages)
        self._page_spin.setValue(self._current_page)
        self._total_pages_label.setText(f"/ {self._total_pages} 页")
        self._total_rows_label.setText(f"共 {self._total_rows} 行")

        # 更新按钮状态
        self._first_btn.setEnabled(self._current_page > 1)
        self._prev_btn.setEnabled(self._current_page > 1)
        self._next_btn.setEnabled(self._current_page < self._total_pages)
        self._last_btn.setEnabled(self._current_page < self._total_pages)

    def _on_page_size_changed(self, index: int):
        """每页行数变更"""
        self._page_size = self._page_size_combo.currentData()
        self._total_pages = max(
            1, (self._total_rows + self._page_size - 1) // self._page_size
        )
        self._current_page = 1
        self._update_ui()
        self.page_size_changed.emit(self._page_size)

    def _on_first_page(self):
        """首页"""
        if self._current_page != 1:
            self._current_page = 1
            self._update_ui()
            self.page_changed.emit(self._current_page)

    def _on_prev_page(self):
        """上一页"""
        if self._current_page > 1:
            self._current_page -= 1
            self._update_ui()
            self.page_changed.emit(self._current_page)

    def _on_next_page(self):
        """下一页"""
        if self._current_page < self._total_pages:
            self._current_page += 1
            self._update_ui()
            self.page_changed.emit(self._current_page)

    def _on_last_page(self):
        """末页"""
        if self._current_page != self._total_pages:
            self._current_page = self._total_pages
            self._update_ui()
            self.page_changed.emit(self._current_page)

    def _on_page_spin_changed(self):
        """页码输入框变更"""
        new_page = self._page_spin.value()
        if new_page != self._current_page:
            self._current_page = new_page
            self._update_ui()
            self.page_changed.emit(self._current_page)


class DataTableView(QWidget):
    """
    数据表格视图

    提供数据表格展示、分页、排序、筛选、编辑功能。
    使用 VirtualTableView + DataTableModel 实现虚拟滚动。
    """

    def __init__(self, database: str, table: str, parent=None):
        super().__init__(parent)
        self._database = database
        self._table = table
        self._db_connection = get_db_connection()

        # 数据状态
        self._columns: List[str] = []
        self._primary_key: Optional[str] = None
        self._total_rows: int = 0
        self._current_sort_column: Optional[str] = None
        self._current_sort_order: str = "ASC"
        self._is_loading: bool = False

        # 编辑状态
        self._diff_tracker = DiffTracker()
        self._original_data: Dict[int, Dict[str, Any]] = {}  # 原始数据备份 {row: data}
        self._worker_manager = get_worker_manager()
        self._current_worker: Optional[ProcessWorker] = None

        self._init_ui()
        self._load_primary_key()

        # 初始加载
        self._load_total_rows()
        self._load_data()

    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 工具栏
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(8, 8, 8, 8)
        toolbar_layout.setSpacing(8)

        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.setFixedWidth(60)
        refresh_btn.clicked.connect(self._on_refresh)
        toolbar_layout.addWidget(refresh_btn)

        toolbar_layout.addSpacing(16)

        # 编辑按钮
        add_row_btn = QPushButton("新增行")
        add_row_btn.setFixedWidth(70)
        add_row_btn.clicked.connect(self._on_add_row)
        toolbar_layout.addWidget(add_row_btn)

        delete_row_btn = QPushButton("删除行")
        delete_row_btn.setFixedWidth(70)
        delete_row_btn.clicked.connect(self._on_delete_row)
        toolbar_layout.addWidget(delete_row_btn)

        toolbar_layout.addSpacing(8)

        commit_btn = QPushButton("提交更改")
        commit_btn.setFixedWidth(80)
        commit_btn.setStyleSheet("QPushButton { background-color: #4CAF50; }")
        commit_btn.clicked.connect(self._on_commit)
        toolbar_layout.addWidget(commit_btn)

        rollback_btn = QPushButton("撤销")
        rollback_btn.setFixedWidth(60)
        rollback_btn.setStyleSheet("QPushButton { background-color: #f44336; }")
        rollback_btn.clicked.connect(self._on_rollback)
        toolbar_layout.addWidget(rollback_btn)

        toolbar_layout.addSpacing(16)

        # 排序状态显示
        self._sort_label = QLabel("排序: 无")
        toolbar_layout.addWidget(self._sort_label)

        toolbar_layout.addStretch()

        # 编辑状态显示
        self._edit_status_label = QLabel("")
        self._edit_status_label.setStyleSheet("QLabel { color: #FFD700; }")
        toolbar_layout.addWidget(self._edit_status_label)

        # 加载指示器
        self._loading_label = QLabel("加载中...")
        self._loading_label.hide()
        toolbar_layout.addWidget(self._loading_label)

        layout.addLayout(toolbar_layout)

        # 筛选控件（初始隐藏，加载列后显示）
        self._filter_widget = None

        # 表格（使用 VirtualTableView）
        self._table_view = VirtualTableView()
        self._table_view.scroll_to_bottom.connect(self._on_scroll_to_bottom)
        layout.addWidget(self._table_view)

        # 分页控件
        self._pagination = PaginationWidget()
        self._pagination.page_changed.connect(self._on_page_changed)
        self._pagination.page_size_changed.connect(self._on_page_size_changed)
        layout.addWidget(self._pagination)

    def _load_primary_key(self):
        """加载表的主键字段"""
        try:
            structure = self._db_connection.get_table_structure(
                self._database, self._table
            )
            for field_info in structure:
                if field_info.get("key") == "PRI":
                    self._primary_key = field_info.get("name")
                    logger.info(f"表 {self._table} 的主键: {self._primary_key}")
                    break
        except Exception as e:
            logger.warning(f"获取主键失败: {e}")

    def _load_total_rows(self):
        """加载总行数"""
        try:
            sql = f"SELECT COUNT(*) as count FROM `{self._database}`.`{self._table}`"
            result, _, _ = self._db_connection.execute_query(sql)
            if result:
                self._total_rows = result[0].get("count", 0)
                self._pagination.set_total_rows(self._total_rows)
                logger.info(
                    f"表 {self._database}.{self._table} 共有 {self._total_rows} 行"
                )
        except Exception as e:
            logger.error(f"获取总行数失败: {e}")
            self._total_rows = 0

    def _load_data(self):
        """加载数据"""
        if self._is_loading:
            return

        self._is_loading = True
        self._loading_label.show()
        self._table_view.set_loading(True)

        try:
            # 构建 SQL
            sql = self._build_query()

            # 获取连接配置
            config_dict = self._db_connection.config.to_dict() if self._db_connection.config else {}

            # 使用多进程执行查询
            task_id = f"load_data_{self._database}_{self._table}_{id(self)}"
            self._current_worker = self._worker_manager.start_process_query(
                task_id=task_id,
                query_type="query",
                sql=sql,
                config_dict=config_dict,
            )

            # 连接信号
            self._current_worker.result_ready.connect(self._on_data_loaded)
            self._current_worker.error_occurred.connect(self._on_data_load_error)
            self._current_worker.finished.connect(self._on_data_load_finished)

        except Exception as e:
            logger.error(f"启动数据加载失败: {e}")
            QMessageBox.critical(self, "错误", f"启动数据加载失败:\n{e}")
            self._is_loading = False
            self._loading_label.hide()
            self._table_view.set_loading(False)

    def _on_data_loaded(self, task_id: str, result: Any, row_count: int, message: str):
        """数据加载完成回调"""
        try:
            if result is not None:
                # 首次加载时获取列名
                if not self._columns and result:
                    self._columns = list(result[0].keys())
                    self._setup_columns()

                # 备份原始数据
                offset = self._pagination.get_offset()
                for i, row_data in enumerate(result):
                    self._original_data[offset + i] = row_data.copy()

                # 填充数据
                self._fill_data(result, offset)

                # 清除差异追踪
                self._diff_tracker.clear()
                self._update_edit_status()

                logger.info(f"加载了 {row_count} 行数据")

        except Exception as e:
            logger.error(f"处理数据加载结果失败: {e}")
            QMessageBox.critical(self, "错误", f"处理数据失败:\n{e}")

    def _on_data_load_error(self, task_id: str, error: str):
        """数据加载错误回调"""
        logger.error(f"数据加载失败: {error}")
        QMessageBox.critical(self, "错误", f"加载数据失败:\n{error}")

    def _on_data_load_finished(self, task_id: str):
        """数据加载完成回调"""
        self._is_loading = False
        self._loading_label.hide()
        self._table_view.set_loading(False)

    def _build_query(self) -> str:
        """构建查询 SQL"""
        # 基础查询
        columns = (
            ", ".join([f"`{col}`" for col in self._columns]) if self._columns else "*"
        )
        sql = f"SELECT {columns} FROM `{self._database}`.`{self._table}`"

        # 添加筛选条件
        if self._filter_widget:
            filters = self._filter_widget.get_filters()
            if filters:
                conditions = []
                for col, keyword in filters.items():
                    conditions.append(f"`{col}` LIKE '%{keyword}%'")
                sql += " WHERE " + " AND ".join(conditions)

        # 添加排序
        if self._current_sort_column:
            sql += f" ORDER BY `{self._current_sort_column}` {self._current_sort_order}"

        # 添加分页
        offset = self._pagination.get_offset()
        limit = self._pagination.get_page_size()
        sql += f" LIMIT {limit} OFFSET {offset}"

        return sql

    def _setup_columns(self):
        """设置表格列"""
        self._table_view.set_columns(self._columns)

        # 创建筛选控件
        if self._filter_widget:
            self._filter_widget.deleteLater()

        self._filter_widget = FilterWidget(self._columns)
        self._filter_widget.filter_changed.connect(self._on_filter_changed)

        # 插入到布局中（表格之前）
        layout = self.layout()
        layout.insertWidget(1, self._filter_widget)

    def _fill_data(self, data: List[Dict[str, Any]], start_index: int):
        """填充表格数据"""
        self._table_view.set_data(data, self._total_rows, start_index)

    def _on_cell_changed(self, row: int, column: int, old_value: Any, new_value: Any):
        """单元格内容变更（通过模型信号）"""
        if column >= len(self._columns):
            return

        col_name = self._columns[column]
        original_value = self._original_data.get(row, {}).get(col_name)

        if new_value != original_value:
            # 记录修改
            self._diff_tracker.add_modification(
                row, col_name, original_value, new_value
            )
        else:
            # 恢复原样
            self._diff_tracker.modified_cells.pop((row, col_name), None)

        self._update_edit_status()

    def _on_column_header_clicked(self, logical_index: int):
        """列头点击事件 - 排序"""
        if logical_index >= len(self._columns):
            return

        column = self._columns[logical_index]

        # 切换排序方向
        if self._current_sort_column == column:
            self._current_sort_order = (
                "DESC" if self._current_sort_order == "ASC" else "ASC"
            )
        else:
            self._current_sort_column = column
            self._current_sort_order = "ASC"

        # 更新排序状态显示
        self._sort_label.setText(f"排序: {column} {self._current_sort_order}")

        # 重新加载数据
        self._pagination.set_current_page(1)
        self._load_data()

    def _on_filter_changed(self):
        """筛选条件变更"""
        # 重置到第一页并重新加载
        self._pagination.set_current_page(1)
        self._load_total_rows()
        self._load_data()

    def _on_page_changed(self, page: int):
        """页码变更"""
        self._load_data()

    def _on_page_size_changed(self, page_size: int):
        """每页行数变更"""
        self._load_total_rows()
        self._load_data()

    def _on_scroll_to_bottom(self):
        """滚动到底部（懒加载触发）"""
        # 当前使用分页模式，此方法保留用于未来无限滚动
        pass

    def _on_refresh(self):
        """刷新数据"""
        if self._diff_tracker.has_changes():
            reply = QMessageBox.question(
                self,
                "确认刷新",
                "有未提交的更改，刷新将丢失这些更改。确定要刷新吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        self._load_total_rows()
        self._load_data()

    def _on_add_row(self):
        """新增行"""
        if not self._columns:
            return

        # 通过模型添加新行
        new_row = self._table_view.model.add_new_row()

        # 记录新增行
        self._diff_tracker.add_new_row(new_row)

        # 滚动到新行
        self._table_view.scroll_to_row(new_row)

        self._update_edit_status()
        logger.info(f"新增行: {new_row}")

    def _on_delete_row(self):
        """删除选中行"""
        selected_rows = self._table_view.get_selected_rows()

        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要删除的行")
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除选中的 {len(selected_rows)} 行吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        # 标记删除
        for row in selected_rows:
            self._diff_tracker.mark_deleted(row)
            self._table_view.model.mark_deleted(row)

        self._update_edit_status()
        logger.info(f"标记删除 {len(selected_rows)} 行")

    def _on_commit(self):
        """提交更改"""
        if not self._diff_tracker.has_changes():
            QMessageBox.information(self, "提示", "没有需要提交的更改")
            return

        try:
            # 开始事务
            self._db_connection.begin_transaction()

            sql_statements = []

            # 处理删除
            for row_idx in self._diff_tracker.deleted_rows:
                if row_idx in self._original_data:
                    where_clause = self._build_where_clause(
                        self._original_data[row_idx]
                    )
                    sql = f"DELETE FROM `{self._database}`.`{self._table}` WHERE {where_clause}"
                    sql_statements.append(sql)
                    self._db_connection.execute_query(sql, fetch=False)

            # 处理修改
            processed_rows = set()
            for (row, col), diff in self._diff_tracker.modified_cells.items():
                if row in self._diff_tracker.deleted_rows:
                    continue
                if row in processed_rows:
                    continue

                # 获取该行所有修改
                row_diffs = self._diff_tracker.get_modifications_for_row(row)
                if row_diffs and row in self._original_data:
                    set_clauses = []
                    for d in row_diffs:
                        if d.new_value == "NULL":
                            set_clauses.append(f"`{d.column}` = NULL")
                        elif d.new_value == "":
                            set_clauses.append(f"`{d.column}` = ''")
                        else:
                            set_clauses.append(f"`{d.column}` = '{d.new_value}'")

                    where_clause = self._build_where_clause(self._original_data[row])
                    sql = f"UPDATE `{self._database}`.`{self._table}` SET {', '.join(set_clauses)} WHERE {where_clause}"
                    sql_statements.append(sql)
                    self._db_connection.execute_query(sql, fetch=False)
                    processed_rows.add(row)

            # 处理新增
            for row_idx, row_diff in self._diff_tracker.new_rows.items():
                if row_idx in self._diff_tracker.deleted_rows:
                    continue

                # 从模型获取该行数据
                row_data = self._table_view.model.get_row_data(row_idx)
                if row_data:
                    values = {}
                    for col_name, value in row_data.items():
                        if value is not None and value != "":
                            values[col_name] = value

                    if values:
                        columns_str = ", ".join([f"`{k}`" for k in values.keys()])
                        values_str = ", ".join([f"'{v}'" for v in values.values()])
                        sql = f"INSERT INTO `{self._database}`.`{self._table}` ({columns_str}) VALUES ({values_str})"
                        sql_statements.append(sql)
                        self._db_connection.execute_query(sql, fetch=False)

            # 提交事务
            self._db_connection.commit()

            QMessageBox.information(
                self,
                "提交成功",
                f"成功执行 {len(sql_statements)} 条 SQL 语句",
            )

            # 刷新数据
            self._load_total_rows()
            self._load_data()

        except Exception as e:
            # 回滚事务
            try:
                self._db_connection.rollback()
            except Exception:
                pass

            QMessageBox.critical(
                self,
                "提交失败",
                f"事务已回滚:\n{e}",
            )
            logger.error(f"提交失败: {e}")

    def _build_where_clause(self, row_data: Dict[str, Any]) -> str:
        """构建 WHERE 子句（使用主键或所有列）"""
        if self._primary_key and self._primary_key in row_data:
            value = row_data[self._primary_key]
            if value is None:
                return f"`{self._primary_key}` IS NULL"
            return f"`{self._primary_key}` = '{value}'"

        # 没有主键时使用所有列
        conditions = []
        for col, value in row_data.items():
            if value is None:
                conditions.append(f"`{col}` IS NULL")
            else:
                conditions.append(f"`{col}` = '{value}'")
        return " AND ".join(conditions)

    def _on_rollback(self):
        """撤销更改"""
        if not self._diff_tracker.has_changes():
            return

        reply = QMessageBox.question(
            self,
            "确认撤销",
            "确定要丢弃所有未提交的更改吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # 重新加载数据
            self._load_data()
            logger.info("已撤销所有更改")

    def _update_edit_status(self):
        """更新编辑状态显示"""
        modified_count = len(self._diff_tracker.modified_cells)
        new_count = len(self._diff_tracker.new_rows)
        deleted_count = len(self._diff_tracker.deleted_rows)

        if modified_count + new_count + deleted_count > 0:
            parts = []
            if modified_count > 0:
                parts.append(f"修改: {modified_count}")
            if new_count > 0:
                parts.append(f"新增: {new_count}")
            if deleted_count > 0:
                parts.append(f"删除: {deleted_count}")
            self._edit_status_label.setText(" | ".join(parts))
        else:
            self._edit_status_label.setText("")

    def refresh(self):
        """公共刷新方法"""
        self._on_refresh()
