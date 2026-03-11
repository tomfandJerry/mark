"""固件加载器 - Binwalk 解包与目标检测"""
import os
import subprocess
import shutil
import logging
from dataclasses import dataclass
from typing import Optional, List

logger = logging.getLogger("IoTFuzzer.FirmwareLoader")

@dataclass
class FirmwareInfo:
    path: str
    extracted_dir: str = ""
    root_fs: str = ""
    target_binary: str = ""
    architecture: str = "unknown"

COMMON_TARGETS = ["mosquitto", "httpd", "uhttpd", "coap-server", "telnetd", "dropbear"]

class FirmwareLoader:
    def __init__(self, binwalk_path: str = "binwalk", work_dir: str = "/tmp/firmware_work"):
        self.binwalk_path = binwalk_path
        self.work_dir = work_dir
        os.makedirs(work_dir, exist_ok=True)

    def load(self, firmware_path: str, target_name: str = "") -> FirmwareInfo:
        info = FirmwareInfo(path=firmware_path)
        if not os.path.exists(firmware_path):
            raise FileNotFoundError(f"固件不存在: {firmware_path}")
        out_dir = os.path.join(self.work_dir, os.path.splitext(os.path.basename(firmware_path))[0] + "_extracted")
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)
        try:
            subprocess.run([self.binwalk_path, "--extract", "--recurse", "--directory", out_dir, firmware_path],
                          capture_output=True, timeout=300)
        except FileNotFoundError:
            info.extracted_dir = os.path.dirname(firmware_path)
            return info
        info.extracted_dir = out_dir
        for root, dirs, _ in os.walk(out_dir):
            if "bin" in dirs and "lib" in dirs:
                info.root_fs = root
                break
        if not info.root_fs:
            info.root_fs = out_dir
        for name in (target_name and [target_name]) or COMMON_TARGETS:
            for r, _, files in os.walk(info.root_fs):
                for f in files:
                    if f == name or f.startswith(name):
                        fp = os.path.join(r, f)
                        if os.access(fp, os.X_OK) or self._is_elf(fp):
                            info.target_binary = fp
                            return info
        return info

    def _is_elf(self, path: str) -> bool:
        try:
            return open(path, "rb").read(4) == b"\x7fELF"
        except Exception:
            return False
