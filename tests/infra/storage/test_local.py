import pytest

from pystonic.infra.storage.local import LocalStorage


@pytest.fixture(scope="module", autouse=True)
def storage_driver():
    storage = LocalStorage("/tmp")
    yield storage
    storage.delete("test_dir")


def test_list_files(storage_driver):
    storage_driver.write("test_dir/foo.txt", "foo")
    storage_driver.write("test_dir/bar.txt", b"bar")
    assert len(storage_driver.list_files("test_dir")) == 2
    assert storage_driver.read("test_dir/foo.txt").decode() == "foo"
    assert storage_driver.read("test_dir/bar.txt").decode() == "bar"
    assert storage_driver.get_file("test_dir/foo.txt") is not None
    assert storage_driver.get_file("test_dir/bar.txt") is not None
