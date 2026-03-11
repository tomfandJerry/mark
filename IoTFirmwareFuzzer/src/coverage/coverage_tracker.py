"""覆盖率追踪 - AFL 位图与响应引导"""
import hashlib
import logging
import threading
from dataclasses import dataclass
from typing import Optional, Set, Dict

logger = logging.getLogger("IoTFuzzer.Coverage")

AFL_MAP_SIZE = 65536

@dataclass
class CoverageData:
    bitmap: bytes
    new_bits: int = 0
    total_bits: int = 0
    new_edges: Set[int] = None

    def __post_init__(self):
        if self.new_edges is None:
            self.new_edges = set()

class CoverageTracker:
    def __init__(self, method: str = "stub", map_size: int = AFL_MAP_SIZE, shm_id: Optional[str] = None):
        self.method = method
        self.map_size = map_size
        self._virgin_bits = bytearray(b"\xff" * map_size)
        self._lock = threading.Lock()
        self._total_executions = 0

    def read_bitmap(self) -> Optional[bytes]:
        if self.method == "stub":
            import random
            b = bytearray(self.map_size)
            for _ in range(random.randint(10, 100)):
                b[random.randint(0, self.map_size - 1)] = random.randint(1, 255)
            return bytes(b)
        return None

    def process_bitmap(self, bitmap: bytes, is_crash: bool = False) -> CoverageData:
        with self._lock:
            self._total_executions += 1
            data = CoverageData(bitmap=bitmap)
            virgin = self._virgin_bits
            for i in range(min(len(bitmap), self.map_size)):
                cur, prev = bitmap[i], virgin[i]
                new = cur & prev
                if new:
                    data.new_bits += bin(new).count("1")
                    data.new_edges.add(i)
                    virgin[i] &= ~new
                if cur:
                    data.total_bits += bin(cur).count("1")
            return data

    def get_stats(self) -> Dict:
        covered = sum(1 for b in self._virgin_bits if b != 0xFF)
        return {"total_executions": self._total_executions, "covered_edges": covered,
                "coverage_pct": f"{covered / self.map_size * 100:.2f}%", "map_size": self.map_size}

class ResponseGuidedTracker:
    def __init__(self):
        self._seen: Set[str] = set()

    def analyze_response(self, response: bytes, sent: bytes) -> Dict:
        key = hashlib.md5(response[:32]).hexdigest()[:8] if response else "empty"
        is_new = key not in self._seen
        self._seen.add(key)
        return {"new_signal": is_new, "signal_key": key}
