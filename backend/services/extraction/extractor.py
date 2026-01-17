"""
finLine Document Extractor

Main extraction orchestrator using vision LLMs.
"""

import base64
import json
import logging
import re
import time
import uuid
from datetime import datetime
from typing import Any

import httpx

from config import get_settings
from .file_handler import FileHandler
from .image_optimizer import ImageOptimizer
from .models import ExtractionMetadata, ExtractionResult
from .prompts import ExtractionPrompts

logger = logging.getLogger(__name__)
settings = get_settings()


class DocumentExtractor:
    """
    Orchestrates financial data extraction from documents.

    Uses vision LLMs (OpenAI GPT-4o, Claude, Gemini) to extract
    financial data from PDFs and images.
    """

    def __init__(self, upload_dir: str = "uploads"):
        self.file_handler = FileHandler(upload_dir)
        self.image_optimizer = ImageOptimizer()
        self.provider = settings.llm_provider
        self.model = settings.llm_model
        self.api_key = settings.llm_api_key

        logger.info(f"DocumentExtractor initialized with {self.provider}/{self.model}")

    async def extract_from_file(
        self,
        file_bytes: bytes,
        filename: str,
        extraction_id: str | None = None,
    ) -> ExtractionResult:
        """
        Extract financial data from uploaded file.

        Args:
            file_bytes: Raw file content
            filename: Original filename
            extraction_id: Optional extraction ID

        Returns:
            Complete extraction result
        """
        start_time = time.time()
        extraction_id = extraction_id or str(uuid.uuid4())

        file_size_mb = len(file_bytes) / (1024 * 1024)
        logger.info(f"Starting extraction {extraction_id} for {filename} ({file_size_mb:.2f}MB)")

        try:
            # Process file to images
            images, file_hash, file_metadata = await self.file_handler.process_file(
                file_bytes, filename, store_original=True
            )

            # Optimize images
            optimized_images = []
            for i, img in enumerate(images):
                optimized = self.image_optimizer.optimize_for_extraction(img)
                optimized_images.append(optimized)
                logger.debug(f"Optimized image {i + 1}/{len(images)}")

            # Run extraction
            logger.info("Starting LLM extraction...")

            # Phase 1: Extract metadata from first few pages
            metadata_response = await self._extract_with_vision(
                optimized_images[:3],
                ExtractionPrompts.get_metadata_prompt()
            )
            metadata = self._parse_json_response(metadata_response)
            logger.info(f"Extracted metadata: company={metadata.get('company_name')}")

            # Phase 2: Extract financial data
            years = metadata.get("all_years", ["2024", "2025", "2026", "2027", "2028"])
            currency = metadata.get("currency", "USD")
            unit = metadata.get("unit", "millions")

            financial_response = await self._extract_with_vision(
                optimized_images,
                ExtractionPrompts.get_financial_data_prompt(years, currency, unit)
            )
            financial_data = self._parse_json_response(financial_response)

            # Phase 3: Extract business insights
            insights_response = await self._extract_with_vision(
                optimized_images[:5],
                ExtractionPrompts.get_business_insights_prompt(metadata)
            )
            insights_data = self._parse_json_response(insights_response)

            # Combine extracted data
            raw_data = {
                "metadata": metadata,
                "financials": financial_data.get("financials", {}),
                "deal_parameters": financial_data.get("deal_parameters", {}),
            }

            # Map to finLine schema
            mapped_data = self._map_to_finline_schema(raw_data)

            extraction_time = time.time() - start_time
            logger.info(f"Extraction completed in {extraction_time:.2f}s")

            return ExtractionResult(
                raw_data=raw_data,
                mapped_data=mapped_data,
                conflicts=[],
                confidence_scores={"overall": 0.85},
                metadata=ExtractionMetadata(
                    extraction_id=extraction_id,
                    timestamp=datetime.now(),
                    file_name=filename,
                    file_type=file_metadata["file_type"],
                    file_size_mb=file_metadata["file_size_mb"],
                    provider=self.provider,
                    model=self.model,
                    total_tokens=0,
                    extraction_time_seconds=extraction_time,
                ),
                insights_data=insights_data,
                status="complete"
            )

        except Exception as e:
            logger.error(f"Extraction failed: {e}", exc_info=True)
            raise

    async def _extract_with_vision(self, images: list[bytes], prompt: str) -> str:
        """Call vision LLM with images and prompt."""
        if self.provider == "openai":
            return await self._openai_vision(images, prompt)
        elif self.provider == "claude":
            return await self._claude_vision(images, prompt)
        elif self.provider == "gemini":
            return await self._gemini_vision(images, prompt)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    async def _openai_vision(self, images: list[bytes], prompt: str) -> str:
        """OpenAI GPT-4o vision API call."""
        content = [{"type": "text", "text": prompt}]

        for img_bytes in images:
            base64_image = base64.b64encode(img_bytes).decode("utf-8")
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}",
                    "detail": "high"
                }
            })

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model if "gpt" in self.model else "gpt-4o",
                    "messages": [{"role": "user", "content": content}],
                    "max_tokens": 4096,
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                }
            )
            response.raise_for_status()
            data = response.json()

        return data["choices"][0]["message"]["content"]

    async def _claude_vision(self, images: list[bytes], prompt: str) -> str:
        """Anthropic Claude vision API call."""
        content = []

        for img_bytes in images:
            base64_image = base64.b64encode(img_bytes).decode("utf-8")
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": base64_image
                }
            })

        content.append({"type": "text", "text": prompt})

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model if "claude" in self.model else "claude-3-5-sonnet-20241022",
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": content}]
                }
            )
            response.raise_for_status()
            data = response.json()

        return data["content"][0]["text"]

    async def _gemini_vision(self, images: list[bytes], prompt: str) -> str:
        """Google Gemini vision API call."""
        parts = [{"text": prompt}]

        for img_bytes in images:
            base64_image = base64.b64encode(img_bytes).decode("utf-8")
            parts.append({
                "inline_data": {
                    "mime_type": "image/png",
                    "data": base64_image
                }
            })

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
                params={"key": self.api_key},
                json={
                    "contents": [{"parts": parts}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 4096
                    }
                }
            )
            response.raise_for_status()
            data = response.json()

        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "")

        return "{}"

    def _parse_json_response(self, text: str) -> dict[str, Any]:
        """Parse JSON from LLM response."""
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Try to find JSON in markdown code block
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object anywhere
        brace_match = re.search(r'\{[\s\S]*\}', text)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        logger.warning(f"Could not parse JSON from response: {text[:200]}...")
        return {}

    def _map_to_finline_schema(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Map extracted data to finLine project schema."""
        metadata = raw_data.get("metadata", {})
        financials = raw_data.get("financials", {})
        deal_params = raw_data.get("deal_parameters", {})

        # Build finLine case structure
        case_data = {
            "case_desc": "Base Case",
            "deal_parameters": {
                "deal_date": "2024-12-31",
                "exit_date": "2029-12-31",
                "tax_rate": deal_params.get("tax_rate", 0.25),
                "minimum_cash": 0.0,
                "entry_fee_percentage": 2.0,
                "exit_fee_percentage": 2.0,
                "entry_valuation": {
                    "method": "multiple",
                    "metric": "EBITDA",
                    "multiple": 8.0
                },
                "exit_valuation": {
                    "method": "multiple",
                    "metric": "EBITDA",
                    "multiple": 8.0
                },
                "capital_structure": {
                    "tranches": [],
                    "reference_rate_curve": None
                },
                "equity_injection": None
            },
            "financials": financials
        }

        return {
            "meta": {
                "version": "1.0",
                "name": metadata.get("company_name", "Extracted Project"),
                "company_name": metadata.get("company_name", ""),
                "currency": metadata.get("currency", "USD"),
                "unit": metadata.get("unit", "millions"),
                "frequency": metadata.get("frequency", "annual"),
                "financial_year_end": metadata.get("financial_year_end", "December"),
            },
            "cases": {
                "base_case": case_data
            }
        }
