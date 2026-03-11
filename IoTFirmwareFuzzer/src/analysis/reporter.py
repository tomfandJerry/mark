"""报告生成器 - HTML/JSON/Markdown，中文友好、突出报错位置"""
import os
import json
from datetime import datetime
from typing import Dict, List

from .crash_analyzer import CrashRecord, CrashType, Exploitability
from ..utils import safe_mkdir, format_duration


def _exploit_cn(e: Exploitability) -> str:
    return e.value if isinstance(e.value, str) and any(c in e.value for c in "高中低") else {
        "HIGH": "高（可能被利用）",
        "MEDIUM": "中（需进一步分析）",
        "LOW": "低（难以利用）",
        "UNKNOWN": "未知",
    }.get(e.value, str(e.value))


def _crash_type_cn(c: CrashRecord) -> str:
    return c.crash_type.value


def _location_hint(pc: int, backtrace: List[str]) -> str:
    """生成「如何定位到代码」的简短说明"""
    parts = []
    if pc and pc != 0:
        parts.append(f"程序崩溃时指令地址（PC）为 0x{pc:08x}。")
        parts.append("在目标程序所在目录执行：addr2line -e <目标程序> -f 0x%08x 可反推出对应的源码文件名与行号（需带调试信息编译）。" % pc)
    if backtrace:
        parts.append("调用栈（从下往上为调用顺序，最顶一帧通常为崩溃发生处）：")
    return " ".join(parts)


class Reporter:
    def __init__(self, output_dir: str = "./output"):
        self.report_dir = os.path.join(output_dir, "reports")
        safe_mkdir(self.report_dir)

    def generate(self, stats: Dict, crashes: List[CrashRecord], config: Dict = None, format: str = "html") -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fpath = os.path.join(self.report_dir, f"report_{ts}.{format}")
        if format == "html":
            content = self._gen_html(stats, crashes, config)
        elif format == "json":
            content = json.dumps({
                "stats": stats,
                "crashes": [{"id": c.id, "type": _crash_type_cn(c), "exploitability": _exploit_cn(c.exploitability),
                             "pc": f"0x{c.pc_at_crash:08x}", "backtrace": c.backtrace} for c in crashes],
                "config": config or {}
            }, indent=2, ensure_ascii=False)
        else:
            content = f"# 模糊测试报告\n\n唯一崩溃数: {len(crashes)}\n统计: {stats}\n"
        open(fpath, "w", encoding="utf-8").write(content)
        return fpath

    def _gen_html(self, stats: Dict, crashes: List[CrashRecord], config: Dict) -> str:
        fuzzer = stats.get("fuzzer", {})
        cov = stats.get("coverage", {})
        crash_s = stats.get("crashes", {})
        gen_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

        # 测试概览（全中文）
        overview = f"""
        <div class="card overview">
          <h2>一、测试概览</h2>
          <ul class="stat-list">
            <li><span class="label">总执行次数</span><span class="value">{fuzzer.get('total_execs', 0):,}</span></li>
            <li><span class="label">唯一崩溃数</span><span class="value danger">{crash_s.get('unique_crashes', 0)}</span></li>
            <li><span class="label">高危崩溃数</span><span class="value danger">{crash_s.get('high_severity', 0)}</span></li>
            <li><span class="label">代码覆盖率</span><span class="value">{cov.get('coverage_pct', '0%')}</span></li>
            <li><span class="label">语料库大小</span><span class="value">{fuzzer.get('corpus_size', 0)}</span></li>
            <li><span class="label">运行时长</span><span class="value">{format_duration(fuzzer.get('elapsed_secs', 0))}</span></li>
          </ul>
          <p class="meta">报告生成时间：{gen_time}</p>
        </div>
        """

        # 崩溃详情：每个崩溃一块，突出「报错在程序的哪块」
        crash_blocks = []
        for i, c in enumerate(crashes, 1):
            loc_hint = _location_hint(c.pc_at_crash, c.backtrace)
            bt_html = ""
            if c.backtrace:
                bt_html = "<ul class=\"backtrace\">" + "".join(f"<li><code>{line}</code></li>" for line in c.backtrace[:15]) + "</ul>"
            else:
                bt_html = "<p class=\"no-bt\">（无调用栈信息，可用 GDB 挂载目标程序复现后执行 <code>bt</code> 获取）</p>"

            notes_html = ""
            if c.analysis_notes:
                notes_html = "<p class=\"notes\">分析建议：" + "；".join(c.analysis_notes) + "</p>"
            input_name = os.path.basename(c.input_path) if c.input_path else "—"
            crash_blocks.append(f"""
        <div class="card crash-card">
          <h2>崩溃 #{i}：{_crash_type_cn(c)}</h2>
          <table class="info-table">
            <tr><td class="label">崩溃编号</td><td>{c.id}</td></tr>
            <tr><td class="label">严重程度</td><td class="exploit-{c.exploitability.name.lower()}">{_exploit_cn(c.exploitability)}</td></tr>
            <tr><td class="label">程序计数器（PC）</td><td><code>0x{c.pc_at_crash:08x}</code> <span class="hint">崩溃时 CPU 执行到的指令地址</span></td></tr>
            <tr><td class="label">触发输入文件</td><td><code>{input_name}</code>（位于 output/crashes/ 目录）</td></tr>
          </table>
          <div class="location-block">
            <h3>报错在程序的哪块？</h3>
            <p class="hint-text">{loc_hint}</p>
            <h4>调用栈（从上往下为从内到外）</h4>
            {bt_html}
            {notes_html}
          </div>
        </div>
            """)

        crashes_section = "".join(crash_blocks) if crash_blocks else '<div class="card"><h2>二、崩溃详情</h2><p class="empty">本次测试未发现崩溃。</p></div>'
        intro_card = '<div class="card"><h2>二、崩溃详情</h2><p class="intro">以下列出每个唯一崩溃的类型、严重程度及<strong>程序中的报错位置</strong>（PC 与调用栈）。根据 PC 或调用栈最顶帧，用 <code>addr2line -e 目标程序 -f &lt;地址&gt;</code> 或 GDB 即可对应到源码位置。</p></div>'

        # 简单的时间-崩溃数“趋势表”，方便老师肉眼看出走势
        timeline_rows = ""
        tl = stats.get("timeline") or []
        if tl:
            # 采样最多 10 个点：首尾必含，中间均匀抽样
            points = []
            n = len(tl)
            if n <= 10:
                points = tl
            else:
                idxs = {0, n - 1}
                step = max(1, n // 8)
                for i in range(step, n - 1, step):
                    idxs.add(i)
                for i in sorted(list(idxs))[:10]:
                    points.append(tl[i])
            timeline_rows = "".join(
                f"<tr><td>{p.get('time', 0):.1f}</td><td>{p.get('execs', 0)}</td><td>{p.get('crashes', 0)}</td><td>{p.get('corpus_size', 0)}</td></tr>"
                for p in points
            )

        if timeline_rows:
            timeline_block = (
                '<table class="timeline-table">'
                '<thead><tr><th>时间(秒)</th><th>执行次数</th><th>唯一崩溃</th><th>语料库大小</th></tr></thead>'
                '<tbody>' + timeline_rows + '</tbody></table>'
            )
        else:
            timeline_block = '<p class="empty">（时间线数据不足，未生成趋势表。）</p>'

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>模糊测试报告 - IoT Firmware Fuzzer</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: "Segoe UI", "Microsoft YaHei", sans-serif; background: #0d1117; color: #e6edf3; line-height: 1.6; padding: 24px; }}
    .container {{ max-width: 900px; margin: 0 auto; }}
    h1 {{ font-size: 1.5rem; color: #58a6ff; margin-bottom: 8px; }}
    .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 20px; margin-bottom: 20px; }}
    .card h2 {{ font-size: 1.1rem; color: #79c0ff; margin-bottom: 12px; border-bottom: 1px solid #21262d; padding-bottom: 8px; }}
    .card h3 {{ font-size: 1rem; color: #d2a8ff; margin: 16px 0 8px; }}
    .card h4 {{ font-size: 0.95rem; color: #a1a1aa; margin: 12px 0 6px; }}
    .stat-list {{ list-style: none; display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }}
    .stat-list .label {{ color: #8b949e; display: block; font-size: 0.9rem; }}
    .stat-list .value {{ font-size: 1.4rem; font-weight: 600; color: #58a6ff; }}
    .stat-list .value.danger {{ color: #f85149; }}
    .meta {{ color: #8b949e; font-size: 0.85rem; margin-top: 12px; }}
    .info-table {{ width: 100%; border-collapse: collapse; margin: 8px 0; }}
    .info-table td {{ padding: 8px 12px; border-bottom: 1px solid #21262d; vertical-align: top; }}
    .info-table .label {{ color: #8b949e; width: 160px; }}
    .location-block {{ background: #0d1117; border-radius: 8px; padding: 14px; margin-top: 12px; border: 1px solid #21262d; }}
    .hint-text {{ color: #8b949e; font-size: 0.9rem; margin-bottom: 10px; }}
    .hint {{ color: #6e7681; font-size: 0.85rem; margin-left: 8px; }}
    .backtrace {{ margin: 8px 0; padding-left: 20px; font-family: Consolas, monospace; font-size: 0.85rem; color: #e6edf3; }}
    .backtrace li {{ margin: 4px 0; }}
    .backtrace code {{ color: #a5d6ff; }}
    .no-bt {{ color: #8b949e; font-size: 0.9rem; }}
    .notes {{ color: #fbbf24; font-size: 0.9rem; margin-top: 10px; }}
    .exploit-high {{ color: #f85149; font-weight: 600; }}
    .exploit-medium {{ color: #d29922; }}
    .exploit-low {{ color: #58a6ff; }}
    .empty {{ color: #8b949e; }}
    .intro {{ color: #c9d1d9; margin-bottom: 0; }}
    .config-pre {{ background: #0d1117; padding: 12px; border-radius: 6px; font-size: 0.85rem; overflow-x: auto; color: #8b949e; border: 1px solid #21262d; }}
    .timeline-table {{ width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 0.85rem; }}
    .timeline-table th, .timeline-table td {{ padding: 6px 8px; border-bottom: 1px solid #21262d; text-align: left; }}
    .timeline-table th {{ color: #8b949e; }}
    code {{ background: #21262d; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>IoT Firmware Fuzzer 模糊测试报告</h1>
    <p class="meta" style="margin-bottom:20px;">本报告除数字与地址外均使用中文，便于快速找到程序中的报错位置。</p>
    {overview}
    <div class="card">
      <h2>二、执行趋势（抽样）</h2>
      <p class="intro">下表按时间抽样展示执行次数与崩溃数变化趋势，便于直观判断模糊测试是否仍在带来新行为。</p>
      {timeline_block}
    </div>
    {intro_card}
    {crashes_section}
    <div class="card">
      <h2>三、配置摘要</h2>
      <pre class="config-pre">{json.dumps(config or {}, indent=2, ensure_ascii=False)}</pre>
    </div>
  </div>
</body>
</html>
"""
        return html
