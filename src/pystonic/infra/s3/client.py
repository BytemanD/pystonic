from datetime import datetime

import boto3
import httpx
from loguru import logger
from pydantic import BaseModel, Field

from pystonic.common.conf import CONF


class S3Object(BaseModel):
    key: str = Field(alias="Key")
    last_modified: datetime = Field(alias="LastModified")
    e_tag: str = Field(alias="ETag")
    size: int = Field(alias="Size")
    storage_class: str = Field(alias="StorageClass")


class S3Client:
    def __init__(
        self,
        endpoint_url: str,
        bucket: str,
        access_key_id: str,
        secret_access_key: str,
        session_token: str | None = None,
        region_name: str = "auto",
    ) -> None:
        self.s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url or CONF.s3.endpoint_url,
            region_name=region_name or CONF.s3.region_name,
            aws_access_key_id=access_key_id or CONF.s3.access_key_id,
            aws_secret_access_key=secret_access_key or CONF.s3.secret_access_key,
            aws_session_token=session_token or CONF.s3.session_token,
        )
        self.bucket = bucket

    def list_objects(self):
        items = self.s3.list_objects_v2(Bucket=self.bucket)
        return [S3Object.model_validate(x) for x in items.get("Contents", [])]


class UpstashS3Client(S3Client):
    """
    Usage:

    >>> s3_client = UpstashS3Client()
    >>> print(s3_client.list_objects())
    """

    def __init__(self):
        try:
            credentials = httpx.post(
                CONF.upstash.url,
                headers={"Authorization": f"Bearer {CONF.upstash.token}"},
                timeout=60,
            ).json()
        except httpx.HTTPError as e:
            raise RuntimeError(
                f"create upstash credential({CONF.upstash.url}) failed: {e}"
            )
        logger.debug("upstash credentials: {}", credentials)
        super().__init__(
            credentials["endpoint"],
            credentials["bucket"],
            access_key_id=credentials["accessKeyId"],
            secret_access_key=credentials["secretAccessKey"],
            session_token=credentials["sessionToken"],
        )
