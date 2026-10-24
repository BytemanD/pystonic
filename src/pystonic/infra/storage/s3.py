import os
from pathlib import Path

from loguru import logger

from pystonic.common.conf import CONF, S3Config
from pystonic.infra.storage.objects import FilePath

import boto3
from botocore.exceptions import ClientError
# from botocore.errorfactory import NoSuchKey


class S3Storage:
    def __init__(self, config: S3Config | None = None):
        config = config or CONF.s3
        self.bucket = config.bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=config.endpoint_url,
            region_name=config.region,
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
            aws_session_token=config.session_token,
        )

    def list_files(self, directory: str = None):
        items = self.client.list_objects_v2(Bucket=self.bucket)
        return [
            FilePath(
                name=os.path.basename(x.get("Key")),
                path=x.get("Key"),
                size=x.get("Size"),
                is_dir=False,
                modify_time=x.get("LastModified"),
            )
            for x in items.get("Contents", [])
        ]

    def get_file(self, path: str):
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=path)
        except ClientError as e:
            if type(e).__name__ == "NoSuchKey":
                raise FileNotFoundError(f"file {path} not exists")
            raise
        return FilePath(
            name=os.path.basename(response.get("Key")),
            path=response.get("Key"),
            size=response.get("Size"),
            modify_time=response.get("LastModified"),
            is_dir=False,
        )

    def write(self, path: str, content: bytes | str):
        logger.debug("put object: {}", path)
        self.client.put_object(
            Bucket=self.bucket,
            Key=path,
            Body=content if isinstance(content, bytes) else content.encode(),
            ContentType="application/octet-stream",
        )

    def read(self, path: str):
        logger.debug("read object: {}", path)
        response = self.client.get_object(Bucket=self.bucket, Key=path)
        return response["Body"].read()

    def delete(self, path: str):
        logger.debug("delete object: {}", path)
        self.client.delete_object(Bucket=self.bucket, Key=path)

    def upload_file(self, file_path: Path, key: str | None = None):
        logger.debug("upload file: {}", file_path)
        self.client.upload_file(
            Bucket=self.bucket,
            Filename=file_path.absolute().as_posix(),
            Key=key or file_path.name,
        )
