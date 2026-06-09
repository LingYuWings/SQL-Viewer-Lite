"""
配置管理器单元测试
"""

import pytest
import json
from pathlib import Path

from sql_viewer_lite.models.connection import ConnectionConfig
from sql_viewer_lite.utils.config_manager import ConfigManager, ConfigManagerError


class TestConnectionConfig:
    """ConnectionConfig 测试"""

    def test_default_values(self):
        """测试默认值"""
        config = ConnectionConfig()
        assert config.host == "localhost"
        assert config.port == 3306
        assert config.user == "root"
        assert config.password == ""
        assert config.database is None
        assert config.alias is None

    def test_display_name_with_alias(self):
        """测试有别名时的显示名称"""
        config = ConnectionConfig(alias="My Server")
        assert config.display_name == "My Server"

    def test_display_name_without_alias(self):
        """测试无别名时的显示名称"""
        config = ConnectionConfig(host="192.168.1.1", port=3307, user="admin")
        assert config.display_name == "admin@192.168.1.1:3307"

    def test_to_dict(self):
        """测试转换为字典"""
        config = ConnectionConfig(host="localhost", port=3306, user="root")
        data = config.to_dict()

        assert data["host"] == "localhost"
        assert data["port"] == 3306
        assert data["user"] == "root"

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "host": "192.168.1.1",
            "port": 3307,
            "user": "admin",
            "password": "secret",
            "unknown_field": "ignored",
        }
        config = ConnectionConfig.from_dict(data)

        assert config.host == "192.168.1.1"
        assert config.port == 3307
        assert config.user == "admin"
        assert config.password == "secret"

    def test_to_json_from_json(self):
        """测试 JSON 序列化和反序列化"""
        original = ConnectionConfig(
            host="localhost",
            port=3306,
            user="root",
            password="test123",
            alias="Test",
        )

        json_str = original.to_json()
        restored = ConnectionConfig.from_json(json_str)

        assert restored.host == original.host
        assert restored.port == original.port
        assert restored.user == original.user
        assert restored.password == original.password
        assert restored.alias == original.alias

    def test_validate_valid(self):
        """测试有效配置验证"""
        config = ConnectionConfig(host="localhost", port=3306, user="root")
        errors = config.validate()
        assert len(errors) == 0

    def test_validate_invalid_port(self):
        """测试无效端口验证"""
        config = ConnectionConfig(port=99999)
        errors = config.validate()
        assert len(errors) > 0
        assert any("端口" in e for e in errors)

    def test_validate_empty_host(self):
        """测试空主机验证"""
        config = ConnectionConfig(host="")
        errors = config.validate()
        assert len(errors) > 0
        assert any("主机" in e for e in errors)


class TestConfigManager:
    """ConfigManager 测试"""

    def test_save_and_load(self, tmp_path):
        """测试保存和加载配置"""
        config_file = tmp_path / "configs.json"
        manager = ConfigManager(config_file)

        config = ConnectionConfig(
            host="localhost",
            port=3306,
            user="root",
            password="test123",
            alias="Test",
        )

        manager.save_config(config)

        configs = manager.load_configs()
        assert len(configs) == 1
        assert configs[0].alias == "Test"
        assert configs[0].password == "test123"  # 应该已解密

    def test_save_multiple_configs(self, tmp_path):
        """测试保存多个配置"""
        config_file = tmp_path / "configs.json"
        manager = ConfigManager(config_file)

        config1 = ConnectionConfig(alias="Server 1", host="192.168.1.1")
        config2 = ConnectionConfig(alias="Server 2", host="192.168.1.2")

        manager.save_config(config1)
        manager.save_config(config2)

        configs = manager.load_configs()
        assert len(configs) == 2

    def test_update_existing_config(self, tmp_path):
        """测试更新现有配置"""
        config_file = tmp_path / "configs.json"
        manager = ConfigManager(config_file)

        config1 = ConnectionConfig(alias="Test", host="localhost", password="old_pass")
        manager.save_config(config1)

        config2 = ConnectionConfig(alias="Test", host="localhost", password="new_pass")
        manager.save_config(config2)

        configs = manager.load_configs()
        assert len(configs) == 1
        assert configs[0].password == "new_pass"

    def test_delete_config(self, tmp_path):
        """测试删除配置"""
        config_file = tmp_path / "configs.json"
        manager = ConfigManager(config_file)

        config = ConnectionConfig(alias="To Delete")
        manager.save_config(config)

        assert manager.delete_config("To Delete") is True

        configs = manager.load_configs()
        assert len(configs) == 0

    def test_delete_nonexistent_config(self, tmp_path):
        """测试删除不存在的配置"""
        config_file = tmp_path / "configs.json"
        manager = ConfigManager(config_file)

        assert manager.delete_config("Nonexistent") is False

    def test_clear_all(self, tmp_path):
        """测试清除所有配置"""
        config_file = tmp_path / "configs.json"
        manager = ConfigManager(config_file)

        manager.save_config(ConnectionConfig(alias="Config 1"))
        manager.save_config(ConnectionConfig(alias="Config 2"))

        manager.clear_all()

        configs = manager.load_configs()
        assert len(configs) == 0

    def test_load_empty_file(self, tmp_path):
        """测试加载不存在的文件"""
        config_file = tmp_path / "nonexistent.json"
        manager = ConfigManager(config_file)

        configs = manager.load_configs()
        assert len(configs) == 0

    def test_load_invalid_json(self, tmp_path):
        """测试加载无效 JSON"""
        config_file = tmp_path / "configs.json"
        config_file.write_text("invalid json content", encoding="utf-8")

        manager = ConfigManager(config_file)

        with pytest.raises(ConfigManagerError):
            manager.load_configs()
