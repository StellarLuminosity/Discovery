from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent
DISCOVERYGUY_SRC_ROOT = PACKAGE_ROOT.parent
PROMPTS_ROOT = PACKAGE_ROOT / "prompts"
RUN_DISCO_FUZZ_PATH = DISCOVERYGUY_SRC_ROOT / "run_disco_fuzz.py"
CODEQL_TEMPLATES_ROOT = PACKAGE_ROOT / "toolbox" / "templates" / "codeql"
