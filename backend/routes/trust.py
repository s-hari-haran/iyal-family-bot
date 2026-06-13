from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import json
import os
import logging
import httpx
from backend.config import settings
from backend.database import (
    get_pending_confirmations_repo,
    verify_medium_confidence_expense_repo,
    verify_low_confidence_request_repo,
    discard_confirmation_request_repo,
    get_voice_timeline_repo,
    get_family_financial_summary_repo,
    delete_expense_repo,
    delete_debt_repo,
    update_expense_repo,
    update_debt_repo,
    get_members_repo,
    update_member_repo,
    get_family_name_repo,
    update_family_name_repo,
    update_budget_limit_repo,
    create_budget_repo,
    delete_budget_repo,
    update_goal_repo,
    create_goal_repo,
    delete_goal_repo
)

logger = logging.getLogger("uvicorn")

router = APIRouter(prefix="/api/trust", tags=["Trust Layer Dashboard"])

class ConfirmRequestPayload(BaseModel):
    amount: float
    category: str
    date: Optional[str] = None
    description: Optional[str] = None
    lender_name: Optional[str] = None
    borrower_name: Optional[str] = None
    due_date: Optional[str] = None
    note: Optional[str] = None

@router.get("/pending-confirmations/{family_id}")
async def get_pending_confirmations(family_id: str):
    """
    Returns items requiring family confirmation (Low and Medium confidence logs).
    """
    try:
        return get_pending_confirmations_repo(family_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-expense/{expense_id}")
async def verify_medium_confidence_expense(expense_id: str):
    """
    Verifies a medium confidence expense (status 'needs_review' -> 'confirmed').
    """
    try:
        res = verify_medium_confidence_expense_repo(expense_id)
        if not res:
            raise HTTPException(status_code=404, detail="Expense not found")
        return {"status": "success", "message": "Expense verified to memory", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-request/{request_id}")
async def verify_low_confidence_request(request_id: str, payload: ConfirmRequestPayload):
    """
    Verifies a low confidence request, creates the final transaction, and marks request as confirmed.
    """
    try:
        res = verify_low_confidence_request_repo(request_id, payload.model_dump())
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/discard-request/{request_id}")
async def discard_confirmation_request(request_id: str):
    """
    Discards/rejects a low confidence request.
    """
    try:
        res = discard_confirmation_request_repo(request_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/timeline/{family_id}")
async def get_voice_timeline(family_id: str):
    """
    Returns a timeline of voice conversations (call_logs) for a family.
    """
    try:
        return get_voice_timeline_repo(family_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary/{family_id}")
async def get_family_financial_summary(family_id: str):
    """
    Returns summary stats, budgets vs spent, goals progress, and total debt outstanding.
    """
    try:
        return get_family_financial_summary_repo(family_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset-data/{family_id}")
async def reset_data(family_id: str):
    """
    Clears transactions, debts, confirmation requests, and call logs for a family.
    Resets goals progress to 0.
    """
    try:
        from backend.database import is_local_mode, SQLITE_PATH, supabase_client
        import sqlite3
        if not is_local_mode:
            supabase_client.table("expenses").delete().eq("family_id", family_id).execute()
            supabase_client.table("debts").delete().eq("family_id", family_id).execute()
            supabase_client.table("confirmation_requests").delete().eq("family_id", family_id).execute()
            supabase_client.table("call_logs").delete().eq("family_id", family_id).execute()
            supabase_client.table("memory_events").delete().eq("family_id", family_id).execute()
            supabase_client.table("goals").update({"current_amount": 0.0}).eq("family_id", family_id).execute()
        else:
            conn = sqlite3.connect(SQLITE_PATH)
            c = conn.cursor()
            c.execute("DELETE FROM expenses WHERE family_id = ?", (family_id,))
            c.execute("DELETE FROM debts WHERE family_id = ?", (family_id,))
            c.execute("DELETE FROM confirmation_requests WHERE family_id = ?", (family_id,))
            c.execute("DELETE FROM call_logs WHERE family_id = ?", (family_id,))
            c.execute("DELETE FROM memory_events WHERE family_id = ?", (family_id,))
            c.execute("UPDATE goals SET current_amount = 0.0 WHERE family_id = ?", (family_id,))
            conn.commit()
            conn.close()
        return {"status": "success", "message": "Database entries successfully cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class TriggerCallPayload(BaseModel):
    phone_number: str
    member_name: Optional[str] = None

@router.post("/trigger-call")
async def trigger_call(payload: TriggerCallPayload):
    """
    Triggers an outbound call using Bolna's calling API.
    """
    logger.info(f"Triggering Bolna outbound call to: {payload.phone_number} for {payload.member_name}")
    
    agent_id = "9ce8d3e3-1513-461e-aad1-3b8f2d933ee1" # fallback
    try:
        existing_agent_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "existing_agent.json")
        if os.path.exists(existing_agent_path):
            with open(existing_agent_path, "r", encoding="utf-8") as f:
                agent_data = json.load(f)
                if "id" in agent_data:
                    agent_id = agent_data["id"]
                    logger.info(f"Loaded agent_id from existing_agent.json: {agent_id}")
    except Exception as e:
        logger.error(f"Error reading existing_agent.json: {e}")

    bolna_payload = {
        "agent_id": agent_id,
        "recipient_phone_number": payload.phone_number,
        "bypass_call_guardrails": True
    }
    
    if payload.member_name:
        bolna_payload["user_data"] = {
            "member_name": payload.member_name
        }

    headers = {
        "Authorization": f"Bearer {settings.BOLNA_API_KEY}",
        "Content-Type": "application/json"
    }

    logger.info(f"Sending request to Bolna API: https://api.bolna.ai/call. Payload: {bolna_payload}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.bolna.ai/call", json=bolna_payload, headers=headers, timeout=30.0)
            
            if response.status_code in [200, 201]:
                res_data = response.json()
                logger.info(f"Bolna outbound call triggered successfully: {res_data}")
                return {
                    "status": "success",
                    "message": "Outbound call successfully triggered via Bolna",
                    "details": res_data
                }
            else:
                logger.error(f"Bolna API failed with status {response.status_code}: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Bolna API error: {response.text}"
                )
    except httpx.RequestError as exc:
        logger.error(f"HTTP Request failed while calling Bolna API: {exc}")
        raise HTTPException(
            status_code=502,
            detail=f"Could not connect to Bolna API: {str(exc)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in trigger_call: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

class UpdateExpensePayload(BaseModel):
    amount: float
    category: str
    description: str

class UpdateDebtPayload(BaseModel):
    amount: float
    lender_name: str
    borrower_name: str
    note: str

@router.delete("/expense/{expense_id}")
async def delete_expense(expense_id: str):
    """Deletes an expense record."""
    try:
        success = delete_expense_repo(expense_id)
        if not success:
            raise HTTPException(status_code=404, detail="Expense not found")
        return {"status": "success", "message": "Expense deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/debt/{debt_id}")
async def delete_debt(debt_id: str):
    """Deletes a debt record."""
    try:
        success = delete_debt_repo(debt_id)
        if not success:
            raise HTTPException(status_code=404, detail="Debt not found")
        return {"status": "success", "message": "Debt deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/expense/{expense_id}")
async def update_expense(expense_id: str, payload: UpdateExpensePayload):
    """Updates an expense record."""
    try:
        success = update_expense_repo(expense_id, payload.amount, payload.category, payload.description)
        if not success:
            raise HTTPException(status_code=404, detail="Expense not found")
        return {"status": "success", "message": "Expense updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/debt/{debt_id}")
async def update_debt(debt_id: str, payload: UpdateDebtPayload):
    """Updates a debt record."""
    try:
        success = update_debt_repo(debt_id, payload.amount, payload.lender_name, payload.borrower_name, payload.note)
        if not success:
            raise HTTPException(status_code=404, detail="Debt not found")
        return {"status": "success", "message": "Debt updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class UpdateMemberPayload(BaseModel):
    name: str
    role: str
    phone_number: str
    preferred_language: str


@router.get("/members/{family_id}")
async def get_members(family_id: str):
    """
    Retrieves all family members for profile configuration.
    """
    try:
        return get_members_repo(family_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/members/{member_id}")
async def update_member(member_id: str, payload: UpdateMemberPayload):
    """
    Updates a family member's configurations.
    """
    try:
        res = update_member_repo(
            member_id=member_id,
            name=payload.name,
            role=payload.role,
            phone_number=payload.phone_number,
            preferred_language=payload.preferred_language
        )
        if not res:
            raise HTTPException(status_code=404, detail="Member not found")
        return {"status": "success", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class UpdateBudgetPayload(BaseModel):
    monthly_limit: float

class CreateBudgetPayload(BaseModel):
    family_id: str
    category: str
    monthly_limit: float

class UpdateGoalPayload(BaseModel):
    goal_name: str
    target_amount: float
    target_date: str

class CreateGoalPayload(BaseModel):
    family_id: str
    goal_name: str
    target_amount: float
    target_date: str
    importance_level: str = "medium"

class UpdateFamilyPayload(BaseModel):
    name: str


@router.put("/budget/{budget_id}")
async def update_budget(budget_id: str, payload: UpdateBudgetPayload):
    """Updates a budget's monthly limit."""
    try:
        success = update_budget_limit_repo(budget_id, payload.monthly_limit)
        if not success:
            raise HTTPException(status_code=404, detail="Budget not found")
        return {"status": "success", "message": "Budget updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/budget")
async def create_budget(payload: CreateBudgetPayload):
    """Creates a new budget entry."""
    try:
        budget = create_budget_repo(payload.family_id, payload.category, payload.monthly_limit)
        return {"status": "success", "data": budget}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/budget/{budget_id}")
async def delete_budget(budget_id: str):
    """Deletes a budget entry."""
    try:
        success = delete_budget_repo(budget_id)
        if not success:
            raise HTTPException(status_code=404, detail="Budget not found")
        return {"status": "success", "message": "Budget deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/goal/{goal_id}")
async def update_goal(goal_id: str, payload: UpdateGoalPayload):
    """Updates a goal's details."""
    try:
        success = update_goal_repo(goal_id, payload.goal_name, payload.target_amount, payload.target_date)
        if not success:
            raise HTTPException(status_code=404, detail="Goal not found")
        return {"status": "success", "message": "Goal updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/goal")
async def create_goal(payload: CreateGoalPayload):
    """Creates a new goal."""
    try:
        goal = create_goal_repo(payload.family_id, payload.goal_name, payload.target_amount, payload.target_date, payload.importance_level)
        return {"status": "success", "data": goal}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/goal/{goal_id}")
async def delete_goal(goal_id: str):
    """Deletes a goal."""
    try:
        success = delete_goal_repo(goal_id)
        if not success:
            raise HTTPException(status_code=404, detail="Goal not found")
        return {"status": "success", "message": "Goal deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/family/{family_id}")
async def update_family(family_id: str, payload: UpdateFamilyPayload):
    """Updates the family name."""
    try:
        success = update_family_name_repo(family_id, payload.name)
        if not success:
            raise HTTPException(status_code=404, detail="Family not found")
        return {"status": "success", "message": "Family name updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/family/{family_id}")
async def get_family(family_id: str):
    """Retrieves the family name."""
    try:
        name = get_family_name_repo(family_id)
        if name is None:
            raise HTTPException(status_code=404, detail="Family not found")
        return {"name": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
