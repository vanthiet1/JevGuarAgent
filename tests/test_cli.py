"""
tests/test_cli.py
=================
Kiểm thử tự động cho mô-đun đánh chặn CLI (jog/intercept_cli.py).
Kiểm tra các hành vi:
  - Cho phép thực thi lệnh an toàn (allow -> exit 0)
  - Chặn ngay lập tức lệnh phá hoại hoặc lộ key (block -> exit 1)
  - Cảnh báo lệnh rủi ro vừa phải và xử lý câu trả lời [y/N] (warn -> 130 khi từ chối, 0 khi đồng ý).
"""

import os
import sys
import unittest
from unittest.mock import patch
from io import StringIO

from jog.intercept_cli import run_cli_interceptor


class TestCliInterceptor(unittest.TestCase):
    """Kiểm thử hoạt động của CLI Interceptor."""

    def setUp(self):
        os.environ["JOG_TEST_MODE"] = "1"

    def test_safe_command_allowed(self):
        """Lệnh an toàn phải trả về exit code 0."""
        code = run_cli_interceptor("echo", ["Hello", "World"])
        self.assertEqual(code, 0)

    def test_destructive_command_blocked(self):
        """Lệnh phá hoại rm -rf / phải bị chặn ngay và trả về exit code 1."""
        code = run_cli_interceptor("claude", ["rm -rf /"])
        self.assertEqual(code, 1)

    def test_credential_leak_blocked(self):
        """Lệnh chứa secret key phải bị chặn ngay và trả về exit code 1."""
        code = run_cli_interceptor("gemini", ["Deploy with key: ghp_123456789012345678901234567890123456"])
        self.assertEqual(code, 1)

    @patch("builtins.input", return_value="n")
    def test_warning_command_aborted_by_user(self, mock_input):
        """Lệnh cảnh báo khi người dùng gõ 'n' phải hủy bỏ và trả về exit code 130."""
        code = run_cli_interceptor("codex", ["git reset --hard HEAD~1"])
        self.assertEqual(code, 130)

    @patch("builtins.input", return_value="y")
    def test_warning_command_confirmed_by_user(self, mock_input):
        """Lệnh cảnh báo khi người dùng gõ 'y' phải được tiếp tục (exit code 0 trong test mode)."""
        code = run_cli_interceptor("codex", ["git reset --hard HEAD~1"])
        self.assertEqual(code, 0)

    def test_activate_and_deactivate(self):
        """Kiểm tra lệnh jog activate và deactivate trên một repository mục tiêu."""
        import tempfile
        import subprocess
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / ".git").mkdir()

            jog_bin = Path(__file__).resolve().parent.parent / "bin" / "jog"

            # 1. Kích hoạt
            proc = subprocess.run(
                [sys.executable, str(jog_bin), "activate", str(tmppath)],
                capture_output=True,
                text=True
            )
            self.assertEqual(proc.returncode, 0)
            self.assertTrue((tmppath / ".agents" / "rules" / "jog_guardrail.md").exists())
            self.assertTrue((tmppath / ".agents" / "skills" / "jog-guard" / "SKILL.md").exists())
            self.assertTrue((tmppath / ".git" / "hooks" / "pre-commit").exists())

            # 2. Hủy kích hoạt
            proc2 = subprocess.run(
                [sys.executable, str(jog_bin), "deactivate", str(tmppath)],
                capture_output=True,
                text=True
            )
            self.assertEqual(proc2.returncode, 0)
            self.assertFalse((tmppath / ".agents" / "rules" / "jog_guardrail.md").exists())
            self.assertFalse((tmppath / ".git" / "hooks" / "pre-commit").exists())


if __name__ == "__main__":
    unittest.main()

