from loguru import logger

from pystonic.common.conf import CONF, ChromaConfig
from langchain_chroma import Chroma
from langchain_core.documents import Document as RawDocument
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from pystonic.infra.vector.objects import VectorDocument


class ChromaVector:
    def __init__(self, config: ChromaConfig | None = None):
        config = config or CONF.chroma
        self.persist_directory = config.persist_directory
        self.host = config.host
        self.port = config.port
        self.default_collection = config.default_collection
        self.splite_thresold = config.splite_thresold

    def _get_vectorstore(self, collection: str | None = None):
        return Chroma(
            collection_name=collection or self.default_collection,
            persist_directory=self.persist_directory,
            host=self.host,
            port=self.port,
        )

    def add_document(
        self,
        content: str,
        collection: str = None,
        metadata: dict | None = None,
    ):
        metadata = metadata or {}
        logger.info("add document with metadata: {}", metadata)
        vectorstore = self._get_vectorstore(collection)
        if len(content) >= 1000:
            headers_to_split_on = [
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
            ]
            logger.info("split ...")
            md_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on, strip_headers=False
            )
            chunks = md_splitter.split_text(content)
            for chunk in chunks:
                chunk.metadata.update(metadata)

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
            )
            vectorstore.add_documents(text_splitter.split_documents(chunks))
        else:
            vectorstore.add_documents(
                [RawDocument(page_content=content, metadata=metadata)]
            )
        logger.success("add documents success")

    def list_documents(
        self, collection: str | None = None, metadata: dict | None = None
    ):
        vectorstore = self._get_vectorstore(collection)
        res = vectorstore.get(where=metadata)
        return [
            VectorDocument(
                id=id,
                content=res["documents"][index],
                metadata=res["metadatas"][index] or {},
            )
            for index, id in enumerate(res["ids"])
        ]

    def delete_document(self, id: str | int, collection: str | None = None):
        vectorstore = self._get_vectorstore(collection)

        logger.info("delete vector by id: {}", id)
        vectorstore.delete(ids=[str(id)])

    def delete_collection(self, collection: str):
        vectorstore = self._get_vectorstore(collection)
        vectorstore.delete_collection()

    def retrieval(self, query: str, k: int = 3, collection: str | None = None):
        """召回文档

        score 越小越相似
        """
        vectorstore = self._get_vectorstore(collection)
        logger.info("retrival({}): {}", k, query)
        results = vectorstore.similarity_search_with_score(query, k=k)
        return [
            VectorDocument(
                id=doc.id or "",
                score=score,
                content=doc.page_content,
                metadata=doc.metadata or {},
            )
            for doc, score in results
        ]
