"""
LangChain-based business insights extractor.
Ported from finForge - DO NOT MODIFY without testing.

This module is COMPLETELY SEPARATE from the main extraction pipeline.
It only handles business insights extraction using LangChain for better context management.
"""

import asyncio
import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class LangChainBusinessInsights:
    """
    Extracts business insights using LangChain with sequential steps.

    This is a standalone module that:
    1. Does NOT modify any existing extraction logic
    2. Returns data in the EXACT same format as the original extractor
    3. Uses LangChain to maintain context across multiple extraction steps
    """

    def __init__(self, api_key: str):
        """Initialize with OpenAI API key."""
        self.api_key = api_key
        self._initialize_chains()
        logger.info("LangChain Business Insights extractor initialized")

    def _initialize_chains(self):
        """Initialize LangChain components."""
        try:
            from langchain.chains import LLMChain
            from langchain.prompts import PromptTemplate
            from langchain_openai import ChatOpenAI

            # Initialize LLM with appropriate temperature for each task
            self.llm_factual = ChatOpenAI(
                api_key=self.api_key,
                model="gpt-4o",
                temperature=0.05,  # Very low for factual extraction
            )

            self.llm_analytical = ChatOpenAI(
                api_key=self.api_key,
                model="gpt-4o",
                temperature=0.3,  # Slightly higher for SWOT/strategy
            )

            # Initialize memory to maintain context
            self.memory = None  # Will store context manually

            # Load prompts
            from .langchain_prompts import LangChainPrompts

            self.prompts = LangChainPrompts()

            # Create chains for each extraction step
            self._create_extraction_chains()

        except ImportError as e:
            logger.error(f"Failed to import LangChain dependencies: {e}")
            raise

    def _create_extraction_chains(self):
        """Create individual chains for each extraction step."""
        from langchain.chains import LLMChain
        from langchain.prompts import PromptTemplate

        # Chain 1: Company Identification
        self.company_chain = LLMChain(
            llm=self.llm_factual,
            prompt=PromptTemplate(
                input_variables=["document"],
                template=self.prompts.get_company_identification_prompt(),
            ),
            output_key="company_info",
        )

        # Chain 2: Business Model
        self.business_model_chain = LLMChain(
            llm=self.llm_factual,
            prompt=PromptTemplate(
                input_variables=["document", "company_info"],
                template=self.prompts.get_business_model_prompt(),
            ),
            output_key="business_model",
        )

        # Chain 3: Management Team
        self.management_chain = LLMChain(
            llm=self.llm_factual,
            prompt=PromptTemplate(
                input_variables=["document", "company_info"],
                template=self.prompts.get_management_team_prompt(),
            ),
            output_key="management_team",
        )

        # Chain 4: SWOT Analysis
        self.swot_chain = LLMChain(
            llm=self.llm_analytical,
            prompt=PromptTemplate(
                input_variables=["company_info", "business_model", "financial_summary"],
                template=self.prompts.get_swot_analysis_prompt(),
            ),
            output_key="swot_analysis",
        )

        # Chain 5: Risk Assessment
        self.risk_chain = LLMChain(
            llm=self.llm_analytical,
            prompt=PromptTemplate(
                input_variables=["company_info", "business_model", "swot_analysis"],
                template=self.prompts.get_risk_assessment_prompt(),
            ),
            output_key="risk_analysis",
        )

        # Chain 6: Recent Events - Use Perplexity for web search if available
        perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        if perplexity_api_key:
            try:
                from langchain_openai import ChatOpenAI
                self.llm_perplexity = ChatOpenAI(
                    api_key=perplexity_api_key,
                    base_url="https://api.perplexity.ai",
                    model="sonar-pro",
                    temperature=0.1,
                )
                logger.info(f"Using Perplexity for recent events (model: sonar-pro)")
                self.perplexity_available = True
            except Exception as e:
                logger.warning(f"Failed to initialize Perplexity, falling back to GPT-4: {e}")
                self.llm_perplexity = self.llm_factual
                self.perplexity_available = False
        else:
            logger.info("No PERPLEXITY_API_KEY found, using GPT-4 for recent events")
            self.llm_perplexity = self.llm_factual
            self.perplexity_available = False

        self.recent_events_chain = LLMChain(
            llm=self.llm_perplexity,
            prompt=PromptTemplate(
                input_variables=["company_info", "document"],
                template=self.prompts.get_recent_events_prompt(),
            ),
            output_key="recent_events",
        )

    async def extract(self, images: list[Any], structured_text: Any | None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Extract business insights using LangChain sequential approach.

        Returns data in EXACT same format as original extractor.
        """
        logger.info("Starting LangChain business insights extraction")
        logger.info(f"Images count: {len(images) if images else 0}")
        logger.info(f"Has structured text: {bool(structured_text)}")

        # Log metadata context if provided
        if metadata:
            logger.info(f"Using metadata context: Company={metadata.get('company_name', 'Unknown')}, Industry={metadata.get('industry', 'Unknown')}")
            self.metadata_context = metadata
        else:
            logger.info("No metadata context provided")
            self.metadata_context = None

        try:
            # Prepare document text
            document_text = self._prepare_document_text(images, structured_text)

            # Step 1: Company Identification
            logger.info("Step 1: Identifying company...")

            # If metadata already has company info, use it as base
            if self.metadata_context and self.metadata_context.get('company_name'):
                logger.info("Using company name from metadata context")
                company_info = {
                    "company_name": self.metadata_context.get('company_name'),
                    "industry": self.metadata_context.get('industry', 'Not specified'),
                    "sector": self.metadata_context.get('sector', 'Not specified'),
                    "country": self.metadata_context.get('country_of_operations', 'Not specified')
                }
                # Still run chain but with context
                company_result = await self.company_chain.ainvoke({
                    "document": f"KNOWN CONTEXT: Company is {company_info['company_name']} in {company_info['industry']} industry.\n\nDOCUMENT:\n{document_text[:3000]}"
                })
                # Merge results, preferring extracted over metadata
                extracted_info = self._parse_json_response(company_result["company_info"])
                for key, value in extracted_info.items():
                    if value and value != "Not specified" and value != "Unknown":
                        company_info[key] = value
            else:
                company_result = await self.company_chain.ainvoke({"document": document_text[:3000]})
                company_info = self._parse_json_response(company_result["company_info"])

            logger.info(f"Identified: {company_info.get('company_name', 'Unknown')}, Industry: {company_info.get('industry', 'Unknown')}")

            # Step 2: Business Model Extraction
            logger.info("Step 2: Extracting business model...")
            business_result = await self.business_model_chain.ainvoke(
                {"document": document_text[:5000], "company_info": json.dumps(company_info)}
            )
            business_model = self._parse_json_response(business_result["business_model"])
            logger.info(f"Parsed business model - Revenue streams: {business_model.get('revenue_streams', [])}")

            # Step 3: Management Team
            logger.info("Step 3: Extracting management team...")
            management_result = await self.management_chain.ainvoke(
                {"document": document_text[:5000], "company_info": json.dumps(company_info)}
            )
            management_team = self._parse_json_response(management_result["management_team"])
            if isinstance(management_team, list):
                logger.info(f"Parsed management team: {len(management_team)} members")
            else:
                logger.info(f"Parsed management team: Not a list - type is {type(management_team)}")

            # Get financial summary (if available)
            financial_summary = self._get_financial_summary(structured_text)

            # Step 4: SWOT Analysis
            logger.info("Step 4: Creating SWOT analysis...")
            swot_result = await self.swot_chain.ainvoke(
                {
                    "company_info": json.dumps(company_info),
                    "business_model": json.dumps(business_model),
                    "financial_summary": json.dumps(financial_summary),
                }
            )
            swot_analysis = self._parse_json_response(swot_result["swot_analysis"])
            logger.info(f"Parsed SWOT - S:{len(swot_analysis.get('strengths', []))} W:{len(swot_analysis.get('weaknesses', []))} O:{len(swot_analysis.get('opportunities', []))} T:{len(swot_analysis.get('threats', []))}")

            # Step 5 & 6: Risk Assessment and Recent Events (run in parallel)
            logger.info("Step 5-6: Performing risk assessment and extracting recent events in parallel...")

            # Run both chains concurrently
            risk_task = self.risk_chain.ainvoke(
                {
                    "company_info": json.dumps(company_info),
                    "business_model": json.dumps(business_model),
                    "swot_analysis": json.dumps(swot_analysis),
                }
            )

            # Try with Perplexity first, fall back to GPT-4 if it fails
            try:
                recent_events_task = self.recent_events_chain.ainvoke(
                    {"document": document_text[:5000], "company_info": json.dumps(company_info)}
                )
                risk_result, recent_events_result = await asyncio.gather(risk_task, recent_events_task)
            except Exception as e:
                if self.perplexity_available and "401" in str(e):
                    logger.warning(f"Perplexity API failed with auth error, falling back to GPT-4: {e}")
                    self.llm_perplexity = self.llm_factual
                    self.perplexity_available = False
                    self.recent_events_chain.llm = self.llm_factual
                    recent_events_task = self.recent_events_chain.ainvoke(
                        {"document": document_text[:5000], "company_info": json.dumps(company_info)}
                    )
                    risk_result = await risk_task
                    recent_events_result = await recent_events_task
                else:
                    raise

            # Process risk assessment
            risk_analysis = self._parse_json_response(risk_result["risk_analysis"])
            logger.info(f"Parsed risk assessment - Overall: {risk_analysis.get('overall_risk_assessment', 'Unknown')}")

            # Process recent events
            recent_events = self._parse_json_response(recent_events_result["recent_events"])
            if isinstance(recent_events, list):
                logger.info(f"Parsed recent events: {len(recent_events)} events found")
            else:
                logger.info(f"Parsed recent events: Not a list - type is {type(recent_events)}")
                recent_events = []

            # Compile results in EXACT format expected by the system
            result = self._compile_results(
                company_info,
                business_model,
                management_team,
                swot_analysis,
                risk_analysis,
                recent_events,
            )

            logger.info("LangChain business insights extraction completed")

            return {
                "data": result,
                "tokens": 5000,  # Estimate
            }

        except Exception as e:
            logger.error(f"LangChain extraction failed: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"data": self._get_empty_result(), "tokens": 0}

    def _prepare_document_text(self, images: list[Any], structured_text: Any | None) -> str:
        """Prepare document text from structured text or fallback to description."""
        if structured_text and hasattr(structured_text, "format_for_llm"):
            return structured_text.format_for_llm()
        elif structured_text:
            return str(structured_text)[:10000]
        else:
            return "Document images provided but no text extracted."

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        """Parse JSON response from LLM."""
        try:
            if isinstance(response, str):
                # Remove markdown code blocks if present
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0].strip()

                # Try to find JSON array first
                if response.strip().startswith("["):
                    start = response.find("[")
                    end = response.rfind("]") + 1
                    if start >= 0 and end > start:
                        json_str = response[start:end]
                        return json.loads(json_str)

                # Find JSON object
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        # Count braces to find proper end
                        brace_count = 0
                        for i, char in enumerate(response[start:], start):
                            if char == "{":
                                brace_count += 1
                            elif char == "}":
                                brace_count -= 1
                                if brace_count == 0:
                                    json_str = response[start : i + 1]
                                    return json.loads(json_str)

                return json.loads(response)
            return response
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return {} if "[" not in str(response).strip()[:1] else []

    def _get_financial_summary(self, structured_text: Any) -> dict[str, Any]:
        """Extract basic financial metrics if available."""
        return {
            "has_financials": bool(structured_text),
            "note": "Financial details in separate extraction",
        }

    def _compile_results(
        self,
        company_info: dict,
        business_model: dict,
        management_team: Any,
        swot: dict,
        risk: dict,
        recent_events: list[dict] = None,
    ) -> dict[str, Any]:
        """
        Compile results in EXACT format expected by the system.
        """
        return {
            "company_identification": {"company_name": company_info.get("company_name", "")},
            "information_extraction": {
                "business_description": {
                    "summary": business_model.get("business_summary", ""),
                    "source_pages": [],
                    "confidence": "high" if company_info.get("company_name") else "low",
                },
                "revenue_model": {
                    "key_products_services": business_model.get("products_services", []),
                    "revenue_streams": business_model.get("revenue_streams", []),
                    "customer_segments": business_model.get("customer_segments", []),
                    "geographic_markets": business_model.get("geographic_markets", []),
                    "business_segments": business_model.get("business_segments", []),
                },
                "cost_structure": {
                    "fixed_costs": business_model.get("fixed_costs", []),
                    "variable_costs": business_model.get("variable_costs", []),
                    "key_cost_drivers": business_model.get("cost_drivers", []),
                    "operating_leverage": business_model.get("operating_leverage"),
                },
                "capital_requirements": {
                    "capex_types": business_model.get("capex_types", []),
                    "capital_intensity": business_model.get("capital_intensity", "unknown"),
                    "key_assets": business_model.get("key_assets", []),
                    "investment_focus": business_model.get("investment_focus"),
                },
                "management_team": management_team if isinstance(management_team, list) else [],
            },
            "strategic_analysis": {
                "strategy": {
                    "business_strategy": swot.get("strategy", {}).get("business_strategy", ""),
                    "competitive_positioning": swot.get("strategy", {}).get("competitive_positioning", ""),
                    "differentiation": swot.get("strategy", {}).get("differentiation", ""),
                    "growth_initiatives": swot.get("strategy", {}).get("growth_initiatives", []),
                },
                "swot_analysis": {
                    "strengths": swot.get("strengths", []),
                    "weaknesses": swot.get("weaknesses", []),
                    "opportunities": swot.get("opportunities", []),
                    "threats": swot.get("threats", []),
                },
                "industry_context": swot.get(
                    "industry_context",
                    {
                        "market_characteristics": "",
                        "growth_trends": "",
                        "regulatory_factors": [],
                        "competitive_dynamics": "",
                        "industry_reports": [],
                    },
                ),
                "recent_events": recent_events if recent_events else [],
                "risk_analysis": risk,
            },
        }

    def _get_empty_result(self) -> dict[str, Any]:
        """Return empty result in expected format."""
        return {
            "company_identification": {"company_name": ""},
            "information_extraction": {
                "business_description": {"summary": "", "source_pages": [], "confidence": "low"},
                "revenue_model": {
                    "key_products_services": [],
                    "revenue_streams": [],
                    "customer_segments": [],
                    "geographic_markets": [],
                    "business_segments": [],
                },
                "cost_structure": {
                    "fixed_costs": [],
                    "variable_costs": [],
                    "key_cost_drivers": [],
                    "operating_leverage": None,
                },
                "capital_requirements": {
                    "capex_types": [],
                    "capital_intensity": "low",
                    "key_assets": [],
                    "investment_focus": None,
                },
                "management_team": [],
            },
            "strategic_analysis": {
                "strategy": {
                    "business_strategy": "",
                    "competitive_positioning": "",
                    "differentiation": "",
                    "growth_initiatives": [],
                },
                "swot_analysis": {
                    "strengths": [],
                    "weaknesses": [],
                    "opportunities": [],
                    "threats": [],
                },
                "industry_context": {
                    "market_characteristics": "",
                    "growth_trends": "",
                    "regulatory_factors": [],
                    "competitive_dynamics": "",
                    "industry_reports": [],
                },
                "recent_events": [],
                "risk_analysis": {
                    "revenue_concentration": {"flag": False, "details": "", "top_client_percentage": None},
                    "liquidity_concerns": {"flag": False, "cash_runway": "", "details": ""},
                    "related_party_transactions": {"flag": False, "transactions": [], "source": ""},
                    "governance_issues": {"flag": False, "issues": [], "details": ""},
                    "strategic_inconsistencies": {"flag": False, "inconsistencies": []},
                    "financial_red_flags": {"flag": False, "flags": [], "details": ""},
                    "operational_risks": {"flag": False, "risks": []},
                    "market_risks": {"flag": False, "risks": []},
                    "overall_risk_assessment": "low",
                },
            },
        }
