"""AI-powered event form assistant using Gemini REST API."""

import json
import logging
from datetime import date

import requests as _requests
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import TokenData, verify_token
from ..config import settings
from ..database import get_db, get_or_create_user
from ..exceptions import BadRequest
from ..schemas.common import ok

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Event Assistant"])

_REQUIRED = {"title", "date", "venue", "category"}
_CATEGORIES = ["music", "corporate", "wedding", "sports", "art", "food"]

_SYSTEM_PROMPT = """You are an AI event assistant for Eventoo that helps users create events through conversation.

Your task:
1. Extract event details from what the user says
2. Ask about missing required fields in a friendly, brief way
3. Once all required fields are filled, summarize and confirm

Required fields:
- title: Event name
- date: Date in YYYY-MM-DD format (today is {today})
- venue: Venue / location name
- category: Exactly one of: music, corporate, wedding, sports, art, food

Optional fields you can also extract:
- time: HH:MM (24-hour)
- city: City name
- attendee_count: integer
- capacity: integer
- description: string
- client_name: string
- client_phone: string
- client_email: string
- budget: integer (₹ thousands)
- notes: string

Context — fields already collected: {current_fields}

Respond ONLY with a valid JSON object, no markdown, no extra text:
{{
  "message": "Your friendly reply to the user",
  "extractedFields": {{...all fields extracted so far, merged with what user just said...}},
  "missingRequired": [...which of title/date/venue/category are still missing...],
  "readyToSubmit": false
}}

Rules:
- extractedFields must include all previously known fields PLUS anything new from the latest message
- Set readyToSubmit: true only when all 4 required fields are present
- When readyToSubmit is true, your message should summarize the event and ask "Shall I create this event?"
- Keep replies short (1-2 sentences max)
- Convert natural dates like "next Friday", "April 15", "25th March 2026" to YYYY-MM-DD
- category must be one of the 6 exact values above
"""


class ChatMessage(BaseModel):
    role: str   # "user" or "model"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    currentFields: dict = {}


class ChatResponse(BaseModel):
    message: str
    extractedFields: dict
    missingRequired: list[str]
    readyToSubmit: bool


@router.post("/event-assistant/chat")
def event_assistant_chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    get_or_create_user(db, token.uid, token.phone)

    if not settings.gemini_api_key:
        raise BadRequest("AI assistant is not configured (missing GEMINI_API_KEY)")

    system_instruction = _SYSTEM_PROMPT.format(
        today=date.today().isoformat(),
        current_fields=json.dumps(body.currentFields) if body.currentFields else "none yet",
    )

    # Build contents list — Gemini requires it starts with a user turn
    prior = [m for m in body.messages[:-1] if m.role in ("user", "model")]
    while prior and prior[0].role == "model":
        prior.pop(0)
    contents = [{"role": m.role, "parts": [{"text": m.content}]} for m in prior]
    last_message = body.messages[-1].content if body.messages else "Hello"
    contents.append({"role": "user", "parts": [{"text": last_message}]})

    payload = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": contents,
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.4,
        },
    }

    url = (
        "https://generativelanguage.googleapis.com/v1beta"
        f"/models/gemini-flash-latest:generateContent?key={settings.gemini_api_key}"
    )

    try:
        resp = _requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
    except Exception as exc:
        logger.exception("Gemini REST call failed: %s", exc)
        raise

    raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]

    try:
        data = json.loads(raw_text)
    except (json.JSONDecodeError, ValueError):
        logger.warning("Gemini returned non-JSON: %s", raw_text)
        data = {
            "message": raw_text[:300],
            "extractedFields": body.currentFields,
            "missingRequired": list(_REQUIRED - set(body.currentFields.keys())),
            "readyToSubmit": False,
        }

    # Enforce field types and validate category
    extracted = data.get("extractedFields", body.currentFields)
    if "category" in extracted and extracted["category"] not in _CATEGORIES:
        extracted.pop("category", None)

    missing = [f for f in _REQUIRED if not extracted.get(f)]
    ready = len(missing) == 0

    return ok({
        "message": data.get("message", "How can I help?"),
        "extractedFields": extracted,
        "missingRequired": missing,
        "readyToSubmit": ready,
    })
