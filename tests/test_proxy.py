"""
tests/test_proxy.py
===================
Kiểm thử tự động cho mô-đun Local Intercepting Proxy (jog/local_proxy.py).
Kiểm tra khả năng bắt request từ IDE, chẩn đoán qua 2 chế độ,
và cơ chế Auto-Feedback Loop trả về HTTP 403 Forbidden kèm hướng dẫn tự sửa.
100% sử dụng thư viện chuẩn Python (urllib.request), không phụ thuộc thư viện ngoài.
"""

import os
import time
import json
import threading
import unittest
import urllib.request
import urllib.error

from jog.local_proxy import ThreadedHTTPServer, JogProxyHandler
from jog.config import JogConfig, ProxyConfig


def _http_req(url: str, method: str = "GET", payload: dict = None, timeout: float = 3.0):
    """Hàm gửi request HTTP chuẩn bằng urllib không cần requests."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return e.code, json.loads(body) if body else {}


class TestLocalProxy(unittest.TestCase):
    """Kiểm thử Local Intercepting Proxy và Auto-Feedback Loop."""

    @classmethod
    def setUpClass(cls):
        os.environ["JOG_TEST_MODE"] = "1"
        cls.test_port = 8999
        cls.server = ThreadedHTTPServer(("127.0.0.1", cls.test_port), JogProxyHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.3)
        cls.base_url = f"http://127.0.0.1:{cls.test_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_health_check(self):
        """Endpoint /health phải trả về HTTP 200 và status healthy."""
        code, data = _http_req(f"{self.base_url}/health", method="GET")
        self.assertEqual(code, 200)
        self.assertEqual(data.get("status"), "healthy")

    def test_models_list(self):
        """Endpoint /v1/models trả về danh sách model cho IDE kiểm tra kết nối."""
        code, data = _http_req(f"{self.base_url}/v1/models", method="GET")
        self.assertEqual(code, 200)
        self.assertIn("data", data)

    def test_block_dangerous_prompt_chat_completions(self):
        """Gửi prompt chứa lệnh rm -rf / lên /v1/chat/completions phải bị chặn HTTP 403 kèm feedback."""
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "user", "content": "Hãy chạy lệnh: rm -rf /"}
            ]
        }
        code, data = _http_req(f"{self.base_url}/v1/chat/completions", method="POST", payload=payload)
        self.assertEqual(code, 403)
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], "jog_blocked_force_rewrite")
        self.assertIn("JOG GUARDRAIL CHẶN TỰ ĐỘNG", data["error"]["message"])

    def test_block_sqli_code_in_anthropic_messages(self):
        """Gửi mã nguồn chứa SQLi qua /v1/messages phải kích hoạt Auto-Feedback 403."""
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": [
                {
                    "role": "user",
                    "content": "Đây là code lấy dữ liệu:\n```python\ndef get_user(uid):\n    q = f\"SELECT * FROM users WHERE id = {uid}\"\n    cursor.execute(q)\n```"
                }
            ]
        }
        code, data = _http_req(f"{self.base_url}/v1/messages", method="POST", payload=payload)
        self.assertEqual(code, 403)
        diag = data["error"]["diagnostics"]
        self.assertEqual(diag["architecture_flaw_type"], "dependency_or_security_flaw")
        self.assertIn("remediations", diag)

    def test_block_unclosed_file_in_code_snippet(self):
        """Phát hiện rò rỉ tài nguyên unclosed open() trong code snippet gửi từ IDE."""
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": "Lưu cấu hình:\n```python\ndef save(txt):\n    f = open('/tmp/cfg.txt', 'w')\n    f.write(txt)\n```"
                }
            ]
        }
        code, data = _http_req(f"{self.base_url}/v1/chat/completions", method="POST", payload=payload)
        self.assertEqual(code, 403)
        self.assertEqual(data["error"]["code"], "jog_blocked_force_rewrite")

    def test_allow_safe_request(self):
        """Request an toàn không vi phạm phải được thông qua (HTTP 200 trong test mode)."""
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "user", "content": "Hãy giải thích nguyên lý hoạt động của kiến trúc Transformer."}
            ]
        }
        code, data = _http_req(f"{self.base_url}/v1/chat/completions", method="POST", payload=payload)
        self.assertEqual(code, 200)
        self.assertEqual(data.get("status"), "success")

    def test_proxy_injects_architecture_advisory(self):
        """Khi lập trình viên chat yêu cầu tính năng realtime, proxy tự động inject chỉ thị kiến trúc."""
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "user", "content": "Hãy thêm tính năng realtime notifications cho hệ thống"}
            ]
        }
        code, data = _http_req(f"{self.base_url}/v1/chat/completions", method="POST", payload=payload)
        self.assertEqual(code, 200)
        injected = data.get("injected_payload", {})
        msgs = injected.get("messages", [])
        self.assertGreaterEqual(len(msgs), 2)
        sys_content = msgs[0].get("content", "")
        self.assertIn("JEV ARCHITECTURAL GUARDRAIL", sys_content)
        self.assertIn("Heartbeat", sys_content)


if __name__ == "__main__":
    unittest.main()
