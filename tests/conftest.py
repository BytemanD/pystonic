import pytest

from pystonic import conf


@pytest.fixture(scope="session", autouse=True)
def config():
    return conf.BaseAppConfig.setup({"db": {"auto_create_tables": True}})
