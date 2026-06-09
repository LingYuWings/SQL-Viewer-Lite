"""
数据库连接管理模块

封装 PyMySQL 连接操作，提供连接测试、数据库列表、表列表等功能。
"""

import logging
from typing import Optional, List, Tuple, Any, Dict

import pymysql
from pymysql.cursors import DictCursor

from sql_viewer_lite.models.connection import ConnectionConfig

logger = logging.getLogger(__name__)


class ConnectionError(Exception):
    """连接错误"""

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

    封装 PyMySQL 连接操作，提供连接管理、查询执行等功能。
    """

    def __init__(self):
        self._connection: Optional[pymysql.Connection] = None
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
        return self._state == ConnectionState.CONNECTED

    @property
    def config(self) -> Optional[ConnectionConfig]:
        """获取当前连接配置"""
        return self._config

    @property
    def last_error(self) -> Optional[str]:
        """获取最后的错误信息"""
        return self._last_error

    def connect(self, config: ConnectionConfig) -> bool:
        """
        建立数据库连接

        Args:
            config: 连接配置

        Returns:
            是否连接成功

        Raises:
            ConnectionError: 连接失败时抛出
        """
        # 断开现有连接
        self.disconnect()

        self._config = config
        self._state = ConnectionState.CONNECTING
        self._last_error = None

        try:
            logger.info(f"正在连接: {config.user}@{config.host}:{config.port}")

            self._connection = pymysql.connect(
                host=config.host,
                port=config.port,
                user=config.user,
                password=config.password,
                database=config.database,
                charset="utf8mb4",
                cursorclass=DictCursor,
                connect_timeout=10,
                autocommit=True,
            )

            self._state = ConnectionState.CONNECTED
            logger.info("数据库连接成功")
            return True

        except pymysql.Error as e:
            error_msg = f"连接失败: {e}"
            logger.error(error_msg)
            self._state = ConnectionState.ERROR
            self._last_error = error_msg
            raise ConnectionError(error_msg)

        except Exception as e:
            error_msg = f"连接异常: {e}"
            logger.error(error_msg)
            self._state = ConnectionState.ERROR
            self._last_error = error_msg
            raise ConnectionError(error_msg)

    def disconnect(self):
        """断开数据库连接"""
        if self._connection is not None:
            try:
                self._connection.close()
                logger.info("数据库连接已断开")
            except Exception as e:
                logger.warning(f"断开连接时出错: {e}")
            finally:
                self._connection = None
                self._state = ConnectionState.DISCONNECTED

    def test_connection(self, config: ConnectionConfig) -> Tuple[bool, str]:
        """
        测试数据库连接

        Args:
            config: 连接配置

        Returns:
            (是否成功, 消息)
        """
        test_conn = None
        try:
            logger.info(f"测试连接: {config.user}@{config.host}:{config.port}")

            test_conn = pymysql.connect(
                host=config.host,
                port=config.port,
                user=config.user,
                password=config.password,
                charset="utf8mb4",
                cursorclass=DictCursor,
                connect_timeout=5,
            )

            # 执行简单查询验证连接
            with test_conn.cursor() as cursor:
                cursor.execute("SELECT VERSION() as version")
                result = cursor.fetchone()
                version = result.get("version", "未知") if result else "未知"

            message = f"连接成功 (MySQL {version})"
            logger.info(message)
            return True, message

        except pymysql.Error as e:
            message = f"连接失败: {e}"
            logger.warning(message)
            return False, message

        except Exception as e:
            message = f"连接异常: {e}"
            logger.error(message)
            return False, message

        finally:
            if test_conn is not None:
                try:
                    test_conn.close()
                except Exception:
                    pass

    def get_databases(self) -> List[str]:
        """
        获取数据库列表

        Returns:
            数据库名称列表

        Raises:
            ConnectionError: 未连接时抛出
            QueryError: 查询失败时抛出
        """
        self._check_connected()

        try:
            with self._connection.cursor() as cursor:
                cursor.execute("SHOW DATABASES")
                result = cursor.fetchall()
                databases = [row["Database"] for row in result]

                # 过滤系统数据库（可选）
                # databases = [db for db in databases if db not in ("information_schema", "performance_schema", "mysql", "sys")]

                logger.info(f"获取到 {len(databases)} 个数据库")
                return databases

        except pymysql.Error as e:
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
            ConnectionError: 未连接时抛出
            QueryError: 查询失败时抛出
        """
        self._check_connected()

        try:
            with self._connection.cursor() as cursor:
                # 先切换到目标数据库
                cursor.execute(f"USE `{database}`")

                # 获取表状态信息
                cursor.execute("SHOW TABLE STATUS")
                tables = cursor.fetchall()

                result = []
                for table in tables:
                    data_length = table.get("Data_length") or 0
                    index_length = table.get("Index_length") or 0
                    result.append(
                        {
                            "name": table.get("Name", ""),
                            "rows": table.get("Rows") or 0,
                            "engine": table.get("Engine") or "",
                            "charset": (
                                table.get("Collation", "").split("_")[0]
                                if table.get("Collation")
                                else ""
                            ),
                            "size": data_length + index_length,
                            "comment": table.get("Comment") or "",
                        }
                    )

                logger.info(f"数据库 {database} 共有 {len(result)} 个表")
                return result

        except pymysql.Error as e:
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
            ConnectionError: 未连接时抛出
            QueryError: 查询失败时抛出
        """
        self._check_connected()

        try:
            with self._connection.cursor() as cursor:
                cursor.execute(f"SHOW FULL COLUMNS FROM `{database}`.`{table}`")
                columns = cursor.fetchall()

                result = []
                for col in columns:
                    result.append(
                        {
                            "name": col.get("Field", ""),
                            "type": col.get("Type", ""),
                            "null": col.get("Null", ""),
                            "key": col.get("Key", ""),
                            "default": col.get("Default", ""),
                            "extra": col.get("Extra", ""),
                            "comment": col.get("Comment", ""),
                        }
                    )

                logger.info(f"表 {database}.{table} 共有 {len(result)} 个字段")
                return result

        except pymysql.Error as e:
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
            ConnectionError: 未连接时抛出
            QueryError: 查询失败时抛出
        """
        self._check_connected()

        try:
            with self._connection.cursor() as cursor:
                logger.debug(f"执行 SQL: {sql}")
                affected_rows = cursor.execute(sql, params)

                if fetch:
                    result = cursor.fetchall()
                    message = f"查询成功，返回 {len(result)} 行"
                    return result, len(result), message
                else:
                    message = f"执行成功，影响 {affected_rows} 行"
                    return None, affected_rows, message

        except pymysql.Error as e:
            error_msg = f"SQL 执行失败: {e}"
            logger.error(error_msg)
            raise QueryError(error_msg)

    def execute_many(self, sql: str, params_list: List[tuple]) -> int:
        """
        批量执行 SQL

        Args:
            sql: SQL 语句模板
            params_list: 参数列表

        Returns:
            影响的总行数

        Raises:
            ConnectionError: 未连接时抛出
            QueryError: 查询失败时抛出
        """
        self._check_connected()

        try:
            with self._connection.cursor() as cursor:
                affected_rows = cursor.executemany(sql, params_list)
                logger.debug(f"批量执行完成，影响 {affected_rows} 行")
                return affected_rows

        except pymysql.Error as e:
            error_msg = f"批量执行失败: {e}"
            logger.error(error_msg)
            raise QueryError(error_msg)

    def begin_transaction(self):
        """开始事务"""
        self._check_connected()
        try:
            self._connection.begin()
            logger.debug("事务已开始")
        except pymysql.Error as e:
            raise QueryError(f"开始事务失败: {e}")

    def commit(self):
        """提交事务"""
        self._check_connected()
        try:
            self._connection.commit()
            logger.debug("事务已提交")
        except pymysql.Error as e:
            raise QueryError(f"提交事务失败: {e}")

    def rollback(self):
        """回滚事务"""
        self._check_connected()
        try:
            self._connection.rollback()
            logger.debug("事务已回滚")
        except pymysql.Error as e:
            raise QueryError(f"回滚事务失败: {e}")

    def _check_connected(self):
        """检查是否已连接"""
        if not self.is_connected:
            raise ConnectionError("数据库未连接")


# 全局连接实例
_db_connection: Optional[DatabaseConnection] = None


def get_db_connection() -> DatabaseConnection:
    """获取数据库连接单例"""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection
