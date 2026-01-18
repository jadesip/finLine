"""
finLine Document Extractor

Main extraction orchestrator using vision LLMs.
IMPORTANT: Must match FinForge's extraction behavior exactly.
Uses hybrid text+image extraction when text is available for accurate number parsing.
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

from config import get_settings, ExtractionConfig
from .file_handler import FileHandler
from .image_optimizer import ImageOptimizer
from .models import ExtractionMetadata, ExtractionResult
from .prompts import ExtractionPrompts
from .text_extractor import TextExtractor

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
            # Process file to images AND extract structured text (hybrid extraction)
            images, file_hash, file_metadata, structured_text = await self.file_handler.process_file(
                file_bytes, filename, store_original=True, extract_text=True
            )

            # Log hybrid extraction status
            if structured_text:
                logger.info(f"Hybrid extraction enabled: {len(structured_text.pages)} pages of text extracted")
            else:
                logger.info("Image-only extraction: no structured text available")

            # Optimize images
            optimized_images = []
            for i, img in enumerate(images):
                optimized = self.image_optimizer.optimize_for_extraction(img)
                optimized_images.append(optimized)
                logger.debug(f"Optimized image {i + 1}/{len(images)}")

            # Run extraction
            logger.info("Starting LLM extraction...")

            # Phase 1: Extract metadata from first few pages
            # Temperature: 0.1 (matches FinForge)
            metadata_response = await self._extract_with_vision(
                optimized_images[:3],
                ExtractionPrompts.get_metadata_prompt(),
                temperature=ExtractionConfig.TEMP_METADATA
            )

            # CRITICAL DEBUG: Log raw metadata response
            logger.info("=" * 80)
            logger.info("RAW LLM METADATA RESPONSE:")
            logger.info(metadata_response[:1500] if metadata_response else "EMPTY RESPONSE")
            logger.info("=" * 80)

            metadata = self._parse_json_response(metadata_response)

            # DETAILED METADATA DEBUG
            logger.info("=" * 80)
            logger.info("PARSED METADATA DEBUG:")
            logger.info(f"  Company: {metadata.get('company_name')}")
            logger.info(f"  Unit: {metadata.get('unit')}")
            logger.info(f"  Currency: {metadata.get('currency')}")
            logger.info(f"  Frequency: {metadata.get('frequency')}")
            logger.info(f"  Last Historical Period: {metadata.get('last_historical_period')}")
            logger.info(f"  All Years: {metadata.get('all_years')}")
            logger.info(f"  Number of Forecast Periods: {metadata.get('number_of_periods_forecast')}")
            logger.info("=" * 80)

            # Phase 2: Extract financial data
            # Temperature: 0.1 (matches FinForge)
            years = metadata.get("all_years", ["2024", "2025", "2026", "2027", "2028"])
            currency = metadata.get("currency", "USD")
            unit = metadata.get("unit", "millions")

            logger.info(f"Financial extraction params: years={years}, currency={currency}, unit={unit}")

            # Use hybrid prompt if structured text is available (key for correct number parsing)
            if structured_text and ExtractionConfig.USE_HYBRID_TEXT_IMAGE:
                logger.info("Using HYBRID text+image prompt for financial extraction")
                financial_prompt = ExtractionPrompts.get_hybrid_financial_data_prompt(
                    years, currency, unit, structured_text
                )
            else:
                logger.info("Using image-only prompt for financial extraction")
                financial_prompt = ExtractionPrompts.get_financial_data_prompt(years, currency, unit)

            financial_response = await self._extract_with_vision(
                optimized_images,
                financial_prompt,
                temperature=ExtractionConfig.TEMP_FINANCIAL_DATA
            )

            # CRITICAL DEBUG: Log raw LLM response before parsing
            logger.info("=" * 80)
            logger.info("RAW LLM FINANCIAL RESPONSE (first 2000 chars):")
            logger.info(financial_response[:2000] if financial_response else "EMPTY RESPONSE")
            logger.info("=" * 80)

            financial_data = self._parse_json_response(financial_response)

            # Log sample values for debugging - DETAILED
            income_stmt = financial_data.get("financials", {}).get("income_statement", {})
            sample_revenue = income_stmt.get("revenue", {})
            sample_ebitda = income_stmt.get("ebitda", {})

            logger.info("=" * 80)
            logger.info("PARSED FINANCIAL DATA DEBUG:")
            logger.info(f"  Unit from metadata: {unit}")
            logger.info(f"  Currency: {currency}")
            logger.info(f"  Years: {years}")
            logger.info(f"  Revenue values: {sample_revenue}")
            logger.info(f"  EBITDA values: {sample_ebitda}")

            # Check for division issue - log first numeric value
            for year, value in sample_revenue.items():
                if value is not None:
                    logger.info(f"  FIRST REVENUE VALUE: Year={year}, Value={value}, Type={type(value)}")
                    break
            logger.info("=" * 80)

            # Phase 3: Extract business insights
            # Use LangChain if enabled (matches FinForge behavior)
            insights_data = await self._extract_business_insights(
                optimized_images, structured_text, metadata
            )

            # Combine extracted data
            raw_data = {
                "metadata": metadata,
                "financials": financial_data.get("financials", {}),
                "deal_parameters": financial_data.get("deal_parameters", {}),
            }

            # Map to finLine schema
            mapped_data = self._map_to_finline_schema(raw_data)

            # CRITICAL DEBUG: Log mapped data
            logger.info("=" * 80)
            logger.info("FINAL MAPPED DATA DEBUG:")
            mapped_meta = mapped_data.get("meta", {})
            logger.info(f"  Meta.unit: {mapped_meta.get('unit')}")
            logger.info(f"  Meta.currency: {mapped_meta.get('currency')}")
            logger.info(f"  Meta.last_historical_period: {mapped_meta.get('last_historical_period')}")
            logger.info(f"  Meta.frequency: {mapped_meta.get('frequency')}")

            # Check financials in mapped data
            base_case = mapped_data.get("cases", {}).get("base_case", {})
            mapped_financials = base_case.get("financials", {})
            mapped_income = mapped_financials.get("income_statement", {})
            logger.info(f"  Mapped revenue: {mapped_income.get('revenue', {})}")
            logger.info(f"  Mapped ebitda: {mapped_income.get('ebitda', {})}")
            logger.info("=" * 80)

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

    async def _extract_business_insights(
        self, images: list[bytes], structured_text: Any, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Extract business insights using LangChain if enabled.
        Matches FinForge's behavior exactly.
        """
        logger.info(f"=== BUSINESS INSIGHTS EXTRACTION ===")
        logger.info(f"USE_LANGCHAIN_BUSINESS_INSIGHTS = {ExtractionConfig.USE_LANGCHAIN_BUSINESS_INSIGHTS}")

        if ExtractionConfig.USE_LANGCHAIN_BUSINESS_INSIGHTS:
            try:
                logger.info("Attempting LangChain import...")
                from .langchain_business_insights import LangChainBusinessInsights
                logger.info("LangChain import successful")

                logger.info("Initializing LangChainBusinessInsights...")
                langchain_extractor = LangChainBusinessInsights(self.api_key)
                logger.info("LangChainBusinessInsights initialized")

                logger.info("Starting LangChain extraction...")
                result = await langchain_extractor.extract(images, structured_text, metadata)
                logger.info(f"LangChain extraction returned: {type(result)}")
                logger.info(f"LangChain result keys: {result.keys() if result else 'None'}")

                if result:
                    logger.info("LangChain business insights extraction successful")
                    # LangChain returns {"data": {...}, "tokens": ...}, extract the data
                    data = result.get("data", {})
                    logger.info(f"LangChain data keys: {data.keys() if data else 'None'}")
                    # Structure the result to match expected format
                    return {
                        "information_extraction": data.get("information_extraction", {}),
                        "strategic_analysis": data.get("strategic_analysis", {}),
                    }
                else:
                    logger.warning("LangChain returned empty result")
            except ImportError as e:
                logger.error(f"LangChain import failed: {e}")
                logger.error("Make sure langchain and langchain-openai are installed")
            except Exception as e:
                logger.error(f"LangChain extraction failed with error: {type(e).__name__}: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")

        # Fallback to basic extraction (temperature 0.05 like FinForge)
        logger.info("Using basic extraction for business insights")
        insights_response = await self._extract_with_vision(
            images[:5],
            ExtractionPrompts.get_business_insights_prompt(metadata),
            temperature=ExtractionConfig.TEMP_BUSINESS_INSIGHTS
        )
        return self._parse_json_response(insights_response)

    async def _extract_with_vision(
        self, images: list[bytes], prompt: str, temperature: float = 0.1
    ) -> str:
        """Call vision LLM with images and prompt."""
        if self.provider == "openai":
            return await self._openai_vision(images, prompt, temperature)
        elif self.provider == "claude":
            return await self._claude_vision(images, prompt, temperature)
        elif self.provider == "gemini":
            return await self._gemini_vision(images, prompt, temperature)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    async def _openai_vision(
        self, images: list[bytes], prompt: str, temperature: float = 0.1
    ) -> str:
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

        logger.debug(f"OpenAI vision call: model={self.model}, temperature={temperature}")

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
                    "temperature": temperature,
                    "response_format": {"type": "json_object"}
                }
            )
            response.raise_for_status()
            data = response.json()

        return data["choices"][0]["message"]["content"]

    async def _claude_vision(
        self, images: list[bytes], prompt: str, temperature: float = 0.1
    ) -> str:
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

        logger.debug(f"Claude vision call: model={self.model}, temperature={temperature}")

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
                    "temperature": temperature,
                    "messages": [{"role": "user", "content": content}]
                }
            )
            response.raise_for_status()
            data = response.json()

        return data["content"][0]["text"]

    async def _gemini_vision(
        self, images: list[bytes], prompt: str, temperature: float = 0.1
    ) -> str:
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

        logger.debug(f"Gemini vision call: model={self.model}, temperature={temperature}")

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
                params={"key": self.api_key},
                json={
                    "contents": [{"parts": parts}],
                    "generationConfig": {
                        "temperature": temperature,
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

    def _normalize_frequency(self, frequency: str) -> str:
        """Normalize frequency values from LLM response."""
        freq_lower = frequency.lower().strip()
        if freq_lower in ("annually", "annual", "yearly", "year"):
            return "annual"
        elif freq_lower in ("quarterly", "quarter"):
            return "quarterly"
        elif freq_lower in ("monthly", "month"):
            return "monthly"
        return "annual"  # default

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

        # Normalize frequency value (annually -> annual, etc.)
        raw_frequency = metadata.get("frequency", "annual")
        frequency = self._normalize_frequency(raw_frequency)

        return {
            "meta": {
                "version": "1.0",
                "name": metadata.get("company_name", "Extracted Project"),
                "company_name": metadata.get("company_name", ""),
                "currency": metadata.get("currency", "USD"),
                "unit": metadata.get("unit", "millions"),
                "frequency": frequency,
                "financial_year_end": metadata.get("financial_year_end", "December"),
                "last_historical_period": metadata.get("last_historical_period", ""),
                "number_of_periods_forecast": metadata.get("number_of_periods_forecast", 3),
                "naics_sector": metadata.get("naics_sector", ""),
                "naics_subsector": metadata.get("naics_subsector", ""),
                "country_of_operations": metadata.get("country_of_operations", ""),
                "country_of_headquarters": metadata.get("country_of_headquarters", ""),
            },
            "cases": {
                "base_case": case_data
            }
        }
