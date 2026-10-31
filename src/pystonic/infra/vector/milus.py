from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
from loguru import logger
from pymilvus import MilvusClient

from pystonic.common.conf import CONF, MilvusConfig
from pystonic.infra.vector.objects import VectorDocument


class ChromaOnnxEmbeddingFunction:
    def __init__(self):
        self.ef = ONNXMiniLM_L6_V2()

    def __call__(self, content: str):
        return self.ef([content])[0]


def metedata_to_filter(conditions: dict | None) -> str:
    if not conditions:
        return ""
    field: str = "metadata"
    parts = []
    for key, value in conditions.items():
        json_path = f'{field}["{key}"]'
        if isinstance(value, list):
            formatted = ", ".join(
                f'"{v}"' if isinstance(v, str) else str(v) for v in value
            )
            parts.append(f"{json_path} in [{formatted}]")
        elif isinstance(value, str):
            parts.append(f'{json_path} == "{value}"')
        else:
            parts.append(f"{json_path} == {value}")
    return " and ".join(parts)


class MilvusVector:
    """Milvus 向量库驱动

    依赖 chroma embedding functions,

    手动安装模型:
    ```
    wget https://chroma-onnx-models.s3.amazonaws.com/all-MiniLM-L6-v2/onnx.tar.gz
    cp onnx.tar.gz ~/.cache/chroma/onnx_models/all-MiniLM-L6-v2/onnx.tar.gz
    ```
    注意: collection 名称首个字符应为下划线、小写字母或大写字母
    """

    def __init__(self, config: MilvusConfig | None = None):
        config = config or CONF.milvus
        self.client = MilvusClient(
            uri=config.uri,
            token=config.token,
            user=config.user,
            password=config.password,
            db_name=config.db_name,
            timeout=config.timeout,
        )
        self.default_collection = config.default_collection
        self.consistency_level = config.consistency_level
        self.embedding_function = ChromaOnnxEmbeddingFunction()
        self._collections = set()

    def _makesure_collection(self, collection_name: str):
        if collection_name not in self._collections:
            logger.info("list collections")
            self._collections = set(self.client.list_collections())
        if collection_name not in self._collections:
            logger.info("create collection: {}", collection_name)
            self.client.create_collection(
                collection_name=collection_name,
                dimension=384,
                auto_id=True,
            )
            self._collections.add(collection_name)

    def add_document(
        self,
        content: str,
        collection: str | None = None,
        metadata: dict | None = None,
    ):
        collection = collection or self.default_collection
        self._makesure_collection(collection)
        metadata = metadata or {}
        data = {
            "vector": self.embedding_function(content),
            "text": content,
            "metadata": metadata,
        }
        self.client.insert(collection, data=[data])

    def list_documents(
        self,
        ids: list[int] | None = None,
        collection: str | None = None,
        metadata: dict | None = None,
    ):
        collection = collection or self.default_collection
        self._makesure_collection(collection)
        flt = metedata_to_filter(metadata)
        # pymilvus 3.x: filter 与 ids 不能同时传
        if metadata and ids:
            res = self.client.query(
                collection,
                filter=flt,
                output_fields=["text", "metadata"],
                limit=100,
                consistency_level=self.consistency_level,
            )
            res = [x for x in res if x.get("id") in ids]
        else:
            res = self.client.query(
                collection,
                filter=flt,
                output_fields=["text", "metadata"],
                ids=ids if not metadata else None,
                limit=100,
                consistency_level=self.consistency_level,
            )
        return [
            VectorDocument(
                id=x.get("id"), content=x.get("text"), metadata=x.get("metadata")
            )
            for x in res
        ]

    def delete_document(self, id: int | str, collection: str | None = None):
        self.client.delete(collection or self.default_collection, ids=[int(id)])

    def delete_collection(self, collection: str):
        self.client.drop_collection(collection)
        if collection in self._collections:
            self._collections.remove(collection)

    def retrieval(self, query: str, k: int = 3, collection: str | None = None):
        """召回文档

        score 越小越相似
        """
        collection = collection or self.default_collection
        query_vector = self.embedding_function(query)
        res = self.client.search(
            collection_name=collection,
            data=[query_vector],
            limit=k,
            output_fields=["text", "metadata"],
            search_params={"params": {}},
            consistency_level=self.consistency_level,
        )
        return [
            VectorDocument(
                id=x["id"],
                score=1 - x["distance"],
                content=(x.get("entity") or {}).get("text"),
                metadata=(x.get("entity") or {}).get("metadata") or {},
            )
            for x in res[0]
        ]
