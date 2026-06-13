import logging
from fastapi import APIRouter, HTTPException, Body
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from backend.database import (
    resolve_member_by_phone,
    save_call_record
)

logger = logging.getLogger("uvicorn")
router = APIRouter(prefix="/api/webhook", tags=["Bolna Webhooks"])

class WebhookPayload(BaseModel):
    call_id: Optional[str] = None
    id: Optional[str] = None
    phone_number: Optional[str] = None
    user_number: Optional[str] = None
    transcript: Any = None
    recording_url: Optional[str] = None
    status: str = "completed"
    extractions: Optional[Dict[str, Any]] = None
    extracted_data: Optional[Dict[str, Any]] = None
    member_name: Optional[str] = None
    confidence: Optional[float] = None
    telephony_data: Optional[Dict[str, Any]] = None

@router.post("/bolna")
async def receive_bolna_webhook(payload: WebhookPayload):
    """
    Post-call webhook from Bolna Voice AI.
    Read-only: saves call log for observability, voice history, and audit.
    Does NOT write expenses, debts, or goals — those are handled by real-time custom tools during the call.
    """
    call_id = payload.call_id or payload.id or "unknown_call_id"
    phone_number = payload.phone_number or payload.user_number
    if not phone_number and payload.telephony_data:
        phone_number = payload.telephony_data.get("to_number") or payload.telephony_data.get("from_number") or payload.telephony_data.get("user_number")

    logger.info(f"Received Bolna webhook for call: {call_id}, phone: {phone_number}")

    # 1. Resolve Identity (for audit/logging only)
    members = resolve_member_by_phone(phone_number) if phone_number else []
    member_id = None
    family_id = None

    if members:
        active_member = members[0]
        family_id = active_member["family_id"]
        member_id = active_member["id"]
        if payload.member_name:
            matched = [m for m in members if m["name"].lower() == payload.member_name.lower()]
            if matched:
                active_member = matched[0]
                member_id = active_member["id"]

    # 2. Save call log (transcript, recording, metadata)
    transcript_to_save = []
    if isinstance(payload.transcript, str):
        for line in payload.transcript.split("\n"):
            line = line.strip()
            if not line:
                continue
            if ":" in line:
                parts = line.split(":", 1)
                role = parts[0].strip().lower()
                content = parts[1].strip()
                transcript_to_save.append({"role": role, "content": content})
            else:
                transcript_to_save.append({"role": "unknown", "content": line})
    elif isinstance(payload.transcript, list):
        transcript_to_save = payload.transcript

    recording_url = payload.recording_url
    if not recording_url and payload.telephony_data:
        recording_url = payload.telephony_data.get("recording_url")

    try:
        save_call_record(
            call_id=call_id,
            family_id=family_id,
            member_id=member_id,
            transcript=transcript_to_save,
            extracted_json=payload.extracted_data or payload.extractions or {},
            confidence=payload.confidence or 1.0,
            status=payload.status,
            recording_url=recording_url
        )
    except Exception as e:
        logger.error(f"Error saving webhook call log: {e}")

    return {
        "status": "success",
        "message": "Call log saved (read-only webhook)",
        "call_id": call_id,
        "resolved_family_id": family_id,
        "resolved_member_id": member_id
    }
