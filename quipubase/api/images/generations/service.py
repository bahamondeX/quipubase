import os
import vertexai
from vertexai.vision_models import ImageGenerationModel, GeneratedImage	
import base64
from pydantic import BaseModel, Field
from typing import Literal, Optional, Generator
from boto3 import client  # type:ignore
from botocore.config import Config  # Import boto3
from dotenv import load_dotenv
from hashlib import md5
from quipubase.api.chat.service import OpenAITool

load_dotenv()

GCS_BUCKET = os.getenv(
	"GCS_BUCKET", "quipubase-store"
)  # Make bucket configurable via env var

GCS_PATH = (
	"/images"  # This path doesn't seem to be used directly by boto3 operations here.
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

class ImageGenerationRequest(
	 OpenAITool
):  # Changed from OpenAITool as it's not provided
	model_config = {"extra": "allow"}
	prompt: str = Field(..., description="Text prompt describing the image.")
	n: int = Field(default=1, description="Number of images to generate.")
	ratio: Literal["1:1", "16:9", "4:3"] = Field(
		default="16:9", description="Ratio of the image to generate."
	)
	response_format: Literal["url", "b64_json"] = Field(
		default="b64_json", description="Format of the image response."
	)
	user: Optional[str] = Field(
		default=None, description="Unique identifier for the end-user."
	)	
	
	def generator(self):
		vertexai.init(project=os.getenv("GOOGLE_PROJECT_ID"), location="us-central1")
		generation_model = ImageGenerationModel.from_pretrained(
			"imagen-4.0-generate-preview-05-20"
		)

		if self.response_format == "url":
			images = generation_model.generate_images(
				prompt=self.prompt,
				number_of_images=self.n,
				aspect_ratio=self.ratio,
				add_watermark=False,
				safety_filter_level="block_few",
				person_generation="allow_adult"
			)
		else:
			images = generation_model.generate_images(
				prompt=self.prompt,
				number_of_images=self.n,
				aspect_ratio=self.ratio,
				add_watermark=False,
				safety_filter_level="block_few",
				person_generation="allow_adult",
			)
			for img in images:
				if self.response_format == "b64_json":
					yield {"b64_json": img._as_base64_string()}
				elif self.response_format == "url":
					try:
						image_id = md5(img._as_base64_string().encode()).hexdigest()
						image_key = f"{GCS_PATH}/{image_id}.png"
						s3.put_object(
							Bucket=GCS_BUCKET,
							Key=image_key,
						Body=img._image_bytes,
						ContentType="image/png",
					)
						image_url = s3.generate_presigned_url(
							"get_object",
							Params={"Bucket": GCS_BUCKET, "Key": image_key},
							ExpiresIn=3600,
						)
						yield {"url": image_url}
					except Exception as e:
						yield {self.response_format: f"Failed to upload image to S3: {e}"}
			else:
				raise NotImplementedError("Unsupported response format.")
				
	async def run(self):
		for res in self.generator():
			if self.response_format == "b64_json":
				image_str = res.get('b64_json')	
			else:
				image_str = res.get('url')
			if image_str is None:
				continue
			yield self._parse_chunk(image_str)	
			
				

	async def create(self):
		# Implementation needed or remove this method if not used.
		return {"data":list(self.generator())}