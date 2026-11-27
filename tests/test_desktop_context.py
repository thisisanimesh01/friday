"""Unit tests for Milestone 7.3: Active Window Awareness & Desktop Context."""

from __future__ import annotations

from friday.macos.desktop_context import (
    classify_desktop_intent,
    filter_sensitive_title,
    get_desktop_context,
)
from friday.macos.registry import default_registry
from friday.macos.router import route_macos_intent


def test_desktop_context_dry_run_never_touches_hardware():
    ctx = get_desktop_context(dry_run=True)
    assert ctx.status == "dry_run"
    assert "[DRY_RUN]" in ctx.frontmost_app_name
    assert len(ctx.screens) > 0
    assert len(ctx.visible_windows) > 0


def test_desktop_context_structure():
    ctx = get_desktop_context(filter_privacy=True)
    assert ctx.status == "success"
    assert isinstance(ctx.frontmost_app_name, str)
    assert isinstance(ctx.frontmost_bundle_id, str)
    assert isinstance(ctx.screens, list)
    assert isinstance(ctx.visible_windows, list)
    assert ctx.latency_seconds > 0.0


def test_classify_desktop_intent_metadata_vs_visual():
    intent_meta, auth_meta = classify_desktop_intent("Which application am I using?")
    assert intent_meta == "metadata"
    assert auth_meta is False

    intent_meta2, auth_meta2 = classify_desktop_intent("Current window ka size batao")
    assert intent_meta2 == "metadata"
    assert auth_meta2 is False

    intent_vis, auth_vis = classify_desktop_intent("Explain the error on my screen")
    assert intent_vis == "visual"
    assert auth_vis is True

    intent_vis2, auth_vis2 = classify_desktop_intent("Screen par kya likha hai ocr karo")
    assert intent_vis2 == "visual"
    assert auth_vis2 is True


def test_privacy_guard_censors_protected_folder_window_title():
    raw_title = "Finder - /Users/animeshyadav/Desktop/me and she/private_photos"
    censored, is_sens = filter_sensitive_title(raw_title)
    assert is_sens is True
    assert "me and she" not in censored
    assert "[PROTECTED_OR_SENSITIVE]" in censored


def test_privacy_guard_censors_keychain_passwords():
    raw_title = "Passwords & Keychain Access"
    censored, is_sens = filter_sensitive_title(raw_title)
    assert is_sens is True
    assert "[PROTECTED_OR_SENSITIVE]" in censored


def test_action_registry_milestone_7_3_actions():
    actions = default_registry.list_actions()
    names = {a["name"] if isinstance(a, dict) else a.name for a in actions}
    assert "get_desktop_context" in names
    assert "get_active_window_context" in names
    assert "get_display_layout" in names


def test_router_desktop_context_natural_language_intents():
    m1, res1 = route_macos_intent("which application am I using?", dry_run=True)
    assert m1 is True
    assert res1.action_name == "get_active_window_context"

    m2, res2 = route_macos_intent("what window is currently active?", dry_run=True)
    assert m2 is True
    assert res2.action_name == "get_active_window_context"

    m3, res3 = route_macos_intent("which monitor am I using?", dry_run=True)
    assert m3 is True
    assert res3.action_name == "get_display_layout"

    m4, res4 = route_macos_intent("how are my windows arranged?", dry_run=True)
    assert m4 is True
    assert res4.action_name == "get_desktop_context"

    m5, res5 = route_macos_intent("screen par kya khula hai?", dry_run=True)
    assert m5 is True
    assert res5.action_name == "get_desktop_context"
