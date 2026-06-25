"""
数据库驱动抽象基类

定义统一的数据库驱动接口，支持多数据库扩展。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from sql_viewer_lite.models.connection import ConnectionConfig


@dataclass
class TableInfo:
    """表信息"""

    name: str
    rows: int = 0
    engine: str = ""
    charset: str = ""
    size: int = 0
    comment: str = ""


@dataclass
class ColumnInfo:
    """列信息"""

    name: str
    type: str
    nullable: bool = True
    default: Optional[str] = None
    is_primary_key: bool = False
    comment: str = ""


class DatabaseDriver(ABC):
    """
    数据库驱动抽象基类

    所有数据库驱动必须实现此接口。
    """

    @property
    @abstractmethod
    def driver_name(self) -> str:
        """驱动名称"""
        pass

    @property
    @abstractmethod
    def default_port(self) -> int:
        """默认端口"""
        pass

    @abstractmethod
    def connect(self, config: "ConnectionConfig") -> None:
        """
        建立数据库连接

        Args:
            config: 连接配置
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """关闭数据库连接"""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        测试连接是否正常

        Returns:
            连接是否成功
        """
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """是否已连接"""
        pass

    @abstractmethod
    def get_databases(self) -> List[str]:
        """
        获取数据库列表

        Returns:
            数据库名称列表
        """
        pass

    @abstractmethod
    def get_tables(self, database: str) -> List[TableInfo]:
        """
        获取指定数据库的表列表

        Args:
            database: 数据库名

        Returns:
            表信息列表
        """
        pass

    @abstractmethod
    def get_columns(self, database: str, table: str) -> List[ColumnInfo]:
        """
        获取表的列信息

        Args:
            database: 数据库名
            table: 表名

        Returns:
            列信息列表
        """
        pass

    @abstractmethod
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
        """
        pass

    @abstractmethod
    def begin_transaction(self) -> None:
        """开始事务"""
        pass

    @abstractmethod
    def commit(self) -> None:
        """提交事务"""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """回滚事务"""
        pass

    def escape_identifier(self, identifier: str) -> str:
        """
        转义标识符（表名、列名等）

        Args:
            identifier: 标识符

        Returns:
            转义后的标识符
        """
        # 默认使用双引号转义
        return f'"{identifier}"'

    def get_limit_sql(self, limit: int, offset: int = 0) -> str:
        """
        获取分页 SQL

        Args:
            limit: 每页行数
            offset: 偏移量

        Returns:
            分页 SQL 片段
        """
        # 默认使用标准 SQL 语法
        return f"LIMIT {limit} OFFSET {offset}"
