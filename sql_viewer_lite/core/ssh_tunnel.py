"""
SSH 隧道模块

提供通过 SSH 隧道连接远程 MySQL 的功能。
"""

import logging
import socket
import threading
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import paramiko

    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False
    logger.warning("paramiko 未安装，SSH 隧道功能不可用")


class SSHTunnelError(Exception):
    """SSH 隧道错误"""

    pass


class SSHTunnel:
    """
    SSH 隧道

    通过 SSH 隧道转发端口连接远程 MySQL。
    """

    def __init__(
        self,
        ssh_host: str,
        ssh_port: int = 22,
        ssh_user: str = "",
        ssh_password: str = "",
        remote_host: str = "127.0.0.1",
        remote_port: int = 3306,
        local_port: int = 0,  # 0 表示自动分配
        key_filename: Optional[str] = None,
    ):
        """
        初始化 SSH 隧道

        Args:
            ssh_host: SSH 主机地址
            ssh_port: SSH 端口
            ssh_user: SSH 用户名
            ssh_password: SSH 密码
            remote_host: 远程 MySQL 主机（默认 127.0.0.1）
            remote_port: 远程 MySQL 端口（默认 3306）
            local_port: 本地转发端口（0 表示自动分配）
            key_filename: SSH 密钥文件路径（可选）
        """
        if not HAS_PARAMIKO:
            raise SSHTunnelError("paramiko 未安装，无法使用 SSH 隧道")

        self._ssh_host = ssh_host
        self._ssh_port = ssh_port
        self._ssh_user = ssh_user
        self._ssh_password = ssh_password
        self._remote_host = remote_host
        self._remote_port = remote_port
        self._local_port = local_port
        self._key_filename = key_filename

        self._ssh_client: Optional[paramiko.SSHClient] = None
        self._transport: Optional[paramiko.Transport] = None
        self._channel = None
        self._is_connected = False
        self._server_socket: Optional[socket.socket] = None
        self._forward_thread: Optional[threading.Thread] = None

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._is_connected

    @property
    def local_port(self) -> int:
        """获取本地端口"""
        return self._local_port

    def connect(self) -> int:
        """
        建立 SSH 隧道

        Returns:
            本地端口号
        """
        if self._is_connected:
            return self._local_port

        try:
            # 创建 SSH 客户端
            self._ssh_client = paramiko.SSHClient()
            self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # 连接 SSH
            logger.info(f"连接 SSH: {self._ssh_user}@{self._ssh_host}:{self._ssh_port}")

            connect_kwargs = {
                "hostname": self._ssh_host,
                "port": self._ssh_port,
                "username": self._ssh_user,
            }

            if self._ssh_password:
                connect_kwargs["password"] = self._ssh_password

            if self._key_filename:
                connect_kwargs["key_filename"] = self._key_filename

            self._ssh_client.connect(**connect_kwargs)

            # 打开传输通道
            self._transport = self._ssh_client.get_transport()

            # 创建本地端口转发
            self._setup_port_forwarding()

            self._is_connected = True
            logger.info(f"SSH 隧道建立成功，本地端口: {self._local_port}")

            return self._local_port

        except Exception as e:
            self.disconnect()
            raise SSHTunnelError(f"SSH 隧道建立失败: {e}")

    def _setup_port_forwarding(self):
        """设置端口转发"""
        # 创建本地服务器套接字
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # 绑定到本地端口
        if self._local_port == 0:
            self._server_socket.bind(("127.0.0.1", 0))
            self._local_port = self._server_socket.getsockname()[1]
        else:
            self._server_socket.bind(("127.0.0.1", self._local_port))

        self._server_socket.listen(5)

        # 启动转发线程
        self._forward_thread = threading.Thread(target=self._forward_loop, daemon=True)
        self._forward_thread.start()

    def _forward_loop(self):
        """转发循环"""
        while self._is_connected:
            try:
                # 接受本地连接
                self._server_socket.settimeout(1.0)
                try:
                    client_socket, addr = self._server_socket.accept()
                except socket.timeout:
                    continue

                # 打开到远程的通道
                channel = self._transport.open_channel(
                    "direct-tcpip",
                    (self._remote_host, self._remote_port),
                    client_socket.getsockname(),
                )

                # 启动双向转发
                threading.Thread(
                    target=self._forward,
                    args=(client_socket, channel),
                    daemon=True,
                ).start()

            except Exception as e:
                if self._is_connected:
                    logger.error(f"转发错误: {e}")
                break

    def _forward(self, client_socket: socket.socket, channel):
        """双向转发数据"""
        import select

        try:
            while self._is_connected:
                r, _, _ = select.select([client_socket, channel.sock], [], [], 1.0)

                if not r:
                    continue

                for sock in r:
                    data = sock.recv(4096)
                    if not data:
                        return

                    if sock is client_socket:
                        channel.send(data)
                    else:
                        client_socket.send(data)
        except Exception:
            pass
        finally:
            try:
                channel.close()
            except Exception:
                pass
            try:
                client_socket.close()
            except Exception:
                pass

    def disconnect(self):
        """断开 SSH 隧道"""
        self._is_connected = False

        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
            self._server_socket = None

        if self._channel:
            try:
                self._channel.close()
            except Exception:
                pass
            self._channel = None

        if self._transport:
            try:
                self._transport.close()
            except Exception:
                pass
            self._transport = None

        if self._ssh_client:
            try:
                self._ssh_client.close()
            except Exception:
                pass
            self._ssh_client = None

        logger.info("SSH 隧道已断开")

    def get_tunnel_config(self) -> Tuple[str, int]:
        """
        获取隧道配置（用于 MySQL 连接）

        Returns:
            (本地主机, 本地端口)
        """
        if not self._is_connected:
            raise SSHTunnelError("SSH 隧道未连接")

        return "127.0.0.1", self._local_port
