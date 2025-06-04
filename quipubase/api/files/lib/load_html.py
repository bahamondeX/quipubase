import base64
import typing as tp
from dataclasses import dataclass

import typing_extensions as tpe
from bs4 import BeautifulSoup, CData
from bs4.element import NavigableString

from ._base import Artifact


@dataclass
class HTMLLoader(Artifact):
    ref: tpe.Annotated[
        str,
        tpe.Doc(
            """
        This `ref` can represent one out of three things:

        - An HTTP URL.
        - A file path (temporary or not) within the local filesystem.
        - A text file content.
        """
        ),
    ]

    def extract(self) -> tp.Generator[str, None, None]:
        """
        Extract text and images from HTML content.

        Yields:
            Text chunks and image data from the HTML
        """
        file_path = self.retrieve()

        # Load HTML content with encoding detection
        try:
            # First try UTF-8
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
            except UnicodeDecodeError:
                # If UTF-8 fails, try with chardet to detect encoding
                import chardet

                # Read binary data
                with open(file_path, "rb") as file:
                    raw_data = file.read()

                # Detect encoding
                result = chardet.detect(raw_data)
                encoding = result["encoding"] if result["encoding"] else "utf-8"

                # Try with detected encoding
                with open(file_path, "r", encoding=encoding, errors="replace") as file:
                    content = file.read()

                # Let the user know which encoding was used
                yield f"<!-- HTML file encoded in {encoding} -->"

            soup = BeautifulSoup(content, "lxml")

            # Extract and yield text
            text = soup.get_text(
                separator="\n", strip=True, types=(NavigableString, CData)
            )
            if text:
                yield text

            # Extract and yield images
            for image in soup.find_all("img", src=True):
                src = tp.cast(str, image.get("src"))

                if src:
                    if src.startswith("data:"):
                        # Already a data URL
                        yield f'<img style="width: 24em;" src="{src}" />'
                    elif src.startswith(("http://", "https://")):
                        # Remote image URL
                        with self.__load__() as session:
                            try:
                                response = session.get(src)
                                if response.status_code == 200:
                                    img_data = base64.b64encode(
                                        response.content
                                    ).decode("utf-8")
                                    img_type = response.headers.get(
                                        "content-type", "image/png"
                                    )
                                    yield f'<img style="width: 24em;" src="data:{img_type};base64,{img_data}" />'
                            except Exception:
                                # Skip images that can't be loaded
                                pass
                    else:
                        # Local image reference - skip for safety
                        pass
        except Exception as e:
            # Handle errors gracefully
            yield f"Error processing HTML: {str(e)}"
