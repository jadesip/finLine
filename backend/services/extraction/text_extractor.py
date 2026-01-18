"""
PDF text extraction with layout preservation for financial documents.
Ported from FinForge - MUST remain identical for consistent behavior.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Types of documents based on content analysis."""

    IMAGE_ONLY = "image_only"
    PDF_WITH_TEXT = "pdf_with_text"
    PDF_SCANNED = "pdf_scanned"


@dataclass
class TextQuality:
    """Assessment of text extraction quality."""

    is_sufficient: bool
    confidence: float
    char_count: int
    word_count: int
    financial_indicators: int
    recommendation: str
    details: dict[str, Any]


@dataclass
class TableRegion:
    """Represents a detected table region in the document."""

    page_num: int
    bbox: tuple[float, float, float, float]  # x0, y0, x1, y1
    columns: list[float]  # x-coordinates of column boundaries
    rows: list[dict[str, Any]]  # structured row data
    confidence: float


@dataclass
class StructuredText:
    """Structured representation of extracted text."""

    pages: list[dict[str, Any]]
    tables: list[TableRegion]
    raw_text: str
    metadata: dict[str, Any]

    def format_for_llm(self) -> str:
        """
        Format structured text for LLM consumption.

        Returns:
            Formatted string optimized for LLM understanding
        """
        formatted_parts = []

        for page in self.pages:
            formatted_parts.append(f"\n=== PAGE {page['page_num']} ===\n")

            # Add paragraphs
            for para in page.get("paragraphs", []):
                formatted_parts.append(para["text"])
                formatted_parts.append("")  # Empty line

            # Add tables with structure
            for table in page.get("tables", []):
                formatted_parts.append("\n[TABLE]")

                # Format rows
                for row in table["rows"]:
                    cells = row["cells"]
                    # Order cells by column position
                    sorted_cols = sorted(cells.keys())
                    row_text = " | ".join(str(cells.get(col, "")) for col in sorted_cols)
                    formatted_parts.append(row_text)

                formatted_parts.append("[/TABLE]\n")

        return "\n".join(formatted_parts)


class TextExtractor:
    """
    Extracts and structures text from PDF documents while preserving layout.

    Designed specifically for financial documents with tables and structured data.
    Ported from FinForge - MUST remain identical for consistent extraction.
    """

    # Financial keywords to detect relevant content
    FINANCIAL_KEYWORDS = {
        "revenue",
        "sales",
        "ebitda",
        "ebit",
        "capex",
        "cash flow",
        "income",
        "expense",
        "profit",
        "loss",
        "assets",
        "liabilities",
        "balance sheet",
        "income statement",
        "cash flow statement",
        "$",
        "€",
        "£",
        "¥",
        "usd",
        "eur",
        "gbp",
        "millions",
        "thousands",
    }

    # Minimum thresholds for text quality
    MIN_CHARS_FOR_TEXT = 500
    MIN_WORDS_FOR_TEXT = 50
    MIN_FINANCIAL_INDICATORS = 2

    def __init__(self):
        """Initialize the text extractor."""
        logger.info("TextExtractor initialized (basic text extraction)")

    def analyze_document(self, file_bytes: bytes, filename: str) -> DocumentType:
        """
        Determine document type based on content analysis.

        Args:
            file_bytes: Raw file bytes
            filename: Original filename

        Returns:
            Document type classification
        """
        # Handle pure image files
        if filename.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff")):
            logger.info(f"Detected image file: {filename}")
            return DocumentType.IMAGE_ONLY

        # Handle PDFs
        if filename.lower().endswith(".pdf"):
            try:
                pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
                quality = self.assess_text_quality(pdf_doc)
                pdf_doc.close()

                if quality.is_sufficient:
                    logger.info(f"Detected PDF with extractable text: {filename}")
                    return DocumentType.PDF_WITH_TEXT
                else:
                    logger.info(f"Detected scanned PDF: {filename}")
                    return DocumentType.PDF_SCANNED

            except Exception as e:
                logger.error(f"Error analyzing PDF: {e}")
                return DocumentType.PDF_SCANNED

        # Default to image processing
        return DocumentType.IMAGE_ONLY

    def assess_text_quality(self, pdf_doc) -> TextQuality:
        """
        Assess the quality of extractable text in a PDF.

        Args:
            pdf_doc: PyMuPDF document object

        Returns:
            Text quality assessment
        """
        sample_pages = min(3, len(pdf_doc))  # Check first 3 pages
        total_chars = 0
        total_words = 0
        financial_indicators = 0
        page_details = []

        for i in range(sample_pages):
            page = pdf_doc[i]
            text = page.get_text()

            # Basic metrics
            chars = len(text.strip())
            words = len(text.split())
            total_chars += chars
            total_words += words

            # Look for financial content
            text_lower = text.lower()
            page_financial_count = sum(
                1 for keyword in self.FINANCIAL_KEYWORDS if keyword in text_lower
            )
            financial_indicators += page_financial_count

            page_details.append(
                {
                    "page": i + 1,
                    "chars": chars,
                    "words": words,
                    "financial_keywords": page_financial_count,
                }
            )

            logger.debug(
                f"Page {i + 1}: {chars} chars, {words} words, "
                f"{page_financial_count} financial indicators"
            )

        # Calculate quality metrics
        avg_chars_per_page = total_chars / sample_pages if sample_pages > 0 else 0
        avg_words_per_page = total_words / sample_pages if sample_pages > 0 else 0

        # Determine if text quality is sufficient
        has_text = total_chars >= self.MIN_CHARS_FOR_TEXT
        has_structure = total_words >= self.MIN_WORDS_FOR_TEXT
        has_financial_content = financial_indicators >= self.MIN_FINANCIAL_INDICATORS

        is_sufficient = has_text and has_structure

        # Calculate confidence score (0-1)
        confidence = min(
            1.0,
            (
                (total_chars / (self.MIN_CHARS_FOR_TEXT * 2)) * 0.3
                + (total_words / (self.MIN_WORDS_FOR_TEXT * 2)) * 0.3
                + (financial_indicators / (self.MIN_FINANCIAL_INDICATORS * 3)) * 0.4
            ),
        )

        # Recommendation based on analysis
        if is_sufficient and has_financial_content:
            recommendation = "hybrid"  # Use both text and images
        elif is_sufficient:
            recommendation = "text_first"  # Try text first, fallback to images
        else:
            recommendation = "image_only"  # Skip text extraction

        quality = TextQuality(
            is_sufficient=is_sufficient,
            confidence=confidence,
            char_count=total_chars,
            word_count=total_words,
            financial_indicators=financial_indicators,
            recommendation=recommendation,
            details={
                "pages_analyzed": sample_pages,
                "avg_chars_per_page": avg_chars_per_page,
                "avg_words_per_page": avg_words_per_page,
                "has_financial_content": has_financial_content,
                "page_details": page_details,
            },
        )

        logger.info(
            f"Text quality: {quality.confidence:.1%} confidence, "
            f"{total_words} words, {financial_indicators} financial indicators, "
            f"recommendation: {recommendation}"
        )

        return quality

    def extract_structured_text_basic(self, pdf_doc) -> StructuredText:
        """
        Extract text from PDF using basic approach.

        Args:
            pdf_doc: PyMuPDF document object

        Returns:
            Structured text data with basic table detection
        """
        pages_data = []
        all_tables = []
        full_text = []

        for page_num, page in enumerate(pdf_doc):
            logger.info(f"Extracting text from page {page_num + 1}/{len(pdf_doc)}")

            # Get text with detailed positioning information
            text_dict = page.get_text("dict")

            # Extract raw text for this page
            page_text = page.get_text()
            full_text.append(page_text)

            # Detect and extract tables using basic method
            tables = self._detect_tables(text_dict, page_num)
            all_tables.extend(tables)

            # Extract paragraphs (non-table text)
            paragraphs = self._extract_paragraphs(text_dict, tables)

            # Store page data
            page_data = {
                "page_num": page_num + 1,
                "raw_text": page_text,
                "tables": [self._table_to_dict(t) for t in tables],
                "paragraphs": paragraphs,
                "dimensions": {"width": page.rect.width, "height": page.rect.height},
            }
            pages_data.append(page_data)

        # Create metadata
        metadata = {
            "total_pages": len(pdf_doc),
            "total_tables": len(all_tables),
            "extraction_method": "basic_text_extraction",
        }

        return StructuredText(
            pages=pages_data, tables=all_tables, raw_text="\n\n".join(full_text), metadata=metadata
        )

    def _detect_tables(self, text_dict: dict, page_num: int) -> list[TableRegion]:
        """
        Detect table regions based on text alignment patterns.

        Args:
            text_dict: PyMuPDF text dictionary with positioning
            page_num: Current page number

        Returns:
            List of detected table regions
        """
        tables = []

        # Extract all text blocks with positions
        blocks = []
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if span.get("text", "").strip():
                            blocks.append(
                                {
                                    "text": span["text"],
                                    "bbox": span["bbox"],  # (x0, y0, x1, y1)
                                    "line_bbox": line["bbox"],
                                    "block_bbox": block["bbox"],
                                }
                            )

        if not blocks:
            return tables

        # Group blocks by vertical alignment (potential columns)
        column_groups = defaultdict(list)
        tolerance = 5  # pixels tolerance for alignment

        for block in blocks:
            x_pos = block["bbox"][0]
            # Snap to grid
            x_grid = round(x_pos / tolerance) * tolerance
            column_groups[x_grid].append(block)

        # Identify table regions (3+ aligned columns)
        if len(column_groups) >= 3:
            sorted_columns = sorted(column_groups.keys())

            # Check for consistent row alignment
            table_rows = self._extract_table_rows(column_groups, sorted_columns)

            if len(table_rows) >= 2:  # Minimum rows for a table
                # Calculate table bounding box
                all_bboxes = [b["bbox"] for blocks in column_groups.values() for b in blocks]
                x0 = min(bbox[0] for bbox in all_bboxes)
                y0 = min(bbox[1] for bbox in all_bboxes)
                x1 = max(bbox[2] for bbox in all_bboxes)
                y1 = max(bbox[3] for bbox in all_bboxes)

                table = TableRegion(
                    page_num=page_num,
                    bbox=(x0, y0, x1, y1),
                    columns=sorted_columns,
                    rows=table_rows,
                    confidence=0.8,  # Base confidence, could be refined
                )

                tables.append(table)
                logger.debug(
                    f"Detected table with {len(table_rows)} rows, {len(sorted_columns)} columns"
                )

        return tables

    def _extract_table_rows(self, column_groups: dict, sorted_columns: list[float]) -> list[dict]:
        """
        Extract structured rows from column groups.

        Args:
            column_groups: Text blocks grouped by x-coordinate
            sorted_columns: Sorted list of column x-coordinates

        Returns:
            List of structured row dictionaries
        """
        rows = []

        # Get all unique y-positions (potential rows)
        all_y_positions = []
        for blocks in column_groups.values():
            for block in blocks:
                y_pos = block["bbox"][1]
                all_y_positions.append(y_pos)

        # Group by y-position (rows)
        y_tolerance = 5
        row_groups = defaultdict(dict)

        for col_x in sorted_columns:
            col_blocks = column_groups[col_x]
            for block in col_blocks:
                y_pos = block["bbox"][1]
                y_grid = round(y_pos / y_tolerance) * y_tolerance

                # Store by row and column
                if y_grid not in row_groups:
                    row_groups[y_grid] = {}
                row_groups[y_grid][col_x] = block["text"].strip()

        # Convert to list of rows
        for y_pos in sorted(row_groups.keys()):
            row_data = row_groups[y_pos]
            if len(row_data) >= 2:  # Row must have at least 2 cells
                row = {"y_position": y_pos, "cells": row_data}
                rows.append(row)

        return rows

    def _extract_paragraphs(self, text_dict: dict, tables: list[TableRegion]) -> list[dict]:
        """
        Extract paragraph text that's not part of tables.

        Args:
            text_dict: PyMuPDF text dictionary
            tables: List of detected table regions

        Returns:
            List of paragraph dictionaries
        """
        paragraphs = []

        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # Text block
                block_bbox = block["bbox"]

                # Check if block overlaps with any table
                in_table = False
                for table in tables:
                    if self._bbox_overlap(block_bbox, table.bbox):
                        in_table = True
                        break

                if not in_table:
                    # Extract paragraph text
                    text_parts = []
                    for line in block.get("lines", []):
                        line_text = " ".join(span["text"] for span in line.get("spans", []))
                        if line_text.strip():
                            text_parts.append(line_text.strip())

                    if text_parts:
                        paragraphs.append({"text": " ".join(text_parts), "bbox": block_bbox})

        return paragraphs

    def _bbox_overlap(self, bbox1: tuple, bbox2: tuple) -> bool:
        """Check if two bounding boxes overlap."""
        x0_1, y0_1, x1_1, y1_1 = bbox1
        x0_2, y0_2, x1_2, y1_2 = bbox2

        return not (x1_1 < x0_2 or x1_2 < x0_1 or y1_1 < y0_2 or y1_2 < y0_1)

    def _table_to_dict(self, table: TableRegion) -> dict:
        """Convert TableRegion to dictionary for serialization."""
        return {
            "page_num": table.page_num,
            "bbox": table.bbox,
            "columns": table.columns,
            "rows": table.rows,
            "confidence": table.confidence,
        }

    def format_for_llm(self, structured_text: StructuredText) -> str:
        """
        Format structured text for LLM consumption.

        Args:
            structured_text: Extracted structured text

        Returns:
            Formatted string optimized for LLM understanding
        """
        formatted_parts = []

        for page in structured_text.pages:
            formatted_parts.append(f"\n=== PAGE {page['page_num']} ===\n")

            # Add paragraphs
            for para in page.get("paragraphs", []):
                formatted_parts.append(para["text"])
                formatted_parts.append("")  # Empty line

            # Add tables with structure
            for table in page.get("tables", []):
                formatted_parts.append("\n[TABLE]")

                # Format rows
                for row in table["rows"]:
                    cells = row["cells"]
                    # Order cells by column position
                    sorted_cols = sorted(cells.keys())
                    row_text = " | ".join(str(cells.get(col, "")) for col in sorted_cols)
                    formatted_parts.append(row_text)

                formatted_parts.append("[/TABLE]\n")

        return "\n".join(formatted_parts)
