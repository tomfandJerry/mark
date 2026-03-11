"""日志模块"""
import logging
import os
from datetime import datetime
from rich.console import Console
from rich.theme import Theme

custom_theme = Theme({
    "info": "cyan", "warning": "yellow", "error": "bold red",
    "success": "bold green", "fuzzing": "bold magenta", "crash": "bold red on white",
})
console = Console(theme=custom_theme)

def setup_logger(name: str, level: str = "INFO", log_file: str = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()
    from rich.logging import RichHandler
    rich_handler = RichHandler(console=console, show_time=True, markup=True)
    rich_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(rich_handler)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(fh)
    return logger

class FuzzerLogger:
    def __init__(self, output_dir: str = "./output"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(output_dir, "logs", f"fuzzer_{ts}.log")
        self.logger = setup_logger("IoTFuzzer", log_file=log_path)

    def info(self, msg: str): self.logger.info(msg)
    def warning(self, msg: str): self.logger.warning(msg)
    def error(self, msg: str): self.logger.error(msg)
    def success(self, msg: str): self.logger.info(f"[success]{msg}[/success]")
    def crash(self, msg: str): self.logger.critical(f"[crash] {msg}")
    def coverage(self, msg: str): self.logger.info(f"[cov]{msg}[/cov]")
    def fuzzing(self, msg: str): self.logger.info(f"[fuzzing]{msg}[/fuzzing]")

    def print_banner(self):
        console.print("[bold cyan]IoT Firmware Grey-box Fuzzer v1.0.0[/bold cyan]")
        console.print("[dim]面向IoT固件协议的自动化灰盒模糊测试工具[/dim]")
