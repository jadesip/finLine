"""
finLine Chat API

Natural language interface for updating financial models.
Parses user intent and returns structured updates.
"""

import json
import logging
import re
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from api.auth import CurrentUser
from database import get_project as db_get_project, update_project as db_update_project
from services.llm import get_llm_client

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# Request/Response Models
# ============================================================

class ChatMessage(BaseModel):
    """Chat message from user."""
    message: str
    case_id: str = "base_case"
    auto_apply: bool = False  # If True, apply changes without confirmation


class ChatUpdate(BaseModel):
    """A single update extracted from chat."""
    path: str
    value: Any
    description: str


class ChatResponse(BaseModel):
    """Chat response with proposed updates."""
    response: str
    updates: list[ChatUpdate] = []
    applied: bool = False
    error: str | None = None


# ============================================================
# System Prompt for Intent Parsing
# ============================================================

SYSTEM_PROMPT = """You are a financial modeling assistant for an LBO (Leveraged Buyout) analysis tool.
Your job is to parse user requests and extract structured updates to the financial model.

The model has this structure for each case:
- deal_parameters:
  - deal_date, exit_date (format: "YYYY-MM-DD")
  - tax_rate (decimal, e.g., 0.25 for 25%)
  - minimum_cash (number)
  - entry_fee_percentage, exit_fee_percentage (number, e.g., 2.0 for 2%)
  - entry_valuation.multiple (number, e.g., 10.0)
  - exit_valuation.multiple (number, e.g., 8.0)
  - capital_structure.tranches (array of debt tranches)

- financials.income_statement:
  - revenue (object with year values)
  - ebitda (array: [{year, value}, ...])
  - ebit (array: [{year, value}, ...])
  - d_and_a (array: [{year, value}, ...])

- financials.cash_flow_statement:
  - capex (object with values array)
  - working_capital (object with values array)

When the user makes a request, respond with a JSON object containing:
{
  "response": "Human-readable confirmation of what you understood",
  "updates": [
    {
      "path": "dot.notation.path.to.field",
      "value": <the new value>,
      "description": "Brief description of what this changes"
    }
  ]
}

IMPORTANT RULES:
1. For financial data (EBITDA, revenue, etc.), include ALL years when updating.
2. For percentages in text (e.g., "25%"), convert to decimals for tax_rate (0.25) but keep as numbers for fee percentages (25.0).
3. For multiples (e.g., "10x"), extract just the number (10.0).
4. For growth formulas, calculate and provide explicit year values.
5. All paths start from the case level (e.g., "deal_parameters.tax_rate" not "cases.base_case.deal_parameters.tax_rate").
6. If you can't understand the request, set updates to empty array and explain in response.
7. ALWAYS respond with valid JSON only - no markdown, no code blocks, just the JSON object.

Examples:
User: "Set the entry multiple to 12x"
Response: {"response": "I'll set the entry valuation multiple to 12.0x", "updates": [{"path": "deal_parameters.entry_valuation.multiple", "value": 12.0, "description": "Entry multiple"}]}

User: "Change tax rate to 30%"
Response: {"response": "I'll update the tax rate to 30%", "updates": [{"path": "deal_parameters.tax_rate", "value": 0.30, "description": "Tax rate"}]}

User: "Set EBITDA to 100 in 2024, growing 10% annually through 2029"
Response: {"response": "I'll set EBITDA starting at 100 in 2024 with 10% annual growth", "updates": [{"path": "financials.income_statement.ebitda", "value": [{"year": "2024", "value": 100}, {"year": "2025", "value": 110}, {"year": "2026", "value": 121}, {"year": "2027", "value": 133.1}, {"year": "2028", "value": 146.41}, {"year": "2029", "value": 161.05}], "description": "EBITDA with 10% growth"}]}
"""


# ============================================================
# Helper Functions
# ============================================================

def extract_json_from_response(text: str) -> dict:
    """Extract JSON from LLM response, handling various formats."""
    # Try direct parse first
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

    # Try to find JSON object anywhere in text
    brace_match = re.search(r'\{[\s\S]*\}', text)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    logger.warning(f"Could not extract JSON from response: {text[:200]}...")
    return {"response": text, "updates": []}


def apply_updates_to_project(data: dict, case_id: str, updates: list[dict]) -> dict:
    """Apply updates to project data."""
    case_data = data.get("cases", {}).get(case_id, {})

    for update in updates:
        path = update["path"]
        value = update["value"]

        # Navigate to the right location
        keys = path.split(".")
        current = case_data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value
        logger.info(f"Applied update: {path} = {value}")

    data["cases"][case_id] = case_data
    return data


# ============================================================
# Endpoints
# ============================================================

@router.post("/{project_id}/chat", response_model=ChatResponse)
async def chat_with_project(
    project_id: str,
    message: ChatMessage,
    current_user: CurrentUser
):
    """
    Chat interface for updating financial models.

    Parses natural language requests and returns structured updates.
    If auto_apply is True, applies changes immediately.
    """
    logger.info(f"Chat request for project {project_id}: {message.message[:100]}...")

    # Get project
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

    # Check if case exists
    data = project["data"]
    if message.case_id not in data.get("cases", {}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Case '{message.case_id}' not found"
        )

    # Get current state for context
    case_data = data["cases"][message.case_id]
    deal_params = case_data.get("deal_parameters", {})
    financials = case_data.get("financials", {})

    context = f"""Current project state for case '{message.case_id}':
- Deal date: {deal_params.get('deal_date', 'not set')}
- Exit date: {deal_params.get('exit_date', 'not set')}
- Entry multiple: {deal_params.get('entry_valuation', {}).get('multiple', 'not set')}x
- Exit multiple: {deal_params.get('exit_valuation', {}).get('multiple', 'not set')}x
- Tax rate: {deal_params.get('tax_rate', 0.25) * 100:.0f}%
- EBITDA periods: {len(financials.get('income_statement', {}).get('ebitda', []))} years
- Debt tranches: {len(deal_params.get('capital_structure', {}).get('tranches', []))}

User request: {message.message}"""

    try:
        # Call LLM
        llm = get_llm_client()
        response_text = await llm.chat([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context}
        ])

        # Parse response
        parsed = extract_json_from_response(response_text)
        response_msg = parsed.get("response", "I understood your request.")
        updates = parsed.get("updates", [])

        logger.info(f"LLM parsed {len(updates)} updates")

        # Convert to ChatUpdate models
        chat_updates = [
            ChatUpdate(
                path=u.get("path", ""),
                value=u.get("value"),
                description=u.get("description", "")
            )
            for u in updates
            if u.get("path")
        ]

        # Apply if auto_apply is True
        applied = False
        if message.auto_apply and chat_updates:
            try:
                updated_data = apply_updates_to_project(
                    data,
                    message.case_id,
                    [u.model_dump() for u in chat_updates]
                )
                await db_update_project(project_id, updated_data)
                applied = True
                response_msg += " Changes have been applied."
                logger.info(f"Auto-applied {len(chat_updates)} updates to project {project_id}")
            except Exception as e:
                logger.error(f"Failed to apply updates: {e}")
                return ChatResponse(
                    response=response_msg,
                    updates=chat_updates,
                    applied=False,
                    error=f"Failed to apply updates: {str(e)}"
                )

        return ChatResponse(
            response=response_msg,
            updates=chat_updates,
            applied=applied
        )

    except Exception as e:
        logger.error(f"Chat processing failed: {e}", exc_info=True)
        return ChatResponse(
            response="I encountered an error processing your request.",
            updates=[],
            applied=False,
            error=str(e)
        )


@router.post("/{project_id}/chat/apply", response_model=ChatResponse)
async def apply_chat_updates(
    project_id: str,
    updates: list[ChatUpdate],
    current_user: CurrentUser,
    case_id: str = "base_case"
):
    """
    Apply previously proposed chat updates.

    Use this endpoint to apply updates that were returned by the chat endpoint
    but not auto-applied.
    """
    logger.info(f"Applying {len(updates)} chat updates to project {project_id}")

    # Get project
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

    data = project["data"]
    if case_id not in data.get("cases", {}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Case '{case_id}' not found"
        )

    try:
        updated_data = apply_updates_to_project(
            data,
            case_id,
            [u.model_dump() for u in updates]
        )
        await db_update_project(project_id, updated_data)

        return ChatResponse(
            response=f"Applied {len(updates)} updates successfully.",
            updates=updates,
            applied=True
        )

    except Exception as e:
        logger.error(f"Failed to apply updates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply updates: {str(e)}"
        )
