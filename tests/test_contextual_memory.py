"""Unit and regression tests for Milestone 5.2 Contextual Memory Improvements."""

from friday.memory.local import get_all, init_db
from friday.memory.memory_manager import (
    clear_memory,
    delete_memory,
    load_personality,
    retrieve_memory,
    store_memory,
)


def setup_function():
    """Ensure clean database state before each test."""
    init_db()
    clear_memory()



def test_memory_storage_and_retrieval():
    mid = store_memory("My favorite project is Project LUNA", "I will remember that you love Project LUNA!")
    assert mid is not None

    memories = get_all()
    assert len(memories) == 1
    assert "Project LUNA" in memories[0][1]

    # Test semantic retrieval
    results = retrieve_memory("favorite project", limit=5)
    assert len(results) >= 1
    assert "Project LUNA" in results[0][1]


def test_memory_deduplication():
    # Store first turn
    id1 = store_memory("What is my current GPU?", "You are on an Apple Silicon M1 unified memory.")
    assert id1 is not None

    # Storing identical turn should be skipped by deduplication
    id2 = store_memory("What is my current GPU?", "You are on an Apple Silicon M1 unified memory.", deduplicate=True)
    assert id2 is None

    memories = get_all()
    assert len(memories) == 1


def test_memory_deletion_controls():
    id1 = store_memory("Remember to buy groceries", "Added to your memory.")
    id2 = store_memory("Meeting at 3 PM today", "I have noted your meeting at 3 PM.")
    assert id1 is not None and id2 is not None

    memories = get_all()
    assert len(memories) == 2

    # Delete by string ID
    deleted = delete_memory(str(id1))
    assert deleted is True

    memories_after = get_all()
    assert len(memories_after) == 1
    assert "Meeting" in memories_after[0][1]

    # Delete by keyword query
    deleted_query = delete_memory("Meeting")
    assert deleted_query is True

    assert len(get_all()) == 0


def test_clear_all_memory():
    store_memory("Query 1", "Reply 1")
    store_memory("Query 2", "Reply 2")
    assert len(get_all()) == 2

    cnt = clear_memory()
    assert cnt == 2
    assert len(get_all()) == 0

    # Ensure in-memory session history is also cleared
    p = load_personality()
    assert len(p.get("full_history", [])) == 0
    assert len(p.get("history", [])) == 0


def test_short_term_context_accumulation():
    store_memory("Hello Friday", "Hello! How can I assist you?")
    store_memory("I am working on Milestone 5.2", "That sounds like a great milestone.")

    p = load_personality()
    full_history = p.get("full_history", [])
    assert len(full_history) == 2
    assert full_history[0]["user"] == "Hello Friday"
    assert "Milestone 5.2" in full_history[1]["user"]
