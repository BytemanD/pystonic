import pytest
from loguru import logger

from pystonic.common.conf import CONF
from pystonic.infra.vector.milus import MilvusVector

pytestmark = pytest.mark.skipif(
    not CONF.milvus.uri, reason="milvus uri not configed, skip"
)

COLLECTION_NAME = "test"
DOC_ID1 = "11111111"
DOC_ID2 = "22222222"


@pytest.fixture(scope="module", autouse=True)
def vector_driver():
    driver = MilvusVector()
    yield driver
    logger.debug("delete colloection: {}", COLLECTION_NAME)
    driver.delete_collection(COLLECTION_NAME)


def test_list_documents(vector_driver):
    vector_driver.add_document(
        "hello, world", collection=COLLECTION_NAME, metadata={"doc_id": DOC_ID1}
    )
    items = vector_driver.list_documents(collection=COLLECTION_NAME)
    assert DOC_ID1 in [x.metadata.get("doc_id") for x in items]

    items = vector_driver.list_documents(
        collection=COLLECTION_NAME, metadata={"doc_id": DOC_ID1}
    )
    assert len(items) == 1
    assert items[0].content == "hello, world"

    vector_driver.delete_document(items[0].id, collection=COLLECTION_NAME)
    items = vector_driver.list_documents(
        collection=COLLECTION_NAME, metadata={"doc_id": DOC_ID1}
    )
    assert len(items) == 0


def test_retrieval(vector_driver):
    vector_driver.add_document(
        "test retrival", collection=COLLECTION_NAME, metadata={"doc_id": DOC_ID2}
    )
    docs = vector_driver.retrieval("test retrival", k=1, collection=COLLECTION_NAME)
    assert DOC_ID2 in [x.metadata.get("doc_id") for x in docs]
