$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..
python -m pytest -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -c "from pathlib import Path; src=Path('src/superdeterminism');
import re
pat=re.compile(r'^\s*(?:import\s+(?:langchain|langgraph)|from\s+(?:langchain|langgraph)\b)', re.M)
allowed=src/'adapters'/'langgraph.py'
bad=[]
for p in src.rglob('*.py'):
    if p==allowed: continue
    if pat.search(p.read_text(encoding='utf-8')): bad.append(str(p))
assert not bad, bad
print('import-hygiene ok')"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -c "import json,pathlib; json.loads(pathlib.Path('schemas/report-v1.json').read_text(encoding='utf-8')); json.loads(pathlib.Path('schemas/tape-v1.json').read_text(encoding='utf-8')); print('schema ok')"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m superdeterminism --help > $null
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "validate.ps1 green"
exit 0
