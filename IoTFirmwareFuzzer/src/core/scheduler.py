"""模糊测试调度器 - 协调种子、变异、专家、RL"""
import random
import logging
from typing import Optional, Tuple, Dict

from ..mutation.seed_manager import SeedManager, Seed
from ..mutation.protocol_mutator import ProtocolMutator
from ..expert.knowledge_base import ExpertKnowledgeBase
from ..expert.rl_optimizer import RLOptimizer, FuzzerState
from ..coverage.coverage_tracker import CoverageTracker, CoverageData

logger = logging.getLogger("IoTFuzzer.Scheduler")

class FuzzScheduler:
    EXPERT_INJECT_PROB = 0.15

    def __init__(self, seed_manager: SeedManager, mutator: ProtocolMutator, coverage: CoverageTracker,
                 knowledge_base: ExpertKnowledgeBase, rl_optimizer: RLOptimizer, max_mutations_per_seed: int = 100):
        self.seeds = seed_manager
        self.mutator = mutator
        self.coverage = coverage
        self.kb = knowledge_base
        self.rl = rl_optimizer
        self.max_muts = max_mutations_per_seed
        self._current_seed: Optional[Seed] = None
        self._mut_count = 0

    def next_input(self) -> Tuple[bytes, Dict]:
        if self._current_seed is None or self._mut_count >= self.max_muts:
            self._current_seed = self.seeds.select_next()
            self._mut_count = 0
        if self._current_seed is None:
            return b"\x00", {"source": "empty", "strategy": "none"}
        seed = self._current_seed
        if random.random() < self.EXPERT_INJECT_PROB:
            payloads = self.kb.get_severity_payloads(min_severity=4)
            if payloads:
                self._mut_count += 1
                return random.choice(payloads), {"source": "expert", "seed_id": seed.id, "strategy": "expert_payload"}
        state = FuzzerState(
            coverage_pct=float(self.coverage.get_stats().get("coverage_pct", "0").replace("%", "") or 0),
            total_execs=self.seeds.get_stats().get("total_execs", 0),
            corpus_size=len(self.seeds.seeds),
            favor_seed_ratio=sum(1 for s in self.seeds.seeds if s.favor) / max(len(self.seeds.seeds), 1),
        )
        decision = self.rl.decide(state)
        strategy = decision["mutation_strategy"]
        corpus = [s.data for s in random.choices(self.seeds.seeds, k=min(5, len(self.seeds.seeds)))] if self.seeds.seeds else []
        mutated = self.mutator.mutate(seed.data, strategy=strategy, corpus=corpus)
        expert_score = self.kb.score_input(mutated)
        self._mut_count += 1
        return mutated, {"source": "mutation", "seed_id": seed.id, "strategy": strategy, "expert_score": expert_score}

    def feedback(self, input_data: bytes, cov_data: Optional[CoverageData], crashed: bool, exec_time_ms: int, meta: Dict):
        seed = self._current_seed
        if seed is None: return
        if cov_data and cov_data.new_bits > 0:
            self.seeds.add_seed(input_data, parent_id=seed.id, coverage_map=cov_data.bitmap, expert_score=meta.get("expert_score", 0))
        self.seeds.update_seed_stats(seed, exec_time_ms, cov_data.bitmap if cov_data else None, False)
        self.rl.record_reward(self.rl.compute_reward(cov_data.new_bits if cov_data else 0, crashed, False, exec_time_ms, meta.get("expert_score", 0)))
        if self._mut_count % 500 == 0:
            self.seeds.update_favor()
