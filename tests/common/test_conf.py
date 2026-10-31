import pytest
from pydantic_core import ValidationError

from pystonic.common.conf import CONF, BaseAppConfig


def test_get_conf_files():
    assert len(CONF.get_conf_files()) >= 1


def test_conf_init_without_setup():
    new_config = BaseAppConfig.model_validate({})
    new_config.save()
    assert new_config.log.level == "WARNING"


def test_conf_update_disable():

    with pytest.raises(ValidationError):
        CONF.store = "/tmp"

    with pytest.raises(ValidationError):
        CONF.log.level = "TRACE"


def test_conf_shell_env_conflict_raise(monkeypatch):
    """shell 中与配置字段同名的裸变量（AGENT=1）应直接抛 ValidationError，不静默忽略"""
    monkeypatch.setenv("AGENT", "1")

    with pytest.raises(ValidationError):
        BaseAppConfig()


def test_conf_dotenv_invalid_value_raises(tmp_path, monkeypatch):
    """.env 里的值不合法必须报错，不允许静默忽略"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("LOG__LEVEL=12345\n", encoding="utf-8")

    with pytest.raises(ValidationError):
        BaseAppConfig()


def test_conf_init_source_priority_over_env(monkeypatch):
    """显式 init kwargs 优先于 shell 环境变量"""
    monkeypatch.setenv("S3__BUCKET", "env-bucket")

    assert BaseAppConfig().s3.bucket == "env-bucket"
