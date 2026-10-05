# Repository guidance

## Project

- ECode is an experimental Python system for evolutionary coding agents and benchmark evaluation. See `README.md` for setup and run instructions.
- Python support and CI target Python 3.10.
- Main areas: `coding_agent.py`, `ecode.py`, `swe_bench/`, `polyglot/`, `tools/`, and `tests/`.

## Working in this repository

- Follow the existing module structure and keep changes focused on the requested behavior.
- Treat model-generated code, patches, benchmark repositories, and model output as untrusted. Review execution paths and preserve isolation around Docker-backed evaluation; do not run generated code directly on the host.
- Do not add credentials, local evaluation caches, or generated benchmark output to version control.
- Use the existing tests and CI checks; do not claim provider-backed or benchmark qualification from unit tests alone.

## Validation

CI uses Python 3.10 and runs:

```bash
ruff check .
python -m compileall -q analysis coding_agent.py coding_agent_polyglot.py ecode.py llm.py llm_withtools.py self_improve_step.py swe_bench polyglot prompts tools utils test_swebench.py
python -m pytest -q
```

Run the relevant checks for the change and report any checks that were not run or were blocked by environment requirements such as Docker, API credentials, or benchmark data.
