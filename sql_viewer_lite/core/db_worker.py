"""
数据库查询工作者模块

提供两种查询执行器：
- QueryWorker: 基于 QThread 的异步查询执行器（保留作为备选）
- ProcessWorker: 基于 multiprocessing 的多进程查询执行器（推荐）
"""

import logging
import multiprocessing
import threading
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


# ─── 多进程查询工作者 ──────────────────────────────────────────


def _process_worker_target(
    task_id: str,
    query_type: str,
    sql: str,
    params: tuple,
    config_dict: dict,
    result_queue: multiprocessing.Queue,
    cancel_event: multiprocessing.Event,
):
    """
    多进程工作者目标函数

    在子进程中执行数据库查询，通过 Queue 返回结果。

    Args:
        task_id: 任务标识
        query_type: 查询类型
        sql: SQL 语句
        params: 查询参数
        config_dict: 连接配置字典
        result_queue: 结果队列
        cancel_event: 取消事件
    """
    try:
        # 在子进程中重新创建连接配置
        from sql_viewer_lite.models.connection import ConnectionConfig

        config = ConnectionConfig.from_dict(config_dict)

        # 创建独立连接
        db_connection = DatabaseConnection()
        db_connection.connect(config)

        # 检查取消
        if cancel_event.is_set():
            result_queue.put(("cancelled", task_id, None, 0, "已取消"))
            return

        # 执行查询
        if query_type == "query":
            result, row_count, message = db_connection.execute_query(sql, params, fetch=True)
            result_queue.put(("result", task_id, result, row_count, message))
        elif query_type == "execute":
            result, affected_rows, message = db_connection.execute_query(sql, params, fetch=False)
            result_queue.put(("result", task_id, None, affected_rows, message))
        elif query_type == "count":
            result, _, message = db_connection.execute_query(sql, params, fetch=True)
            count = result[0].get("count", 0) if result else 0
            result_queue.put(("result", task_id, count, 1, message))
        elif query_type == "databases":
            databases = db_connection.get_databases()
            result_queue.put(("result", task_id, databases, len(databases), f"获取到 {len(databases)} 个数据库"))
        elif query_type == "tables":
            tables = db_connection.get_tables(sql)  # sql 字段传递数据库名
            result_queue.put(("result", task_id, tables, len(tables), f"获取到 {len(tables)} 个表"))
        else:
            result_queue.put(("error", task_id, f"未知查询类型: {query_type}", 0, ""))

        db_connection.disconnect()

    except Exception as e:
        logger.error(f"子进程查询失败: {e}")
        result_queue.put(("error", task_id, str(e), 0, ""))


class ProcessWorker(QObject):
    """
    多进程查询工作者

    使用 multiprocessing.Process 在独立进程中执行数据库查询，
    避免 Python GIL 限制，实现真正的并行执行。
    """

    # 信号：查询完成
    result_ready = pyqtSignal(str, object, int, str)  # task_id, result, row_count, message

    # 信号：查询错误
    error_occurred = pyqtSignal(str, str)  # task_id, error_message

    # 信号：查询完成（无论成功或失败）
    finished = pyqtSignal(str)  # task_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process: Optional[multiprocessing.Process] = None
        self._result_queue: Optional[multiprocessing.Queue] = None
        self._cancel_event: Optional[multiprocessing.Event] = None
        self._task_id: str = ""
        self._poll_timer: Optional[QTimer] = None

    @property
    def task_id(self) -> str:
        """获取任务标识"""
        return self._task_id

    def start(
        self,
        task_id: str,
        query_type: str,
        sql: str = "",
        params: tuple = None,
        config_dict: dict = None,
    ):
        """
        启动查询任务

        Args:
            task_id: 任务唯一标识
            query_type: 查询类型
            sql: SQL 语句
            params: 查询参数
            config_dict: 连接配置字典
        """
        self._task_id = task_id

        # 创建进程间通信对象
        self._result_queue = multiprocessing.Queue()
        self._cancel_event = multiprocessing.Event()

        # 创建子进程
        self._process = multiprocessing.Process(
            target=_process_worker_target,
            args=(
                task_id,
                query_type,
                sql,
                params or (),
                config_dict or {},
                self._result_queue,
                self._cancel_event,
            ),
            daemon=True,
        )

        # 启动轮询定时器检查结果
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_results)
        self._poll_timer.start(100)  # 每 100ms 检查一次

        # 启动进程
        self._process.start()
        logger.info(f"启动多进程查询: {task_id}")

    def cancel(self):
        """取消查询"""
        if self._cancel_event:
            self._cancel_event.set()
        if self._process and self._process.is_alive():
            self._process.terminate()
        logger.info(f"取消多进程查询: {self._task_id}")

    def _poll_results(self):
        """轮询结果队列"""
        if self._result_queue is None:
            return

        try:
            while not self._result_queue.empty():
                status, task_id, data, row_count, message = self._result_queue.get_nowait()

                if status == "result":
                    self.result_ready.emit(task_id, data, row_count, message)
                elif status == "error":
                    self.error_occurred.emit(task_id, str(data))
                elif status == "cancelled":
                    logger.info(f"查询已取消: {task_id}")

                # 清理
                self._cleanup()
                return

        except Exception as e:
            logger.warning(f"轮询结果队列异常: {e}")
            self._cleanup()

    def _cleanup(self):
        """清理资源"""
        if self._poll_timer:
            self._poll_timer.stop()
        if self._process and self._process.is_alive():
            self._process.join(timeout=1)
        self.finished.emit(self._task_id)

    def wait(self, timeout_ms: int = 1000):
        """等待进程完成"""
        if self._process and self._process.is_alive():
            self._process.join(timeout=timeout_ms / 1000)


class WorkerManager(QObject):
    """
    工作者管理器

    管理多个查询工作者，支持 QThread 和 multiprocessing 两种模式。
    """

    def __init__(self, parent=None, use_multiprocessing: bool = True):
        super().__init__(parent)
        self._thread_workers: Dict[str, QueryWorker] = {}
        self._process_workers: Dict[str, ProcessWorker] = {}
        self._use_multiprocessing = use_multiprocessing

    def start_query(
        self, task_id: str, query_type: str, sql: str = "", params: tuple = None
    ) -> QueryWorker:
        """
        启动查询任务（QThread 模式）

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
        worker.signals.finished.connect(lambda: self._on_thread_worker_finished(task_id))

        # 存储并启动
        self._thread_workers[task_id] = worker
        worker.start()

        logger.info(f"启动查询任务 (QThread): {task_id}")
        return worker

    def start_process_query(
        self,
        task_id: str,
        query_type: str,
        sql: str = "",
        params: tuple = None,
        config_dict: dict = None,
    ) -> ProcessWorker:
        """
        启动查询任务（多进程模式）

        Args:
            task_id: 任务唯一标识
            query_type: 查询类型
            sql: SQL 语句
            params: 查询参数
            config_dict: 连接配置字典

        Returns:
            ProcessWorker 实例
        """
        # 如果已有同名任务，先取消
        self.cancel_task(task_id)

        # 创建新工作者
        worker = ProcessWorker(self)

        # 连接信号
        worker.result_ready.connect(
            lambda tid, result, rc, msg: self._on_process_result(task_id, result, rc, msg)
        )
        worker.error_occurred.connect(
            lambda tid, err: self._on_process_error(task_id, err)
        )
        worker.finished.connect(lambda tid: self._on_process_worker_finished(task_id))

        # 存储
        self._process_workers[task_id] = worker

        # 启动
        worker.start(task_id, query_type, sql, params, config_dict)

        logger.info(f"启动查询任务 (Process): {task_id}")
        return worker

    def cancel_task(self, task_id: str):
        """取消指定任务"""
        # 取消 QThread 任务
        if task_id in self._thread_workers:
            worker = self._thread_workers[task_id]
            worker.cancel()
            worker.wait(1000)
            del self._thread_workers[task_id]
            logger.info(f"取消任务 (QThread): {task_id}")

        # 取消多进程任务
        if task_id in self._process_workers:
            worker = self._process_workers[task_id]
            worker.cancel()
            worker.wait(1000)
            del self._process_workers[task_id]
            logger.info(f"取消任务 (Process): {task_id}")

    def cancel_all(self):
        """取消所有任务"""
        for task_id in list(self._thread_workers.keys()):
            self.cancel_task(task_id)
        for task_id in list(self._process_workers.keys()):
            self.cancel_task(task_id)

    def get_worker(self, task_id: str) -> Optional[QueryWorker]:
        """获取指定任务的工作者（QThread）"""
        return self._thread_workers.get(task_id)

    def get_process_worker(self, task_id: str) -> Optional[ProcessWorker]:
        """获取指定任务的工作者（Process）"""
        return self._process_workers.get(task_id)

    def is_running(self, task_id: str) -> bool:
        """检查任务是否正在运行"""
        return task_id in self._thread_workers or task_id in self._process_workers

    def _on_thread_worker_finished(self, task_id: str):
        """QThread 工作者完成回调"""
        if task_id in self._thread_workers:
            del self._thread_workers[task_id]
            logger.debug(f"任务完成并清理 (QThread): {task_id}")

    def _on_process_result(self, task_id: str, result: Any, row_count: int, message: str):
        """多进程结果回调"""
        logger.debug(f"多进程查询结果: {task_id}, {row_count} 行")

    def _on_process_error(self, task_id: str, error: str):
        """多进程错误回调"""
        logger.error(f"多进程查询错误: {task_id}: {error}")

    def _on_process_worker_finished(self, task_id: str):
        """多进程工作者完成回调"""
        if task_id in self._process_workers:
            del self._process_workers[task_id]
            logger.debug(f"任务完成并清理 (Process): {task_id}")


# 全局工作者管理器
_worker_manager: Optional[WorkerManager] = None
_singleton_lock = threading.Lock()


def get_worker_manager() -> WorkerManager:
    """获取工作者管理器单例（线程安全）"""
    global _worker_manager
    if _worker_manager is None:
        with _singleton_lock:
            if _worker_manager is None:
                _worker_manager = WorkerManager()
    return _worker_manager
