import os
import time
import typing as tp
from pathlib import Path

import base64c as base64  # import base64c as base64 for binary content handling
from boto3 import client  # type:ignore
from botocore.config import Config  # type:ignore
from botocore.exceptions import \
    ClientError  # Import for specific error handling
from fastapi import UploadFile

from quipubase.lib.utils import asyncify

from .lib import load_document
from .typedefs import ChunkFile, FileType, GetOrCreateFile, TreeNode

# Ensure these environment variables are set correctly for GCS S3 compatibility
# e.g., S3_ENDPOINT_URL="https://storage.googleapis.com"
#       AWS_ACCESS_KEY_ID="GOOG..."
#       AWS_SECRET_ACCESS_KEY="..."
GCS_BUCKET = os.getenv(
    "GCS_BUCKET", "quipubase-store"
)  # Make bucket configurable via env var
GCS_PATH = (
    "/blobs"  # This path doesn't seem to be used directly by boto3 operations here.
)


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
        return ChunkFile(chunks=chunks, created=created, chunkedCount=chunkedCount)

    async def put(
        self, id: str, file: UploadFile, bucket: str = GCS_BUCKET
    ) -> GetOrCreateFile:
        start = time.perf_counter_ns()
        # Ensure key handles potential directories
        assert file.filename is not None
        key = os.path.join(GCS_PATH, id, file.filename)
        try:
            s3.put_object(
                Bucket=GCS_BUCKET,
                Key=key,
                Body=await file.read(),
                ContentType=file.content_type or "application/octet-stream",
            )
            url = self._get(key, bucket)
            created = (time.perf_counter_ns() - start) / 1e9
            return GetOrCreateFile(
                data=FileType(url=url, path=key),
                created=created,
            )
        except ClientError as e:
            print(f"Error putting object to S3/GCS: {e}")
            raise e  # Re-raise for API handler to catch
        except Exception as e:
            print(f"An unexpected error occurred during put: {e}")
            raise e

    def get(self, path: str, bucket: str = GCS_BUCKET) -> GetOrCreateFile:
        start = time.perf_counter_ns()
        try:
            key = os.path.join(GCS_PATH, path)
            url = self._get(key, bucket)
            created = (time.perf_counter_ns() - start) / 1e9
            return GetOrCreateFile(
                data=FileType(url=url, path=key),
                created=created,
            )
        except ClientError as e:
            print(f"Error generating presigned URL for get: {e}")
            raise e
        except Exception as e:
            print(f"An unexpected error occurred during get: {e}")
            raise e

    def _get(self, path: str, bucket: str = GCS_BUCKET) -> str:
        key = os.path.join(GCS_PATH, path)
        return s3.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=3600
        )

    def delete(self, path: str, bucket: str = GCS_BUCKET) -> dict[str, float]:
        start = time.perf_counter_ns()
        key = os.path.join(GCS_PATH, path)
        try:
            s3.delete_object(Bucket=bucket, Key=key)
            created = (time.perf_counter_ns() - start) / 1e9
            return {"code": 0, "created": created}
        except ClientError as e:
            print(f"Error deleting object from S3/GCS: {e}")
            raise e
        except Exception as e:
            print(f"An unexpected error occurred during delete: {e}")
            raise e

    @asyncify
    def _get_object_content(self, key: str, bucket_name: str = GCS_BUCKET):
        """Helper to fetch object content and encode if binary."""
        try:
            response = s3.get_object(Bucket=bucket_name, Key=key)
            body_bytes = response["Body"].read()
            try:
                # Attempt to decode as UTF-8
                return body_bytes.decode("utf-8")
            except UnicodeDecodeError:
                # If it's not valid UTF-8, assume binary and base64 encode
                return base64.b64encode(body_bytes).decode("utf-8")
        except ClientError as e:
            raise e
        except Exception as e:
            print(f"An unexpected error occurred getting content for {key}: {e}")
            raise e

    @asyncify
    def _paginate(self, prefix: str = "", bucket: str = GCS_BUCKET) -> tp.Any:
        """
        Generador que maneja la paginación de resultados de S3/GCS.
        Devuelve un diccionario con los resultados de cada página.
        """
        try:
            paginator = s3.get_paginator("list_objects_v2")
            return paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter="/")
        except ClientError as e:
            print(f"Error paginating objects: {e}")
            raise e
        except Exception as e:
            print(f"An unexpected error occurred during pagination: {e}")
            raise e

    async def scan(self, path: str = "", bucket: str = GCS_BUCKET):
        """
        Generador que recorre recursivamente un bucket GCS compatible con S3
        y produce TreeNode individuales para archivos y carpetas.
        """

        async def async_generator(prefix: str, bucket_: str):
            """
            Generador asíncrono que recorre un prefijo específico en el bucket
            y produce TreeNode para cada archivo y carpeta.
            """
            for page in await self._paginate(prefix=prefix, bucket=bucket_):
                # Carpetas
                for common_prefix in page.get("CommonPrefixes", []):
                    dir_prefix = common_prefix.get("Prefix")
                    if not dir_prefix:
                        continue
                    name = Path(dir_prefix.rstrip("/")).name

                    # Genera la carpeta como un nodo con contenido vacío
                    yield TreeNode(
                        type="folder",
                        name=name,
                        path=dir_prefix,
                        content=[
                            child
                            async for child in async_generator(dir_prefix, bucket_)
                        ],
                    )
                # Archivos
                for obj in page.get("Contents", []):
                    key = obj.get("Key")
                    if not key or key == prefix:
                        continue
                    name = Path(key).name
                    content = await self._get_object_content(
                        key=key, bucket_name=bucket_
                    )

                    yield TreeNode(type="file", name=name, path=key, content=content)

        async for node in async_generator(prefix=path, bucket_=bucket):
            yield node.model_dump_json(exclude_none=True)
