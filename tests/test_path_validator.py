import os
import pytest

from security import path_validator


def test_get_safe_path_strips_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(path_validator, "BASE_DIR", str(tmp_path))
    safe = path_validator.get_safe_path("../../etc/passwd")
    assert safe == os.path.realpath(os.path.join(str(tmp_path), "passwd"))


def test_get_safe_path_blocks_symlink(tmp_path, monkeypatch):
    monkeypatch.setattr(path_validator, "BASE_DIR", str(tmp_path))
    target = tmp_path / "real.txt"
    target.write_text("hello")
    link = tmp_path / "link.txt"
    link.symlink_to(target)

    with pytest.raises(PermissionError, match="symlink"):
        path_validator.get_safe_path("link.txt")
