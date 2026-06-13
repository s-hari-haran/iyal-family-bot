from fastapi import APIRouter, HTTPException, Body, Header, Depends
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator
import logging
import datetime
import re
from backend.database import (
    resolve_member_by_phone,
    check_budget_limit,
    record_expense_transaction,
    record_debt_transaction,
    get_recent_family_context,
    get_spending_summary_repo,
    get_goal_status_repo,
    update_goal_progress_repo,
    get_debt_guidance_repo,
    get_family_financial_summary_repo
)

logger = logging.getLogger("uvicorn")
router = APIRouter(prefix="/api/tools", tags=["Bolna Custom Tools"])

# --- Bolna Payload Sanitization ---
# Bolna sends unresolved %(param)s placeholders as literal strings when the LLM
# doesn't fill optional params. We must strip these before Pydantic validation.
_UNRESOLVED_PLACEHOLDER = re.compile(r"^%\(.+\)s$")

def _sanitize_bolna_value(val: Any) -> Any:
    """Converts unresolved Bolna placeholders and empty strings to None."""
    if isinstance(val, str):
        val = val.strip()
        if not val or _UNRESOLVED_PLACEHOLDER.match(val):
            return None
    return val

def _coerce_float(val: Any, default: float = 0.0) -> float:
    """Safely coerce a value to float, handling strings and placeholders."""
    val = _sanitize_bolna_value(val)
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

class IdentityPayload(BaseModel):
    phone_number: str = Field(..., description="The caller's phone number")
    member_name: Optional[str] = Field(None, description="The explicitly confirmed name of the speaker")
    call_id: Optional[str] = Field(None, description="The unique Bolna call execution ID (auto-injected via %(call_sid)s)")

    @model_validator(mode="before")
    @classmethod
    def sanitize_bolna_placeholders(cls, values):
        if isinstance(values, dict):
            for key in list(values.keys()):
                values[key] = _sanitize_bolna_value(values[key])
            # Ensure phone_number is never None after sanitization
            if not values.get("phone_number"):
                values["phone_number"] = "+919538133265"  # fallback default family phone
            if not values.get("call_id"):
                import uuid
                values["call_id"] = f"manual-{uuid.uuid4()}"
        return values

class ExpenseToolPayload(IdentityPayload):
    amount: Any = Field(..., description="Amount spent in INR")
    category: str = Field("misc", description="Category of expenditure (e.g. groceries, fuel, tuition)")
    date: Optional[str] = Field(None, description="ISO format date string (YYYY-MM-DD)")
    description: Optional[str] = Field(None, description="Brief note about the expense")
    confidence: Any = Field(1.0, description="STT/LLM extraction confidence level (0.0 to 1.0)")

    @model_validator(mode="before")
    @classmethod
    def coerce_numeric_fields(cls, values):
        if isinstance(values, dict):
            values["amount"] = _coerce_float(values.get("amount"), 0.0)
            values["confidence"] = _coerce_float(values.get("confidence"), 0.9)
            # Default date to today if unresolved or missing
            date_val = _sanitize_bolna_value(values.get("date"))
            if not date_val:
                values["date"] = datetime.date.today().isoformat()
            else:
                values["date"] = date_val
        return values

class DebtToolPayload(IdentityPayload):
    lender_name: str = Field(..., description="Name of the person who lent the money")
    borrower_name: str = Field(..., description="Name of the person who borrowed the money")
    amount: Any = Field(..., description="Amount borrowed/lent in INR")
    due_date: Optional[str] = Field(None, description="Due date for repayment (YYYY-MM-DD)")
    note: Optional[str] = Field(None, description="Notes on the loan")
    confidence: Any = Field(1.0, description="Extraction confidence score")

    @model_validator(mode="before")
    @classmethod
    def coerce_numeric_fields(cls, values):
        if isinstance(values, dict):
            values["amount"] = _coerce_float(values.get("amount"), 0.0)
            values["confidence"] = _coerce_float(values.get("confidence"), 0.9)
            due_val = _sanitize_bolna_value(values.get("due_date"))
            values["due_date"] = due_val
            note_val = _sanitize_bolna_value(values.get("note"))
            values["note"] = note_val
        return values

class BudgetStatusPayload(BaseModel):
    phone_number: str
    member_name: Optional[str] = None
    category: str

    @model_validator(mode="before")
    @classmethod
    def sanitize_bolna_placeholders(cls, values):
        if isinstance(values, dict):
            for key in list(values.keys()):
                values[key] = _sanitize_bolna_value(values[key])
            if not values.get("phone_number"):
                values["phone_number"] = "+919538133265"
            if not values.get("category"):
                values["category"] = "misc"
        return values

class LiteracyPayload(BaseModel):
    query: str = Field(..., description="Financial concept to explain (e.g. PPF, FD, Compounding)")

    @model_validator(mode="before")
    @classmethod
    def sanitize_bolna_placeholders(cls, values):
        if isinstance(values, dict):
            for key in list(values.keys()):
                values[key] = _sanitize_bolna_value(values[key])
            if not values.get("query"):
                values["query"] = "general savings advice"
        return values

# Multilingual dictionary mapping regional languages to English backend keys
MULTILINGUAL_MAP = {
    # Member Names (Hindi, Tamil, Telugu, Malayalam)
    "रमेश": "ramesh", "ரமேஷ்": "ramesh", "రమేష్": "ramesh", "രമേഷ്": "ramesh",
    "सुनिता": "sunita", "सुनीता": "sunita", "சுனிதா": "sunita", "సునీత": "sunita", "സുനിത": "sunita",
    "हरी": "hari", "ஹரி": "hari", "హరి": "hari", "ഹരി": "hari",
    "प्रकाश": "prakash", "பிரகாஷ்": "prakash", "ప్రకాష్": "prakash", "പ്രകാശ്": "prakash",
    
    # Categories
    "किराना": "groceries", "किराने": "groceries", "மளிகை": "groceries", "కిరాణా": "groceries", "പലചരക്ക്": "groceries",
    "उपयोगिता": "utilities", "बिजली": "utilities", "உபயோகம்": "utilities", "యుటిలిటీస్": "utilities", "ഉപയോഗങ്ങൾ": "utilities",
    "ईंधन": "fuel", "पेट्रोल": "fuel", "எரிபொருள்": "fuel", "ఇంధనం": "fuel", "ഇന്ധനം": "fuel", "petrol": "fuel",
    "ट्यूशन": "tuition", "फीस": "tuition", "பயிற்சி": "tuition", "ట్యూషన్": "tuition", "ട്യൂഷൻ": "tuition",
    "विविध": "misc", "இதர": "misc", "ఇతర": "misc", "മറ്റ്": "misc",
    "किराया": "rent", "வாடகை": "rent", "అద్దె": "rent", "വാടക": "rent",
    
    # Goals
    "आपातकालीन निधि": "emergency fund", "आपातकाल": "emergency fund", "அவசர நிதி": "emergency fund", "అత్యవసర నిధి": "emergency fund", "അടിയന്തര ഫണ്ട്": "emergency fund", "emergency": "emergency fund",
    "छुट्टी": "vacation", "விடுமுறை": "vacation", "సెలవు": "vacation", "അവധിക്കാലം": "vacation"
}

def normalize_string(val: Optional[str]) -> Optional[str]:
    """Translates known non-English parameters into internal English keys."""
    if not val:
        return val
    low_val = val.strip().lower()
    return MULTILINGUAL_MAP.get(low_val, low_val)

def get_active_member(phone_number: str, member_name: Optional[str] = None):
    """
    Helper function to resolve identity (phone number + optional member name confirmation).
    """
    logger.info(f"RESOLVING IDENTITY: phone_number={phone_number}, member_name={member_name}")
    members = resolve_member_by_phone(phone_number)
    if not members:
        logger.warning(f"IDENTITY RESOLUTION FAILED: phone_number {phone_number} is not registered!")
        raise HTTPException(
            status_code=400,
            detail="Phone number not registered. Please register this phone on your dashboard."
        )
    
    if len(members) == 1:
        return members[0]
        
    if member_name:
        # Match case-insensitive name
        normalized_name = normalize_string(member_name)
        matched = [m for m in members if m["name"].strip().lower() == normalized_name]
        if matched:
            return matched[0]
            
    # Ambiguous identity -> Return list of choices for Bolna to ask
    names = ", ".join([m["name"] for m in members])
    raise HTTPException(
        status_code=300,
        detail=f"Ambiguous identity. Multiple members share this number: {names}. Please state your name."
    )

@router.post("/record-expense")
async def api_record_expense(payload: ExpenseToolPayload):
    """
    API Tool for recording an expense. Checks budgets and commits according to confidence.
    """
    try:
        member = get_active_member(payload.phone_number, payload.member_name)
    except HTTPException as e:
        if e.status_code == 300:
            return {"status": "identity_clarification_required", "message": e.detail}
        raise e

    family_id = member["family_id"]
    member_id = member["id"]

    # Normalize category for cross-lingual support
    norm_category = normalize_string(payload.category)

    # 1. Budget checking
    budget_info = check_budget_limit(family_id, norm_category, payload.amount)

    # 2. Log transaction using three-tier confidence scale
    db_res = record_expense_transaction(
        family_id=family_id,
        member_id=member_id,
        amount=payload.amount,
        category=norm_category,
        date=payload.date,
        description=payload.description,
        call_id=payload.call_id,
        confidence=payload.confidence
    )

    # Context response back to Bolna
    status_msg = ""
    if db_res["status"] == "exists":
        status_msg = f"This expense of ₹{payload.amount} was already logged."
    elif db_res["entry_status"] == "confirmed":
        status_msg = f"Logged ₹{payload.amount} for {norm_category} by {member['name']}."
    elif db_res["entry_status"] == "needs_review":
        status_msg = f"Logged ₹{payload.amount} for {norm_category} by {member['name']} (marked for dashboard review)."
    else:
        status_msg = f"I noted down ₹{payload.amount} for {norm_category}. Since I'm not fully certain, I saved it to your dashboard pending confirmations panel."

    # Inbound budget alerts to voice
    alert_msg = budget_info["warning"] if budget_info["has_budget"] else ""
    full_voice_response = f"{status_msg} {alert_msg}".strip()

    return {
        "status": "success",
        "entry_status": db_res["entry_status"],
        "voice_response": full_voice_response,
        "budget_limit_exceeded": budget_info.get("remaining", 0) < 0
    }

@router.post("/record-debt")
async def api_record_debt(payload: DebtToolPayload):
    """
    API Tool for recording a debt/loan.
    """
    try:
        member = get_active_member(payload.phone_number, payload.member_name)
    except HTTPException as e:
        if e.status_code == 300:
            return {"status": "identity_clarification_required", "message": e.detail}
        raise e

    family_id = member["family_id"]

    db_res = record_debt_transaction(
        family_id=family_id,
        lender_name=payload.lender_name,
        borrower_name=payload.borrower_name,
        amount=payload.amount,
        due_date=payload.due_date,
        note=payload.note,
        call_id=payload.call_id,
        confidence=payload.confidence
    )

    status_msg = ""
    if db_res["status"] == "exists":
        status_msg = f"This debt record of ₹{payload.amount} was already saved."
    elif db_res["entry_status"] == "active":
        status_msg = f"Recorded that {payload.borrower_name} owes ₹{payload.amount} to {payload.lender_name}."
    elif db_res["entry_status"] == "needs_review":
        status_msg = f"Logged debt of ₹{payload.amount} (marked for dashboard review)."
    else:
        status_msg = f"Noted loan details for ₹{payload.amount}. Placed in the pending review list."

    return {
        "status": "success",
        "entry_status": db_res["entry_status"],
        "voice_response": status_msg
    }

@router.post("/budget-status")
async def api_budget_status(payload: BudgetStatusPayload):
    """
    API Tool to query the remaining amount of a category budget limit.
    """
    members = resolve_member_by_phone(payload.phone_number)
    if not members:
        return {"status": "error", "voice_response": "I couldn't find your family budget profile."}

    family_id = members[0]["family_id"]
    budget_info = check_budget_limit(family_id, payload.category, 0)

    if not budget_info["has_budget"]:
        return {
            "status": "success",
            "voice_response": f"You haven't set a budget limit for {payload.category} yet. You can do that in your dashboard."
        }

    limit = budget_info["limit"]
    spent = budget_info["spent"]
    remaining = limit - spent

    if remaining >= 0:
        msg = f"For {payload.category}, you have spent ₹{spent:.0f} out of ₹{limit:.0f}. You have ₹{remaining:.0f} left this month."
    else:
        msg = f"For {payload.category}, you have spent ₹{spent:.0f} and exceeded your budget limit of ₹{limit:.0f} by ₹{abs(remaining):.0f}."

    return {
        "status": "success",
        "voice_response": msg,
        "limit": limit,
        "spent": spent,
        "remaining": remaining
    }

@router.post("/get-financial-literacy")
async def api_get_financial_literacy(payload: LiteracyPayload):
    """
    Guidance Mode: Literacy Copilot. Explains basic local savings programs.
    Strictly educational: prohibits stock/crypto recommendations or predictions.
    """
    query_lower = payload.query.lower()
    
    # Safety Check: Prohibit stocks, crypto, personalized trading advice
    prohibited_keywords = ["stock", "shares", "crypto", "bitcoin", "ethereum", "trade", "buy call", "put option", "prediction", "forecast", "शेयर", "क्रिप्टो", "बिटकॉइन", "பங்கு", "కుప్ట్ర", "స్టాక్"]
    if any(kw in query_lower for kw in prohibited_keywords):
        return {
            "status": "warning",
            "voice_response": "I am an educational savings copilot and cannot give regulated stock recommendations, crypto advice, or market predictions. I can help explain safe household savings like Fixed Deposits, Public Provident Fund, or compounding."
        }

    # Concept Explanations
    if "ppf" in query_lower or "provident" in query_lower or "पीपीएफ" in query_lower or "பிபிஎப்" in query_lower:
        explanation = (
            "The Public Provident Fund, or PPF, is a highly secure, government-backed savings scheme in India. "
            "It offers tax benefits under Section 80C, has a lock-in period of 15 years, and interest is compound-adjusted. "
            "It is a great choice for long-term safe goals like child education or retirement."
        )
    elif "sukanya" in query_lower or "ssy" in query_lower or "सुकन्या" in query_lower or "சுகன்யா" in query_lower:
        explanation = (
            "Sukanya Samriddhi Yojana is a government savings program specifically for girls below 10 years. "
            "It currently offers a higher tax-free interest rate, helps build a fund for education or marriage, "
            "and can be opened at any post office or bank branch."
        )
    elif "compounding" in query_lower or "compound interest" in query_lower or "चक्रवृद्धि" in query_lower or "கூட்டு வட்டி" in query_lower:
        explanation = (
            "Compounding means earning interest on your interest. In simple words, when you save money "
            "and get interest, that interest is added back to your balance, so next time you earn interest "
            "on a larger amount. Over time, like 10 or 20 years, even small monthly savings can grow significantly."
        )
    elif "fixed deposit" in query_lower or "fd" in query_lower or "फिक्स्ड डिपॉजिट" in query_lower or "நிலையான வைப்பு" in query_lower:
        explanation = (
            "A Fixed Deposit is where you lock a lump sum amount in a bank for a set time (like 1 to 5 years) "
            "for a guaranteed interest rate. It is very safe, though returns are fully taxable unless it is a 5-year tax-saver FD."
        )
    elif "recurring deposit" in query_lower or "rd" in query_lower or "आरडी" in query_lower:
        explanation = (
            "A Recurring Deposit allows you to invest a fixed amount of money every month (like ₹1,000) "
            "for a chosen tenure. It helps discipline your monthly savings habits while earning fixed interest rates similar to FDs."
        )
    elif "emergency fund" in query_lower or "emergency" in query_lower or "आपातकालीन" in query_lower or "அவசரநிதி" in query_lower:
        explanation = (
            "An emergency fund is money kept aside for unexpected expenses, like medical bills or sudden loss of income. "
            "It is recommended to have 3 to 6 months of household expenses kept in highly liquid safe options, "
            "like a standard bank savings account or a sweep-in Fixed Deposit."
        )
    else:
        explanation = (
            "I can explain household budgeting concepts, Fixed Deposits, Recurring Deposits, Public Provident Fund (PPF), "
            "Sukanya Samriddhi Yojana, or compound interest. Which of these safe options would you like to learn about?"
        )

    return {
        "status": "success",
        "voice_response": explanation
    }

class SpendingSummaryPayload(BaseModel):
    phone_number: str
    category: Optional[str] = Field(None, description="Category of interest (e.g. groceries, fuel)")
    member_name: Optional[str] = Field(None, description="Name of family member (e.g. Ramesh, Sunita)")
    timeframe: Optional[str] = Field("month", description="Timeframe: 'week' or 'month'")
    largest_only: Optional[bool] = Field(False, description="Set to true if user is asking for the largest expense")

    @model_validator(mode="before")
    @classmethod
    def sanitize_bolna_placeholders(cls, values):
        if isinstance(values, dict):
            for key in list(values.keys()):
                values[key] = _sanitize_bolna_value(values[key])
            if not values.get("phone_number"):
                values["phone_number"] = "+919538133265"
            # Handle largest_only as string "true"/"false" from Bolna
            lo = values.get("largest_only")
            if isinstance(lo, str):
                values["largest_only"] = lo.lower() == "true"
            elif lo is None:
                values["largest_only"] = False
            if not values.get("timeframe"):
                values["timeframe"] = "month"
        return values

class FinancialSummaryPayload(BaseModel):
    phone_number: str
    member_name: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def sanitize_bolna_placeholders(cls, values):
        if isinstance(values, dict):
            for key in list(values.keys()):
                values[key] = _sanitize_bolna_value(values[key])
            if not values.get("phone_number"):
                values["phone_number"] = "+919538133265"
        return values

class GoalStatusPayload(BaseModel):
    phone_number: str
    member_name: Optional[str] = None
    goal_name: str = Field(..., description="Name of the savings goal (e.g. emergency fund, education)")

    @model_validator(mode="before")
    @classmethod
    def sanitize_bolna_placeholders(cls, values):
        if isinstance(values, dict):
            for key in list(values.keys()):
                values[key] = _sanitize_bolna_value(values[key])
            if not values.get("phone_number"):
                values["phone_number"] = "+919538133265"
        return values

class GoalUpdatePayload(IdentityPayload):
    goal_name: str = Field(..., description="Name of the savings goal (e.g. emergency fund, education)")
    amount: Any = Field(..., description="Amount to contribute in INR")
    confidence: Any = Field(1.0, description="Extraction confidence score")

    @model_validator(mode="before")
    @classmethod
    def coerce_numeric_fields(cls, values):
        if isinstance(values, dict):
            values["amount"] = _coerce_float(values.get("amount"), 0.0)
            values["confidence"] = _coerce_float(values.get("confidence"), 0.9)
        return values

class DebtGuidancePayload(BaseModel):
    phone_number: str
    member_name: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def sanitize_bolna_placeholders(cls, values):
        if isinstance(values, dict):
            for key in list(values.keys()):
                values[key] = _sanitize_bolna_value(values[key])
            if not values.get("phone_number"):
                values["phone_number"] = "+919538133265"
        return values

@router.post("/spending-summary")
async def api_spending_summary(payload: SpendingSummaryPayload):
    """
    API Tool to query total/category spending or specific member expenditures.
    """
    members = resolve_member_by_phone(payload.phone_number)
    if not members:
        return {"status": "error", "voice_response": "I couldn't find your family budget profile."}
        
    family_id = members[0]["family_id"]
    res = get_spending_summary_repo(
        family_id=family_id,
        category=payload.category,
        member_name=payload.member_name,
        timeframe=payload.timeframe or "month",
        largest_only=payload.largest_only or False
    )
    return {
        "status": "success",
        "voice_response": res["voice_response"],
        "total_amount": res["total_amount"]
    }

@router.post("/financial-summary")
async def api_financial_summary(payload: FinancialSummaryPayload):
    """
    API Tool for holistic family financial summary.
    """
    members = resolve_member_by_phone(payload.phone_number)
    if not members:
        return {"status": "error", "voice_response": "I couldn't find your family financial profile."}

    family_id = members[0]["family_id"]
    summary = get_family_financial_summary_repo(family_id)
    
    # Calculate spending this month
    today = datetime.date.today()
    start_of_month = today.replace(day=1).isoformat()
    monthly_expenses = [e for e in summary.get("expenses", []) if e.get("date", "") >= start_of_month]
    total_spent = sum(float(e["amount"]) for e in monthly_expenses)
    
    # Identify top category spent this month
    category_totals = {}
    for e in monthly_expenses:
        cat = e["category"]
        category_totals[cat] = category_totals.get(cat, 0.0) + float(e["amount"])
    
    top_categories_str = "none"
    if category_totals:
        sorted_cats = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        top_categories_str = ", ".join([f"{cat} (₹{amt:.0f})" for cat, amt in sorted_cats[:2]])
        
    # Active debts
    active_debts = summary.get("active_debts", [])
    total_debts = sum(float(d["amount"]) for d in active_debts)
    
    # Goals progress
    goals = summary.get("goals", [])
    goals_progress_list = []
    for g in goals:
        pct = (float(g["current_amount"]) / float(g["target_amount"])) * 100 if float(g["target_amount"]) > 0 else 0
        goals_progress_list.append(f"{g['goal_name']}: {pct:.0f}% saved")
    goals_str = "; ".join(goals_progress_list) if goals_progress_list else "no goals set"

    voice_response = (
        f"Here is your family financial summary. This month, the family spent a total of ₹{total_spent:.0f}. "
        f"Your highest spending was on {top_categories_str}. "
        f"You have ₹{total_debts:.0f} in outstanding debts. "
        f"For savings goals, your progress is: {goals_str}. "
        f"Overall, you're managing collaborative savings nicely. Keep it up!"
    )

    return {
        "status": "success",
        "voice_response": voice_response,
        "total_spent": total_spent,
        "total_debts": total_debts
    }

@router.post("/goal-status")
async def api_goal_status(payload: GoalStatusPayload):
    """
    API Tool to query savings goal status.
    """
    members = resolve_member_by_phone(payload.phone_number)
    if not members:
        return {"status": "error", "voice_response": "I couldn't find your family profile."}

    family_id = members[0]["family_id"]
    res = get_goal_status_repo(family_id, normalize_string(payload.goal_name))
    return res

@router.post("/goal-update")
async def api_goal_update(payload: GoalUpdatePayload):
    """
    API Tool for voice-based savings goal contribution.
    """
    try:
        norm_name = normalize_string(payload.member_name) if payload.member_name else None
        member = get_active_member(payload.phone_number, norm_name)
    except HTTPException as e:
        if e.status_code == 300:
            return {"status": "identity_clarification_required", "message": e.detail}
        raise e

    family_id = member["family_id"]
    member_id = member["id"]
    
    try:
        res = update_goal_progress_repo(
            family_id=family_id,
            goal_name=normalize_string(payload.goal_name),
            amount=payload.amount,
            member_id=member_id,
            call_id=payload.call_id,
            confidence=payload.confidence
        )
        return res
    except Exception as e:
        return {"status": "error", "voice_response": f"Sorry, I had trouble updating your goal: {str(e)}"}

@router.post("/debt-guidance")
async def api_debt_guidance(payload: DebtGuidancePayload):
    """
    API Tool to query family debt priorities and reduction advice.
    """
    members = resolve_member_by_phone(payload.phone_number)
    if not members:
        return {"status": "error", "voice_response": "I couldn't find your family profile."}

    family_id = members[0]["family_id"]
    res = get_debt_guidance_repo(family_id)
    return res
