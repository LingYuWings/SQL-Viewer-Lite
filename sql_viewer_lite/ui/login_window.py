"""
登录窗口 - 数据库连接登录界面

提供数据库连接信息输入、测试连接、保存配置等功能。
支持多种数据库类型：MySQL、SQLite 等。
"""

import logging
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QPushButton,
    QCheckBox,
    QComboBox,
    QLabel,
    QMessageBox,
    QGroupBox,
    QSpacerItem,
    QSizePolicy,
    QFileDialog,
    QWidget,
    QStackedWidget,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from sql_viewer_lite.models.connection import ConnectionConfig, create_default_config, SUPPORTED_DB_TYPES
from sql_viewer_lite.core.db_connection import DatabaseConnection, DatabaseConnectionError
from sql_viewer_lite.utils.config_manager import get_config_manager

logger = logging.getLogger(__name__)

# 数据库类型显示名称
DB_TYPE_NAMES = {
    "mysql": "MySQL",
    "sqlite": "SQLite",
    "postgresql": "PostgreSQL",
    "mssql": "SQL Server",
}


class LoginWindow(QDialog):
    """
    登录窗口

    提供数据库连接信息输入界面，支持：
    - 手动输入连接信息
    - 从已保存配置中选择
    - 测试连接
    - 保存/删除配置
    - 多数据库类型选择
    """

    # 信号：登录成功
    login_success = pyqtSignal(ConnectionConfig)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SQL-Viewer Lite - 连接数据库")
        self.setFixedSize(480, 680)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)

        # 初始化组件
        self._db_connection = DatabaseConnection()
        self._config_manager = get_config_manager()
        self._current_config: Optional[ConnectionConfig] = None

        # 初始化 UI
        self._init_ui()

        # 加载已保存的配置
        self._load_saved_configs()

        logger.info("登录窗口初始化完成")

    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(36, 28, 36, 24)

        # 标题
        self._title_label = QLabel("连接数据库")
        self._title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        self._title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._title_label)

        # 已保存配置选择
        saved_group = QGroupBox("已保存的连接")
        saved_layout = QHBoxLayout(saved_group)
        saved_layout.setContentsMargins(12, 18, 12, 14)
        saved_layout.setSpacing(10)

        self._config_combo = QComboBox()
        self._config_combo.setMinimumWidth(260)
        self._config_combo.setFixedHeight(34)
        self._config_combo.currentIndexChanged.connect(self._on_config_selected)
        saved_layout.addWidget(self._config_combo)

        self._delete_config_btn = QPushButton("删除")
        self._delete_config_btn.setFixedSize(60, 34)
        self._delete_config_btn.clicked.connect(self._on_delete_config)
        saved_layout.addWidget(self._delete_config_btn)

        layout.addWidget(saved_group)

        # 数据库类型选择
        type_group = QGroupBox("数据库类型")
        type_layout = QHBoxLayout(type_group)
        type_layout.setContentsMargins(14, 18, 14, 14)

        self._db_type_combo = QComboBox()
        self._db_type_combo.setFixedHeight(34)
        for db_type in SUPPORTED_DB_TYPES:
            name = DB_TYPE_NAMES.get(db_type, db_type)
            self._db_type_combo.addItem(name, db_type)
        self._db_type_combo.currentIndexChanged.connect(self._on_db_type_changed)
        type_layout.addWidget(self._db_type_combo)

        layout.addWidget(type_group)

        # 连接信息表单（使用堆叠窗口切换不同数据库类型的表单）
        self._form_stack = QStackedWidget()

        # MySQL 表单
        self._mysql_form = self._create_mysql_form()
        self._form_stack.addWidget(self._mysql_form)

        # SQLite 表单
        self._sqlite_form = self._create_sqlite_form()
        self._form_stack.addWidget(self._sqlite_form)

        # PostgreSQL 表单（暂时使用 MySQL 表单）
        self._pg_form = self._create_mysql_form()
        self._form_stack.addWidget(self._pg_form)

        # SQL Server 表单（暂时使用 MySQL 表单）
        self._mssql_form = self._create_mysql_form()
        self._form_stack.addWidget(self._mssql_form)

        layout.addWidget(self._form_stack)

        # 保存连接选项
        self._save_checkbox = QCheckBox("保存此连接")
        self._save_checkbox.setChecked(True)
        layout.addWidget(self._save_checkbox)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(16)

        # 测试连接按钮
        self._test_btn = QPushButton("测试连接")
        self._test_btn.setFixedHeight(40)
        self._test_btn.clicked.connect(self._on_test_connection)
        button_layout.addWidget(self._test_btn)

        # 登录按钮
        self._login_btn = QPushButton("登录")
        self._login_btn.setFixedHeight(40)
        self._login_btn.setDefault(True)
        self._login_btn.clicked.connect(self._on_login)
        button_layout.addWidget(self._login_btn)

        layout.addLayout(button_layout)

        # 添加弹性空间
        layout.addSpacerItem(
            QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        # 默认显示 MySQL 表单
        self._form_stack.setCurrentIndex(0)

    def _create_mysql_form(self) -> QWidget:
        """创建 MySQL 连接表单"""
        form = QWidget()
        form_layout = QFormLayout(form)
        form_layout.setSpacing(14)
        form_layout.setContentsMargins(14, 22, 14, 14)
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # 主机地址
        self._host_input = QLineEdit()
        self._host_input.setPlaceholderText("localhost")
        self._host_input.setText("localhost")
        self._host_input.setFixedHeight(34)
        form_layout.addRow("主机地址:", self._host_input)

        # 端口
        self._port_input = QSpinBox()
        self._port_input.setRange(1, 65535)
        self._port_input.setValue(3306)
        self._port_input.setFixedHeight(34)
        form_layout.addRow("端口:", self._port_input)

        # 用户名
        self._user_input = QLineEdit()
        self._user_input.setPlaceholderText("root")
        self._user_input.setText("root")
        self._user_input.setFixedHeight(34)
        form_layout.addRow("用户名:", self._user_input)

        # 密码
        self._password_input = QLineEdit()
        self._password_input.setPlaceholderText("请输入密码")
        self._password_input.setEchoMode(QLineEdit.Password)
        self._password_input.setFixedHeight(34)
        form_layout.addRow("密码:", self._password_input)

        # 数据库（可选）
        self._database_input = QLineEdit()
        self._database_input.setPlaceholderText("可选，登录后选择")
        self._database_input.setFixedHeight(34)
        form_layout.addRow("数据库:", self._database_input)

        # 连接别名
        self._alias_input = QLineEdit()
        self._alias_input.setPlaceholderText("可选，用于标识连接")
        self._alias_input.setFixedHeight(34)
        form_layout.addRow("连接别名:", self._alias_input)

        return form

    def _create_sqlite_form(self) -> QWidget:
        """创建 SQLite 连接表单"""
        form = QWidget()
        form_layout = QFormLayout(form)
        form_layout.setSpacing(14)
        form_layout.setContentsMargins(14, 22, 14, 14)
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # 数据库文件路径
        file_layout = QHBoxLayout()
        file_layout.setSpacing(8)

        self._file_path_input = QLineEdit()
        self._file_path_input.setPlaceholderText("选择或输入 .db 文件路径")
        self._file_path_input.setFixedHeight(34)
        file_layout.addWidget(self._file_path_input)

        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedSize(70, 34)
        browse_btn.clicked.connect(self._on_browse_file)
        file_layout.addWidget(browse_btn)

        form_layout.addRow("数据库文件:", file_layout)

        # 连接别名
        self._sqlite_alias_input = QLineEdit()
        self._sqlite_alias_input.setPlaceholderText("可选，用于标识连接")
        self._sqlite_alias_input.setFixedHeight(34)
        form_layout.addRow("连接别名:", self._sqlite_alias_input)

        return form

    def _on_browse_file(self):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 SQLite 数据库文件",
            "",
            "SQLite 数据库 (*.db *.sqlite *.sqlite3 *.db3);;所有文件 (*.*)",
        )
        if file_path:
            self._file_path_input.setText(file_path)

    def _on_db_type_changed(self, index: int):
        """数据库类型变更"""
        db_type = self._db_type_combo.currentData()

        # 切换表单
        if db_type == "sqlite":
            self._form_stack.setCurrentIndex(1)
            self._title_label.setText("连接到 SQLite")
        elif db_type == "postgresql":
            self._form_stack.setCurrentIndex(2)
            self._title_label.setText("连接到 PostgreSQL")
        elif db_type == "mssql":
            self._form_stack.setCurrentIndex(3)
            self._title_label.setText("连接到 SQL Server")
        else:
            self._form_stack.setCurrentIndex(0)
            self._title_label.setText("连接到 MySQL")

    def _load_saved_configs(self):
        """加载已保存的配置"""
        try:
            configs = self._config_manager.load_configs()

            self._config_combo.clear()
            self._config_combo.addItem("-- 选择已保存的连接 --", None)

            for config in configs:
                self._config_combo.addItem(config.display_name, config)

            logger.info(f"加载了 {len(configs)} 个已保存配置")
        except Exception as e:
            logger.error(f"加载配置失败: {e}")

    def _on_config_selected(self, index: int):
        """配置选择变更"""
        config = self._config_combo.currentData()

        if config is None:
            # 清空表单
            self._host_input.setText("localhost")
            self._port_input.setValue(3306)
            self._user_input.setText("root")
            self._password_input.clear()
            self._database_input.clear()
            self._alias_input.clear()
            self._file_path_input.clear()
            self._sqlite_alias_input.clear()
            return

        # 设置数据库类型
        db_type = config.db_type
        for i in range(self._db_type_combo.count()):
            if self._db_type_combo.itemData(i) == db_type:
                self._db_type_combo.setCurrentIndex(i)
                break

        # 填充表单
        if db_type == "sqlite":
            self._file_path_input.setText(config.file_path or "")
            self._sqlite_alias_input.setText(config.alias or "")
        else:
            self._host_input.setText(config.host)
            self._port_input.setValue(config.port)
            self._user_input.setText(config.user)
            self._password_input.setText(config.password)
            self._database_input.setText(config.database or "")
            self._alias_input.setText(config.alias or "")

        self._current_config = config
        logger.debug(f"选择配置: {config.display_name}")

    def _on_delete_config(self):
        """删除配置"""
        config = self._config_combo.currentData()
        if config is None:
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除连接配置 '{config.display_name}' 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            alias = config.alias or config.display_name
            if self._config_manager.delete_config(alias):
                self._load_saved_configs()
                QMessageBox.information(self, "成功", "配置已删除")
            else:
                QMessageBox.warning(self, "失败", "删除配置失败")

    def _get_form_config(self) -> ConnectionConfig:
        """从表单获取连接配置"""
        db_type = self._db_type_combo.currentData()

        if db_type == "sqlite":
            return ConnectionConfig(
                db_type="sqlite",
                file_path=self._file_path_input.text().strip() or None,
                alias=self._sqlite_alias_input.text().strip() or None,
            )
        else:
            return ConnectionConfig(
                db_type=db_type,
                host=self._host_input.text().strip() or "localhost",
                port=self._port_input.value(),
                user=self._user_input.text().strip() or "root",
                password=self._password_input.text(),
                database=self._database_input.text().strip() or None,
                alias=self._alias_input.text().strip() or None,
            )

    def _validate_form(self) -> bool:
        """验证表单输入"""
        config = self._get_form_config()
        errors = config.validate()

        if errors:
            QMessageBox.warning(
                self,
                "输入错误",
                "\n".join(errors),
            )
            return False

        return True

    def _on_test_connection(self):
        """测试连接"""
        if not self._validate_form():
            return

        config = self._get_form_config()

        # 禁用按钮，显示测试中状态
        self._test_btn.setEnabled(False)
        self._test_btn.setText("测试中...")
        self.repaint()

        try:
            success, message = self._db_connection.test_connection(config)

            if success:
                QMessageBox.information(self, "连接成功", message)
            else:
                QMessageBox.warning(self, "连接失败", message)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"测试连接时发生错误:\n{e}")
        finally:
            self._test_btn.setEnabled(True)
            self._test_btn.setText("测试连接")

    def _on_login(self):
        """登录"""
        if not self._validate_form():
            return

        config = self._get_form_config()

        # 禁用按钮，显示连接中状态
        self._login_btn.setEnabled(False)
        self._login_btn.setText("连接中...")
        self.repaint()

        try:
            # 建立连接
            self._db_connection.connect(config)

            # 保存配置（如果勾选）
            if self._save_checkbox.isChecked():
                try:
                    self._config_manager.save_config(config)
                    logger.info("连接配置已保存")
                except Exception as e:
                    logger.warning(f"保存配置失败: {e}")

            # 发射登录成功信号
            self.login_success.emit(config)

            # 关闭窗口
            self.accept()

        except DatabaseConnectionError as e:
            QMessageBox.critical(
                self,
                "连接失败",
                f"无法连接到数据库:\n{e}",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"登录时发生错误:\n{e}",
            )
        finally:
            self._login_btn.setEnabled(True)
            self._login_btn.setText("登录")

    def closeEvent(self, event):
        """窗口关闭事件"""
        self._db_connection.disconnect()
        super().closeEvent(event)
