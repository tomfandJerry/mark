"""核心模糊测试引擎 - 主循环与组件整合"""
import os
import time
import signal
import threading
import logging
import shutil
from typing import Dict, List

import yaml

from ..emulation.qemu_manager import QEMUManager, QEMUConfig, QEMUMode, ExecutionResult
from ..emulation.firmware_loader import FirmwareLoader
from ..mutation.seed_manager import SeedManager
from ..mutation.protocol_mutator import ProtocolMutator
from ..coverage.coverage_tracker import CoverageTracker, CoverageData, ResponseGuidedTracker
from ..expert.knowledge_base import ExpertKnowledgeBase
from ..expert.rl_optimizer import RLOptimizer, FuzzerState
from ..analysis.crash_analyzer import CrashAnalyzer, CrashRecord
from ..analysis.reporter import Reporter
from .scheduler import FuzzScheduler
from ..utils import FuzzerLogger, safe_mkdir, format_duration

logger = logging.getLogger("IoTFuzzer.Core")

class FuzzingStats:
    def __init__(self):
        self.start_time = time.time()
        self.total_execs = 0
        self.unique_crashes = 0
        self.execs_per_sec = 0.0
        self._exec_window = []

    def record_exec(self, crashed: bool = False):
        self.total_execs += 1
        if crashed: self.unique_crashes += 1
        now = time.time()
        self._exec_window.append(now)
        self._exec_window = [t for t in self._exec_window if now - t < 1.0]
        self.execs_per_sec = len(self._exec_window)

    @property
    def elapsed_secs(self): return time.time() - self.start_time

    def to_dict(self):
        return {"total_execs": self.total_execs, "unique_crashes": self.unique_crashes,
                "execs_per_sec": round(self.execs_per_sec, 1), "elapsed_secs": round(self.elapsed_secs, 1), "corpus_size": 0}

class IoTFirmwareFuzzer:
    def __init__(self, config_path: str = "./config/default_config.yaml"):
        self.config = self._load_config(config_path)
        self.output_dir = self.config.get("fuzzer", {}).get("output_dir", "./output")
        safe_mkdir(self.output_dir)
        self._flog = FuzzerLogger(self.output_dir)
        self._stats = FuzzingStats()
        self._stop_event = threading.Event()
        self._timeline: List[Dict] = []
        self._init_components()
        # 仅在主线程注册信号，Web UI 在子线程中运行时跳过（通过 API 停止）
        if threading.current_thread() is threading.main_thread():
            try:
                signal.signal(signal.SIGINT, lambda s, f: self._stop_event.set())
                signal.signal(signal.SIGTERM, lambda s, f: self._stop_event.set())
            except ValueError:
                pass  # 非主解释器或不可用

    def _init_components(self):
        cfg = self.config
        self.kb = ExpertKnowledgeBase(extra_dangerous_funcs=cfg.get("expert", {}).get("dangerous_funcs", []))
        self.coverage = CoverageTracker(method=cfg.get("coverage", {}).get("method", "stub"))
        self.response_tracker = ResponseGuidedTracker()
        seed_cfg = cfg.get("seed", {})
        self.seed_mgr = SeedManager(
            corpus_dir=seed_cfg.get("init_corpus", "./seeds"),
            schedule=seed_cfg.get("power_schedule", "fast"),
            max_seed_size=seed_cfg.get("max_seed_size", 65536),
            min_seed_size=seed_cfg.get("min_seed_size", 4),
            max_corpus=seed_cfg.get("max_corpus", 1000),
        )
        self.mutator = ProtocolMutator(cfg.get("protocol", {}).get("name", "mqtt"), cfg.get("mutation", {}).get("protocol_constraint", True))
        self.rl = RLOptimizer(enabled=cfg.get("expert", {}).get("rl_enabled", True), model_path=os.path.join(self.output_dir, "rl_model"))
        self.scheduler = FuzzScheduler(self.seed_mgr, self.mutator, self.coverage, self.kb, self.rl, cfg.get("mutation", {}).get("max_mutations_per_seed", 100))
        emu_cfg = cfg.get("emulation", {})
        qemu_cfg = QEMUConfig(mode=QEMUMode.USER, architecture=emu_cfg.get("architecture", "arm"), timeout=emu_cfg.get("timeout", 30),
                              binary=cfg.get("firmware", {}).get("target_binary", ""), root_fs=cfg.get("firmware", {}).get("root_fs", ""))
        self.qemu = QEMUManager(qemu_cfg, self.output_dir)
        self.crash_analyzer = CrashAnalyzer(self.output_dir, cfg.get("crash", {}).get("dedup_method", "backtrace"), max_crashes=cfg.get("fuzzer", {}).get("max_crashes", 100))
        self.reporter = Reporter(self.output_dir)

    def run(self, firmware_path: str = "", target_binary: str = "", timeout_secs: int = 0):
        self._flog.print_banner()
        self._flog.info(f"协议={self.config['protocol']['name']} 架构={self.config['emulation']['architecture']}")

        # 环境自检：检查 QEMU / Binwalk 是否可用，尽早给出友好提示
        emu_cfg = self.config.get("emulation", {})
        fw_cfg = self.config.get("firmware", {})
        if firmware_path and fw_cfg.get("extract", True):
            binwalk_bin = fw_cfg.get("binwalk_path", "binwalk")
            if shutil.which(binwalk_bin) is None:
                self._flog.warning(f"未检测到 Binwalk（当前配置为 '{binwalk_bin}'），将尝试直接使用固件目录，固件自动解包功能可能不可用。")

        # 若需要真实仿真，提前检查 QEMU 是否在 PATH 中
        qemu_needed = bool(firmware_path or target_binary)
        if qemu_needed:
            arch = emu_cfg.get("architecture", "arm")
            # 优先使用配置中的 qemu_user_path / qemu_path
            candidates = [
                emu_cfg.get("qemu_user_path"),
                emu_cfg.get("qemu_path"),
                f"qemu-{arch}",
            ]
            if not any(c and shutil.which(c) for c in candidates):
                self._flog.warning(
                    f"未在 PATH 中检测到适用于架构 {arch} 的 QEMU，可安装 qemu-user / qemu-system，"
                    f"或在配置中勾选存根模式（--no-qemu）仅体验流程。"
                )

        if firmware_path and os.path.exists(firmware_path):
            info = FirmwareLoader().load(firmware_path, target_binary)
            if info.target_binary:
                self.qemu.config.binary, self.qemu.config.root_fs = info.target_binary, info.root_fs
                self.qemu.config.architecture = info.architecture
                self._flog.success(f"固件: {info.target_binary}")
        if target_binary: self.qemu.config.binary = target_binary
        has_target = bool(self.qemu.config.binary)
        if has_target:
            try: self.qemu.start()
            except Exception as e: self._flog.warning(f"QEMU 启动失败: {e}"); has_target = False
        deadline = time.time() + timeout_secs if timeout_secs > 0 else float("inf")
        last_status = time.time()
        try:
            while not self._stop_event.is_set() and time.time() < deadline:
                input_data, meta = self.scheduler.next_input()
                result = self.qemu.run_input(input_data) if has_target else self._stub_execute(input_data)
                bitmap = self.coverage.read_bitmap()
                cov_data = self.coverage.process_bitmap(bitmap, result.crashed) if bitmap else None
                self.response_tracker.analyze_response(result.stdout, input_data)
                crash_record = self.crash_analyzer.analyze(result, input_data) if (result.crashed or result.timeout) else None
                if crash_record and crash_record.is_unique: self._stats.unique_crashes += 1; self._flog.crash(f"崩溃 #{self._stats.unique_crashes}")
                self.scheduler.feedback(input_data, cov_data, result.crashed, result.elapsed_ms, meta)
                self._stats.record_exec(result.crashed)
                if has_target and (result.crashed or result.timeout): self.qemu.reset()
                if time.time() - last_status >= 5:
                    self._flog.fuzzing(f"执行 {self._stats.total_execs:,} 速度 {self._stats.execs_per_sec:.0f}/s 崩溃 {self._stats.unique_crashes} 语料 {len(self.seed_mgr.seeds)} {format_duration(self._stats.elapsed_secs)}")
                    self._timeline.append({"time": self._stats.elapsed_secs, "execs": self._stats.total_execs, "crashes": self._stats.unique_crashes})
                    last_status = time.time()
        except KeyboardInterrupt:
            pass
        finally:
            self._finalize()

    def _stub_execute(self, data: bytes) -> ExecutionResult:
        import random
        time.sleep(random.uniform(0.001, 0.01))
        crashed = random.random() < 0.002
        return ExecutionResult(exit_code=-11 if crashed else 0, signal_num=11 if crashed else 0, stdout=b"OK", stderr=b"", elapsed_ms=random.randint(1, 50), crashed=crashed)

    def _finalize(self):
        try: self.qemu.stop()
        except Exception: pass
        stats = {"fuzzer": {**self._stats.to_dict(), "corpus_size": len(self.seed_mgr.seeds)}, "coverage": self.coverage.get_stats(), "crashes": self.crash_analyzer.get_stats(), "timeline": self._timeline}
        path = self.reporter.generate(stats, self.crash_analyzer.get_crashes(True), self.config, self.config.get("report", {}).get("format", "html"))
        self._flog.success(f"报告: {path} | 执行 {self._stats.total_execs:,} 崩溃 {self._stats.unique_crashes}")

    @staticmethod
    def _load_config(path: str) -> Dict:
        if not os.path.exists(path): return {"fuzzer": {"output_dir": "./output"}, "emulation": {"mode": "user", "architecture": "arm"}, "protocol": {"name": "mqtt"}, "mutation": {}, "coverage": {}, "expert": {}, "seed": {}, "crash": {}, "report": {"format": "html"}}
        with open(path, "r", encoding="utf-8") as f: return yaml.safe_load(f) or {}
