import typing as tp
from dataclasses import dataclass

import base64c as base64
import typing_extensions as tpe
from fitz import open as open_pdf  # PyMuPDF

from ._base import Artifact


@dataclass
class PdfLoader(Artifact):
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
        Extract text and images from PDF documents.

        Yields:
            Text content and image data as HTML
        """
        file_path = self.retrieve()

        try:
            # First check if the file exists
            if not file_path.exists():
                yield f"Error: PDF file not found at {file_path}"
                return

            # Try to open the PDF document
            try:
                # Check for encryption
                doc = open_pdf(file_path)

                # If the document is encrypted, inform the user
                if doc.is_encrypted:
                    # Try with empty password first
                    try:
                        doc.authenticate("")
                    except Exception:
                        yield "Error: This PDF is encrypted and requires a password."
                        return

                    # Check if we succeeded with empty password
                    if doc.is_encrypted:
                        yield "Error: This PDF is encrypted and requires a password."
                        return
            except Exception as e:
                if "password" in str(e).lower():
                    yield "Error: This PDF is encrypted and requires a password."
                    return
                else:
                    yield f"Error opening PDF: {str(e)}"
                    return

            # Process each page
            for page_index, page in enumerate(doc):
                # Mark the page number
                yield f"<h2>Page {page_index + 1}</h2>"

                # Extract text content
                text = page.get_text()
                if text:
                    yield f"<div>{text}</div>"

                # Extract images
                for img_index, img in enumerate(page.get_images()):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        if base_image and "image" in base_image:
                            image_bytes = base_image["image"]
                            if isinstance(image_bytes, bytes):
                                img_data = base64.b64encode(image_bytes).decode()
                                img_ext = base_image.get("ext", "png")
                                yield f'<img style="width: 24em;" src="data:image/{img_ext};base64,{img_data}" />'
                    except Exception as img_error:
                        yield f"<p>Error extracting image {img_index}: {str(img_error)}</p>"

                # Also try to get HTML representation which may preserve formatting better
                try:
                    html_content = page.get_textpage().extractHTML()
                    if html_content:
                        yield html_content
                except Exception:
                    # If HTML extraction fails, we already have the plain text
                    pass

        except Exception as e:
            # Handle errors gracefully
            yield f"Error processing PDF file: {str(e)}"
