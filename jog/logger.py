"""
jog/logger.py
==============
Mô-đun ghi log kiểm toán (Audit Trail) và hiển thị cảnh báo giao diện dòng lệnh (CLI UI).
Lưu trữ toàn bộ các sự kiện bảo mật theo định dạng chuẩn JSONL để phục vụ SecOps,
đồng thời xuất cảnh báo màu sắc trực quan ra Terminal.
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

# Các mã màu ANSI tiêu chuẩn cho Terminal
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
    """
    Quản lý nhật ký kiểm toán (Audit Logger) cho toàn bộ hệ thống JOG.
    Ghi nhận mọi hành vi quét, vi phạm, quyết định chặn/cảnh báo.
    """

    def __init__(self, log_path: Optional[str] = None):
        if log_path is None:
            log_path = os.environ.get("JOG_AUDIT_LOG", ".jog/logs/audit.log")
        self.log_file = Path(log_path)
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        """Tự động khởi tạo thư mục cha của file log nếu chưa tồn tại."""
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
        """
        Ghi một sự kiện bảo mật có cấu trúc vào audit.log (JSON Lines).
        
        :param event_type: Loại sự kiện ('prompt_check', 'code_check', 'git_commit', 'proxy_request')
        :param channel: Kênh phát sinh ('cli', 'proxy', 'git_hook')
        :param verdict: Quyết định ('allow', 'warn_user', 'block_immediately', 'pass', 'reject_force_agent_rewrite')
        :param risk_score: Điểm số rủi ro (1-10)
        :param details: Thông tin chi tiết các vi phạm
        :param raw_snippet: Trích đoạn mã hoặc lệnh (đã che các key nhạy cảm)
        """
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "channel": channel,
            "verdict": verdict,
            "risk_score": round(risk_score, 2),
            "details": details,
            "pid": os.getpid(),
            "user": os.environ.get("USER", "unknown"),
        }
        if raw_snippet:
            # Rút ngắn snippet để log không bị quá tải
            record["snippet_preview"] = raw_snippet[:300] + ("..." if len(raw_snippet) > 300 else "")

        try:
            self._ensure_log_dir()
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            # Không làm sập tiến trình nếu ghi log thất bại
            sys.stderr.write(f"[JOG Logger Error] Không thể ghi audit log: {e}\n")

    # =========================================================================
    # Các hàm hỗ trợ hiển thị Terminal đẹp mắt cho người dùng
    # =========================================================================

    @staticmethod
    def print_banner():
        """In biểu trưng Jev Omnichannel Guardrail trên Terminal."""
        banner = f"""{ANSI_CYAN}{ANSI_BOLD}
╔═════════════════════════════════════════════════════════════════════════════╗
║                   🛡️   JEV OMNICHANNEL GUARDRAIL (JOG)                      ║
║                 SecOps & AI Code Integrity Defense System                   ║
╚═════════════════════════════════════════════════════════════════════════════╝{ANSI_RESET}"""
        print(banner, file=sys.stderr)

    @staticmethod
    def print_block_alert(title: str, reason: str, remediation: Optional[str] = None):
        """In thông báo chặn khẩn cấp màu đỏ nổi bật."""
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
            msg += f"""{ANSI_YELLOW}║ Hướng dẫn khắc phục (Feedback cho Agent):
║   -> {remediation}
{ANSI_RESET}"""
        msg += f"""{ANSI_RED}{ANSI_BOLD}╚{border}╝{ANSI_RESET}
"""
        print(msg, file=sys.stderr)

    @staticmethod
    def print_warn_alert(title: str, warnings: list) -> None:
        """In thông báo cảnh báo màu vàng cho lệnh tiềm ẩn nguy cơ."""
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
        """In thông báo kiểm tra an toàn."""
        print(f"{ANSI_GREEN}🛡️  [JOG {channel.upper()}] An toàn: {message}{ANSI_RESET}", file=sys.stderr)


# Khởi tạo singleton logger
_global_logger: Optional[JogLogger] = None

def get_logger(log_path: Optional[str] = None) -> JogLogger:
    """Trả về phiên bản Logger toàn cục của JOG."""
    global _global_logger
    if _global_logger is None:
        _global_logger = JogLogger(log_path)
    return _global_logger
