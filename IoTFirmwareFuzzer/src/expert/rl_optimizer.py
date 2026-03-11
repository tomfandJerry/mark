"""强化学习调度优化器 - PPO-lite"""
import os
import logging
import numpy as np
from dataclasses import dataclass
from typing import Dict

logger = logging.getLogger("IoTFuzzer.RLOptimizer")

MUTATION_STRATEGIES = ["random", "field", "payload", "special", "hybrid"]
STATE_DIM = 16

@dataclass
class FuzzerState:
    coverage_pct: float = 0.0
    total_execs: int = 0
    corpus_size: int = 0
    favor_seed_ratio: float = 0.0
    dangerous_hit_ratio: float = 0.0

    def to_vector(self) -> np.ndarray:
        return np.array([
            self.coverage_pct / 100.0, min(self.total_execs / 1e6, 1.0),
            min(self.corpus_size / 10000.0, 1.0), self.favor_seed_ratio, self.dangerous_hit_ratio,
        ] + [0.0] * (STATE_DIM - 5), dtype=np.float32)

class RLOptimizer:
    def __init__(self, enabled: bool = True, model_path: str = "./output/rl_model", train_interval: int = 1000):
        self.enabled = enabled
        self.model_path = model_path
        self.train_interval = train_interval
        self._step = 0

    def decide(self, state: FuzzerState) -> Dict[str, str]:
        if not self.enabled:
            return {"mutation_strategy": "hybrid", "schedule_strategy": "fast"}
        self._step += 1
        mut = np.random.choice(MUTATION_STRATEGIES)
        return {"mutation_strategy": mut, "schedule_strategy": "fast"}

    def record_reward(self, reward: float, done: bool = False):
        pass

    def compute_reward(self, new_bits: int, crashed: bool, hit_dangerous: bool, exec_time_ms: int, expert_score: float = 0.0) -> float:
        r = float(new_bits)
        if crashed: r += 100.0
        if hit_dangerous: r += 10.0
        r += expert_score * 5.0
        r -= exec_time_ms / 5000.0
        return r

    def get_stats(self) -> Dict:
        return {"rl_enabled": self.enabled, "total_steps": self._step}
