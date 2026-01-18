"""
finLine Business Insights API

Endpoints for fetching business intelligence using Perplexity.
Returns structured InsightsData compatible with frontend.
"""

import logging
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from api.auth import CurrentUser
from config import get_settings
from database import get_project as db_get_project

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


# ============================================================
# Request/Response Models
# ============================================================

class InsightsRequest(BaseModel):
    """Request for business insights."""
    query: str | None = None
    topics: list[str] = ["industry", "competitors", "market_trends", "risks"]


# Nested models matching frontend InsightsData type
class BusinessDescription(BaseModel):
    summary: str
    confidence: str = "medium"


class BusinessSegment(BaseModel):
    name: str
    description: str
    revenue_contribution: str | None = None


class RevenueModel(BaseModel):
    key_products_services: list[str] = []
    revenue_streams: list[str] = []
    customer_segments: list[str] = []
    geographic_markets: list[str] = []
    business_segments: list[BusinessSegment] = []


class CostStructure(BaseModel):
    fixed_costs: list[str] = []
    variable_costs: list[str] = []
    key_cost_drivers: list[str] = []
    operating_leverage: str | None = None


class CapitalRequirements(BaseModel):
    capex_types: list[str] = []
    capital_intensity: str = "medium"
    key_assets: list[str] = []
    investment_focus: str | None = None


class ManagementMember(BaseModel):
    name: str
    position: str
    age: int | None = None
    tenure: str | None = None
    career_summary: str | None = None
    linkedin_profile: str | None = None
    previous_roles: list[str] = []
    board_member: bool = False


class BusinessInsights(BaseModel):
    business_description: BusinessDescription
    revenue_model: RevenueModel = RevenueModel()
    cost_structure: CostStructure = CostStructure()
    capital_requirements: CapitalRequirements = CapitalRequirements()
    management_team: list[ManagementMember] = []


class Strategy(BaseModel):
    business_strategy: str | None = None
    competitive_positioning: str | None = None
    differentiation: str | None = None
    growth_initiatives: list[str] = []


class SwotAnalysis(BaseModel):
    strengths: list[str] = []
    weaknesses: list[str] = []
    opportunities: list[str] = []
    threats: list[str] = []


class IndustryContext(BaseModel):
    market_characteristics: str | None = None
    growth_trends: str | None = None
    regulatory_factors: list[str] = []
    competitive_dynamics: str | None = None


class RecentEvent(BaseModel):
    date: str | None = None
    event_type: str
    description: str
    impact: str | None = None


class RiskFlag(BaseModel):
    flag: bool = False
    details: str | None = None


class RevenueConcentration(RiskFlag):
    top_client_percentage: float | None = None


class LiquidityConcerns(RiskFlag):
    cash_runway: str | None = None


class RelatedPartyTransactions(RiskFlag):
    transactions: list[str] = []


class GovernanceIssues(RiskFlag):
    issues: list[str] = []


class StrategicInconsistencies(RiskFlag):
    inconsistencies: list[str] = []


class FinancialRedFlags(RiskFlag):
    flags: list[str] = []


class OperationalRisks(RiskFlag):
    risks: list[str] = []


class MarketRisks(RiskFlag):
    risks: list[str] = []


class RiskAnalysis(BaseModel):
    revenue_concentration: RevenueConcentration = RevenueConcentration()
    liquidity_concerns: LiquidityConcerns = LiquidityConcerns()
    related_party_transactions: RelatedPartyTransactions = RelatedPartyTransactions()
    governance_issues: GovernanceIssues = GovernanceIssues()
    strategic_inconsistencies: StrategicInconsistencies = StrategicInconsistencies()
    financial_red_flags: FinancialRedFlags = FinancialRedFlags()
    operational_risks: OperationalRisks = OperationalRisks()
    market_risks: MarketRisks = MarketRisks()
    overall_risk_assessment: str = "medium"


class StrategicAnalysis(BaseModel):
    strategy: Strategy = Strategy()
    swot_analysis: SwotAnalysis = SwotAnalysis()
    industry_context: IndustryContext = IndustryContext()
    recent_events: list[RecentEvent] = []
    risk_analysis: RiskAnalysis = RiskAnalysis()


class InsightsData(BaseModel):
    """Full insights data structure matching frontend type."""
    business_insights: BusinessInsights
    strategic_analysis: StrategicAnalysis = StrategicAnalysis()
    last_updated: str | None = None


# ============================================================
# Endpoints
# ============================================================

@router.post("/{project_id}/insights", response_model=InsightsData)
async def get_business_insights(
    project_id: str,
    request: InsightsRequest,
    current_user: CurrentUser,
):
    """
    Fetch business insights for a project.

    Returns structured InsightsData with:
    - business_insights: Company description, revenue model, management
    - strategic_analysis: Strategy, SWOT, industry context, risks

    Topics available:
    - industry: Industry analysis and trends
    - competitors: Competitive landscape
    - market_trends: Market size and growth
    - risks: Key business risks
    - opportunities: Growth opportunities
    """
    logger.info(f"Insights request for project {project_id}: topics={request.topics}")

    # Verify project access
    project = await db_get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    if project["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Get company info from project
    project_data = project["data"]
    meta = project_data.get("meta", {})
    company_name = meta.get("company_name") or meta.get("name") or project["name"]
    industry = meta.get("industry", "")

    if not company_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project has no company name set"
        )

    # Check for existing extracted insights
    existing_insights = project_data.get("insights_data")

    # Check for Perplexity API key
    perplexity_key = settings.perplexity_api_key

    if not perplexity_key:
        logger.warning("Perplexity API key not configured, returning mock/extracted data")
        return _generate_insights_data(company_name, industry, request.topics, existing_insights)

    try:
        # Build query for Perplexity
        query = _build_perplexity_query(company_name, industry, request.topics)

        # Call Perplexity
        raw_insights, sources = await _call_perplexity(query, perplexity_key)

        # Parse and structure the response
        insights_data = _parse_perplexity_response(
            raw_insights,
            company_name,
            industry,
            request.topics,
            existing_insights
        )

        return insights_data

    except Exception as e:
        logger.warning(f"Perplexity API call failed: {e}, returning fallback data")
        return _generate_insights_data(company_name, industry, request.topics, existing_insights)


@router.get("/{project_id}/insights/quick")
async def get_quick_insights(
    project_id: str,
    current_user: CurrentUser,
):
    """Get quick industry insights without custom query."""
    request = InsightsRequest(topics=["industry", "market_trends"])
    return await get_business_insights(project_id, request, current_user)


# ============================================================
# Helpers
# ============================================================

def _build_perplexity_query(company_name: str, industry: str, topics: list[str]) -> str:
    """Build comprehensive query for Perplexity."""
    base = f"Provide a comprehensive business analysis of {company_name}"
    if industry:
        base += f" (a company in the {industry} sector)"

    topic_prompts = []
    if "industry" in topics:
        topic_prompts.append("industry trends and market dynamics")
    if "competitors" in topics:
        topic_prompts.append("competitive landscape and key competitors")
    if "market_trends" in topics:
        topic_prompts.append("market size, growth outlook, and emerging trends")
    if "risks" in topics:
        topic_prompts.append("key business risks and challenges")
    if "opportunities" in topics:
        topic_prompts.append("growth opportunities and strategic initiatives")

    if topic_prompts:
        base += f". Focus on: {', '.join(topic_prompts)}"

    base += ". Include specific details, data points, and recent developments."

    return base


async def _call_perplexity(query: str, api_key: str) -> tuple[str, list[str]]:
    """Call Perplexity API for business insights."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": """You are a business analyst providing detailed, factual insights about companies.
Structure your response with clear sections for:
1. Business Overview
2. Industry Context
3. Competitive Position
4. Key Strengths and Weaknesses
5. Opportunities and Threats
6. Risk Factors
Cite sources and include recent data when available."""
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 3000,
                "return_citations": True
            }
        )
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    citations = data.get("citations", [])

    return content, citations


def _parse_perplexity_response(
    raw_insights: str,
    company_name: str,
    industry: str,
    topics: list[str],
    existing_insights: dict | None
) -> InsightsData:
    """Parse Perplexity response into structured InsightsData."""
    # Start with base structure
    insights = _generate_insights_data(company_name, industry, topics, existing_insights)

    # Update business description with Perplexity response
    insights.business_insights.business_description.summary = raw_insights[:2000]
    insights.business_insights.business_description.confidence = "high"

    # Parse SWOT from response if present
    lower_response = raw_insights.lower()

    # Extract strengths
    if "strength" in lower_response:
        insights.strategic_analysis.swot_analysis.strengths = _extract_list_items(
            raw_insights, ["strengths:", "strength:", "key strengths:"]
        ) or insights.strategic_analysis.swot_analysis.strengths

    # Extract weaknesses
    if "weakness" in lower_response:
        insights.strategic_analysis.swot_analysis.weaknesses = _extract_list_items(
            raw_insights, ["weaknesses:", "weakness:", "key weaknesses:"]
        ) or insights.strategic_analysis.swot_analysis.weaknesses

    # Extract opportunities
    if "opportunit" in lower_response:
        insights.strategic_analysis.swot_analysis.opportunities = _extract_list_items(
            raw_insights, ["opportunities:", "opportunity:", "growth opportunities:"]
        ) or insights.strategic_analysis.swot_analysis.opportunities

    # Extract threats
    if "threat" in lower_response:
        insights.strategic_analysis.swot_analysis.threats = _extract_list_items(
            raw_insights, ["threats:", "threat:", "key threats:"]
        ) or insights.strategic_analysis.swot_analysis.threats

    # Extract risks
    if "risk" in lower_response:
        risk_items = _extract_list_items(raw_insights, ["risks:", "risk factors:", "key risks:"])
        if risk_items:
            insights.strategic_analysis.risk_analysis.market_risks.flag = True
            insights.strategic_analysis.risk_analysis.market_risks.risks = risk_items[:5]

    return insights


def _extract_list_items(text: str, markers: list[str]) -> list[str]:
    """Extract bullet points following a marker."""
    items = []
    text_lower = text.lower()

    for marker in markers:
        pos = text_lower.find(marker)
        if pos != -1:
            # Get text after marker
            section = text[pos + len(marker):pos + len(marker) + 500]

            # Extract bullet points or numbered items
            lines = section.split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith(("-", "•", "*", "1.", "2.", "3.", "4.", "5.")):
                    item = line.lstrip("-•*0123456789. ").strip()
                    if item and len(item) > 5:
                        items.append(item[:200])
                elif items and not line:
                    break  # Stop at empty line after items

            if items:
                break

    return items[:10]


def _parse_risk_analysis(risk_data: dict) -> RiskAnalysis:
    """Parse risk analysis data from LangChain extraction format."""
    if not risk_data:
        return RiskAnalysis()

    def parse_risk_flag(data: dict | None, flag_class, extra_fields: dict = None):
        """Helper to parse individual risk flags."""
        if not data or not isinstance(data, dict):
            return flag_class()
        kwargs = {
            "flag": data.get("flag", False),
            "details": data.get("details")
        }
        if extra_fields:
            for key, default in extra_fields.items():
                kwargs[key] = data.get(key, default)
        return flag_class(**kwargs)

    return RiskAnalysis(
        revenue_concentration=RevenueConcentration(
            flag=risk_data.get("revenue_concentration", {}).get("flag", False),
            details=risk_data.get("revenue_concentration", {}).get("details"),
            top_client_percentage=risk_data.get("revenue_concentration", {}).get("top_client_percentage")
        ),
        liquidity_concerns=LiquidityConcerns(
            flag=risk_data.get("liquidity_concerns", {}).get("flag", False),
            details=risk_data.get("liquidity_concerns", {}).get("details"),
            cash_runway=risk_data.get("liquidity_concerns", {}).get("cash_runway")
        ),
        related_party_transactions=RelatedPartyTransactions(
            flag=risk_data.get("related_party_transactions", {}).get("flag", False),
            details=risk_data.get("related_party_transactions", {}).get("details"),
            transactions=risk_data.get("related_party_transactions", {}).get("transactions", [])
        ),
        governance_issues=GovernanceIssues(
            flag=risk_data.get("governance_issues", {}).get("flag", False),
            details=risk_data.get("governance_issues", {}).get("details"),
            issues=risk_data.get("governance_issues", {}).get("issues", [])
        ),
        strategic_inconsistencies=StrategicInconsistencies(
            flag=risk_data.get("strategic_inconsistencies", {}).get("flag", False),
            details=risk_data.get("strategic_inconsistencies", {}).get("details"),
            inconsistencies=risk_data.get("strategic_inconsistencies", {}).get("inconsistencies", [])
        ),
        financial_red_flags=FinancialRedFlags(
            flag=risk_data.get("financial_red_flags", {}).get("flag", False),
            details=risk_data.get("financial_red_flags", {}).get("details"),
            flags=risk_data.get("financial_red_flags", {}).get("flags", [])
        ),
        operational_risks=OperationalRisks(
            flag=risk_data.get("operational_risks", {}).get("flag", False),
            details=risk_data.get("operational_risks", {}).get("details"),
            risks=risk_data.get("operational_risks", {}).get("risks", [])
        ),
        market_risks=MarketRisks(
            flag=risk_data.get("market_risks", {}).get("flag", False),
            details=risk_data.get("market_risks", {}).get("details"),
            risks=risk_data.get("market_risks", {}).get("risks", [])
        ),
        overall_risk_assessment=risk_data.get("overall_risk_assessment", "medium")
    )


def _generate_insights_data(
    company_name: str,
    industry: str,
    topics: list[str],
    existing_insights: dict | None
) -> InsightsData:
    """Generate InsightsData structure with mock/extracted data."""
    from datetime import datetime

    # Use existing insights if available (supports LangChain extraction format)
    if existing_insights:
        try:
            # Check if this is LangChain extraction format (has information_extraction)
            info_extraction = existing_insights.get("information_extraction", {})
            strategic = existing_insights.get("strategic_analysis", {})

            if info_extraction or strategic:
                # LangChain format - map to our structure
                bus_desc = info_extraction.get("business_description", {})
                rev_model = info_extraction.get("revenue_model", {})
                cost_struct = info_extraction.get("cost_structure", {})
                cap_req = info_extraction.get("capital_requirements", {})
                mgmt_team = info_extraction.get("management_team", [])

                strategy_data = strategic.get("strategy", {})
                swot_data = strategic.get("swot_analysis", {})
                industry_ctx = strategic.get("industry_context", {})
                recent_evts = strategic.get("recent_events", [])
                risk_data = strategic.get("risk_analysis", {})

                return InsightsData(
                    business_insights=BusinessInsights(
                        business_description=BusinessDescription(
                            summary=bus_desc.get("summary", f"{company_name} operates in {industry or 'the'} sector."),
                            confidence=bus_desc.get("confidence", "medium")
                        ),
                        revenue_model=RevenueModel(
                            key_products_services=rev_model.get("key_products_services", []),
                            revenue_streams=rev_model.get("revenue_streams", []),
                            customer_segments=rev_model.get("customer_segments", []),
                            geographic_markets=rev_model.get("geographic_markets", []),
                            business_segments=[
                                BusinessSegment(
                                    name=s.get("name", ""),
                                    description=s.get("description", ""),
                                    revenue_contribution=s.get("revenue_contribution")
                                )
                                for s in rev_model.get("business_segments", [])
                            ] if rev_model.get("business_segments") else []
                        ),
                        cost_structure=CostStructure(
                            fixed_costs=cost_struct.get("fixed_costs", []),
                            variable_costs=cost_struct.get("variable_costs", []),
                            key_cost_drivers=cost_struct.get("key_cost_drivers", []),
                            operating_leverage=cost_struct.get("operating_leverage")
                        ),
                        capital_requirements=CapitalRequirements(
                            capex_types=cap_req.get("capex_types", []),
                            capital_intensity=cap_req.get("capital_intensity", "medium"),
                            key_assets=cap_req.get("key_assets", []),
                            investment_focus=cap_req.get("investment_focus")
                        ),
                        management_team=[
                            ManagementMember(
                                name=m.get("name", ""),
                                position=m.get("position", ""),
                                tenure=m.get("tenure"),
                                career_summary=m.get("career_summary"),
                                linkedin_profile=m.get("linkedin_profile"),
                                previous_roles=m.get("previous_roles", []),
                                board_member=m.get("board_member", False)
                            )
                            for m in mgmt_team if isinstance(m, dict)
                        ]
                    ),
                    strategic_analysis=StrategicAnalysis(
                        strategy=Strategy(
                            business_strategy=strategy_data.get("business_strategy"),
                            competitive_positioning=strategy_data.get("competitive_positioning"),
                            differentiation=strategy_data.get("differentiation"),
                            growth_initiatives=strategy_data.get("growth_initiatives", [])
                        ),
                        swot_analysis=SwotAnalysis(
                            strengths=swot_data.get("strengths", []),
                            weaknesses=swot_data.get("weaknesses", []),
                            opportunities=swot_data.get("opportunities", []),
                            threats=swot_data.get("threats", [])
                        ),
                        industry_context=IndustryContext(
                            market_characteristics=industry_ctx.get("market_characteristics"),
                            growth_trends=industry_ctx.get("growth_trends"),
                            regulatory_factors=industry_ctx.get("regulatory_factors", []),
                            competitive_dynamics=industry_ctx.get("competitive_dynamics")
                        ),
                        recent_events=[
                            RecentEvent(
                                date=e.get("date"),
                                event_type=e.get("category", e.get("event_type", "other")),
                                description=e.get("event", e.get("description", "")),
                                impact=e.get("impact")
                            )
                            for e in recent_evts if isinstance(e, dict)
                        ],
                        risk_analysis=_parse_risk_analysis(risk_data)
                    ),
                    last_updated=datetime.utcnow().isoformat()
                )

            # Legacy/simple format fallback
            return InsightsData(
                business_insights=BusinessInsights(
                    business_description=BusinessDescription(
                        summary=existing_insights.get("summary", f"{company_name} is a company operating in the {industry or 'technology'} sector."),
                        confidence=existing_insights.get("confidence", "medium")
                    ),
                    revenue_model=RevenueModel(
                        key_products_services=existing_insights.get("key_products", []),
                        revenue_streams=existing_insights.get("revenue_streams", []),
                        customer_segments=existing_insights.get("customer_segments", []),
                        geographic_markets=existing_insights.get("markets", [])
                    ),
                    management_team=[
                        ManagementMember(
                            name=m.get("name", ""),
                            position=m.get("position", ""),
                            career_summary=m.get("background")
                        )
                        for m in existing_insights.get("management_team", [])
                    ]
                ),
                strategic_analysis=StrategicAnalysis(
                    strategy=Strategy(
                        business_strategy=existing_insights.get("strategy", {}).get("business_strategy"),
                        competitive_positioning=existing_insights.get("strategy", {}).get("competitive_positioning"),
                        growth_initiatives=existing_insights.get("strategy", {}).get("growth_initiatives", [])
                    ),
                    risk_analysis=RiskAnalysis(
                        market_risks=MarketRisks(
                            flag=len(existing_insights.get("risks", {}).get("key_risks", [])) > 0,
                            risks=existing_insights.get("risks", {}).get("key_risks", [])
                        ),
                        overall_risk_assessment=existing_insights.get("risks", {}).get("risk_level", "medium")
                    )
                ),
                last_updated=datetime.utcnow().isoformat()
            )
        except Exception as e:
            logger.warning(f"Failed to parse existing insights: {e}")

    # Generate default structure
    return InsightsData(
        business_insights=BusinessInsights(
            business_description=BusinessDescription(
                summary=f"{company_name} is a company operating in the {industry or 'technology'} sector. This is placeholder information - upload a company document for detailed insights, or configure PERPLEXITY_API_KEY for live business intelligence.",
                confidence="low"
            ),
            revenue_model=RevenueModel(
                key_products_services=["Product/Service 1", "Product/Service 2"],
                revenue_streams=["Primary revenue stream"],
                customer_segments=["Enterprise", "SMB"],
                geographic_markets=["North America", "Europe"]
            ),
            cost_structure=CostStructure(
                fixed_costs=["Personnel", "Facilities"],
                variable_costs=["Materials", "Distribution"],
                key_cost_drivers=["Labor costs", "Technology infrastructure"],
                operating_leverage="Medium"
            ),
            capital_requirements=CapitalRequirements(
                capex_types=["Technology", "Equipment"],
                capital_intensity="medium",
                key_assets=["Technology platform", "Customer relationships"],
                investment_focus="R&D and market expansion"
            )
        ),
        strategic_analysis=StrategicAnalysis(
            strategy=Strategy(
                business_strategy="Growth-focused strategy with emphasis on market expansion",
                competitive_positioning="Mid-market player with differentiated offering",
                differentiation="Technology-enabled solutions",
                growth_initiatives=["Market expansion", "Product development", "Strategic partnerships"]
            ),
            swot_analysis=SwotAnalysis(
                strengths=["Established market presence", "Strong technology platform", "Experienced management team"],
                weaknesses=["Limited geographic reach", "Dependency on key customers", "Resource constraints"],
                opportunities=["Market expansion", "New product development", "Industry consolidation"],
                threats=["Competitive pressure", "Regulatory changes", "Economic uncertainty"]
            ),
            industry_context=IndustryContext(
                market_characteristics=f"The {industry or 'technology'} industry is characterized by rapid innovation and competitive dynamics.",
                growth_trends="Industry experiencing moderate to high growth",
                regulatory_factors=["Industry regulations", "Data privacy requirements"],
                competitive_dynamics="Fragmented market with several key players"
            ),
            risk_analysis=RiskAnalysis(
                market_risks=MarketRisks(
                    flag=True,
                    risks=["Competitive pressure", "Market volatility"],
                    details="Standard market risks for the industry"
                ),
                overall_risk_assessment="medium"
            )
        ),
        last_updated=datetime.utcnow().isoformat()
    )
