#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import yaml

from discoveryguy.config import Config, DiscoverGuyMode, CRSMode
from discoveryguy.standalone_config import ACTIVE_CONFIG


REPO_ROOT = Path(__file__).resolve().parents[2]
LIB_PATHS = [
    REPO_ROOT / "libs" / "crs-utils" / "src",
    REPO_ROOT / "libs" / "coveragelib",
    REPO_ROOT / "libs" / "agentlib",
    REPO_ROOT / "libs" / "debug-lib",
    REPO_ROOT / "libs" / "libcodeql" / "src",
]
for lib_path in LIB_PATHS:
    lib_path_str = str(lib_path)
    if lib_path.exists() and lib_path_str not in sys.path:
        sys.path.insert(0, lib_path_str)


def _set_default_output_paths():
    cfg = ACTIVE_CONFIG
    base = REPO_ROOT / "discoveryguy" / "standalone_outputs" / cfg.target.project_id

    if not cfg.io.report_dir:
        cfg.io.report_dir = str(base / "reports")
    if not cfg.io.backup_seeds_vault:
        cfg.io.backup_seeds_vault = str(base / "seed_backup")
    if not cfg.io.crash_dir_pass_to_pov:
        cfg.io.crash_dir_pass_to_pov = str(base / "pov_crashes")
    if not cfg.io.crash_metadata_dir_pass_to_pov:
        cfg.io.crash_metadata_dir_pass_to_pov = str(base / "pov_crash_meta")
    if not cfg.io.fuzzers_sync_base:
        cfg.io.fuzzers_sync_base = str(base / "fuzzer_sync")


def _mkdir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)


def _ensure_local_harness_info_file() -> str:
    cfg = ACTIVE_CONFIG

    out = cfg.io.aggregated_harness_info_file.strip()
    if out:
        out_path = Path(out)
        if out_path.exists():
            return str(out_path)
    else:
        out_path = Path(cfg.io.report_dir) / "generated_aggregated_harness_info.yaml"

    harness_id = "local-harness-id"
    build_id = "local-build-id"
    project_name = cfg.target.project_id
    source_entrypoint = cfg.target.harness_source_path.strip() or None

    payload = {
        "build_configurations": {
            build_id: {
                "project_id": cfg.target.project_id,
                "project_name": project_name,
                "sanitizer": "address",
                "architecture": "x86_64",
            }
        },
        "harness_infos": {
            harness_id: {
                "architecture": "x86_64",
                "build_configuration_id": build_id,
                "cp_harness_binary_path": cfg.target.harness_name,
                "cp_harness_name": cfg.target.harness_name,
                "entrypoint_function": cfg.target.harness_function_name,
                "project_harness_metadata_id": harness_id,
                "project_id": cfg.target.project_id,
                "project_name": project_name,
                "sanitizer": "address",
                "source_entrypoint": source_entrypoint,
            }
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return str(out_path)


def _validate_config() -> list[str]:
    cfg = ACTIVE_CONFIG
    errors = []

    def _req_file(name: str, value: str):
        if not value:
            errors.append(f"{name} is empty")
            return
        p = Path(value)
        if not p.exists():
            errors.append(f"{name} does not exist: {value}")
        elif not p.is_file():
            errors.append(f"{name} is not a file: {value}")

    def _req_dir(name: str, value: str):
        if not value:
            errors.append(f"{name} is empty")
            return
        p = Path(value)
        if not p.exists():
            errors.append(f"{name} does not exist: {value}")
        elif not p.is_dir():
            errors.append(f"{name} is not a directory: {value}")

    mode = cfg.runtime.mode.upper()
    if mode not in {"POIS", "SARIF"}:
        errors.append(f"Unsupported mode '{cfg.runtime.mode}'. Standalone supports only POIS or SARIF.")

    _req_dir("source_dir", cfg.target.source_dir)
    if not cfg.target.run_command.strip():
        errors.append("run_command is empty")
    if cfg.target.harness_name.strip() == "":
        errors.append("harness_name is empty")

    _req_file("target_metadata", cfg.io.target_metadata)
    _req_file("functions_by_file_index", cfg.io.functions_by_file_index)
    _req_file("function_index", cfg.io.function_index)
    _req_dir("target_functions_jsons_dir", cfg.io.target_functions_jsons_dir)
    if cfg.io.aggregated_harness_info_file:
        _req_file("aggregated_harness_info_file", cfg.io.aggregated_harness_info_file)
    if cfg.io.codeql_db_path:
        _req_dir("codeql_db_path", cfg.io.codeql_db_path)

    if cfg.runtime.use_llm_api:
        if not cfg.runtime.llm_api_url.strip():
            errors.append("runtime.use_llm_api is enabled but llm_api_url is empty")
        if not cfg.runtime.llm_api_key.strip():
            errors.append("runtime.use_llm_api is enabled but llm_api_key is empty")

    if mode == "POIS":
        _req_file("function_ranking", cfg.io.function_ranking)
    elif mode == "SARIF":
        _req_file("sarif", cfg.io.sarif)
        _req_file("sarif_meta", cfg.io.sarif_meta)
        if not cfg.io.sarif_assessment_out_path:
            errors.append("sarif_assessment_out_path is empty")

    return errors


def main():
    _set_default_output_paths()
    errors = _validate_config()
    if errors:
        print("Invalid standalone configuration:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(2)

    cfg = ACTIVE_CONFIG
    mode = cfg.runtime.mode.upper()
    _mkdir(cfg.io.backup_seeds_vault)
    _mkdir(cfg.io.report_dir)
    _mkdir(cfg.io.crash_dir_pass_to_pov)
    _mkdir(cfg.io.crash_metadata_dir_pass_to_pov)
    _mkdir(cfg.io.fuzzers_sync_base)
    harness_info_file = _ensure_local_harness_info_file()

    os.environ["LOCAL_RUN"] = "True" if cfg.runtime.local_run else "False"
    if cfg.runtime.use_llm_api:
        os.environ["USE_LLM_API"] = "1"
        os.environ["AIXCC_LITELLM_HOSTNAME"] = cfg.runtime.llm_api_url
        os.environ["LITELLM_KEY"] = cfg.runtime.llm_api_key

    Config.crs_mode = CRSMode.FULL
    Config.is_local_run = cfg.runtime.local_run
    Config.use_codeql_server = cfg.runtime.use_codeql_server
    Config.send_fuzz_request = cfg.runtime.send_fuzz_request
    Config.skip_already_pwned = cfg.runtime.skip_already_pwned
    Config.nap_mode = False
    if cfg.runtime.jimmypwn_models:
        Config.jimmypwn_llms = list(cfg.runtime.jimmypwn_models)
    if cfg.runtime.summary_models:
        Config.summary_agent_llms = list(cfg.runtime.summary_models)
    if cfg.runtime.honey_select_models:
        Config.honey_select_llms = list(cfg.runtime.honey_select_models)

    if mode == "POIS":
        Config.discoveryguy_mode = DiscoverGuyMode.POIS
    elif mode == "SARIF":
        Config.discoveryguy_mode = DiscoverGuyMode.SARIF
    else:
        print(f"Unsupported mode: {cfg.runtime.mode}")
        sys.exit(2)

    kwargs = {
        "project_id": cfg.target.project_id,
        "dg_id": cfg.target.dg_id,
        "project_language": cfg.target.project_language,
        "project_source": cfg.target.source_dir,
        "target_source_dir": cfg.target.source_dir,
        "target_build_command": cfg.target.build_command,
        "target_run_command": cfg.target.run_command,
        "target_harness_name": cfg.target.harness_name,
        "target_harness_function_name": cfg.target.harness_function_name,
        "target_harness_source_path": cfg.target.harness_source_path,
        "target_crash_keywords": cfg.target.crash_keywords,
        "target_metadata": cfg.io.target_metadata,
        "target_functions_jsons_dir": cfg.io.target_functions_jsons_dir,
        "aggregated_harness_info_file": harness_info_file,
        "functions_by_file_index": cfg.io.functions_by_file_index,
        "function_index": cfg.io.function_index,
        "function_ranking": cfg.io.function_ranking,
        "codeql_db_path": cfg.io.codeql_db_path,
        "backup_seeds_vault": cfg.io.backup_seeds_vault,
        "report_dir": cfg.io.report_dir,
        "fuzzers_sync_base": cfg.io.fuzzers_sync_base,
        "crash_dir_pass_to_pov": cfg.io.crash_dir_pass_to_pov,
        "crash_metadata_dir_pass_to_pov": cfg.io.crash_metadata_dir_pass_to_pov,
    }

    if mode == "SARIF":
        kwargs["sarif"] = cfg.io.sarif
        kwargs["sarif_meta"] = cfg.io.sarif_meta
        kwargs["sarif_assessment_out_path"] = cfg.io.sarif_assessment_out_path

    from discoveryguy.main import main as discovery_main
    discovery_main(**kwargs)


if __name__ == "__main__":
    main()
