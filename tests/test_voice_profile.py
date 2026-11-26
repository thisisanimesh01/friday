from friday.audio.voice_profile import VoiceProfile, VoiceRegistry


def test_voice_registry_defaults():
    registry = VoiceRegistry()
    hinata = registry.get_profile("hinata")

    assert hinata.profile_id == "hinata"
    assert hinata.speech_rate == 190
    assert hinata.target_style == "gentle"
    assert hinata.engine == "neural"
    assert "hinata" in hinata.primary_voice
    assert "Lekha" in hinata.hindi_voice
    assert "Samantha" in hinata.fallback_voice

    gentle = registry.get_profile("friday-gentle")
    assert gentle.profile_id == "friday-gentle"
    assert gentle.primary_voice == "hinata"
    assert gentle.target_style == "gentle"

    standard = registry.get_profile("friday-standard")
    assert standard.profile_id == "friday-standard"
    assert standard.speech_rate == 185
    assert standard.target_style == "standard"


def test_voice_registry_fallback_and_list():
    registry = VoiceRegistry()
    # Unknown ID should fall back to hinata
    fallback = registry.get_profile("non_existent_profile")
    assert fallback.profile_id == "hinata"

    profiles = registry.list_profiles()
    assert len(profiles) >= 3
    profile_ids = [p.profile_id for p in profiles]
    assert "hinata" in profile_ids
    assert "friday-gentle" in profile_ids
    assert "friday-standard" in profile_ids


def test_voice_registry_custom_registration():
    registry = VoiceRegistry()
    custom = VoiceProfile(
        profile_id="custom-test",
        display_name="Custom Profile",
        engine="native",
        primary_voice="TestVoice",
        hindi_voice="TestHindi",
        speech_rate=150,
        target_style="custom",
    )
    registry.register(custom)
    retrieved = registry.get_profile("custom-test")
    assert retrieved.profile_id == "custom-test"
    assert retrieved.speech_rate == 150
