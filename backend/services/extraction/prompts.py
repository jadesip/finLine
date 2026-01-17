"""
Extraction prompts for financial data.
Simplified for finLine schema.
"""

import json
from typing import Any


class ExtractionPrompts:
    """Manages prompts for financial data extraction."""

    @staticmethod
    def get_metadata_prompt() -> str:
        """Get prompt for extracting document metadata."""
        return """
Extract the following information from this financial document and return as JSON:

{
    "company_name": "Exact company name from document",
    "currency": "USD",  // Three-letter code (USD, EUR, GBP, etc.)
    "unit": "millions",  // millions, thousands, billions, or unit
    "frequency": "annual",  // annual, quarterly, or monthly
    "financial_year_end": "December",  // Full month name only
    "industry": "Technology",  // Industry/sector
    "all_years": ["2022", "2023", "2024", "2025", "2026", "2027", "2028"],  // ALL years in document
    "number_of_periods_forecast": 4  // Count of forecast years
}

IMPORTANT:
- Look for currency symbols: $ = USD, € = EUR, £ = GBP
- Check table headers for units (millions, $M, 000s)
- Extract ALL years that have data (both historical and forecast)
"""

    @staticmethod
    def get_financial_data_prompt(years: list[str], currency: str, unit: str) -> str:
        """Get prompt for extracting financial data."""
        return f"""
Extract financial data from the document for years: {", ".join(years)}.

Return the data EXACTLY as shown in the document in JSON format (values in {currency} {unit}):

{{
    "financials": {{
        "income_statement": {{
            "revenue": [
                {{"year": "2024", "value": 100.0}},
                {{"year": "2025", "value": 120.0}}
            ],
            "ebitda": [
                {{"year": "2024", "value": 25.0}},
                {{"year": "2025", "value": 30.0}}
            ],
            "ebit": [
                {{"year": "2024", "value": 20.0}},
                {{"year": "2025", "value": 24.0}}
            ],
            "d_and_a": [
                {{"year": "2024", "value": 5.0}},
                {{"year": "2025", "value": 6.0}}
            ]
        }},
        "cash_flow_statement": {{
            "capex": {{
                "values": [
                    {{"year": "2024", "value": 10.0}},
                    {{"year": "2025", "value": 12.0}}
                ]
            }},
            "working_capital": {{
                "values": [
                    {{"year": "2024", "value": 15.0}},
                    {{"year": "2025", "value": 18.0}}
                ]
            }}
        }}
    }},
    "deal_parameters": {{
        "tax_rate": 0.25
    }}
}}

IMPORTANT:
- Extract values EXACTLY as shown in the document
- Use the array format shown above with year/value pairs
- If a line item exists but value is missing, use null
- For values shown as "150" in millions, extract as 150.0
"""

    @staticmethod
    def get_business_insights_prompt(metadata: dict[str, Any] | None = None) -> str:
        """Get prompt for business insights extraction."""
        context = ""
        if metadata:
            company = metadata.get("company_name", "Unknown")
            industry = metadata.get("industry", "")
            if company != "Unknown":
                context = f"\n\nCompany: {company}"
                if industry:
                    context += f"\nIndustry: {industry}"

        return f"""
Extract business intelligence from this document.{context}

Return as JSON:
{{
    "business_description": {{
        "summary": "2-3 paragraph description of the business",
        "confidence": "high|medium|low"
    }},
    "revenue_model": {{
        "key_products_services": ["Product 1", "Product 2"],
        "revenue_streams": ["Revenue type 1", "Revenue type 2"],
        "customer_segments": ["Segment 1", "Segment 2"],
        "geographic_markets": ["Region 1", "Region 2"]
    }},
    "management_team": [
        {{
            "name": "John Doe",
            "position": "CEO",
            "background": "Brief background"
        }}
    ],
    "strategy": {{
        "business_strategy": "Strategic direction",
        "competitive_positioning": "Market position",
        "growth_initiatives": ["Initiative 1", "Initiative 2"]
    }},
    "risks": {{
        "key_risks": ["Risk 1", "Risk 2"],
        "risk_level": "low|medium|high"
    }}
}}

Extract ONLY information explicitly stated in the document.
"""

    @staticmethod
    def get_combined_extraction_prompt(years: list[str], currency: str, unit: str) -> str:
        """Get combined prompt for single-pass extraction."""
        return f"""
You are a financial data extraction expert. Extract ALL financial information from this document.

DOCUMENT CONTEXT:
- Currency: {currency}
- Unit: {unit}
- Years to extract: {", ".join(years)}

Return a JSON object with this EXACT structure:

{{
    "metadata": {{
        "company_name": "Company name from document",
        "currency": "{currency}",
        "unit": "{unit}",
        "industry": "Industry/sector",
        "all_years": {json.dumps(years)}
    }},
    "financials": {{
        "income_statement": {{
            "revenue": [{{"year": "2024", "value": 100.0}}, ...],
            "ebitda": [{{"year": "2024", "value": 25.0}}, ...],
            "ebit": [{{"year": "2024", "value": 20.0}}, ...],
            "d_and_a": [{{"year": "2024", "value": 5.0}}, ...]
        }},
        "cash_flow_statement": {{
            "capex": {{"values": [{{"year": "2024", "value": 10.0}}, ...]}},
            "working_capital": {{"values": [{{"year": "2024", "value": 15.0}}, ...]}}
        }}
    }},
    "deal_parameters": {{
        "tax_rate": 0.25
    }},
    "business_insights": {{
        "summary": "Brief business description",
        "key_products": ["Product 1", "Product 2"],
        "markets": ["Market 1", "Market 2"]
    }}
}}

CRITICAL INSTRUCTIONS:
1. Extract values EXACTLY as shown in the document
2. Use the array format with year/value pairs
3. Include ALL years that have data
4. Use null for missing values
5. Return ONLY valid JSON - no markdown, no comments
"""
