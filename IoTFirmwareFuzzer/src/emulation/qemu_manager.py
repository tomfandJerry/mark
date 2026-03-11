"""QEMU 仿真管理器 - 支持用户模式/全系统，多架构"""
import os
import time
import signal
import subprocess
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable

logger = logging.getLogger("IoTFuzzer.QEMU")

class QEMUMode(Enum):
    USER = 1
    SYSTEM = 2

@dataclass
class QEMUConfig:
    mode: QEMUMode = QEMUMode.USER
    architecture: str = "arm"
    qemu_path: str = ""
    memory: str = "256M"
    binary: str = ""
    root_fs: str = ""
    gdb_port: int = 1234
    timeout: int = 30
    snapshot: bool = True
    extra_args: list = None

@dataclass
class ExecutionResult:
    exit_code: int = 0
    signal_num: int = 0
    stdout: bytes = b""
    stderr: bytes = b""
    elapsed_ms: int = 0
    crashed: bool = False
    timeout: bool = False
    pc_at_crash: int = 0
    backtrace: list = None

    def __post_init__(self):
        if self.backtrace is None:
            self.backtrace = []

QEMU_USER_BINS = {
    "arm": "qemu-arm", "mips": "qemu-mips", "mipsel": "qemu-mipsel",
    "aarch64": "qemu-aarch64", "x86": "qemu-i386", "x86_64": "qemu-x86_64",
}

class QEMUManager:
    def __init__(self, config: QEMUConfig, output_dir: str = "./output"):
        self.config = config
        self.output_dir = output_dir
        self._process: Optional[subprocess.Popen] = None
        self._crash_callback: Optional[Callable[[ExecutionResult], None]] = None

    def register_crash_callback(self, cb: Callable[[ExecutionResult], None]):
        self._crash_callback = cb

    def start(self):
        cmd = self._build_command()
        logger.info("启动 QEMU: %s", " ".join(cmd))
        self._process = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=os.environ.copy(),
        )
        time.sleep(0.2)

    def stop(self):
        if self._process and self._process.poll() is None:
            try:
                self._process.kill()
                self._process.wait(timeout=5)
            except Exception:
                pass
        self._process = None

    def reset(self):
        self.stop()
        self.start()

    def run_input(self, input_data: bytes) -> ExecutionResult:
        if self._process is None or self._process.poll() is not None:
            self.start()
        start = time.time()
        result = ExecutionResult()
        try:
            proc = subprocess.Popen(
                self._build_command(),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            stdout, stderr = proc.communicate(input=input_data, timeout=self.config.timeout)
            result.exit_code = proc.returncode
            result.stdout, result.stderr = stdout, stderr
            result.crashed = result.exit_code < 0 or result.exit_code in (139, 134)
            result.signal_num = -result.exit_code if result.exit_code < 0 else 0
        except subprocess.TimeoutExpired:
            proc.kill()
            result.timeout = result.crashed = True
        result.elapsed_ms = int((time.time() - start) * 1000)
        if result.crashed and self._crash_callback:
            self._crash_callback(result)
        return result

    def _build_command(self) -> list:
        cfg = self.config
        qemu_bin = cfg.qemu_path or QEMU_USER_BINS.get(cfg.architecture, "qemu-arm")
        cmd = [qemu_bin]
        if cfg.root_fs:
            cmd += ["-L", cfg.root_fs]
        cmd += ["-g", str(cfg.gdb_port)]
        cmd.append(cfg.binary)
        return cmd
