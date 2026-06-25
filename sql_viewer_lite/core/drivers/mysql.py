"""
MySQL 数据库驱动

基于 PyMySQL 实现的 MySQL 数据库驱动。
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING

import pymysql
from pymysql.cursors import DictCursor

from sql_viewer_lite.core.drivers.base import DatabaseDriver, TableInfo, ColumnInfo

if TYPE_CHECKING:
    from sql_viewer_lite.models.connection import ConnectionConfig

logger = logging.getLogger(__name__)


class MySQLDriver(DatabaseDriver):
    """
    MySQL 数据库驱动

    使用 PyMySQL 连接和操作 MySQL 数据库。
    """

    def __init__(self):
        self._connection: Optional[pymysql.Connection] = None
        self._in_transaction: bool = False

    @property
    def driver_name(self) -> str:
        """驱动名称"""
        return "mysql"

    @property
    def default_port(self) -> int:
        """默认端口"""
        return 3306

    def connect(self, config: "ConnectionConfig") -> None:
        """
        建立 MySQL 连接

        Args:
            config: 连接配置
        """
        try:
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
            logger.info(f"MySQL 连接成功: {config.user}@{config.host}:{config.port}/{config.database or ''}")
        except pymysql.Error as e:
            logger.error(f"MySQL 连接失败: {e}")
            raise ConnectionError(f"MySQL 连接失败: {e}")

    def disconnect(self) -> None:
        """关闭 MySQL 连接"""
        if self._connection:
            try:
                self._connection.close()
                logger.info("MySQL 连接已关闭")
            except Exception as e:
                logger.warning(f"关闭 MySQL 连接时出错: {e}")
            finally:
                self._connection = None
                self._in_transaction = False

    def test_connection(self) -> bool:
        """
        测试 MySQL 连接

        Returns:
            连接是否正常
        """
        if not self._connection:
            return False

        try:
            with self._connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"MySQL 连接测试失败: {e}")
            return False

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        if not self._connection:
            return False
        try:
            self._connection.ping(reconnect=False)
            return True
        except Exception:
            return False

    def get_databases(self) -> List[str]:
        """
        获取数据库列表

        Returns:
            数据库名称列表
        """
        if not self._connection:
            raise ConnectionError("数据库未连接")

        try:
            with self._connection.cursor() as cursor:
                cursor.execute("SHOW DATABASES")
                databases = [row["Database"] for row in cursor.fetchall()]
                return databases
        except pymysql.Error as e:
            logger.error(f"获取数据库列表失败: {e}")
            raise RuntimeError(f"获取数据库列表失败: {e}")

    def get_tables(self, database: str) -> List[TableInfo]:
        """
        获取表列表

        Args:
            database: 数据库名

        Returns:
            表信息列表
        """
        if not self._connection:
            raise ConnectionError("数据库未连接")

        try:
            with self._connection.cursor() as cursor:
                # 切换到目标数据库（转义反引号防注入）
                safe_db = database.replace("`", "``")
                cursor.execute(f"USE `{safe_db}`")

                # 获取表状态信息
                cursor.execute("SHOW TABLE STATUS")
                tables = cursor.fetchall()

                result = []
                for table in tables:
                    data_length = table.get("Data_length") or 0
                    index_length = table.get("Index_length") or 0
                    result.append(
                        TableInfo(
                            name=table.get("Name", ""),
                            rows=table.get("Rows") or 0,
                            engine=table.get("Engine") or "",
                            charset=(
                                table.get("Collation", "").split("_")[0]
                                if table.get("Collation")
                                else ""
                            ),
                            size=data_length + index_length,
                            comment=table.get("Comment") or "",
                        )
                    )
                return result
        except pymysql.Error as e:
            logger.error(f"获取表列表失败: {e}")
            raise RuntimeError(f"获取表列表失败: {e}")

    def get_columns(self, database: str, table: str) -> List[ColumnInfo]:
        """
        获取表的列信息

        Args:
            database: 数据库名
            table: 表名

        Returns:
            列信息列表
        """
        if not self._connection:
            raise ConnectionError("数据库未连接")

        try:
            with self._connection.cursor() as cursor:
                # 转义反引号防注入
                safe_db = database.replace("`", "``")
                safe_table = table.replace("`", "``")
                cursor.execute(
                    f"SHOW FULL COLUMNS FROM `{safe_db}`.`{safe_table}`"
                )
                columns = cursor.fetchall()

                # 获取主键信息
                cursor.execute(
                    f"SHOW KEYS FROM `{safe_db}`.`{safe_table}` WHERE Key_name = 'PRIMARY'"
                )
                primary_keys = {row["Column_name"] for row in cursor.fetchall()}

                result = []
                for col in columns:
                    result.append(
                        ColumnInfo(
                            name=col.get("Field", ""),
                            type=col.get("Type", ""),
                            nullable=col.get("Null") == "YES",
                            default=col.get("Default"),
                            is_primary_key=col.get("Field") in primary_keys,
                            comment=col.get("Comment") or "",
                        )
                    )
                return result
        except pymysql.Error as e:
            logger.error(f"获取列信息失败: {e}")
            raise RuntimeError(f"获取列信息失败: {e}")

    def execute_query(
        self, sql: str, params: Optional[Tuple] = None, fetch: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """
        执行 SQL 查询

        Args:
            sql: SQL 语句
            params: 查询参数（参数化查询）
            fetch: 是否获取结果

        Returns:
            查询结果（SELECT 语句）或 None

        Raises:
            RuntimeError: 查询失败时抛出
        """
        if not self._connection:
            raise ConnectionError("数据库未连接")

        try:
            with self._connection.cursor() as cursor:
                cursor.execute(sql, params)

                if fetch:
                    result = cursor.fetchall()
                    logger.debug(f"查询返回 {len(result)} 行")
                    return list(result)
                else:
                    return None
        except pymysql.Error as e:
            logger.error(f"查询执行失败: {e}\nSQL: {sql}")
            raise RuntimeError(f"查询执行失败: {e}")

    def begin_transaction(self) -> None:
        """开始事务"""
        if not self._connection:
            raise ConnectionError("数据库未连接")

        try:
            self._connection.autocommit(False)
            self._in_transaction = True
            logger.debug("事务已开始")
        except pymysql.Error as e:
            logger.error(f"开始事务失败: {e}")
            raise RuntimeError(f"开始事务失败: {e}")

    def commit(self) -> None:
        """提交事务"""
        if not self._connection:
            raise ConnectionError("数据库未连接")

        try:
            self._connection.commit()
            self._connection.autocommit(True)
            self._in_transaction = False
            logger.debug("事务已提交")
        except pymysql.Error as e:
            logger.error(f"提交事务失败: {e}")
            raise RuntimeError(f"提交事务失败: {e}")

    def rollback(self) -> None:
        """回滚事务"""
        if not self._connection:
            raise ConnectionError("数据库未连接")

        try:
            self._connection.rollback()
            self._connection.autocommit(True)
            self._in_transaction = False
            logger.debug("事务已回滚")
        except pymysql.Error as e:
            logger.error(f"回滚事务失败: {e}")
            raise RuntimeError(f"回滚事务失败: {e}")

    def escape_identifier(self, identifier: str) -> str:
        """
        转义标识符（使用 MySQL 反引号）

        Args:
            identifier: 标识符

        Returns:
            转义后的标识符
        """
        safe = identifier.replace("`", "``")
        return f"`{safe}`"

    def get_limit_sql(self, limit: int, offset: int = 0) -> str:
        """
        获取分页 SQL（MySQL 语法）

        Args:
            limit: 每页行数
            offset: 偏移量

        Returns:
            分页 SQL 片段
        """
        return f"LIMIT {limit} OFFSET {offset}"
