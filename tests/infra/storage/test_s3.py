import pytest

from pystonic.infra.storage.s3 import S3Storage


@pytest.fixture(scope="module", autouse=True)
def storage_driver():
    storage = S3Storage()
    yield storage
    storage.delete("test_dir/foo.txt")


def test_list_files(storage_driver):
    storage_driver.write("test_dir/foo.txt", "foo")
    assert len(storage_driver.list_files("test_dir")) == 1
