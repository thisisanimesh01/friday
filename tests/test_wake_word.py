from friday.audio.wake_word import (
    ListenerState,
    WakeWordEngine,
    WakeWordEvent,
    WakeWordListener,
)


def test_wake_word_engine_initialization():
    engine = WakeWordEngine(phrase="Hey Friday", sensitivity=0.7, cooldown=1.5)
    assert engine.phrase == "Hey Friday"
    assert engine.sensitivity == 0.7
    assert engine.cooldown == 1.5
    assert engine.is_available() is True


def test_wake_word_cooldown_and_simulation():
    engine = WakeWordEngine(phrase="Hey Friday", cooldown=0.5)
    event1 = engine.simulate_detection(confidence=0.92)
    assert event1 is not None
    assert isinstance(event1, WakeWordEvent)
    assert event1.phrase == "Hey Friday"
    assert event1.confidence == 0.92

    # Second immediate simulation should be suppressed by cooldown
    event2 = engine.simulate_detection(confidence=0.95)
    assert event2 is None

    # After cooldown reset, should trigger again
    engine.reset()
    event3 = engine.simulate_detection(confidence=0.99)
    assert event3 is not None
    assert event3.confidence == 0.99


def test_wake_word_listener_lifecycle():
    engine = WakeWordEngine()
    detected = []

    def on_wake(ev: WakeWordEvent) -> None:
        detected.append(ev)

    listener = WakeWordListener(engine=engine, on_wake=on_wake)
    assert listener.state == ListenerState.DISABLED

    listener.start()
    assert listener.state == ListenerState.STANDBY

    # Process empty frame
    res = listener.handle_audio_frame(b"")
    assert res is None
    assert listener.state == ListenerState.STANDBY

    # Simulate wake word trigger through listener
    simulated = engine.simulate_detection(confidence=0.9)
    assert simulated is not None

    listener.stop()
    assert listener.state == ListenerState.DISABLED
