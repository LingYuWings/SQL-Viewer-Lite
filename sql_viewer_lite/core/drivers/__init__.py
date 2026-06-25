"""
数据库驱动包

提供统一的数据库驱动接口，支持多数据库扩展。
"""

import logging
from typing import Dict, Type, Optional

from sql_viewer_lite.core.drivers.base import DatabaseDriver, TableInfo, ColumnInfo
from sql_viewer_lite.core.drivers.mysql import MySQLDriver
from sql_viewer_lite.core.drivers.sqlite import SQLiteDriver

logger = logging.getLogger(__name__)

# 驱动注册表
_DRIVER_REGISTRY: Dict[str, Type[DatabaseDriver]] = {
    "mysql": MySQLDriver,
    "sqlite": SQLiteDriver,
}


def register_driver(db_type: str, driver_class: Type[DatabaseDriver]) -> None:
    """
    注册数据库驱动

    Args:
        db_type: 数据库类型标识
        driver_class: 驱动类
    """
    _DRIVER_REGISTRY[db_type] = driver_class
    logger.info(f"已注册数据库驱动: {db_type} -> {driver_class.__name__}")


def get_driver(db_type: str) -> DatabaseDriver:
    """
    获取数据库驱动实例

    Args:
        db_type: 数据库类型标识

    Returns:
        驱动实例

    Raises:
        ValueError: 不支持的数据库类型
    """
    driver_class = _DRIVER_REGISTRY.get(db_type)
    if not driver_class:
        supported = ", ".join(_DRIVER_REGISTRY.keys())
        raise ValueError(
            f"不支持的数据库类型: {db_type}，支持的类型: {supported}"
        )
    return driver_class()


def get_supported_databases() -> list:
    """
    获取支持的数据库类型列表

    Returns:
        数据库类型标识列表
    """
    return list(_DRIVER_REGISTRY.keys())


__all__ = [
    "DatabaseDriver",
    "TableInfo",
    "ColumnInfo",
    "MySQLDriver",
    "register_driver",
    "get_driver",
    "get_supported_databases",
]
