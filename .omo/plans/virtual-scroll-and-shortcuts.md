# SQL-Viewer Lite 优化计划 Part 1: 虚拟滚动表格

## TL;DR

> **目标**: 将 QTableWidget 替换为 QTableView + QAbstractTableModel，支持百万行数据流畅显示
>
> **核心改动**:
> - 实现 DataTableModel（QAbstractTableModel 子类）
> - 实现虚拟滚动（只渲染可见区域）
> - 保持现有编辑、排序、筛选功能
> - 支持懒加载和分页
>
> **预计时间**: 2-3 小时
> **风险**: 中等（需要保持现有 API 兼容）

---

## Context

### 当前问题

1. **QTableWidget 限制**: 一次性加载所有数据到内存，大数据量（>10万行）会导致：
   - 启动缓慢
   - 内存占用过高
   - 滚动卡顿

2. **分页机制**: 当前使用 LIMIT/OFFSET 分页，每页最多 2000 行，无法满足大数据量场景

3. **用户体验**: 需要更流畅的数据浏览体验

### 解决方案

使用 QTableView + QAbstractTableModel 实现虚拟滚动：
- 只加载和渲染可见区域的数据
- 按需加载更多数据
- 支持无限滚动

---

## Work Objectives

### Core Objective
实现虚拟滚动表格，支持百万行数据流畅显示

### Concrete Deliverables
- `sql_viewer_lite/ui/data_table_model.py` - 自定义数据模型
- `sql_viewer_lite/ui/virtual_table_view.py` - 虚拟滚动表格视图
- 更新 `sql_viewer_lite/ui/table_view.py` 集成新组件

### Definition of Done
- [ ] 能加载 100 万行数据无卡顿
- [ ] 滚动流畅，无明显延迟
- [ ] 保持现有编辑、排序、筛选功能
- [ ] 内存占用 < 200MB（100 万行数据）

### Must Have
- 虚拟滚动（只渲染可见区域）
- 懒加载（按需加载数据）
- 保持现有 API 兼容
- 支持排序和筛选

### Must NOT Have (Guardrails)
- 不破坏现有编辑功能
- 不改变 UI 布局
- 不引入新的依赖

---

## Verification Strategy

### Test Decision
- **Automated tests**: YES (tests-after)
- **Framework**: pytest

### QA Policy
每个任务完成后运行测试并验证性能

---

## Execution Strategy

### Part 1: 虚拟滚动表格（优先）

```
Wave 1 (基础):
├── Task 1: 实现 DataTableModel
├── Task 2: 实现 VirtualTableView
└── Task 3: 集成到主窗口

Wave 2 (功能完善):
├── Task 4: 支持排序
├── Task 5: 支持筛选
└── Task 6: 支持编辑

Wave 3 (性能优化):
├── Task 7: 懒加载优化
└── Task 8: 性能测试
```

### Part 2: 键盘快捷键（次要）

```
Wave 4 (快捷键):
├── Task 9: 定义快捷键映射
├── Task 10: 实现快捷键处理
└── Task 11: 快捷键配置
```

---

## TODOs

### Part 1: 虚拟滚动表格

- [x] 1. 实现 DataTableModel

  **What to do**:
  - 创建 `sql_viewer_lite/ui/data_table_model.py`
  - 继承 QAbstractTableModel
  - 实现必要的方法：
    - `rowCount()` / `columnCount()`
    - `data()` / `setData()`
    - `headerData()`
    - `flags()` (支持编辑)
  - 实现数据缓存机制
  - 支持异步数据加载

  **Must NOT do**:
  - 不要一次性加载所有数据
  - 不要阻塞主线程

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocks**: Task 2, 3, 4, 5, 6

  **References**:
  - `sql_viewer_lite/ui/table_view.py:268-502` - 现有 DataTableView 实现
  - PyQt5 文档: QAbstractTableModel

  **Acceptance Criteria**:
  - [ ] DataTableModel 能加载 10 万行数据
  - [ ] 内存占用 < 50MB
  - [ ] 支持基本的 data() / setData() 操作

  **QA Scenarios**:
  ```
  Scenario: 加载大量数据
    Tool: Bash (pytest)
    Steps:
      1. 创建 DataTableModel 实例
      2. 加载 10 万行测试数据
      3. 验证 rowCount() 返回正确值
      4. 验证内存占用 < 50MB
    Expected: 加载成功，内存占用正常
  ```

  **Commit**: YES
  - Message: `feat(model): add DataTableModel for virtual scrolling`

---

- [x] 2. 实现 VirtualTableView

  **What to do**:
  - 创建 `sql_viewer_lite/ui/virtual_table_view.py`
  - 继承 QTableView
  - 集成 DataTableModel
  - 实现滚动条懒加载
  - 支持行选择和单元格选择

  **Must NOT do**:
  - 不要使用 QTableWidget
  - 不要一次性渲染所有行

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO (依赖 Task 1)
  - **Blocks**: Task 3, 4, 5, 6
  - **Blocked By**: Task 1

  **References**:
  - `sql_viewer_lite/ui/table_view.py:330-337` - 现有表格配置
  - PyQt5 文档: QTableView

  **Acceptance Criteria**:
  - [ ] VirtualTableView 能显示 DataTableModel 数据
  - [ ] 滚动流畅，无卡顿
  - [ ] 支持行选择

  **QA Scenarios**:
  ```
  Scenario: 滚动测试
    Tool: Playwright
    Steps:
      1. 加载 10 万行数据
      2. 快速滚动到底部
      3. 验证无卡顿
    Expected: 滚动流畅
  ```

  **Commit**: YES
  - Message: `feat(view): add VirtualTableView with lazy loading`

---

- [x] 3. 集成到主窗口

  **What to do**:
  - 修改 `sql_viewer_lite/ui/table_view.py`
  - 将 QTableWidget 替换为 VirtualTableView
  - 保持现有 API 兼容
  - 更新分页逻辑

  **Must NOT do**:
  - 不要改变公共 API
  - 不要删除现有功能

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO (依赖 Task 1, 2)
  - **Blocks**: Task 4, 5, 6, 7
  - **Blocked By**: Task 1, 2

  **References**:
  - `sql_viewer_lite/ui/table_view.py:268-502` - 现有实现
  - `main.py:456-485` - 创建表标签页

  **Acceptance Criteria**:
  - [ ] 主窗口能正常显示表格
  - [ ] 现有功能（分页、排序）正常工作

  **QA Scenarios**:
  ```
  Scenario: 集成测试
    Tool: Playwright
    Steps:
      1. 启动程序
      2. 连接数据库
      3. 打开一个表
      4. 验证数据正常显示
    Expected: 功能正常
  ```

  **Commit**: YES
  - Message: `refactor(ui): integrate VirtualTableView into main window`

---

- [x] 4. 支持排序

  **What to do**:
  - 在 DataTableModel 中实现排序
  - 支持点击列头排序
  - 支持多列排序（可选）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 5, 6)
  - **Blocked By**: Task 3

  **Acceptance Criteria**:
  - [ ] 点击列头能排序
  - [ ] 排序后数据正确

  **Commit**: YES
  - Message: `feat(sort): add column sorting to virtual table`

---

- [x] 5. 支持筛选

  **What to do**:
  - 保持现有筛选功能
  - 优化筛选性能（服务器端筛选）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 4, 6)
  - **Blocked By**: Task 3

  **Acceptance Criteria**:
  - [ ] 筛选功能正常
  - [ ] 筛选性能良好

  **Commit**: YES
  - Message: `feat(filter): optimize filtering for virtual table`

---

- [x] 6. 支持编辑

  **What to do**:
  - 保持现有编辑功能
  - 支持单元格编辑
  - 支持新增行、删除行

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 4, 5)
  - **Blocked By**: Task 3

  **Acceptance Criteria**:
  - [ ] 能编辑单元格
  - [ ] 能新增/删除行
  - [ ] 能提交更改

  **Commit**: YES
  - Message: `feat(edit): support cell editing in virtual table`

---

- [x] 7. 懒加载优化

  **What to do**:
  - 实现滚动时按需加载数据
  - 优化内存使用
  - 添加加载指示器

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: Task 3

  **Acceptance Criteria**:
  - [ ] 滚动时自动加载更多数据
  - [ ] 内存占用稳定

  **Commit**: YES
  - Message: `perf(lazy): implement lazy loading for large datasets`

---

- [x] 8. 性能测试

  **What to do**:
  - 编写性能测试脚本
  - 测试 1 万 / 10 万 / 100 万行数据
  - 记录加载时间、内存占用

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: Task 7

  **Acceptance Criteria**:
  - [ ] 100 万行数据加载 < 5 秒
  - [ ] 内存占用 < 200MB

  **Commit**: YES
  - Message: `test(perf): add performance benchmarks`

---

### Part 2: 键盘快捷键

- [x] 9. 定义快捷键映射

  **What to do**:
  - 创建 `sql_viewer_lite/utils/shortcuts.py`
  - 定义常用快捷键：
    - Ctrl+C: 复制
    - Ctrl+V: 粘贴
    - Ctrl+S: 保存
    - F5: 刷新
    - Ctrl+F: 搜索
    - Ctrl+N: 新建连接

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 1-8)
  - **Blocks**: Task 10, 11

  **Acceptance Criteria**:
  - [ ] 快捷键映射定义完整

  **Commit**: YES
  - Message: `feat(shortcuts): define keyboard shortcut mappings`

---

- [x] 10. 实现快捷键处理

  **What to do**:
  - 在主窗口中注册快捷键
  - 实现快捷键处理函数
  - 与现有菜单项关联

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: Task 9

  **Acceptance Criteria**:
  - [ ] 快捷键能正常触发
  - [ ] 与菜单项功能一致

  **Commit**: YES
  - Message: `feat(shortcuts): implement shortcut handlers`

---

- [x] 11. 快捷键配置

  **What to do**:
  - 支持自定义快捷键
  - 快捷键配置持久化
  - 设置界面（可选）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Blocked By**: Task 10

  **Acceptance Criteria**:
  - [ ] 快捷键配置能保存
  - [ ] 重启后配置生效

  **Commit**: YES
  - Message: `feat(shortcuts): support custom shortcut configuration`

---

## Final Verification Wave

- [x] F1. **功能完整性测试** - `unspecified-high`
  - 测试所有现有功能是否正常
  - 测试虚拟滚动是否正常
  - 测试快捷键是否正常

- [x] F2. **性能测试** - `unspecified-high`
  - 测试大数据量加载性能
  - 测试内存占用
  - 测试响应时间

- [x] F3. **用户体验测试** - `unspecified-high`
  - 测试操作流畅度
  - 测试快捷键响应

---

## Success Criteria

### Verification Commands
```bash
# 运行测试
python -m pytest sql_viewer_lite/tests/ -v

# 性能测试
python -m sql_viewer_lite.tests.perf_test

# 启动程序验证
python main.py
```

### Final Checklist
- [x] 虚拟滚动正常工作
- [x] 大数据量加载无卡顿
- [x] 现有功能完整保留
- [x] 快捷键正常工作
- [x] 所有测试通过
