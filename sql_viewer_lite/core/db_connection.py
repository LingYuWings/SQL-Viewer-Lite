"""
数据库连接管理模块

提供统一的数据库连接管理，支持多数据库驱动。
"""

import logging
import threading
from typing import Optional, List, Tuple, Any, Dict

from sql_viewer_lite.models.connection import ConnectionConfig
from sql_viewer_lite.core.drivers import get_driver, DatabaseDriver, TableInfo, ColumnInfo

logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """数据库连接错误"""

    pass


class QueryError(Exception):
    """查询错误"""

    pass


class ConnectionState:
    """连接状态枚举"""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class DatabaseConnection:
    """
    数据库连接管理器

    通过驱动抽象层管理数据库连接，支持多数据库。
    """

    def __init__(self):
        self._driver: Optional[DatabaseDriver] = None
        self._config: Optional[ConnectionConfig] = None
        self._state: str = ConnectionState.DISCONNECTED
        self._last_error: Optional[str] = None

    @property
    def state(self) -> str:
        """获取连接状态"""
        return self._state

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._state == ConnectionState.CONNECTED and self._driver is not None

    @property
    def config(self) -> Optional[ConnectionConfig]:
        """获取当前连接配置"""
        return self._config

    @property
    def last_error(self) -> Optional[str]:
        """获取最后的错误信息"""
        return self._last_error

    @property
    def db_type(self) -> Optional[str]:
        """获取当前数据库类型"""
        return self._config.db_type if self._config else None

    def connect(self, config: ConnectionConfig) -> bool:
        """
        建立数据库连接

        Args:
            config: 连接配置

        Returns:
            是否连接成功

        Raises:
            DatabaseConnectionError: 连接失败时抛出
        """
        # 断开现有连接
        self.disconnect()

        self._config = config
        self._state = ConnectionState.CONNECTING
        self._last_error = None

        try:
            logger.info(f"正在连接: {config.display_name} (类型: {config.db_type})")

            # 获取对应数据库驱动
            self._driver = get_driver(config.db_type)

            # 建立连接
            self._driver.connect(config)

            self._state = ConnectionState.CONNECTED
            logger.info("数据库连接成功")
            return True

        except Exception as e:
            error_msg = f"连接失败: {e}"
            logger.error(error_msg)
            self._state = ConnectionState.ERROR
            self._last_error = error_msg
            self._driver = None
            raise DatabaseConnectionError(error_msg)

    def disconnect(self):
        """断开数据库连接"""
        if self._driver is not None:
            try:
                self._driver.disconnect()
                logger.info("数据库连接已断开")
            except Exception as e:
                logger.warning(f"断开连接时出错: {e}")
            finally:
                self._driver = None
                self._state = ConnectionState.DISCONNECTED

    def test_connection(self, config: ConnectionConfig) -> Tuple[bool, str]:
        """
        测试数据库连接

        Args:
            config: 连接配置

        Returns:
            (是否成功, 消息)
        """
        test_driver = None
        try:
            logger.info(f"测试连接: {config.display_name} (类型: {config.db_type})")

            # 获取驱动并连接
            test_driver = get_driver(config.db_type)
            test_driver.connect(config)

            # 测试连接
            if test_driver.test_connection():
                message = f"连接成功 ({test_driver.driver_name})"
                logger.info(message)
                return True, message
            else:
                message = "连接测试失败"
                logger.warning(message)
                return False, message

        except Exception as e:
            message = f"连接失败: {e}"
            logger.warning(message)
            return False, message

        finally:
            if test_driver is not None:
                try:
                    test_driver.disconnect()
                except Exception:
                    pass

    def get_databases(self) -> List[str]:
        """
        获取数据库列表

        Returns:
            数据库名称列表

        Raises:
            DatabaseConnectionError: 未连接时抛出
            QueryError: 查询失败时抛出
        """
        self._check_connected()

        try:
            databases = self._driver.get_databases()
            logger.info(f"获取到 {len(databases)} 个数据库")
            return databases
        except Exception as e:
            error_msg = f"获取数据库列表失败: {e}"
            logger.error(error_msg)
            raise QueryError(error_msg)

    def get_tables(self, database: str) -> List[Dict[str, Any]]:
        """
        获取指定数据库的表列表

        Args:
            database: 数据库名

        Returns:
            表信息列表，每项包含表名、行数、引擎、字符集等

        Raises:
            DatabaseConnectionError: 未连接时抛出
            QueryError: 查询失败时抛出
        """
        self._check_connected()

        try:
            tables = self._driver.get_tables(database)
            result = []
            for table in tables:
                result.append({
                    "name": table.name,
                    "rows": table.rows,
                    "engine": table.engine,
                    "charset": table.charset,
                    "size": table.size,
                    "comment": table.comment,
                })
            logger.info(f"数据库 {database} 共有 {len(result)} 个表")
            return result
        except Exception as e:
            error_msg = f"获取表列表失败: {e}"
            logger.error(error_msg)
            raise QueryError(error_msg)

    def get_table_structure(self, database: str, table: str) -> List[Dict[str, Any]]:
        """
        获取表结构

        Args:
            database: 数据库名
            table: 表名

        Returns:
            字段信息列表

        Raises:
            DatabaseConnectionError: 未连接时抛出
            QueryError: 查询失败时抛出
        """
        self._check_connected()

        try:
            columns = self._driver.get_columns(database, table)
            result = []
            for col in columns:
                result.append({
                    "name": col.name,
                    "type": col.type,
                    "null": "YES" if col.nullable else "NO",
                    "key": "PRI" if col.is_primary_key else "",
                    "default": col.default if col.default is not None else "",
                    "extra": "",
                    "comment": col.comment,
                })
            logger.info(f"表 {database}.{table} 共有 {len(result)} 个字段")
            return result
        except Exception as e:
            error_msg = f"获取表结构失败: {e}"
            logger.error(error_msg)
            raise QueryError(error_msg)

    def execute_query(
        self,
        sql: str,
        params: Optional[tuple] = None,
        fetch: bool = True,
    ) -> Tuple[Optional[List[Dict[str, Any]]], int, str]:
        """
        执行 SQL 查询

        Args:
            sql: SQL 语句
            params: 查询参数
            fetch: 是否获取结果（SELECT 语句为 True）

        Returns:
            (结果列表, 影响行数, 执行信息)

        Raises:
            DatabaseConnectionError: 未连接时抛出
            QueryError: 查询失败时抛出
        """
        self._check_connected()

        try:
            logger.debug(f"执行 SQL: {sql}")
            result = self._driver.execute_query(sql, params, fetch)

            if fetch and result is not None:
                message = f"查询成功，返回 {len(result)} 行"
                return result, len(result), message
            else:
                message = "执行成功"
                return None, 0, message

        except Exception as e:
            error_msg = f"SQL 执行失败: {e}"
            logger.error(error_msg)
            raise QueryError(error_msg)

    def begin_transaction(self):
        """开始事务"""
        self._check_connected()
        try:
            self._driver.begin_transaction()
            logger.debug("事务已开始")
        except Exception as e:
            raise QueryError(f"开始事务失败: {e}")

    def commit(self):
        """提交事务"""
        self._check_connected()
        try:
            self._driver.commit()
            logger.debug("事务已提交")
        except Exception as e:
            raise QueryError(f"提交事务失败: {e}")

    def rollback(self):
        """回滚事务"""
        self._check_connected()
        try:
            self._driver.rollback()
            logger.debug("事务已回滚")
        except Exception as e:
            raise QueryError(f"回滚事务失败: {e}")

    def _check_connected(self):
        """检查是否已连接"""
        if not self.is_connected:
            raise DatabaseConnectionError("数据库未连接")


# 全局连接实例
_db_connection: Optional[DatabaseConnection] = None
_singleton_lock = threading.Lock()


def get_db_connection() -> DatabaseConnection:
    """获取数据库连接单例（线程安全）"""
    global _db_connection
    if _db_connection is None:
        with _singleton_lock:
            if _db_connection is None:
                _db_connection = DatabaseConnection()
    return _db_connection
