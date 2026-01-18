"""
Extraction prompts for financial data using simplified v2 template.
Ported from finForge - DO NOT MODIFY these prompts without testing.
"""

import json
from typing import Any


class ExtractionPrompts:
    """
    Manages prompts for financial data extraction.

    Uses simplified v2 template format - all years together, no cases.
    Supports both image-only and hybrid text+image extraction.
    """

    @staticmethod
    def get_metadata_prompt() -> str:
        """
        Get prompt for extracting document metadata.

        Returns:
            Metadata extraction prompt
        """
        return """
Extract the following information from this financial document and return as JSON:

{
    "company_name": "Exact company name from document",
    "currency": "USD",  // Three-letter code (USD, EUR, GBP, etc.)
    "unit": "millions",  // millions, thousands, billions, or unit
    "frequency": "annually",  // annually, quarterly, or monthly
    "financial_year_end": "December",  // Full month name only
    "last_historical_period": "Dec-24",  // Last actual data period Mon-YY
    "naics_sector": "Information",  // Best guess if not stated
    "naics_subsector": "Software Publishers",  // Best guess if not stated
    "country_of_operations": "United States",  // Default if not stated
    "country_of_headquarters": "United States",  // Default if not stated
    "document_type": "financial_statement",  // or annual_report, cim, pitch_deck
    "all_years": ["2022", "2023", "2024", "2025", "2026", "2027", "2028"],  // ALL years in document
    "number_of_periods_forecast": 4,  // Count of forecast years
    "da_present_in_pl": 0  // CRITICAL: Set to 1 if Depreciation & Amortization (D&A) appears as a separate line item in the P&L/Income Statement, 0 otherwise
}

IMPORTANT:
- Look for currency symbols: $ = USD, € = EUR, £ = GBP
- Check table headers for units (millions, $M, 000s)
- Extract ALL years that have data (both historical and forecast)
- Count how many years are projections/forecasts
- For da_present_in_pl: Check if D&A/Depreciation is shown as its own line in the P&L statement
- Only if Depreciation and amortisation (D&A) is not available in the income statement (preferred), then check the cash flow statement

"""

    @staticmethod
    def get_financial_data_prompt(years: list[str], currency: str, unit: str) -> str:
        """
        Get prompt for extracting ALL financial data (historical + forecast).

        Args:
            years: List of all years to extract
            currency: Currency code
            unit: Unit (millions, thousands, etc.)

        Returns:
            Financial data extraction prompt
        """
        return f"""
Extract financial data from the document for years: {", ".join(years)}.

Return the data EXACTLY as shown in the document in JSON format (values in {currency} {unit}):

{{
    "financials": {{
        "income_statement": {{
            "revenue": {{
                "2022": 80.0,
                "2023": 100.0,
                "2024": 120.0,
                "2025": 150.0,
                "2026": 180.0,
                "2027": 220.0,
                "2028": 260.0
            }},
            "cogs": {{
                "2022": 32.0,
                "2023": 40.0,
                "2024": 48.0,
                "2025": 60.0,
                "2026": 72.0,
                "2027": 88.0,
                "2028": 104.0
            }},
            "opex": {{
                "2022": 28.0,
                "2023": 35.0,
                "2024": 42.0,
                "2025": 52.5,
                "2026": 63.0,
                "2027": 77.0,
                "2028": 91.0
            }},
            "ebitda": {{
                "2022": 20.0,
                "2023": 25.0,
                "2024": 30.0,
                "2025": 37.5,
                "2026": 45.0,
                "2027": 55.0,
                "2028": 65.0
            }},
            "d&a": {{
                "2022": 6.4,
                "2023": 8.0,
                "2024": 9.6,
                "2025": 12.0,
                "2026": 14.4,
                "2027": 17.6,
                "2028": 20.8
            }},
            "ebit": {{
                "2022": 13.6,
                "2023": 17.0,
                "2024": 20.4,
                "2025": 25.5,
                "2026": 30.6,
                "2027": 37.4,
                "2028": 44.2
            }},
            "interest_expense": {{
                "2022": 4.0,
                "2023": 5.0,
                "2024": 6.0,
                "2025": 7.5,
                "2026": 9.0,
                "2027": 11.0,
                "2028": 13.0
            }},
            "profit_before_tax": {{
                "2022": 9.6,
                "2023": 12.0,
                "2024": 14.4,
                "2025": 18.0,
                "2026": 21.6,
                "2027": 26.4,
                "2028": 31.2
            }},
            "tax": {{
                "2022": 2.4,
                "2023": 3.0,
                "2024": 3.6,
                "2025": 4.5,
                "2026": 5.4,
                "2027": 6.6,
                "2028": 7.8
            }},
            "net_income": {{
                "2022": 7.2,
                "2023": 9.0,
                "2024": 10.8,
                "2025": 13.5,
                "2026": 16.2,
                "2027": 19.8,
                "2028": 23.4
            }}
        }},
        "balance_sheet": {{
            "cash": {{
                "2022": 12.0,
                "2023": 15.0,
                "2024": 18.0,
                "2025": 22.5,
                "2026": 27.0,
                "2027": 33.0,
                "2028": 39.0
            }},
            "working_capital": {{
                "2022": 16.0,
                "2023": 20.0,
                "2024": 24.0,
                "2025": 30.0,
                "2026": 36.0,
                "2027": 44.0,
                "2028": 52.0
            }},
            "receivables": {{
                "2022": 10.0,
                "2023": 12.0,
                "2024": 13.8,
                "2025": 15.6,
                "2026": 17.4,
                "2027": 19.2,
                "2028": 21.0
            }},
            "inventory": {{
                "2022": 6.5,
                "2023": 8.0,
                "2024": 9.2,
                "2025": 10.4,
                "2026": 11.6,
                "2027": 12.8,
                "2028": 14.0
            }},
            "payables": {{
                "2022": 4.5,
                "2023": 6.0,
                "2024": 6.9,
                "2025": 7.8,
                "2026": 8.7,
                "2027": 9.6,
                "2028": 10.5
            }},
            "ppe": {{
                "2022": 75.0,
                "2023": 80.0,
                "2024": 85.0,
                "2025": 90.0,
                "2026": 95.0,
                "2027": 100.0,
                "2028": 105.0
            }},
            "total_assets": {{
                "2022": 103.0,
                "2023": 115.0,
                "2024": 127.0,
                "2025": 142.5,
                "2026": 158.0,
                "2027": 177.0,
                "2028": 196.0
            }},
            "total_debt": {{
                "2022": 40.0,
                "2023": 50.0,
                "2024": 60.0,
                "2025": 75.0,
                "2026": 90.0,
                "2027": 110.0,
                "2028": 130.0
            }},
            "shareholders_equity": {{
                "2022": 63.0,
                "2023": 65.0,
                "2024": 67.0,
                "2025": 67.5,
                "2026": 68.0,
                "2027": 67.0,
                "2028": 66.0
            }},
            "total_liabilities_equity": {{
                "2022": 103.0,
                "2023": 115.0,
                "2024": 127.0,
                "2025": 142.5,
                "2026": 158.0,
                "2027": 177.0,
                "2028": 196.0
            }}
        }},
        "cash_flow_statement": {{
            "capex": {{
                "2022": 9.6,
                "2023": 12.0,
                "2024": 14.4,
                "2025": 18.0,
                "2026": 21.6,
                "2027": 26.4,
                "2028": 31.2
            }}
        }}
    }},
    "deal_parameters": {{
        "tax_rate": 0.25  // Extract if shown (as decimal)
    }}
}}

IMPORTANT:
- Extract values EXACTLY as shown in the document
- If a line item exists but value is missing, use null
- Only if Depreciation and amortisation (D&A) is not available in the income statement (preferred), then check the cash flow statement
- Include working capital breakdown (receivables/inventory/payables) only if shown
- For values shown as "150" in millions, extract as 150.0
"""

    @staticmethod
    def get_hybrid_metadata_prompt(structured_text: Any) -> str:
        """
        Get prompt for extracting metadata using both text and images.

        Args:
            structured_text: Extracted text structure from PDF

        Returns:
            Hybrid metadata extraction prompt
        """
        # Format the structured text
        formatted_text = ""

        if hasattr(structured_text, "pages"):
            # Extract key text from first few pages
            for page in structured_text.pages[:2]:  # First 2 pages
                formatted_text += f"\n--- Page {page['page_num']} ---\n"
                formatted_text += page.get("raw_text", "")[:1000]  # First 1000 chars
        else:
            # Fallback if structured_text has different format
            formatted_text = str(structured_text)[:2000]

        return f"""
Extract metadata from this financial document using BOTH the extracted text and images.

EXTRACTED TEXT (for precise reading):
{formatted_text}

USE THE IMAGES BELOW to:
1. Verify the text extraction is accurate
2. Identify any information not captured in the text
3. Understand table layouts and relationships

Return the following information as JSON:

{{
    "company_name": "Exact company name from document",
    "currency": "USD",  // Three-letter code (USD, EUR, GBP, etc.)
    "unit": "millions",  // millions, thousands, billions, or unit
    "frequency": "annually",  // annually, quarterly, or monthly
    "financial_year_end": "December",  // Full month name only
    "last_historical_period": "Dec-24",  // Last actual data period Mon-YY
    "naics_sector": "Information",  // Best guess if not stated
    "naics_subsector": "Software Publishers",  // Best guess if not stated
    "country_of_operations": "United States",  // Default if not stated
    "country_of_headquarters": "United States",  // Default if not stated
    "document_type": "financial_statement",  // or annual_report, cim, pitch_deck
    "all_years": ["2022", "2023", "2024", "2025", "2026", "2027", "2028"],  // ALL years in document
    "number_of_periods_forecast": 4,  // Count of forecast years
    "da_present_in_pl": 0  // CRITICAL: Set to 1 if Depreciation & Amortization (D&A) appears as a separate line item in the P&L/Income Statement, 0 otherwise
}}

IMPORTANT:
- Use the extracted text for precise values
- Use the images to verify and understand context
- For da_present_in_pl: Check if D&A/Depreciation is shown as its own line in the P&L statement
- Look for currency symbols: $ = USD, € = EUR, £ = GBP
- Check table headers for units (millions, $M, 000s)
- Extract ALL years that have data (both historical and forecast)
"""

    @staticmethod
    def get_hybrid_financial_data_prompt(
        years: list[str], currency: str, unit: str, structured_text: Any
    ) -> str:
        """
        Get prompt for extracting financial data using both text and images.

        Args:
            years: List of all years to extract
            currency: Currency code
            unit: Unit (millions, thousands, etc.)
            structured_text: Extracted text structure from PDF

        Returns:
            Hybrid financial data extraction prompt
        """
        # Format structured text focusing on tables
        formatted_text = ""

        if hasattr(structured_text, "format_for_llm"):
            # Use the built-in formatter
            formatted_text = structured_text.format_for_llm()
        elif hasattr(structured_text, "pages"):
            # Manual formatting with advanced table support
            for page in structured_text.pages:
                formatted_text += f"\n=== PAGE {page['page_num']} ===\n"

                # Prefer advanced extracted tables if available
                if "advanced_tables" in page:
                    for adv_table in page["advanced_tables"]:
                        formatted_text += f"\n[EXTRACTED TABLE - {adv_table.table_type.upper()}]\n"
                        formatted_text += f"Method: {adv_table.extraction_method}\n"
                        formatted_text += f"Confidence: {adv_table.confidence:.1%}\n"
                        formatted_text += f"Headers: {' | '.join(adv_table.headers)}\n"
                        formatted_text += "-" * 50 + "\n"

                        # Add table data (first 10 rows to avoid context overflow)
                        for idx, row in adv_table.df.head(10).iterrows():
                            row_text = " | ".join(str(val) for val in row if str(val).strip())
                            if row_text.strip():
                                formatted_text += row_text + "\n"
                        formatted_text += "[/EXTRACTED TABLE]\n\n"
                else:
                    # Fallback to basic table format
                    for table in page.get("tables", []):
                        formatted_text += "\n[TABLE]\n"
                        for row in table.get("rows", []):
                            cells = row.get("cells", {})
                            row_text = " | ".join(str(v) for v in cells.values())
                            formatted_text += row_text + "\n"
                        formatted_text += "[/TABLE]\n"

        return f"""
Extract financial data for years: {", ".join(years)} using BOTH text and images.

EXTRACTED TEXT WITH TABLE STRUCTURE:
{formatted_text[:3000]}...  # Truncated for context window

USE THE IMAGES BELOW to:
1. Verify table layouts and column alignments
2. Resolve any ambiguities in the text extraction
3. Find data that may have been missed in text extraction

Return the data EXACTLY as shown in the document in JSON format (values in {currency} {unit}):

{{
    "financials": {{
        "income_statement": {{
            "revenue": {{"2023": 100.0, "2024": 120.0, ...}},
            "cogs": {{...}},
            "opex": {{...}},
            "ebitda": {{...}},
            "d&a": {{...}},
            "ebit": {{...}},
            "interest_expense": {{...}},
            "profit_before_tax": {{...}},
            "tax": {{...}},
            "net_income": {{...}}
        }},
        "balance_sheet": {{
            "cash": {{...}},
            "working_capital": {{...}},
            "receivables": {{...}},  // Optional if shown
            "inventory": {{...}},     // Optional if shown
            "payables": {{...}},      // Optional if shown
            "ppe": {{...}},
            "total_assets": {{...}},
            "total_debt": {{...}},
            "shareholders_equity": {{...}},
            "total_liabilities_equity": {{...}}
        }},
        "cash_flow_statement": {{
            "d&a": {{...}},
            "capex": {{...}}
        }}
    }},
    "deal_parameters": {{
        "tax_rate": 0.25  // Extract if shown (as decimal)
    }}
}}

IMPORTANT:
- I've pre-extracted tables using ML-based detection - USE THIS DATA FIRST
- The extracted tables are already structured with proper headers and values
- Use images primarily to verify and fill gaps in the extracted data
- If extracted table data conflicts with images, trust the images
- Extract values EXACTLY as shown in the document
- If a line item exists but value is missing, use null
- For values shown as "150" in millions, extract as 150.0

PRIORITY ORDER:
1. Use extracted table data as the primary source
2. Cross-reference with images for verification
3. Fill any missing data from images
4. Flag any discrepancies between extracted and visual data
"""

    @staticmethod
    def get_business_insights_prompt(metadata: dict[str, Any] | None = None) -> str:
        """Get prompt for business and operations analysis (Request 3A)."""
        # Build context from metadata if available
        context_info = ""
        if metadata:
            company = metadata.get("company_name", "Unknown")
            industry = metadata.get("industry", "")
            currency = metadata.get("currency", "")
            if company and company != "Unknown":
                context_info = f"\n\nCONTEXT FROM PREVIOUS ANALYSIS:\n- Company Name: {company}"
                if industry:
                    context_info += f"\n- Industry/Sector: {industry}"
                if currency:
                    context_info += f"\n- Currency: {currency}"
                context_info += "\n\nPlease ensure all analysis is consistent with this company context."

        prompt = {
            "role": "You are a financial analyst extracting business intelligence from documents.",
            "instruction": f"Extract ONLY information explicitly stated in the provided documents. Do not use external knowledge or make assumptions. Use 'Not specified in documents' for missing data. Return the results in JSON format.{context_info}",
            "temperature_note": "Using temperature 0.05 for maximum factual accuracy",
            "required_extraction": {
                "business_description": {
                    "summary": "2-3 paragraph description of core business activities",
                    "source_pages": "List page numbers where found",
                    "confidence": "high|medium|low",
                },
                "revenue_model": {
                    "key_products_services": "List of main offerings",
                    "revenue_streams": "List of ways company generates revenue (return as array)",
                    "customer_segments": "Target customers/market segments",
                    "geographic_markets": "Key regions/countries",
                    "business_segments": [
                        {
                            "name": "Segment name",
                            "description": "What this segment does",
                            "revenue_contribution": "% or amount if available",
                        }
                    ],
                },
                "cost_structure": {
                    "fixed_costs": "List of fixed cost categories",
                    "variable_costs": "List of variable cost categories",
                    "key_cost_drivers": "Major expense drivers",
                    "operating_leverage": "Assessment if mentioned",
                },
                "capital_requirements": {
                    "capex_types": "Types of capital expenditure",
                    "capital_intensity": "high|medium|low|unknown",
                    "key_assets": "Major assets driving business",
                    "investment_focus": "Where capex is directed",
                },
                "management_team": [
                    {
                        "name": "Full name",
                        "position": "Title/role",
                        "age": "Number if specified",
                        "tenure": "Time in role if mentioned",
                        "career_summary": "Brief background",
                        "linkedin_profile": "URL if provided in document",
                        "previous_roles": "List of prior positions",
                        "board_member": "true|false",
                    }
                ],
            },
            "important_notes": [
                "Extract ONLY from the uploaded documents",
                "Include page references where possible",
                "Use null/empty for unavailable information",
                "Flag uncertain data with lower confidence scores",
            ],
        }
        return json.dumps(prompt, indent=2)

    @staticmethod
    def get_strategic_analysis_prompt(metadata: dict[str, Any] | None = None) -> str:
        """Get prompt for strategic and risk analysis (Request 3B)."""
        # Build context from metadata if available
        context_info = ""
        if metadata:
            company = metadata.get("company_name", "Unknown")
            industry = metadata.get("industry", "")
            if company and company != "Unknown":
                context_info = f"\n\nCONTEXT FROM PREVIOUS ANALYSIS:\n- Company Name: {company}"
                if industry:
                    context_info += f"\n- Industry/Sector: {industry}"
                context_info += "\n\nPlease ensure all strategic analysis is specific to this company."

        prompt = {
            "role": "You are a financial analyst performing strategic and risk analysis.",
            "instruction": f"Extract ONLY information explicitly stated in the provided documents. Focus on factual content without interpretation beyond what is directly stated. Return the results in JSON format.{context_info}",
            "temperature_note": "Using temperature 0.08 for strategic analysis",
            "required_extraction": {
                "strategy": {
                    "business_strategy": "Stated strategic direction",
                    "competitive_positioning": "Market position if mentioned",
                    "differentiation": "Competitive advantages noted",
                    "growth_initiatives": "List of expansion plans/projects (return as array)",
                },
                "swot_analysis": {
                    "strengths": "List based on performance/capabilities",
                    "weaknesses": "Identified challenges/gaps",
                    "opportunities": "Growth prospects mentioned",
                    "threats": "Risk factors or market challenges",
                },
                "industry_context": {
                    "market_characteristics": "Industry dynamics if described",
                    "growth_trends": "Market growth rates/trends",
                    "regulatory_factors": "Compliance/regulatory items",
                    "competitive_dynamics": "Competitor information",
                    "industry_reports": "Names of reports mentioned",
                },
                "recent_events": [
                    {
                        "date": "When it occurred",
                        "event_type": "M&A|Contract|Operational|Financial|Management|Other",
                        "description": "What happened",
                        "impact": "Effect on business if stated",
                    }
                ],
                "risk_analysis": {
                    "revenue_concentration": {
                        "flag": "true if any client >30% revenue",
                        "details": "Specific concentration details",
                        "top_client_percentage": "% if specified",
                    },
                    "liquidity_concerns": {
                        "flag": "true if low cash/short runway",
                        "cash_runway": "Months/timeline if mentioned",
                        "details": "Specific concerns",
                    },
                    "related_party_transactions": {
                        "flag": "true if found",
                        "transactions": "List of transactions",
                        "source": "Where found (e.g., footnotes)",
                    },
                    "governance_issues": {
                        "flag": "true if issues found",
                        "issues": "List (dual-class, audit remarks, etc.)",
                        "details": "Specific concerns",
                    },
                    "strategic_inconsistencies": {
                        "flag": "true if conflicting plans",
                        "inconsistencies": "List of conflicts",
                    },
                    "financial_red_flags": {
                        "flag": "true if found",
                        "flags": "List (accounting issues, covenant breaches)",
                        "details": "Specific concerns",
                    },
                    "operational_risks": {
                        "flag": "true if risks identified",
                        "risks": "List (key person, regulatory, etc.)",
                    },
                    "market_risks": {
                        "flag": "true if risks identified",
                        "risks": "List (competition, disruption, etc.)",
                    },
                    "overall_risk_assessment": "low|medium|high|critical",
                },
            },
            "extraction_guidelines": [
                "Base SWOT on document evidence only",
                "Flag risks based on explicit mentions or clear data patterns",
                "Include competitor websites only if mentioned in documents",
                "Note industry report titles/dates for user reference",
                "3-year lookback for events from document date",
            ],
        }
        return json.dumps(prompt, indent=2)
