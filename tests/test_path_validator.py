import os

import pytest

from security import path_validator


def test_get_safe_path_strips_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(path_validator, "BASE_DIR", str(tmp_path))
    safe = path_validator.get_safe_path("../../etc/passwd")
    assert safe == os.path.realpath(os.path.join(str(tmp_path), "passwd"))


def test_get_safe_path_blocks_external_symlink(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setattr(path_validator, "BASE_DIR", str(workspace))

    outside = tmp_path / "outside.txt"
    outside.write_text("secret")
    link = workspace / "link.txt"
    link.symlink_to(outside)

    with pytest.raises(PermissionError, match="outside workspace"):
        path_validator.get_safe_path("link.txt")
