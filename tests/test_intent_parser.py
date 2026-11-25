from intent_parser import detect_intent, extract_filename


def test_extract_filename_matches_extension():
    assert extract_filename("create file notes.txt") == "notes.txt"
    assert extract_filename("open report_1.pdf") == "report_1.pdf"


def test_extract_filename_fallback():
    assert extract_filename("create a new file") == "test.txt"


def test_detect_intent_commands():
    assert detect_intent("create file hello.txt") == "create_file"
    assert detect_intent("remove file old.txt") == "delete_file"
    assert detect_intent("what is the weather today") == "weather"
    assert detect_intent("play lofi on youtube") == "play_youtube"
    assert detect_intent("play jazz on spotify") == "play_spotify"


def test_detect_intent_chat_fallback():
    assert detect_intent("hello how are you") == "chat"
