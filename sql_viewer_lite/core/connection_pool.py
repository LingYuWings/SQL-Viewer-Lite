"""
连接池模块

提供数据库连接复用，避免频繁创建/销毁连接。
"""

import logging
import threading
import time
from typing import Optional, Dict, Any
from collections import OrderedDict

from sql_viewer_lite.models.connection import ConnectionConfig
from sql_viewer_lite.core.db_connection import DatabaseConnection

logger = logging.getLogger(__name__)


class PooledConnection:
    """连接池中的连接"""

    def __init__(self, connection: DatabaseConnection, config: ConnectionConfig):
        self.connection = connection
        self.config = config
        self.created_at = time.time()
        self.last_used = time.time()
        self.in_use = False

    @property
    def is_expired(self) -> bool:
        """是否已过期（空闲超过 30 分钟）"""
        return not self.in_use and (time.time() - self.last_used) > 1800

    def touch(self):
        """更新最后使用时间"""
        self.last_used = time.time()


class ConnectionPool:
    """
    数据库连接池

    管理多个数据库连接，支持连接复用和自动回收。
    """

    def __init__(self, max_connections: int = 5):
        """
        初始化连接池

        Args:
            max_connections: 最大连接数
        """
        self._max_connections = max_connections
        self._pool: OrderedDict[str, PooledConnection] = OrderedDict()
        self._lock = threading.Lock()

        # 启动清理线程
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def _get_key(self, config: ConnectionConfig) -> str:
        """生成连接键"""
        return f"{config.host}:{config.port}:{config.user}"

    def get_connection(self, config: ConnectionConfig) -> DatabaseConnection:
        """
        获取连接

        如果池中有可用连接则复用，否则创建新连接。

        Args:
            config: 连接配置

        Returns:
            数据库连接
        """
        key = self._get_key(config)

        with self._lock:
            # 检查是否有可用连接
            if key in self._pool:
                pooled = self._pool[key]
                if not pooled.in_use and not pooled.is_expired:
                    pooled.in_use = True
                    pooled.touch()
                    logger.debug(f"复用连接: {key}")
                    return pooled.connection

            # 检查连接数是否达到上限
            if len(self._pool) >= self._max_connections:
                # 移除最旧的空闲连接
                self._remove_oldest_idle()

            # 创建新连接
            conn = DatabaseConnection()
            conn.connect(config)

            pooled = PooledConnection(conn, config)
            pooled.in_use = True
            self._pool[key] = pooled

            logger.debug(f"创建新连接: {key}，当前连接数: {len(self._pool)}")
            return conn

    def release_connection(self, config: ConnectionConfig):
        """
        释放连接（将连接标记为空闲）

        Args:
            config: 连接配置
        """
        key = self._get_key(config)

        with self._lock:
            if key in self._pool:
                self._pool[key].in_use = False
                self._pool[key].touch()
                logger.debug(f"释放连接: {key}")

    def _remove_oldest_idle(self):
        """移除最旧的空闲连接"""
        for key, pooled in self._pool.items():
            if not pooled.in_use:
                pooled.connection.disconnect()
                del self._pool[key]
                logger.debug(f"移除空闲连接: {key}")
                return

    def _cleanup_loop(self):
        """清理过期连接"""
        while True:
            time.sleep(300)  # 每 5 分钟检查一次

            with self._lock:
                expired_keys = [
                    key for key, pooled in self._pool.items() if pooled.is_expired
                ]

                for key in expired_keys:
                    pooled = self._pool[key]
                    pooled.connection.disconnect()
                    del self._pool[key]
                    logger.debug(f"清理过期连接: {key}")

    def close_all(self):
        """关闭所有连接"""
        with self._lock:
            for key, pooled in self._pool.items():
                try:
                    pooled.connection.disconnect()
                except Exception:
                    pass

            self._pool.clear()
            logger.info("已关闭所有连接")

    @property
    def active_connections(self) -> int:
        """获取活跃连接数"""
        with self._lock:
            return sum(1 for p in self._pool.values() if p.in_use)

    @property
    def idle_connections(self) -> int:
        """获取空闲连接数"""
        with self._lock:
            return sum(1 for p in self._pool.values() if not p.in_use)


class QueryCache:
    """
    查询结果缓存

    缓存相同 SQL 的查询结果，避免重复查询。
    """

    def __init__(self, ttl: float = 5.0, max_size: int = 100):
        """
        初始化查询缓存

        Args:
            ttl: 缓存过期时间（秒）
            max_size: 最大缓存条目数
        """
        self._ttl = ttl
        self._max_size = max_size
        self._cache: OrderedDict[str, tuple] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, sql: str) -> Optional[tuple]:
        """
        获取缓存结果

        Args:
            sql: SQL 查询

        Returns:
            缓存的结果，如果不存在或已过期返回 None
        """
        with self._lock:
            if sql in self._cache:
                result, timestamp = self._cache[sql]
                if time.time() - timestamp < self._ttl:
                    # 移到末尾（最近使用）
                    self._cache.move_to_end(sql)
                    logger.debug(f"缓存命中: {sql[:50]}...")
                    return result
                else:
                    # 已过期，移除
                    del self._cache[sql]

        return None

    def set(self, sql: str, result: tuple):
        """
        设置缓存

        Args:
            sql: SQL 查询
            result: 查询结果
        """
        with self._lock:
            # 检查大小限制
            if len(self._cache) >= self._max_size:
                # 移除最旧的
                self._cache.popitem(last=False)

            self._cache[sql] = (result, time.time())
            logger.debug(f"设置缓存: {sql[:50]}...")

    def invalidate(self, sql_pattern: str = None):
        """
        使缓存失效

        Args:
            sql_pattern: SQL 模式（如果为 None 则清除所有）
        """
        with self._lock:
            if sql_pattern:
                # 清除匹配的缓存
                keys_to_remove = [
                    k for k in self._cache.keys() if sql_pattern.lower() in k.lower()
                ]
                for key in keys_to_remove:
                    del self._cache[key]
            else:
                # 清除所有缓存
                self._cache.clear()

            logger.debug(f"缓存已清除: {sql_pattern or '全部'}")

    def clear(self):
        """清除所有缓存"""
        with self._lock:
            self._cache.clear()


# 全局实例
_connection_pool: Optional[ConnectionPool] = None
_query_cache: Optional[QueryCache] = None
_singleton_lock = threading.Lock()


def get_connection_pool() -> ConnectionPool:
    """获取连接池单例（线程安全）"""
    global _connection_pool
    if _connection_pool is None:
        with _singleton_lock:
            if _connection_pool is None:
                _connection_pool = ConnectionPool()
    return _connection_pool


def get_query_cache() -> QueryCache:
    """获取查询缓存单例（线程安全）"""
    global _query_cache
    if _query_cache is None:
        with _singleton_lock:
            if _query_cache is None:
                _query_cache = QueryCache()
    return _query_cache
