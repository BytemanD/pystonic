import os

import boto3
import requests

from pystonic.common.conf import CONF


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
            endpoint_url=endpoint_url,
            region_name=region_name,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            aws_session_token=session_token,
        )
        self.bucket = bucket

    @classmethod
    def from_upstash(cls, token: str | None = None):
        credentials = requests.post(
            "https://blob.upstash.io/v1/credentials",
            headers={"Authorization": f"Bearer {token or CONF.s3.upstash_token}"},
        ).json()
        return S3Client(
            credentials["endpoint"],
            credentials["bucket"],
            access_key_id=credentials["accessKeyId"],
            secret_access_key=credentials["secretAccessKey"],
            session_token=credentials["sessionToken"],
        )

    def list_objects(self):
        # s3.upload_file("image.png", credentials["bucket"], "image.png")
        listing = self.s3.list_objects_v2(Bucket=self.bucket)
        return [item["Key"] for item in listing.get("Contents", [])]
        # print([item["Key"] for item in listing.get("Contents", [])])



s3_client = S3Client.from_upstash(
    "AgAkADAMM2JiODY1MjktMmZkYS00ZmM1LTg4OTUtNzVmNWFiZTUyNGRhT1Rnd01UTTFNR1F0WkRGaVlpMDBOemt4TFdGbE5EZ3ROalZtWmpnek9Ea3pZVEJoYmU5MDk2MzA1MmRk"
)

s3_client.list_objects()
