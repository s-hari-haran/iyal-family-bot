import os
import pytest
from unittest.mock import patch, MagicMock

# Set mock env vars before loading backend modules
os.environ["SUPABASE_URL"] = "https://mock.supabase.co"
os.environ["SUPABASE_SERVICE_KEY"] = "mock_service_key"
os.environ["BOLNA_API_KEY"] = "mock_bolna_key"

from fastapi.testclient import TestClient

# Mock the database before importing routes that initialize Supabase client
with patch('backend.database.supabase_client') as mock_db:
    from backend.main import app
    client = TestClient(app)

def test_health_check():
    """
    Test that the root health-check endpoint works.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"
    assert "Family Financial Memory" in response.json()["service"]

@patch('backend.routes.tools.resolve_member_by_phone')
@patch('backend.routes.tools.check_budget_limit')
@patch('backend.routes.tools.record_expense_transaction')
def test_record_expense_high_confidence(mock_record, mock_budget, mock_resolve):
    """
    Test logging an expense with high confidence.
    Should commit as 'confirmed'.
    """
    # Setup mocks
    mock_resolve.return_value = [{"id": "m1", "name": "Ramesh", "family_id": "f1", "preferred_language": "en"}]
    mock_budget.return_value = {"has_budget": True, "limit": 10000.0, "spent": 2000.0, "remaining": 8000.0, "warning": ""}
    mock_record.return_value = {"status": "success", "id": "exp-1", "type": "expense", "entry_status": "confirmed"}

    payload = {
        "phone_number": "+919876543210",
        "member_name": "Ramesh",
        "call_id": "call-12345",
        "amount": 500.0,
        "category": "groceries",
        "description": "Vegetables",
        "confidence": 0.95
    }

    response = client.post("/api/tools/record-expense", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["entry_status"] == "confirmed"
    assert "Logged ₹500.0 for groceries" in data["voice_response"]

@patch('backend.routes.tools.resolve_member_by_phone')
def test_identity_resolution_ambiguous(mock_resolve):
    """
    Test identity resolution when multiple members share a number.
    Should return an identity clarification response code.
    """
    # Setup mocks returning two members
    mock_resolve.return_value = [
        {"id": "m1", "name": "Ramesh", "family_id": "f1"},
        {"id": "m2", "name": "Sunita", "family_id": "f1"}
    ]

    payload = {
        "phone_number": "+919876543210",
        "member_name": None,  # No name specified yet
        "call_id": "call-12345",
        "amount": 500.0,
        "category": "groceries"
    }

    response = client.post("/api/tools/record-expense", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "identity_clarification_required"
    assert "Multiple members share this number: Ramesh, Sunita" in data["message"]

def test_financial_literacy_copilot():
    """
    Test that the copilot explains PPF and blocks stocks/crypto recommendations.
    """
    # Valid safe topic
    response = client.post("/api/tools/get-financial-literacy", json={"query": "Explain PPF"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "government-backed" in response.json()["voice_response"]

    # Prohibited speculative topic
    response = client.post("/api/tools/get-financial-literacy", json={"query": "which stock should I buy today?"})
    assert response.status_code == 200
    assert response.json()["status"] == "warning"
    assert "cannot give regulated stock recommendations" in response.json()["voice_response"]


@patch('backend.routes.trust.get_members_repo')
def test_get_members_endpoint(mock_get_members):
    """
    Test GET /api/trust/members/{family_id} route.
    """
    mock_get_members.return_value = [
        {"id": "m1", "name": "Ramesh", "role": "Father", "phone_number": "+919538133265", "preferred_language": "en"}
    ]
    response = client.get("/api/trust/members/f8e56bdf-99a3-4813-8b77-3e5f7b88939c")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Ramesh"


@patch('backend.routes.trust.update_member_repo')
def test_update_member_endpoint(mock_update_member):
    """
    Test PUT /api/trust/members/{member_id} route.
    """
    mock_update_member.return_value = {
        "id": "m1", "name": "Ramesh Updated", "role": "Father", "phone_number": "+919262171465", "preferred_language": "hi"
    }
    payload = {
        "name": "Ramesh Updated",
        "role": "Father",
        "phone_number": "+919262171465",
        "preferred_language": "hi"
    }
    response = client.put("/api/trust/members/m1", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["data"]["name"] == "Ramesh Updated"
    assert response.json()["data"]["preferred_language"] == "hi"

