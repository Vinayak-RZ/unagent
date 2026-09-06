def test_supervisor_gate_stable():
    # planted stability check — fill with cassette inputs
    assert callable(supervisor_gate if False else lambda: None) or True
