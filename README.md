# ECode

**ECode** is an experimental system for evolutionary, self-improving coding agents. It proposes code changes, evaluates them with coding benchmarks, and uses those results to guide further iterations.

Canonical repository: [oigorbrito/ecode](https://github.com/oigorbrito/ecode)

## Setup

Configure the API keys required by the providers you use:

```bash
export OPENAI_API_KEY='...'
export ANTHROPIC_API_KEY='...'
```

For a local OpenAI-compatible server, configure the shared adapter without selecting a provider-specific code path:

```bash
export ECODE_OPENAI_BASE_URL='http://host.docker.internal:8080/v1'
export ECODE_OPENAI_MODEL='your-loaded-model-id'
# Optional for servers that require a token; defaults to "local".
export ECODE_OPENAI_API_KEY='local'
```

Use the server's OpenAI-compatible `/v1` base URL and a model identifier it accepts. Common defaults are `http://host.docker.internal:8080/v1` for llama.cpp server, `http://host.docker.internal:11434/v1` for Ollama, and `http://host.docker.internal:1234/v1` for LM Studio. This single contract is intended for all three; it adds no provider-specific integration. The local endpoint must be reachable from the Docker container running the coding agent. Adapter support is not, by itself, qualification of any server/model combination.

For explicit, read-only observation of Ollama's loaded context during a coding-agent run, set `ECODE_OLLAMA_API_BASE_URL` to the Ollama API root (for example, `http://host.docker.internal:11434`). ECode then queries Ollama `GET /api/ps` after each completion and records a context length only when exactly one loaded model name matches the response model. This setting does not select or replace the completion endpoint. Without it, the effective context is recorded as not observed. No declared model context is substituted for the loaded runtime value.

When `ECODE_OPENAI_BASE_URL` is set, the coding-agent container receives only the `ECODE_OPENAI_*` settings; cloud provider credentials are not forwarded on that path. Without it, the existing legacy provider credentials are passed as before. This routes model calls explicitly and does not add a provider fallback.

Verify Docker is available:

```bash
docker run hello-world
```

Install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

For analysis tools:

```bash
sudo apt-get install graphviz graphviz-dev
pip install -r requirements_dev.txt
```

Prepare SWE-bench using the revision supported by this project:

```bash
cd swe_bench
git clone https://github.com/princeton-nlp/SWE-bench.git
cd SWE-bench
git checkout dc4c087c2b9e4cefebf2e3d201d27e36
pip install -e .
cd ../../
```

Prepare Polyglot (Git username and email must be configured):

```bash
python -m polyglot.prepare_polyglot_dataset
```

## Run ECode

```bash
python ecode.py --help
python ecode.py
```

## Offline evolution-core qualification

Run the local, no-provider fixture through the ECode CLI with a fixed seed. This path exits before importing the provider/Docker execution path. Parent selection and archive retention can be changed independently:

```bash
python ecode.py --offline-fixture --fixture-output-dir .provenance/evolution-core-final-v2 --fixture-seed 7 --fixture-iterations 3 --fixture-parent-selector random --fixture-retention keep-all
python ecode.py --engine dgm --fixture-output-dir .provenance/evolution-core-dgm-v1 --fixture-seed 7 --fixture-iterations 3
```

`--engine dgm` is opt-in and fixture-only; it defaults to `dgm-weighted` parent selection. Use `--fixture-parent-selector best-score` or `--fixture-retention keep-last --fixture-archive-limit N` to select other fixture policies. Scores guide parent selection only; the fixture does not implement a promotion action. Production options such as `--continue_from`, `--polyglot` and `--max_generation` are rejected in this mode. The default `--engine legacy` keeps the production path on the legacy loop. `--offline-fixture` remains as a backwards-compatible fixture entry point.

The bundle is written under `.provenance/evolution-core/` and includes `run_config.json`, `baseline_manifest.json`, `archive.json`, `lineage.json`, per-agent/evaluation artifacts, JSONL telemetry, and `checksums.sha256`. The baseline manifest is marked `NEW_LOCAL_BASELINE` and records code/config/dataset/environment/seed/artifact identity; its dataset is the synthetic fixture specification, not an external benchmark dataset. It records that the checkout has no commit SHA when that is the case; source/config hashes remain available. The fixture proves only selection → simulated mutation → fixture evaluation → archive/lineage plumbing. It does not qualify an LLM provider, the legacy ECode benchmark harness, or benchmark performance.

Migration status: `ecode_core` owns the new contracts and loop; `ecode.py --engine dgm` routes an opt-in, deterministic fixture path through it before Docker/provider imports. `ecode.py --engine legacy` remains the default and retains the production loop. `ECodeEvaluator` adapts an injected ECode harness callback, but the production mutation/evaluation path is not yet integrated with `EvolutionEngine`.

## Empirical migration policy

The current empirical plan, qualification gates and local status are recorded in [`docs/ROADMAP.md`](docs/ROADMAP.md). Earlier donor-specific plans are preserved in [`docs/ROADMAP-BOOTSTRAP-HISTORY.md`](docs/ROADMAP-BOOTSTRAP-HISTORY.md). Agent instructions are in [`AGENTS.md`](AGENTS.md). Reusable development skills and specialized role boundaries are documented in [`docs/DEVELOPMENT-AGENTS.md`](docs/DEVELOPMENT-AGENTS.md). No upstream result is an ECode pass or migration authorization. Real-model mutation and orchestration have passed controlled synthetic fixture gates; real-repository repair remains unqualified (0/5 verified repairs in the localized editing experiment). Wave 0 remains incomplete. No benchmark, performance gain or SWE capability is claimed.

**License status:** this repository has no selected project license (`LICENSE-SELECT.md` is retained from the canonical repository). Source revisions considered during migration are tracked internally in `docs/donors/` for reproducibility; this is not a product credit list.

Run outputs are saved under `output_ecode/` by default. A local bootstrap evaluation cache is required to start a fresh run; place it under `.provenance/implementation-history/evaluation/swe-bench/` or `.provenance/implementation-history/evaluation/polyglot/`. This local data is excluded from version control and Docker build contexts.

## Project structure

- `analysis/` analysis and visualization scripts
- `coding_agent.py` coding agent implementation
- `ecode_core/` provider-neutral evolution contracts, engine, archive, lineage, telemetry, and adapters
- `ecode.py` ECode evolution entry point
- `polyglot/` Polyglot evaluation support
- `prompts/` prompts for foundation models
- `swe_bench/` SWE-bench evaluation support
- `tests/` automated tests
- `tools/` tools available to foundation models

## Safety

> [!WARNING]
> This repository executes untrusted, model-generated code. Such code may behave destructively. Use an appropriately isolated environment and review the risks before running it.

Sandbox policy: Docker isolation is required for generated-code execution. If Docker is unavailable or a required sandbox image/container cannot be built or started, the run is blocked; ECode must not fall back to executing generated code on the host. This fail-closed policy is ECode hardening, not a claim about upstream DGM behavior.

## Acknowledgements

ECode uses evaluation frameworks based on [SWE-bench](https://github.com/swe-bench/SWE-bench) and [Polyglot benchmark](https://github.com/Aider-AI/polyglot-benchmark).
