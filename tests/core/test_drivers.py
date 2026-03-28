import pytest
import tempfile
from unittest.mock import patch, MagicMock
from pystonic.shell.drivers import (
    Cmd,
    ExecuteDriver,
    PowershellDriver,
    CmdDriver,
    BashDriver,
)


class TestCmdEnum:
    """测试 Cmd 枚举类"""

    def test_cmd_values(self):
        """测试命令枚举值"""
        assert Cmd.POWERSHELL.value == "powershell"
        assert Cmd.CALL.value == "call"
        assert Cmd.BASH.value == "bash"

    def test_cmd_type(self):
        """测试命令类型"""
        assert isinstance(Cmd.POWERSHELL, str)
        assert isinstance(Cmd.CALL, str)
        assert isinstance(Cmd.BASH, str)


class TestPowershellDriver:
    """测试 PowerShell 驱动"""

    def test_powershell_driver_init(self):
        """测试 PowerShell 驱动初始化"""
        driver = PowershellDriver()
        assert driver.platform is not None
        assert driver.version is not None
        assert driver.architecture is not None
        assert driver.SCRIPT_SUFFIX == ".ps1"

    def test_powershell_oneline_command(self):
        """测试 PowerShell 单行命令"""
        driver = PowershellDriver()
        result = driver.oneline_command("Get-Process")
        assert result == 'powershell -Command "Get-Process"'

    def test_powershell_oneline_command_with_special_chars(self):
        """测试 PowerShell 单行命令包含特殊字符"""
        driver = PowershellDriver()
        result = driver.oneline_command("Write-Host 'Hello World'")
        assert "powershell -Command \"Write-Host 'Hello World'\"" in result

    def test_powershell_file_command(self):
        """测试 PowerShell 文件命令"""
        driver = PowershellDriver()
        result = driver.file_command("script.ps1")
        assert result == 'powershell -File "script.ps1"'

    def test_powershell_execute(self):
        """测试 PowerShell 执行代码块"""
        driver = PowershellDriver()

        with patch("os.system") as mock_system:
            with patch("os.remove") as mock_remove:
                with patch.object(tempfile, "NamedTemporaryFile") as mock_tempfile:
                    # 模拟临时文件
                    mock_file = MagicMock()
                    mock_file.name = "test.ps1"
                    mock_file.__enter__ = MagicMock(return_value=mock_file)
                    mock_file.__exit__ = MagicMock(return_value=None)
                    mock_tempfile.return_value = mock_file

                    # 执行代码块
                    driver.execute("Write-Host 'Test'")

                    # 验证调用了 os.system
                    assert mock_system.called
                    # 验证清理了临时文件
                    assert mock_remove.called


class TestCmdDriver:
    """测试 CMD 命令驱动"""

    def test_cmd_driver_init(self):
        """测试 CMD 驱动初始化"""
        driver = CmdDriver()
        assert driver.platform is not None
        assert driver.SCRIPT_SUFFIX == ".bat"

    def test_cmd_oneline_command(self):
        """测试 CMD 单行命令"""
        driver = CmdDriver()
        result = driver.oneline_command("dir")
        assert result == 'call "dir"'

    def test_cmd_file_command(self):
        """测试 CMD 文件命令"""
        driver = CmdDriver()
        result = driver.file_command("script.bat")
        assert result == 'call "script.bat"'

    def test_cmd_execute(self):
        """测试 CMD 执行代码块"""
        driver = CmdDriver()

        with patch("os.system") as mock_system:
            with patch("os.remove") as mock_remove:
                with patch.object(tempfile, "NamedTemporaryFile") as mock_tempfile:
                    mock_file = MagicMock()
                    mock_file.name = "test.bat"
                    mock_file.__enter__ = MagicMock(return_value=mock_file)
                    mock_file.__exit__ = MagicMock(return_value=None)
                    mock_tempfile.return_value = mock_file

                    driver.execute("echo Hello")

                    assert mock_system.called
                    assert mock_remove.called


class TestBashDriver:
    """测试 Bash 驱动"""

    def test_bash_driver_init(self):
        """测试 Bash 驱动初始化"""
        driver = BashDriver()
        assert driver.cmd == "bash"
        assert driver.SCRIPT_SUFFIX == ""

    def test_bash_oneline_command(self):
        """测试 Bash 单行命令"""
        driver = BashDriver()
        result = driver.oneline_command("ls -la")
        assert result == 'bash -c "ls -la"'

    def test_bash_oneline_command_with_params(self):
        """测试 Bash 单行命令带参数"""
        driver = BashDriver()
        result = driver.oneline_command("grep 'pattern' file.txt")
        assert "bash -c \"grep 'pattern' file.txt\"" in result

    def test_bash_file_command(self):
        """测试 Bash 文件命令"""
        driver = BashDriver()
        result = driver.file_command("/path/to/script.sh")
        assert result == 'bash "/path/to/script.sh"'

    def test_bash_execute(self):
        """测试 Bash 执行代码块"""
        driver = BashDriver()

        with patch("os.system") as mock_system:
            with patch("os.remove") as mock_remove:
                with patch.object(tempfile, "NamedTemporaryFile") as mock_tempfile:
                    mock_file = MagicMock()
                    mock_file.name = "test.sh"
                    mock_file.__enter__ = MagicMock(return_value=mock_file)
                    mock_file.__exit__ = MagicMock(return_value=None)
                    mock_tempfile.return_value = mock_file

                    driver.execute("echo 'Test'")

                    assert mock_system.called
                    assert mock_remove.called


class TestExecuteDriverBase:
    """测试基础执行驱动"""

    def test_execute_driver_is_abstract(self):
        """测试 ExecuteDriver 是抽象类"""
        with pytest.raises(TypeError):
            ExecuteDriver()  # type: ignore[abstract]

    def test_execute_driver_subclass_must_implement_abstract(self):
        """测试子类必须实现抽象方法"""

        class IncompleteDriver(ExecuteDriver):
            pass

        with pytest.raises(TypeError):
            IncompleteDriver()  # type: ignore[abstract]


class TestDriverPlatformCompatibility:
    """测试驱动平台兼容性"""

    def test_all_drivers_handle_platform_info(self):
        """测试所有驱动都能获取平台信息"""
        # PowershellDriver 和 CmdDriver 有 platform 属性，BashDriver 没有
        drivers_with_platform = [PowershellDriver(), CmdDriver()]

        for driver in drivers_with_platform:
            assert driver.platform is not None
            assert isinstance(driver.platform, str)

        # BashDriver 使用自定义的 cmd 属性
        bash_driver = BashDriver()
        assert bash_driver.cmd == "bash"

    def test_drivers_have_required_methods(self):
        """测试所有驱动都有必需的方法"""
        drivers = [PowershellDriver(), CmdDriver(), BashDriver()]

        for driver in drivers:
            assert hasattr(driver, "oneline_command")
            assert hasattr(driver, "file_command")
            assert hasattr(driver, "execute")
            assert callable(getattr(driver, "oneline_command"))
            assert callable(getattr(driver, "file_command"))
            assert callable(getattr(driver, "execute"))
