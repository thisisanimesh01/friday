import os

from sandbox import file_manager


def test_create_read_delete_restore_flow(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    trash = workspace / ".trash"
    workspace.mkdir()
    trash.mkdir()

    monkeypatch.setattr(file_manager, "BASE_DIR", str(workspace))
    monkeypatch.setattr(file_manager, "TRASH_DIR", str(trash))

    from security import path_validator
    monkeypatch.setattr(path_validator, "BASE_DIR", str(workspace))

    msg = file_manager.create_file("demo.txt", "hello friday")
    assert "created" in msg.lower()
    assert os.path.exists(workspace / "demo.txt")

    assert file_manager.read_file("demo.txt") == "hello friday"
    assert "demo.txt" in file_manager.list_files()

    del_msg = file_manager.delete_file("demo.txt")
    assert "trash" in del_msg.lower() or "deleted" in del_msg.lower()
    assert not os.path.exists(workspace / "demo.txt")
    assert len(file_manager.list_trash()) == 1
