
import os
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        os.system("")
    except Exception:
        pass

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_BLUE = "\033[34m"
ANSI_MAGENTA = "\033[35m"
ANSI_CYAN = "\033[36m"
ANSI_WHITE = "\033[37m"
ANSI_BG_RED = "\033[41m"
ANSI_BG_YELLOW = "\033[43m"

class JogLogger:

    def __init__(self, log_path: Optional[str] = None):
        if log_path is None:
            log_path = os.environ.get("JOG_AUDIT_LOG", ".jog/logs/audit.log")
        self.log_file = Path(log_path)
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def log_event(
        self,
        event_type: str,
        channel: str,
        verdict: str,
        risk_score: float,
        details: Dict[str, Any],
        raw_snippet: Optional[str] = None
    ) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "channel": channel,
            "verdict": verdict,
            "risk_score": round(risk_score, 2),
            "details": details,
            "pid": os.getpid(),
            "user": os.environ.get("USER") or os.environ.get("USERNAME", "unknown"),
        }
        if raw_snippet:

            record["snippet_preview"] = raw_snippet[:300] + ("..." if len(raw_snippet) > 300 else "")

        try:
            self._ensure_log_dir()
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            sys.stderr.write(f"[JOG Logger Error] Không thể ghi audit log: {e}\n")

        try:
            global_log = Path.home() / ".jog" / "logs" / "audit.log"
            if global_log.resolve() != self.log_file.resolve():
                global_log.parent.mkdir(parents=True, exist_ok=True)
                with open(global_log, "a", encoding="utf-8") as gf:
                    gf.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass

    @staticmethod
    def print_banner():
        banner = f"""{ANSI_CYAN}{ANSI_BOLD}
╔═════════════════════════════════════════════════════════════════════════════╗
║                   🛡️   JEV OMNICHANNEL GUARDRAIL (JOG)                      ║
║                 SecOps & AI Code Integrity Defense System                   ║
╚═════════════════════════════════════════════════════════════════════════════╝{ANSI_RESET}"""
        print(banner, file=sys.stderr)

    @staticmethod
    def print_block_alert(title: str, reason: str, remediation: Optional[str] = None):
        border = "═" * 75
        msg = f"""
{ANSI_RED}{ANSI_BOLD}╔{border}╗
║ 🚨 [JOG GUARDRAIL CHẶN TỨC THỜI]                                          ║
║ TIÊU ĐỀ: {title[:60]:<60} ║
╠{border}╣{ANSI_RESET}
{ANSI_RED}║ Lý do vi phạm:
║   -> {reason}
{ANSI_RESET}"""
        if remediation:
            msg += f"""{ANSI_YELLOW}║ Hướng dẫn sửa đổi (Feedback cho Agent):
║   -> {remediation}
{ANSI_RESET}"""
        msg += f"""{ANSI_RED}{ANSI_BOLD}╚{border}╝{ANSI_RESET}
"""
        print(msg, file=sys.stderr)

    @staticmethod
    def print_warn_alert(title: str, warnings: list) -> None:
        border = "─" * 75
        msg = f"""
{ANSI_YELLOW}{ANSI_BOLD}┌{border}┐
│ ⚠️  [JOG CẢNH BÁO NGUY CƠ TIỀM ẨN]                                         │
│ Tiêu đề: {title[:60]:<60} │
├{border}┤{ANSI_RESET}
{ANSI_YELLOW}│ Phát hiện các vấn đề cần lưu ý:"""
        for w in warnings:
            msg += f"\n│   • {w}"
        msg += f"""
{ANSI_YELLOW}{ANSI_BOLD}└{border}┘{ANSI_RESET}
"""
        print(msg, file=sys.stderr)

    @staticmethod
    def print_safe_pass(channel: str, message: str):
        print(f"{ANSI_GREEN}🛡️  [Jev Guardrail] {message}{ANSI_RESET}", file=sys.stderr)

_global_logger: Optional[JogLogger] = None

def get_logger(log_path: Optional[str] = None) -> JogLogger:
    global _global_logger
    if _global_logger is None:
        _global_logger = JogLogger(log_path)
    return _global_logger
