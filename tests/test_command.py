import subprocess

from pystonic.utils import command


def test_execute():
    status, _ = command.execute("hostname")
    assert status == 0


def test_execute_failed():
    import pytest

    with pytest.raises(subprocess.CalledProcessError):
        command.execute("hostname-xxxxx")
