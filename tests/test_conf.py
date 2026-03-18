import tempfile
from pathlib import Path

import toml

from pystonic.conf import BaseAppConfig


def test_conf_save():
    with tempfile.TemporaryDirectory() as tmpdir:
        toml_file = Path(tmpdir, "test.toml")
        conf = BaseAppConfig.setup({"log": {"level": "TRACE"}}, toml_files=[toml_file])
        conf.save()
        assert toml_file.exists()

        file_conf = toml.load(toml_file)
        assert file_conf.get("log").get("level") == "TRACE"


def test_conf_save_with_single_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        toml_file = Path(tmpdir, "test.toml")
        conf = BaseAppConfig.setup({"log": {"level": "TRACE"}}, toml_files=toml_file)
        conf.save()
        assert toml_file.exists()

        file_conf = toml.load(toml_file)
        assert file_conf.get("log").get("level") == "TRACE"


def test_conf_save_skip():
    conf = BaseAppConfig.setup({"log": {"level": "TRACE"}})
    conf.save()
