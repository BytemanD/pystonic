import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from loguru import logger

from pystonic.common.conf import CONF, S3Config
from pystonic.infra.storage.objects import FilePath


class S3Storage:
    SCHEMA = "s3://"

    def __init__(self, config: S3Config | None = None):
        config = config or CONF.s3
        self.bucket = config.bucket
        creds = {
            "aws_access_key_id": config.access_key_id,
            "aws_secret_access_key": config.secret_access_key,
            "aws_session_token": config.session_token,
        }
        # 空值不显式传入，保留 botocore 默认凭据链（环境变量/实例角色）
        kwargs = {k: v for k, v in creds.items() if v}
        self.client = boto3.client(
            "s3",
            endpoint_url=config.endpoint_url,
            region_name=config.region,
            **kwargs,
        )

    def list_files(self, directory: str | None = None):
        files = []
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=directory or ""):
            items = page.get("Contents", [])
            files.extend(
                FilePath(
                    name=os.path.basename(x.get("Key")),
                    path=x.get("Key"),
                    size=x.get("Size"),
                    is_dir=False,
                    modify_time=x.get("LastModified"),
                )
                for x in items
            )
        return files

    def get_file(self, path: str):
        try:
            response = self.client.head_object(Bucket=self.bucket, Key=path)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in ("404", "NotFound", "NoSuchKey"):
                raise FileNotFoundError(f"file {path} not exists") from e
            raise
        return FilePath(
            name=os.path.basename(path),
            path=path,
            size=response.get("ContentLength"),
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
