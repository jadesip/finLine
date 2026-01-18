"""
LangChain-specific prompts for business insights extraction.
Ported from finForge - DO NOT MODIFY these prompts without testing.

These prompts are SEPARATE from the main prompts.py file.
They are optimized for sequential extraction with context passing.
"""


class LangChainPrompts:
    """Prompts specifically designed for LangChain sequential extraction."""

    @staticmethod
    def get_company_identification_prompt() -> str:
        """First step: Identify the company clearly."""
        return """You are analyzing financial documents to identify the company.

PRIORITY TASKS:
1. Find the exact legal entity name (check headers, footers, "Consolidated Statements of [Company]")
2. Identify the company website if mentioned
3. Determine if it's a public company (look for ticker symbols)
4. Identify the primary industry/sector

Document excerpt:
{document}

Return ONLY a JSON object with this structure:
{{
    "company_name": "Exact legal name (e.g., 'Alphabet Inc.')",
    "website": "Company website if found",
    "ticker_symbol": "Stock ticker if public",
    "is_public": true,
    "industry": "Primary industry sector",
    "parent_company": "Parent company if subsidiary",
    "identification_confidence": "high"
}}

IMPORTANT: Be very specific with the company name - use the full legal name.
Note: Use boolean true/false, not strings."""

    @staticmethod
    def get_business_model_prompt() -> str:
        """Second step: Extract business model details."""
        return """You are extracting business model information for the identified company.

Company Information:
{company_info}

Document excerpt:
{document}

INSTRUCTIONS:
1. Extract information from the document first
2. If the company is clearly identified (from company_info) AND information is missing:
   - You may supplement with well-known public information
   - Clearly indicate what comes from the document vs. external knowledge

Return ONLY a JSON object with this structure:
{{
    "business_summary": "2-3 paragraph description of what the company does",
    "products_services": ["Product/Service 1", "Product/Service 2"],
    "revenue_streams": ["Revenue source 1", "Revenue source 2"],
    "customer_segments": ["Segment 1", "Segment 2"],
    "geographic_markets": ["Market 1", "Market 2"],
    "business_segments": [
        {{
            "name": "Segment name",
            "description": "What this segment does",
            "revenue_contribution": "% or amount if available"
        }}
    ],
    "fixed_costs": ["Cost category 1", "Cost category 2"],
    "variable_costs": ["Cost category 1", "Cost category 2"],
    "cost_drivers": ["Driver 1", "Driver 2"],
    "operating_leverage": "high",
    "capex_types": ["Type 1", "Type 2"],
    "capital_intensity": "high",
    "key_assets": ["Asset 1", "Asset 2"],
    "investment_focus": "Where capital is being invested"
}}

For well-known companies like Alphabet/Google, Amazon, Meta, etc., ensure you include their main products and revenue streams even if not in the document."""

    @staticmethod
    def get_management_team_prompt() -> str:
        """Third step: Extract management team information."""
        return """You are extracting management team information.

Company Information:
{company_info}

Document excerpt:
{document}

INSTRUCTIONS:
1. First check the document for management information
2. If the company is a well-known public company AND no management info in document:
   - Include key executives from public knowledge
   - At minimum: CEO, CFO, and major division heads
3. For Alphabet/Google, Meta, Amazon, etc., include their well-known executives
4. For Meta Platforms specifically, include Mark Zuckerberg (CEO), Susan Li (CFO), etc.

Return ONLY a JSON array of management team members:
[
    {{
        "name": "Full name",
        "position": "Title/role",
        "tenure": "Years in role (if known)",
        "previous_roles": ["Prior role 1", "Prior role 2"],
        "age": null,
        "career_summary": "Brief background",
        "linkedin_profile": null,
        "board_member": true,
        "source": "document"
    }}
]

IMPORTANT:
- For identified public companies, return at least 5 key executives
- Empty arrays are not acceptable for major companies
- Use boolean true/false, not strings
- Use null for unknown values, not empty strings"""

    @staticmethod
    def get_swot_analysis_prompt() -> str:
        """Fourth step: Create SWOT analysis based on all gathered information."""
        return """Create a comprehensive SWOT analysis based on the company information.

Company Information:
{company_info}

Business Model:
{business_model}

Financial Context:
{financial_summary}

Create a thorough SWOT analysis combining:
1. Information from the documents
2. Financial performance indicators
3. Well-known market factors for identified companies

Return ONLY a JSON object:
{{
    "strategy": {{
        "business_strategy": "Overall strategic direction",
        "competitive_positioning": "Market position",
        "differentiation": "Key competitive advantages",
        "growth_initiatives": ["Initiative 1", "Initiative 2"]
    }},
    "strengths": [
        "Strength 1 (e.g., market leadership)",
        "Strength 2 (e.g., strong financials)",
        "Strength 3",
        "Strength 4"
    ],
    "weaknesses": [
        "Weakness 1",
        "Weakness 2",
        "Weakness 3",
        "Weakness 4"
    ],
    "opportunities": [
        "Opportunity 1 (e.g., AI/ML expansion)",
        "Opportunity 2 (e.g., emerging markets)",
        "Opportunity 3",
        "Opportunity 4"
    ],
    "threats": [
        "Threat 1 (e.g., regulatory scrutiny)",
        "Threat 2 (e.g., competition)",
        "Threat 3",
        "Threat 4"
    ],
    "industry_context": {{
        "market_characteristics": "Industry dynamics",
        "growth_trends": "Market growth patterns",
        "regulatory_factors": ["Factor 1", "Factor 2"],
        "competitive_dynamics": "Competition landscape",
        "industry_reports": []
    }}
}}

MANDATORY: Each SWOT category must have at least 4 specific items. For big tech companies, threats MUST include regulatory/antitrust concerns."""

    @staticmethod
    def get_risk_assessment_prompt() -> str:
        """Fifth step: Comprehensive risk assessment."""
        return """Perform a comprehensive risk assessment for the company.

Company Information:
{company_info}

Business Model:
{business_model}

SWOT Analysis:
{swot_analysis}

Analyze risks based on:
1. Business model vulnerabilities
2. SWOT-identified threats
3. Industry-specific risks
4. For big tech: regulatory and antitrust risks are MANDATORY

Return ONLY a JSON object:
{{
    "revenue_concentration": {{
        "flag": true,
        "details": "Concentration details if any",
        "top_client_percentage": null
    }},
    "liquidity_concerns": {{
        "flag": false,
        "cash_runway": "Estimated runway",
        "details": "Specific concerns"
    }},
    "related_party_transactions": {{
        "flag": false,
        "transactions": [],
        "source": "Where found"
    }},
    "governance_issues": {{
        "flag": false,
        "issues": ["Issue 1", "Issue 2"],
        "details": "Specific governance concerns"
    }},
    "strategic_inconsistencies": {{
        "flag": false,
        "inconsistencies": ["Inconsistency 1", "Inconsistency 2"]
    }},
    "financial_red_flags": {{
        "flag": false,
        "flags": ["Flag 1", "Flag 2"],
        "details": "Financial concerns"
    }},
    "operational_risks": {{
        "flag": true,
        "risks": ["Risk 1", "Risk 2", "Risk 3"]
    }},
    "market_risks": {{
        "flag": true,
        "risks": ["Competition", "Market disruption", "Technology shifts"]
    }},
    "overall_risk_assessment": "medium"
}}

IMPORTANT:
- For big tech companies (Google, Meta, Amazon, Apple, Microsoft), regulatory risk flags MUST be true
- At least 2-3 risk categories should have flags set to true for any substantial company
- Use boolean values (true/false), not strings
- Use null for unknown numeric values"""

    @staticmethod
    def get_recent_events_prompt() -> str:
        """Extract recent MAJOR CORPORATE and FINANCIAL events using web search."""
        return """You are extracting recent financial news about the company.

Company Information:
{company_info}

Document excerpt:
{document}

Use web search to find recent and significant financial news from the LAST 12 MONTHS. Search for:

Focus on FINANCIAL NEWS or Major Corporate developments.

Return ONLY a JSON array of recent events:
[
    {{
        "date": "2024-01-15",
        "event": "Event description",
        "category": "acquisition",
        "impact": "high",
        "source": "document"
    }}
]

Categories: financial_results, acquisition, debt_issuance, credit_rating, guidance_update, management_change, other_corporate_event
Impact levels: high, medium, low

Each news item must be a distinct event and no two items should have the same date.
Use web search for recent news (last 6 months), not training data."""
