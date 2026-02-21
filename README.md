# Discovery

Standalone DiscoveryGuy runner for local POI and SARIF-driven vulnerability discovery.

## Standalone Run

From repo root:

```bash
python discoveryguy/src/standalone_run.py
```

Configuration is fully file-driven (no CLI args).
Edit:

- `discoveryguy/src/discoveryguy/standalone_config.py`

Minimum required target fields in `StandaloneTargetConfig`:

- `source_dir`: absolute/relative path to your local C/C++ project source
- `build_command`: optional shell command run in `source_dir` before analysis
- `run_command`: shell command template to execute target with generated input

`run_command` supports placeholders:

- `{input}` or `{input_path}`
- `{harness}` or `{harness_name}`
- `{sanitizer}`
- `{source_dir}`

Optional custom LLM backend (in `StandaloneRuntimeConfig`):

- `use_llm_api = True`
- `llm_api_url`
- `llm_api_key`

Supported modes in standalone:

- `POIS`
- `SARIF`

Unsupported in standalone:

- `BYPASS`
- `POISBACKDOOR`
- `DIFFONLY`

## Notes

- Competition orchestration entrypoints were removed.
- DiscoveryGuy now runs as a local standalone workflow.
