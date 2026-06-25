# SQL-Viewer Lite — 任务清单

> 本文件是开发过程中的任务跟踪清单。每项任务对应 PLAN.md 中的具体里程碑。
> 状态标记：`[ ]` 待做 / `[~]` 进行中 / `[x]` 已完成

---

## 第一阶段：基础功能可用 ✅

### M1 — 项目骨架搭建

- [x] 创建项目目录结构（ui/ core/ models/ utils/ backend/ tests/）
- [x] 编写 `requirements.txt`（PyQt5, PyMySQL, pycryptodome, paramiko 等）
- [x] 编写 `main.py` 程序入口，启动空白主窗口
- [x] 编写 `ui/__init__.py`、`core/__init__.py` 等包初始化文件
- [x] 编写基础 QSS 样式文件 `ui/styles/main.qss`
- [x] 验证：程序能正常启动并显示空白窗口

### M2 — 登录模块

- [x] 设计并实现 `ui/login_window.py` 登录窗口 UI
- [x] 实现 `core/db_connection.py` 数据库连接管理
- [x] 实现 `models/connection.py` 连接配置数据模型
- [x] 实现 `utils/config_manager.py` 配置持久化
- [x] 实现 `utils/encryption.py` 密码加密
- [x] 登录流程联调与错误处理

### M3 — 数据库浏览

- [x] 实现 `ui/main_window.py` 主窗口框架
- [x] 左侧数据库/表树形结构（QTreeWidget）
- [x] 实现搜索过滤
- [x] 表元信息获取与展示
- [x] 双击表名发射信号

### M4 — 数据查看

- [x] 实现 `ui/table_view.py` 数据表格组件
- [x] 分页加载：每页 500 行
- [x] 列排序
- [x] 列筛选
- [x] 实现 `ui/table_structure.py` 表结构查看

### M5 — 数据编辑

- [x] QTableWidget 启用单元格编辑
- [x] 编辑状态标记
- [x] 工具栏按钮（新增/删除/提交/撤销）
- [x] Diff 模型与事务提交

### M6 — 多线程集成

- [x] 实现 `core/db_worker.py` 查询工作者
- [x] 主窗口集成 Worker
- [x] 加载状态 UI
- [x] 取消操作

### M7 — CLI 后端 + 单元测试

- [x] 实现 `backend/cli.py` 命令行接口
- [x] 编写单元测试
- [x] 编写测试配置

---

## 第二阶段：体验优化 ✅

### M8 — UI 全面美化

- [x] 重写 `ui/styles/main.qss` 深色主题
- [x] 编写 `ui/styles/light.qss` 浅色主题
- [x] 主题切换机制与持久化
- [x] 主窗口布局优化
- [x] 登录窗口美化
- [x] 加载状态优化
- [x] 状态栏完善

### M9 — 功能增强

- [x] SQL 执行器（`ui/sql_editor.py`）
- [x] 查询历史
- [x] 数据导出
- [x] 右键菜单
- [x] 表搜索增强

### M10 — 国际化

- [x] 提取可翻译字符串
- [x] 编写中文/英文翻译
- [x] 集成 `QTranslator`
- [x] 语言偏好持久化

### M11 — SSH 隧道

- [x] 集成 `paramiko` 库
- [x] 登录窗口 SSH 隧道面板
- [x] 实现隧道连接
- [x] 隧道连接状态管理

### M12 — 性能优化

- [x] 数据库连接池
- [x] 查询结果缓存
- [x] 大数据量内存优化
- [x] 性能基准测试脚本

---

## 第三阶段：安全修复与代码重构 ✅

### M16 — 安全漏洞修复（代码审查结果）

**CRITICAL（必须修复）**

- [x] C1: `table_view.py:628` — 筛选条件 SQL 注入，改用参数化查询
- [x] C2: `table_view.py:824` — UPDATE SET 子句 SQL 注入，改用参数化查询
- [x] C3: `table_view.py:847` — INSERT VALUES 子句 SQL 注入，改用参数化查询
- [x] C4: `table_view.py:885` — WHERE 子句 SQL 注入，改用参数化查询
- [x] C5: `ssh_tunnel.py:102` — SSH `AutoAddPolicy` MITM 漏洞，改用 `RejectPolicy`
- [x] C6: `encryption.py:92` — AES-CBC 无认证，改用 AES-GCM

**HIGH（应该修复）**

- [x] H1: `db_connection.py:237` — `USE` 语句转义反引号
- [x] H2: `db_connection.py:289` — `SHOW FULL COLUMNS` 转义反引号
- [ ] H3: `cli.py:242` — `_export_sql` 值拼接改用转义
- [x] H4: `encryption.py:57` — 密钥文件 `os.chmod(key_file, 0o600)`
- [x] H5: `config_manager.py:85` — 配置文件 `os.open(..., 0o600)`
- [x] H6: `connection.py:86` — `list[str]` → `List[str]`（Python 3.8 兼容）
- [x] H7: `db_connection.py:18` — `ConnectionError` → `DatabaseConnectionError`
- [x] H8: 6 个模块单例加 `threading.Lock`

**MEDIUM（应修复）**

- [ ] M1: `db_worker.py:344` — `except Exception: pass` 改为 `logger.warning`
- [ ] M2: `sql_editor.py:248` — SQL 执行器加 LIMIT 防护
- [ ] M3: `table_view.py:557-567` — 消除信号重复连接
- [ ] M4: `db_worker.py:77` — `cancel()` 实际中断查询
- [ ] M5: `connection_pool.py:131` — 清理线程加退出信号
- [ ] M6: `ssh_tunnel.py:174` — SSH 转发线程数加限制
- [ ] M7: `ssh_tunnel.py:217` — `disconnect()` 加锁
- [ ] M8: `config_manager.py:92` — 配置保存加文件锁
- [ ] M9: `encryption.py:126` — 解密加 IV 长度校验
- [ ] M10: 配置路径常量集中到 `utils/constants.py`
- [ ] M11: `i18n.py:175` — 设置加载异常改为 `logger.warning`

**LOW（建议修复）**

- [ ] L1: `logger.info(f"...")` → `logger.info("...", arg)` 延迟求值
- [x] L2: `main.py` 未使用导入清理
- [x] L3: `main.py` 死代码 `_load_table_info()` 删除
- [ ] L4: `main.py` 编辑菜单 action 连接 slot
- [ ] L5: `sql_editor.py` 查询历史持久化
- [ ] L6: `sql_editor.py` 危险 SQL 确认提示

### M17 — main.py 拆分重构 ✅

- [x] 提取 `DatabaseTreeWidget` → `ui/database_tree.py`（236 行）
- [x] 提取 `MainWindow` → `ui/main_window.py`（374 行）
- [x] `main.py` 仅保留入口函数和 HiDPI 配置（88 行）
- [x] 更新所有 import 路径
- [x] 验证：程序启动和功能不受影响

### M18 — 驱动抽象层 ✅

- [x] 创建 `core/drivers/` 目录结构
- [x] 设计 `DatabaseDriver` 抽象基类（`core/drivers/base.py`）
- [x] 实现 `MySQLDriver` 适配器（`core/drivers/mysql.py`），封装现有 PyMySQL 逻辑
- [x] `ConnectionConfig` 添加 `db_type` 字段（默认 `"mysql"`，向后兼容）
- [x] 单元测试：现有 MySQL 功能回归通过（58/58 测试通过）

---

## 第四阶段：多连接管理 ⬜

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

---

## 第五阶段：多数据库支持 ⬜

### M24 — PostgreSQL 支持

- [ ] 实现 `core/drivers/postgresql.py` PostgreSQL 适配器
- [ ] 添加 `psycopg2` 依赖到 `requirements.txt`
- [ ] 更新登录窗口支持 PostgreSQL 类型选择
- [ ] 更新 `ConnectionConfig` 支持 PostgreSQL 配置（schema 等）
- [ ] 测试 PostgreSQL 连接与基本查询

### M25 — SQLite 支持

- [ ] 实现 `core/drivers/sqlite.py` SQLite 适配器
- [ ] 更新登录窗口支持 SQLite 文件选择
- [ ] 实现 SQLite 数据库创建与打开
- [ ] 测试 SQLite 连接与基本查询

### M26 — SQL Server 支持

- [ ] 实现 `core/drivers/mssql.py` SQL Server 适配器
- [ ] 添加 `pymssql` 依赖到 `requirements.txt`
- [ ] 更新登录窗口支持 SQL Server 类型选择
- [ ] 测试 SQL Server 连接与基本查询

### M27 — 方言适配与功能降级

- [ ] SQL 方言适配器：根据 `db_type` 自动调整 `LIMIT/OFFSET`、引号等语法
- [ ] 功能降级处理：某些数据库不支持的功能优雅降级并提示
- [ ] 统一的连接测试接口
- [ ] 更新 SQL 执行器支持方言切换

---

## 第六阶段：打包发布 ⬜

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

## 待开发功能

- [ ] 语法高亮（SQL 编辑器）

---

## 附录：通用任务

以下任务贯穿整个开发过程，不属于特定里程碑：

- [x] Git 版本管理：每个里程碑完成后提交
- [x] 代码风格：遵循 PEP 8，使用 `black` 格式化
- [x] 日志记录：使用 `logging` 模块，关键操作记录日志
- [x] 异常处理：所有数据库操作捕获 `pymysql.Error` 并友好提示
- [x] 类型注解：核心模块使用 type hints
- [x] 文档注释：公共 API 编写 docstring
