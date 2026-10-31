import os

import pytest


@pytest.fixture(autouse=True)
def _clean_conf_name_env_vars(monkeypatch):
    """每个测试再清理一次（防止测试自身设置了冲突变量）"""
    from pystonic.common.conf import BaseAppConfig

    os.environ.clear()
    for field in BaseAppConfig.model_fields:
        monkeypatch.delenv(field, raising=False)
        monkeypatch.delenv(field.upper(), raising=False)


@pytest.fixture(scope="session", autouse=True)
def config():
    os.environ["AGENT__CHECKPOINT_CONNECTION"] = "sqlite:///:memory:"
