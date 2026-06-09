# SQL-Viewer Lite — 任务清单

> 本文件是开发过程中的任务跟踪清单。每项任务对应 PLAN.md 中的具体里程碑。
> 状态标记：`[ ]` 待做 / `[~]` 进行中 / `[x]` 已完成

---

## 第一阶段：基础功能可用

### M1 — 项目骨架搭建

- [x] 创建项目目录结构（ui/ core/ models/ utils/ backend/ tests/）
- [x] 编写 `requirements.txt`（PyQt5, PyMySQL, pycryptodome, paramiko 等）
- [x] 编写 `main.py` 程序入口，启动空白主窗口
- [x] 编写 `ui/__init__.py`、`core/__init__.py` 等包初始化文件
- [x] 编写基础 QSS 样式文件 `ui/styles/main.qss`
- [x] 验证：程序能正常启动并显示空白窗口

### M2 — 登录模块

- [x] 设计并实现 `ui/login_window.py` 登录窗口 UI
  - [x] 主机地址输入框（默认 localhost）
  - [x] 端口输入框（默认 3306）
  - [x] 用户名输入框
  - [x] 密码输入框（密码遮盖）
  - [x] "测试连接"按钮
  - [x] "登录"按钮
  - [x] "保存连接"复选框
- [x] 实现 `core/db_connection.py` 数据库连接管理
  - [x] `connect()` — 建立 PyMySQL 连接
  - [x] `disconnect()` — 断开连接
  - [x] `test_connection()` — 测试连接是否可用
  - [x] `get_databases()` — 获取数据库列表
  - [x] `get_tables(db_name)` — 获取指定数据库的表列表
  - [x] 连接状态管理（已连接 / 未连接 / 错误）
- [x] 实现 `models/connection.py` 连接配置数据模型
  - [x] 字段：host, port, user, password, database, alias
  - [x] 序列化 / 反序列化为 JSON
- [x] 实现 `utils/config_manager.py` 配置持久化
  - [x] `save_config(connection)` — 保存连接配置到本地文件
  - [x] `load_configs()` — 读取所有已保存的配置
  - [x] `delete_config(alias)` — 删除指定配置
  - [x] 配置文件路径：用户目录下 `.sql_viewer_lite/configs.json`
- [x] 实现 `utils/encryption.py` 密码加密
  - [x] `encrypt(password)` — AES 加密密码
  - [x] `decrypt(encrypted)` — AES 解密密码
  - [x] 密钥管理：首次运行生成并保存到 `.sql_viewer_lite/key`
- [x] 登录流程联调：输入 → 测试连接 → 登录 → 发射 `login_success` 信号
- [x] 错误处理：连接超时、认证失败、网络异常的友好提示
- [x] 验证：能成功登录 MySQL 并获取数据库列表

### M3 — 数据库浏览

- [x] 实现 `ui/main_window.py` 主窗口框架
  - [x] 左侧边栏区域（QDockWidget 或固定宽度 QWidget）
  - [x] 右侧数据展示区域（QTabWidget）
  - [x] 顶部工具栏（QToolBar）
  - [x] 底部状态栏（QStatusBar）
- [x] 左侧数据库/表树形结构（QTreeWidget）
  - [x] 一级节点：数据库名
  - [x] 二级节点：表名
  - [x] 节点图标区分数据库和表
  - [x] 点击数据库节点 → 展开/折叠表列表
- [x] 实现搜索过滤
  - [x] 顶部搜索框（QLineEdit）
  - [x] 实时过滤：输入关键字 → 筛选匹配的数据库/表名
  - [x] 使用 QSortFilterProxyModel 或手动过滤
- [x] 表元信息获取
  - [x] 执行 `SHOW TABLE STATUS` 获取表详情
  - [x] Tooltip 展示：行数、引擎、字符集、数据大小
- [x] 双击表名 → 发射 `table_selected(db_name, table_name)` 信号
- [x] 验证：能浏览数据库/表，搜索过滤正常

### M4 — 数据查看

- [x] 实现 `ui/table_view.py` 数据表格组件
  - [x] 基于 QTableWidget 或 QTableView + QStandardItemModel
  - [x] 分页加载：每页 500 行，底部翻页控件（上一页/下一页/页码/跳转）
  - [x] 自动计算总行数（`SELECT COUNT(*)`）
- [x] 列排序
  - [x] 点击列头 → 触发 `ORDER BY column ASC/DESC`
  - [x] 排序指示器图标
- [x] 列筛选
  - [x] 每列顶部添加筛选输入框
  - [x] 输入关键字 → 构建 `WHERE column LIKE '%keyword%'` 查询
  - [x] 多列筛选组合生效
- [x] 实现 `ui/table_structure.py` 表结构查看
  - [x] 执行 `DESCRIBE table_name` 或 `SHOW FULL COLUMNS`
  - [x] 展示：字段名、类型、是否可空、键、默认值、额外信息
  - [x] Tab 页展示（与数据 Tab 并列）
- [x] 表数据刷新按钮
- [x] 验证：能分页查看数据，排序和筛选正常

### M5 — 数据编辑

- [x] QTableWidget 启用单元格编辑（`DoubleClicked | SelectedClicked`）
- [x] 编辑状态标记：修改过的单元格高亮显示
- [x] 工具栏按钮
  - [x] "新增行" — 在表格末尾插入空行
  - [x] "删除行" — 删除选中行（可多选）
  - [x] "提交更改" — 执行 SQL 提交
  - [x] "撤销" — 丢弃所有未提交修改
- [x] Diff 模型
  - [x] 记录每个修改的单元格（原始值 → 新值）
  - [x] 新增行记录
  - [x] 删除行记录
- [x] 提交逻辑
  - [x] 构建 `UPDATE ... SET ... WHERE primary_key = ...` SQL
  - [x] 构建 `INSERT INTO ...` SQL
  - [x] 构建 `DELETE FROM ... WHERE ...` SQL
  - [x] 所有 SQL 在一个事务中执行
  - [x] 成功 → 清空 diff，刷新表格
  - [x] 失败 → 回滚事务，提示错误
- [x] 验证：能编辑、新增、删除并成功提交到数据库

### M6 — 多线程集成

- [x] 实现 `core/db_worker.py` 查询工作者
  - [x] 继承 QThread 或使用 `moveToThread` 模式
  - [x] 信号：`result_ready(object)`, `error_occurred(str)`, `progress_updated(int)`
  - [x] 支持取消操作：`cancel()` 方法设置标志位
- [x] 主窗口集成 Worker
  - [x] 打开表 → 创建 Worker → 执行查询 → 信号连接 UI 更新
  - [x] 多表同时加载：每个表独立 Worker，互不阻塞
  - [x] Worker 完成后自动清理
- [x] 加载状态 UI
  - [x] 表格区域显示加载指示器（QProgressBar 或 Spinner）
  - [x] 加载完成后隐藏指示器
- [x] 取消操作
  - [x] 加载中可点击"取消"中断查询
  - [x] 取消后清理 Worker，恢复 UI 状态
- [x] 验证：同时加载 3+ 个表，主界面不卡顿

### M7 — CLI 后端 + 单元测试

- [x] 实现 `backend/cli.py` 命令行接口
  - [x] 参数：`--host`, `--port`, `--user`, `--password`, `--database`
  - [x] 命令：`list-db`（列出数据库）、`list-tables`（列出表）
  - [x] 命令：`query "SELECT ..."`（执行 SQL 并输出结果）
  - [x] 命令：`export --format csv --output file.csv`（导出数据）
- [x] 编写单元测试
  - [x] `tests/test_db_connection.py` — 连接/断开/错误处理
  - [x] `tests/test_query_executor.py` — 查询执行/事务
  - [x] `tests/test_config_manager.py` — 配置读写
  - [x] `tests/test_encryption.py` — 加密/解密
- [x] 编写 `pytest.ini` 或 `pyproject.toml` 测试配置
- [x] 验证：CLI 能独立执行查询并导出 CSV，测试全部通过

---

## 第二阶段：体验优化

### M8 — UI 全面美化

- [x] 重写 `ui/styles/main.qss` 深色主题
  - [x] 全局背景色、文字色、边框色定义
  - [x] 输入框、按钮、表格、树形控件样式
  - [x] 悬停、聚焦、禁用状态样式
- [x] 编写 `ui/styles/light.qss` 浅色主题
- [x] 主题切换机制
  - [x] 设置菜单 → 选择深色/浅色 → 实时切换
  - [x] 主题偏好持久化到配置文件
- [x] 主窗口布局优化
  - [x] 可拖拽分割线调整侧边栏宽度
  - [x] 侧边栏可折叠/展开
  - [x] 窗口最小尺寸约束
- [x] 登录窗口美化
  - [x] 卡片式居中布局
  - [x] Logo / 品牌标题
  - [x] 连接历史下拉选择
- [x] 加载状态优化
  - [x] 骨架屏或 Spinner 动画替代简单进度条
  - [x] 表格加载时显示半透明遮罩
- [x] 状态栏完善
  - [x] 左侧：连接状态图标 + 服务器信息
  - [x] 中间：当前数据库 / 当前表名
  - [x] 右侧：总行数 + 查询耗时

### M9 — 功能增强

- [x] SQL 执行器
  - [x] 实现 `ui/sql_editor.py`：QDockWidget 中的 SQL 输入区
  - [x] 代码编辑器：等宽字体、行号（可选语法高亮）
  - [x] "执行"按钮 → 执行 SQL → 下方表格展示结果
  - [x] 执行耗时显示
- [x] 查询历史
  - [x] 记录每次执行的 SQL 和时间戳
  - [x] 侧边栏或下拉列表展示历史
  - [x] 点击历史记录 → 自动填入 SQL 输入框
- [x] 数据导出
  - [x] 选中行导出为 CSV
  - [x] 选中行导出为 JSON
  - [x] 选中行导出为 SQL INSERT 语句
  - [x] 导出对话框：选择格式、输出路径
- [x] 右键菜单
  - [x] 复制单元格值
  - [x] 复制整行
  - [x] 刷新当前表
  - [x] 导出选中行
  - [x] 查看行详情（弹窗展示完整字段）
- [x] 表搜索增强
  - [x] 模糊匹配搜索
  - [x] 可选正则匹配模式

### M10 — 国际化

- [x] 提取可翻译字符串（`pylupdate5`）
- [x] 编写 `translations/zh_CN.ts` 中文翻译
- [x] 编写 `translations/en_US.ts` 英文翻译
- [x] 编译 `.ts` → `.qm`（`lrelease`）
- [x] 集成 `QTranslator`，运行时加载翻译
- [x] 设置菜单 → 语言切换（中文 / English）
- [x] 语言偏好持久化

### M11 — SSH 隧道

- [x] 集成 `paramiko` 库
- [x] 登录窗口增加 SSH 隧道折叠面板
  - [x] SSH 主机 / 端口 / 用户名
  - [x] 认证方式：密码 / 密钥文件
  - [x] 密码输入框 / 密钥文件选择按钮
- [x] 实现隧道连接
  - [x] `paramiko.SSHClient` 建立 SSH 连接
  - [x] `transport.open_channel('direct-tcpip', ...)` 转发端口
  - [x] PyMySQL 通过隧道端口连接 MySQL
- [x] 隧道连接状态管理
  - [x] 连接中 / 已连接 / 断开 / 错误
  - [x] 自动重连机制
- [x] 验证：通过 SSH 隧道成功连接远程 MySQL

### M12 — 性能优化

- [x] 数据库连接池
  - [x] 实现连接复用，避免频繁创建/销毁
  - [x] 连接超时自动回收
  - [x] 空闲连接数上限控制
- [x] 查询结果缓存
  - [x] 相同 SQL 查询 5 秒内复用缓存结果
  - [x] 数据修改后自动失效缓存
- [x] 大数据量内存优化
  - [x] QTableView + 自定义 Model 替代 QTableWidget（虚拟行）
  - [x] 分页加载优化：仅加载可见区域数据
- [x] 性能基准测试脚本
  - [x] 测试用例：1万行 / 10万行 / 100万行
  - [x] 记录加载时间、内存占用
  - [x] 对比优化前后性能数据

---

## 第三阶段：打包发布

### M13 — PyInstaller 打包

- [ ] 编写 `build.spec` PyInstaller 配置文件
- [ ] 处理资源文件打包
  - [ ] QSS 样式文件
  - [ ] 翻译文件 `.qm`
  - [ ] 图标文件
- [ ] 测试打包后程序
  - [ ] 无 Python 环境的机器上运行
  - [ ] 所有功能正常（登录、浏览、编辑、导出）
  - [ ] 主题切换正常
- [ ] Windows 平台打包测试
- [ ] macOS 平台打包测试（如有条件）

### M14 — 安装程序

- [ ] Windows 安装包（NSIS 或 Inno Setup）
  - [ ] 安装向导界面
  - [ ] 自定义安装路径
  - [ ] 桌面快捷方式（可选）
  - [ ] 开始菜单快捷方式
  - [ ] 卸载程序
- [ ] 安装包测试：安装 → 运行 → 卸载 全流程

### M15 — 文档与发布

- [ ] 编写 `README.md`
  - [ ] 项目介绍与功能概述
  - [ ] 功能截图（登录界面、主界面、数据编辑）
  - [ ] 安装说明（pip 安装 + 打包版本）
  - [ ] 使用指南（快速上手）
  - [ ] 开发指南（环境搭建、运行测试）
  - [ ] 技术栈说明
  - [ ] 许可证信息
- [ ] GitHub Release v1.0.0
  - [ ] 上传安装包
  - [ ] 编写 Release Notes
  - [ ] 版本号 v1.0.0

---

## 附录：通用任务

以下任务贯穿整个开发过程，不属于特定里程碑：

- [ ] Git 版本管理：每个里程碑完成后提交
- [ ] 代码风格：遵循 PEP 8，使用 `black` 格式化
- [ ] 日志记录：使用 `logging` 模块，关键操作记录日志
- [ ] 异常处理：所有数据库操作捕获 `pymysql.Error` 并友好提示
- [ ] 类型注解：核心模块使用 type hints
- [ ] 文档注释：公共 API 编写 docstring
