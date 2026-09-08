import pytest

from pystonic.common import conf


@pytest.fixture(scope="session", autouse=True)
def config():
    return conf.BaseAppConfig.model_validate({})
