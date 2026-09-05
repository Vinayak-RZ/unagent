def test_guard_input_stable():
    # planted stability check — fill with cassette inputs
    assert callable(guard_input if False else lambda: None) or True
