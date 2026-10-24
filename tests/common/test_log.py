import pytest
from loguru import logger
from pydantic import ValidationError

from pystonic.common.conf import DEFAULT_FORMAT, LogConfig
from pystonic.common.log import setup_logger


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

    with pytest.raises(ValidationError):
        config.level = "ERROR"


def test_setup_logger_with_stdout():
    """测试设置控制台日志处理器"""
    config = LogConfig(level="INFO")
    setup_logger(config)

    # 验证日志器已配置
    assert len(logger._core.handlers) > 0


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
