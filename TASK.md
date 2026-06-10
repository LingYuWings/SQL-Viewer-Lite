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

## 第三阶段：打包发布（进行中）

### M13 — PyInstaller 打包

- [ ] 编写 `build.spec` PyInstaller 配置文件
- [ ] 处理资源文件打包
- [ ] 测试打包后程序
- [ ] Windows 平台打包测试
- [ ] macOS 平台打包测试（如有条件）

### M14 — 安装程序

- [ ] Windows 安装包（NSIS 或 Inno Setup）
- [ ] 安装包测试

### M15 — 文档与发布

- [ ] 编写 `README.md`
- [ ] GitHub Release v1.0.0

---

## 附加优化（第二阶段后新增）✅

### 虚拟滚动表格

- [x] 实现 `ui/data_table_model.py` — QAbstractTableModel 数据模型
- [x] 实现 `ui/virtual_table_view.py` — 虚拟滚动视图
- [x] 更新 `ui/table_view.py` 集成新组件
- [x] 编写单元测试 `tests/test_data_table_model.py`（22 个测试）
- [x] 支持编辑、排序、筛选功能

### 键盘快捷键

- [x] 实现 `utils/shortcuts.py` — 16 个快捷键定义
- [x] 在 `main.py` 注册快捷键
- [x] 快捷键配置持久化到 `~/.sql_viewer_lite/shortcuts.json`

### UI 改进

- [x] 树状图添加图标区分数据库/表节点
- [x] 鼠标中键关闭标签页（eventFilter）
- [x] 筛选控件使用 QScrollArea 防止拥挤
- [x] 修复筛选控件高度问题（固定 36px）

### 多进程优化

- [x] 实现 `ProcessWorker` 基于 multiprocessing.Process
- [x] 更新 `WorkerManager` 支持双模式（QThread/Process）
- [x] 更新 `DataTableView` 使用 ProcessWorker 异步加载

### HiDPI 支持

- [x] 启用 `Qt.AA_EnableHighDpiScaling`
- [x] 启用 `Qt.AA_UseHighDpiPixmaps`
- [x] 设置默认字体含抗锯齿

### 多连接管理

- [ ] 修改 `core/db_connection.py` 支持多连接实例管理
  - [ ] 实现 `ConnectionManager` 类管理多个连接
  - [ ] 每个连接独立维护连接状态
  - [ ] 支持连接池复用
- [ ] 实现连接选择器 UI
  - [ ] 在工具栏添加连接下拉菜单
  - [ ] 显示所有已保存的连接配置
  - [ ] 支持快速切换当前活跃连接
  - [ ] 显示连接状态指示器
- [ ] 更新数据库树支持多连接
  - [ ] 每个连接独立显示数据库/表树
  - [ ] 连接切换时刷新左侧树形结构
  - [ ] 保留每个连接的展开状态
- [ ] 更新 SQL 执行器支持多连接
  - [ ] 在 SQL 执行器添加连接选择下拉框
  - [ ] 支持指定目标连接执行查询
  - [ ] 查询结果显示来源连接
- [ ] 更新状态栏显示多连接信息
  - [ ] 显示当前活跃连接名称
  - [ ] 显示所有已连接的数据库数量
  - [ ] 支持点击切换连接
- [ ] 多连接配置存储
  - [ ] 支持同时保存多个连接配置
  - [ ] 连接配置分组管理
  - [ ] 最近使用的连接优先显示

---

## 待开发功能

- [ ] 右键菜单（复制单元格、导出选中行）
- [ ] 数据导出对话框
- [ ] 查询结果高亮
- [ ] 语法高亮（SQL 编辑器）
- [ ] 打包发布（PyInstaller）

---

## 附录：通用任务

以下任务贯穿整个开发过程，不属于特定里程碑：

- [x] Git 版本管理：每个里程碑完成后提交
- [x] 代码风格：遵循 PEP 8，使用 `black` 格式化
- [x] 日志记录：使用 `logging` 模块，关键操作记录日志
- [x] 异常处理：所有数据库操作捕获 `pymysql.Error` 并友好提示
- [x] 类型注解：核心模块使用 type hints
- [x] 文档注释：公共 API 编写 docstring
