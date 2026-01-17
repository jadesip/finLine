"""
finLine Business Insights API

Endpoints for fetching business intelligence using Perplexity.
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


class InsightsRequest(BaseModel):
    """Request for business insights."""
    query: str | None = None
    topics: list[str] = ["industry", "competitors", "market_trends"]


class InsightsResponse(BaseModel):
    """Response with business insights."""
    company_name: str
    insights: dict[str, Any]
    sources: list[str] = []


# ============================================================
# Endpoints
# ============================================================

@router.post("/{project_id}/insights", response_model=InsightsResponse)
async def get_business_insights(
    project_id: str,
    request: InsightsRequest,
    current_user: CurrentUser,
):
    """
    Fetch business insights for a project using Perplexity.

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

    # Check for Perplexity API key
    perplexity_key = settings.perplexity_api_key
    if not perplexity_key:
        logger.warning("Perplexity API key not configured, returning mock data")
        return InsightsResponse(
            company_name=company_name,
            insights=_generate_mock_insights(company_name, industry, request.topics),
            sources=["Mock data - configure PERPLEXITY_API_KEY for real insights"]
        )

    # Build query for Perplexity
    if request.query:
        query = request.query
    else:
        topic_queries = {
            "industry": f"What industry is {company_name} in and what are the key trends?",
            "competitors": f"Who are the main competitors of {company_name}?",
            "market_trends": f"What is the market size and growth outlook for {company_name}'s industry?",
            "risks": f"What are the key business risks for {company_name}?",
            "opportunities": f"What growth opportunities exist for {company_name}?",
        }
        queries = [topic_queries.get(t, "") for t in request.topics if t in topic_queries]
        query = " ".join(queries)

    if industry:
        query = f"Company: {company_name}, Industry: {industry}. {query}"
    else:
        query = f"Company: {company_name}. {query}"

    try:
        insights, sources = await _call_perplexity(query, perplexity_key)

        # Structure insights by topic
        structured_insights = _structure_insights(insights, request.topics)

        return InsightsResponse(
            company_name=company_name,
            insights=structured_insights,
            sources=sources
        )

    except Exception as e:
        logger.warning(f"Perplexity API call failed: {e}, returning mock data")
        return InsightsResponse(
            company_name=company_name,
            insights=_generate_mock_insights(company_name, industry, request.topics),
            sources=[f"Mock data - Perplexity API error: {str(e)[:100]}"]
        )


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
                        "content": "You are a business analyst providing concise, factual insights about companies. Focus on recent data and cite sources."
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 2000,
                "return_citations": True
            }
        )
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    citations = data.get("citations", [])

    return content, citations


def _structure_insights(raw_insights: str, topics: list[str]) -> dict[str, Any]:
    """Structure raw insights into topic categories."""
    # For now, return as a single block
    # Could be enhanced with LLM to parse into structured sections
    return {
        "summary": raw_insights,
        "topics_requested": topics,
    }


def _generate_mock_insights(company_name: str, industry: str, topics: list[str]) -> dict[str, Any]:
    """Generate mock insights when API key not available."""
    mock = {
        "summary": f"Mock insights for {company_name}",
        "topics_requested": topics,
    }

    if "industry" in topics:
        mock["industry"] = {
            "sector": industry or "Technology",
            "description": f"{company_name} operates in the {industry or 'technology'} sector.",
            "key_trends": ["Digital transformation", "AI adoption", "Sustainability focus"]
        }

    if "competitors" in topics:
        mock["competitors"] = {
            "main_competitors": ["Competitor A", "Competitor B", "Competitor C"],
            "competitive_position": "Mid-market player with growth potential"
        }

    if "market_trends" in topics:
        mock["market_trends"] = {
            "market_size": "$50B (estimated)",
            "growth_rate": "8-12% annually",
            "outlook": "Positive growth expected"
        }

    if "risks" in topics:
        mock["risks"] = {
            "key_risks": [
                "Market competition",
                "Regulatory changes",
                "Economic downturn"
            ],
            "risk_level": "Medium"
        }

    if "opportunities" in topics:
        mock["opportunities"] = {
            "growth_opportunities": [
                "Market expansion",
                "Product innovation",
                "Strategic partnerships"
            ]
        }

    return mock
