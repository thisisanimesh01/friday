"""Unit and regression tests for Milestone 5.3 Intelligent Memory & Personalization."""

from friday.memory.intelligence import (
    contains_sensitive_info,
    extract_preference_category,
    is_ephemeral_or_transient,
    is_fact_correction,
)
from friday.memory.local import (
    get_all,
    get_all_preferences,
    init_db,
    set_preference,
)
from friday.memory.memory_manager import (
    clear_memory,
    delete_memory,
    store_memory,
)


def setup_function():
    """Ensure clean database and context state before each test."""
    init_db()
    clear_memory()


def test_sensitive_info_filter():
    """Verify passwords, API keys, tokens, and credit cards are filtered from memory."""
    assert contains_sensitive_info("My password is SuperSecret123!") is True
    assert contains_sensitive_info("Here is my secret API key: sk-abcdef1234567890abcdef1234567890") is True
    assert contains_sensitive_info("My credit card number is 4111 2222 3333 4444") is True
    assert contains_sensitive_info("My favorite language is Python") is False

    # Storing sensitive turns must be blocked by intelligent filter
    mid1 = store_memory("My password is SuperSecret123!", "I will not store your password.")
    assert mid1 is None
    assert len(get_all()) == 0

    mid2 = store_memory("Export API_KEY=sk-12345678901234567890123456", "Saved key.")
    assert mid2 is None
    assert len(get_all()) == 0


def test_ephemeral_conversational_noise_filter():
    """Verify greetings, short acknowledgments, and transient queries are filtered."""
    assert is_ephemeral_or_transient("ok") is True
    assert is_ephemeral_or_transient("thanks") is True
    assert is_ephemeral_or_transient("what is the weather today?") is True
    assert is_ephemeral_or_transient("what time is it?") is True
    assert is_ephemeral_or_transient("system status") is True
    assert is_ephemeral_or_transient("I love building fast microservices in Go") is False

    # Storing ephemeral noise should be skipped
    mid = store_memory("ok", "Glad to help!")
    assert mid is None
    assert len(get_all()) == 0

    mid2 = store_memory("what time is it?", "It is 12:00 PM.")
    assert mid2 is None
    assert len(get_all()) == 0


def test_preference_recognition_and_storage():
    """Verify user preferences are recognized, extracted, and persisted to user_preferences table."""
    cat, val = extract_preference_category("My favorite programming language is Python")
    assert cat == "programming_language"
    assert "Python" in val

    mid = store_memory("My primary programming language is Python.", "Got it, Python recorded.")
    assert mid is not None

    prefs = get_all_preferences()
    assert "programming_language" in prefs
    assert prefs["programming_language"] == "Python"


def test_fact_correction_and_contradiction_handling():
    """Verify fact corrections supersede older conflicting memories."""
    # First state preference for Python
    mid1 = store_memory("My favorite programming language is Python.", "Noted, Python.")
    assert mid1 is not None
    assert get_all_preferences().get("programming_language") == "Python"
    assert len(get_all()) == 1

    # User later corrects/updates to Rust
    assert is_fact_correction("Actually, I switched to Rust for my projects.") is True
    mid2 = store_memory("Actually, I switched from Python to Rust as my primary language.", "Updated preference to Rust.")
    assert mid2 is not None

    # Check that user_preferences was updated
    prefs = get_all_preferences()
    assert prefs.get("programming_language") == "Rust"

    # Conflicting older memory with Python should be pruned/superseded
    memories = get_all()
    user_messages = [m[1] for m in memories]
    assert any("Rust" in m for m in user_messages)
    assert not any("favorite programming language is Python" in m for m in user_messages)


def test_persistence_and_restart_simulation():
    """Verify preferences and memories persist across reload."""
    set_preference("editor", "Neovim")
    store_memory("My project name is Project AETHER.", "Saved project AETHER.")

    # Re-read fresh
    prefs = get_all_preferences()
    assert prefs.get("editor") == "Neovim"

    mems = get_all()
    assert len(mems) == 1
    assert "Project AETHER" in mems[0][1]


def test_memory_deletion_and_clearing():
    """Verify deleting memory and clearing memory resets state."""
    store_memory("I like dark mode theme.", "Theme preference saved.")
    assert len(get_all()) == 1

    delete_memory("dark mode")
    assert len(get_all()) == 0

    store_memory("I like light mode theme.", "Theme preference saved.")
    clear_memory()
    assert len(get_all()) == 0
    assert len(get_all_preferences()) == 0
