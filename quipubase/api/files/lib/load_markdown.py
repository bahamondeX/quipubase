import base64c as base64
import re
import typing as tp
from dataclasses import dataclass

import markdown
import typing_extensions as tpe

from ._base import Artifact


@dataclass
class MarkdownLoader(Artifact):
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
        Extract content from Markdown files including images.

        Yields:
            HTML converted from markdown and image tags
        """
        file_path = self.retrieve()

        try:
            # Read the markdown content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for image references in the markdown
            image_pattern = r"!\[(.*?)\]\((.*?)\)"
            image_matches = re.findall(image_pattern, content)

            # Handle images if found
            for alt_text, img_url in image_matches:
                # For images, try to embed them
                if img_url.startswith(("http://", "https://")):
                    try:
                        with self.__load__() as session:
                            response = session.get(img_url)
                            if response.status_code == 200:
                                img_data = base64.b64encode(response.content).decode(
                                    "utf-8"
                                )
                                yield f'<img style="width: 24em;" src="data:image/png;base64,{img_data}" alt="{alt_text}" />'
                    except Exception:
                        # If we can't get the image, include the original markdown as is
                        yield f"![{alt_text}]({img_url})"
                elif not img_url.startswith(("http://", "https://")):
                    # Try to handle as a local file reference using proper artifact retrieval
                    try:
                        # Create a new artifact instance for the image
                        from ._base import Artifact

                        img_artifact = Artifact(ref=img_url)  # type: ignore
                        img_path = img_artifact.retrieve()

                        if img_path.exists():
                            with open(img_path, "rb") as img_file:
                                img_data = base64.b64encode(img_file.read()).decode(
                                    "utf-8"
                                )
                                yield f'<img style="width: 24em;" src="data:image/png;base64,{img_data}" alt="{alt_text}" />'
                        else:
                            # Fall back to original markdown if retrieval fails
                            yield f"![{alt_text}]({img_url})"
                    except Exception:
                        # Fall back to original markdown
                        yield f"![{alt_text}]({img_url})"
                else:
                    # Just include the original markdown reference
                    yield f"![{alt_text}]({img_url})"

            # Convert markdown to HTML and yield
            html_content = markdown.markdown(
                content, extensions=["extra", "codehilite"]
            )
            yield html_content

        except Exception as e:
            # Handle errors gracefully
            yield f"Error processing Markdown: {str(e)}"
