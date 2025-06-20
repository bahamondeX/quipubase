import os
import random
import time
from hashlib import md5

import base64c as base64  # type: ignore
from boto3 import client  # type:ignore
from botocore.config import Config  # Import boto3
from dotenv import load_dotenv
from google.genai import Client, types
from openai.types.image_generate_params import ImageGenerateParams

load_dotenv()

GCS_BUCKET = os.getenv(
    "GCS_BUCKET", "quipubase-store"
)  # Make bucket configurable via env var

GCS_PATH = (
    "images"  # This path doesn't seem to be used directly by boto3 operations here.
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


class ImageGenerationService:
    """
    Service for generating images using Google's Imagen model.
    """

    def generate(self, request: ImageGenerateParams):
        client = Client(api_key=os.environ.get("OPENAI_API_KEY"))
        result = client.models.generate_images(
            model="models/imagen-3.0-generate-002",
            prompt=request["prompt"],
            config={
                "number_of_images": request.get("n") or 1,
                "output_mime_type": "image/png",
                "person_generation": types.PersonGeneration.ALLOW_ADULT,
                "aspect_ratio": "16:9",
            },
        )

        if not result.generated_images:
            raise ValueError(
                "No images generated. Please check your prompt and parameters."
            )

        for generated_image in result.generated_images:
            yield generated_image

    def generator(self, request: ImageGenerateParams):
        for x in self.generate(request):
            img = x.image
            if not img:
                continue
            print(img.mime_type)
            assert img.image_bytes
            assert img.mime_type
            if request.get("response_format") == "b64_json":
                yield {"b64_json": base64.b64encode(img.image_bytes).decode()}
            else:
                try:
                    image_id = md5(img.image_bytes).hexdigest()
                    ext = img.mime_type.split("/")[-1]
                    image_key = f"{GCS_PATH}/{image_id}.{ext}"
                    s3.put_object(
                        Bucket=GCS_BUCKET,
                        Key=image_key,
                        Body=img.image_bytes,
                        ContentType=img.mime_type,
                    )
                    image_url = s3.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": GCS_BUCKET, "Key": image_key},
                        ExpiresIn=3600,
                    )
                    yield {"url": image_url}
                except Exception as e:
                    raise ValueError("No image generated")

    async def run(self, request: ImageGenerateParams) -> dict[str, object]:
        data = list(self.generator(request))
        return {"data": data, "created": int(time.time())}
