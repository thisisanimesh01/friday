import llm_router


def test_explicit_url_routing():
    res = llm_router.route_command("https://github.com/thisisanimesh01/friday")
    assert res["intent"] == "open_website"
    assert res["args"]["is_url"] is True
    assert res["args"]["website_name"] == "https://github.com/thisisanimesh01/friday"


def test_spotify_and_youtube_routing():
    sp = llm_router.route_command("play blinding lights on spotify")
    assert sp["intent"] == "play_spotify"
    assert sp["args"]["query"] == "blinding lights"

    yt = llm_router.route_command("play lofi beats on youtube")
    assert yt["intent"] == "play_youtube"
    assert yt["args"]["query"] == "lofi beats"


def test_deterministic_fallback_without_llm(monkeypatch):
    monkeypatch.setattr(llm_router, "client", None)
    monkeypatch.setattr(llm_router, "GEMINI_API_KEY", None)
    monkeypatch.setattr(llm_router, "LLM_PROVIDER", "auto")

    assert llm_router.route_command("what time is it")["intent"] == "get_time"
    assert llm_router.route_command("what is today's date")["intent"] == "get_date"
    assert llm_router.route_command("open github")["intent"] == "open_website"
    assert llm_router.route_command("tell me a joke")["intent"] == "chat"
