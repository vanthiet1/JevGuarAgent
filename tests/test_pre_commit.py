"""
tests/test_pre_commit.py
========================
Kiểm thử tự động cho mô-đun Git Pre-commit Hook (jog/pre_commit_guard.py).
Kiểm tra khả năng phát hiện tệp staged vi phạm ngưỡng rò rỉ hoặc rủi ro tương lai.
"""

import os
import sys
import unittest
import tempfile
import subprocess
from unittest.mock import patch

from jog.pre_commit_guard import execute_pre_commit_guard, SENSITIVE_FILENAMES


class TestPreCommitGuard(unittest.TestCase):
    """Kiểm thử hoạt động của pre_commit_guard."""

    def test_sensitive_filenames_list(self):
        """Danh sách tệp nhạy cảm phải bao gồm .env và private keys."""
        self.assertIn(".env", SENSITIVE_FILENAMES)
        self.assertIn("id_rsa", SENSITIVE_FILENAMES)
        self.assertIn("credentials.json", SENSITIVE_FILENAMES)

    @patch("jog.pre_commit_guard.get_staged_files")
    def test_no_staged_files_passes(self, mock_staged):
        """Khi không có tệp nào staged, hook cho qua (exit code 0)."""
        mock_staged.return_value = []
        code = execute_pre_commit_guard()
        self.assertEqual(code, 0)

    @patch("jog.pre_commit_guard.get_staged_files")
    def test_sensitive_env_file_blocked(self, mock_staged):
        """Khi có tệp .env hoặc .env.production bị stage, hook phải chặn (exit code 1)."""
        mock_staged.return_value = [("A", ".env")]
        code = execute_pre_commit_guard()
        self.assertEqual(code, 1)

    @patch("jog.pre_commit_guard.get_staged_diff")
    @patch("jog.pre_commit_guard.get_staged_content")
    @patch("jog.pre_commit_guard.get_staged_files")
    def test_staged_code_with_sqli_blocked(self, mock_staged, mock_content, mock_diff):
        """Mã nguồn chứa SQLi có điểm sập hệ thống cao (>= 7.5) phải bị chặn."""
        mock_staged.return_value = [("M", "src/user_repo.py")]
        mock_content.return_value = """
def find_user(id):
    query = f"SELECT * FROM users WHERE id = {id}"
    cursor.execute(query)
"""
        mock_diff.return_value = "+ query = f\"SELECT * FROM users WHERE id = {id}\""
        code = execute_pre_commit_guard()
        self.assertEqual(code, 1)

    @patch("jog.pre_commit_guard.get_staged_diff")
    @patch("jog.pre_commit_guard.get_staged_content")
    @patch("jog.pre_commit_guard.get_staged_files")
    def test_staged_clean_code_allowed(self, mock_staged, mock_content, mock_diff):
        """Mã nguồn sạch sẽ, tuân thủ best practices phải được thông qua (exit code 0)."""
        mock_staged.return_value = [("M", "src/safe_service.py")]
        mock_content.return_value = """
def get_user_safely(cursor, user_id):
    query = "SELECT * FROM users WHERE id = %s"
    cursor.execute(query, (user_id,))
    return cursor.fetchone()
"""
        mock_diff.return_value = "+ cursor.execute(query, (user_id,))"
        code = execute_pre_commit_guard()
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
