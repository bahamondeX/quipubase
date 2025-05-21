import mimetypes
import importlib
import inspect
import tempfile
import shutil
import typing as tp
from pathlib import Path

import requests
from fastapi import UploadFile
from bs4 import BeautifulSoup, Comment

# Import the FileType enum from the existing code
from ._base import FileType, Artifact
from .load_docx import DocxLoader
from .load_jsonl import JsonLoader
from .load_markdown import MarkdownLoader
from .load_pdf import PdfLoader
from .load_pptx import PptxLoader
from .load_xlsx import ExcelLoader
from .load_html import HTMLLoader
from .load_csv import CSVLoader
from .load_xml import XMLLoader
from .load_rtf import RTFLoader


class DocumentLoaderError(Exception):
    """Custom exception for document loading errors."""
    pass


class AnyDocs:
    """
    A flexible document loader that detects file type and extracts content.

    Supports loading from:
    - Local file paths
    - URLs
    - HTTP responses
    
    Provides:
    - Registry for document loaders
    - Dynamic loader registration
    - Text extraction for LLM context windows
    """

    # Registry for file extensions and their corresponding loaders
    _registry: tp.ClassVar[dict[str, tp.Type[Artifact]]] = {
        FileType.DOCX.value: DocxLoader,
        FileType.DOC.value: DocxLoader,
        FileType.PDF.value: PdfLoader,
        FileType.PPTX.value: PptxLoader,
        FileType.PPT.value: PptxLoader,
        FileType.XLSX.value: ExcelLoader,
        FileType.XLS.value: ExcelLoader,
        FileType.JSON.value: JsonLoader,
        FileType.MD.value: MarkdownLoader,
        FileType.TXT.value: MarkdownLoader,
        FileType.HTML.value: HTMLLoader,
        FileType.HTM.value: HTMLLoader,
        FileType.CSS.value: MarkdownLoader,
        FileType.JS.value: MarkdownLoader,
        FileType.XML.value: XMLLoader,
        FileType.CSV.value: CSVLoader,
        FileType.RTF.value: RTFLoader,
    }

    @classmethod
    def _guess_file_type_from_mimetype(cls, mimetype: str) -> tp.Optional[str]:
        """
        Convert mimetype to file suffix.

        Args:
            mimetype: MIME type string

        Returns:
            Corresponding file suffix or None
        """
        mimetype = mimetype.lower()
        mimetype_to_suffix = {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": FileType.DOCX.value,
            "application/msword": FileType.DOC.value,
            "application/pdf": FileType.PDF.value,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": FileType.PPTX.value,
            "application/vnd.ms-powerpoint": FileType.PPT.value,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": FileType.XLSX.value,
            "application/vnd.ms-excel": FileType.XLS.value,
            "application/json": FileType.JSON.value,
            "text/markdown": FileType.MD.value,
            "text/plain": FileType.TXT.value,
            "text/html": FileType.HTML.value,
            "text/css": FileType.CSS.value,
            "application/javascript": FileType.JS.value,
        }

        return mimetype_to_suffix.get(mimetype)

    @classmethod
    def _detect_file_type(cls, file_path: Path) -> str:
        """
        Detect file type using multiple methods.

        Args:
            file_path: Path to the file

        Returns:
            File suffix

        Raises:
            DocumentLoaderError if file type cannot be determined
        """
        # 1. Check file extension first
        if file_path.suffix:
            # Normalize the suffix to match FileType
            suffix = file_path.suffix.lower()
            normalized_suffixes = {
                ".doc": FileType.DOCX.value,
                ".docx": FileType.DOCX.value,
                ".pdf": FileType.PDF.value,
                ".ppt": FileType.PPTX.value,
                ".pptx": FileType.PPTX.value,
                ".xls": FileType.XLSX.value,
                ".xlsx": FileType.XLSX.value,
                ".xlsb": FileType.XLSX.value,
                ".json": FileType.JSON.value,
                ".jsonl": FileType.JSON.value,
                ".md": FileType.MD.value,
                ".txt": FileType.TXT.value,
                ".html": FileType.HTML.value,
                ".htm": FileType.HTML.value,
                ".css": FileType.CSS.value,
                ".js": FileType.JS.value,
            }
            if suffix in normalized_suffixes:
                return normalized_suffixes[suffix]

        # 2. Try mimetypes package
        mimetype, _ = mimetypes.guess_type(str(file_path))
        if mimetype:
            guessed_type = cls._guess_file_type_from_mimetype(mimetype)
            if guessed_type:
                return guessed_type

        # 3. Try reading file content (if file is open-able)
        try:
            with open(file_path, "rb") as f:
                # Read first few bytes to detect file type
                header = f.read(16)

                # PDF magic number
                if header.startswith(b"%PDF-"):
                    return FileType.PDF.value

                # DOCX magic number
                if header.startswith(b"PK\x03\x04") and b"word/" in header:
                    return FileType.DOCX.value

                # XLSX magic number
                if header.startswith(b"PK\x03\x04") and b"xl/" in header:
                    return FileType.XLSX.value

                # PPTX magic number
                if header.startswith(b"PK\x03\x04") and b"ppt/" in header:
                    return FileType.PPTX.value
        except Exception:
            pass

        # If all methods fail
        raise DocumentLoaderError(f"Could not determine file type for {file_path}")

    @classmethod
    def register_loader(cls, extension: str, loader_class: tp.Type[Artifact]) -> None:
        """
        Register a new document loader for a specific file extension.
        
        Args:
            extension: The file extension to register (including the dot)
            loader_class: The loader class (must inherit from Artifact)
        
        Raises:
            TypeError: If the loader class doesn't inherit from Artifact
            ValueError: If the extension is invalid
        """
        # Validate loader class
        if not inspect.isclass(loader_class):
            raise TypeError(f"Loader class must inherit from Artifact base class")
        
        # Validate extension
        if not extension.startswith('.'):
            extension = f".{extension}"
            
        extension = extension.lower()
        
        # Register the loader
        cls._registry[extension] = loader_class

    @classmethod
    def from_module(cls, module_name: str) -> None:
        """
        Dynamically load loaders from a module and register them.
        
        Args:
            module_name: The name of the module to import
            
        Raises:
            ImportError: If the module cannot be imported or has no loaders
        """
        try:
            module = importlib.import_module(module_name)
            
            # Find all classes that inherit from Artifact
            loaders_found = False
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, Artifact) and obj != Artifact:
                    # Try to determine the file extension from the class name
                    extension = None
                    
                    if name.endswith('Loader'):
                        # Remove 'Loader' suffix and convert to extension
                        ext_part = name[:-6].lower()
                        
                        # Handle special cases
                        if ext_part == 'html':
                            extension = '.html'
                        elif ext_part == 'docx':
                            extension = '.docx'
                        elif ext_part == 'pdf':
                            extension = '.pdf'
                        elif ext_part == 'pptx':
                            extension = '.pptx'
                        elif ext_part == 'excel':
                            extension = '.xlsx'
                        elif ext_part == 'json':
                            extension = '.json'
                        elif ext_part == 'markdown':
                            extension = '.md'
                        elif ext_part == 'jsonl':
                            extension = '.jsonl'
                        if extension:
                            cls.register_loader(extension, obj)
                            loaders_found = True
            
            if not loaders_found:
                raise ImportError(f"No valid loader classes found in module {module_name}")
                            
        except (ImportError, AttributeError) as e:
            raise ImportError(f"Could not import loaders from module {module_name}: {str(e)}")

    @classmethod
    def _extract_text_only(cls, html_content: str) -> str:
        """
        Extract plain text from HTML content, removing all tags and scripts.
        
        Args:
            html_content: HTML content as string
            
        Returns:
            Plain text suitable for LLM context window
        """
        try:
            # Parse HTML content
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Remove scripts, styles, and comments
            for element in soup(['script', 'style', 'head', 'title', 'meta', '[document]']):
                element.extract()
                
            # Remove comments
            for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
                comment.extract()
            
            # Get text with sensible spacing
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception:
            # If parsing fails, return original content
            return html_content

    @classmethod
    def load_document(cls, file: tp.Union[str, Path, UploadFile], extract_text_only: bool = True) -> tp.Generator[str, None, None]:
        """
        Load and extract text from a document based on its type.

        Args:
            file: A file path, URL, or UploadFile object
            extract_text_only: If True, extracts only plain text without HTML formatting

        Returns:
            A generator yielding text chunks from the document

        Raises:
            DocumentLoaderError: If the file type is unsupported
        """
        # Handle UploadFile directly
        # Convert string to Path or handle as URL
        if isinstance(file, str):
            if file.startswith(("http://", "https://")):
                # Download the file from URL
                try:
                    response = requests.get(file, stream=True, timeout=10)
                    response.raise_for_status()
                    content_type = response.headers.get("Content-Type", "").lower()
                    guessed_ext = cls._guess_file_type_from_mimetype(content_type)
                    suffix = Path(file.split("?")[0]).suffix.lower() or f".{guessed_ext or 'tmp'}"
                    if not suffix or suffix not in cls._registry:
                        raise DocumentLoaderError(f"Unsupported or undetectable file type for URL: {file}")
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        for chunk in response.iter_content(chunk_size=8192):
                            tmp.write(chunk)
                        tmp_path = Path(tmp.name)
                except Exception as e:
                    raise DocumentLoaderError(f"Failed to download file from URL: {e}")

                loader_cls = cls._registry[suffix]
                doc = loader_cls(tmp_path.as_posix())
                for chunk in doc.extract():
                    yield cls._extract_text_only(chunk) if extract_text_only else chunk
                tmp_path.unlink()
                return
        # Local file path
        elif isinstance(file,Path):
            if not file.exists():
                raise DocumentLoaderError(f"File not found: {file}")
            try:
                suffix = cls._detect_file_type(file)
                if suffix not in cls._registry:
                    raise DocumentLoaderError(f"No loader registered for: {suffix}")
                loader_cls = cls._registry[suffix]
                doc = loader_cls(file.as_posix())
                for chunk in doc.extract():
                    yield cls._extract_text_only(chunk) if extract_text_only else chunk
            except Exception as e:
                raise DocumentLoaderError(f"Failed to load document: {e}")
        else:
            filename = file.filename or "uploaded_file"
            suffix = Path(filename).suffix.lower()
            if suffix not in cls._registry:
                raise DocumentLoaderError(f"Unsupported file type: {suffix}")
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = Path(tmp.name)

            loader_cls = cls._registry[suffix]
            doc = loader_cls(ref=tmp_path.as_posix())
            for chunk in doc.extract():
                yield cls._extract_text_only(chunk) if extract_text_only else chunk
            tmp_path.unlink()  # cleanup
            return
        
    @classmethod
    def get_registry(cls):
        return cls._registry


# Convenience function that uses the new AnyDocs class
def load_document(
    file: tp.Union[str, Path, UploadFile], 
    extract_text_only: bool = True
) -> tp.Generator[str, None, None]:
    """
    Load a document from a source (URL, file path, or content) and extract its content.
    
    Args:
        file: The document source (URL, file path, or UploadFile object)
        extract_text_only: If True, extracts only plain text without HTML formatting
    
    Returns:
        A generator yielding document content chunks
        
    Raises:
        DocumentLoaderError: If the document type is unsupported
    """
    return AnyDocs.load_document(file, extract_text_only)