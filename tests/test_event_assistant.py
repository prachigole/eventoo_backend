"""
End-to-end test: AI event assistant chat → POST /events → GET /events.

The Gemini REST call is mocked so tests run offline and deterministically.
"""
import json
from unittest.mock import MagicMock, patch

import pytest

AUTH = {"Authorization": "Bearer manager-uid"}


def _gemini_response(payload: dict) -> MagicMock:
    """Return a mock requests.Response that looks like a Gemini success response."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": json.dumps(payload)}]
                }
            }
        ]
    }
    return mock_resp


# ── Helpers ───────────────────────────────────────────────────────────────────

def _chat(client, messages, current_fields=None):
    return client.post(
        "/api/v1/event-assistant/chat",
        json={"messages": messages, "currentFields": current_fields or {}},
        headers=AUTH,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestEventAssistantChat:
    def test_extracts_fields_and_asks_for_missing(self, client):
        """First user message → assistant extracts fields, asks for date."""
        gemini_payload = {
            "message": "That sounds lovely! When is Prachi's wedding?",
            "extractedFields": {
                "title": "Prachi's Wedding",
                "category": "wedding",
                "venue": "Marriott",
                "budget": 560,
            },
            "missingRequired": ["date"],
            "readyToSubmit": False,
        }
        with patch(
            "app.routers.event_assistant._requests.post",
            return_value=_gemini_response(gemini_payload),
        ):
            resp = _chat(client, [
                {"role": "user", "content": "Prachis wedding at marriot, budget 560000, category wedding"},
            ])

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["readyToSubmit"] is False
        assert data["missingRequired"] == ["date"]
        assert data["extractedFields"]["title"] == "Prachi's Wedding"
        assert data["extractedFields"]["venue"] == "Marriott"
        assert data["extractedFields"]["category"] == "wedding"

    def test_ready_to_submit_when_all_fields_present(self, client):
        """All 4 required fields provided → readyToSubmit=True."""
        gemini_payload = {
            "message": "Got everything! Shall I create this event?",
            "extractedFields": {
                "title": "Prachi's Wedding",
                "category": "wedding",
                "venue": "Marriott",
                "date": "2026-12-15",
            },
            "missingRequired": [],
            "readyToSubmit": True,
        }
        with patch(
            "app.routers.event_assistant._requests.post",
            return_value=_gemini_response(gemini_payload),
        ):
            resp = _chat(client, [
                {"role": "user", "content": "Prachis wedding at marriot on 15 december"},
            ])

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["readyToSubmit"] is True
        assert data["missingRequired"] == []

    def test_rejects_invalid_category(self, client):
        """Category not in the allowed set is stripped."""
        gemini_payload = {
            "message": "What category is this event?",
            "extractedFields": {
                "title": "My Event",
                "venue": "Some Place",
                "date": "2026-06-01",
                "category": "birthday",   # invalid — not in the 6 allowed values
            },
            "missingRequired": [],
            "readyToSubmit": True,
        }
        with patch(
            "app.routers.event_assistant._requests.post",
            return_value=_gemini_response(gemini_payload),
        ):
            resp = _chat(client, [{"role": "user", "content": "birthday party"}])

        assert resp.status_code == 200
        data = resp.json()["data"]
        # category stripped → still missing → not ready
        assert "category" in data["extractedFields"] is False or data["readyToSubmit"] is False

    def test_missing_api_key_returns_bad_request(self, client):
        """Missing GEMINI_API_KEY → 400 BAD_REQUEST."""
        with patch("app.routers.event_assistant.settings") as mock_settings:
            mock_settings.gemini_api_key = ""
            resp = _chat(client, [{"role": "user", "content": "hello"}])

        assert resp.status_code == 400


class TestFullFlow:
    def test_chat_then_create_then_list(self, client):
        """
        Full flow:
        1. Chat with assistant (Gemini mocked) → get extracted fields
        2. POST /events with those fields
        3. GET /events → event appears in the list
        """
        # Step 1: chat
        extracted = {
            "title": "Prachi's Wedding",
            "category": "wedding",
            "venue": "Marriott Mumbai",
            "date": "2026-12-15",
            "budget": 560,
        }
        gemini_payload = {
            "message": "All set! Shall I create the event?",
            "extractedFields": extracted,
            "missingRequired": [],
            "readyToSubmit": True,
        }
        with patch(
            "app.routers.event_assistant._requests.post",
            return_value=_gemini_response(gemini_payload),
        ):
            chat_resp = _chat(client, [
                {"role": "user", "content": "Prachis wedding at Marriott Mumbai on 15 dec, budget 560000"},
            ])

        assert chat_resp.status_code == 200
        fields = chat_resp.json()["data"]["extractedFields"]
        assert fields["title"] == "Prachi's Wedding"
        assert chat_resp.json()["data"]["readyToSubmit"] is True

        # Step 2: create event with extracted fields
        create_resp = client.post(
            "/api/v1/events",
            json={
                "title": fields["title"],
                "date": fields["date"],
                "venue": fields["venue"],
                "category": fields["category"],
            },
            headers=AUTH,
        )
        assert create_resp.status_code == 201
        created = create_resp.json()["data"]
        assert created["title"] == "Prachi's Wedding"
        assert created["venue"] == "Marriott Mumbai"

        # Step 3: GET /events → event appears
        list_resp = client.get("/api/v1/events", headers=AUTH)
        assert list_resp.status_code == 200
        items = list_resp.json()["data"]["items"]
        assert len(items) == 1
        assert items[0]["title"] == "Prachi's Wedding"
        assert items[0]["category"] == "wedding"
