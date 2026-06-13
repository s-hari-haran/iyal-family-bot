import os
import sqlite3
import json
import datetime
import logging
import uuid
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from backend.config import settings

logger = logging.getLogger("uvicorn")

# Check if we should run in Local SQLite Fallback Mode
is_local_mode = (
    "mock" in settings.SUPABASE_URL.lower() 
    or "mock_service_key" in settings.SUPABASE_SERVICE_KEY 
    or not settings.SUPABASE_URL
)

# Initialize Supabase client if not in local mode
supabase_client: Optional[Client] = None
if not is_local_mode:
    try:
        supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        logger.info("Database: Connected to live Supabase Instance.")
    except Exception as e:
        logger.warning(f"Database: Failed to connect to Supabase ({e}). Switching to Local SQLite Mode.")
        is_local_mode = True
else:
    logger.info("Database: Running in Local SQLite Mode (family_memory.db).")

# --- SQLite Local DB Configuration & Init ---
SQLITE_PATH = os.path.join(os.path.dirname(__file__), "family_memory.db")

def init_sqlite_db(seed_data: bool = False):
    """
    Initializes SQLite tables and seeds mock data if they do not exist.
    """
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 1. families
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS families (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)
    
    # 2. members
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS members (
        id TEXT PRIMARY KEY,
        family_id TEXT NOT NULL REFERENCES families(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        preferred_language TEXT NOT NULL DEFAULT 'en',
        role TEXT NOT NULL DEFAULT 'member',
        created_at TEXT NOT NULL
    );
    """)
    
    # 3. expenses
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id TEXT PRIMARY KEY,
        family_id TEXT NOT NULL REFERENCES families(id) ON DELETE CASCADE,
        member_id TEXT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
        amount REAL NOT NULL,
        currency TEXT NOT NULL DEFAULT 'INR',
        category TEXT NOT NULL DEFAULT 'misc',
        date TEXT NOT NULL,
        description TEXT,
        status TEXT NOT NULL,
        importance_level TEXT NOT NULL,
        call_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)
    
    # 4. debts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS debts (
        id TEXT PRIMARY KEY,
        family_id TEXT NOT NULL REFERENCES families(id) ON DELETE CASCADE,
        lender_name TEXT NOT NULL,
        borrower_name TEXT NOT NULL,
        amount REAL NOT NULL,
        due_date TEXT,
        note TEXT,
        status TEXT NOT NULL,
        importance_level TEXT NOT NULL,
        call_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)
    
    # 5. goals
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS goals (
        id TEXT PRIMARY KEY,
        family_id TEXT NOT NULL REFERENCES families(id) ON DELETE CASCADE,
        goal_name TEXT NOT NULL,
        target_amount REAL NOT NULL,
        current_amount REAL NOT NULL DEFAULT 0.0,
        target_date TEXT NOT NULL,
        importance_level TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)
    
    # 6. budgets
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        id TEXT PRIMARY KEY,
        family_id TEXT NOT NULL REFERENCES families(id) ON DELETE CASCADE,
        category TEXT NOT NULL,
        monthly_limit REAL NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(family_id, category)
    );
    """)
    
    # 7. recurring_expenses
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recurring_expenses (
        id TEXT PRIMARY KEY,
        family_id TEXT NOT NULL REFERENCES families(id) ON DELETE CASCADE,
        member_id TEXT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        frequency TEXT NOT NULL,
        next_due_date TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)
    
    # 8. insights
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS insights (
        id TEXT PRIMARY KEY,
        family_id TEXT NOT NULL REFERENCES families(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        insight_type TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)
    
    # 9. memory_events
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memory_events (
        id TEXT PRIMARY KEY,
        family_id TEXT NOT NULL REFERENCES families(id) ON DELETE CASCADE,
        event_type TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)
    
    # 10. confirmation_requests
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS confirmation_requests (
        id TEXT PRIMARY KEY,
        family_id TEXT NOT NULL REFERENCES families(id) ON DELETE CASCADE,
        item_type TEXT NOT NULL,
        raw_value TEXT NOT NULL, -- Stored as JSON string in SQLite
        status TEXT NOT NULL,
        confidence_score REAL NOT NULL,
        uncertainty_reason TEXT,
        created_at TEXT NOT NULL
    );
    """)
    
    # 11. call_logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS call_logs (
        id TEXT PRIMARY KEY,
        call_id TEXT UNIQUE NOT NULL,
        family_id TEXT REFERENCES families(id) ON DELETE CASCADE,
        member_id TEXT REFERENCES members(id) ON DELETE SET NULL,
        transcript TEXT NOT NULL, -- Stored as JSON string
        extracted_json TEXT NOT NULL, -- Stored as JSON string
        confidence REAL NOT NULL,
        status TEXT NOT NULL,
        recording_url TEXT,
        created_at TEXT NOT NULL
    );
    """)
    
    if seed_data:
        cursor.execute("SELECT COUNT(*) FROM families WHERE id = 'f8e56bdf-99a3-4813-8b77-3e5f7b88939c'")
        if cursor.fetchone()[0] == 0:
            logger.info("Database: Seeding default SQLite Sharma Family details.")
            now = datetime.datetime.now().isoformat()

            cursor.execute(
                "INSERT INTO families (id, name, created_at) VALUES (?, ?, ?)",
                ("f8e56bdf-99a3-4813-8b77-3e5f7b88939c", "Sharma Family", now)
            )

            cursor.execute(
                "INSERT INTO members (id, family_id, name, phone_number, preferred_language, role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("m1", "f8e56bdf-99a3-4813-8b77-3e5f7b88939c", "Ramesh", "+919449694564", "en", "Father", now)
            )
            cursor.execute(
                "INSERT INTO members (id, family_id, name, phone_number, preferred_language, role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("m2", "f8e56bdf-99a3-4813-8b77-3e5f7b88939c", "Sunita", "+919538133265", "hi", "Mother", now)
            )
            cursor.execute(
                "INSERT INTO members (id, family_id, name, phone_number, preferred_language, role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("m3", "f8e56bdf-99a3-4813-8b77-3e5f7b88939c", "Hari", "+919538133265", "en", "Son", now)
            )
            cursor.execute(
                "INSERT INTO members (id, family_id, name, phone_number, preferred_language, role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("m4", "f8e56bdf-99a3-4813-8b77-3e5f7b88939c", "Prakash", "+917760599655", "en", "Brother", now)
            )

            budgets_data = [
                ("groceries", 10000.00),
                ("utilities", 5000.00),
                ("fuel", 4000.00),
                ("tuition", 12000.00)
            ]
            for category, limit in budgets_data:
                cursor.execute(
                    "INSERT INTO budgets (id, family_id, category, monthly_limit, created_at) VALUES (?, ?, ?, ?, ?)",
                    (f"b-{category}", "f8e56bdf-99a3-4813-8b77-3e5f7b88939c", category, limit, now)
                )

            cursor.execute(
                "INSERT INTO goals (id, family_id, goal_name, target_amount, current_amount, target_date, importance_level, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("g-1", "f8e56bdf-99a3-4813-8b77-3e5f7b88939c", "Vacation Savings", 80000.00, 15000.00, "2026-12-31", "high", now)
            )
            cursor.execute(
                "INSERT INTO goals (id, family_id, goal_name, target_amount, current_amount, target_date, importance_level, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("g-2", "f8e56bdf-99a3-4813-8b77-3e5f7b88939c", "Emergency Fund", 100000.00, 25000.00, "2026-10-31", "high", now)
            )
            cursor.execute(
                "INSERT INTO goals (id, family_id, goal_name, target_amount, current_amount, target_date, importance_level, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("g-3", "f8e56bdf-99a3-4813-8b77-3e5f7b88939c", "Education Fund", 150000.00, 45000.00, "2027-06-30", "high", now)
            )
            cursor.execute(
                "INSERT INTO goals (id, family_id, goal_name, target_amount, current_amount, target_date, importance_level, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("g-4", "f8e56bdf-99a3-4813-8b77-3e5f7b88939c", "Vehicle Goal", 200000.00, 0.00, "2028-03-31", "medium", now)
            )

            cursor.execute(
                "INSERT INTO debts (id, family_id, lender_name, borrower_name, amount, due_date, note, status, importance_level, call_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("d-1", "f8e56bdf-99a3-4813-8b77-3e5f7b88939c", "Uncle Vinay", "Ramesh", 8000.00, "2026-06-25", "Borrowed for repairs", "active", "high", "seed-call-1", now)
            )

    conn.commit()
    conn.close()


if is_local_mode:
    init_sqlite_db(seed_data=False)


# --- Database Repository Wrapper Functions ---

def resolve_member_by_phone(phone_number: str) -> List[Dict[str, Any]]:
    """
    Looks up family members associated with a phone number.
    Handles shared phone lines for identity resolution.
    Matches phone numbers based on their last 10 digits.
    Falls back to all registered members if the phone number is not recognized.
    """
    cleaned = "".join([c for c in phone_number if c.isdigit()])
    last_10 = cleaned[-10:] if len(cleaned) >= 10 else cleaned

    if not is_local_mode:
        response = supabase_client.table("members").select("id, name, role, family_id, preferred_language").like("phone_number", f"%{last_10}").execute()
        res = response.data
        if not res:
            # Fallback: return default seeded family members
            fallback_res = supabase_client.table("members").select("id, name, role, family_id, preferred_language").execute()
            return fallback_res.data
        return res
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, role, family_id, preferred_language FROM members WHERE phone_number LIKE ?", (f"%{last_10}",))
        rows = cursor.fetchall()
        res = [dict(row) for row in rows]
        if not res:
            # Fallback: return all members in SQLite
            cursor.execute("SELECT id, name, role, family_id, preferred_language FROM members")
            rows = cursor.fetchall()
            res = [dict(row) for row in rows]
        conn.close()
        return res

def get_recent_family_context(family_id: str) -> Dict[str, Any]:
    """
    Retrieves summarized family context for Bolna LLM prompt injection.
    Memory = persisted data + contextual retrieval.
    """
    if not is_local_mode:
        goals_res = supabase_client.table("goals").select("goal_name, target_amount, current_amount, target_date").eq("family_id", family_id).order("target_date").limit(2).execute()
        debts_res = supabase_client.table("debts").select("lender_name, borrower_name, amount, due_date").eq("family_id", family_id).eq("status", "active").order("due_date").limit(3).execute()
        memory_res = supabase_client.table("memory_events").select("event_type, content, created_at").eq("family_id", family_id).order("created_at", desc=True).limit(3).execute()
        budgets_res = supabase_client.table("budgets").select("category, monthly_limit").eq("family_id", family_id).execute()
        return {
            "active_goals": goals_res.data,
            "outstanding_debts": debts_res.data,
            "recent_memory_events": memory_res.data,
            "budgets": budgets_res.data
        }
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Goals
        cursor.execute("SELECT goal_name, target_amount, current_amount, target_date FROM goals WHERE family_id = ? ORDER BY target_date LIMIT 2", (family_id,))
        goals = [dict(r) for r in cursor.fetchall()]
        
        # Debts
        cursor.execute("SELECT lender_name, borrower_name, amount, due_date FROM debts WHERE family_id = ? AND status = 'active' ORDER BY due_date LIMIT 3", (family_id,))
        debts = [dict(r) for r in cursor.fetchall()]
        
        # Memory events
        cursor.execute("SELECT event_type, content, created_at FROM memory_events WHERE family_id = ? ORDER BY created_at DESC LIMIT 3", (family_id,))
        memory = [dict(r) for r in cursor.fetchall()]
        
        # Budgets
        cursor.execute("SELECT category, monthly_limit FROM budgets WHERE family_id = ?", (family_id,))
        budgets = [dict(r) for r in cursor.fetchall()]
        
        conn.close()
        return {
            "active_goals": goals,
            "outstanding_debts": debts,
            "recent_memory_events": memory,
            "budgets": budgets
        }

def check_budget_limit(family_id: str, category: str, amount_to_add: float) -> Dict[str, Any]:
    """
    Calculates the category budget usage for the current month and checks if the limit is exceeded.
    """
    start_of_month = datetime.date.today().replace(day=1).isoformat()
    
    if not is_local_mode:
        budget_res = supabase_client.table("budgets").select("monthly_limit").eq("family_id", family_id).eq("category", category).execute()
        if not budget_res.data:
            return {"has_budget": False, "limit": 0, "spent": 0, "remaining": 0, "warning": ""}
        limit = float(budget_res.data[0]["monthly_limit"])
        
        expenses_res = supabase_client.table("expenses").select("amount").eq("family_id", family_id).eq("category", category).eq("status", "confirmed").gte("date", start_of_month).execute()
        spent = sum(float(exp["amount"]) for exp in expenses_res.data)
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        
        # Get Limit
        cursor.execute("SELECT monthly_limit FROM budgets WHERE family_id = ? AND category = ?", (family_id, category))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return {"has_budget": False, "limit": 0, "spent": 0, "remaining": 0, "warning": ""}
        limit = float(row[0])
        
        # Get Spent
        cursor.execute("SELECT amount FROM expenses WHERE family_id = ? AND category = ? AND status = 'confirmed' AND date >= ?", (family_id, category, start_of_month))
        spent = sum(float(r[0]) for r in cursor.fetchall())
        conn.close()

    new_total = spent + amount_to_add
    remaining = limit - new_total
    
    warning = ""
    percent = (new_total / limit) * 100 if limit > 0 else 0
    if new_total > limit:
        warning = f"Alert: Logging this expense will exceed your monthly {category} limit of ₹{limit:.0f} by ₹{abs(remaining):.0f}."
    elif percent >= 80:
        warning = f"Warning: You have used {percent:.0f}% of your monthly {category} budget limit (₹{new_total:.0f} of ₹{limit:.0f})."

    return {
        "has_budget": True,
        "limit": limit,
        "spent": spent,
        "remaining": remaining,
        "warning": warning
    }

def record_expense_transaction(
    family_id: str,
    member_id: str,
    amount: float,
    category: str,
    date: str,
    description: str,
    call_id: str,
    confidence: float
) -> Dict[str, Any]:
    """
    Logs an expense transaction following the three-tier confirmation logic.
    Supports call_id idempotency.
    """
    now = datetime.datetime.now().isoformat()
    date_val = date or datetime.date.today().isoformat()
    desc_val = description or f"Voice log ({category})"
    
    # Determine importance level
    importance_level = "low"
    if amount >= 5000 or category in ["rent", "tuition"]:
        importance_level = "high"
    elif amount >= 1000 or category in ["utilities"]:
        importance_level = "medium"

    # Determine status based on confidence thresholds
    if confidence >= 0.90:
        entry_status = "confirmed"
    elif confidence >= 0.70:
        entry_status = "needs_review"
    else:
        entry_status = "pending_confirmation"

    if not is_local_mode:
        # Idempotency checks
        existing_exp = supabase_client.table("expenses").select("id, status").eq("call_id", call_id).execute()
        if existing_exp.data:
            return {"status": "exists", "id": existing_exp.data[0]["id"], "type": "expense", "entry_status": existing_exp.data[0]["status"]}
            
        existing_req = supabase_client.table("confirmation_requests").select("id, status").eq("raw_value->>call_id", call_id).execute()
        if existing_req.data:
            return {"status": "exists", "id": existing_req.data[0]["id"], "type": "confirmation_request", "entry_status": existing_req.data[0]["status"]}

        if entry_status in ["confirmed", "needs_review"]:
            data = {
                "family_id": family_id,
                "member_id": member_id,
                "amount": amount,
                "category": category,
                "date": date_val,
                "description": desc_val,
                "status": entry_status,
                "importance_level": importance_level,
                "call_id": call_id
            }
            res = supabase_client.table("expenses").insert(data).execute()
            
            if entry_status == "confirmed" and importance_level == "high":
                supabase_client.table("memory_events").insert({
                    "family_id": family_id,
                    "event_type": "expense_logged",
                    "content": f"High importance expense logged: ₹{amount} spent on {category}."
                }).execute()
                
            return {"status": "success", "id": res.data[0]["id"], "type": "expense", "entry_status": entry_status}
        else:
            # Low confidence -> confirmation_requests
            raw_val = {
                "call_id": call_id,
                "member_id": member_id,
                "amount": amount,
                "category": category,
                "date": date_val,
                "description": desc_val
            }
            data = {
                "family_id": family_id,
                "item_type": "expense",
                "raw_value": raw_val,
                "status": "pending",
                "confidence_score": confidence,
                "uncertainty_reason": "Low transcription confidence."
            }
            res = supabase_client.table("confirmation_requests").insert(data).execute()
            return {"status": "success", "id": res.data[0]["id"], "type": "confirmation_request", "entry_status": "pending"}
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        
        # Idempotency Check in SQLite
        cursor.execute("SELECT id, status FROM expenses WHERE call_id = ?", (call_id,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return {"status": "exists", "id": row[0], "type": "expense", "entry_status": row[1]}
            
        cursor.execute("SELECT id, status FROM confirmation_requests WHERE json_extract(raw_value, '$.call_id') = ?", (call_id,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return {"status": "exists", "id": row[0], "type": "confirmation_request", "entry_status": row[1]}

        new_id = f"exp-{datetime.datetime.now().timestamp()}"
        if entry_status in ["confirmed", "needs_review"]:
            cursor.execute(
                "INSERT INTO expenses (id, family_id, member_id, amount, currency, category, date, description, status, importance_level, call_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (new_id, family_id, member_id, amount, "INR", category, date_val, desc_val, entry_status, importance_level, call_id, now)
            )
            if entry_status == "confirmed" and importance_level == "high":
                cursor.execute(
                    "INSERT INTO memory_events (id, family_id, event_type, content, created_at) VALUES (?, ?, ?, ?, ?)",
                    (f"mem-{datetime.datetime.now().timestamp()}", family_id, "expense_logged", f"High importance expense logged: ₹{amount} spent on {category}.", now)
                )
            conn.commit()
            conn.close()
            return {"status": "success", "id": new_id, "type": "expense", "entry_status": entry_status}
        else:
            raw_val = {
                "call_id": call_id,
                "member_id": member_id,
                "amount": amount,
                "category": category,
                "date": date_val,
                "description": desc_val
            }
            new_req_id = f"req-{datetime.datetime.now().timestamp()}"
            cursor.execute(
                "INSERT INTO confirmation_requests (id, family_id, item_type, raw_value, status, confidence_score, uncertainty_reason, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (new_req_id, family_id, "expense", json.dumps(raw_val), "pending", confidence, "Low transcription confidence.", now)
            )
            conn.commit()
            conn.close()
            return {"status": "success", "id": new_req_id, "type": "confirmation_request", "entry_status": "pending"}

def record_debt_transaction(
    family_id: str,
    lender_name: str,
    borrower_name: str,
    amount: float,
    due_date: str,
    note: str,
    call_id: str,
    confidence: float
) -> Dict[str, Any]:
    """
    Logs a debt/loan transaction following three-tier confidence logic.
    """
    now = datetime.datetime.now().isoformat()
    due_val = due_date or (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
    note_val = note or f"Lent ₹{amount} from {lender_name} to {borrower_name}"
    
    # Determine status
    if confidence >= 0.90:
        entry_status = "active"
    elif confidence >= 0.70:
        entry_status = "needs_review"
    else:
        entry_status = "pending_confirmation"

    if not is_local_mode:
        # Idempotency
        existing_debt = supabase_client.table("debts").select("id, status").eq("call_id", call_id).execute()
        if existing_debt.data:
            return {"status": "exists", "id": existing_debt.data[0]["id"], "type": "debt", "entry_status": existing_debt.data[0]["status"]}

        if entry_status in ["active", "needs_review"]:
            data = {
                "family_id": family_id,
                "lender_name": lender_name,
                "borrower_name": borrower_name,
                "amount": amount,
                "due_date": due_val,
                "note": note_val,
                "status": "active" if entry_status == "active" else "needs_review",
                "importance_level": "high",
                "call_id": call_id
            }
            res = supabase_client.table("debts").insert(data).execute()
            
            if entry_status == "active":
                supabase_client.table("memory_events").insert({
                    "family_id": family_id,
                    "event_type": "debt_created",
                    "content": f"New debt of ₹{amount} added (Owed to {lender_name} by {borrower_name})."
                }).execute()
                
            return {"status": "success", "id": res.data[0]["id"], "type": "debt", "entry_status": entry_status}
        else:
            raw_val = {
                "call_id": call_id,
                "lender_name": lender_name,
                "borrower_name": borrower_name,
                "amount": amount,
                "due_date": due_val,
                "note": note_val
            }
            data = {
                "family_id": family_id,
                "item_type": "debt",
                "raw_value": raw_val,
                "status": "pending",
                "confidence_score": confidence,
                "uncertainty_reason": "Low transcription confidence."
            }
            res = supabase_client.table("confirmation_requests").insert(data).execute()
            return {"status": "success", "id": res.data[0]["id"], "type": "confirmation_request", "entry_status": "pending"}
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, status FROM debts WHERE call_id = ?", (call_id,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return {"status": "exists", "id": row[0], "type": "debt", "entry_status": row[1]}

        new_id = f"debt-{datetime.datetime.now().timestamp()}"
        if entry_status in ["active", "needs_review"]:
            cursor.execute(
                "INSERT INTO debts (id, family_id, lender_name, borrower_name, amount, due_date, note, status, importance_level, call_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (new_id, family_id, lender_name, borrower_name, amount, due_val, note_val, "active" if entry_status == "active" else "needs_review", "high", call_id, now)
            )
            if entry_status == "active":
                cursor.execute(
                    "INSERT INTO memory_events (id, family_id, event_type, content, created_at) VALUES (?, ?, ?, ?, ?)",
                    (f"mem-{datetime.datetime.now().timestamp()}", family_id, "debt_created", f"New debt of ₹{amount} added (Owed to {lender_name} by {borrower_name}).", now)
                )
            conn.commit()
            conn.close()
            return {"status": "success", "id": new_id, "type": "debt", "entry_status": entry_status}
        else:
            raw_val = {
                "call_id": call_id,
                "lender_name": lender_name,
                "borrower_name": borrower_name,
                "amount": amount,
                "due_date": due_val,
                "note": note_val
            }
            new_req_id = f"req-{datetime.datetime.now().timestamp()}"
            cursor.execute(
                "INSERT INTO confirmation_requests (id, family_id, item_type, raw_value, status, confidence_score, uncertainty_reason, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (new_req_id, family_id, "debt", json.dumps(raw_val), "pending", confidence, "Low transcription confidence.", now)
            )
            conn.commit()
            conn.close()
            return {"status": "success", "id": new_req_id, "type": "confirmation_request", "entry_status": "pending"}

def save_call_record(
    call_id: str,
    family_id: Optional[str],
    member_id: Optional[str],
    transcript: List[Dict[str, Any]],
    extracted_json: Dict[str, Any],
    confidence: float,
    status: str,
    recording_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Saves/updates a call record for timeline tracking.
    """
    now = datetime.datetime.now().isoformat()
    if not is_local_mode:
        data = {
            "call_id": call_id,
            "family_id": family_id,
            "member_id": member_id,
            "transcript": transcript,
            "extracted_json": extracted_json,
            "confidence": confidence,
            "status": status,
            "recording_url": recording_url
        }
        response = supabase_client.table("call_logs").upsert(data, on_conflict="call_id").execute()
        return response.data[0]
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        
        # Check if exists
        cursor.execute("SELECT id FROM call_logs WHERE call_id = ?", (call_id,))
        row = cursor.fetchone()
        
        t_str = json.dumps(transcript)
        e_str = json.dumps(extracted_json)
        
        if row:
            cursor.execute(
                "UPDATE call_logs SET family_id = ?, member_id = ?, transcript = ?, extracted_json = ?, confidence = ?, status = ?, recording_url = ? WHERE call_id = ?",
                (family_id, member_id, t_str, e_str, confidence, status, recording_url, call_id)
            )
            new_id = row[0]
        else:
            new_id = f"call-{datetime.datetime.now().timestamp()}"
            cursor.execute(
                "INSERT INTO call_logs (id, call_id, family_id, member_id, transcript, extracted_json, confidence, status, recording_url, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (new_id, call_id, family_id, member_id, t_str, e_str, confidence, status, recording_url, now)
            )
        conn.commit()
        conn.close()
        return {"id": new_id, "call_id": call_id}

# --- Dashboard Trust Layer Query Implementations ---

def get_pending_confirmations_repo(family_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetches Low Confidence requests and Medium Confidence expenses.
    """
    if not is_local_mode:
        low_res = supabase_client.table("confirmation_requests").select("*").eq("family_id", family_id).eq("status", "pending").order("created_at", desc=True).execute()
        med_res = supabase_client.table("expenses").select("*, members(name)").eq("family_id", family_id).eq("status", "needs_review").order("created_at", desc=True).execute()
        return {
            "low_confidence_requests": low_res.data,
            "medium_confidence_expenses": med_res.data
        }
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Low confidence
        cursor.execute("SELECT * FROM confirmation_requests WHERE family_id = ? AND status = 'pending' ORDER BY created_at DESC", (family_id,))
        low_list = []
        for r in cursor.fetchall():
            row_dict = dict(r)
            row_dict["raw_value"] = json.loads(row_dict["raw_value"])
            low_list.append(row_dict)
            
        # Medium confidence
        cursor.execute(
            "SELECT e.*, m.name as member_name FROM expenses e JOIN members m ON e.member_id = m.id WHERE e.family_id = ? AND e.status = 'needs_review' ORDER BY e.created_at DESC",
            (family_id,)
        )
        med_list = []
        for r in cursor.fetchall():
            row_dict = dict(r)
            row_dict["members"] = {"name": row_dict.pop("member_name")}
            med_list.append(row_dict)
            
        conn.close()
        return {
            "low_confidence_requests": low_list,
            "medium_confidence_expenses": med_list
        }

def verify_medium_confidence_expense_repo(expense_id: str) -> Dict[str, Any]:
    """
    Updates the status of a medium-confidence expense from 'needs_review' to 'confirmed'.
    Also updates goal progress if this expense represents a goal contribution.
    """
    if not is_local_mode:
        orig = supabase_client.table("expenses").select("*").eq("id", expense_id).execute()
        if not orig.data:
            return {}
        expense_data = orig.data[0]
        res = supabase_client.table("expenses").update({"status": "confirmed"}).eq("id", expense_id).execute()
        
        # If it was a goal update, apply the goal amount addition
        if expense_data.get("category") == "savings" and expense_data.get("description", "").startswith("Goal Update:"):
            goal_name = expense_data["description"].split("Goal Update:")[1].strip()
            goals_res = supabase_client.table("goals").select("*").eq("family_id", expense_data["family_id"]).execute()
            for goal in goals_res.data:
                if goal["goal_name"].lower().strip() == goal_name.lower().strip() or goal_name.lower().strip() in goal["goal_name"].lower():
                    new_amt = float(goal["current_amount"]) + float(expense_data["amount"])
                    supabase_client.table("goals").update({"current_amount": new_amt}).eq("id", goal["id"]).execute()
                    
                    # Log memory event
                    supabase_client.table("memory_events").insert({
                        "family_id": expense_data["family_id"],
                        "event_type": "goal_updated",
                        "content": f"Confirmed savings of ₹{expense_data['amount']} contributed to {goal['goal_name']}."
                    }).execute()
                    break
        return res.data[0] if res.data else {}
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return {}
        
        expense_data = dict(row)
        cursor.execute("UPDATE expenses SET status = 'confirmed' WHERE id = ?", (expense_id,))
        
        # If it was a goal update, apply the goal amount addition
        if expense_data.get("category") == "savings" and expense_data.get("description", "").startswith("Goal Update:"):
            goal_name = expense_data["description"].split("Goal Update:")[1].strip()
            cursor.execute("SELECT id, goal_name, current_amount FROM goals WHERE family_id = ?", (expense_data["family_id"],))
            goals = cursor.fetchall()
            for g in goals:
                if g["goal_name"].lower().strip() == goal_name.lower().strip() or goal_name.lower().strip() in g["goal_name"].lower():
                    new_amt = float(g["current_amount"]) + float(expense_data["amount"])
                    cursor.execute("UPDATE goals SET current_amount = ? WHERE id = ?", (new_amt, g["id"]))
                    
                    # Log memory event
                    now = datetime.datetime.now().isoformat()
                    cursor.execute(
                        "INSERT INTO memory_events (id, family_id, event_type, content, created_at) VALUES (?, ?, ?, ?, ?)",
                        (f"mem-{datetime.datetime.now().timestamp()}", expense_data["family_id"], "goal_updated", f"Confirmed savings of ₹{expense_data['amount']} contributed to {g['goal_name']}.", now)
                    )
                    break
        conn.commit()
        cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        updated_row = cursor.fetchone()
        conn.close()
        return dict(updated_row) if updated_row else {}

def verify_low_confidence_request_repo(request_id: str, verified_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Accepts verified data for a low-confidence request, commits it to memory,
    and updates the request status to 'confirmed'. Also updates goal progress if applicable.
    """
    now = datetime.datetime.now().isoformat()
    if not is_local_mode:
        req_res = supabase_client.table("confirmation_requests").select("*").eq("id", request_id).execute()
        if not req_res.data:
            raise Exception("Request not found")
        req = req_res.data[0]
        raw_val = req["raw_value"]
        item_type = req["item_type"]
        family_id = req["family_id"]

        if item_type == "expense":
            desc_val = verified_data.get("description") or f"Contributed to {raw_val.get('goal_name', 'savings')}"
            data = {
                "family_id": family_id,
                "member_id": raw_val["member_id"],
                "amount": verified_data["amount"],
                "category": verified_data["category"],
                "date": verified_data.get("date") or datetime.date.today().isoformat(),
                "description": desc_val,
                "status": "confirmed",
                "importance_level": "high" if verified_data["amount"] >= 5000 else "medium" if verified_data["amount"] >= 1000 else "low",
                "call_id": raw_val["call_id"]
            }
            supabase_client.table("expenses").insert(data).execute()
            
            # Check if this request represents a goal contribution
            if raw_val.get("goal_name"):
                goals_res = supabase_client.table("goals").select("*").eq("family_id", family_id).execute()
                for goal in goals_res.data:
                    if goal["goal_name"].lower().strip() == raw_val["goal_name"].lower().strip() or raw_val["goal_name"].lower().strip() in goal["goal_name"].lower():
                        new_amt = float(goal["current_amount"]) + float(verified_data["amount"])
                        supabase_client.table("goals").update({"current_amount": new_amt}).eq("id", goal["id"]).execute()
                        
                        supabase_client.table("memory_events").insert({
                            "family_id": family_id,
                            "event_type": "goal_updated",
                            "content": f"Confirmed savings of ₹{verified_data['amount']} contributed to {goal['goal_name']}."
                        }).execute()
                        break
        elif item_type == "debt":
            data = {
                "family_id": family_id,
                "lender_name": verified_data.get("lender_name") or raw_val.get("lender_name"),
                "borrower_name": verified_data.get("borrower_name") or raw_val.get("borrower_name"),
                "amount": verified_data["amount"],
                "due_date": verified_data.get("due_date") or raw_val.get("due_date"),
                "note": verified_data.get("note") or raw_val.get("note") or "Voice log debt (Verified)",
                "status": "active",
                "importance_level": "high",
                "call_id": raw_val["call_id"]
            }
            supabase_client.table("debts").insert(data).execute()

        supabase_client.table("confirmation_requests").update({"status": "confirmed"}).eq("id", request_id).execute()
        return {"status": "success"}
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM confirmation_requests WHERE id = ?", (request_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise Exception("Request not found")
            
        req = dict(row)
        raw_val = json.loads(req["raw_value"])
        item_type = req["item_type"]
        family_id = req["family_id"]

        if item_type == "expense":
            new_id = f"exp-{datetime.datetime.now().timestamp()}"
            importance = "high" if verified_data["amount"] >= 5000 else "medium" if verified_data["amount"] >= 1000 else "low"
            desc_val = verified_data.get("description") or f"Contributed to {raw_val.get('goal_name', 'savings')}"
            cursor.execute(
                "INSERT INTO expenses (id, family_id, member_id, amount, currency, category, date, description, status, importance_level, call_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (new_id, family_id, raw_val["member_id"], verified_data["amount"], "INR", verified_data["category"], verified_data.get("date") or datetime.date.today().isoformat(), desc_val, "confirmed", importance, raw_val["call_id"], now)
            )
            
            # Check if this request represents a goal contribution in SQLite
            if raw_val.get("goal_name"):
                cursor.execute("SELECT id, goal_name, current_amount FROM goals WHERE family_id = ?", (family_id,))
                goals = cursor.fetchall()
                for g in goals:
                    if g["goal_name"].lower().strip() == raw_val["goal_name"].lower().strip() or raw_val["goal_name"].lower().strip() in g["goal_name"].lower():
                        new_amt = float(g["current_amount"]) + float(verified_data["amount"])
                        cursor.execute("UPDATE goals SET current_amount = ? WHERE id = ?", (new_amt, g["id"]))
                        
                        cursor.execute(
                            "INSERT INTO memory_events (id, family_id, event_type, content, created_at) VALUES (?, ?, ?, ?, ?)",
                            (f"mem-{datetime.datetime.now().timestamp()}", family_id, "goal_updated", f"Confirmed savings of ₹{verified_data['amount']} contributed to {g['goal_name']}.", now)
                        )
                        break
        elif item_type == "debt":
            new_id = f"debt-{datetime.datetime.now().timestamp()}"
            cursor.execute(
                "INSERT INTO debts (id, family_id, lender_name, borrower_name, amount, due_date, note, status, importance_level, call_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (new_id, family_id, verified_data.get("lender_name") or raw_val.get("lender_name"), verified_data.get("borrower_name") or raw_val.get("borrower_name"), verified_data["amount"], verified_data.get("due_date") or raw_val.get("due_date"), verified_data.get("note") or raw_val.get("note") or "Voice log debt (Verified)", "active", "high", raw_val["call_id"], now)
            )
            
        cursor.execute("UPDATE confirmation_requests SET status = 'confirmed' WHERE id = ?", (request_id,))
        conn.commit()
        conn.close()
        return {"status": "success"}

def discard_confirmation_request_repo(request_id: str) -> Dict[str, Any]:
    """
    Marks a confirmation request as rejected/discarded.
    """
    if not is_local_mode:
        res = supabase_client.table("confirmation_requests").update({"status": "rejected"}).eq("id", request_id).execute()
        return res.data[0] if res.data else {}
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE confirmation_requests SET status = 'rejected' WHERE id = ?", (request_id,))
        conn.commit()
        conn.close()
        return {"status": "success"}

def get_voice_timeline_repo(family_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves call logs timeline for a family.
    """
    if not is_local_mode:
        res = supabase_client.table("call_logs").select("*, members(name)").eq("family_id", family_id).order("created_at", desc=True).execute()
        return res.data
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT c.*, m.name as member_name FROM call_logs c LEFT JOIN members m ON c.member_id = m.id WHERE c.family_id = ? ORDER BY c.created_at DESC",
            (family_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        timeline_list = []
        for r in rows:
            row_dict = dict(r)
            row_dict["transcript"] = json.loads(row_dict["transcript"])
            row_dict["extracted_json"] = json.loads(row_dict["extracted_json"])
            row_dict["members"] = {"name": row_dict.pop("member_name")} if row_dict["member_name"] else None
            timeline_list.append(row_dict)
        return timeline_list

def get_family_financial_summary_repo(family_id: str) -> Dict[str, Any]:
    """
    Computes budgets limits vs spent, outstanding debts, active goals.
    """
    today = datetime.date.today()
    start_of_month = today.replace(day=1).isoformat()
    
    if not is_local_mode:
        budgets_res = supabase_client.table("budgets").select("category, monthly_limit").eq("family_id", family_id).execute()
        expenses_res = supabase_client.table("expenses").select("amount, category").eq("family_id", family_id).eq("status", "confirmed").gte("date", start_of_month).execute()
        debts_res = supabase_client.table("debts").select("*").eq("family_id", family_id).eq("status", "active").execute()
        goals_res = supabase_client.table("goals").select("*").eq("family_id", family_id).execute()
        expenses_all_res = supabase_client.table("expenses").select("*, members(name)").eq("family_id", family_id).eq("status", "confirmed").execute()
        
        spent_by_category = {}
        for exp in expenses_res.data:
            cat = exp["category"]
            spent_by_category[cat] = spent_by_category.get(cat, 0) + float(exp["amount"])
            
        budgets_summary = []
        for b in budgets_res.data:
            cat = b["category"]
            limit = float(b["monthly_limit"])
            spent = spent_by_category.get(cat, 0.0)
            budgets_summary.append({
                "category": cat,
                "limit": limit,
                "spent": spent,
                "remaining": limit - spent
            })
            
        total_assets = sum(float(g["current_amount"]) for g in goals_res.data)
        total_debts = sum(float(d["amount"]) for d in debts_res.data)
        
        return {
            "budgets": budgets_summary,
            "active_debts": debts_res.data,
            "goals": goals_res.data,
            "expenses": expenses_all_res.data,
            "total_assets": total_assets,
            "total_debts": total_debts,
            "savings_rate": 0
        }
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Budgets
        cursor.execute("SELECT category, monthly_limit FROM budgets WHERE family_id = ?", (family_id,))
        budgets_rows = [dict(r) for r in cursor.fetchall()]
        
        # Expenses spent
        cursor.execute("SELECT amount, category FROM expenses WHERE family_id = ? AND status = 'confirmed' AND date >= ?", (family_id, start_of_month))
        spent_by_category = {}
        for r in cursor.fetchall():
            cat = r[1]
            spent_by_category[cat] = spent_by_category.get(cat, 0.0) + float(r[0])
            
        budgets_summary = []
        for b in budgets_rows:
            cat = b["category"]
            limit = float(b["monthly_limit"])
            spent = spent_by_category.get(cat, 0.0)
            budgets_summary.append({
                "category": cat,
                "limit": limit,
                "spent": spent,
                "remaining": limit - spent
            })
            
        # Debts
        cursor.execute("SELECT * FROM debts WHERE family_id = ? AND status = 'active'", (family_id,))
        debts = [dict(r) for r in cursor.fetchall()]
        
        # Goals
        cursor.execute("SELECT * FROM goals WHERE family_id = ?", (family_id,))
        goals = [dict(r) for r in cursor.fetchall()]
        
        # Confirmed expenses
        cursor.execute(
            "SELECT e.*, m.name as member_name FROM expenses e JOIN members m ON e.member_id = m.id WHERE e.family_id = ? AND e.status = 'confirmed'",
            (family_id,)
        )
        expenses_all = []
        for r in cursor.fetchall():
            row_dict = dict(r)
            row_dict["members"] = {"name": row_dict.pop("member_name")}
            expenses_all.append(row_dict)
            
        conn.close()
        
        total_assets = sum(float(g["current_amount"]) for g in goals)
        total_debts = sum(float(d["amount"]) for d in debts)
        
        return {
            "budgets": budgets_summary,
            "active_debts": debts,
            "goals": goals,
            "expenses": expenses_all,
            "total_assets": total_assets,
            "total_debts": total_debts,
            "savings_rate": 0
        }

def delete_expense_repo(expense_id: str) -> bool:
    """Deletes an expense record by ID."""
    if not is_local_mode:
        res = supabase_client.table("expenses").delete().eq("id", expense_id).execute()
        return len(res.data) > 0 if res.data else False
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        rows_deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_deleted > 0

def delete_debt_repo(debt_id: str) -> bool:
    """Deletes a debt record by ID."""
    if not is_local_mode:
        res = supabase_client.table("debts").delete().eq("id", debt_id).execute()
        return len(res.data) > 0 if res.data else False
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM debts WHERE id = ?", (debt_id,))
        rows_deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_deleted > 0

def update_expense_repo(expense_id: str, amount: float, category: str, description: str) -> bool:
    """Updates an expense record by ID."""
    if not is_local_mode:
        res = supabase_client.table("expenses").update({
            "amount": amount,
            "category": category,
            "description": description
        }).eq("id", expense_id).execute()
        return len(res.data) > 0 if res.data else False
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE expenses SET amount = ?, category = ?, description = ? WHERE id = ?",
            (amount, category, description, expense_id)
        )
        rows_updated = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_updated > 0

def update_debt_repo(debt_id: str, amount: float, lender_name: str, borrower_name: str, note: str) -> bool:
    """Updates a debt record by ID."""
    if not is_local_mode:
        res = supabase_client.table("debts").update({
            "amount": amount,
            "lender_name": lender_name,
            "borrower_name": borrower_name,
            "note": note
        }).eq("id", debt_id).execute()
        return len(res.data) > 0 if res.data else False
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE debts SET amount = ?, lender_name = ?, borrower_name = ?, note = ? WHERE id = ?",
            (amount, lender_name, borrower_name, note, debt_id)
        )
        rows_updated = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_updated > 0

# --- Sprint Voice Expansion Repository Helper Functions ---

def get_spending_summary_repo(
    family_id: str,
    category: Optional[str] = None,
    member_name: Optional[str] = None,
    timeframe: str = "month",
    largest_only: bool = False
) -> Dict[str, Any]:
    """
    Retrieves and aggregates confirmed expenses for a family.
    Filters by timeframe ('week' or 'month'), category, or family member.
    """
    today = datetime.date.today()
    
    if timeframe == "week":
        start_date = (today - datetime.timedelta(days=7)).isoformat()
        timeframe_desc = "this week"
    else:
        start_date = today.replace(day=1).isoformat()
        timeframe_desc = "this month"

    # Fetch confirmed expenses
    if not is_local_mode:
        query = supabase_client.table("expenses").select("*, members(name)").eq("family_id", family_id).eq("status", "confirmed").gte("date", start_date)
        res = query.execute()
        expenses = []
        for e in res.data:
            item = dict(e)
            item["member_name"] = e.get("members", {}).get("name")
            expenses.append(item)
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT e.*, m.name as member_name FROM expenses e JOIN members m ON e.member_id = m.id WHERE e.family_id = ? AND e.status = 'confirmed' AND e.date >= ?",
            (family_id, start_date)
        )
        expenses = [dict(r) for r in cursor.fetchall()]
        conn.close()

    # Filter by category if provided
    if category and category.strip().lower() != "all" and category.strip().lower() != "misc":
        expenses = [e for e in expenses if e["category"].lower().strip() == category.lower().strip()]

    # Filter by member name if provided
    # Resolve role-based aliases (e.g. "dad", "father", "mom") to actual member names via DB
    if member_name:
        std_name = member_name.strip().lower()
        role_aliases = {
            "dad": "father", "papa": "father", "appa": "father", "nanna": "father",
            "mom": "mother", "amma": "mother", "mummy": "mother",
            "bro": "brother", "anna": "brother",
            "sis": "sister", "akka": "sister",
            "son": "son", "daughter": "daughter"
        }
        if std_name in role_aliases:
            target_role = role_aliases[std_name]
            # Look up actual member name from the family's members table
            role_members = []
            if not is_local_mode:
                role_res = supabase_client.table("members").select("name").eq("family_id", family_id).ilike("role", f"%{target_role}%").execute()
                role_members = [r["name"].lower() for r in role_res.data]
            else:
                conn2 = sqlite3.connect(SQLITE_PATH)
                conn2.row_factory = sqlite3.Row
                c2 = conn2.cursor()
                c2.execute("SELECT name FROM members WHERE family_id = ? AND LOWER(role) LIKE ?", (family_id, f"%{target_role}%"))
                role_members = [r["name"].lower() for r in c2.fetchall()]
                conn2.close()
            if role_members:
                expenses = [e for e in expenses if e["member_name"].lower().strip() in role_members]
            else:
                expenses = []
        else:
            expenses = [e for e in expenses if e["member_name"].lower().strip() == std_name]

    if not expenses:
        filter_desc = ""
        if member_name:
            filter_desc += f" by {member_name}"
        if category:
            filter_desc += f" on {category}"
        
        voice_response = f"I couldn't find any confirmed expenses {timeframe_desc}{filter_desc}."
        return {
            "total_amount": 0.0,
            "expenses": [],
            "voice_response": voice_response
        }

    if largest_only:
        # Sort and pick largest
        largest_expense = max(expenses, key=lambda x: float(x["amount"]))
        voice_response = (
            f"The largest expense {timeframe_desc} was ₹{largest_expense['amount']:.0f} spent "
            f"on {largest_expense['category']} by {largest_expense['member_name']} for {largest_expense['description']}."
        )
        return {
            "total_amount": float(largest_expense["amount"]),
            "expenses": [largest_expense],
            "voice_response": voice_response
        }

    total_amount = sum(float(e["amount"]) for e in expenses)
    
    # Generate conversational wording
    filter_parts = []
    if member_name:
        filter_parts.append(f"by {member_name}")
    if category:
        filter_parts.append(f"on {category}")
        
    filter_desc = " ".join(filter_parts)
    if filter_desc:
        voice_response = f"The total spending {timeframe_desc} {filter_desc} is ₹{total_amount:.0f} across {len(expenses)} transactions."
    else:
        voice_response = f"The family spent a total of ₹{total_amount:.0f} {timeframe_desc} across {len(expenses)} transactions."

    return {
        "total_amount": total_amount,
        "expenses": expenses,
        "voice_response": voice_response
    }


def get_goal_status_repo(family_id: str, goal_name: str) -> Dict[str, Any]:
    """
    Retrieves progress on a savings goal and estimates required contributions.
    """
    if not is_local_mode:
        res = supabase_client.table("goals").select("*").eq("family_id", family_id).execute()
        goals = res.data
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM goals WHERE family_id = ?", (family_id,))
        goals = [dict(r) for r in cursor.fetchall()]
        conn.close()

    # Find the target goal
    matched_goal = None
    target_name_lower = goal_name.strip().lower()
    
    # Try exact or substring match
    for g in goals:
        g_name_lower = g["goal_name"].strip().lower()
        if target_name_lower in g_name_lower or g_name_lower in target_name_lower:
            matched_goal = g
            break
            
    if not matched_goal:
        active_names = ", ".join([g["goal_name"] for g in goals]) if goals else "none"
        return {
            "status": "error",
            "voice_response": f"I couldn't find a savings goal matching '{goal_name}'. Your family's active goals are: {active_names}."
        }

    current = float(matched_goal["current_amount"])
    target = float(matched_goal["target_amount"])
    remaining = target - current

    if remaining <= 0:
        return {
            "status": "success",
            "goal": matched_goal,
            "voice_response": f"Congratulations! You have fully achieved your savings goal for {matched_goal['goal_name']}, saving ₹{current:.0f} out of ₹{target:.0f}!"
        }

    # Calculate estimated monthly contributions needed
    today = datetime.date.today()
    try:
        t_date = datetime.datetime.strptime(matched_goal["target_date"], "%Y-%m-%d").date()
        months_left = (t_date.year - today.year) * 12 + (t_date.month - today.month)
        if months_left <= 0:
            months_left = 1
    except Exception:
        months_left = 1

    monthly_est = remaining / months_left
    
    try:
        date_obj = datetime.datetime.strptime(matched_goal["target_date"], "%Y-%m-%d")
        date_speech = date_obj.strftime("%B %Y")
    except Exception:
        date_speech = matched_goal["target_date"]

    voice_response = (
        f"For your {matched_goal['goal_name']}, you have saved ₹{current:.0f} out of your ₹{target:.0f} goal. "
        f"You need ₹{remaining:.0f} more. To hit your target by {date_speech}, "
        f"you should contribute about ₹{monthly_est:.0f} per month."
    )

    return {
        "status": "success",
        "goal": matched_goal,
        "remaining_amount": remaining,
        "months_left": months_left,
        "monthly_contribution_needed": monthly_est,
        "voice_response": voice_response
    }


def update_goal_progress_repo(
    family_id: str,
    goal_name: str,
    amount: float,
    member_id: str,
    call_id: str,
    confidence: float
) -> Dict[str, Any]:
    """
    Contributes funds to a savings goal via the Trust Layer workflows.
    """
    now = datetime.datetime.now().isoformat()
    
    if not is_local_mode:
        res = supabase_client.table("goals").select("*").eq("family_id", family_id).execute()
        goals = res.data
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM goals WHERE family_id = ?", (family_id,))
        goals = [dict(r) for r in cursor.fetchall()]
        conn.close()

    matched_goal = None
    target_name_lower = goal_name.strip().lower()
    for g in goals:
        g_name_lower = g["goal_name"].strip().lower()
        if target_name_lower in g_name_lower or g_name_lower in target_name_lower:
            matched_goal = g
            break
            
    if not matched_goal:
        active_names = ", ".join([g["goal_name"] for g in goals]) if goals else "none"
        raise Exception(f"Goal matching '{goal_name}' not found. Active goals: {active_names}")

    goal_id = matched_goal["id"]
    goal_title = matched_goal["goal_name"]

    if not is_local_mode:
        m_res = supabase_client.table("members").select("name").eq("id", member_id).execute()
        member_name = m_res.data[0]["name"] if m_res.data else "Family Member"
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM members WHERE id = ?", (member_id,))
        m_row = cursor.fetchone()
        member_name = m_row[0] if m_row else "Family Member"
        conn.close()

    if confidence >= 0.90:
        entry_status = "confirmed"
    elif confidence >= 0.70:
        entry_status = "needs_review"
    else:
        entry_status = "pending_confirmation"

    if not is_local_mode:
        existing_exp = supabase_client.table("expenses").select("id, status").eq("call_id", call_id).execute()
        if existing_exp.data:
            return {"status": "exists", "id": existing_exp.data[0]["id"], "type": "goal_update", "entry_status": existing_exp.data[0]["status"]}
            
        existing_req = supabase_client.table("confirmation_requests").select("id, status").eq("raw_value->>call_id", call_id).execute()
        if existing_req.data:
            return {"status": "exists", "id": existing_req.data[0]["id"], "type": "confirmation_request", "entry_status": existing_req.data[0]["status"]}
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, status FROM expenses WHERE call_id = ?", (call_id,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return {"status": "exists", "id": row[0], "type": "goal_update", "entry_status": row[1]}
        cursor.execute("SELECT id, status FROM confirmation_requests WHERE json_extract(raw_value, '$.call_id') = ?", (call_id,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return {"status": "exists", "id": row[0], "type": "confirmation_request", "entry_status": row[1]}
        conn.close()

    new_id = f"exp-{datetime.datetime.now().timestamp()}"
    desc_confirmed = f"Added ₹{amount:.0f} to {goal_title} via phone"
    desc_review = f"Goal Update: {goal_title}"

    if entry_status == "confirmed":
        new_amt = float(matched_goal["current_amount"]) + amount
        if not is_local_mode:
            supabase_client.table("goals").update({"current_amount": new_amt}).eq("id", goal_id).execute()
            data = {
                "id": new_id,
                "family_id": family_id,
                "member_id": member_id,
                "amount": amount,
                "category": "savings",
                "date": datetime.date.today().isoformat(),
                "description": desc_confirmed,
                "status": "confirmed",
                "importance_level": "medium",
                "call_id": call_id
            }
            supabase_client.table("expenses").insert(data).execute()
            supabase_client.table("memory_events").insert({
                "family_id": family_id,
                "event_type": "goal_updated",
                "content": f"{member_name} added ₹{amount:.0f} to {goal_title} via phone."
            }).execute()
        else:
            conn = sqlite3.connect(SQLITE_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE goals SET current_amount = ? WHERE id = ?", (new_amt, goal_id))
            cursor.execute(
                "INSERT INTO expenses (id, family_id, member_id, amount, currency, category, date, description, status, importance_level, call_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (new_id, family_id, member_id, amount, "INR", "savings", datetime.date.today().isoformat(), desc_confirmed, "confirmed", "medium", call_id, now)
            )
            cursor.execute(
                "INSERT INTO memory_events (id, family_id, event_type, content, created_at) VALUES (?, ?, ?, ?, ?)",
                (f"mem-{datetime.datetime.now().timestamp()}", family_id, "goal_updated", f"{member_name} added ₹{amount:.0f} to {goal_title} via phone.", now)
            )
            conn.commit()
            conn.close()
            
        voice_response = f"Done! I've added ₹{amount:.0f} to your {goal_title} goal."
        return {"status": "success", "id": new_id, "entry_status": "confirmed", "voice_response": voice_response}
        
    elif entry_status == "needs_review":
        if not is_local_mode:
            data = {
                "id": new_id,
                "family_id": family_id,
                "member_id": member_id,
                "amount": amount,
                "category": "savings",
                "date": datetime.date.today().isoformat(),
                "description": desc_review,
                "status": "needs_review",
                "importance_level": "medium",
                "call_id": call_id
            }
            supabase_client.table("expenses").insert(data).execute()
        else:
            conn = sqlite3.connect(SQLITE_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO expenses (id, family_id, member_id, amount, currency, category, date, description, status, importance_level, call_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (new_id, family_id, member_id, amount, "INR", "savings", datetime.date.today().isoformat(), desc_review, "needs_review", "medium", call_id, now)
            )
            conn.commit()
            conn.close()
            
        voice_response = f"I noted that you want to add ₹{amount:.0f} to {goal_title}. I've marked this for your review on the dashboard."
        return {"status": "success", "id": new_id, "entry_status": "needs_review", "voice_response": voice_response}
        
    else:
        raw_val = {
            "call_id": call_id,
            "member_id": member_id,
            "amount": amount,
            "category": "savings",
            "goal_name": goal_title,
            "description": f"Contribute ₹{amount:.0f} to {goal_title}"
        }
        new_req_id = f"req-{datetime.datetime.now().timestamp()}"
        if not is_local_mode:
            data = {
                "id": new_req_id,
                "family_id": family_id,
                "item_type": "expense",
                "raw_value": raw_val,
                "status": "pending",
                "confidence_score": confidence,
                "uncertainty_reason": "Low transcription confidence for goal update."
            }
            supabase_client.table("confirmation_requests").insert(data).execute()
        else:
            conn = sqlite3.connect(SQLITE_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO confirmation_requests (id, family_id, item_type, raw_value, status, confidence_score, uncertainty_reason, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (new_req_id, family_id, "expense", json.dumps(raw_val), "pending", confidence, "Low transcription confidence for goal update.", now)
            )
            conn.commit()
            conn.close()
            
        voice_response = f"I heard a request to add ₹{amount:.0f} to {goal_title}, but I'm not fully certain. I saved it to your dashboard validations list."
        return {"status": "success", "id": new_req_id, "entry_status": "pending", "voice_response": voice_response}


def get_debt_guidance_repo(family_id: str) -> Dict[str, Any]:
    """
    Prioritizes active family debts and returns conversational household reduction guidance.
    """
    if not is_local_mode:
        res = supabase_client.table("debts").select("*").eq("family_id", family_id).eq("status", "active").execute()
        active_debts = res.data
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM debts WHERE family_id = ? AND status = 'active'", (family_id,))
        active_debts = [dict(r) for r in cursor.fetchall()]
        conn.close()

    if not active_debts:
        return {
            "status": "success",
            "debts": [],
            "voice_response": "Great news! Your family doesn't have any active outstanding debts logged in our financial memory."
        }

    def sort_key(d):
        date_str = d.get("due_date")
        if not date_str:
            date_val = datetime.date(9999, 12, 31)
        else:
            try:
                date_val = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            except Exception:
                date_val = datetime.date(9999, 12, 31)
        return (date_val, -float(d["amount"]))

    sorted_debts = sorted(active_debts, key=sort_key)
    
    priority_parts = []
    for idx, d in enumerate(sorted_debts[:3], 1):
        due_info = f"due by {d['due_date']}" if d.get('due_date') else "no due date set"
        note_info = f" ({d['note']})" if d.get('note') else ""
        priority_parts.append(f"{idx}. Pay back ₹{d['amount']:.0f} to {d['lender_name']} {due_info}{note_info}")
        
    priority_list_str = "; ".join(priority_parts)
    
    voice_response = (
        f"You have {len(active_debts)} outstanding debts. Based on due dates, "
        f"here is your recommended repayment priority: {priority_list_str}. "
        f"We prioritize by nearest due date to avoid late penalties. Clear urgent debts first, then tackle larger balances. "
        f"Please avoid taking new loans and consider redirecting any surplus monthly budget towards these repayments."
    )

    return {
        "status": "success",
        "debts": sorted_debts,
        "voice_response": voice_response
    }


def get_members_repo(family_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves all members of a family.
    """
    if not is_local_mode:
        response = supabase_client.table("members").select("id, name, role, phone_number, preferred_language, family_id").eq("family_id", family_id).execute()
        return response.data
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, role, phone_number, preferred_language, family_id FROM members WHERE family_id = ?", (family_id,))
        rows = cursor.fetchall()
        res = [dict(row) for row in rows]
        conn.close()
        return res


def update_member_repo(member_id: str, name: str, role: str, phone_number: str, preferred_language: str) -> Optional[Dict[str, Any]]:
    """
    Updates family member configuration in the database.
    """
    if not is_local_mode:
        data = {
            "name": name,
            "role": role,
            "phone_number": phone_number,
            "preferred_language": preferred_language
        }
        response = supabase_client.table("members").update(data).eq("id", member_id).execute()
        return response.data[0] if response.data else None
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE members SET name = ?, role = ?, phone_number = ?, preferred_language = ? WHERE id = ?",
            (name, role, phone_number, preferred_language, member_id)
        )
        conn.commit()
        
        # Fetch updated member
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, role, phone_number, preferred_language, family_id FROM members WHERE id = ?", (member_id,))
        row = cursor.fetchone()
        res = dict(row) if row else None
        conn.close()
        return res


def get_family_name_repo(family_id: str) -> Optional[str]:
    """
    Retrieves the family name by family_id.
    """
    if not is_local_mode:
        response = supabase_client.table("families").select("name").eq("id", family_id).execute()
        if response.data:
            return response.data[0]["name"]
        return None
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM families WHERE id = ?", (family_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row["name"]
        return None


def update_family_name_repo(family_id: str, new_name: str) -> bool:
    """
    Updates the family name.
    """
    if not is_local_mode:
        response = supabase_client.table("families").update({"name": new_name}).eq("id", family_id).execute()
        return len(response.data) > 0 if response.data else False
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE families SET name = ? WHERE id = ?", (new_name, family_id))
        conn.commit()
        rows_updated = cursor.rowcount
        conn.close()
        return rows_updated > 0


def update_budget_limit_repo(budget_id: str, monthly_limit: float) -> bool:
    """
    Updates the monthly limit for a budget.
    """
    if not is_local_mode:
        response = supabase_client.table("budgets").update({"monthly_limit": monthly_limit}).eq("id", budget_id).execute()
        return len(response.data) > 0 if response.data else False
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE budgets SET monthly_limit = ? WHERE id = ?", (monthly_limit, budget_id))
        conn.commit()
        rows_updated = cursor.rowcount
        conn.close()
        return rows_updated > 0


def create_budget_repo(family_id: str, category: str, monthly_limit: float) -> Dict[str, Any]:
    """
    Creates a new budget entry for the family.
    """
    budget_id = f"b-{category}"
    created_at = datetime.datetime.now().isoformat()
    budget_data = {
        "id": budget_id,
        "family_id": family_id,
        "category": category,
        "monthly_limit": monthly_limit,
        "created_at": created_at
    }
    if not is_local_mode:
        response = supabase_client.table("budgets").insert(budget_data).execute()
        return response.data[0] if response.data else budget_data
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO budgets (id, family_id, category, monthly_limit, created_at) VALUES (?, ?, ?, ?, ?)",
            (budget_id, family_id, category, monthly_limit, created_at)
        )
        conn.commit()
        conn.close()
        return budget_data


def delete_budget_repo(budget_id: str) -> bool:
    """
    Deletes a budget entry by ID.
    """
    if not is_local_mode:
        response = supabase_client.table("budgets").delete().eq("id", budget_id).execute()
        return len(response.data) > 0 if response.data else False
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
        conn.commit()
        rows_deleted = cursor.rowcount
        conn.close()
        return rows_deleted > 0


def update_goal_repo(goal_id: str, goal_name: str, target_amount: float, target_date: str) -> bool:
    """
    Updates an existing goal's name, target amount, and target date.
    """
    if not is_local_mode:
        response = supabase_client.table("goals").update({
            "goal_name": goal_name,
            "target_amount": target_amount,
            "target_date": target_date
        }).eq("id", goal_id).execute()
        return len(response.data) > 0 if response.data else False
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE goals SET goal_name = ?, target_amount = ?, target_date = ? WHERE id = ?",
            (goal_name, target_amount, target_date, goal_id)
        )
        conn.commit()
        rows_updated = cursor.rowcount
        conn.close()
        return rows_updated > 0


def create_goal_repo(family_id: str, goal_name: str, target_amount: float, target_date: str, importance_level: str = "medium") -> Dict[str, Any]:
    """
    Creates a new goal for the family.
    """
    goal_id = f"g-{uuid.uuid4().hex[:8]}"
    created_at = datetime.datetime.now().isoformat()
    goal_data = {
        "id": goal_id,
        "family_id": family_id,
        "goal_name": goal_name,
        "target_amount": target_amount,
        "current_amount": 0.0,
        "target_date": target_date,
        "importance_level": importance_level,
        "created_at": created_at
    }
    if not is_local_mode:
        response = supabase_client.table("goals").insert(goal_data).execute()
        return response.data[0] if response.data else goal_data
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO goals (id, family_id, goal_name, target_amount, current_amount, target_date, importance_level, created_at) VALUES (?, ?, ?, ?, 0.0, ?, ?, ?)",
            (goal_id, family_id, goal_name, target_amount, target_date, importance_level, created_at)
        )
        conn.commit()
        conn.close()
        return goal_data


def delete_goal_repo(goal_id: str) -> bool:
    """
    Deletes a goal by ID.
    """
    if not is_local_mode:
        response = supabase_client.table("goals").delete().eq("id", goal_id).execute()
        return len(response.data) > 0 if response.data else False
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        conn.commit()
        rows_deleted = cursor.rowcount
        conn.close()
        return rows_deleted > 0
