from dataclasses import dataclass


@dataclass
class StandaloneTargetConfig:
    project_id: str = "local-project"
    dg_id: str = "1"
    project_source: str = ""
    oss_fuzz_debug_targets_folder: str = ""


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
