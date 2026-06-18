"""Tests for the emergency detector and safety module."""

from __future__ import annotations

import pytest

from app.safety.emergency_detector import (
    SAFE_RESPONSE_CRISIS,
    SAFE_RESPONSE_MEDICAL,
    check,
)


# ---------------------------------------------------------------------------
# Medical emergency detection
# ---------------------------------------------------------------------------


class TestMedicalEmergencyDetection:
    """Verify that medical emergency phrases trigger the detector."""

    @pytest.mark.asyncio
    async def test_chest_pain_triggers(self) -> None:
        """Chest pain should trigger a medical emergency response."""
        triggered, response = await check("I'm having severe chest pain")
        assert triggered is True
        assert response == SAFE_RESPONSE_MEDICAL

    @pytest.mark.asyncio
    async def test_cant_breathe_triggers(self) -> None:
        """Breathing difficulty should trigger a medical emergency response."""
        triggered, response = await check("I can't breathe properly")
        assert triggered is True
        assert response == SAFE_RESPONSE_MEDICAL

    @pytest.mark.asyncio
    async def test_heart_attack_triggers(self) -> None:
        """Heart attack mention should trigger."""
        triggered, response = await check("I think I'm having a heart attack")
        assert triggered is True
        assert response == SAFE_RESPONSE_MEDICAL

    @pytest.mark.asyncio
    async def test_overdose_triggers(self) -> None:
        """Overdose mention should trigger."""
        triggered, response = await check("my friend just took an overdose")
        assert triggered is True
        assert response == SAFE_RESPONSE_MEDICAL

    @pytest.mark.asyncio
    async def test_seizure_triggers(self) -> None:
        """Seizure mention should trigger."""
        triggered, response = await check("someone is having a seizure")
        assert triggered is True
        assert response == SAFE_RESPONSE_MEDICAL

    @pytest.mark.asyncio
    async def test_severe_bleeding_triggers(self) -> None:
        """Severe bleeding should trigger."""
        triggered, response = await check("there is severe bleeding from the wound")
        assert triggered is True
        assert response == SAFE_RESPONSE_MEDICAL

    @pytest.mark.asyncio
    async def test_case_insensitive(self) -> None:
        """Detection should be case-insensitive."""
        triggered, response = await check("I have CHEST PAIN")
        assert triggered is True
        assert response == SAFE_RESPONSE_MEDICAL


# ---------------------------------------------------------------------------
# Mental health crisis detection
# ---------------------------------------------------------------------------


class TestMentalHealthCrisisDetection:
    """Verify that mental health crisis phrases trigger the detector."""

    @pytest.mark.asyncio
    async def test_suicidal_triggers(self) -> None:
        """Suicidal ideation should trigger a crisis response."""
        triggered, response = await check("I'm feeling suicidal")
        assert triggered is True
        assert response == SAFE_RESPONSE_CRISIS

    @pytest.mark.asyncio
    async def test_want_to_die_triggers(self) -> None:
        """Want to die should trigger."""
        triggered, response = await check("I just want to die")
        assert triggered is True
        assert response == SAFE_RESPONSE_CRISIS

    @pytest.mark.asyncio
    async def test_kill_myself_triggers(self) -> None:
        """Kill myself should trigger."""
        triggered, response = await check("I want to kill myself")
        assert triggered is True
        assert response == SAFE_RESPONSE_CRISIS

    @pytest.mark.asyncio
    async def test_self_harm_triggers(self) -> None:
        """Self-harm should trigger."""
        triggered, response = await check("I've been thinking about self-harm")
        assert triggered is True
        assert response == SAFE_RESPONSE_CRISIS

    @pytest.mark.asyncio
    async def test_no_reason_to_live_triggers(self) -> None:
        """No reason to live should trigger."""
        triggered, response = await check("there's no reason to live anymore")
        assert triggered is True
        assert response == SAFE_RESPONSE_CRISIS

    @pytest.mark.asyncio
    async def test_crisis_takes_priority_over_medical(self) -> None:
        """When both crisis and medical phrases are present, crisis wins."""
        triggered, response = await check(
            "I want to kill myself and I have chest pain"
        )
        assert triggered is True
        assert response == SAFE_RESPONSE_CRISIS


# ---------------------------------------------------------------------------
# Normal queries should NOT trigger
# ---------------------------------------------------------------------------


class TestNormalQueriesDoNotTrigger:
    """Verify that benign queries pass through without triggering."""

    @pytest.mark.asyncio
    async def test_normal_health_question(self) -> None:
        """A normal health question should not trigger."""
        triggered, response = await check("What are the symptoms of a cold?")
        assert triggered is False
        assert response is None

    @pytest.mark.asyncio
    async def test_normal_legal_question(self) -> None:
        """A normal legal question should not trigger."""
        triggered, response = await check(
            "What is the statute of limitations for breach of contract?"
        )
        assert triggered is False
        assert response is None

    @pytest.mark.asyncio
    async def test_normal_code_question(self) -> None:
        """A coding question should not trigger."""
        triggered, response = await check("How do I sort a list in Python?")
        assert triggered is False
        assert response is None

    @pytest.mark.asyncio
    async def test_empty_message(self) -> None:
        """An empty message should not trigger."""
        triggered, response = await check("")
        assert triggered is False
        assert response is None


# ---------------------------------------------------------------------------
# Safe responses are fixed strings
# ---------------------------------------------------------------------------


class TestSafeResponsesAreFixed:
    """Verify that safe responses are predetermined, never model-generated."""

    def test_medical_response_is_string(self) -> None:
        """Medical safe response must be a non-empty string constant."""
        assert isinstance(SAFE_RESPONSE_MEDICAL, str)
        assert len(SAFE_RESPONSE_MEDICAL) > 0
        assert "911" in SAFE_RESPONSE_MEDICAL or "emergency" in SAFE_RESPONSE_MEDICAL.lower()

    def test_crisis_response_is_string(self) -> None:
        """Crisis safe response must be a non-empty string constant."""
        assert isinstance(SAFE_RESPONSE_CRISIS, str)
        assert len(SAFE_RESPONSE_CRISIS) > 0
        assert "988" in SAFE_RESPONSE_CRISIS or "crisis" in SAFE_RESPONSE_CRISIS.lower()

    def test_medical_response_contains_emergency_number(self) -> None:
        """Medical response should direct to emergency services."""
        assert "911" in SAFE_RESPONSE_MEDICAL

    def test_crisis_response_contains_hotline(self) -> None:
        """Crisis response should include the 988 Suicide & Crisis Lifeline."""
        assert "988" in SAFE_RESPONSE_CRISIS
