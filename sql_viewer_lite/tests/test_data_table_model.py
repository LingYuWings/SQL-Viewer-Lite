"""
DataTableModel 单元测试
"""

import pytest
from PyQt5.QtCore import Qt, QModelIndex

from sql_viewer_lite.ui.data_table_model import DataTableModel


@pytest.fixture
def model():
    """创建 DataTableModel 实例"""
    return DataTableModel()


class TestDataTableModelBasic:
    """基础功能测试"""

    def test_initial_state(self, model):
        """测试初始状态"""
        assert model.rowCount() == 0
        assert model.columnCount() == 0
        assert model.get_total_rows() == 0

    def test_set_columns(self, model):
        """测试设置列"""
        columns = ["id", "name", "email"]
        model.set_columns(columns)
        
        assert model.columnCount() == len(columns)
        assert model._columns == columns

    def test_set_data(self, model):
        """测试设置数据"""
        columns = ["id", "name"]
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        
        model.set_columns(columns)
        model.set_data(data, total_rows=10)
        
        assert model.rowCount() == 10
        assert model.get_row_data(0) == {"id": 1, "name": "Alice"}
        assert model.get_row_data(1) == {"id": 2, "name": "Bob"}

    def test_clear(self, model):
        """测试清除数据"""
        model.set_columns(["id", "name"])
        model.set_data([{"id": 1, "name": "Alice"}], total_rows=1)
        
        model.clear()
        
        assert model.rowCount() == 0
        assert model.get_total_rows() == 0


class TestDataTableModelData:
    """数据访问测试"""

    def test_data_display_role(self, model):
        """测试 DisplayRole 数据"""
        model.set_columns(["id", "name"])
        model.set_data([{"id": 1, "name": "Alice"}], total_rows=1)
        
        index = model.index(0, 0)
        assert model.data(index, Qt.DisplayRole) == "1"
        
        index = model.index(0, 1)
        assert model.data(index, Qt.DisplayRole) == "Alice"

    def test_data_null_value(self, model):
        """测试 NULL 值显示"""
        model.set_columns(["id", "name"])
        model.set_data([{"id": 1, "name": None}], total_rows=1)
        
        index = model.index(0, 1)
        assert model.data(index, Qt.DisplayRole) == "NULL"
        assert model.data(index, Qt.EditRole) == ""

    def test_data_user_role(self, model):
        """测试 UserRole 原始值"""
        model.set_columns(["id", "name"])
        model.set_data([{"id": 1, "name": "Alice"}], total_rows=1)
        
        index = model.index(0, 0)
        assert model.data(index, Qt.UserRole) == 1

    def test_header_data(self, model):
        """测试表头数据"""
        model.set_columns(["id", "name"])
        model.set_data([{"id": 1, "name": "Alice"}], total_rows=1)
        
        # 水平表头
        assert model.headerData(0, Qt.Horizontal) == "id"
        assert model.headerData(1, Qt.Horizontal) == "name"
        
        # 垂直表头（行号）
        assert model.headerData(0, Qt.Vertical) == 1
        assert model.headerData(1, Qt.Vertical) == 2


class TestDataTableModelEdit:
    """编辑功能测试"""

    def test_set_data_edit(self, model):
        """测试编辑单元格"""
        model.set_columns(["id", "name"])
        model.set_data([{"id": 1, "name": "Alice"}], total_rows=1)
        
        index = model.index(0, 1)
        result = model.setData(index, "Bob", Qt.EditRole)
        
        assert result is True
        assert model.get_cell_value(0, "name") == "Bob"

    def test_set_data_null(self, model):
        """测试设置 NULL 值"""
        model.set_columns(["id", "name"])
        model.set_data([{"id": 1, "name": "Alice"}], total_rows=1)
        
        index = model.index(0, 1)
        model.setData(index, "NULL", Qt.EditRole)
        
        assert model.get_cell_value(0, "name") is None

    def test_edit_tracking(self, model):
        """测试编辑跟踪"""
        model.set_columns(["id", "name"])
        model.set_data([{"id": 1, "name": "Alice"}], total_rows=1)
        
        index = model.index(0, 1)
        model.setData(index, "Bob", Qt.EditRole)
        
        assert model.has_changes() is True
        assert len(model.get_modified_cells()) == 1

    def test_edit_unchanged(self, model):
        """测试编辑未改变值"""
        model.set_columns(["id", "name"])
        model.set_data([{"id": 1, "name": "Alice"}], total_rows=1)
        
        index = model.index(0, 1)
        model.setData(index, "Alice", Qt.EditRole)
        
        assert model.has_changes() is False

    def test_flags(self, model):
        """测试项目标志"""
        model.set_columns(["id", "name"])
        model.set_data([{"id": 1, "name": "Alice"}], total_rows=1)
        
        index = model.index(0, 0)
        flags = model.flags(index)
        
        assert flags & Qt.ItemIsEnabled
        assert flags & Qt.ItemIsSelectable
        assert flags & Qt.ItemIsEditable


class TestDataTableModelNewRow:
    """新增行测试"""

    def test_add_new_row(self, model):
        """测试添加新行"""
        model.set_columns(["id", "name"])
        model.set_data([{"id": 1, "name": "Alice"}], total_rows=1)
        
        new_row = model.add_new_row()
        
        assert new_row == 1
        assert model.rowCount() == 2
        assert new_row in model.get_new_rows()

    def test_new_row_empty(self, model):
        """测试新行数据为空"""
        model.set_columns(["id", "name"])
        model.set_data([], total_rows=0)
        
        new_row = model.add_new_row()
        
        assert model.get_row_data(new_row) == {"id": None, "name": None}


class TestDataTableModelDelete:
    """删除行测试"""

    def test_mark_deleted(self, model):
        """测试标记删除"""
        model.set_columns(["id", "name"])
        model.set_data([{"id": 1, "name": "Alice"}], total_rows=1)
        
        model.mark_deleted(0)
        
        assert 0 in model.get_deleted_rows()

    def test_unmark_deleted(self, model):
        """测试取消删除标记"""
        model.set_columns(["id", "name"])
        model.set_data([{"id": 1, "name": "Alice"}], total_rows=1)
        
        model.mark_deleted(0)
        model.unmark_deleted(0)
        
        assert 0 not in model.get_deleted_rows()

    def test_delete_new_row(self, model):
        """测试删除新增行（直接移除）"""
        model.set_columns(["id", "name"])
        model.set_data([], total_rows=0)
        
        new_row = model.add_new_row()
        model.mark_deleted(new_row)
        
        assert new_row not in model.get_new_rows()
        assert model.rowCount() == 0


class TestDataTableModelBackground:
    """背景色测试"""

    def test_background_modified(self, model):
        """测试修改单元格背景色"""
        model.set_columns(["id", "name"])
        model.set_data([{"id": 1, "name": "Alice"}], total_rows=1)
        
        index = model.index(0, 1)
        model.setData(index, "Bob", Qt.EditRole)
        
        bg = model.data(index, Qt.BackgroundRole)
        assert bg is not None
        assert bg.red() == 255
        assert bg.green() == 255
        assert bg.blue() == 200

    def test_background_new_row(self, model):
        """测试新增行背景色"""
        model.set_columns(["id", "name"])
        model.set_data([], total_rows=0)
        
        model.add_new_row()
        
        index = model.index(0, 0)
        bg = model.data(index, Qt.BackgroundRole)
        assert bg is not None
        assert bg.red() == 200
        assert bg.green() == 255
        assert bg.blue() == 200

    def test_background_deleted_row(self, model):
        """测试删除行背景色"""
        model.set_columns(["id", "name"])
        model.set_data([{"id": 1, "name": "Alice"}], total_rows=1)
        
        model.mark_deleted(0)
        
        index = model.index(0, 0)
        bg = model.data(index, Qt.BackgroundRole)
        assert bg is not None
        assert bg.red() == 255
        assert bg.green() == 200
        assert bg.blue() == 200


class TestDataTableModelClearChanges:
    """清除更改测试"""

    def test_clear_changes(self, model):
        """测试清除所有更改"""
        model.set_columns(["id", "name"])
        model.set_data([{"id": 1, "name": "Alice"}], total_rows=1)
        
        # 做一些修改
        model.setData(model.index(0, 1), "Bob", Qt.EditRole)
        model.add_new_row()
        model.mark_deleted(0)
        
        assert model.has_changes() is True
        
        model.clear_changes()
        
        assert model.has_changes() is False
        assert len(model.get_modified_cells()) == 0
        assert len(model.get_new_rows()) == 0
        assert len(model.get_deleted_rows()) == 0
