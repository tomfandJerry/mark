#!/usr/bin/env python3
"""IoT Firmware Fuzzer - 命令行入口"""
import os
import sys
import click
import logging
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option("1.0.0", prog_name="IoTFirmwareFuzzer")
def cli():
    """面向 IoT 固件协议的自动化灰盒模糊测试工具。

常规用法:

  python main.py -h
    显示本帮助及常规用法。

  python main.py ui
    启动 Web 界面（推荐），在浏览器中配置并运行测试。

  python main.py fuzz --no-qemu -p mqtt -t 60
    存根模式运行 60 秒（不连真实目标，用于体验流程）。

  python main.py seed mqtt -n 20
    生成 20 个 MQTT 协议种子到 ./seeds/mqtt/。

  python main.py fuzz -b /path/to/目标程序 -p mqtt -t 3600
    对指定二进制进行模糊测试，运行 1 小时。

  python main.py fuzz -f 固件.bin -a arm -p mqtt
    自动解包固件并对其中目标程序进行测试。

  python main.py info
    查看当前配置文件中的协议、架构、输出目录等。

  python main.py <命令> -h
    查看该命令的详细选项说明（如 fuzz -h、seed -h、ui -h）。
"""
    pass

VALID_ARCH = ["arm", "mips", "mipsel", "aarch64", "x86", "x86_64"]
VALID_PROTOCOL = ["mqtt", "coap", "http"]

@cli.command("fuzz")
@click.option("-c", "--config", default="./config/default_config.yaml", help="配置文件")
@click.option("-f", "--firmware", default="", help="固件路径")
@click.option("-b", "--binary", default="", help="目标二进制")
@click.option("-p", "--protocol", default=None, help="协议: mqtt/coap/http，不填则用配置文件")
@click.option("-a", "--arch", default=None, help="架构: arm/mips/mipsel/aarch64/x86/x86_64，不填则用配置文件")
@click.option("-t", "--timeout", default=0, type=int, help="运行秒数，0=无限")
@click.option("-o", "--output", default="")
@click.option("--no-rl", is_flag=True, help="禁用RL")
@click.option("--no-qemu", is_flag=True, help="存根执行（不启动QEMU）")
def fuzz(config, firmware, binary, protocol, arch, timeout, output, no_rl, no_qemu):
    """启动模糊测试"""
    if protocol is not None and protocol not in VALID_PROTOCOL:
        raise click.BadParameter(f"protocol 须为 {VALID_PROTOCOL} 之一")
    if arch is not None and arch not in VALID_ARCH:
        raise click.BadParameter(f"arch 须为 {VALID_ARCH} 之一")
    cfg = yaml.safe_load(open(config, "r", encoding="utf-8")) if os.path.exists(config) else {}
    if protocol: cfg.setdefault("protocol", {})["name"] = protocol
    if arch: cfg.setdefault("emulation", {})["architecture"] = arch
    if output: cfg.setdefault("fuzzer", {})["output_dir"] = output
    if no_rl: cfg.setdefault("expert", {})["rl_enabled"] = False
    if no_qemu: cfg.setdefault("firmware", {})["target_binary"] = ""
    import tempfile
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    yaml.dump(cfg, tmp, allow_unicode=True)
    tmp.close()
    from src.core.fuzzer import IoTFirmwareFuzzer
    f = IoTFirmwareFuzzer(config_path=tmp.name)
    os.unlink(tmp.name)
    f.run(firmware_path=firmware, target_binary=binary, timeout_secs=timeout)

@cli.command("seed")
@click.argument("protocol", type=click.Choice(["mqtt", "coap", "http"]))
@click.option("-o", "--output", default="./seeds")
@click.option("-n", "--count", default=10)
def seed(protocol, output, count):
    """生成初始种子"""
    import struct
    seeds = []
    if protocol == "mqtt":
        for i in range(count):
            cid = f"client_{i}".encode()
            var = b"\x00\x04MQTT\x04\x02" + struct.pack(">H", 60)
            payload = struct.pack(">H", len(cid)) + cid
            seeds.append(b"\x10" + bytes([len(var + payload)]) + var + payload)
        seeds.append(b"\xc0\x00")
    elif protocol == "http":
        for i in range(count):
            seeds.append("GET / HTTP/1.1\r\nHost: localhost\r\n\r\n".encode())
    pdir = os.path.join(output, protocol)
    os.makedirs(pdir, exist_ok=True)
    for i, s in enumerate(seeds[:count]):
        open(os.path.join(pdir, f"seed_{i:04d}.bin"), "wb").write(s)
    click.echo(f"已生成 {min(len(seeds), count)} 个种子 -> {pdir}")

@cli.command("info")
@click.option("-c", "--config", default="./config/default_config.yaml")
def info(config):
    """显示配置"""
    if os.path.exists(config):
        cfg = yaml.safe_load(open(config, "r", encoding="utf-8"))
        click.echo(f"协议: {cfg.get('protocol',{}).get('name')} 架构: {cfg.get('emulation',{}).get('architecture')} 输出: {cfg.get('fuzzer',{}).get('output_dir')}")
    else:
        click.echo("配置文件不存在")

@cli.command("ui")
@click.option("--port", default=5000, type=int, help="Web UI 端口")
@click.option("--no-browser", is_flag=True, help="不自动打开浏览器")
def ui(port, no_browser):
    """启动 Web 界面（在浏览器中配置并运行模糊测试）"""
    import webbrowser
    url = f"http://127.0.0.1:{port}"
    click.echo(f"Web UI 启动后请在浏览器打开: {url}")
    if not no_browser:
        def open_later():
            import time
            time.sleep(1.2)
            webbrowser.open(url)
        import threading
        threading.Thread(target=open_later, daemon=True).start()
    from web_ui import app
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

if __name__ == "__main__":
    cli()
