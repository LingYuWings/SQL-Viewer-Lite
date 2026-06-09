"""
加密模块单元测试
"""

import pytest
import tempfile
import os
from pathlib import Path

from sql_viewer_lite.utils.encryption import (
    EncryptionManager,
    encrypt_password,
    decrypt_password,
    EncryptionError,
)


class TestEncryptionManager:
    """EncryptionManager 测试"""

    def test_encrypt_decrypt(self, tmp_path):
        """测试加密和解密"""
        # 使用临时目录
        manager = EncryptionManager()
        manager._ensure_config_dir = lambda: None
        manager._key = None

        # 模拟密钥文件
        key_file = tmp_path / "key"
        manager._ensure_config_dir = lambda: key_file.parent.mkdir(
            parents=True, exist_ok=True
        )

        plaintext = "test_password_123"
        encrypted = manager.encrypt(plaintext)

        assert encrypted != plaintext
        assert len(encrypted) > 0

        decrypted = manager.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_empty_string(self):
        """测试加密空字符串"""
        manager = EncryptionManager()
        result = manager.encrypt("")
        assert result == ""

    def test_decrypt_empty_string(self):
        """测试解密空字符串"""
        manager = EncryptionManager()
        result = manager.decrypt("")
        assert result == ""

    def test_encrypt_different_results(self):
        """测试相同明文加密结果不同（因为 IV 不同）"""
        manager = EncryptionManager()

        plaintext = "same_password"
        encrypted1 = manager.encrypt(plaintext)
        encrypted2 = manager.encrypt(plaintext)

        # 由于 IV 不同，加密结果应该不同
        assert encrypted1 != encrypted2

    def test_decrypt_invalid_data(self):
        """测试解密无效数据"""
        manager = EncryptionManager()

        with pytest.raises(EncryptionError):
            manager.decrypt("invalid_base64_data!!!")


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_encrypt_decrypt_password(self):
        """测试 encrypt_password 和 decrypt_password"""
        password = "my_secret_password"
        encrypted = encrypt_password(password)

        assert encrypted != password

        decrypted = decrypt_password(encrypted)
        assert decrypted == password

    def test_roundtrip(self):
        """测试往返加密解密"""
        passwords = [
            "simple",
            "with spaces",
            "with!special@chars#",
            "中文密码",
            "123456",
            "",
        ]

        for password in passwords:
            if password:  # 跳过空密码
                encrypted = encrypt_password(password)
                decrypted = decrypt_password(encrypted)
                assert decrypted == password, f"Failed for password: {password}"
