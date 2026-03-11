"""崩溃分析器 - 去重、分类、可利用性评估"""
import os
import json
import signal
import hashlib
import logging
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict, Set
from datetime import datetime

from ..emulation.qemu_manager import ExecutionResult
from ..utils import sha256_hash, safe_mkdir

logger = logging.getLogger("IoTFuzzer.CrashAnalyzer")

class CrashType(Enum):
    SEGFAULT = "段错误（非法内存访问）"
    STACK_OVERFLOW = "栈溢出"
    HEAP_OVERFLOW = "堆溢出"
    FORMAT_STRING = "格式字符串漏洞"
    NULL_DEREF = "空指针解引用"
    ABORT = "程序异常终止"
    TIMEOUT = "超时/挂起"
    UNKNOWN = "未知类型"

class Exploitability(Enum):
    HIGH = "高（可能被利用）"
    MEDIUM = "中（需进一步分析）"
    LOW = "低（难以利用）"
    UNKNOWN = "未知"

@dataclass
class CrashRecord:
    id: str
    timestamp: str
    input_hash: str
    input_data: bytes
    crash_type: CrashType = CrashType.UNKNOWN
    exploitability: Exploitability = Exploitability.UNKNOWN
    signal_num: int = 0
    pc_at_crash: int = 0
    backtrace: List[str] = None
    stderr_output: str = ""
    dedup_key: str = ""
    is_unique: bool = True
    input_path: str = ""
    analysis_notes: List[str] = None

    def __post_init__(self):
        if self.backtrace is None: self.backtrace = []
        if self.analysis_notes is None: self.analysis_notes = []

class CrashAnalyzer:
    def __init__(self, output_dir: str = "./output", dedup_method: str = "backtrace", binary: str = "", max_crashes: int = 100):
        self.crash_dir = os.path.join(output_dir, "crashes")
        self.dedup_method = dedup_method
        self.max_crashes = max_crashes
        safe_mkdir(self.crash_dir)
        self._crashes: List[CrashRecord] = []
        self._dedup_keys: Set[str] = set()
        self._total_seen = 0

    def analyze(self, result: ExecutionResult, input_data: bytes) -> Optional[CrashRecord]:
        if not result.crashed and not result.timeout: return None
        self._total_seen += 1
        input_hash = sha256_hash(input_data)
        dedup_key = hashlib.md5((str(result.backtrace[:3]) + str(result.signal_num)).encode()).hexdigest()
        is_unique = dedup_key not in self._dedup_keys
        record = CrashRecord(
            id=f"crash_{len(self._crashes):04d}_{dedup_key[:8]}",
            timestamp=datetime.now().isoformat(),
            input_hash=input_hash, input_data=input_data,
            signal_num=result.signal_num, pc_at_crash=result.pc_at_crash,
            backtrace=result.backtrace or [],
            stderr_output=result.stderr.decode("utf-8", errors="replace")[:1024],
            dedup_key=dedup_key, is_unique=is_unique,
        )
        record.crash_type = CrashType.SEGFAULT if result.signal_num == 11 else CrashType.TIMEOUT if result.timeout else CrashType.UNKNOWN
        record.exploitability = Exploitability.HIGH if record.crash_type == CrashType.STACK_OVERFLOW else Exploitability.MEDIUM
        if is_unique:
            self._dedup_keys.add(dedup_key)
            if len(self._crashes) < self.max_crashes:
                self._crashes.append(record)
                record.input_path = os.path.join(self.crash_dir, f"{record.id}.bin")
                open(record.input_path, "wb").write(input_data)
                with open(os.path.join(self.crash_dir, f"{record.id}.json"), "w", encoding="utf-8") as f:
                    json.dump({"id": record.id, "crash_type": record.crash_type.value, "exploitability": record.exploitability.value,
                               "pc": f"0x{record.pc_at_crash:08x}", "backtrace": record.backtrace}, f, indent=2)
                logger.info(f"[CRASH] #{len(self._crashes)}: {record.crash_type.value} | {record.exploitability.value}")
        return record

    def get_crashes(self, unique_only: bool = True) -> List[CrashRecord]:
        return [c for c in self._crashes if c.is_unique] if unique_only else self._crashes

    def get_stats(self) -> Dict:
        u = [c for c in self._crashes if c.is_unique]
        return {"total_seen": self._total_seen, "unique_crashes": len(u),
                "high_severity": sum(1 for c in u if c.exploitability == Exploitability.HIGH)}
