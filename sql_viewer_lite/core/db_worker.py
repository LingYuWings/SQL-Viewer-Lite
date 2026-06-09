"""
数据库查询工作者模块

基于 QThread 的异步查询执行器，支持取消操作和进度更新。
"""

import logging
from typing import Optional, List, Dict, Any, Tuple

from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer

from sql_viewer_lite.core.db_connection import (
    get_db_connection,
    DatabaseConnection,
    QueryError,
)

logger = logging.getLogger(__name__)


class QueryWorkerSignals(QObject):
    """查询工作者信号"""

    # 查询完成信号: (结果列表, 影响行数, 消息)
    result_ready = pyqtSignal(object, int, str)

    # 错误信号: (错误消息)
    error_occurred = pyqtSignal(str)

    # 进度更新信号: (当前进度, 总数)
    progress_updated = pyqtSignal(int, int)

    # 开始信号
    started = pyqtSignal()

    # 完成信号（无论成功或失败）
    finished = pyqtSignal()


class QueryWorker(QThread):
    """
    查询工作者线程

    在后台线程执行数据库查询，避免阻塞主界面。
    """

    def __init__(
        self, query_type: str, sql: str = "", params: tuple = None, parent=None
    ):
        """
        初始化工作者

        Args:
            query_type: 查询类型 ('query', 'execute', 'count', 'databases', 'tables')
            sql: SQL 语句
            params: 查询参数
            parent: 父对象
        """
        super().__init__(parent)
        self._query_type = query_type
        self._sql = sql
        self._params = params
        self._is_cancelled = False
        self._signals = QueryWorkerSignals()

        # 创建独立的数据库连接（线程安全）
        self._db_connection = DatabaseConnection()

    @property
    def signals(self) -> QueryWorkerSignals:
        """获取信号对象"""
        return self._signals

    def cancel(self):
        """取消查询"""
        self._is_cancelled = True
        logger.info("查询已取消")

    def run(self):
        """执行查询"""
        self._signals.started.emit()

        try:
            # 复制主连接的配置来建立新连接
            main_conn = get_db_connection()
            if main_conn.config is None:
                self._signals.error_occurred.emit("数据库未连接")
                return

            # 建立独立连接
            self._db_connection.connect(main_conn.config)

            if self._is_cancelled:
                return

            # 根据查询类型执行
            if self._query_type == "query":
                self._execute_query()
            elif self._query_type == "execute":
                self._execute_update()
            elif self._query_type == "count":
                self._execute_count()
            elif self._query_type == "databases":
                self._fetch_databases()
            elif self._query_type == "tables":
                self._fetch_tables()
            else:
                self._signals.error_occurred.emit(f"未知查询类型: {self._query_type}")

        except Exception as e:
            if not self._is_cancelled:
                logger.error(f"查询执行失败: {e}")
                self._signals.error_occurred.emit(str(e))

        finally:
            self._db_connection.disconnect()
            self._signals.finished.emit()

    def _execute_query(self):
        """执行 SELECT 查询"""
        result, row_count, message = self._db_connection.execute_query(
            self._sql, self._params, fetch=True
        )

        if not self._is_cancelled:
            self._signals.result_ready.emit(result, row_count, message)

    def _execute_update(self):
        """执行 UPDATE/INSERT/DELETE 查询"""
        result, affected_rows, message = self._db_connection.execute_query(
            self._sql, self._params, fetch=False
        )

        if not self._is_cancelled:
            self._signals.result_ready.emit(None, affected_rows, message)

    def _execute_count(self):
        """执行 COUNT 查询"""
        result, _, message = self._db_connection.execute_query(
            self._sql, self._params, fetch=True
        )

        if not self._is_cancelled and result:
            count = result[0].get("count", 0)
            self._signals.result_ready.emit(count, 1, message)

    def _fetch_databases(self):
        """获取数据库列表"""
        databases = self._db_connection.get_databases()

        if not self._is_cancelled:
            self._signals.result_ready.emit(
                databases, len(databases), f"获取到 {len(databases)} 个数据库"
            )

    def _fetch_tables(self):
        """获取表列表"""
        database = self._sql  # 使用 sql 字段传递数据库名
        tables = self._db_connection.get_tables(database)

        if not self._is_cancelled:
            self._signals.result_ready.emit(
                tables, len(tables), f"获取到 {len(tables)} 个表"
            )


class WorkerManager(QObject):
    """
    工作者管理器

    管理多个查询工作者线程，支持并发执行。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._workers: Dict[str, QueryWorker] = {}

    def start_query(
        self, task_id: str, query_type: str, sql: str = "", params: tuple = None
    ) -> QueryWorker:
        """
        启动查询任务

        Args:
            task_id: 任务唯一标识
            query_type: 查询类型
            sql: SQL 语句
            params: 查询参数

        Returns:
            工作者实例
        """
        # 如果已有同名任务，先取消
        self.cancel_task(task_id)

        # 创建新工作者
        worker = QueryWorker(query_type, sql, params, self)

        # 完成后自动清理
        worker.signals.finished.connect(lambda: self._on_worker_finished(task_id))

        # 存储并启动
        self._workers[task_id] = worker
        worker.start()

        logger.info(f"启动查询任务: {task_id}")
        return worker

    def cancel_task(self, task_id: str):
        """取消指定任务"""
        if task_id in self._workers:
            worker = self._workers[task_id]
            worker.cancel()
            worker.wait(1000)  # 等待最多 1 秒
            del self._workers[task_id]
            logger.info(f"取消任务: {task_id}")

    def cancel_all(self):
        """取消所有任务"""
        for task_id in list(self._workers.keys()):
            self.cancel_task(task_id)

    def get_worker(self, task_id: str) -> Optional[QueryWorker]:
        """获取指定任务的工作者"""
        return self._workers.get(task_id)

    def is_running(self, task_id: str) -> bool:
        """检查任务是否正在运行"""
        return task_id in self._workers

    def _on_worker_finished(self, task_id: str):
        """工作者完成回调"""
        if task_id in self._workers:
            del self._workers[task_id]
            logger.debug(f"任务完成并清理: {task_id}")


# 全局工作者管理器
_worker_manager: Optional[WorkerManager] = None


def get_worker_manager() -> WorkerManager:
    """获取工作者管理器单例"""
    global _worker_manager
    if _worker_manager is None:
        _worker_manager = WorkerManager()
    return _worker_manager
