import pytest

from friday.cli import build_parser


def test_cli_version(capsys):
    parser = build_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--version"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "friday" in captured.out.lower()


def test_cli_help(capsys):
    parser = build_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--help"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "--provider" in captured.out
    assert "--debug" in captured.out


def test_cli_provider_and_debug_flags():
    parser = build_parser()
    args = parser.parse_args(["--debug", "--provider", "ollama"])
    assert args.debug is True
    assert args.provider == "ollama"


def test_cli_invalid_provider():
    parser = build_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--provider", "unknown"])
    assert exc.value.code == 2
