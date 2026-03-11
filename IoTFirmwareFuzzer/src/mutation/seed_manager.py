"""种子语料库管理 - Power Schedule 调度 + 语料库修剪"""
import os
import random
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Set

from ..utils import sha256_hash, timestamp_ms, safe_mkdir

logger = logging.getLogger("IoTFuzzer.SeedManager")

@dataclass
class Seed:
    id: int
    data: bytes
    path: str = ""
    checksum: str = ""
    coverage_map: Optional[bytes] = None
    unique_edges: int = 0
    exec_time_ms: int = 0
    exec_count: int = 0
    energy: float = 1.0
    fuzz_level: int = 0
    favor: bool = False
    parent_id: int = -1
    mutation_type: str = "initial"
    expert_score: float = 0.0

    def __post_init__(self):
        if not self.checksum:
            self.checksum = sha256_hash(self.data)

class SeedManager:
    def __init__(self, corpus_dir: str, schedule: str = "fast", max_seed_size: int = 65536,
                 min_seed_size: int = 4, max_corpus: int = 1000):
        self.corpus_dir = corpus_dir
        self.max_seed_size = max_seed_size
        self.min_seed_size = min_seed_size
        self.max_corpus = max_corpus
        self.seeds: List[Seed] = []
        self._id_counter = 0
        self._total_execs = 0
        self._seen_checksums: Set[str] = set()
        self._coverage_hashes: Set[str] = set()
        safe_mkdir(corpus_dir)
        self._load_corpus()

    def _load_corpus(self):
        if not os.path.isdir(self.corpus_dir): return
        for fname in os.listdir(self.corpus_dir):
            fpath = os.path.join(self.corpus_dir, fname)
            if os.path.isfile(fpath):
                try:
                    data = open(fpath, "rb").read()
                    if self.min_seed_size <= len(data) <= self.max_seed_size:
                        self.add_seed(data, path=fpath, mutation_type="initial")
                except Exception:
                    pass
        if not self.seeds:
            for d in [b"\x10\x00", b"GET / HTTP/1.0\r\n\r\n", bytes(4)]:
                self.add_seed(d, mutation_type="minimal")

    def add_seed(self, data: bytes, path: str = "", parent_id: int = -1, coverage_map: bytes = None,
                 expert_score: float = 0.0, mutation_type: str = "mutation") -> Optional[Seed]:
        if not data or len(data) < self.min_seed_size: return None
        data = data[:self.max_seed_size]
        checksum = sha256_hash(data)
        if checksum in self._seen_checksums: return None
        self._seen_checksums.add(checksum)
        seed = Seed(id=self._id_counter, data=data, path=path, checksum=checksum, coverage_map=coverage_map,
                   parent_id=parent_id, mutation_type=mutation_type, expert_score=expert_score)
        if coverage_map:
            ch = sha256_hash(coverage_map)
            if ch in self._coverage_hashes: return None
            self._coverage_hashes.add(ch)
            seed.unique_edges = sum(1 for b in coverage_map if b > 0)
        self._id_counter += 1
        self.seeds.append(seed)
        seed.path = path or os.path.join(self.corpus_dir, f"id_{seed.id:06d}_{checksum[:8]}")
        if not path:
            open(seed.path, "wb").write(seed.data)

        # 语料库过大时自动修剪，避免内存与磁盘无限膨胀
        if len(self.seeds) > self.max_corpus:
            self._shrink_corpus()
        return seed

    def select_next(self) -> Optional[Seed]:
        if not self.seeds: return None
        favor = [s for s in self.seeds if s.favor]
        if favor and random.random() < 0.5: return random.choice(favor)
        # 限制 fuzz_level 指数，避免 2**fuzz_level 溢出
        weights = [max(1.0, 100 / max(s.exec_time_ms, 1)) * (2.0 ** min(s.fuzz_level, 24)) for s in self.seeds]
        total = sum(weights)
        return random.choices(self.seeds, weights=[w / total for w in weights], k=1)[0]

    def update_seed_stats(self, seed: Seed, exec_time_ms: int, coverage_map: bytes = None, hit_dangerous: bool = False):
        seed.exec_count += 1
        seed.exec_time_ms = (seed.exec_time_ms + exec_time_ms) // 2
        seed.fuzz_level = min(seed.fuzz_level + 1, 24)  # 上限 24，避免权重计算溢出
        self._total_execs += 1
        if coverage_map and not seed.coverage_map:
            seed.coverage_map = coverage_map
            seed.unique_edges = sum(1 for b in coverage_map if b > 0)
        if hit_dangerous:
            seed.expert_score = min(seed.expert_score + 0.5, 5.0)

    def update_favor(self):
        if not self.seeds: return
        sorted_seeds = sorted(self.seeds, key=lambda s: s.unique_edges, reverse=True)
        for i, s in enumerate(sorted_seeds):
            s.favor = i < max(1, len(sorted_seeds) // 5)

    def get_stats(self) -> Dict:
        return {"total_seeds": len(self.seeds), "total_execs": self._total_execs,
                "favor_seeds": sum(1 for s in self.seeds if s.favor)}

    def _shrink_corpus(self) -> None:
        """根据覆盖率与执行统计对语料库进行修剪，仅保留高价值种子。"""
        if len(self.seeds) <= self.max_corpus:
            return
        # 优先保留：favor 种子 + 覆盖边数多、执行时间短的种子
        favor_seeds = [s for s in self.seeds if s.favor]
        others = [s for s in self.seeds if not s.favor]
        others_sorted = sorted(
            others,
            key=lambda s: (-s.unique_edges, s.exec_time_ms, -s.exec_count),
        )
        keep = favor_seeds + others_sorted[: max(0, self.max_corpus - len(favor_seeds))]
        removed = len(self.seeds) - len(keep)
        self.seeds = keep
        logger.info("语料库已修剪：当前 %d 个种子，移除 %d 个低优先级种子", len(self.seeds), removed)
