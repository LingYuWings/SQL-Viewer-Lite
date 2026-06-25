"""
SQLite 数据库驱动

基于 Python 内置 sqlite3 模块实现的 SQLite 数据库驱动。
"""

import logging
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING

from sql_viewer_lite.core.drivers.base import DatabaseDriver, TableInfo, ColumnInfo

if TYPE_CHECKING:
    from sql_viewer_lite.models.connection import ConnectionConfig

logger = logging.getLogger(__name__)


class SQLiteDriver(DatabaseDriver):
    """
    SQLite 数据库驱动

    使用 Python 内置 sqlite3 模块连接和操作 SQLite 数据库。
    """

    def __init__(self):
        self._connection: Optional[sqlite3.Connection] = None
        self._file_path: Optional[str] = None

    @property
    def driver_name(self) -> str:
        """驱动名称"""
        return "sqlite"

    @property
    def default_port(self) -> int:
        """默认端口（SQLite 无端口概念）"""
        return 0

    def connect(self, config: "ConnectionConfig") -> None:
        """
        建立 SQLite 连接

        Args:
            config: 连接配置（使用 file_path 字段）
        """
        file_path = config.file_path
        if not file_path:
            raise ConnectionError("SQLite 数据库文件路径不能为空")

        try:
            path = Path(file_path)
            # 如果文件不存在，SQLite 会自动创建
            self._connection = sqlite3.connect(str(path))
            self._connection.row_factory = sqlite3.Row
            # 启用外键约束
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._file_path = str(path)
            logger.info(f"SQLite 连接成功: {path}")
        except sqlite3.Error as e:
            logger.error(f"SQLite 连接失败: {e}")
            raise ConnectionError(f"SQLite 连接失败: {e}")

    def disconnect(self) -> None:
        """关闭 SQLite 连接"""
        if self._connection:
            try:
                self._connection.close()
                logger.info("SQLite 连接已关闭")
            except Exception as e:
                logger.warning(f"关闭 SQLite 连接时出错: {e}")
            finally:
                self._connection = None
                self._file_path = None

    def test_connection(self) -> bool:
        """
        测试 SQLite 连接

        Returns:
            连接是否正常
        """
        if not self._connection:
            return False

        try:
            self._connection.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"SQLite 连接测试失败: {e}")
            return False

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connection is not None

    def get_databases(self) -> List[str]:
        """
        获取数据库列表

        SQLite 单数据库，返回文件名。

        Returns:
            数据库名称列表
        """
        if not self._connection:
            raise ConnectionError("数据库未连接")

        # SQLite 只有一个主数据库
        if self._file_path:
            return [Path(self._file_path).stem]
        return ["main"]

    def get_tables(self, database: str) -> List[TableInfo]:
        """
        获取表列表

        Args:
            database: 数据库名（SQLite 中忽略，始终查询主数据库）

        Returns:
            表信息列表
        """
        if not self._connection:
            raise ConnectionError("数据库未连接")

        try:
            cursor = self._connection.cursor()

            # 获取所有表
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = cursor.fetchall()

            result = []
            for row in tables:
                table_name = row["name"]

                # 获取行数
                try:
                    cursor.execute(f'SELECT COUNT(*) as cnt FROM "{table_name}"')
                    count_row = cursor.fetchone()
                    row_count = count_row["cnt"] if count_row else 0
                except sqlite3.Error:
                    row_count = 0

                # 获取页面大小（估算表大小）
                try:
                    cursor.execute(f'PRAGMA table_info("{table_name}")')
                    columns = cursor.fetchall()
                    col_count = len(columns)
                except sqlite3.Error:
                    col_count = 0

                result.append(
                    TableInfo(
                        name=table_name,
                        rows=row_count,
                        engine="sqlite",
                        charset="UTF-8",
                        size=0,  # SQLite 没有直接的表大小查询
                        comment=f"{col_count} 列",
                    )
                )

            return result
        except sqlite3.Error as e:
            logger.error(f"获取表列表失败: {e}")
            raise RuntimeError(f"获取表列表失败: {e}")

    def get_columns(self, database: str, table: str) -> List[ColumnInfo]:
        """
        获取表的列信息

        Args:
            database: 数据库名（SQLite 中忽略）
            table: 表名

        Returns:
            列信息列表
        """
        if not self._connection:
            raise ConnectionError("数据库未连接")

        try:
            cursor = self._connection.cursor()
            cursor.execute(f'PRAGMA table_info("{table}")')
            columns = cursor.fetchall()

            result = []
            for col in columns:
                result.append(
                    ColumnInfo(
                        name=col["name"],
                        type=col["type"],
                        nullable=not col["notnull"],
                        default=col["dflt_value"],
                        is_primary_key=bool(col["pk"]),
                        comment="",
                    )
                )
            return result
        except sqlite3.Error as e:
            logger.error(f"获取列信息失败: {e}")
            raise RuntimeError(f"获取列信息失败: {e}")

    def execute_query(
        self, sql: str, params: Optional[Tuple] = None, fetch: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """
        执行 SQL 查询

        Args:
            sql: SQL 语句
            params: 查询参数
            fetch: 是否获取结果

        Returns:
            查询结果（SELECT 语句）或 None

        Raises:
            RuntimeError: 查询失败时抛出
        """
        if not self._connection:
            raise ConnectionError("数据库未连接")

        try:
            cursor = self._connection.cursor()

            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            if fetch:
                rows = cursor.fetchall()
                result = [dict(row) for row in rows]
                logger.debug(f"查询返回 {len(result)} 行")
                return result
            else:
                return None
        except sqlite3.Error as e:
            logger.error(f"查询执行失败: {e}\nSQL: {sql}")
            raise RuntimeError(f"查询执行失败: {e}")

    def begin_transaction(self) -> None:
        """开始事务"""
        if not self._connection:
            raise ConnectionError("数据库未连接")

        try:
            self._connection.execute("BEGIN")
            logger.debug("事务已开始")
        except sqlite3.Error as e:
            logger.error(f"开始事务失败: {e}")
            raise RuntimeError(f"开始事务失败: {e}")

    def commit(self) -> None:
        """提交事务"""
        if not self._connection:
            raise ConnectionError("数据库未连接")

        try:
            self._connection.commit()
            logger.debug("事务已提交")
        except sqlite3.Error as e:
            logger.error(f"提交事务失败: {e}")
            raise RuntimeError(f"提交事务失败: {e}")

    def rollback(self) -> None:
        """回滚事务"""
        if not self._connection:
            raise ConnectionError("数据库未连接")

        try:
            self._connection.rollback()
            logger.debug("事务已回滚")
        except sqlite3.Error as e:
            logger.error(f"回滚事务失败: {e}")
            raise RuntimeError(f"回滚事务失败: {e}")

    def escape_identifier(self, identifier: str) -> str:
        """
        转义标识符（使用双引号）

        Args:
            identifier: 标识符

        Returns:
            转义后的标识符
        """
        safe = identifier.replace('"', '""')
        return f'"{safe}"'

    def get_limit_sql(self, limit: int, offset: int = 0) -> str:
        """
        获取分页 SQL（SQLite 语法）

        Args:
            limit: 每页行数
            offset: 偏移量

        Returns:
            分页 SQL 片段
        """
        return f"LIMIT {limit} OFFSET {offset}"
