# SQL-Viewer Lite — 开发计划

## 总览

本项目分六个阶段迭代开发，每个阶段产出可运行的版本。各阶段之间存在依赖关系，后续阶段基于前一阶段的代码基础演进。

| 阶段 | 目标 | 预估周期 | 前置条件 | 状态 |
|------|------|---------|---------|------|
| **第一阶段** | 基础功能可用 | 2~3 周 | 无 | ✅ 已完成 |
| **第二阶段** | 体验优化 | 2~3 周 | 第一阶段完成 | ✅ 已完成 |
| **第三阶段** | 安全修复与代码重构 | 1 周 | 第二阶段完成 | ✅ 已完成 |
| **第四阶段** | 多连接管理 | 1~2 周 | 第三阶段完成 | ⬜ 待开始 |
| **第五阶段** | 多数据库支持 | 2~3 周 | 第三阶段完成 | ⬜ 待开始 |
| **第六阶段** | 打包发布 | 1~2 周 | 第四、五阶段完成 | ⬜ 待开始 |

---

## 第一阶段：基础功能可用 ✅

**目标**：跑通核心功能链路——登录 → 浏览 → 查看 → 编辑，UI 从简，确保功能正确。

### 里程碑

| # | 里程碑 | 交付物 | 状态 |
|---|--------|--------|------|
| M1 | 项目骨架搭建 | 目录结构、依赖清单、入口文件、基础 QSS | ✅ |
| M2 | 登录模块完成 | 登录窗口、连接管理、多连接保存 | ✅ |
| M3 | 数据库浏览完成 | 左侧数据库/表树、搜索过滤 | ✅ |
| M4 | 数据查看完成 | 表格分页加载、排序、列筛选 | ✅ |
| M5 | 数据编辑完成 | 单元格编辑、新增/删除行、事务提交 | ✅ |
| M6 | 多线程集成 | Worker 线程池、异步加载、取消操作 | ✅ |
| M7 | CLI 后端 + 单元测试 | 命令行接口、核心模块测试覆盖 | ✅ |

### 验收标准

- [x] 能成功登录 MySQL 并加载数据库列表
- [x] 能浏览数据库/表，双击打开查看数据
- [x] 大表分页加载不卡顿
- [x] 能编辑单元格、新增/删除行并提交
- [x] 多表同时加载时主界面保持响应
- [x] CLI 后端能独立执行查询并导出
- [x] 核心模块单元测试通过

---

## 第二阶段：体验优化 ✅

**目标**：在功能完整的基础上，提升 UI 美观度、交互流畅度和功能完善度。

### 里程碑

| # | 里程碑 | 交付物 | 状态 |
|---|--------|--------|------|
| M8 | UI 全面美化 | 深色/浅色主题、现代化布局、响应式设计 | ✅ |
| M9 | 功能增强 | SQL 执行器、数据导出、右键菜单 | ✅ |
| M10 | 国际化 | 中英文切换 | ✅ |
| M11 | SSH 隧道 | 支持通过 SSH 隧道连接远程 MySQL | ✅ |
| M12 | 性能优化 | 连接池、查询缓存、内存优化 | ✅ |

### 附加优化（已完成） ✅

- [x] 虚拟滚动表格：`DataTableModel` + `VirtualTableView`
- [x] 键盘快捷键：`ShortcutManager` 管理 16 个快捷键
- [x] UI 改进：树状图图标、中键关闭标签页、筛选控件 QScrollArea
- [x] 多进程优化：`ProcessWorker` + `WorkerManager` 双模式
- [x] HiDPI 支持：`AA_EnableHighDpiScaling` + `AA_UseHighDpiPixmaps`

### 验收标准

- [x] 深色/浅色主题切换正常
- [x] 所有界面元素响应式布局，缩放无错位
- [x] SQL 执行器能执行查询并展示结果
- [x] 数据导出 CSV / JSON / SQL 正确
- [x] 中英文切换完整
- [x] SSH 隧道连接远程 MySQL 成功
- [x] 大表（>10万行）首屏加载 < 3 秒

---

## 第三阶段：安全修复与代码重构 ✅

**目标**：修复代码审查中发现的安全漏洞和代码质量问题，为后续扩展打好基础。

### M16 — 安全漏洞修复（代码审查结果）

**审查时间**：2026-06-12 | **审查范围**：全部 18 个 Python 文件（~4,600 行）

#### CRITICAL（必须修复）

| # | 漏洞 | 文件 | 行号 | 修复方案 | 状态 |
|---|------|------|------|---------|------|
| C1 | SQL 注入：筛选条件 `LIKE '%{keyword}%'` | `table_view.py` | 628 | 参数化查询 `%s` + `LIKE CONCAT('%%', %s, '%%')` | ✅ 已修复 |
| C2 | SQL 注入：UPDATE SET 子句 | `table_view.py` | 824 | 参数化查询 `%s` | ✅ 已修复 |
| C3 | SQL 注入：INSERT VALUES 子句 | `table_view.py` | 847 | 参数化查询 `%s` | ✅ 已修复 |
| C4 | SQL 注入：WHERE 子句 | `table_view.py` | 885 | 参数化查询 `%s` | ✅ 已修复 |
| C5 | SSH 主机密钥未验证（MITM） | `ssh_tunnel.py` | 102 | `AutoAddPolicy` → `RejectPolicy` 或 `known_hosts` | ✅ 已修复 |
| C6 | AES-CBC 无认证（密文可篡改） | `encryption.py` | 92 | CBC → AES-GCM | ✅ 已修复 |

#### HIGH（应该修复）

| # | 漏洞 | 文件 | 行号 | 修复方案 | 状态 |
|---|------|------|------|---------|------|
| H1 | SQL 注入：`USE` 语句 | `db_connection.py` | 237 | 转义反引号 | ✅ 已修复 |
| H2 | SQL 注入：`SHOW FULL COLUMNS` | `db_connection.py` | 289 | 转义反引号 | ✅ 已修复 |
| H3 | SQL 注入：CLI `_export_sql` 值拼接 | `cli.py` | 242 | 参数化 + 转义单引号 | ⬜ 待修复 |
| H4 | 加密密钥文件无权限限制 | `encryption.py` | 57 | `os.chmod(key_file, 0o600)` | ✅ 已修复 |
| H5 | 配置文件创建无权限限制 | `config_manager.py` | 85 | `os.open(..., 0o600)` | ✅ 已修复 |
| H6 | Python 3.8 不兼容 `list[str]` | `connection.py` | 86 | → `List[str]` | ✅ 已修复 |
| H7 | `ConnectionError` 遮蔽 Python 内建 | `db_connection.py` | 18 | 重命名为 `DatabaseConnectionError` | ✅ 已修复 |
| H8 | 线程不安全单例模式（6 个模块） | 多个 | — | 加 `threading.Lock` | ✅ 已修复 |

#### MEDIUM（应修复）

| # | 漏洞 | 文件 | 行号 | 状态 |
|---|------|------|------|------|
| M1 | `except Exception: pass` 吞没异常 | `db_worker.py` | 344 | ⬜ 待修复 |
| M2 | SQL 执行器无 LIMIT 防护（DoS 风险） | `sql_editor.py` | 248 | ⬜ 待修复 |
| M3 | 信号重复连接 | `table_view.py` | 557-567 | ⬜ 待修复 |
| M4 | `cancel()` 无法实际中断查询 | `db_worker.py` | 77-79 | ⬜ 待修复 |
| M5 | 清理线程无退出信号 | `connection_pool.py` | 131 | ⬜ 待修复 |
| M6 | SSH 转发线程无上限 | `ssh_tunnel.py` | 174-178 | ⬜ 待修复 |
| M7 | SSH `disconnect()` 非线程安全 | `ssh_tunnel.py` | 217-249 | ⬜ 待修复 |
| M8 | 配置保存/加载非原子操作 | `config_manager.py` | 92-153 | ⬜ 待修复 |
| M9 | 解密无 IV 长度校验 | `encryption.py` | 126 | ⬜ 待修复 |
| M10 | 配置路径常量重复定义 5 处 | 多个 | — | ⬜ 待修复 |
| M11 | `i18n.py` 吞没设置加载异常 | `i18n.py` | 175 | ⬜ 待修复 |

#### LOW（建议修复）

| # | 问题 | 文件 | 状态 |
|---|------|------|------|
| L1 | `logger.info(f"...")` 应改为延迟求值 | 所有文件 | ⬜ 待修复 |
| L2 | 未使用导入 (`QProgressBar` 等) | `main.py` | ✅ 已清理 |
| L3 | 死代码 `_load_table_info()` | `main.py` | ✅ 已清理 |
| L4 | 编辑菜单 action 无 slot 连接 | `main.py` | ⬜ 待修复 |
| L5 | 查询历史未持久化 | `sql_editor.py` | ⬜ 待修复 |
| L6 | 危险 SQL 无确认提示 | `sql_editor.py` | ⬜ 待修复 |

### M17 — main.py 拆分重构 ✅

原 `main.py` 有 663 行，包含 `DatabaseTreeWidget` 和 `MainWindow` 两个大类，违反单一职责。

- [x] 提取 `DatabaseTreeWidget` → `ui/database_tree.py`（236 行）
- [x] 提取 `MainWindow` → `ui/main_window.py`（374 行）
- [x] `main.py` 仅保留入口函数和 HiDPI 配置（88 行）
- [x] 更新所有 import 路径
- [x] 验证：程序启动和功能不受影响

### M18 — 驱动抽象层（为多数据库做准备） ✅

已创建驱动抽象层，为多数据库支持做好准备。

- [x] 创建 `core/drivers/` 目录结构
- [x] 设计 `DatabaseDriver` 抽象基类（`core/drivers/base.py`）
- [x] 实现 `MySQLDriver` 适配器（`core/drivers/mysql.py`），封装现有 PyMySQL 逻辑
- [x] `ConnectionConfig` 添加 `db_type` 字段（默认 `"mysql"`，向后兼容）
- [x] 单元测试：现有 MySQL 功能回归通过（58 个测试全部通过）

**涉及文件**：

```
core/
├── drivers/
│   ├── __init__.py           # 驱动注册表
│   ├── base.py               # 抽象基类 DatabaseDriver（含 TableInfo, ColumnInfo）
│   └── mysql.py              # MySQL 适配器
models/
├── connection.py             # 新增 db_type 字段
```

### 验收标准

- [x] SQL 筛选和编辑操作全部使用参数化查询
- [x] `main.py` ≤ 100 行（从 663 行精简到 88 行）
- [x] `DatabaseDriver` 抽象基类定义清晰，MySQL 功能回归通过
- [x] 现有单元测试全部通过（58/58）

---

## 第四阶段：多连接管理 ⬜

**目标**：支持同时管理多个数据库连接，方便跨库操作和对比。

**前置条件**：第三阶段 M18（驱动抽象层）完成。

### M19 — ConnectionManager 改造

- [ ] 实现 `ConnectionManager` 类管理多个 `DatabaseConnection` 实例
- [ ] 每个连接独立维护连接状态和连接池
- [ ] 支持连接的创建、销毁、状态查询
- [ ] `get_db_connection()` 改为 `get_connection_manager()`

### M20 — 连接选择器 UI

- [ ] 工具栏添加连接下拉菜单
- [ ] 显示所有已保存的连接配置
- [ ] 支持快速切换当前活跃连接
- [ ] 显示连接状态指示器（已连接/断开/错误）

### M21 — 多连接数据库树

- [ ] 每个连接独立显示数据库/表树（顶层节点为连接名）
- [ ] 连接切换时刷新左侧树形结构
- [ ] 保留每个连接的展开状态

### M22 — SQL 执行器多连接支持

- [ ] SQL 执行器添加连接选择下拉框
- [ ] 支持指定目标连接执行查询
- [ ] 查询结果显示来源连接

### M23 — 多连接状态栏

- [ ] 显示当前活跃连接名称
- [ ] 显示所有已连接的数据库数量
- [ ] 支持点击切换连接

**涉及文件**：

- `core/db_connection.py` — 新增 `ConnectionManager` 类
- `core/drivers/base.py` — 驱动接口支持多实例
- `ui/main_window.py` — 连接选择器 UI
- `ui/database_tree.py` — 多连接树形结构
- `ui/sql_editor.py` — SQL 执行器连接选择
- `utils/config_manager.py` — 多连接配置存储

### 验收标准

- [ ] 能同时保持 ≥2 个数据库连接
- [ ] 连接切换时左侧树和标签页正确更新
- [ ] SQL 执行器能选择目标连接执行查询
- [ ] 连接断开后能自动重连或提示

---

## 第五阶段：多数据库支持 ⬜

**目标**：支持 PostgreSQL、SQLite、SQL Server 等多种数据库系统。

**前置条件**：第三阶段 M18（驱动抽象层）完成。

### M24 — PostgreSQL 支持

- [ ] 实现 `core/drivers/postgresql.py` PostgreSQL 适配器
  - 继承 `DatabaseDriver` 抽象基类
  - 实现 `connect()`, `disconnect()`, `execute_query()` 等方法
  - 处理 PostgreSQL 特有语法（`RETURNING`, `ILIKE`, `LIMIT/OFFSET`）
- [ ] 添加 `psycopg2` 依赖到 `requirements.txt`
- [ ] 更新登录窗口支持 PostgreSQL 类型选择
- [ ] 更新 `ConnectionConfig` 支持 PostgreSQL 配置（schema 等）
- [ ] 测试 PostgreSQL 连接与基本查询

### M25 — SQLite 支持

- [ ] 实现 `core/drivers/sqlite.py` SQLite 适配器
  - 继承 `DatabaseDriver` 抽象基类
  - 实现文件路径选择（无需主机/端口/用户名）
  - 处理 SQLite 特有语法（`AUTOINCREMENT`, `WITHOUT ROWID`）
- [ ] 更新登录窗口支持 SQLite 文件选择
- [ ] 实现 SQLite 数据库创建与打开
- [ ] 测试 SQLite 连接与基本查询

### M26 — SQL Server 支持

- [ ] 实现 `core/drivers/mssql.py` SQL Server 适配器
  - 继承 `DatabaseDriver` 抽象基类
  - 处理 SQL Server 特有语法（`TOP`, `IDENTITY`）
- [ ] 添加 `pymssql` 依赖到 `requirements.txt`
- [ ] 更新登录窗口支持 SQL Server 类型选择
- [ ] 测试 SQL Server 连接与基本查询

### M27 — 方言适配与功能降级

- [ ] SQL 方言适配器：根据 `db_type` 自动调整 `LIMIT/OFFSET`、引号等语法
- [ ] 功能降级处理：某些数据库不支持的功能优雅降级并提示
- [ ] 统一的连接测试接口
- [ ] 更新 SQL 执行器支持方言切换

**涉及文件**：

- `core/drivers/base.py` — 扩展方言接口
- `core/drivers/postgresql.py` — 新增
- `core/drivers/sqlite.py` — 新增
- `core/drivers/mssql.py` — 新增
- `models/connection.py` — 扩展 `db_type` 验证
- `ui/login_window.py` — 数据库类型选择 UI
- `ui/sql_editor.py` — 方言适配

### 验收标准

- [ ] 能连接 PostgreSQL 并完成基本 CRUD 操作
- [ ] 能连接 SQLite 并完成基本 CRUD 操作
- [ ] 能连接 SQL Server 并完成基本 CRUD 操作
- [ ] SQL 方言差异自动处理（LIMIT/TOP 等）
- [ ] 不支持的功能有友好提示而非崩溃

---

## 第六阶段：打包发布 ⬜

**目标**：将项目打包为独立可执行程序，发布 v1.0。

**前置条件**：第四、五阶段完成。

### M28 — PyInstaller 打包

- [ ] 编写 `build.spec` PyInstaller 配置文件
- [ ] 处理资源文件打包（QSS 样式、翻译文件）
- [ ] 处理多数据库驱动的动态加载
- [ ] 测试打包后程序
- [ ] Windows 平台打包测试
- [ ] macOS 平台打包测试（如有条件）

### M29 — 安装程序

- [ ] Windows 安装包（NSIS 或 Inno Setup）
- [ ] 安装包测试

### M30 — 文档与发布

- [ ] 编写 `README.md`
- [ ] 编写用户手册
- [ ] GitHub Release v1.0.0

---

## 风险与应对

| 风险 | 影响 | 应对策略 |
|------|------|---------|
| SQL 注入漏洞（`table_view.py` 筛选/编辑拼接） | **高** | 第三阶段 M16 优先修复，使用参数化查询 |
| `main.py` 膨胀（674 行含两个大类） | 中 | 第三阶段 M17 拆分重构 |
| 驱动抽象层迁移可能破坏现有功能 | 中 | M18 先抽取抽象层 + MySQL 适配器，回归测试后再接入新数据库 |
| PyQt5 大数据表格渲染性能不足 | 高 | ✅ 已使用虚拟滚动 (`QTableView` + `DataTableModel`) |
| PyMySQL 不支持某些 MySQL 特性 | 中 | 必要时降级到 `mysqlclient` |
| PyInstaller 打包体积过大 | 中 | 使用 `--exclude-module` 排除无用依赖，压缩资源 |
| SSH 隧道稳定性 | 中 | 超时重连机制，连接状态监控 |
| 跨平台兼容性（Win/Mac） | 中 | 早期就在双平台测试，避免后期大量修复 |
| Python GIL 限制多线程并行 | 中 | ✅ 已使用 `multiprocessing` 替代 QThread |
| 多连接管理与单例模式冲突 | 中 | 第四阶段重写 `get_db_connection()` 为 `get_connection_manager()` |
| 多数据库 SQL 方言差异 | 中 | 第五阶段 M27 统一方言适配层 |

---

## 版本规划

| 版本 | 阶段 | 主要内容 |
|------|------|---------|
| `v0.1.0` | 第一阶段 M1-M3 | 登录 + 浏览 |
| `v0.2.0` | 第一阶段 M4-M5 | 查看 + 编辑 |
| `v0.3.0` | 第一阶段 M6-M7 | 多线程 + CLI + 测试 |
| `v0.4.0` | 第二阶段 M8-M12 | UI 美化 + 功能增强 |
| `v0.4.1` | 第二阶段附加优化 | 虚拟滚动 + 快捷键 + 多进程 |
| `v0.5.0` | 第三阶段 M16-M18 | 安全修复 + 代码重构 + 驱动抽象层 |
| `v0.6.0` | 第四阶段 M19-M23 | 多连接管理 |
| `v0.7.0` | 第五阶段 M24-M25 | PostgreSQL + SQLite 支持 |
| `v0.8.0` | 第五阶段 M26-M27 | SQL Server + 方言适配 |
| `v1.0.0` | 第六阶段 M28-M30 | 打包发布 |
