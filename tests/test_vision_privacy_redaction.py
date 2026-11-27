"""Unit tests for Milestone 7.5: Vision Privacy, Redaction & Security Hardening."""

from __future__ import annotations

import pytest

from friday.macos.media_capture import (
    issue_single_use_capture_authorization,
    revoke_capture_authorization,
)
from friday.macos.redaction import (
    SensitiveDataRedactor,
    luhn_verify,
)
from friday.macos.registry import create_default_registry
from friday.macos.router import route_macos_intent
from friday.security.privacy_guard import (
    PrivacyViolationError,
    get_workspace_path,
    is_path_permanently_protected,
    validate_workspace_path,
)


def test_sensitive_data_redactor_api_keys():
    redactor = SensitiveDataRedactor()
    text = (
        "OpenAI key: sk-abcdef1234567890abcdef1234567890\n"
        "GitHub token: ghp_123456789012345678901234567890123456\n"
        "AWS Access: AKIAIOSFODNN7EXAMPLE\n"
        "Bearer auth: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-IDcSemACt8x4iTMC6Y9DbGQnMmtqFl_gAgJECIrQU"
    )
    res = redactor.redact_text(text)
    assert res.total_entities_redacted >= 4
    assert "sk-" not in res.redacted_text
    assert "ghp_" not in res.redacted_text
    assert "AKIA" not in res.redacted_text
    assert "[REDACTED_API_KEY]" in res.redacted_text


def test_sensitive_data_redactor_emails_and_phones():
    redactor = SensitiveDataRedactor(mask_style="token")
    text = "Reach out to alice@example.com or call +1-555-123-4567 for account details."
    res = redactor.redact_text(text)
    assert "alice@example.com" not in res.redacted_text
    assert "+1-555-123-4567" not in res.redacted_text
    assert "[REDACTED_EMAIL]" in res.redacted_text
    assert "[REDACTED_PHONE_NUMBER]" in res.redacted_text


def test_sensitive_data_redactor_financial_cards():
    redactor = SensitiveDataRedactor()
    valid_visa = "4532-1234-5678-9014"  # Valid Luhn number
    invalid_number = "1234-5678-9012-3456"  # Invalid Luhn

    assert luhn_verify(valid_visa) is True
    assert luhn_verify(invalid_number) is False

    text = f"Card: {valid_visa} and random {invalid_number}"
    res = redactor.redact_text(text)
    assert valid_visa not in res.redacted_text
    assert "[REDACTED_FINANCIAL_CARD]" in res.redacted_text


def test_sensitive_data_redactor_paths_and_chat_titles():
    redactor = SensitiveDataRedactor()
    text = "Logs at /Users/john/.ssh/id_rsa and active window Instagram - Direct Chat with Friend"
    res = redactor.redact_text(text)
    assert "/Users/john/.ssh/id_rsa" not in res.redacted_text
    assert "Instagram - Direct Chat" not in res.redacted_text
    assert "[REDACTED_SENSITIVE_PATH]" in res.redacted_text
    assert "[REDACTED_SENSITIVE_TITLE]" in res.redacted_text


def test_cryptographic_single_use_capture_token_atomic_lifecycle():
    revoke_capture_authorization()
    token = issue_single_use_capture_authorization(mode="window", target="Calculator", timeout_s=10.0)

    # 1. Nonce should be 32-character crypto hex
    assert len(token.nonce) == 32

    # 2. Valid check
    valid, msg = token.is_valid("window", target="Calculator")
    assert valid is True

    # 3. Mode mismatch fails
    valid_mismatch, _ = token.is_valid("fullscreen")
    assert valid_mismatch is False

    # 4. Target mismatch fails
    valid_target, _ = token.is_valid("window", target="Safari")
    assert valid_target is False

    # 5. Atomic consumption prevents replay
    token.consume()
    valid_replay, err = token.is_valid("window", target="Calculator")
    assert valid_replay is False
    assert "already been consumed" in err


def test_privacy_guard_multi_link_protection(tmp_path, monkeypatch):
    test_f = tmp_path / "test_file_normal.txt"
    test_f.write_text("Normal content")

    # Mock WORKSPACE_ROOT to tmp_path to test multi-link checks cleanly in isolated sandbox
    monkeypatch.setattr("friday.security.privacy_guard.WORKSPACE_ROOT", tmp_path)

    # Regular single-link workspace file passes
    res_p = validate_workspace_path(test_f)
    assert res_p.exists()

    # Protected folder path is denied unconditionally
    assert is_path_permanently_protected("~/Desktop/me and she/secret.txt") is True
    with pytest.raises(PrivacyViolationError):
        validate_workspace_path("~/Desktop/me and she/secret.txt")


def test_action_registry_redaction_actions():
    reg = create_default_registry()
    assert reg.get("redact_text") is not None
    assert reg.get("redact_image") is not None

    res = reg.execute(
        name="redact_text",
        text="Key: sk-1234567890abcdef1234567890",
    )
    assert res.success is True
    assert "[REDACTED_API_KEY]" in res.data["redacted_text"]


def test_router_redact_text_intent():
    handled, res = route_macos_intent("redact text My key is sk-1234567890abcdef1234567890", dry_run=True)
    assert handled is True
    assert res is not None
    assert res.action_name == "redact_text"
