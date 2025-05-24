import time
import os
import typing as tp
import uuid

from fastapi import UploadFile
from boto3 import client
from botocore.config import Config
from hashlib import md5

from .lib import load_document
from .typedefs import ContentResponse, UploadedFile, GetFile

GCS_BUCKET = "gs://quipubase-store"
GCS_PATH = "/blobs"

s3 = client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    endpoint_url=os.getenv("S3_ENDPOINT_URL"),
    config=Config(signature_version="s3v4")
)

class ContentService:
    async def run(self, file: UploadFile, format: tp.Literal["html", "text"]):
        start = time.perf_counter_ns()

        def generator():
            pivot = ""
            for chunk in load_document(file, format == "text"):
                if chunk == pivot or len(chunk) == 0:
                    continue
                pivot = chunk
                yield chunk

        chunks = list(generator())
        chunkedCount = len(chunks)
        created = (time.perf_counter_ns() - start) / 1e9
        return ContentResponse(
            chunks=chunks, created=created, chunkedCount=chunkedCount
        )
    
    async def put(self, file: UploadFile):
        start = time.perf_counter_ns()
        key = f"{md5(uuid.uuid4().bytes).hexdigest()}/{file.filename}"
        s3.put_object(
            Bucket=GCS_BUCKET,
            Key=key,
            Body=await file.read(),
            ContentType=file.content_type
        )
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": GCS_BUCKET, "Key": key},
            ExpiresIn=3600
        )
        created = (time.perf_counter_ns() - start) / 1e9
        return UploadedFile(
            url=url,
            created=created,
            key=key,
            size=file.size,
            content_type=file.content_type
        )
    
    def get(self, key: str):
        start = time.perf_counter_ns()
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": GCS_BUCKET, "Key": key},
            ExpiresIn=3600
        )
        created = (time.perf_counter_ns() - start) / 1e9
        return GetFile(
            url=url,
            created=created,
            key=key
        )
    
    def delete(self, key: str):
        start = time.perf_counter_ns()
        s3.delete_object(
            Bucket=GCS_BUCKET,
            Key=key
        )
        created = (time.perf_counter_ns() - start) / 1e9
        return {"code": 0, "created": created}
    
