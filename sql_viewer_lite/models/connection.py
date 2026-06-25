"""
连接配置模型 - 数据库连接信息

定义数据库连接配置的数据结构和序列化方法。
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# 支持的数据库类型
SUPPORTED_DB_TYPES = ["mysql", "postgresql", "sqlite", "mssql"]


@dataclass
class ConnectionConfig:
    """
    数据库连接配置

    Attributes:
        db_type: 数据库类型（mysql, postgresql, sqlite, mssql）
        host: 主机地址
        port: 端口号
        user: 用户名
        password: 密码（明文或加密后的）
        database: 数据库名（可选）
        alias: 连接别名（可选）
        file_path: SQLite 数据库文件路径（可选）
        ssh_host: SSH 主机（可选）
        ssh_port: SSH 端口（可选）
        ssh_user: SSH 用户名（可选）
        ssh_password: SSH 密码（可选）
        ssh_key_file: SSH 密钥文件路径（可选）
    """

    db_type: str = "mysql"  # 数据库类型，默认 MySQL（向后兼容）
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: Optional[str] = None
    alias: Optional[str] = None

    # SQLite 配置
    file_path: Optional[str] = None  # SQLite 数据库文件路径

    # SSH 隧道配置（Phase 2）
    ssh_host: Optional[str] = None
    ssh_port: Optional[int] = 22
    ssh_user: Optional[str] = None
    ssh_password: Optional[str] = None
    ssh_key_file: Optional[str] = None

    @property
    def display_name(self) -> str:
        """显示名称（用于 UI 展示）"""
        if self.alias:
            return self.alias
        if self.db_type == "sqlite" and self.file_path:
            from pathlib import Path
            return Path(self.file_path).name
        return f"{self.user}@{self.host}:{self.port}"

    @property
    def has_ssh_tunnel(self) -> bool:
        """是否配置了 SSH 隧道"""
        return self.ssh_host is not None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConnectionConfig":
        """从字典创建实例"""
        # 过滤掉未知字段
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)

    @classmethod
    def from_json(cls, json_str: str) -> "ConnectionConfig":
        """从 JSON 字符串创建实例"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def copy(self) -> "ConnectionConfig":
        """创建副本"""
        return ConnectionConfig.from_dict(self.to_dict())

    def validate(self) -> List[str]:
        """
        验证配置

        Returns:
            错误消息列表，空列表表示验证通过
        """
        errors = []

        # 验证数据库类型
        if self.db_type not in SUPPORTED_DB_TYPES:
            errors.append(f"不支持的数据库类型: {self.db_type}，支持的类型: {', '.join(SUPPORTED_DB_TYPES)}")

        # SQLite 验证文件路径
        if self.db_type == "sqlite":
            if not self.file_path:
                errors.append("SQLite 数据库文件路径不能为空")
        else:
            # MySQL/PostgreSQL/SQL Server 验证
            if not self.host:
                errors.append("主机地址不能为空")

            if not (1 <= self.port <= 65535):
                errors.append(f"端口号无效: {self.port}")

            if not self.user:
                errors.append("用户名不能为空")

        if self.ssh_host and not self.ssh_user:
            errors.append("SSH 用户名不能为空")

        if self.ssh_port and not (1 <= self.ssh_port <= 65535):
            errors.append(f"SSH 端口号无效: {self.ssh_port}")

        return errors


def create_default_config() -> ConnectionConfig:
    """创建默认连接配置"""
    return ConnectionConfig(
        host="localhost", port=3306, user="root", password="", alias="本地连接"
    )
