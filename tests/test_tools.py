import pytest

from app.tools import calculate_expression, check_leave_approval


def test_calculate_addition():
    result = calculate_expression("128.5 + 69.9 + 42.6")
    assert result == 241.0


def test_calculate_parentheses():
    result = calculate_expression("(100 + 20) * 2")
    assert result == 240.0


def test_calculate_division_by_zero():
    with pytest.raises(ValueError, match="不能除以0"):
        calculate_expression("10 / 0")


def test_calculate_rejects_python_code():
    with pytest.raises(ValueError):
        calculate_expression("__import__('os').system('dir')")


def test_one_day_leave():
    result = check_leave_approval(1)
    assert result["approvers"] == ["直属负责人"]


def test_three_day_leave():
    result = check_leave_approval(3)
    assert result["approvers"] == [
        "直属负责人",
        "部门负责人",
    ]