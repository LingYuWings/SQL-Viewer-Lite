# UI 改进计划：树状图图标 + 中键关标签 + 筛选布局修复

## TL;DR

> **目标**: 提升左侧栏层级辨识度、标签页操作效率、筛选控件可用性
>
> **核心改动**:
> 1. 树状图添加图标区分数据库/表节点
> 2. 鼠标中键点击标签页关闭
> 3. 筛选控件改为可滚动/折行布局，防止挤成一团
>
> **预计时间**: 1-2 小时
> **风险**: 低（UI 层面改动，不影响数据逻辑）

---

## Context

### 当前问题

1. **树状图无图标**: 左侧栏 `QTreeWidget` 只有纯文字，数据库和表的层级关系不直观
2. **标签页关闭不便**: 只能点 × 按钮关闭，无法用中键快速关闭
3. **筛选标签拥挤**: `FilterWidget` 使用 `QHBoxLayout` 水平排列所有列的筛选框，列数多时标签和输入框挤成一团

### 涉及文件

- `main.py` — DatabaseTreeWidget 图标 + 标签页中键关闭
- `sql_viewer_lite/ui/table_view.py` — FilterWidget 布局修复
- `sql_viewer_lite/ui/styles/main.qss` — 树状图图标样式

---

## Work Objectives

### Must Have
- 树状图数据库节点显示 🗄️ 图标，表节点显示 📋 图标
- 鼠标中键点击标签页可关闭
- 筛选控件在列数多时自动换行或可滚动

### Must NOT Have
- 不引入外部图标资源文件（使用 Unicode emoji 或 Qt 内置图标）
- 不改变筛选的 SQL 逻辑
- 不改变标签页的其他行为

---

## TODOs

- [ ] 1. 为树状图添加图标区分节点类型

  **What to do**:
  - 在 `DatabaseTreeWidget._init_ui()` 中创建 `QIcon`（使用 Qt 内置图标或 Unicode）
  - 数据库节点：使用 `QIcon.fromTheme("folder")` 或自定义颜色图标
  - 表节点：使用 `QIcon.fromTheme("table")` 或自定义颜色图标
  - 在 `load_databases()` 和 `_load_tables()` 中设置 `item.setIcon(0, icon)`

  **Must NOT do**:
  - 不创建外部 .png/.svg 文件
  - 不使用需要额外安装的图标库

  **References**:
  - `main.py:107-134` — `load_databases()` 创建数据库节点
  - `main.py:151-184` — `_load_tables()` 创建表节点
  - Qt 内置主题图标: `QIcon.fromTheme("folder")`, `QIcon.fromTheme("text-x-generic")`

  **Acceptance Criteria**:
  - [ ] 数据库节点显示文件夹图标
  - [ ] 表节点显示表格图标
  - [ ] 图标在深色/浅色主题下均可见

  **Commit**: YES
  - Message: `feat(ui): add icons to database tree nodes`

---

- [ ] 2. 鼠标中键关闭标签页

  **What to do**:
  - 在 `MainWindow._init_central_widget()` 中为 `QTabWidget` 安装事件过滤器
  - 重写 `MainWindow.eventFilter()` 捕获 `QEvent.MouseButtonPress`
  - 检查 `event.button() == Qt.MiddleButton` 且点击位置在标签栏内
  - 调用 `self._tab_widget.tabCloseRequested.emit(index)` 关闭标签

  **Must NOT do**:
  - 不影响标签页的其他鼠标行为
  - 不关闭欢迎页标签

  **References**:
  - `main.py:367-370` — QTabWidget 初始化
  - `main.py:521-526` — `_on_tab_close()` 关闭处理

  **Acceptance Criteria**:
  - [ ] 中键点击标签页可关闭
  - [ ] 欢迎页标签不可被中键关闭
  - [ ] 左键/右键行为不受影响

  **Commit**: YES
  - Message: `feat(ui): close tab on middle mouse button click`

---

- [ ] 3. 修复筛选控件布局拥挤问题

  **What to do**:
  - 将 `FilterWidget` 的 `QHBoxLayout` 改为 `QScrollArea` + `QFlowLayout`（或 `QGridLayout`）
  - 方案 A（推荐）：使用 `QScrollArea` 包裹水平布局，列数多时可横向滚动
  - 方案 B：使用 `QGridLayout` 按行排列，每行 3-4 个筛选框
  - 设置筛选输入框最小宽度，防止过度压缩
  - 添加工具提示显示完整列名

  **Must NOT do**:
  - 不改变筛选的 SQL 逻辑
  - 不删除筛选功能

  **References**:
  - `sql_viewer_lite/ui/table_view.py:141-169` — `FilterWidget._init_ui()`

  **Acceptance Criteria**:
  - [ ] 列数 ≤ 4 时正常水平排列
  - [ ] 列数 > 4 时可横向滚动或换行
  - [ ] 筛选框不被压缩到无法使用
  - [ ] 标签文字完整显示

  **Commit**: YES
  - Message: `fix(ui): improve filter widget layout for many columns`

---

## Final Verification Wave

- [ ] F1. **功能测试** — 启动程序，验证树图标、中键关闭、筛选布局
- [ ] F2. **回归测试** — 运行 `python -m pytest sql_viewer_lite/tests/ -v`

---

## Success Criteria

```bash
python -m pytest sql_viewer_lite/tests/ -v  # 所有测试通过
python main.py  # 手动验证 UI 改进
```
