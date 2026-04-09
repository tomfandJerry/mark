#!/usr/bin/env python3
"""
IoT Firmware Fuzzer - Web UI 入口
在浏览器中配置参数、启动/停止测试、查看实时状态与日志。
"""
import os
import sys
import time
import tempfile
import threading
import logging
import subprocess
import shlex
from collections import deque

# 确保项目根在 path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static", template_folder="templates")

# 全局状态
LOG_MAX = 500
log_buffer = deque(maxlen=LOG_MAX)
device_log_buffer = deque(maxlen=LOG_MAX)
current_fuzzer = None
current_thread = None
running = False
current_timeout_secs = 0  # 本次运行的超时设置，用于前端倒计时
last_report_path = None
config_path = os.path.join(os.path.dirname(__file__), "config", "default_config.yaml")

# 设备（QEMU）进程状态
device_process = None
device_lock = threading.Lock()
device_command = ""
device_last_config = {}
device_mode = "user"
device_last_error = ""


def _ts():
    return time.strftime("%H:%M:%S")


def _log_device(msg: str):
    device_log_buffer.append({"t": _ts(), "msg": msg})


class BufferHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            log_buffer.append({"t": time.strftime("%H:%M:%S", time.localtime(record.created)), "msg": msg})
        except Exception:
            pass


def get_fuzzer_stats():
    """从当前 fuzzer 实例读取统计（线程安全读）"""
    if current_fuzzer is None:
        return None
    try:
        s = current_fuzzer._stats
        corpus_size = len(current_fuzzer.seed_mgr.seeds)
        return {
            "total_execs": s.total_execs,
            "unique_crashes": s.unique_crashes,
            "execs_per_sec": round(s.execs_per_sec, 1),
            "elapsed_secs": round(s.elapsed_secs, 1),
            "corpus_size": corpus_size,
        }
    except Exception:
        return None


def _load_cfg():
    return yaml.safe_load(open(config_path, "r", encoding="utf-8")) if os.path.exists(config_path) else {}


def _build_qemu_user_command(data: dict):
    cfg = _load_cfg()
    emu_cfg = cfg.get("emulation", {})
    firmware_cfg = cfg.get("firmware", {})
    demo_shell = bool(data.get("demo_shell", False))

    if demo_shell:
        if os.name == "nt":
            shell_bin = os.environ.get("COMSPEC", "cmd.exe")
        else:
            shell_bin = os.environ.get("SHELL", "/bin/bash")
        return [shell_bin], {
            "arch": "host",
            "root_fs": "",
            "gdb_port": 0,
            "binary": shell_bin,
            "mode": "demo-shell",
            "demo_shell": True,
        }

    arch = (data.get("arch") or emu_cfg.get("architecture") or "arm").strip()
    qemu_user_path = (data.get("qemu_user_path") or emu_cfg.get("qemu_user_path") or "").strip()
    qemu_bin_default = {
        "arm": "qemu-arm",
        "mips": "qemu-mips",
        "mipsel": "qemu-mipsel",
        "aarch64": "qemu-aarch64",
        "x86": "qemu-i386",
        "x86_64": "qemu-x86_64",
    }.get(arch, "qemu-arm")
    qemu_bin = qemu_user_path or qemu_bin_default

    root_fs = (data.get("root_fs") or firmware_cfg.get("root_fs") or "").strip()
    gdb_port = int(data.get("gdb_port") or emu_cfg.get("debug_port") or 1234)
    binary = (data.get("binary") or firmware_cfg.get("target_binary") or "").strip()

    mode = "system" if "qemu-system" in os.path.basename(qemu_bin).lower() else "user"
    cmd = [qemu_bin]
    if mode == "user":
        if root_fs:
            cmd += ["-L", root_fs]
        cmd += ["-g", str(gdb_port)]
        if binary:
            cmd.append(binary)
    else:
        cmd += ["-M", "virt", "-cpu", "cortex-a15", "-m", "256M", "-nographic", "-S"]
    return cmd, {"arch": arch, "root_fs": root_fs, "gdb_port": gdb_port, "binary": binary, "mode": mode, "demo_shell": False}


def _reader_thread(proc: subprocess.Popen):
    global device_process
    try:
        while True:
            line = proc.stdout.readline() if proc.stdout else ""
            if not line:
                break
            _log_device(line.rstrip("\r\n"))
    except Exception as e:
        _log_device(f"[device] 读取输出异常: {e}")
    finally:
        code = proc.poll()
        _log_device(f"[device] 进程已退出，exit_code={code}")
        with device_lock:
            if device_process is proc:
                device_process = None


def _start_device(data: dict):
    global device_process, device_command, device_last_config, device_mode, device_last_error
    with device_lock:
        if device_process and device_process.poll() is None:
            raise RuntimeError("设备已在运行中")

        cmd, resolved = _build_qemu_user_command(data)
        if resolved["mode"] == "user":
            if len(cmd) <= 3:
                raise RuntimeError("缺少目标二进制，请填写设备页中的「目标二进制路径」")
            if not os.path.isfile(resolved["binary"]):
                raise RuntimeError(f"目标二进制不存在: {resolved['binary']}")

        device_command = " ".join(shlex.quote(x) for x in cmd)
        device_mode = resolved["mode"]
        device_last_error = ""
        device_last_config = {
            "qemu_user_path": data.get("qemu_user_path", ""),
            "arch": resolved["arch"],
            "root_fs": resolved["root_fs"],
            "gdb_port": resolved["gdb_port"],
            "binary": resolved["binary"],
            "mode": resolved["mode"],
            "demo_shell": resolved.get("demo_shell", False),
        }
        device_log_buffer.clear()
        _log_device(f"[device] 启动命令: {device_command}")
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        device_process = proc
        _log_device(f"[device] 进程已启动，pid={proc.pid}")
        threading.Thread(target=_reader_thread, args=(proc,), daemon=True).start()
        return proc.pid


def _stop_device():
    global device_process
    with device_lock:
        if not device_process or device_process.poll() is not None:
            device_process = None
            return False
        proc = device_process
        try:
            proc.terminate()
            proc.wait(timeout=5)
            _log_device("[device] 已停止设备进程")
        except Exception:
            try:
                proc.kill()
                _log_device("[device] terminate 失败，已强制 kill")
            except Exception:
                pass
        finally:
            device_process = None
        return True


def run_fuzzer_async(config_path: str, firmware_path: str, target_binary: str, timeout_secs: int):
    global current_fuzzer, running, last_report_path
    try:
        from src.core.fuzzer import IoTFirmwareFuzzer
        f = IoTFirmwareFuzzer(config_path=config_path)
        current_fuzzer = f
        f.run(firmware_path=firmware_path, target_binary=target_binary, timeout_secs=timeout_secs)
        last_report_path = os.path.join(f.output_dir, "reports")
    except Exception as e:
        log_buffer.append({"t": time.strftime("%H:%M:%S"), "msg": f"运行错误: {e}"})
    finally:
        running = False
        current_fuzzer = None


@app.route("/")
def index():
    return send_from_directory(os.path.join(os.path.dirname(__file__), "templates"), "landing.html")


@app.route("/console")
def console():
    return send_from_directory(os.path.join(os.path.dirname(__file__), "templates"), "index.html")


@app.route("/api/status")
def api_status():
    stats = get_fuzzer_stats() if current_fuzzer else None
    logs = list(log_buffer)
    # 最新报告
    report_dir = os.path.join(os.path.dirname(__file__), "output", "reports")
    latest_report = None
    if os.path.isdir(report_dir):
        files = [f for f in os.listdir(report_dir) if f.endswith(".html")]
        if files:
            latest_report = sorted(files)[-1]
    # 最近崩溃列表（最多 10 条）
    recent_crashes = []
    if current_fuzzer is not None:
        try:
            crashes = current_fuzzer.crash_analyzer.get_crashes(unique_only=True)[-10:]
            recent_crashes = [{"id": c.id, "type": c.crash_type.value, "exploit": c.exploitability.name, "exploit_label": c.exploitability.value} for c in reversed(crashes)]
        except Exception:
            pass

    with device_lock:
        dproc = device_process
        device_running = bool(dproc and dproc.poll() is None)
        device_pid = dproc.pid if device_running else None

    return jsonify({
        "running": running,
        "stats": stats,
        "timeout_secs": current_timeout_secs,
        "log": logs[-200:],
        "latest_report": latest_report,
        "recent_crashes": recent_crashes,
        "device": {
            "running": device_running,
            "pid": device_pid,
            "command": device_command,
            "mode": device_mode,
            "last_error": device_last_error,
            "log": list(device_log_buffer)[-200:],
            "config": device_last_config,
        },
    })


@app.route("/api/device/command", methods=["POST"])
def api_device_command():
    data = request.get_json() or {}
    cmd, resolved = _build_qemu_user_command(data)
    cmd_text = " ".join(shlex.quote(x) for x in cmd)
    return jsonify({"ok": True, "command": cmd_text, "resolved": resolved, "mode": resolved.get("mode", "user")})


@app.route("/api/device/start", methods=["POST"])
def api_device_start():
    global device_last_error
    data = request.get_json() or {}
    try:
        pid = _start_device(data)
        return jsonify({"ok": True, "pid": pid, "command": device_command})
    except Exception as e:
        device_last_error = str(e)
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/device/stop", methods=["POST"])
def api_device_stop():
    stopped = _stop_device()
    return jsonify({"ok": True, "stopped": stopped})


@app.route("/api/device/restart", methods=["POST"])
def api_device_restart():
    global device_last_error
    data = request.get_json() or device_last_config
    _stop_device()
    try:
        pid = _start_device(data)
        return jsonify({"ok": True, "pid": pid, "command": device_command})
    except Exception as e:
        device_last_error = str(e)
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/device/send", methods=["POST"])
def api_device_send():
    data = request.get_json() or {}
    cmd = (data.get("command") or "").rstrip("\n")
    if not cmd:
        return jsonify({"ok": False, "error": "命令不能为空"}), 400
    with device_lock:
        proc = device_process
    if not proc or proc.poll() is not None:
        return jsonify({"ok": False, "error": "设备未运行"}), 400
    try:
        if proc.stdin is None:
            return jsonify({"ok": False, "error": "当前设备进程不支持交互输入"}), 400
        proc.stdin.write(cmd + "\n")
        proc.stdin.flush()
        _log_device(f"> {cmd}")
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/device/clear-logs", methods=["POST"])
def api_device_clear_logs():
    device_log_buffer.clear()
    _log_device("[device] 日志已清空")
    return jsonify({"ok": True})


@app.route("/api/start", methods=["POST"])
def api_start():
    global current_thread, running, current_timeout_secs
    if running:
        return jsonify({"ok": False, "error": "已有测试在运行中"}), 400
    data = request.get_json() or {}
    protocol = data.get("protocol") or "mqtt"
    arch = data.get("arch") or "arm"
    power_schedule = (data.get("power_schedule") or "").strip()
    timeout = int(data.get("timeout") or 0)
    no_qemu = bool(data.get("no_qemu", True))
    no_rl = bool(data.get("no_rl", False))
    binary = (data.get("binary") or "").strip()
    firmware = (data.get("firmware") or "").strip()
    output = (data.get("output") or "").strip()

    # 开始前校验：未勾存根时需填写目标
    if not no_qemu and not binary and not firmware:
        return jsonify({"ok": False, "error": "未勾选存根模式时，请填写「目标二进制」或「固件路径」"}), 400
    if binary and not os.path.isfile(binary):
        return jsonify({"ok": False, "error": f"目标二进制不存在: {binary}"}), 400
    if firmware and not os.path.isfile(firmware):
        return jsonify({"ok": False, "error": f"固件文件不存在: {firmware}"}), 400

    current_timeout_secs = timeout
    log_buffer.clear()
    handler = BufferHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    root = logging.getLogger()
    root.addHandler(handler)

    try:
        cfg = _load_cfg()
        cfg.setdefault("protocol", {})["name"] = protocol
        cfg.setdefault("emulation", {})["architecture"] = arch
        if power_schedule:
            cfg.setdefault("seed", {})["power_schedule"] = power_schedule
        if output:
            cfg.setdefault("fuzzer", {})["output_dir"] = output
        cfg.setdefault("expert", {})["rl_enabled"] = not no_rl
        if no_qemu:
            cfg.setdefault("firmware", {})["target_binary"] = ""

        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        yaml.dump(cfg, tmp, allow_unicode=True)
        tmp.close()
        tmp_path = tmp.name

        def run():
            try:
                run_fuzzer_async(tmp_path, firmware, binary, timeout)
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
                root.removeHandler(handler)

        current_thread = threading.Thread(target=run, daemon=True)
        current_thread.start()
        running = True
        return jsonify({"ok": True})
    except Exception as e:
        root.removeHandler(handler)
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/stop", methods=["POST"])
def api_stop():
    global running
    if not current_fuzzer or not running:
        return jsonify({"ok": True, "message": "当前无运行中的测试"})
    try:
        current_fuzzer._stop_event.set()
    except Exception:
        pass
    return jsonify({"ok": True})


@app.route("/api/seed", methods=["POST"])
def api_seed():
    data = request.get_json() or {}
    protocol = data.get("protocol") or "mqtt"
    count = int(data.get("count") or 10)
    output = (data.get("output") or "./seeds").strip()
    try:
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
        pdir = os.path.join(os.path.dirname(__file__), output, protocol)
        os.makedirs(pdir, exist_ok=True)
        for i, s in enumerate(seeds[:count]):
            with open(os.path.join(pdir, f"seed_{i:04d}.bin"), "wb") as f:
                f.write(s)
        return jsonify({"ok": True, "message": f"已生成 {min(len(seeds), count)} 个种子", "path": pdir})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/reports/<path:filename>")
def serve_report(filename):
    report_dir = os.path.join(os.path.dirname(__file__), "output", "reports")
    return send_from_directory(report_dir, filename)


if __name__ == "__main__":
    import webbrowser
    port = 5000
    url = f"http://127.0.0.1:{port}"
    print(f"Web UI 已启动: {url}")
    print("在浏览器中打开上述地址即可使用。")
    webbrowser.open(url)
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
