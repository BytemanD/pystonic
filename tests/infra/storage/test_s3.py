import pytest

from pystonic.common.conf import CONF
from pystonic.infra.storage.s3 import S3Storage

pytestmark = pytest.mark.skipif(
    not CONF.s3.endpoint_url, reason="S3 endpoint url not configed, skip"
)


@pytest.fixture(scope="module", autouse=True)
def storage_driver():
    storage = S3Storage()
    yield storage
    storage.delete("test_dir/foo.txt")


def test_list_files(storage_driver):
    storage_driver.write("test_dir/foo.txt", "foo")
    assert len(storage_driver.list_files("test_dir")) == 1


def test_get_file(storage_driver):
    storage_driver.write("test_dir/foo.txt", "foo")
    file_path = storage_driver.get_file("test_dir/foo.txt")
    assert file_path.name == "foo.txt"
