import typing as tp
from dataclasses import dataclass
import re

import typing_extensions as tpe

from ._base import Artifact


@dataclass
class RTFLoader(Artifact):
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

    def _extract_plain_text(self, rtf_content: str) -> str:
        """
        Extract plain text from RTF content.
        Simple implementation - removes RTF control codes.
        """
        # Remove RTF headers and control words
        text = rtf_content
        
        # Remove header
        text = re.sub(r'^.*\\rtf1.*$', '', text, flags=re.MULTILINE)
        
        # Remove common control words
        text = re.sub(r'\\[a-z0-9]+(-?[0-9]+)?[ ]?', '', text)
        text = re.sub(r'\\\'[0-9a-f]{2}', '', text)  # Hex values like \'92
        
        # Remove curly braces
        text = re.sub(r'[{}]', '', text)
        
        # Remove non-printable characters
        text = re.sub(r'[\x00-\x1F\x7F-\xFF]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def extract(self) -> tp.Generator[str, None, None]:
        """
        Extract text from RTF (Rich Text Format) files.
        
        Yields:
            Plain text extracted from the RTF document
        """
        file_path = self.retrieve()
        
        try:
            # Read the RTF file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                rtf_content = f.read()
            
            # Check if it's a valid RTF file (should start with "{\\rtf")
            if not rtf_content.startswith("{\\rtf"):
                yield "Error: The file does not appear to be a valid RTF document."
                return
            
            # Extract plain text
            plain_text = self._extract_plain_text(rtf_content)
            
            # Split into paragraphs
            paragraphs = re.split(r'\n\s*\n|\r\n\s*\r\n', plain_text)
            
            # Yield each paragraph
            for para in paragraphs:
                if para.strip():
                    yield f"<p>{para.strip()}</p>"
                    
        except Exception as e:
            # Handle errors gracefully
            yield f"Error processing RTF file: {str(e)}"