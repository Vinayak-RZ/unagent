# Examples

Run from a clone after `pip install -e ".[dev]"`:

```bash
python -m superdeterminism recommend examples/advisor_stable_llm.json --n-min 1 --stdout json
python -m superdeterminism recommend examples/advisor_flip_to_det.json --stdout json
python -m superdeterminism validate examples/advisor_stable_llm.json
python -m superdeterminism inspect examples/advisor_stable_llm.json
python -m superdeterminism scaffold report.json --out scaffold/RUN
```

`advisor_stable_llm.json` is one span: ABSTAIN (n=1).  
`advisor_flip_to_det.json` is 40 identical classify traces: cassette-stable FlipToDet at default `n_min=30`.

Copy [custom_adapter.py](custom_adapter.py) for a house JSON mapper (`--adapter custom`).
