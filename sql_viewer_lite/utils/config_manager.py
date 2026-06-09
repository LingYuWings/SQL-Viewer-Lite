"""
配置管理器 - 连接配置的持久化存储

管理数据库连接配置的保存、加载、删除操作。
密码使用 AES 加密存储。
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

from sql_viewer_lite.models.connection import ConnectionConfig
from sql_viewer_lite.utils.encryption import encrypt_password, decrypt_password

logger = logging.getLogger(__name__)

# 配置目录和文件
CONFIG_DIR = Path.home() / ".sql_viewer_lite"
CONFIG_FILE = CONFIG_DIR / "configs.json"


class ConfigManagerError(Exception):
    """配置管理器错误"""

    pass


class ConfigManager:
    """
    配置管理器

    负责连接配置的持久化存储，支持保存、加载、删除操作。
    密码在存储时自动加密，读取时自动解密。
    """

    def __init__(self, config_file: Optional[Path] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径，默认为 ~/.sql_viewer_lite/configs.json
        """
        self._config_file = config_file or CONFIG_FILE
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """确保配置目录存在"""
        self._config_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_raw_configs(self) -> List[dict]:
        """
        加载原始配置数据

        Returns:
            配置字典列表
        """
        if not self._config_file.exists():
            return []

        try:
            with open(self._config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                logger.warning("配置文件格式错误，返回空列表")
                return []

            return data
        except json.JSONDecodeError as e:
            logger.error(f"配置文件 JSON 解析失败: {e}")
            raise ConfigManagerError(f"配置文件格式错误: {e}")
        except Exception as e:
            logger.error(f"读取配置文件失败: {e}")
            raise ConfigManagerError(f"读取配置文件失败: {e}")

    def _save_raw_configs(self, configs: List[dict]):
        """
        保存原始配置数据

        Args:
            configs: 配置字典列表
        """
        try:
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(configs, f, ensure_ascii=False, indent=2)
            logger.debug(f"配置已保存到 {self._config_file}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            raise ConfigManagerError(f"保存配置文件失败: {e}")

    def load_configs(self) -> List[ConnectionConfig]:
        """
        加载所有连接配置

        Returns:
            连接配置列表，密码已解密
        """
        raw_configs = self._load_raw_configs()
        configs = []

        for raw in raw_configs:
            try:
                # 解密密码
                if "password" in raw and raw["password"]:
                    raw["password"] = decrypt_password(raw["password"])

                config = ConnectionConfig.from_dict(raw)
                configs.append(config)
            except Exception as e:
                logger.warning(f"跳过无效配置: {e}")
                continue

        logger.info(f"加载了 {len(configs)} 个连接配置")
        return configs

    def save_config(self, config: ConnectionConfig):
        """
        保存连接配置

        如果存在同名配置则更新，否则新增。
        密码会自动加密后存储。

        Args:
            config: 连接配置
        """
        configs = self._load_raw_configs()

        # 准备保存的数据（加密密码）
        save_data = config.to_dict()
        if save_data["password"]:
            save_data["password"] = encrypt_password(save_data["password"])

        # 查找是否已存在同名配置
        alias = config.alias or f"{config.user}@{config.host}:{config.port}"
        existing_index = None
        for i, raw in enumerate(configs):
            raw_alias = (
                raw.get("alias")
                or f"{raw.get('user', '')}@{raw.get('host', '')}:{raw.get('port', 3306)}"
            )
            if raw_alias == alias:
                existing_index = i
                break

        if existing_index is not None:
            configs[existing_index] = save_data
            logger.info(f"更新连接配置: {alias}")
        else:
            configs.append(save_data)
            logger.info(f"新增连接配置: {alias}")

        self._save_raw_configs(configs)

    def delete_config(self, alias: str) -> bool:
        """
        删除连接配置

        Args:
            alias: 连接别名

        Returns:
            是否删除成功
        """
        configs = self._load_raw_configs()
        original_count = len(configs)

        # 过滤掉要删除的配置
        configs = [
            c
            for c in configs
            if (
                c.get("alias")
                or f"{c.get('user', '')}@{c.get('host', '')}:{c.get('port', 3306)}"
            )
            != alias
        ]

        if len(configs) < original_count:
            self._save_raw_configs(configs)
            logger.info(f"删除连接配置: {alias}")
            return True

        logger.warning(f"未找到配置: {alias}")
        return False

    def get_config_by_alias(self, alias: str) -> Optional[ConnectionConfig]:
        """
        根据别名获取连接配置

        Args:
            alias: 连接别名

        Returns:
            连接配置，未找到返回 None
        """
        configs = self.load_configs()
        for config in configs:
            if config.alias == alias:
                return config
        return None

    def clear_all(self):
        """清除所有配置"""
        self._save_raw_configs([])
        logger.info("已清除所有连接配置")


# 全局单例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取配置管理器单例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
