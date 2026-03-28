from unittest.mock import patch
from pystonic.core.input import get_input_number, select_items


def test_get_input_number_valid_input():
    """测试有效数字输入"""
    with patch("builtins.input", return_value="5"):
        result = get_input_number("请选择")
        assert result == 5


def test_get_input_number_with_quit():
    """测试退出功能"""
    quit_inputs = ["quit", "exit", "q"]
    for quit_str in quit_inputs:
        with patch("builtins.input", return_value=quit_str):
            result = get_input_number("请选择")
            assert result == 0


def test_get_input_number_with_min_max():
    """测试范围限制"""
    # 测试在范围内的输入
    with patch("builtins.input", return_value="5"):
        result = get_input_number("请选择", min_number=1, max_number=10)
        assert result == 5

    # 测试最小值边界
    with patch("builtins.input", return_value="1"):
        result = get_input_number("请选择", min_number=1, max_number=10)
        assert result == 1

    # 测试最大值边界
    with patch("builtins.input", return_value="10"):
        result = get_input_number("请选择", min_number=1, max_number=10)
        assert result == 10


def test_get_input_number_out_of_range():
    """测试超出范围的情况"""
    # 第一次输入超出范围，第二次输入有效
    with patch("builtins.input", side_effect=["100", "5"]):
        result = get_input_number("请选择", min_number=1, max_number=10)
        assert result == 5

    # 第一次输入小于最小值，第二次输入有效
    with patch("builtins.input", side_effect=["0", "5"]):
        result = get_input_number("请选择", min_number=1, max_number=10)
        assert result == 5


def test_get_input_number_invalid_then_valid():
    """测试无效输入后重新输入"""
    # 第一次输入非数字，第二次输入有效数字
    with patch("builtins.input", side_effect=["abc", "5"]):
        result = get_input_number("请选择")
        assert result == 5

    # 多次无效输入后输入有效数字
    with patch("builtins.input", side_effect=["xyz", "!!!", "10"]):
        result = get_input_number("请选择")
        assert result == 10


def test_get_input_number_whitespace_handling():
    """测试空白字符处理"""
    # 测试带空格的输入
    with patch("builtins.input", return_value="  5  "):
        result = get_input_number("请选择")
        assert result == 5

    # 测试带空格的退出命令
    with patch("builtins.input", return_value="  quit  "):
        result = get_input_number("请选择")
        assert result == 0


def test_get_input_number_no_bounds():
    """测试无边界限制"""
    # 没有 min_number 和 max_number 限制
    with patch("builtins.input", return_value="999999"):
        result = get_input_number("请选择")
        assert result == 999999

    with patch("builtins.input", return_value="-999999"):
        result = get_input_number("请选择")
        assert result == -999999


def test_get_input_number_only_min():
    """测试只有最小值限制"""
    with patch("builtins.input", return_value="100"):
        result = get_input_number("请选择", min_number=10)
        assert result == 100

    # 小于最小值会要求重新输入
    with patch("builtins.input", side_effect=["5", "15"]):
        result = get_input_number("请选择", min_number=10)
        assert result == 15


def test_get_input_number_only_max():
    """测试只有最大值限制"""
    with patch("builtins.input", return_value="5"):
        result = get_input_number("请选择", max_number=10)
        assert result == 5

    # 大于最大值会要求重新输入
    with patch("builtins.input", side_effect=["15", "8"]):
        result = get_input_number("请选择", max_number=10)
        assert result == 8


def test_get_input_number_custom_quit_strs():
    """测试自定义退出字符串"""
    with patch("builtins.input", return_value="stop"):
        result = get_input_number("请选择", quit_strs=["stop", "end"])
        assert result == 0

    # 默认的 quit 不再有效
    with patch("builtins.input", side_effect=["quit", "5"]):
        result = get_input_number("请选择", quit_strs=["stop"])
        assert result == 5  # quit 不是退出命令，会被当作无效输入，然后输入 5


def test_select_items_success():
    """测试选择列表项成功"""
    items = ["选项 A", "选项 B", "选项 C"]

    with patch("builtins.input", return_value="2"):
        with patch("pystonic.core.input.cprint") as mock_cprint:
            result = select_items(items)
            assert result == "选项 B"

            # 验证打印了提示
            mock_cprint.assert_called_once()
            assert "请选择:" in mock_cprint.call_args[0][0]


def test_select_items_default_return():
    """测试用户退出时返回默认值"""
    items = ["选项 A", "选项 B", "选项 C"]

    with patch("builtins.input", return_value="quit"):
        result = select_items(items, default="默认选项")
        assert result == "默认选项"


def test_select_items_custom_prompts():
    """测试自定义提示文本"""
    items = ["Item 1", "Item 2"]

    with patch("builtins.input", return_value="1"):
        with patch("pystonic.core.input.cprint") as mock_cprint:
            result = select_items(
                items, select_prompt="请做出选择", input_prompt="请输入你的选择"
            )
            assert result == "Item 1"

            # 验证使用了自定义提示
            mock_cprint.assert_called_once()
            assert "请做出选择" in mock_cprint.call_args[0][0]


def test_select_items_print_format():
    """测试列表打印格式"""
    items = ["A", "B", "C", "D", "E"]

    with patch("builtins.input", return_value="3"):
        with patch("builtins.print") as mock_print:
            result = select_items(items)
            assert result == "C"

            # 验证打印了所有选项 (5 个选项 + 1 个标题行 = 6 次调用)
            assert mock_print.call_count == len(items) + 1
            # 第一个选项应该是 "1. A"
            first_call = mock_print.call_args_list[1]  # 从第 2 次开始是选项
            assert "1." in str(first_call)
            assert "A" in str(first_call)


def test_select_items_empty_default():
    """测试空默认值"""
    items = ["选项 1"]

    with patch("builtins.input", return_value="q"):
        result = select_items(items, default=None)
        assert result is None
