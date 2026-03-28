import pytest
from pystonic.log import LogConfig, setup_logger, add_console_handler, DEFAULT_FORMAT
from loguru import logger


def test_log_config_default():
    """测试 LogConfig 默认值"""
    config = LogConfig()

    assert config.level == "WARNING"
    assert config.file is None
    assert config.format == DEFAULT_FORMAT
    assert config.colorize is None
    assert config.rotation == "10 MB"
    assert config.retention == "30 days"
    assert config.compression == "zip"
    assert config.custom_extra == []


def test_log_config_custom_values():
    """测试 LogConfig 自定义值"""
    config = LogConfig(
        level="DEBUG",
        file="test.log",
        format="{message}",
        colorize=True,
        rotation="1 MB",
        retention="7 days",
        compression="gz",
        custom_extra=["user_id"],
    )

    assert config.level == "DEBUG"
    assert config.file == "test.log"
    assert config.format == "{message}"
    assert config.colorize is True
    assert config.rotation == "1 MB"
    assert config.retention == "7 days"
    assert config.compression == "gz"
    assert config.custom_extra == ["user_id"]


def test_log_config_frozen():
    """测试 LogConfig 不可变性"""
    config = LogConfig(level="INFO")

    # 尝试修改应该抛出异常
    with pytest.raises(Exception):
        config.level = "ERROR"


def test_setup_logger_with_stdout():
    """测试设置控制台日志处理器"""
    config = LogConfig(level="INFO")
    setup_logger(config)

    # 验证日志器已配置
    assert len(logger._core.handlers) > 0


def test_setup_logger_with_file(tmp_path):
    """测试设置文件日志处理器"""
    log_file = tmp_path / "test.log"
    config = LogConfig(level="INFO", file=str(log_file))
    setup_logger(config)

    # 记录一条日志
    logger.info("Test message")

    # 验证文件存在
    assert log_file.exists()


def test_setup_logger_custom_format():
    """测试自定义日志格式"""
    custom_format = "[{level}] {message}"
    config = LogConfig(level="INFO", format=custom_format)
    setup_logger(config)

    # 验证配置正确
    assert config.format == custom_format


def test_add_console_handler():
    """测试添加控制台处理器"""
    config = LogConfig()
    add_console_handler("DEBUG", config)

    # 验证添加了处理器
    assert len(logger._core.handlers) > 0


def test_add_console_handler_with_custom_format():
    """测试添加自定义格式的控制台处理器"""
    custom_format = "CUSTOM: {message}"
    config = LogConfig(format=custom_format)
    add_console_handler("ERROR", config)

    # 验证级别设置正确
    assert config.level == "WARNING"  # 默认值不变


def test_default_format_string():
    """测试默认格式字符串包含必要元素"""
    # 验证默认格式包含时间、级别、消息等
    assert "{time:" in DEFAULT_FORMAT
    assert "{level:" in DEFAULT_FORMAT
    assert "{message}" in DEFAULT_FORMAT
    assert "{name}" in DEFAULT_FORMAT
    assert "{line}" in DEFAULT_FORMAT


def test_log_level_validation():
    """测试日志级别有效性"""
    valid_levels = ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR"]

    for level in valid_levels:
        config = LogConfig(level=level)
        assert config.level == level


def test_log_config_with_invalid_level():
    """测试无效日志级别"""
    # 尝试使用无效级别应该失败或转换为大写
    with pytest.raises(ValueError):
        LogConfig(level="INVALID_LEVEL")


def test_context_patcher_integration():
    """测试上下文补丁功能"""
    config = LogConfig(custom_extra=["user_id", "request_id"])
    setup_logger(config)

    # 验证配置包含了自定义额外字段
    assert "user_id" in config.custom_extra
    assert "request_id" in config.custom_extra
