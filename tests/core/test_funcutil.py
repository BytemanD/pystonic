import re
import time
from unittest.mock import patch
from pystonic.core.funcutil import timeit


@timeit
def _sample_add(x, y):
    """测试用函数 - 有返回值"""
    time.sleep(0.01)
    return x + y


def test_timeit_decorator():
    """验证 timeit 装饰器功能：返回值正确且记录执行时间日志"""
    with patch("pystonic.core.funcutil.logger.info") as mock_logger:
        # 记录实际开始时间
        actual_start = time.perf_counter()

        # 调用被装饰的函数
        result = _sample_add(3, 5)

        # 记录实际结束时间
        actual_end = time.perf_counter()
        actual_elapsed = actual_end - actual_start

        # 断言 1: 验证返回值正确
        assert result == 8

        # 断言 2: 验证日志被记录
        assert mock_logger.called

        # 断言 3: 验证日志内容格式
        log_message = mock_logger.call_args[0][0]
        assert "_sample_add" in log_message
        assert "took" in log_message
        assert "seconds" in log_message

        # 断言 4: 验证日志记录的时间与实际耗时一致（允许 ±0.005 秒误差）
        time_match = re.search(r"took (\d+\.\d+) seconds", log_message)
        assert time_match is not None, "日志中未找到时间信息"

        logged_elapsed = float(time_match.group(1))
        time_diff = abs(logged_elapsed - actual_elapsed)

        # 允许 0.005 秒的测量误差
        assert time_diff < 0.005, (
            f"日志时间 {logged_elapsed:.4f}s 与实际时间 {actual_elapsed:.4f}s 差异过大"
        )
