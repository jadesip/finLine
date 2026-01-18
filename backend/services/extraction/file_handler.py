"""
File handling and processing utilities for extraction.
Ported from FinForge - MUST remain identical for consistent behavior.
"""

import hashlib
import io
import logging
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
from PIL import Image

from .text_extractor import DocumentType, StructuredText, TextExtractor

logger = logging.getLogger(__name__)


class FileHandler:
    """
    Handles file processing for extraction pipeline.

    Supports PDF and image files, converting them to a standard format
    for LLM processing.
    """

    SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}
    SUPPORTED_PDF_FORMAT = ".pdf"
    MAX_FILE_SIZE_MB = 50
    PDF_DPI = 300  # High quality for financial tables

    def __init__(self, upload_dir: str = "uploads"):
        """
        Initialize file handler.

        Args:
            upload_dir: Directory for storing uploaded files
        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.text_extractor = TextExtractor()
        logger.info(f"FileHandler initialized with upload directory: {self.upload_dir}")

    async def process_file(
        self,
        file_bytes: bytes,
        filename: str,
        store_original: bool = True,
        extract_text: bool = True,
    ) -> tuple[list[bytes], str, dict[str, Any], StructuredText | None]:
        """
        Process uploaded file and convert to images.

        Args:
            file_bytes: Raw file bytes
            filename: Original filename
            store_original: Whether to store the original file
            extract_text: Whether to extract text from PDF

        Returns:
            Tuple of (image_list, file_hash, metadata, structured_text)
        """
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            raise ValueError(f"File too large: {file_size_mb:.1f}MB (max: {self.MAX_FILE_SIZE_MB}MB)")

        file_hash = hashlib.sha256(file_bytes).hexdigest()[:16]

        if store_original:
            await self._store_original_file(file_bytes, filename, file_hash)

        file_ext = Path(filename).suffix.lower()
        logger.info(f"Processing file: {filename} (type: {file_ext}, size: {file_size_mb:.2f}MB)")

        if file_ext == self.SUPPORTED_PDF_FORMAT:
            images = await self._process_pdf(file_bytes)
            file_type = "pdf"
        elif file_ext in self.SUPPORTED_IMAGE_FORMATS:
            images = await self._process_image(file_bytes)
            file_type = "image"
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")

        # Analyze document type
        doc_type = self.text_extractor.analyze_document(file_bytes, filename)

        # Extract text if applicable
        structured_text = None
        text_quality = None

        if extract_text and doc_type == DocumentType.PDF_WITH_TEXT:
            logger.info("Extracting text from PDF (hybrid extraction enabled)")
            try:
                pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
                text_quality = self.text_extractor.assess_text_quality(pdf_doc)

                # Use basic text extraction
                structured_text = self.text_extractor.extract_structured_text_basic(pdf_doc)
                pdf_doc.close()
                logger.info(
                    f"Extracted {len(structured_text.pages)} pages with basic text extraction"
                )
            except Exception as e:
                logger.error(f"Text extraction failed: {e}")
                structured_text = None

        metadata = {
            "original_filename": filename,
            "file_type": file_type,
            "file_size_mb": file_size_mb,
            "file_hash": file_hash,
            "page_count": len(images),
            "document_type": doc_type.value,
            "has_text": structured_text is not None,
            "text_quality": text_quality.__dict__ if text_quality else None,
        }

        logger.info(
            f"File processed: {len(images)} images extracted, document type: {doc_type.value}"
        )

        return images, file_hash, metadata, structured_text

    async def _process_pdf(self, pdf_bytes: bytes) -> list[bytes]:
        """Convert PDF to images."""
        images = []

        try:
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            page_count = len(pdf_document)
            logger.info(f"Converting PDF to images: {page_count} pages at {self.PDF_DPI} DPI")

            if page_count > 30:
                logger.warning(f"Large document: {page_count} pages - may take time")

            for page_num in range(page_count):
                page = pdf_document[page_num]
                mat = fitz.Matrix(self.PDF_DPI / 72, self.PDF_DPI / 72)
                pix = page.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes("png")
                images.append(img_bytes)
                logger.debug(f"Converted page {page_num + 1}/{page_count}")

            pdf_document.close()
            logger.info(f"PDF conversion completed: {len(images)} pages")

        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            raise

        return images

    async def _process_image(self, img_bytes: bytes) -> list[bytes]:
        """Process and optimize image."""
        try:
            img = Image.open(io.BytesIO(img_bytes))

            if img.mode != "RGB":
                img = img.convert("RGB")

            max_dimension = 4096
            if img.width > max_dimension or img.height > max_dimension:
                img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                logger.info(f"Resized image to {img.width}x{img.height}")

            buffer = io.BytesIO()
            img.save(buffer, format="PNG", optimize=True)
            return [buffer.getvalue()]

        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            raise

    async def _store_original_file(self, file_bytes: bytes, filename: str, file_hash: str):
        """Store original file for reference."""
        subdir = self.upload_dir / file_hash[:2]
        subdir.mkdir(exist_ok=True)

        safe_filename = f"{file_hash}_{Path(filename).name}"
        file_path = subdir / safe_filename

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        logger.info(f"Stored original file: {file_path}")
