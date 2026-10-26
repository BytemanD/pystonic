import pytest

from pystonic.infra.vector.chroma import ChromaVector

COLLECTION_NAME = "test"
DOC_ID1 = "11111111"
DOC_ID2 = "22222222"
DOC_ID3 = "33333333"


@pytest.fixture(scope="module", autouse=True)
def vector_driver():
    driver = ChromaVector()
    yield driver
    driver.delete_collection(COLLECTION_NAME)


def test_list_documents(vector_driver: ChromaVector):
    vector_driver.add_document(
        "hello, world", collection="test", metadata={"doc_id": DOC_ID1}
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


def test_retrieval(vector_driver: ChromaVector):
    vector_driver.add_document(
        "test retrival", collection="test", metadata={"doc_id": DOC_ID2}
    )
    docs = vector_driver.retrieval("test retrival", k=1, collection=COLLECTION_NAME)
    assert len(docs) == 1
    assert docs[0].score <= 0.1

    vector_driver.add_document(
        "long content," * 1000, collection="test", metadata={"doc_id": DOC_ID3}
    )
    docs = vector_driver.retrieval("long content", k=1, collection=COLLECTION_NAME)
    assert len(docs) == 1
    assert docs[0].score <= 1
