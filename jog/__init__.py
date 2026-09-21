"""
Jev Omnichannel Guardrail (JOG)
===============================
Hệ thống Guardrail đa kênh bảo vệ mã nguồn và môi trường thực thi khi lập trình
cùng các AI Coding Agent (Cursor, Antigravity, Claude Code, Codex, Gemini CLI).

Bản quyền (c) 2026 - Phát triển bởi SecOps & AI Platform Engineering Team.
"""

__version__ = "1.0.0"
__author__ = "JOG SecOps Team"

from jog.config import JogConfig, load_config
from jog.logger import JogLogger, get_logger
from jog.jev_engine import JevEngine, PromptCheckResult, CodeCheckResult

__all__ = [
    "JogConfig",
    "load_config",
    "JogLogger",
    "get_logger",
    "JevEngine",
    "PromptCheckResult",
    "CodeCheckResult",
]
