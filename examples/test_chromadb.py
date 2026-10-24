from pathlib import Path

import chromadb
import click
from loguru import logger

from pystonic.utils.fileutil import file_sha256

client = chromadb.PersistentClient("data/chromadb")
collection = client.get_or_create_collection(name="my_collection")


@click.group()
def root():
    pass


@root.command()
def list_docs():
    results = collection.get(include=["metadatas"])
    docs = []
    for index, doc_id in enumerate(results["ids"]):
        if not results["metadatas"] or not results["metadatas"][index]:
            continue
        docs.append(
            {
                "id": doc_id,
                "description": results["metadatas"][index].get("description"),
            }
        )
    print(docs)


@root.command("import")
@click.argument("file_path")
def import_markdown(file_path: str):
    logger.info("read markdown file ...")
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    doc_id = file_sha256(file_path)
    logger.info("document id: {}", doc_id)
    docs = collection.get(doc_id)
    if docs.get("ids"):
        raise click.ClickException("document already exists")

    logger.info("add document to  ...")
    collection.add(
        ids=[doc_id],
        documents=[text],
        metadatas=[
            {
                "file_name": Path(file_path).name,
            }
        ],
    )


@root.command("query")
@click.argument("text")
def query(text: str):
    results = collection.query(query_texts=[text], n_results=1)
    print(results)


if __name__ == "__main__":
    root()


# print(results)
# collection.update(
#     ids=["id1", "id2"],
#     embeddings=[[1.1, 2.3, 3.2], [4.5, 6.9, 4.4]],
#     metadatas=[{"chapter": "3", "verse": "16"}, {"chapter": "3", "verse": "5"}],
#     documents=["doc1", "doc2"],
# )
# collection.delete(ids=["id1", "id2"])
