from dataclasses import dataclass
import enum
import tempfile
import typing as tp
from abc import ABC, abstractmethod
from pathlib import Path

import typing_extensions as tpe
from httpx import Client

from ._proxy import LazyProxy

# Standard headers for HTTP requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


class FileType(str, enum.Enum):
    """Enumeration of supported file types with their extensions."""

    DOCX = ".docx"
    DOC = ".doc"
    PDF = ".pdf"
    PPTX = ".pptx"
    PPT = ".ppt"
    XLSX = ".xlsx"
    XLS = ".xls"
    TXT = ".txt"
    MD = ".md"
    HTML = ".html"
    CSS = ".css"
    JS = ".js"
    JSON = ".json"
    XML = ".xml"
    CSV = ".csv"
    RTF = ".rtf"
    HTM = ".htm"


# Type alias using the enum for better organization
FileSuffix: tpe.TypeAlias = tp.Literal[
    FileType.DOCX,
    FileType.PDF,
    FileType.PPTX,
    FileType.XLSX,
    FileType.XLS,
    FileType.DOC,
    FileType.PPT,
    FileType.TXT,
    FileType.MD,
    FileType.HTML,
    FileType.CSS,
    FileType.JS,
    FileType.JSON,
    FileType.XML,
    FileType.CSV,
    FileType.RTF,
    FileType.HTM,
]


@dataclass
class Artifact(LazyProxy[Client], ABC):
    """
    Abstract base class for handling different types of artifacts.

    An artifact can be a URL, file path, or raw text content.
    """

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

    def __load__(self) -> Client:
        """Load and return an HTTP client with predefined headers."""
        return Client(headers=HEADERS)

    def retrieve(self) -> Path:
        """
        Retrieve the artifact and return a path to the local file.

        For URLs, downloads the content.
        For file paths, returns the path.
        For raw text content, creates a temporary file.

        Returns:
                Path to the file on the local filesystem
        """
        # Handle HTTP URLs
        if self.ref.startswith(("http://", "https://")):
            with self.__load__() as session:
                response = session.get(self.ref)
                response.raise_for_status()
                content = response.content
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=self._detect_extension()
                ) as file:
                    file.write(content)
                    return Path(file.name)

        else:
            try:
                path = Path(self.ref)
                if path.exists() and path.is_file():
                    return path
            except (TypeError, ValueError):
                raise ValueError(f"Invalid file path: {self.ref}")
            except Exception:
                # Handle raw text content
                with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as file:
                    file.write(self.ref.encode())
                    return Path(file.name)

        # If we get here, something went wrong
        raise ValueError(f"Could not process artifact: {self.ref}")

    def _detect_extension(self) -> str:
        """
        Try to detect file extension from URL or content type.

        Returns:
                A file extension including the dot (e.g., ".pdf")
        """
        try:
            path = Path(self.ref.split("?")[0])  # Remove query parameters
            if path.suffix:
                return path.suffix
        except (TypeError, ValueError):
            pass
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(self.ref.encode())
            path = Path(f.name)
            if path.suffix:
                return path.suffix
        return ".txt"

    @abstractmethod
    def extract(self) -> tp.Generator[str, None, None]:
        """
        Extract text content from the artifact.

        Yields:
                Text chunks from the artifact
        """
        raise NotImplementedError
