"""
AnyDocs - A flexible library for document loading and text extraction from various file formats.

Main functionality:
- Load and extract text from different document types (PDF, DOCX, PPTX, HTML, etc.)
- Extract plain text for LLM context windows
- Register custom document loaders
"""

from ._base import Artifact, FileType
from .anydocs import AnyDocs, DocumentLoaderError, load_document
from .load_csv import CSVLoader
# Document loaders
from .load_docx import DocxLoader
from .load_html import HTMLLoader
from .load_jsonl import JsonLoader
from .load_markdown import MarkdownLoader
from .load_pdf import PdfLoader
from .load_pptx import PptxLoader
from .load_rtf import RTFLoader
from .load_xlsx import ExcelLoader
from .load_xml import XMLLoader
from .utils import (asyncify, chunker, get_key, get_logger, handle,
                    retry_handler, singleton)

__all__ = [
    # Core functionality
    "AnyDocs",
    "load_document",
    "DocumentLoaderError",
    "Artifact",
    "FileType",
    # Loaders
    "DocxLoader",
    "PdfLoader",
    "PptxLoader",
    "ExcelLoader",
    "JsonLoader",
    "MarkdownLoader",
    "HTMLLoader",
    "CSVLoader",
    "XMLLoader",
    "RTFLoader",
    # Utilities
    "singleton",
    "get_logger",
    "get_key",
    "asyncify",
    "handle",
    "chunker",
    "retry_handler",
]
