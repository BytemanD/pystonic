import tempfile
from pathlib import Path

import pytest
import toml
from pydantic_core import ValidationError
from pytest_mock import MockerFixture

from pystonic import conf
from pystonic.conf import BaseAppConfig, FrozenModel
from pystonic.log import LogConfig


def test_conf_setup_with_init_settings(mocker: MockerFixture):
    mocker.patch("pystonic.log.setup_logger")

    conf.setup(init_settings={"log": {"level": "TRACE"}})
    new_config = BaseAppConfig.init({"log": {"level": "TRACE"}})

    assert new_config.log.level == "TRACE"


def test_conf_setup_with_one_toml_file(mocker: MockerFixture):
    mocker.patch("pystonic.log.setup_logger")

    with tempfile.TemporaryDirectory() as tmpdir:
        toml_file = Path(tmpdir, "test.toml")
        conf.setup(toml_file=toml_file)
        new_conf = BaseAppConfig.init(
            {"log": {"level": "TRACE", "format": "中文 message {}"}}
        )
        new_conf.save()
        assert toml_file.exists()

        assert new_conf.get_conf_file() == toml_file
        file_conf = toml.load(toml_file)
        assert file_conf.get("log").get("level") == "TRACE"
        assert file_conf.get("log").get("format") == "中文 message {}"


def test_conf_setup_with_multi_toml_files(mocker: MockerFixture):
    mocker.patch("pystonic.log.setup_logger")

    with tempfile.TemporaryDirectory() as tmpdir:
        toml_file = Path(tmpdir, "test.toml")
        conf.setup(
            init_settings={"log": {"level": "TRACE"}},
            toml_file=[toml_file],
        )
        new_config = BaseAppConfig.model_validate(
            BaseAppConfig(log=LogConfig(level="TRACE").model_dump(mode="json"))
        )
        new_config.save()
        assert toml_file.exists()

        file_conf = toml.load(toml_file)
        assert file_conf.get("log").get("level") == "TRACE"


def test_conf_init_without_setup():
    new_config = BaseAppConfig.init()
    new_config.save()
    assert new_config.log.level == "WARNING"


def test_conf_update_disable():
    new_conf = BaseAppConfig.init()

    with pytest.raises(ValidationError):
        new_conf.log = LogConfig(level="TRACE")

    with pytest.raises(ValidationError):
        new_conf.log.level = "TRACE"

    class FooConfig(FrozenModel):
        bar: str = ""

    class FooConfig(BaseAppConfig):
        foo: FooConfig = FooConfig()

    new_conf = FooConfig()
    with pytest.raises(ValidationError):
        new_conf.foo.bar = "bar"
