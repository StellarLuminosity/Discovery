from __future__ import annotations

import subprocess
import tempfile
import shutil
from pathlib import Path


class LocalImageRunResult:
    def __init__(self, run_exit_code: int, stdout: bytes, stderr: bytes):
        self.run_exit_code = run_exit_code
        self.stdout = stdout
        self.stderr = stderr


class LocalPOV:
    def __init__(self, triggered_sanitizers: list[str]):
        self.triggered_sanitizers = triggered_sanitizers


class LocalRunPovResult:
    def __init__(self, run_exit_code: int, stdout: bytes, stderr: bytes, triggered_sanitizers: list[str], command: str):
        self.run_exit_code = run_exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.command = command
        self.pov = LocalPOV(triggered_sanitizers)

    def __str__(self):
        decoded_stdout = self.stdout.decode(errors="ignore")
        decoded_stderr = self.stderr.decode(errors="ignore")
        return f"{decoded_stdout}\n{decoded_stderr}"


class TargetProject:
    """
    Standalone local target runner for custom C/C++ projects.
    """

    DEFAULT_CRASH_KEYWORDS = [
        "AddressSanitizer",
        "runtime error:",
        "Segmentation fault",
        "stack-overflow",
        "heap-buffer-overflow",
        "use-after-free",
    ]

    def __init__(
        self,
        source_dir: str,
        build_command: str,
        run_command: str,
        harness_function_name: str = "LLVMFuzzerTestOneInput",
        harness_source_path: str = "",
        crash_keywords: list[str] | None = None,
    ):
        self.source_dir = Path(source_dir).resolve()
        self.project_source = str(self.source_dir)
        self.project_path = str(self.source_dir)
        self.build_command = build_command.strip()
        self.run_command = run_command.strip()
        self.harness_function_name = harness_function_name.strip() or "LLVMFuzzerTestOneInput"
        self.harness_source_path = harness_source_path.strip()
        self.crash_keywords = crash_keywords or self.DEFAULT_CRASH_KEYWORDS
        repo_root = Path(__file__).resolve().parents[3]
        local_tmp_root = repo_root / "tmp"
        local_tmp_root.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir_work = Path(
            tempfile.mkdtemp(prefix="discoveryguy-work-", dir=str(local_tmp_root))
        )
        self._built = False

    def build_builder_image(self):
        return None

    def build_runner_image(self):
        return None

    def build_target(self):
        if self._built or not self.build_command:
            self._built = True
            return
        proc = subprocess.run(
            self.build_command,
            shell=True,
            cwd=str(self.source_dir),
            capture_output=True,
        )
        if proc.returncode != 0:
            stderr = proc.stderr.decode(errors="ignore")
            stdout = proc.stdout.decode(errors="ignore")
            raise RuntimeError(f"Target build failed.\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}")
        self._built = True

    def runner_image_run(self, command: str, timeout: int = 60, print_output: bool = False):
        # Local standalone equivalent of running `/work/run_script.sh` in a container.
        cmd = command.strip()
        if cmd.startswith("/work/"):
            script_name = Path(cmd).name
            run_cmd = ["bash", script_name]
        else:
            run_cmd = ["bash", "-lc", cmd]

        proc = subprocess.run(
            run_cmd,
            cwd=str(self.artifacts_dir_work),
            capture_output=True,
            timeout=timeout,
        )
        if print_output:
            print(proc.stdout.decode(errors="ignore"))
            print(proc.stderr.decode(errors="ignore"))
        return LocalImageRunResult(proc.returncode, proc.stdout, proc.stderr)

    def run_pov(self, harness_name: str, data_file: str, sanitizer: str = "address", timeout: int = 60):
        if not self.run_command:
            raise RuntimeError("target_run_command is empty. Configure it in standalone_config.py")

        command = self.run_command.format(
            input=data_file,
            input_path=data_file,
            harness=harness_name,
            harness_name=harness_name,
            sanitizer=sanitizer,
            source_dir=str(self.source_dir),
        )
        proc = subprocess.run(
            command,
            shell=True,
            cwd=str(self.source_dir),
            capture_output=True,
            timeout=timeout,
        )

        output_blob = (proc.stdout + proc.stderr).decode(errors="ignore").lower()
        triggered = []
        if proc.returncode != 0:
            triggered.append(sanitizer or "process-exit")
        elif any(marker.lower() in output_blob for marker in self.crash_keywords):
            triggered.append(sanitizer or "crash-marker")

        return LocalRunPovResult(proc.returncode, proc.stdout, proc.stderr, triggered, command)

    def get_harness_function_index_key(self, harness_name: str, func_resolver):
        for candidate in func_resolver.find_by_funcname(self.harness_function_name):
            return candidate
        for candidate in func_resolver.find_by_funcname(harness_name):
            return candidate
        raise RuntimeError(
            f"Could not resolve harness function key. Tried harness function '{self.harness_function_name}' and harness '{harness_name}'."
        )

    def get_harness_source_artifacts_path(self, harness_name: str, func_resolver):
        if self.harness_source_path:
            explicit = Path(self.harness_source_path)
            if explicit.exists():
                return str(explicit.resolve())

        harness_key = self.get_harness_function_index_key(harness_name, func_resolver)
        function_info = func_resolver.get(harness_key)
        if function_info and function_info.target_container_path:
            target_path = Path(str(function_info.target_container_path).lstrip("/"))
            direct = self.source_dir / target_path
            if direct.exists():
                return str(direct)
            if len(target_path.parts) > 1 and target_path.parts[0] == "src":
                under_src = self.source_dir / Path(*target_path.parts[1:])
                if under_src.exists():
                    return str(under_src)
            fallback = self.source_dir / target_path.name
            if fallback.exists():
                return str(fallback)
            for candidate in self.source_dir.rglob(target_path.name):
                return str(candidate)

        raise RuntimeError(f"Could not resolve harness source for harness '{harness_name}'.")

    def cleanup(self):
        if self.artifacts_dir_work.exists():
            shutil.rmtree(self.artifacts_dir_work, ignore_errors=True)
