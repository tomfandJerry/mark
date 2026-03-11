"""专家知识库 - 危险函数与载荷"""
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional

logger = logging.getLogger("IoTFuzzer.KnowledgeBase")

@dataclass
class DangerousFunction:
    name: str
    category: str
    severity: int
    description: str
    cwe: str
    example_payloads: List[bytes]

BUILTIN = [
    DangerousFunction("strcpy", "overflow", 5, "无边界复制", "CWE-120", [b"A" * 256, b"A" * 1024]),
    DangerousFunction("sprintf", "overflow", 4, "无限制格式化", "CWE-120", [b"%s" * 50]),
    DangerousFunction("printf", "format_string", 4, "格式字符串", "CWE-134", [b"%s%s%s", b"%n"]),
    DangerousFunction("system", "injection", 5, "命令执行", "CWE-78", [b"; id", b"| cat /etc/passwd"]),
]

class ExpertKnowledgeBase:
    def __init__(self, extra_dangerous_funcs: List[str] = None, critical_regions: List[Dict] = None):
        self._functions: Dict[str, DangerousFunction] = {f.name: f for f in BUILTIN}
        if extra_dangerous_funcs:
            for name in extra_dangerous_funcs:
                if name not in self._functions:
                    self._functions[name] = DangerousFunction(name, "custom", 3, "用户自定义", "CWE-000", [])

    def get_dangerous_funcs(self) -> List[str]:
        return list(self._functions.keys())

    def get_payloads_for_function(self, name: str) -> List[bytes]:
        return self._functions.get(name, DangerousFunction("", "", 0, "", "", [])).example_payloads

    def get_all_expert_payloads(self) -> List[bytes]:
        out = []
        for f in self._functions.values():
            out.extend(f.example_payloads)
        return out

    def score_input(self, data: bytes) -> float:
        score = 0.0
        for f in self._functions.values():
            for p in f.example_payloads:
                if p and p in data: score += f.severity * 0.5
        if b"%s" in data or b"%n" in data: score += 2.0
        if len(data) > 1000: score += 1.0
        return min(score, 5.0)

    def get_severity_payloads(self, min_severity: int = 4) -> List[bytes]:
        return [p for f in self._functions.values() if f.severity >= min_severity for p in f.example_payloads]

    def get_stats(self) -> Dict:
        return {"total_dangerous_funcs": len(self._functions)}
