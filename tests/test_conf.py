import tempfile
from pathlib import Path

import toml

from pystonic.conf import BaseAppConfig
from pystonic.log import LogConfig


def test_conf_save():
    with tempfile.TemporaryDirectory() as tmpdir:
        toml_file = Path(tmpdir, "test.toml")
        BaseAppConfig.set(
            init_settings=BaseAppConfig(log=LogConfig(level="TRACE")),
            toml_files=[toml_file],
        )
        conf = BaseAppConfig.setup()
        conf.save()
        assert toml_file.exists()

        file_conf = toml.load(toml_file)
        assert file_conf.get("log").get("level") == "TRACE"


def test_conf_save_with_single_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        toml_file = Path(tmpdir, "test.toml")
        BaseAppConfig.set(
            init_settings={"log": {"level": "TRACE"}},
            toml_files=[toml_file],
        )
        conf = BaseAppConfig.setup()
        conf.save()
        assert toml_file.exists()

        file_conf = toml.load(toml_file)
        assert file_conf.get("log").get("level") == "TRACE"


def test_conf_save_with_chinese():
    with tempfile.TemporaryDirectory() as tmpdir:
        toml_file = Path(tmpdir, "test.toml")

        BaseAppConfig.set(
            {"log": {"level": "TRACE", "format": "中文"}},
            toml_files=toml_file,
        )
        conf = BaseAppConfig.setup()
        conf.save()

        assert toml_file.exists()
        file_conf = toml.load(toml_file)
        assert file_conf.get("log").get("level") == "TRACE"
        assert file_conf.get("log").get("format") == "中文"


def test_conf_save_skip():
    BaseAppConfig.set({"log": {"level": "TRACE"}})
    conf = BaseAppConfig.setup()
    conf.save()
