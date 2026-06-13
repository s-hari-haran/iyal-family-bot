import os

# Set mock env vars
os.environ["SUPABASE_URL"] = "mock_url"
os.environ["SUPABASE_SERVICE_KEY"] = "mock_service_key"
os.environ["BOLNA_API_KEY"] = "mock_bolna_key"

# Delete any existing test database to start fresh before importing backend modules
db_path = os.path.join(os.path.dirname(__file__), "test_family_memory.db")
if os.path.exists(db_path):
    try:
        os.remove(db_path)
    except Exception as e:
        print(f"Error removing db file: {e}")

import backend.database as db_module
db_module.SQLITE_PATH = db_path

from backend.main import app
from backend.database import init_sqlite_db
init_sqlite_db(seed_data=True)

from fastapi.testclient import TestClient
client = TestClient(app)

def test_scenario_a_groceries_high_confidence():
    """
    Scenario A: Mother logs groceries (High confidence).
    Expected: Expense is stored as confirmed, budget is updated.
    """
    payload = {
        "phone_number": "+919876543210",
        "member_name": "Sunita",
        "call_id": "call-scen-a",
        "amount": 1200.0,
        "category": "groceries",
        "description": "Weekly grocery list from local market",
        "confidence": 0.95
    }
    response = client.post("/api/tools/record-expense", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["entry_status"] == "confirmed"
    assert "Logged ₹1200.0 for groceries" in data["voice_response"]

    # Verify dashboard summary reflects updated groceries spent (spent is now 1200)
    summary_res = client.get("/api/trust/summary/f8e56bdf-99a3-4813-8b77-3e5f7b88939c")
    assert summary_res.status_code == 200
    summary_data = summary_res.json()
    
    groceries_budget = next(b for b in summary_data["budgets"] if b["category"] == "groceries")
    assert groceries_budget["spent"] == 1200.0
    assert groceries_budget["remaining"] == 8800.0

def test_scenario_b_debt_logging():
    """
    Scenario B: Father Ramesh logs a debt update.
    Expected: Debt is logged as active.
    """
    payload = {
        "phone_number": "+919876543210",
        "member_name": "Ramesh",
        "call_id": "call-scen-b",
        "lender_name": "Sharma Family",
        "borrower_name": "Uncle Vinay",
        "amount": 2000.0,
        "due_date": "2026-07-15",
        "note": "Lent money for travel expenses",
        "confidence": 0.98
    }
    response = client.post("/api/tools/record-debt", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["entry_status"] == "active"
    assert "Recorded that Uncle Vinay owes" in data["voice_response"]

def test_scenario_c_caller_ambiguity_and_resolution():
    """
    Scenario C: Caller ambiguity on shared phone.
    Expected:
    1. Phone call without member name returns ambiguity code and member names list.
    2. Resubmitting with member name 'Ramesh' resolves the member correctly.
    """
    # 1. Ambiguous caller ID (Shared phone, no name specified)
    payload = {
        "phone_number": "+919876543210",
        "member_name": None,
        "call_id": "call-scen-c-1",
        "amount": 100.0,
        "category": "misc"
    }
    response = client.post("/api/tools/record-expense", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "identity_clarification_required"
    assert "Multiple members share this number: Ramesh, Sunita" in data["message"]

    # 2. Resubmit with speaker identity resolved
    payload["member_name"] = "Ramesh"
    payload["call_id"] = "call-scen-c-2"
    response2 = client.post("/api/tools/record-expense", json=payload)
    assert response2.status_code == 200
    assert response2.json()["status"] == "success"

def test_scenario_d_low_confidence_confirmation_request():
    """
    Scenario D: Low confidence extraction (< 70%).
    Expected:
    1. Stored in confirmation_requests with pending status.
    2. Appears on dashboard pending validations endpoint.
    3. Verifying it via Trust Layer API commits it to permanent expenses.
    """
    payload = {
        "phone_number": "+919876543210",
        "member_name": "Sunita",
        "call_id": "call-scen-d",
        "amount": 600.0,
        "category": "utilities",
        "description": "saji billing or something",
        "confidence": 0.55
    }
    response = client.post("/api/tools/record-expense", json=payload)
    assert response.status_code == 200
    assert response.json()["entry_status"] == "pending"

    # Fetch pending confirmations from dashboard Trust Layer
    pending_res = client.get("/api/trust/pending-confirmations/f8e56bdf-99a3-4813-8b77-3e5f7b88939c")
    assert pending_res.status_code == 200
    pending_data = pending_res.json()
    
    # Verify it exists in low confidence requests
    req = next(r for r in pending_data["low_confidence_requests"] if r["raw_value"]["call_id"] == "call-scen-d")
    assert req["status"] == "pending"
    assert req["confidence_score"] == 0.55

    # Verify/confirm it via Trust Layer
    verify_payload = {
        "amount": 600.0,
        "category": "utilities",
        "date": "2026-06-11",
        "description": "Electricity Bill (Clarified)"
      }
    verify_res = client.post(f"/api/trust/verify-request/{req['id']}", json=verify_payload)
    assert verify_res.status_code == 200

    # Ensure it no longer appears in pending confirmations
    pending_res2 = client.get("/api/trust/pending-confirmations/f8e56bdf-99a3-4813-8b77-3e5f7b88939c")
    assert not any(r["id"] == req["id"] for r in pending_res2.json()["low_confidence_requests"])

def test_scenario_e_context_retrieval():
    """
    Scenario E: Family memory retrieval questions.
    Expected: Asking for category budget status correctly aggregates and reflects the current state.
    """
    payload = {
        "phone_number": "+919876543210",
        "category": "groceries"
    }
    response = client.post("/api/tools/budget-status", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    # Sunita spent 1200 earlier, so total spent is now 1200 out of 10000 limit, leaving 8800
    assert data["spent"] == 1200.0
    assert data["remaining"] == 8800.0
    assert "spent ₹1200 out of ₹10000" in data["voice_response"]

def test_webhook_reliability_and_idempotency():
    """
    Test 4: Webhook reliability and idempotency.
    Expected:
    1. Sending a webhook inserts a call log and expense.
    2. Sending the identical webhook with same call_id does not duplicate records.
    """
    webhook_payload = {
        "call_id": "webhook-call-idempotent-1",
        "phone_number": "+919876543210",
        "member_name": "Ramesh",
        "transcript": [
            {"role": "user", "content": "paid fuel 1000"},
            {"role": "assistant", "content": "Logged 1000 for fuel"}
        ],
        "recording_url": "https://voice.bolna.ai/call-rec-123.mp3",
        "status": "completed",
        "confidence": 0.95,
        "extractions": {
            "expense": {
                "amount": 1000.0,
                "category": "fuel",
                "date": "2026-06-11",
                "description": "paid fuel 1000"
            }
        }
    }

    # First delivery
    res1 = client.post("/api/webhook/bolna", json=webhook_payload)
    assert res1.status_code == 200

    # Verify timeline call log exists
    timeline1 = client.get("/api/trust/timeline/f8e56bdf-99a3-4813-8b77-3e5f7b88939c")
    calls1 = [c for c in timeline1.json() if c["call_id"] == "webhook-call-idempotent-1"]
    assert len(calls1) == 1

    # Second duplicate delivery
    res2 = client.post("/api/webhook/bolna", json=webhook_payload)
    assert res2.status_code == 200

    # Verify timeline call log is STILL exactly 1, not duplicated
    timeline2 = client.get("/api/trust/timeline/f8e56bdf-99a3-4813-8b77-3e5f7b88939c")
    calls2 = [c for c in timeline2.json() if c["call_id"] == "webhook-call-idempotent-1"]
    assert len(calls2) == 1

def test_spending_summary_endpoint():
    """
    Test 5: Spending Summaries voice endpoint.
    Verifies that spending queries aggregate properly and support category / member / largest filters.
    """
    # 1. Total monthly spending query
    payload = {
        "phone_number": "+919538133265",
        "timeframe": "month"
    }
    response = client.post("/api/tools/spending-summary", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    # From previous tests, we have groceries (1200), ambiguous resolved (100)
    assert data["total_amount"] >= 1300.0
    assert "total of" in data["voice_response"]

    # 2. Specific category query (groceries)
    payload_cat = {
        "phone_number": "+919538133265",
        "category": "groceries",
        "timeframe": "month"
    }
    response_cat = client.post("/api/tools/spending-summary", json=payload_cat)
    assert response_cat.status_code == 200
    data_cat = response_cat.json()
    assert data_cat["status"] == "success"
    assert data_cat["total_amount"] == 1200.0
    assert "spending" in data_cat["voice_response"]
    assert "groceries" in data_cat["voice_response"]

    # 3. Largest expense query
    payload_largest = {
        "phone_number": "+919538133265",
        "largest_only": True,
        "timeframe": "month"
    }
    response_largest = client.post("/api/tools/spending-summary", json=payload_largest)
    assert response_largest.status_code == 200
    data_largest = response_largest.json()
    assert data_largest["status"] == "success"
    assert "largest expense" in data_largest["voice_response"]

def test_family_financial_summary_endpoint():
    """
    Test 6: Family Financial Summary voice endpoint.
    Verifies the holistic advisor response containing budgets, goals, and debts.
    """
    payload = {
        "phone_number": "+919538133265"
    }
    response = client.post("/api/tools/financial-summary", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "financial summary" in data["voice_response"]
    assert data["total_spent"] >= 1300.0
    # Seed debt (8000) + Scenario B debt (2000) = 10000
    assert data["total_debts"] == 10000.0

def test_goal_status_endpoint():
    """
    Test 7: Goal Progress Retrieval voice endpoint.
    Verifies remaining amount, target date matching, and monthly savings requirements.
    """
    payload = {
        "phone_number": "+919538133265",
        "goal_name": "emergency"
    }
    response = client.post("/api/tools/goal-status", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["goal"]["goal_name"] == "Emergency Fund"
    # Target 100000, Seed current 25000, remaining 75000
    assert data["remaining_amount"] == 75000.0
    assert "Emergency Fund" in data["voice_response"]
    assert "month" in data["voice_response"]

def test_goal_update_trust_tiers():
    """
    Test 8: Goal Contributions via three-tier trust logic.
    Verifies high confidence auto-confirm, medium confidence reviews, and low confidence pending states.
    """
    # 1. High confidence contribution (>= 90%)
    payload_high = {
        "phone_number": "+919449694564",
        "member_name": "Ramesh",
        "call_id": "goal-call-high-1",
        "goal_name": "Emergency Fund",
        "amount": 2000.0,
        "confidence": 0.95
    }
    res_high = client.post("/api/tools/goal-update", json=payload_high)
    assert res_high.status_code == 200
    data_high = res_high.json()
    assert data_high["status"] == "success"
    assert data_high["entry_status"] == "confirmed"
    assert "added ₹2000" in data_high["voice_response"]

    # Verify goal current_amount updated in DB (from 25,000 to 27,000)
    status_res = client.post("/api/tools/goal-status", json={"phone_number": "+919449694564", "goal_name": "emergency"})
    assert status_res.json()["goal"]["current_amount"] == 27000.0

    # 2. Medium confidence contribution (70% - 90%)
    payload_med = {
        "phone_number": "+919449694564",
        "member_name": "Ramesh",
        "call_id": "goal-call-med-1",
        "goal_name": "Emergency Fund",
        "amount": 3000.0,
        "confidence": 0.82
    }
    res_med = client.post("/api/tools/goal-update", json=payload_med)
    assert res_med.status_code == 200
    data_med = res_med.json()
    assert data_med["status"] == "success"
    assert data_med["entry_status"] == "needs_review"
    assert "marked this for your review" in data_med["voice_response"]

    # Verify goal current_amount did NOT update yet (remains 27,000)
    status_res = client.post("/api/tools/goal-status", json={"phone_number": "+919449694564", "goal_name": "emergency"})
    assert status_res.json()["goal"]["current_amount"] == 27000.0

    # Retrieve pending review expense from Trust Layer
    pending_res = client.get("/api/trust/pending-confirmations/f8e56bdf-99a3-4813-8b77-3e5f7b88939c")
    med_list = pending_res.json()["medium_confidence_expenses"]
    med_exp = next(e for e in med_list if e["call_id"] == "goal-call-med-1")
    assert med_exp["category"] == "savings"
    assert med_exp["description"] == "Goal Update: Emergency Fund"

    # Confirm medium confidence expense via Trust Layer
    confirm_res = client.post(f"/api/trust/verify-expense/{med_exp['id']}")
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "success"

    # Verify goal current_amount is now updated (becomes 30,000)
    status_res = client.post("/api/tools/goal-status", json={"phone_number": "+919449694564", "goal_name": "emergency"})
    assert status_res.json()["goal"]["current_amount"] == 30000.0

    # 3. Low confidence contribution (< 70%)
    payload_low = {
        "phone_number": "+919449694564",
        "member_name": "Ramesh",
        "call_id": "goal-call-low-1",
        "goal_name": "Emergency Fund",
        "amount": 5000.0,
        "confidence": 0.55
    }
    res_low = client.post("/api/tools/goal-update", json=payload_low)
    assert res_low.status_code == 200
    data_low = res_low.json()
    assert data_low["entry_status"] == "pending"
    assert "saved it to your dashboard validations list" in data_low["voice_response"]

    # Verify goal current_amount did NOT update yet (remains 30,000)
    status_res = client.post("/api/tools/goal-status", json={"phone_number": "+919449694564", "goal_name": "emergency"})
    assert status_res.json()["goal"]["current_amount"] == 30000.0

    # Fetch confirmation requests
    pending_res = client.get("/api/trust/pending-confirmations/f8e56bdf-99a3-4813-8b77-3e5f7b88939c")
    low_list = pending_res.json()["low_confidence_requests"]
    low_req = next(r for r in low_list if r["raw_value"]["call_id"] == "goal-call-low-1")
    assert low_req["item_type"] == "expense"
    assert low_req["raw_value"]["goal_name"] == "Emergency Fund"

    # Confirm low confidence request
    verify_payload = {
        "amount": 5000.0,
        "category": "savings",
        "date": "2026-06-12",
        "description": "Contributed to Emergency Fund (Low Confidence Verified)"
    }
    verify_res = client.post(f"/api/trust/verify-request/{low_req['id']}", json=verify_payload)
    assert verify_res.status_code == 200

    # Verify goal current_amount is now updated (becomes 35,000)
    status_res = client.post("/api/tools/goal-status", json={"phone_number": "+919449694564", "goal_name": "emergency"})
    assert status_res.json()["goal"]["current_amount"] == 35000.0

def test_debt_guidance_endpoint():
    """
    Test 9: Debt Reduction Guidance voice endpoint.
    Verifies that active debts are sorted by due date and simple reduction heuristics are returned.
    """
    payload = {
        "phone_number": "+919538133265"
    }
    response = client.post("/api/tools/debt-guidance", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["debts"]) == 2
    # Seed debt (Uncle Vinay, due 2026-06-25) should be prioritized before test_scenario_b debt (Uncle Vinay, due 2026-07-15)
    assert data["debts"][0]["lender_name"] == "Uncle Vinay"
    assert data["debts"][0]["due_date"] == "2026-06-25"
    assert data["debts"][1]["due_date"] == "2026-07-15"
    assert "nearest due date" in data["voice_response"]

