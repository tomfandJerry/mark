# -*- coding: utf-8 -*-
"""文献全文：英文各节与对应中文译文（用于生成完整文献翻译 Word）"""

# 英文各节：(节标题, 段落列表，每段一段字符串)
EN_SECTIONS = [
    ("Abstract", [
        "In network protocol fuzzing, effective seed scheduling plays a critical role in improving testing efficiency. Traditional state-driven seed scheduling methods in network protocol fuzzing are often limited by imbalanced seed selection, monolithic scheduling strategies, and ineffective power allocation. To overcome these limitations, we propose SCFuzz, specifically by employing a multi-armed bandit model to dynamically balance exploration and exploitation across multiple fuzzing phases. The fuzzing process is divided into initial, middle, and final phases with seed selection strategies adapted at each phase to optimize the discovery of new states, paths, and code coverage. Additionally, SCFuzz employs a power allocation method based on state weights, focusing power on high-potential messages to improve the overall fuzzing efficiency. Experimental evaluations on open-source protocol implementations show that SCFuzz significantly improves state and code coverage, achieving up to 17.10% more states, 22.92% higher state transitions, and 7.92% greater code branch coverage compared to AFLNet. Moreover, SCFuzz improves seed selection effectiveness by 389.37% and increases power utilization by 45.61%, effectively boosting the overall efficiency of fuzzing.",
    ]),
    ("1. Introduction", [
        "Fuzzing is a widely used and effective software testing technique that is distinguished by its high level of automation, extensive applicability, and demonstrated efficacy in identifying software vulnerabilities. At its core, fuzzing operates through an iterative process where input seeds are selected from an initial seed pool and modified through mutations to create diverse test cases; then, these cases are executed on the target software.",
        "In recent years, the focus of fuzzing research has primarily centered on coverage-based graybox fuzzing (CGF), which improves testing efficiency by leveraging feedback from code coverage. Building upon the foundations of CGF, researchers have extended these techniques to the domain of network protocol testing, leading to the development of stateful coverage-based graybox fuzzing (SCGF). SCGF not only relies on code coverage information but also integrates state information extracted from network protocol implementations. This allows it to manage complex protocol state transitions and interdependent interactions, providing a more nuanced and effective approach to identifying vulnerabilities in network protocol implementations.",
        "An essential aspect of effective fuzzing lies in seed scheduling, which significantly impacts the efficiency and effectiveness of the fuzzing process. Seed scheduling generally comprises two core tasks: seed selection and power allocation. Seed selection determines which inputs from the seed pool should be prioritized for testing, while power allocation assigns computational effort to these selected seeds to maximize test coverage. Unlike CGF, where seed scheduling is typically guided by feedback on code coverage alone, SCGF must also account for the specific states within the network protocol implementation. This necessitates first identifying the target state for testing and then selecting seeds capable of triggering this state. By incorporating protocol state information into the scheduling process, SCGF can more effectively navigate and explore complex state spaces.",
        "Current research on seed scheduling within SCGF primarily focuses on state representation methods. However, regardless of the state representation method used, the seed scheduling methods in network protocol fuzzing face three significant challenges: Challenge 1—Imbalanced Seed Selection Strategy: existing methods tend to repeatedly select a small subset of high-frequency seeds. Challenge 2—Monolithic Seed Selection Strategy: the state-driven approach can filter out numerous potentially valuable seeds in later phases. Challenge 3—Uneven Power Allocation Strategy: power is overly concentrated on specific messages. In this paper, we propose SCFuzz to address these challenges through a multi-phase seed selection strategy based on the multi-armed bandit model and a power allocation strategy based on state weights. We implemented a prototype and evaluated it on five widely used open-source protocol implementations; the results demonstrate that SCFuzz offers significant improvements over AFLNet across multiple metrics.",
    ]),
    ("2. Background", [
        "2.1 CGF. Coverage-based graybox fuzzing (CGF) collects code coverage through instrumentation and uses it to guide the fuzzing process. CGF inserts lightweight instrumentation at critical locations to monitor execution. If a test case triggers a new path or covers previously unexplored code, it is added to the seed pool. Although CGF performs well for stateless programs, it faces many challenges when applied to stateful network protocols, because network protocols are inherently stateful and CGF inadequately handles state information.",
        "2.2 SCGF. Stateful coverage-based graybox fuzzing (SCGF) combines CGF with enhanced state information management. SCGF captures information during execution, infers the server state, and dynamically constructs a state machine to guide fuzzing. The workflow includes: target state selection, message sequence (seed) selection, sequence mutation (e.g. mutating only the infix to maintain target state stability), and execution and feedback collection.",
        "2.3 Multi-Armed Bandit Model. The multi-armed bandit (MAB) model is a classic optimization problem balancing exploration and exploitation. In fuzzing, seed selection bears significant similarity to the MAB problem. The adversarial MAB variant, where reward distributions can change over time, is particularly well suited for seed selection in fuzzing, as seeds can be viewed as arms whose effectiveness tends to diminish as testing progresses.",
    ]),
    ("3. Related Work", [
        "3.1 Protocol Fuzzing. Network protocol fuzzing has evolved from black-box to gray-box fuzzing. Black-box approaches (e.g. Peach, SPIKE) generate test cases from protocol format knowledge but have limited coverage. Graybox protocol fuzzing uses execution feedback to guide test generation. Pham et al. developed AFLNet, the first stateful graybox protocol fuzzer based on AFL. Subsequent work includes SGPFuzzer (message sequence mutation) and SnapFuzz (snapshot technology for throughput).",
        "3.2 Seed Scheduling. Research on seed scheduling in stateful protocol fuzzing has focused on state selection and state representation. Some work uses Monte Carlo Tree Search or models state selection as a multi-armed bandit problem. StateAFL, NSFuzz, and SGFUZZ improve state representation. In traditional coverage-based fuzzing, AFLFast uses a Markov chain model for power allocation; FairFuzz and others allocate power toward rare branches or high-benefit seeds.",
    ]),
    ("4. Methodology", [
        "4.1 Overview. SCFuzz consists of three primary modules: Multi-Phase Seed Selection (using a multi-armed bandit model to balance exploration and exploitation across initial, middle, and final phases), Power Allocation Based on State Weights (allocating power to messages according to state weights), and Mutation and Execution (mutating messages based on allocated power and updating the seed pool from feedback).",
        "4.2 Multi-Phase Seed Selection. The seed selection problem is modeled as an adversarial multi-armed bandit problem. The fuzzing process is divided into three phases based on runtime: initial (emphasis on state exploration, α > 0.5), middle (balance of state and code path coverage, α = 0.5), and final (focus on code path exploration, α < 0.5). In the exploration state of the seed pool, unselected seeds are prioritized; in the exploitation state, the seed with the highest reward probability is selected according to Equation (8).",
        "4.3 Power Allocation Based on State Weights. Global power initialization follows AFLNet-style strategy (execution time, coverage, introduction timing). State evaluation applies heuristic rules to compute state weights (e.g. lower selection frequency, lower trigger frequency, more transition edges, deeper states, and states that have discovered new paths). Fine-grained power allocation distributes seed power to states proportionally by weight, and thus to individual messages.",
    ]),
    ("5. Evaluation", [
        "5.1 Experimental Setup. SCFuzz is developed based on AFLNet. Experiments run on Ubuntu 20.04 with dual Xeon E5-2690 CPUs and 128 GB RAM. Each fuzzer is subjected to 24 h of fuzzing per protocol, repeated five times. The 24 h is divided into initial (6 h, α=0.8), middle (8 h, α=0.5), and final (10 h, α=0.2) phases. Benchmarks include Live555, LightFTP, Pure-FTPD, ProFTPD, and Forked-daapd from ProFuzzBench. Baseline is AFLNet.",
        "5.2 State Coverage (RQ1). SCFuzz achieves an average improvement of 17.10% in the number of states and 22.92% in state transitions within 24 h compared to AFLNet. The Vargha–Delaney effect size indicates SCFuzz has a clear advantage in exploring the state space. Improvements on LightFTP and Forked-daapd are smaller due to simple functionality or slow execution speed.",
        "5.3 Code Coverage (RQ2). SCFuzz achieves higher branch, line, and path coverage across all five implementations: average 7.92% branch, 6.61% line, and 13.00% path improvement. Branch coverage over time shows SCFuzz surpassing AFLNet particularly in later phases.",
        "5.4 Seed Selection Effectiveness (RQ3). The proportion of selected seeds that received rewards (discovered new code or state coverage) is 27.45% for SCFuzz vs 9.86% for AFLNet on average, representing a 389.37% improvement.",
        "5.5 Power Utilization Effectiveness (RQ4). SCFuzz achieves 0.54% power utilization effectiveness on average vs 0.37% for AFLNet, a 45.61% improvement.",
    ]),
    ("6. Discussion", [
        "SCFuzz still has certain limitations. First, phase durations are currently fixed at the start of fuzzing; they may not be universally applicable across all protocol implementations. Developing adaptive phase durations based on real-time feedback (e.g. state discovery and transition rates) is a promising direction. Secondly, seed scheduling and seed mutation are interdependent; optimizing both in an integrated manner could further improve performance. Future work may explore adaptive phase management and deeper integration of scheduling with mutation strategies.",
    ]),
    ("7. Conclusions", [
        "In this paper, we present SCFuzz, an approach to optimize seed scheduling in network protocol fuzzing. By modeling seed selection as a multi-armed bandit problem and partitioning the fuzzing process into distinct phases, SCFuzz dynamically balances exploration and exploitation. A power allocation strategy based on state weights ensures focused resource distribution. Experimental results show that SCFuzz achieves up to 17.10% more states, 22.92% more state transitions, and 7.92% higher code branch coverage than AFLNet; seed selection effectiveness improves by 389.37% and power utilization by 45.61%. SCFuzz contributes to both the scientific understanding of fuzzing strategies and the practical security of communication protocols. Future work may explore adaptive phase management and the integration of seed scheduling with mutation strategies.",
    ]),
]

# 中文译文：与 EN_SECTIONS 一一对应
CN_SECTIONS = [
    ("摘要", [
        "在网络协议模糊测试中，有效的种子调度对提高测试效率起着关键作用。传统的基于状态驱动的网络协议模糊测试种子调度方法往往受限于种子选择不平衡、调度策略单一以及功率分配不当。为克服这些局限，本文提出 SCFuzz，通过采用多臂老虎机模型在多阶段模糊测试过程中动态平衡探索与利用。将模糊测试过程划分为初始、中期和最终三个阶段，并在各阶段采用相适应的种子选择策略，以优化对新状态、路径与代码覆盖的发现。此外，SCFuzz 采用基于状态权重的功率分配方法，将计算资源集中于高潜力消息，以提升整体模糊测试效率。在开源协议实现上的实验表明，与 AFLNet 相比，SCFuzz 在状态与代码覆盖上均有显著提升：状态数最多增加 17.10%，状态转移提高 22.92%，代码分支覆盖提高 7.92%；种子选择有效性平均提升 389.37%，功率利用有效性提高 45.61%，有效提升了模糊测试的整体效率。",
    ]),
    ("1. 引言", [
        "模糊测试是一种应用广泛、效果显著的软件测试技术，其特点在于自动化程度高、适用面广，且在发现软件漏洞方面已被证明有效。从本质上讲，模糊测试通过迭代过程进行：从初始种子池中选取输入种子，经变异生成多样化测试用例，再在目标软件上执行这些用例。",
        "近年来，模糊测试研究主要集中在基于覆盖率的灰盒模糊测试（CGF）上，其通过利用代码覆盖率反馈提高测试效率。在 CGF 的基础上，研究者将相关技术扩展到网络协议测试领域，形成了基于状态与覆盖的灰盒模糊测试（SCGF）。SCGF 不仅依赖代码覆盖信息，还融合从网络协议实现中提取的状态信息，从而能够管理复杂的协议状态转移与依赖关系，为发现网络协议实现中的漏洞提供更精细、更有效的方法。",
        "有效模糊测试的一个重要方面在于种子调度，其显著影响模糊测试的效率与效果。种子调度通常包含两个核心任务：种子选择与功率分配。种子选择决定应从种子池中优先选取哪些输入进行测试，功率分配则为所选种子分配计算资源以最大化测试覆盖。与仅依靠代码覆盖反馈指导种子调度的 CGF 不同，SCGF 还需考虑网络协议实现中的具体状态，即先确定待测目标状态，再选择能触发该状态的种子。通过将协议状态信息纳入调度过程，SCGF 能更有效地遍历与探索复杂状态空间。",
        "当前针对 SCGF 中种子调度的研究主要集中在状态表示方法上。然而，无论采用何种状态表示，网络协议模糊测试中的种子调度方法均面临三大挑战：挑战一——种子选择策略不平衡，现有方法倾向于反复选择少数高频种子；挑战二——种子选择策略单一，在后期阶段基于状态的驱动会筛掉大量潜在有价值种子；挑战三——功率分配不均，资源过度集中于特定消息。本文提出的 SCFuzz 通过基于多臂老虎机模型的多阶段种子选择策略与基于状态权重的功率分配策略应对上述挑战。我们在五种广泛使用的开源协议实现上实现了原型并进行了评估，实验结果表明 SCFuzz 在多项指标上较 AFLNet 均有显著提升。",
    ]),
    ("2. 背景", [
        "2.1 CGF。基于覆盖率的灰盒模糊测试（CGF）通过插桩收集代码覆盖并用以引导模糊测试过程。CGF 在关键位置插入轻量级插桩以监控执行；若某测试用例触发新路径或覆盖此前未探索的代码，则将其加入种子池。CGF 对无状态程序效果良好，但应用于有状态网络协议时面临诸多挑战，因为网络协议本身具有状态性，而 CGF 对状态信息处理不足。",
        "2.2 SCGF。基于状态与覆盖的灰盒模糊测试（SCGF）将 CGF 与增强的状态信息管理相结合。SCGF 在执行过程中捕获信息、推断服务器状态并动态构建状态机以指导模糊测试。其工作流程包括：目标状态选择、消息序列（种子）选择、序列变异（例如仅变异中缀以保持目标状态稳定）以及执行与反馈收集。",
        "2.3 多臂老虎机模型。多臂老虎机（MAB）模型是一类在探索与利用之间取得平衡的经典优化问题。在模糊测试中，种子选择与 MAB 问题具有明显相似性。对抗式多臂老虎机变体允许奖励分布随时间变化，特别适合模糊测试中的种子选择，因为种子可视为“臂”，其有效性随测试进行往往逐渐下降。",
    ]),
    ("3. 相关工作", [
        "3.1 协议模糊测试。网络协议模糊测试经历了从黑盒到灰盒的发展。黑盒方法（如 Peach、SPIKE）根据协议格式知识生成测试用例，但覆盖有限。灰盒协议模糊测试利用执行反馈指导测试生成。Pham 等人基于 AFL 开发了首个有状态灰盒协议模糊测试工具 AFLNet。后续工作包括 SGPFuzzer（消息序列变异）和 SnapFuzz（利用快照技术提高吞吐）。",
        "3.2 种子调度。有状态协议模糊测试中种子调度的研究主要集中在状态选择与状态表示上。部分工作采用蒙特卡洛树搜索或将状态选择建模为多臂老虎机问题。StateAFL、NSFuzz 和 SGFUZZ 改进了状态表示。在传统基于覆盖的模糊测试中，AFLFast 使用马尔可夫链模型进行功率分配；FairFuzz 等方法将功率分配给稀有分支或高收益种子。",
    ]),
    ("4. 方法", [
        "4.1 概述。SCFuzz 由三个主要模块组成：多阶段种子选择（在初始、中期与最终阶段使用多臂老虎机模型平衡探索与利用）、基于状态权重的功率分配（按状态权重将功率分配给各消息）、以及变异与执行（根据分配功率对消息变异并根据反馈更新种子池）。",
        "4.2 多阶段种子选择。种子选择问题被建模为对抗式多臂老虎机问题。模糊测试过程按运行时间划分为三阶段：初始阶段（侧重状态探索，α > 0.5）、中期阶段（平衡状态与代码路径覆盖，α = 0.5）、最终阶段（侧重代码路径探索，α < 0.5）。在种子池处于探索状态时优先选择未选种子；在利用状态时按式(8)选择奖励概率最高的种子。",
        "4.3 基于状态权重的功率分配。全局功率初始化采用类 AFLNet 策略（执行时间、覆盖率、引入时机）。状态评估通过启发式规则计算状态权重（如选择频率低、触发频率低、转移边多、状态更深、以及曾多次发现新路径的状态）。细粒度功率分配按权重将种子功率按比例分配给各状态，进而分配给各消息。",
    ]),
    ("5. 实验评估", [
        "5.1 实验设置。SCFuzz 基于 AFLNet 开发。实验在 Ubuntu 20.04、双路 Xeon E5-2690、128 GB 内存上进行。每种模糊器对每个协议进行 24 小时模糊测试，重复 5 次。24 小时划分为初始（6 小时，α=0.8）、中期（8 小时，α=0.5）、最终（10 小时，α=0.2）三阶段。基准包括 ProFuzzBench 中的 Live555、LightFTP、Pure-FTPD、ProFTPD 和 Forked-daapd。基线为 AFLNet。",
        "5.2 状态覆盖（RQ1）。与 AFLNet 相比，SCFuzz 在 24 小时内状态数平均提高 17.10%，状态转移平均提高 22.92%。Vargha–Delaney 效应量表明 SCFuzz 在探索状态空间上具有明显优势。在 LightFTP 和 Forked-daapd 上提升较小，原因分别为功能较简单或执行速度较慢。",
        "5.3 代码覆盖（RQ2）。SCFuzz 在五种实现上均获得更高的分支、行与路径覆盖：分支平均提高 7.92%，行覆盖 6.61%，路径覆盖 13.00%。随时间的分支覆盖表明 SCFuzz 尤其在后期阶段超过 AFLNet。",
        "5.4 种子选择有效性（RQ3）。获得奖励（发现新代码或状态覆盖）的种子占所选种子的比例，SCFuzz 平均为 27.45%，AFLNet 为 9.86%，即提升 389.37%。",
        "5.5 功率利用有效性（RQ4）。SCFuzz 平均功率利用有效性为 0.54%，AFLNet 为 0.37%，提升 45.61%。",
    ]),
    ("6. 讨论", [
        "SCFuzz 仍存在一定局限。首先，阶段时长目前在模糊测试开始时固定，可能并非对所有协议实现都适用；基于实时反馈（如状态发现率与转移率）的自适应阶段时长是值得探索的方向。其次，种子调度与种子变异相互依赖；将二者一体化优化有望进一步提升性能。未来工作可探索自适应阶段管理与调度同变异策略的深度融合。",
    ]),
    ("7. 结论", [
        "本文提出 SCFuzz，用于优化网络协议模糊测试中的种子调度。通过将种子选择建模为多臂老虎机问题并将模糊测试过程划分为不同阶段，SCFuzz 动态平衡探索与利用；基于状态权重的功率分配策略保证了资源集中分配。实验结果表明，与 AFLNet 相比，SCFuzz 在状态数上最多提高 17.10%，状态转移提高 22.92%，代码分支覆盖提高 7.92%；种子选择有效性提高 389.37%，功率利用提高 45.61%。SCFuzz 对模糊测试策略的科学理解与通信协议的实际安全均具有贡献。未来工作可探索自适应阶段管理以及种子调度与变异策略的结合。",
    ]),
]

# 文献头信息
EN_TITLE = "Reinforcement Learning-Based Multi-Phase Seed Scheduling for Network Protocol Fuzzing"
EN_AUTHORS = "Mingjie Cheng, Kailong Zhu, Yuanchao Chen, Yuliang Lu, Chiyu Chen, Jiayi Yu\nCollege of Electronic Engineering, National University of Defense Technology, Hefei 230037, China"
EN_SOURCE = "Electronics 2024, 13(24), 4962; https://doi.org/10.3390/electronics13244962"

CN_TITLE = "基于强化学习的网络协议模糊测试多阶段种子调度"
CN_AUTHORS = "程明杰，朱凯龙，陈元超，卢宇亮，陈驰宇，余嘉义\n国防科技大学电子对抗学院，合肥 230037"
CN_SOURCE = "Electronics 2024, 13(24), 4962; https://doi.org/10.3390/electronics13244962"
