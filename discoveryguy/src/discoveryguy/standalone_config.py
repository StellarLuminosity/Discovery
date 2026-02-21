"""
Edit ACTIVE_CONFIG before running:
    python discoveryguy/src/standalone_run.py
"""

from dataclasses import dataclass, field


@dataclass
class StandaloneTargetConfig:
    project_id: str = "local-project"
    dg_id: str = "1"
    project_language: str = "c"
    source_dir: str = ""
    build_command: str = ""
    # Template used by TargetProject.run_pov(). Supported placeholders:
    # {input} / {input_path}, {harness} / {harness_name}, {sanitizer}, {source_dir}
    run_command: str = ""
    harness_name: str = "local_harness"
    harness_function_name: str = "LLVMFuzzerTestOneInput"
    harness_source_path: str = ""
    crash_keywords: list[str] = field(default_factory=list)


@dataclass
class StandaloneIOConfig:
    target_metadata: str = ""
    functions_by_file_index: str = ""
    function_index: str = ""
    target_functions_jsons_dir: str = ""
    aggregated_harness_info_file: str = ""
    function_ranking: str = ""
    sarif: str = ""
    sarif_meta: str = ""
    sarif_assessment_out_path: str = ""
    backup_seeds_vault: str = ""
    report_dir: str = ""
    fuzzers_sync_base: str = ""
    crash_dir_pass_to_pov: str = ""
    crash_metadata_dir_pass_to_pov: str = ""
    codeql_db_path: str = ""


@dataclass
class StandaloneRuntimeConfig:
    mode: str = "POIS"  # POIS or SARIF
    local_run: bool = True
    use_codeql_server: bool = False
    send_fuzz_request: bool = False
    skip_already_pwned: bool = False
    # Enable agentlib LLM API proxy mode (litellm-style backend).
    use_llm_api: bool = False
    llm_api_url: str = ""
    llm_api_key: str = ""
    jimmypwn_models: list[str] = field(default_factory=list)
    summary_models: list[str] = field(default_factory=list)
    honey_select_models: list[str] = field(default_factory=list)


@dataclass
class StandaloneConfig:
    target: StandaloneTargetConfig
    io: StandaloneIOConfig
    runtime: StandaloneRuntimeConfig


ACTIVE_CONFIG = StandaloneConfig(
    target=StandaloneTargetConfig(),
    io=StandaloneIOConfig(),
    runtime=StandaloneRuntimeConfig(),
)
