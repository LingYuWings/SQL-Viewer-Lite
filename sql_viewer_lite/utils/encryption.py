"""
加密工具模块 - 密码加密/解密

使用 AES-CBC 模式加密密码，密钥存储在用户目录下。
"""

import os
import json
import base64
import logging
from pathlib import Path
from typing import Optional

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

logger = logging.getLogger(__name__)

# 配置目录
CONFIG_DIR = Path.home() / ".sql_viewer_lite"
KEY_FILE = CONFIG_DIR / "key"


class EncryptionError(Exception):
    """加密/解密错误"""

    pass


class EncryptionManager:
    """
    加密管理器

    使用 AES-CBC 模式加密密码，密钥存储在本地文件中。
    """

    def __init__(self):
        self._key: Optional[bytes] = None
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """确保配置目录存在"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def _get_or_create_key(self) -> bytes:
        """
        获取或创建加密密钥

        如果密钥文件存在则读取，否则生成新密钥并保存。
        """
        if self._key is not None:
            return self._key

        if KEY_FILE.exists():
            try:
                with open(KEY_FILE, "rb") as f:
                    self._key = f.read()
                logger.debug("密钥已加载")
                return self._key
            except Exception as e:
                logger.error(f"读取密钥文件失败: {e}")
                raise EncryptionError(f"读取密钥文件失败: {e}")

        # 生成新密钥
        self._key = get_random_bytes(32)  # AES-256
        try:
            with open(KEY_FILE, "wb") as f:
                f.write(self._key)
            logger.info("新密钥已生成并保存")
            return self._key
        except Exception as e:
            logger.error(f"保存密钥文件失败: {e}")
            raise EncryptionError(f"保存密钥文件失败: {e}")

    def encrypt(self, plaintext: str) -> str:
        """
        加密明文

        Args:
            plaintext: 要加密的明文

        Returns:
            Base64 编码的密文（包含 IV）
        """
        if not plaintext:
            return ""

        try:
            key = self._get_or_create_key()
            iv = get_random_bytes(16)  # AES 块大小
            cipher = AES.new(key, AES.MODE_CBC, iv)

            # 填充并加密
            padded_data = pad(plaintext.encode("utf-8"), AES.block_size)
            ciphertext = cipher.encrypt(padded_data)

            # 组合 IV + 密文，然后 Base64 编码
            encrypted = base64.b64encode(iv + ciphertext).decode("utf-8")
            logger.debug("加密成功")
            return encrypted
        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise EncryptionError(f"加密失败: {e}")

    def decrypt(self, encrypted: str) -> str:
        """
        解密密文

        Args:
            encrypted: Base64 编码的密文（包含 IV）

        Returns:
            解密后的明文
        """
        if not encrypted:
            return ""

        try:
            key = self._get_or_create_key()

            # Base64 解码
            raw_data = base64.b64decode(encrypted)

            # 提取 IV 和密文
            iv = raw_data[:16]
            ciphertext = raw_data[16:]

            # 解密
            cipher = AES.new(key, AES.MODE_CBC, iv)
            padded_data = cipher.decrypt(ciphertext)

            # 去除填充
            plaintext = unpad(padded_data, AES.block_size).decode("utf-8")
            logger.debug("解密成功")
            return plaintext
        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise EncryptionError(f"解密失败: {e}")


# 全局单例
_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """获取加密管理器单例"""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


def encrypt_password(password: str) -> str:
    """
    加密密码（便捷函数）

    Args:
        password: 明文密码

    Returns:
        加密后的密码
    """
    return get_encryption_manager().encrypt(password)


def decrypt_password(encrypted_password: str) -> str:
    """
    解密密码（便捷函数）

    Args:
        encrypted_password: 加密后的密码

    Returns:
        解密后的明文密码
    """
    return get_encryption_manager().decrypt(encrypted_password)
