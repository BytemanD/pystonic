import subprocess
from unittest.mock import patch

from pystonic.core.system import execute


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
        import pytest

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
