#!/usr/bin/env python3
import os
import sys
from pathlib import Path

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

    _req_file("target_metadata", cfg.io.target_metadata)
    _req_file("functions_by_file_index", cfg.io.functions_by_file_index)
    _req_file("function_index", cfg.io.function_index)
    _req_dir("target_functions_jsons_dir", cfg.io.target_functions_jsons_dir)
    _req_file("aggregated_harness_info_file", cfg.io.aggregated_harness_info_file)
    _req_dir("oss_fuzz_debug_targets_folder", cfg.target.oss_fuzz_debug_targets_folder)
    _req_dir("project_source", cfg.target.project_source)
    _req_dir("backup_seeds_vault", cfg.io.backup_seeds_vault)
    _req_dir("report_dir", cfg.io.report_dir)
    _req_dir("crash_dir_pass_to_pov", cfg.io.crash_dir_pass_to_pov)
    _req_dir("crash_metadata_dir_pass_to_pov", cfg.io.crash_metadata_dir_pass_to_pov)

    if mode == "POIS":
        _req_file("function_ranking", cfg.io.function_ranking)
    elif mode == "SARIF":
        _req_file("sarif", cfg.io.sarif)
        _req_file("sarif_meta", cfg.io.sarif_meta)
        if not cfg.io.sarif_assessment_out_path:
            errors.append("sarif_assessment_out_path is empty")

    return errors


def main():
    errors = _validate_config()
    if errors:
        print("Invalid standalone configuration:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(2)

    cfg = ACTIVE_CONFIG
    mode = cfg.runtime.mode.upper()

    os.environ["LOCAL_RUN"] = "True" if cfg.runtime.local_run else "False"

    Config.crs_mode = CRSMode.FULL
    Config.is_local_run = cfg.runtime.local_run
    Config.use_codeql_server = cfg.runtime.use_codeql_server
    Config.send_fuzz_request = cfg.runtime.send_fuzz_request
    Config.skip_already_pwned = cfg.runtime.skip_already_pwned
    Config.nap_mode = False

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
        "project_source": cfg.target.project_source,
        "oss_fuzz_debug_targets_folder": cfg.target.oss_fuzz_debug_targets_folder,
        "target_metadata": cfg.io.target_metadata,
        "target_functions_jsons_dir": cfg.io.target_functions_jsons_dir,
        "aggregated_harness_info_file": cfg.io.aggregated_harness_info_file,
        "functions_by_file_index": cfg.io.functions_by_file_index,
        "function_index": cfg.io.function_index,
        "function_ranking": cfg.io.function_ranking,
        "codeql_db_path": cfg.io.codeql_db_path,
        "backup_seeds_vault": cfg.io.backup_seeds_vault,
        "report_dir": cfg.io.report_dir,
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
