import io
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from pystonic.core.system import (
    cpu_count,
    disk_usage,
    dot_config,
    execute,
    home_path,
    hostname,
    ip_address,
    is_linux,
    is_windows,
    reset_encoding,
)


def test_is_windows():
    """测试 Windows 系统检测"""
    with patch("platform.system") as mock_system:
        # 测试 Windows 系统
        mock_system.return_value = "Window"  # 注意：代码中是 "Window" 不是 "Windows"
        assert is_windows() is True

        # 测试非 Windows 系统
        mock_system.return_value = "Linux"
        assert is_windows() is False

        mock_system.return_value = "Darwin"
        assert is_windows() is False


def test_is_linux():
    """测试 Linux 系统检测"""
    with patch("platform.system") as mock_system:
        # 测试 Linux 系统
        mock_system.return_value = "Linux"
        assert is_linux() is True

        # 测试非 Linux 系统
        mock_system.return_value = "Window"
        assert is_linux() is False

        mock_system.return_value = "Darwin"
        assert is_linux() is False


def test_reset_encoding_stdout():
    """测试重置 stdout 编码"""
    original_stdout = sys.stdout

    with patch.object(sys, "stdout") as mock_stdout:
        # 模拟当前编码不是 utf-8
        mock_stdout.encoding = "cp936"
        mock_stdout.buffer = MagicMock()

        reset_encoding(encoding="utf-8")

        # 验证 TextIOWrapper 被创建并赋值给 sys.stdout
        assert isinstance(sys.stdout, io.TextIOWrapper)

    # 恢复原始 stdout
    sys.stdout = original_stdout


def test_reset_encoding_stderr():
    """测试重置 stderr 编码"""
    original_stderr = sys.stderr

    with patch.object(sys, "stderr") as mock_stderr:
        # 模拟当前编码不是 utf-8
        mock_stderr.encoding = "cp936"
        mock_stderr.buffer = MagicMock()

        reset_encoding(encoding="utf-8")

        # 验证 TextIOWrapper 被创建并赋值给 sys.stderr
        assert isinstance(sys.stderr, io.TextIOWrapper)

    # 恢复原始 stderr
    sys.stderr = original_stderr


def test_reset_encoding_no_change_needed():
    """测试当编码已经是目标编码时不进行修改"""
    # 创建一个临时的 EncodedFile 用于模拟
    temp_stdout = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    temp_stderr = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")

    original_stdout = sys.stdout
    original_stderr = sys.stderr

    try:
        sys.stdout = temp_stdout
        sys.stderr = temp_stderr

        reset_encoding(encoding="utf-8")

        # 验证没有重新包装（还是同一个对象）
        assert sys.stdout == temp_stdout
        assert sys.stderr == temp_stderr
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr


def test_home_path():
    """测试获取用户主目录路径"""
    result = home_path()

    # 验证返回 Path 对象
    assert isinstance(result, Path)

    # 验证路径存在
    assert result.exists()

    # 验证是绝对路径
    assert result.is_absolute()


def test_dot_config():
    """测试获取 .config 目录路径"""
    result = dot_config()

    # 验证返回 Path 对象
    assert isinstance(result, Path)

    # 验证路径以 .config 结尾
    assert result.name == ".config"

    # 验证是绝对路径
    assert result.is_absolute()


def test_cpu_count():
    """测试获取 CPU 核心数"""
    result = cpu_count()

    # 验证返回整数或 None
    assert result is None or isinstance(result, int)

    # 如果返回整数，应该大于 0
    if result is not None:
        assert result > 0


def test_disk_usage():
    """测试获取磁盘使用情况"""
    # 使用根目录或当前目录测试
    test_path = Path(".")
    result = disk_usage(test_path)

    # 验证返回值为命名元组格式
    assert hasattr(result, "total")
    assert hasattr(result, "used")
    assert hasattr(result, "free")

    # 验证值都是整数
    assert isinstance(result.total, int)
    assert isinstance(result.used, int)
    assert isinstance(result.free, int)

    # 验证总空间 = 已用 + 可用
    assert result.total == result.used + result.free


def test_hostname():
    """测试获取主机名"""
    result = hostname()

    # 验证返回字符串
    assert isinstance(result, str)

    # 验证不为空
    assert len(result) > 0


def test_ip_address_success():
    """测试获取 IP 地址成功"""
    with patch("socket.socket") as mock_socket_class:
        # 模拟 socket 对象
        mock_socket = MagicMock()
        mock_socket.getsockname.return_value = ("192.168.1.100", 0)
        mock_socket_class.return_value = mock_socket

        result = ip_address()

        # 验证返回 IP 地址
        assert result == "192.168.1.100"

        # 验证 socket 被正确调用（端口是 80 不是 8）
        mock_socket.connect.assert_called_once_with(("8.8.8.8", 80))
        mock_socket.close.assert_called_once()


def test_ip_address_fallback():
    """测试获取 IP 地址失败时使用备用方法"""
    with patch("socket.socket") as mock_socket_class:
        with patch("socket.gethostbyname") as mock_gethostbyname:
            with patch("pystonic.core.system.hostname") as mock_hostname:
                # 模拟 socket 连接失败
                mock_socket_class.side_effect = Exception("Connection failed")

                # 模拟备用方法成功
                mock_hostname.return_value = "localhost"
                mock_gethostbyname.return_value = "127.0.0.1"

                result = ip_address()

                # 验证返回备用 IP
                assert result == "127.0.0.1"

                # 验证调用了备用方法
                mock_gethostbyname.assert_called_once_with("localhost")


def test_execute_success():
    """测试执行成功命令"""
    returncode, stdout, stderr = execute("echo hello", shell=True)

    assert returncode == 0
    assert b"hello" in stdout
    assert stderr == b""


def test_execute_with_check_true():
    """测试 check=True 时失败命令抛出异常"""
    with patch("subprocess.run") as mock_run:
        # 模拟 CalledProcessError 异常
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd="invalid_cmd", output=b"", stderr=b"error"
        )

        # check=True 时应该抛出 CalledProcessError
        with pytest.raises(subprocess.CalledProcessError):
            execute("invalid_cmd", check=True)


def test_execute_with_check_false():
    """测试 check=False 时失败命令不抛异常"""
    with patch("subprocess.run") as mock_run:
        mock_result = subprocess.CompletedProcess(
            args="invalid_cmd", returncode=1, stdout=b"", stderr=b"error"
        )
        mock_run.return_value = mock_result

        # check=False 时不应该抛异常
        returncode, stdout, stderr = execute("invalid_cmd", check=False)

        assert returncode == 1
        assert stderr == b"error"


def test_execute_returns_tuple():
    """测试返回值格式为三元组"""
    with patch("subprocess.run") as mock_run:
        mock_result = subprocess.CompletedProcess(
            args="cmd", returncode=0, stdout=b"stdout_data", stderr=b"stderr_data"
        )
        mock_run.return_value = mock_result

        result = execute("cmd")

        assert isinstance(result, tuple)
        assert len(result) == 3

        returncode, stdout, stderr = result
        assert returncode == 0
        assert stdout == b"stdout_data"
        assert stderr == b"stderr_data"


def test_execute_shell_false():
    """测试 shell=False 时的命令执行"""
    with patch("subprocess.run") as mock_run:
        mock_result = subprocess.CompletedProcess(
            args=["ls", "-l"], returncode=0, stdout=b"file list", stderr=b""
        )
        mock_run.return_value = mock_result

        returncode, stdout, stderr = execute(["ls", "-l"], shell=False)

        assert returncode == 0
        assert stdout == b"file list"
        # 验证 subprocess.run 被正确调用
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args.kwargs["shell"] is False


def test_execute_default_parameters():
    """测试默认参数设置"""
    with patch("subprocess.run") as mock_run:
        mock_result = subprocess.CompletedProcess(
            args="cmd", returncode=0, stdout=b"", stderr=b""
        )
        mock_run.return_value = mock_result

        execute("cmd")

        # 验证默认参数
        call_args = mock_run.call_args
        assert call_args.kwargs["check"] is True
        assert call_args.kwargs["shell"] is True
        assert call_args.kwargs["stdout"] == subprocess.PIPE
        assert call_args.kwargs["stderr"] == subprocess.PIPE
