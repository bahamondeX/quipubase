from google import genai
import os
from PIL import Image
from io import BytesIO

def generate():
    client = genai.Client(api_key=os.environ.get("OPENAI_API_KEY"))

    result = client.models.generate_images(
        model="models/imagen-3.0-generate-002",
        prompt="""A 6/10 woman on her thirties with light skin tone, dark hair, big nose, high cheeks, oval face, big brown eyes with eyebrow on the bottom and a visible mole on her right cheekbone, straight flat-ironed black hair from a messy bun, wearing a black t-shirt with drums logo, staring at the camera of her fiance's iphone smiling very surprised with her hands crossed below her chin touching the back of her hands with her chin, sitting within a rock bar in Lima, Peru. Vintage style, 35mm film, high quality, detailed, realistic, cinematic lighting, soft focus""",
        config=dict(
            number_of_images=1,
            output_mime_type="image/png",
            person_generation="ALLOW_ADULT",
            aspect_ratio="1:1",
        ),
    )

    if not result.generated_images:
        print("No images generated.")
        return

    if len(result.generated_images) != 1:
        print("Number of images generated does not match the requested number.")

    for generated_image in result.generated_images:
        image = Image.open(BytesIO(generated_image.image.image_bytes))
        image.save("1.png")


if __name__ == "__main__":
    generate()