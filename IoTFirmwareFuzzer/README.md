# IoT Firmware Grey-box Fuzzer

面向IoT固件协议的自动化灰盒模糊测试工具（毕业设计课题成果）。

## 功能概览

- **QEMU 仿真**：ARM/MIPS 等架构，用户模式与全系统模式
- **协议感知变异**：MQTT / CoAP / HTTP 结构保持变异
- **覆盖率引导**：AFL 兼容位图 + 响应引导（黑盒）
- **专家知识库**：危险函数与载荷注入
- **强化学习调度**：PPO-lite 优化变异与种子选择
- **崩溃分析**：去重、分类、可利用性评估与 HTML 报告

## 快速开始

```bash
pip install -r requirements.txt
python main.py seed mqtt -n 20
python main.py fuzz --no-qemu --protocol mqtt --timeout 60
```

## 项目结构

- `main.py` - CLI 入口（fuzz / seed / info）
- `config/default_config.yaml` - 默认配置
- `src/core/fuzzer.py` - 主引擎
- `src/emulation/` - QEMU 与固件解包
- `src/mutation/` - 协议变异与种子管理
- `src/coverage/` - 覆盖率追踪
- `src/expert/` - 知识库与 RL
- `src/analysis/` - 崩溃分析与报告

## 依赖

Python 3.10+，PyYAML / click / rich / numpy 等（见 requirements.txt）。可选：QEMU、Binwalk、GDB。
