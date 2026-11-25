from friday import runtime_mode
from friday.cli import build_parser


def test_cli_mode_flag():
    parser = build_parser()
    assert parser.parse_args(["--mode", "offline"]).mode == "offline"
    assert parser.parse_args(["--mode", "online"]).mode == "online"
    assert parser.parse_args(["--mode", "auto"]).mode == "auto"


def test_offline_mode_overrides_cloud_fallback(monkeypatch):
    monkeypatch.setenv("FRIDAY_MODE", "offline")
    monkeypatch.setenv("ALLOW_CLOUD_FALLBACK", "true")

    assert runtime_mode.get_mode() == "offline"
    assert runtime_mode.is_offline_mode() is True
    assert runtime_mode.cloud_fallback_allowed() is False
    assert runtime_mode.check_connectivity() is False


def test_online_mode_respects_allow_cloud_fallback(monkeypatch):
    monkeypatch.setenv("FRIDAY_MODE", "online")
    monkeypatch.setenv("ALLOW_CLOUD_FALLBACK", "false")
    assert runtime_mode.cloud_fallback_allowed() is False

    monkeypatch.setenv("ALLOW_CLOUD_FALLBACK", "true")
    assert runtime_mode.cloud_fallback_allowed() is True
