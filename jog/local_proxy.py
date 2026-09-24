"""
jog/local_proxy.py
==================
Mô-đun Local Intercepting HTTP Proxy cho các IDE/GUI như Cursor, Antigravity, VS Code.
Lắng nghe mặc định tại http://127.0.0.1:8080.

Tính năng:
1. Đón các request gửi từ IDE (chuẩn Anthropic /v1/messages hoặc OpenAI /v1/chat/completions).
2. Trích xuất nội dung prompt và các đoạn mã code chuẩn bị thao tác/ghi tệp.
3. Quét qua cả 2 chế độ của JevEngine:
   - Chế độ 1: Quét lộ Secret, Token, Lệnh terminal hủy diệt trong prompt.
   - Chế độ 2: Quét lỗi tương lai (SQLi, N+1 Query, Resource Leak, Missing Timeout).
4. Auto-Feedback Loop:
   - Nếu vi phạm nghiêm trọng: Chặn ngay lập tức với HTTP 403 Forbidden.
   - Trả về body JSON định dạng chuẩn mô tả nguyên nhân và giải pháp để Agent tự động đọc và viết lại code sạch.
5. Nếu an toàn: Chuyển tiếp (forward) request tới máy chủ đích (Anthropic / OpenAI) và stream response về cho IDE.
"""

import os
import sys
import re
import json
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Dict, Any, Optional, Tuple, List

try:
    import requests
except ImportError:
    requests = None

from jog.config import JogConfig, load_config
from jog.logger import JogLogger, get_logger
from jog.jev_engine import JevEngine, PromptCheckResult, CodeCheckResult


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Máy chủ HTTP đa luồng xử lý đồng thời nhiều kết nối từ IDE."""
    daemon_threads = True
    allow_reuse_address = True


class JogProxyHandler(BaseHTTPRequestHandler):
    """Bộ xử lý đánh chặn và chuyển tiếp các yêu cầu HTTP từ IDE."""

    # Tái sử dụng instance của Engine và Config
    config: JogConfig = load_config()
    engine: JevEngine = JevEngine(config)
    logger = get_logger(config.logging.audit_log_file)

    def log_message(self, format, *args):
        """Tắt log mặc định của BaseHTTPRequestHandler để màn hình sạch đẹp."""
        return

    def do_GET(self):
        """Xử lý các truy vấn kiểm tra sức khỏe từ IDE."""
        if self.path in ["/health", "/status", "/"]:
            self._send_json_response(200, {
                "status": "healthy",
                "service": "Jev Omnichannel Guardrail (JOG) Local Proxy",
                "version": "1.0.0",
                "port": self.config.proxy.port,
            })
        elif self.path == "/v1/models":
            # IDE thường gọi /v1/models để kiểm tra API key
            self._send_json_response(200, {
                "object": "list",
                "data": [
                    {"id": "claude-3-5-sonnet-20241022", "object": "model"},
                    {"id": "gpt-4o", "object": "model"},
                    {"id": "gemini-1.5-pro", "object": "model"},
                ]
            })
        else:
            self._send_json_response(404, {"error": "Endpoint không tồn tại trên JOG Proxy."})

    def do_POST(self):
        """Đánh chặn các yêu cầu gửi tin nhắn và sinh mã từ IDE."""
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
        body_str = body_bytes.decode("utf-8", errors="replace")

        # 1. Kiểm tra nếu là endpoint AI thông dụng (/v1/messages hoặc /v1/chat/completions)
        is_ai_endpoint = any(ep in self.path for ep in ["/v1/messages", "/v1/chat/completions", "/v1/completions"])

        if is_ai_endpoint and body_str:
            try:
                payload = json.loads(body_str)
            except Exception:
                payload = {}

            # 2. Trích xuất Prompt và Code từ request payload
            prompt_text, code_snippets = self._extract_content(payload)

            # 3. Quét Chế độ 1: Prompt & Action Check
            mode1_res = self.engine.check_prompt_and_action(
                prompt_or_command=prompt_text,
                channel="ide_proxy_prompt",
                context={"path": self.path, "client": self.client_address[0]}
            )

            # 4. Quét Chế độ 2: Code Health & Future Risk Check trên các đoạn mã phát hiện
            mode2_res = CodeCheckResult(future_security_risk=False, production_stability_score=1.0)
            if code_snippets:
                combined_code = "\n\n# --- NEXT SNIPPET ---\n\n".join(code_snippets)
                mode2_res = self.engine.check_code_health(
                    code_content=combined_code,
                    file_path=None,
                    channel="ide_proxy_code",
                    context={"path": self.path}
                )

            # 5. Đánh giá vi phạm và kích hoạt AUTO-FEEDBACK LOOP nếu nguy hiểm
            is_blocked = False
            rejection_reasons = []
            remediations = []

            # Vi phạm Chế độ 1
            if mode1_res.action_verdict == "block_immediately":
                is_blocked = True
                rejection_reasons.extend(mode1_res.details)
                if mode1_res.remediation:
                    remediations.append(mode1_res.remediation)

            # Vi phạm Chế độ 2
            if mode2_res.maintainability_verdict == "reject_force_agent_rewrite":
                is_blocked = True
                rejection_reasons.extend(mode2_res.detected_flaws)
                remediations.extend(mode2_res.remediation_suggestions)

            if is_blocked:
                # KÍCH HOẠT AUTO-FEEDBACK LOOP CHO AI AGENT
                self._handle_guardrail_rejection(mode1_res, mode2_res, rejection_reasons, remediations)
                return

            # Nếu có cảnh báo nhẹ (warn_user)
            if mode1_res.action_verdict == "warn_user":
                JogLogger.print_warn_alert(
                    title=f"IDE Proxy phát hiện rủi ro từ request [{self.path}]",
                    warnings=mode1_res.details
                )

            # 6. CỐ VẤN KIẾN TRÚC TIÊN LƯỢNG (PROACTIVE ARCHITECTURAL ADVISOR)
            # Tự động nhận diện ý định kỹ thuật (ví dụ: 'thêm tính năng realtime') và bổ trợ quy tắc kiến trúc cho Agent
            advisory = self.engine.predict_architecture_advisory(prompt_text)
            if advisory:
                JogLogger.print_safe_pass(
                    "ADVISOR",
                    f"Phát hiện intent '{advisory.intent_description}'. Đang tự động bổ trợ ràng buộc kiến trúc cho Agent..."
                )
                payload = self._inject_advisory_directive(payload, advisory)
                body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                
                self.logger.log_event(
                    event_type="proactive_advisory_injected",
                    channel="ide_proxy",
                    verdict="augment_advisory",
                    risk_score=2.0,
                    details=advisory.to_dict(),
                    raw_snippet=prompt_text
                )

        # 7. Nếu an toàn: Chuyển tiếp tới Upstream API đích
        self._forward_to_upstream(body_bytes)

    # =========================================================================
    # CƠ CHẾ TRÍCH XUẤT NỘI DUNG (PAYLOAD PARSING)
    # =========================================================================

    def _extract_content(self, payload: Dict[str, Any]) -> Tuple[str, List[str]]:
        """
        Trích xuất văn bản prompt và các khối mã code từ payload
        (hỗ trợ cả OpenAI spec và Anthropic spec).
        """
        text_parts = []
        code_snippets = []

        # Xử lý trường system
        if "system" in payload:
            sys_val = payload["system"]
            if isinstance(sys_val, str):
                text_parts.append(sys_val)
            elif isinstance(sys_val, list):
                for item in sys_val:
                    if isinstance(item, dict) and "text" in item:
                        text_parts.append(item["text"])

        # Xử lý danh sách messages
        messages = payload.get("messages", [])
        if isinstance(messages, list):
            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                content = msg.get("content", "")
                if isinstance(content, str):
                    text_parts.append(content)
                    # Tìm các khối code markdown ```lang ... ```
                    found_blocks = re.findall(r"```(?:[a-zA-Z0-9_-]+)?\n([\s\S]*?)```", content)
                    code_snippets.extend(found_blocks)
                elif isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict):
                            if part.get("type") == "text" and "text" in part:
                                text_str = part["text"]
                                text_parts.append(text_str)
                                found = re.findall(r"```(?:[a-zA-Z0-9_-]+)?\n([\s\S]*?)```", text_str)
                                code_snippets.extend(found)
                            elif part.get("type") == "tool_result" and "content" in part:
                                text_parts.append(str(part["content"]))

        combined_text = "\n".join(text_parts)
        return combined_text, code_snippets

    def _inject_advisory_directive(self, payload: Dict[str, Any], advisory: Any) -> Dict[str, Any]:
        """Bổ trợ chỉ thị kiến trúc của Jev vào request payload trước khi forward tới Upstream LLM."""
        directive_text = f"\n\n{advisory.injected_prompt_directive}\n"

        # Hỗ trợ Anthropic spec (/v1/messages)
        if "system" in payload:
            if isinstance(payload["system"], str):
                payload["system"] += directive_text
            elif isinstance(payload["system"], list):
                payload["system"].append({"type": "text", "text": directive_text})
        elif "/v1/messages" in self.path:
            payload["system"] = directive_text.strip()

        # Hỗ trợ OpenAI spec (/v1/chat/completions)
        if "messages" in payload and isinstance(payload["messages"], list):
            sys_msg = next((m for m in payload["messages"] if isinstance(m, dict) and m.get("role") == "system"), None)
            if sys_msg and isinstance(sys_msg.get("content"), str):
                sys_msg["content"] += directive_text
            else:
                payload["messages"].insert(0, {"role": "system", "content": directive_text.strip()})

        return payload

    # =========================================================================
    # AUTO-FEEDBACK LOOP: PHẢN HỒI HTTP 403 FORBIDDEN KÈM HƯỚNG DẪN TỰ SỬA
    # =========================================================================

    def _handle_guardrail_rejection(
        self,
        m1: PromptCheckResult,
        m2: CodeCheckResult,
        reasons: List[str],
        remediations: List[str]
    ):
        """
        Trả về HTTP 403 Forbidden kèm body JSON định dạng chuẩn OpenAI/Anthropic Error.
        Cơ chế này bắt buộc AI Agent trong Cursor/Antigravity nhận lỗi, đọc lý do,
        và tự động kích hoạt chu trình viết lại code an toàn (Self-Correction Loop).
        """
        reason_summary = " | ".join(reasons) if reasons else "Vi phạm chính sách bảo mật JOG."
        remediation_summary = " ".join(remediations) if remediations else "Vui lòng kiểm tra và sửa đổi mã nguồn."

        error_feedback = (
            f"[JOG GUARDRAIL CHẶN TỰ ĐỘNG]\n"
            f"LÝ DO: {reason_summary}\n"
            f"YÊU CẦU CHO AGENT: Bạn vừa sinh ra mã nguồn hoặc lệnh bị đánh giá là nguy hiểm/không đạt chuẩn. "
            f"Hãy tự động viết lại (rewrite) sạch sẽ theo hướng dẫn sau:\n"
            f"-> {remediation_summary}"
        )

        response_body = {
            "error": {
                "message": error_feedback,
                "type": "guardrail_violation",
                "code": "jog_blocked_force_rewrite",
                "param": None,
                "diagnostics": {
                    "destructive_intent_score": m1.destructive_intent_score,
                    "has_credential_leak": m1.has_credential_leak,
                    "production_stability_score": m2.production_stability_score,
                    "architecture_flaw_type": m2.architecture_flaw_type,
                    "reasons": reasons,
                    "remediations": remediations,
                }
            }
        }

        # In cảnh báo ra Terminal máy trạm
        JogLogger.print_block_alert(
            title="IDE Proxy đã chặn request nguy hại và kích hoạt Auto-Feedback",
            reason=reason_summary,
            remediation=remediation_summary
        )

        # Ghi log kiểm toán
        self.logger.log_event(
            event_type="proxy_block_feedback",
            channel="ide_proxy",
            verdict="reject_force_agent_rewrite",
            risk_score=max(m1.destructive_intent_score, m2.production_stability_score),
            details=response_body["error"]["diagnostics"]
        )

        self._send_json_response(403, response_body)

    # =========================================================================
    # CHUYỂN TIẾP TỚI MÁY CHỦ UPSTREAM (FORWARDING & STREAMING)
    # =========================================================================

    def _determine_upstream_url(self) -> str:
        """Xác định địa chỉ upstream phù hợp dựa vào path hoặc header tùy chỉnh."""
        custom_upstream = self.headers.get("X-Upstream-Url")
        if custom_upstream:
            return custom_upstream.rstrip("/") + self.path

        if "/v1/messages" in self.path:
            return self.config.proxy.upstream_anthropic_url.rstrip("/") + self.path
        else:
            return self.config.proxy.upstream_openai_url.rstrip("/") + self.path

    def _forward_to_upstream(self, body_bytes: bytes):
        """Chuyển tiếp request an toàn tới Upstream API và stream response về IDE."""
        # Nếu đang trong chế độ kiểm thử nội bộ (JOG_TEST_MODE=1), phản hồi tức thì
        if os.environ.get("JOG_TEST_MODE") == "1":
            try:
                echo_payload = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                echo_payload = {}
            self._send_json_response(200, {
                "id": "jog-test-response",
                "status": "success",
                "message": "Request an toàn được thông qua bởi JOG Proxy (Test Mode Echo).",
                "path": self.path,
                "injected_payload": echo_payload,
            })
            return

        upstream_url = self._determine_upstream_url()

        # Chuẩn bị headers chuyển tiếp
        forward_headers = {}
        for k, v in self.headers.items():
            if k.lower() not in ["host", "content-length"]:
                forward_headers[k] = v

        try:
            # Gửi request sang upstream server
            upstream_resp = requests.post(
                upstream_url,
                data=body_bytes,
                headers=forward_headers,
                stream=True,
                timeout=30.0
            )

            # Trả status code và headers về IDE
            self.send_response(upstream_resp.status_code)
            for hk, hv in upstream_resp.headers.items():
                if hk.lower() not in ["transfer-encoding", "content-encoding", "content-length"]:
                    self.send_header(hk, hv)
            self.end_headers()

            # Stream dữ liệu phản hồi từng chunk về IDE
            for chunk in upstream_resp.iter_content(chunk_size=4096):
                if chunk:
                    self.wfile.write(chunk)
                    self.wfile.flush()

        except requests.exceptions.RequestException as e:
            self._send_json_response(502, {
                "error": {
                    "message": f"JOG Proxy không thể kết nối tới Upstream ({upstream_url}): {str(e)}",
                    "type": "upstream_connection_error",
                    "code": "bad_gateway"
                }
            })

    def _send_json_response(self, status_code: int, data: Dict[str, Any]):
        """Hàm trợ giúp gửi phản hồi JSON có định dạng."""
        encoded = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self):
        """Hỗ trợ CORS preflight requests từ trình duyệt hoặc web IDE."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()


def run_proxy_server(host: Optional[str] = None, port: Optional[int] = None):
    """Khởi động Local Intercepting Proxy HTTP Server."""
    config = load_config()
    server_host = host or config.proxy.host
    server_port = port or config.proxy.port

    JogLogger.print_banner()
    print(f"\n🚀 [JOG PROXY] Đang khởi động Local Intercepting Proxy...")
    print(f"📍 Lắng nghe tại: http://{server_host}:{server_port}")
    print(f"🔗 Anthropic Upstream: {config.proxy.upstream_anthropic_url}")
    print(f"🔗 OpenAI Upstream:    {config.proxy.upstream_openai_url}")
    print(f"🛡️  Auto-Feedback:     BẬT (Trả về HTTP 403 Forbidden khi phát hiện rủi ro)")
    print(f"⚡ Nhấn Ctrl+C để dừng proxy.\n")

    server_address = (server_host, server_port)
    try:
        httpd = ThreadedHTTPServer(server_address, JogProxyHandler)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 [JOG PROXY] Đang dừng Proxy Server...")
    except Exception as e:
        print(f"\n❌ [JOG PROXY ERROR] Không thể mở cổng {server_port}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run_proxy_server()
