# 改进计划：筛选功能审查 + 多进程性能优化

## TL;DR

> **目标**: 审查筛选功能可用性（有问题则回滚并记录），引入多进程避免 GIL 和死锁
>
> **核心改动**:
> 1. 审查 FilterWidget — 如果仍有问题则暂时移除，写入 TASK.md 待开发
> 2. 将 QThread 替换为 QProcess + multiprocessing.Pool，避免 Python GIL 限制
>
> **预计时间**: 1-2 小时
> **风险**: 中等（多进程涉及进程间通信）

---

## Context

### 当前问题

1. **筛选功能**: FilterWidget 仍可能存在布局问题，需要实际测试验证
2. **性能瓶颈**: 当前使用 `QThread` 执行数据库查询，受 Python GIL 限制，无法真正并行
3. **死锁风险**: 单进程多线程场景下，PyMySQL 连接可能因 GIL 产生死锁

### 涉及文件

- `sql_viewer_lite/ui/table_view.py` — FilterWidget 审查/回滚
- `sql_viewer_lite/core/db_worker.py` — QThread → QProcess 改造
- `sql_viewer_lite/core/db_connection.py` — 连接池多进程安全
- `TASK.md` — 记录待开发功能

---

## TODOs

### Part 1: 筛选功能审查

- [ ] 1. 测试筛选功能是否正常工作

  **What to do**:
  - 启动程序，连接数据库，打开一个表
  - 验证筛选输入框是否正确显示
  - 验证输入筛选条件后数据是否正确过滤
  - 验证清除筛选按钮是否正常工作
  - 如果有问题：移除 FilterWidget，在 TASK.md 中记录为待开发

  **Acceptance Criteria**:
  - [ ] 筛选功能正常工作，OR
  - [ ] 筛选功能已移除，TASK.md 已更新

  **Commit**: YES
  - Message: `fix(ui): remove filter widget temporarily / fix filter layout`

---

### Part 2: 多进程性能优化

- [ ] 2. 创建 ProcessWorker 基于 multiprocessing

  **What to do**:
  - 在 `sql_viewer_lite/core/db_worker.py` 中添加 `ProcessWorker` 类
  - 使用 `multiprocessing.Process` 替代 `QThread`
  - 使用 `multiprocessing.Queue` 进行进程间通信
  - 保持与现有 `QueryWorker` 相同的信号接口

  **Must NOT do**:
  - 不删除现有 QThread 实现（保留作为备选）
  - 不改变公共 API

  **References**:
  - `sql_viewer_lite/core/db_worker.py:40-165` — 现有 QueryWorker 实现
  - Python 文档: multiprocessing.Process, multiprocessing.Queue

  **Acceptance Criteria**:
  - [ ] ProcessWorker 能执行数据库查询
  - [ ] 进程间通信正常工作

  **Commit**: YES
  - Message: `feat(core): add ProcessWorker for multiprocessing`

---

- [ ] 3. 改造 WorkerManager 支持多进程

  **What to do**:
  - 修改 `WorkerManager` 支持 `ProcessWorker`
  - 添加进程池管理
  - 实现进程复用

  **References**:
  - `sql_viewer_lite/core/db_worker.py:167-247` — 现有 WorkerManager

  **Acceptance Criteria**:
  - [ ] WorkerManager 能管理多个进程
  - [ ] 进程完成后自动清理

  **Commit**: YES
  - Message: `refactor(core): update WorkerManager for multiprocessing`

---

- [ ] 4. 更新 DataTableView 使用新 Worker

  **What to do**:
  - 修改 `DataTableView._load_data()` 使用 ProcessWorker
  - 确保信号连接正常工作

  **References**:
  - `sql_viewer_lite/ui/table_view.py:480-530` — DataTableView 数据加载

  **Acceptance Criteria**:
  - [ ] 数据加载使用多进程
  - [ ] UI 不阻塞

  **Commit**: YES
  - Message: `refactor(ui): use ProcessWorker in DataTableView`

---

## Final Verification Wave

- [ ] F1. **功能测试** — 启动程序，验证所有功能正常
- [ ] F2. **性能测试** — 测试大数据量查询性能
- [ ] F3. **回归测试** — 运行 `python -m pytest sql_viewer_lite/tests/ -v`

---

## Success Criteria

```bash
python -m pytest sql_viewer_lite/tests/ -v  # 所有测试通过
python main.py  # 手动验证功能
```
