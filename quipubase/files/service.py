import time
import os
import typing as tp
import uuid
import base64 # Import base64 for binary content handling

from fastapi import UploadFile
from boto3 import client # type:ignore
from botocore.exceptions import ClientError # Import for specific error handling
from botocore.config import Config # type:ignore
from hashlib import md5
from pathlib import Path


from .lib import load_document
from .typedefs import ChunkFile, GetOrCreateFile, TreeNode, FileType
from ..utils.utils import asyncify

# Ensure these environment variables are set correctly for GCS S3 compatibility
# e.g., S3_ENDPOINT_URL="https://storage.googleapis.com"
#       AWS_ACCESS_KEY_ID="GOOG..."
#       AWS_SECRET_ACCESS_KEY="..."
GCS_BUCKET = os.getenv("GCS_BUCKET", "quipubase-store") # Make bucket configurable via env var
GCS_PATH = "/blobs" # This path doesn't seem to be used directly by boto3 operations here.

# Initialize the S3 client (configured for GCS)
s3 = client(
    "s3",
    endpoint_url=os.getenv("S3_ENDPOINT_URL"),
    # It's good practice to explicitly pass credentials if not relying solely on env vars
    # aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    # aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3"),
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
        return ChunkFile(
            chunks=chunks, created=created, chunkedCount=chunkedCount
        )

    async def put(self, file: UploadFile, bucket:str=GCS_BUCKET) -> GetOrCreateFile:
        start = time.perf_counter_ns()
        # Ensure key handles potential directories
        key = f"{md5(uuid.uuid4().bytes).hexdigest()}/{file.filename}"
        try:
            s3.put_object(
                Bucket=GCS_BUCKET,
                Key=key,
                Body=await file.read(),
                ContentType=file.content_type or "application/octet-stream",
            )
            url = await self._get(key, bucket)
            created = (time.perf_counter_ns() - start) / 1e9
            return GetOrCreateFile(
                data=FileType(
                    url=url,
                    path=key
                ),
                created=created,
            )
        except ClientError as e:
            print(f"Error putting object to S3/GCS: {e}")
            raise e # Re-raise for API handler to catch
        except Exception as e:
            print(f"An unexpected error occurred during put: {e}")
            raise e

    async def get(self, key: str, bucket: str = GCS_BUCKET) -> GetOrCreateFile:
        start = time.perf_counter_ns()
        try:
            url = await self._get(key, bucket)
            created = (time.perf_counter_ns() - start) / 1e9
            return GetOrCreateFile(
                data=FileType(
                    url=url,
                    path=key
                ),
                created=created,
            )
        except ClientError as e:
            print(f"Error generating presigned URL for get: {e}")
            raise e
        except Exception as e:
            print(f"An unexpected error occurred during get: {e}")
            raise e

    @asyncify
    def _get(self, key:str, bucket:str = GCS_BUCKET)->str:
        return s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=3600
            )

    @asyncify
    def delete(self, key: str, bucket: str = GCS_BUCKET) -> dict[str, float]:
        start = time.perf_counter_ns()
        try:
            s3.delete_object(
                Bucket=bucket,
                Key=key
            )
            created = (time.perf_counter_ns() - start) / 1e9
            return {"code": 0, "created": created}
        except ClientError as e:
            print(f"Error deleting object from S3/GCS: {e}")
            raise e
        except Exception as e:
            print(f"An unexpected error occurred during delete: {e}")
            raise e


    def _get_object_content(self, bucket_name: str, key: str) -> str:
        """Helper to fetch object content and encode if binary."""
        try:
            response = s3.get_object(Bucket=bucket_name, Key=key)
            body_bytes = response['Body'].read()
            try:
                # Attempt to decode as UTF-8
                return body_bytes.decode('utf-8')
            except UnicodeDecodeError:
                # If it's not valid UTF-8, assume binary and base64 encode
                return base64.b64encode(body_bytes).decode('utf-8')
        except ClientError as e:
            raise e
        except Exception as e:
            print(f"An unexpected error occurred getting content for {key}: {e}")
            raise e


    def scan(self, prefix: str = "", bucket: str = GCS_BUCKET) -> tp.Generator[TreeNode, None, None]:
        """
        Generador que recorre recursivamente un bucket GCS compatible con S3
        y produce TreeNode individuales para archivos y carpetas.
        """
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter='/')

        for page in pages:
            # Carpetas
            for common_prefix in page.get('CommonPrefixes', []):
                dir_prefix = common_prefix.get('Prefix')
                if not dir_prefix:
                    continue
                name = Path(dir_prefix.rstrip('/')).name

                # Genera la carpeta como un nodo con contenido vacío
                yield TreeNode(
                    type="folder",
                    name=name,
                    path=dir_prefix,
                    content=[]
                )

                # Recursión perezosa: yield desde subscan
                yield from self.scan(dir_prefix, bucket)

            # Archivos
            for obj in page.get('Contents', []):
                key = obj.get('Key')
                if not key or key == prefix:
                    continue
                name = Path(key).name
                content = self._get_object_content(bucket, key)

                yield TreeNode(
                    type="file",
                    name=name,
                    path=key,
                    content=content
                )