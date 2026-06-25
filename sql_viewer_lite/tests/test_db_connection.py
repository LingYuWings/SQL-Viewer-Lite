"""
数据库连接单元测试

注意：这些测试需要实际的 MySQL 连接。
可以通过环境变量配置测试数据库：
- TEST_DB_HOST (默认: localhost)
- TEST_DB_PORT (默认: 3306)
- TEST_DB_USER (默认: root)
- TEST_DB_PASSWORD (默认: 空)
"""

import os
import pytest

from sql_viewer_lite.core.db_connection import (
    DatabaseConnection,
    DatabaseConnectionError,
    QueryError,
    ConnectionState,
)
from sql_viewer_lite.models.connection import ConnectionConfig

# 测试数据库配置
TEST_DB_HOST = os.environ.get("TEST_DB_HOST", "localhost")
TEST_DB_PORT = int(os.environ.get("TEST_DB_PORT", "3306"))
TEST_DB_USER = os.environ.get("TEST_DB_USER", "root")
TEST_DB_PASSWORD = os.environ.get("TEST_DB_PASSWORD", "root")


@pytest.fixture
def db_config():
    """创建测试数据库配置"""
    return ConnectionConfig(
        host=TEST_DB_HOST,
        port=TEST_DB_PORT,
        user=TEST_DB_USER,
        password=TEST_DB_PASSWORD,
    )


@pytest.fixture
def db_connection():
    """创建数据库连接实例"""
    return DatabaseConnection()


class TestDatabaseConnection:
    """DatabaseConnection 测试"""

    def test_initial_state(self, db_connection):
        """测试初始状态"""
        assert db_connection.state == ConnectionState.DISCONNECTED
        assert db_connection.is_connected is False
        assert db_connection.config is None
        assert db_connection.last_error is None

    def test_connect_success(self, db_connection, db_config):
        """测试成功连接"""
        result = db_connection.connect(db_config)

        assert result is True
        assert db_connection.is_connected is True
        assert db_connection.config is not None

        db_connection.disconnect()

    def test_connect_failure(self, db_connection):
        """测试连接失败"""
        bad_config = ConnectionConfig(
            host="invalid_host",
            port=9999,
            user="invalid_user",
            password="invalid_password",
        )

        with pytest.raises(DatabaseConnectionError):
            db_connection.connect(bad_config)

        assert db_connection.is_connected is False

    def test_disconnect(self, db_connection, db_config):
        """测试断开连接"""
        db_connection.connect(db_config)
        assert db_connection.is_connected is True

        db_connection.disconnect()
        assert db_connection.is_connected is False

    def test_test_connection_success(self, db_connection, db_config):
        """测试连接测试成功"""
        success, message = db_connection.test_connection(db_config)

        assert success is True
        assert "成功" in message or "MySQL" in message

    def test_test_connection_failure(self, db_connection):
        """测试连接测试失败"""
        bad_config = ConnectionConfig(host="invalid_host")
        success, message = db_connection.test_connection(bad_config)

        assert success is False
        assert len(message) > 0

    def test_get_databases(self, db_connection, db_config):
        """测试获取数据库列表"""
        db_connection.connect(db_config)

        databases = db_connection.get_databases()

        assert isinstance(databases, list)
        assert len(databases) > 0
        assert "information_schema" in databases

        db_connection.disconnect()

    def test_get_tables(self, db_connection, db_config):
        """测试获取表列表"""
        db_connection.connect(db_config)

        tables = db_connection.get_tables("information_schema")

        assert isinstance(tables, list)
        assert len(tables) > 0

        # 检查表信息结构
        table = tables[0]
        assert "name" in table
        assert "rows" in table
        assert "engine" in table

        db_connection.disconnect()

    def test_execute_query_select(self, db_connection, db_config):
        """测试执行 SELECT 查询"""
        db_connection.connect(db_config)

        sql = "SELECT 1 as test_col"
        result, row_count, message = db_connection.execute_query(sql)

        assert result is not None
        assert len(result) == 1
        assert result[0]["test_col"] == 1

        db_connection.disconnect()

    def test_execute_query_not_connected(self, db_connection):
        """测试未连接时执行查询"""
        with pytest.raises(DatabaseConnectionError):
            db_connection.execute_query("SELECT 1")

    def test_begin_commit_transaction(self, db_connection, db_config):
        """测试事务开始和提交"""
        db_connection.connect(db_config)

        db_connection.begin_transaction()
        db_connection.commit()

        db_connection.disconnect()

    def test_begin_rollback_transaction(self, db_connection, db_config):
        """测试事务开始和回滚"""
        db_connection.connect(db_config)

        db_connection.begin_transaction()
        db_connection.rollback()

        db_connection.disconnect()
