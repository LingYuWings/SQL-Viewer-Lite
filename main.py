#!/usr/bin/env python3
"""
SQL-Viewer Lite - 主程序入口

轻量级 MySQL 数据查看与编辑工具
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, List

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenuBar,
    QToolBar,
    QStatusBar,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QAction,
    QTreeWidget,
    QTreeWidgetItem,
    QLineEdit,
    QSplitter,
    QDockWidget,
    QMessageBox,
    QProgressBar,
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QPixmap, QPainter, QColor

from sql_viewer_lite.models.connection import ConnectionConfig
from sql_viewer_lite.core.db_connection import get_db_connection, DatabaseConnection
from sql_viewer_lite.ui.login_window import LoginWindow
from sql_viewer_lite.ui.table_view import DataTableView
from sql_viewer_lite.ui.table_structure import TableStructureView, TableInfoView
from sql_viewer_lite.ui.sql_editor import create_sql_dock_widget
from sql_viewer_lite.utils.theme_manager import get_theme_manager, THEMES
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


class DatabaseTreeWidget(QWidget):
    """
    数据库树形控件
    
    显示数据库和表的层级结构，支持搜索过滤。
    """
    
    # 信号：表被选中
    table_selected = pyqtSignal(str, str)  # database, table
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._db_connection = get_db_connection()
        self._all_items: List[Dict] = []  # 存储所有项目用于过滤
        
        # 创建图标
        self._db_icon = self._create_colored_icon("#4FC3F7", "🗄")  # 浅蓝色
        self._table_icon = self._create_colored_icon("#81C784", "📋")  # 浅绿色
        
        self._init_ui()
    
    @staticmethod
    def _create_colored_icon(color: str, emoji: str) -> QIcon:
        """创建带颜色的图标"""
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(0, 0, 0, 0))  # 透明背景
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制圆形背景
        painter.setBrush(QColor(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(1, 1, 14, 14)
        
        # 绘制中心点
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(5, 5, 6, 6)
        
        painter.end()
        
        return QIcon(pixmap)
    
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
        self._tree.setHeaderLabel("数据库")
        self._tree.setAnimated(True)
        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._tree.itemExpanded.connect(self._on_item_expanded)
        layout.addWidget(self._tree)
    
    def load_databases(self, databases: List[str]):
        """
        加载数据库列表
        
        Args:
            databases: 数据库名称列表
        """
        self._tree.clear()
        self._all_items.clear()
        
        for db_name in databases:
            # 创建数据库节点
            db_item = QTreeWidgetItem(self._tree)
            db_item.setText(0, db_name)
            db_item.setIcon(0, self._db_icon)
            db_item.setData(0, Qt.UserRole, {"type": "database", "name": db_name})
            
            # 添加占位子节点（懒加载）
            placeholder = QTreeWidgetItem(db_item)
            placeholder.setText(0, "加载中...")
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
            
            for table_info in tables:
                table_name = table_info["name"]
                rows = table_info.get("rows", 0)
                engine = table_info.get("engine", "")
                
                # 创建表节点
                table_item = QTreeWidgetItem(db_item)
                table_item.setText(0, table_name)
                table_item.setIcon(0, self._table_icon)
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
            
            logger.info(f"数据库 {database} 加载了 {len(tables)} 个表")
            
        except Exception as e:
            logger.error(f"加载表列表失败: {e}")
            # 添加错误提示节点
            error_item = QTreeWidgetItem(db_item)
            error_item.setText(0, f"加载失败: {e}")
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


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SQL-Viewer Lite")
        self.setMinimumSize(1024, 768)
        self.resize(1280, 800)
        
        # 数据库连接
        self._db_connection = get_db_connection()
        self._current_config: Optional[ConnectionConfig] = None
        
        # 主题相关
        self._theme_actions = {}

        # 初始化 UI
        self._init_menu_bar()
        self._init_toolbar()
        self._init_central_widget()
        self._init_status_bar()

        # 显示登录窗口
        self._show_login_window()

        logger.info("主窗口初始化完成")

    def _init_menu_bar(self):
        """初始化菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        file_menu.addAction("新建连接(&N)", self._on_new_connection)
        file_menu.addAction("断开连接(&D)", self._on_disconnect)
        file_menu.addSeparator()
        file_menu.addAction("退出(&Q)", self.close)

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")
        edit_menu.addAction("撤销(&U)")
        edit_menu.addAction("重做(&R)")
        edit_menu.addSeparator()
        edit_menu.addAction("复制(&C)")
        edit_menu.addAction("粘贴(&V)")

        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        view_menu.addAction("刷新(&R)", self._on_refresh)
        view_menu.addSeparator()
        view_menu.addAction("侧边栏(&S)")
        view_menu.addAction("状态栏(&T)")
        
        # 主题子菜单
        theme_menu = view_menu.addMenu("主题(&T)")
        self._theme_actions = {}
        for theme_id, theme_info in THEMES.items():
            action = theme_menu.addAction(theme_info["name"])
            action.setCheckable(True)
            action.triggered.connect(lambda checked, t=theme_id: self._on_theme_changed(t))
            self._theme_actions[theme_id] = action
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        tools_menu.addAction("SQL 执行器(&S)", self._on_toggle_sql_executor)
        tools_menu.addAction("数据导出(&E)")
        tools_menu.addSeparator()
        tools_menu.addAction("设置(&P)")

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        help_menu.addAction("关于(&A)")
        help_menu.addAction("文档(&D)")

    def _init_toolbar(self):
        """初始化工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        # 添加工具栏按钮（暂用文本，后续替换为图标）
        toolbar.addAction("连接", self._on_new_connection)
        toolbar.addAction("刷新", self._on_refresh)
        toolbar.addSeparator()
        toolbar.addAction("新增行", self._on_add_row)
        toolbar.addAction("删除行", self._on_delete_row)
        toolbar.addAction("提交", self._on_commit)
        toolbar.addAction("撤销", self._on_rollback)

    def _init_central_widget(self):
        """初始化中央部件"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧边栏 - 数据库树
        self._db_tree = DatabaseTreeWidget()
        self._db_tree.table_selected.connect(self._on_table_selected)
        self._db_tree.setMinimumWidth(200)
        self._db_tree.setMaximumWidth(400)
        splitter.addWidget(self._db_tree)

        # 右侧标签页
        self._tab_widget = QTabWidget()
        self._tab_widget.setTabsClosable(True)
        self._tab_widget.tabCloseRequested.connect(self._on_tab_close)
        self._tab_widget.tabBar().installEventFilter(self)
        splitter.addWidget(self._tab_widget)

        # 设置分割器比例
        splitter.setSizes([250, 1030])
        
        # 添加 SQL 执行器停靠窗口
        self._sql_dock = create_sql_dock_widget(self)
        self._sql_dock.hide()  # 默认隐藏
        self.addDockWidget(Qt.BottomDockWidgetArea, self._sql_dock)

        # 添加欢迎页面
        self._add_welcome_tab()

    def _add_welcome_tab(self):
        """添加欢迎标签页"""
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)

        welcome_label = QLabel("欢迎使用 SQL-Viewer Lite")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        welcome_layout.addWidget(welcome_label)

        hint_label = QLabel("请先连接到 MySQL 数据库，然后双击左侧表名查看数据")
        hint_label.setAlignment(Qt.AlignCenter)
        hint_label.setFont(QFont("Microsoft YaHei", 12))
        welcome_layout.addWidget(hint_label)

        self._tab_widget.addTab(welcome_widget, "欢迎")

    def _init_status_bar(self):
        """初始化状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 连接状态
        self.connection_status = QLabel("未连接")
        self.status_bar.addWidget(self.connection_status)

        # 当前数据库
        self.current_db = QLabel("")
        self.status_bar.addWidget(self.current_db)

        # 当前表
        self.current_table = QLabel("")
        self.status_bar.addWidget(self.current_table)

        # 行数
        self.row_count = QLabel("")
        self.status_bar.addWidget(self.row_count)

        # 查询耗时
        self.query_time = QLabel("")
        self.status_bar.addPermanentWidget(self.query_time)

    def _show_login_window(self):
        """显示登录窗口"""
        login_window = LoginWindow(self)
        login_window.login_success.connect(self._on_login_success)
        login_window.exec_()
    
    def _on_login_success(self, config: ConnectionConfig):
        """登录成功回调"""
        self._current_config = config
        self.connection_status.setText(f"已连接: {config.display_name}")
        self.setWindowTitle(f"SQL-Viewer Lite - {config.display_name}")
        
        # 使用主窗口的连接单例建立连接
        try:
            self._db_connection.connect(config)
            # 加载数据库列表
            self._load_databases()
            logger.info(f"登录成功: {config.display_name}")
        except Exception as e:
            logger.error(f"连接失败: {e}")
            QMessageBox.critical(self, "连接失败", f"无法连接到数据库:\n{e}")
    
    def _load_databases(self):
        """加载数据库列表"""
        try:
            databases = self._db_connection.get_databases()
            self._db_tree.load_databases(databases)
            logger.info(f"加载了 {len(databases)} 个数据库")
        except Exception as e:
            logger.error(f"加载数据库列表失败: {e}")
            QMessageBox.critical(self, "错误", f"加载数据库列表失败:\n{e}")
    
    def _on_table_selected(self, database: str, table: str):
        """表被选中"""
        logger.info(f"选中表: {database}.{table}")
        
        # 更新状态栏
        self.current_db.setText(f"数据库: {database}")
        self.current_table.setText(f"表: {table}")
        
        # 检查是否已经打开该表
        for i in range(self._tab_widget.count()):
            tab_data = self._tab_widget.tabToolTip(i)
            if tab_data == f"{database}.{table}":
                self._tab_widget.setCurrentIndex(i)
                return
        
        # 创建新的标签页
        self._create_table_tab(database, table)
    
    def _create_table_tab(self, database: str, table: str):
        """创建表数据标签页"""
        # 创建标签页容器
        tab_container = QTabWidget()
        tab_container.setTabPosition(QTabWidget.South)
        
        # 获取表信息
        table_info = None
        try:
            tables = self._db_connection.get_tables(database)
            for t in tables:
                if t.get("name") == table:
                    table_info = t
                    break
        except Exception as e:
            logger.warning(f"获取表信息失败: {e}")
        
        # 添加数据视图标签页
        data_view = DataTableView(database, table)
        tab_container.addTab(data_view, "数据")
        
        # 添加表结构标签页
        structure_view = TableStructureView(database, table)
        tab_container.addTab(structure_view, "结构")
        
        # 添加表信息标签页
        info_view = TableInfoView(database, table, table_info)
        tab_container.addTab(info_view, "信息")
        
        # 添加到主标签页
        tab_name = f"{database}.{table}"
        index = self._tab_widget.addTab(tab_container, tab_name)
        self._tab_widget.setTabToolTip(index, f"{database}.{table}")
        self._tab_widget.setCurrentIndex(index)
        
        # 更新状态栏
        if table_info:
            self.row_count.setText(f"行数: {table_info.get('rows', '未知')}")
    
    def _load_table_info(self, database: str, table: str):
        """加载表信息"""
        try:
            structure = self._db_connection.get_table_structure(database, table)
            logger.info(f"表 {database}.{table} 有 {len(structure)} 个字段")
        except Exception as e:
            logger.error(f"加载表结构失败: {e}")
    
    def _on_tab_close(self, index: int):
        """关闭标签页"""
        # 不关闭欢迎页面
        if self._tab_widget.tabText(index) == "欢迎":
            return
        self._tab_widget.removeTab(index)

    def eventFilter(self, obj, event):
        """事件过滤器 - 处理中键关闭标签页"""
        if obj == self._tab_widget.tabBar() and event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.MiddleButton:
                # 获取点击位置对应的标签索引
                index = self._tab_widget.tabBar().tabAt(event.pos())
                if index >= 0:
                    self._on_tab_close(index)
                    return True
        return super().eventFilter(obj, event)
    
    def _on_new_connection(self):
        """新建连接"""
        logger.info("新建连接")
        self._show_login_window()

    def _on_disconnect(self):
        """断开连接"""
        logger.info("断开连接")
        self._db_connection.disconnect()
        self._current_config = None
        self.connection_status.setText("未连接")
        self.current_db.setText("")
        self.current_table.setText("")
        self.setWindowTitle("SQL-Viewer Lite")
        
        # 清空数据库树
        self._db_tree.load_databases([])

    def _on_refresh(self):
        """刷新"""
        logger.info("刷新")
        if self._db_connection.is_connected:
            self._db_tree.refresh()

    def _on_add_row(self):
        """新增行"""
        logger.info("新增行")
        # TODO: 添加新行

    def _on_delete_row(self):
        """删除行"""
        logger.info("删除行")
        # TODO: 删除选中行

    def _on_commit(self):
        """提交更改"""
        logger.info("提交更改")
        # TODO: 提交事务

    def _on_rollback(self):
        """撤销更改"""
        logger.info("撤销更改")
        # TODO: 回滚事务
    
    def _on_toggle_sql_executor(self):
        """切换 SQL 执行器显示"""
        if self._sql_dock.isVisible():
            self._sql_dock.hide()
        else:
            self._sql_dock.show()
    
    def _on_theme_changed(self, theme_name: str):
        """主题切换"""
        theme_manager = get_theme_manager()
        theme_manager.set_theme(theme_name)
        self._update_theme_menu_state(theme_name)
    
    def _update_theme_menu_state(self, current_theme: str):
        """更新主题菜单状态"""
        for theme_id, action in self._theme_actions.items():
            action.setChecked(theme_id == current_theme)


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
