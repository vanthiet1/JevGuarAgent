"""
jog/jev_engine.py
=================
Mô-đun lõi phân tích và đánh giá an toàn của Jev Omnichannel Guardrail (JOG).
Thực hiện 2 chế độ kiểm tra:
  - Chế độ 1 (Mode 1): Prompt & Action Check (Câu lệnh người dùng hoặc bash command của Agent).
  - Chế độ 2 (Mode 2): Code Health & Future Risk Check (Mã nguồn chuẩn bị tạo/sửa hoặc Git diff).

Kết nối API TypeSafe: POST https://api.typesafe.ai/v1/systemone (timeout <= 3s).
Nếu mất mạng, timeout hoặc không có API key, tự động kích hoạt Engine Fallback
nội bộ dựa trên AST Parser và Hệ quy tắc Heuristics/Regex chuyên sâu.
"""

import os
import re
import ast
import json
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

import urllib.request
import urllib.error

from jog.config import JogConfig, load_config
from jog.logger import get_logger


# =============================================================================
# HỢP ĐỒNG KẾT QUẢ TRẢ VỀ (DATA CONTRACTS)
# =============================================================================

@dataclass
class PromptCheckResult:
    """Kết quả thẩm định cho Chế độ 1: Prompt & Action Check."""
    has_credential_leak: bool = False
    destructive_intent_score: float = 1.0  # Thang điểm từ 1.0 đến 10.0
    action_verdict: str = "allow"          # "allow" | "warn_user" | "block_immediately"
    details: List[str] = field(default_factory=list)
    remediation: Optional[str] = None
    engine_source: str = "local_fallback"  # "typesafe_cloud" | "openrouter_cloud" | "local_fallback"
    raw_json: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "action_verdict": self.action_verdict,
            "destructive_intent_score": self.destructive_intent_score,
            "has_credential_leak": self.has_credential_leak,
            "engine_source": self.engine_source,
            "details": self.details,
            "remediation": self.remediation,
        }
        if self.raw_json:
            d["raw_model_response"] = self.raw_json
        return d


@dataclass
class CodeCheckResult:
    """Kết quả thẩm định cho Chế độ 2: Code Health & Future Risk Check."""
    future_security_risk: bool = False
    production_stability_score: float = 1.0  # Thang điểm từ 1.0 đến 10.0 (càng cao càng nguy hiểm)
    architecture_flaw_type: str = "clean_and_safe"
    # Lựa chọn: "clean_and_safe" | "resource_leak_or_dos_risk" |
    #          "broken_logic_or_race_condition" | "dependency_or_security_flaw" |
    #          "spaghetti_anti_pattern"
    maintainability_verdict: str = "pass"
    # Lựa chọn: "pass" | "warn_dev_needs_refactor" | "reject_force_agent_rewrite"
    leak_risk: float = 0.0                   # Nguy cơ rò rỉ bí mật trong code (0.0 -> 1.0)
    detected_flaws: List[str] = field(default_factory=list)
    remediation_suggestions: List[str] = field(default_factory=list)
    engine_source: str = "local_fallback"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "future_security_risk": self.future_security_risk,
            "production_stability_score": self.production_stability_score,
            "architecture_flaw_type": self.architecture_flaw_type,
            "maintainability_verdict": self.maintainability_verdict,
            "leak_risk": self.leak_risk,
            "detected_flaws": self.detected_flaws,
            "remediation_suggestions": self.remediation_suggestions,
            "engine_source": self.engine_source,
        }


@dataclass
class ArchitectureAdvisory:
    """Khuyến nghị tối ưu kiến trúc tiên lượng khi nhận diện intent trong chat."""
    detected_intent: str
    intent_description: str
    risk_factors: List[str]
    recommended_patterns: List[str]
    injected_prompt_directive: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detected_intent": self.detected_intent,
            "intent_description": self.intent_description,
            "risk_factors": self.risk_factors,
            "recommended_patterns": self.recommended_patterns,
            "injected_prompt_directive": self.injected_prompt_directive,
        }


# =============================================================================
# HỆ QUY TẮC NHẬN DẠNG SECRETS & PATTERNS
# =============================================================================

SECRET_PATTERNS: List[Tuple[str, str, float]] = [
    (
        "AWS Access Key ID",
        r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
        1.0
    ),
    (
        "AWS Secret Access Key",
        r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}['\"]?",
        1.0
    ),
    (
        "GitHub Personal Access Token",
        r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,255}|github_pat_[A-Za-z0-9_]{22}_[A-Za-z0-9_]{59}",
        1.0
    ),
    (
        "Anthropic API Key",
        r"sk-ant-api[0-9]{2}-[A-Za-z0-9_-]{80,120}",
        1.0
    ),
    (
        "OpenRouter API Key",
        r"sk-or-v1-[a-f0-9]{64}",
        1.0
    ),
    (
        "OpenAI API Key",
        r"sk-(?!(?:ant|or)-)(?:proj-|live-)?[A-Za-z0-9_-]{32,80}",
        1.0
    ),
    (
        "Private RSA/SSH Key",
        r"-----BEGIN (?:RSA |OPENSSH |DSA |EC )?PRIVATE KEY-----",
        1.0
    ),
    (
        "Generic Bearer / JWT Token",
        r"(?i)bearer\s+eyJh[A-Za-z0-9-_=]+\.eyJh[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]+",
        0.9
    ),
    (
        "Slack Bot/User Token",
        r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*",
        0.9
    ),
    (
        "Stripe Live API Key",
        r"(?:sk|rk)_live_[0-9a-zA-Z]{24,34}",
        1.0
    ),
    (
        "Hardcoded Password / Secret Assignment",
        r"(?i)(?:password|passwd|secret_key|client_secret|db_pass)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]",
        0.8
    ),
    (
        "Database Connection String with Credentials",
        r"(?i)(?:postgres|postgresql|mysql|mongodb(?:\+srv)?|redis)://[^:]+:[^@\s]+@[a-zA-Z0-9.-]+",
        0.95
    ),
    (
        ".env Sensitive Key Format",
        r"(?m)^(?:DB_PASSWORD|SECRET_KEY|API_KEY|AUTH_TOKEN|PRIVATE_KEY)\s*=\s*\S+",
        0.85
    )
]


class JevEngine:
    """
    Bộ não trung tâm thực thi Guardrail.
    Cung cấp giao diện đồng nhất để kiểm tra Prompt, Bash action, và Code health.
    """

    def __init__(self, config: Optional[JogConfig] = None):
        self.config = config or load_config()
        self.logger = get_logger(self.config.logging.audit_log_file)

    # =========================================================================
    # CHẾ ĐỘ 1: PROMPT & ACTION CHECK
    # =========================================================================

    def check_prompt_and_action(
        self,
        prompt_or_command: str,
        channel: str = "cli",
        context: Optional[Dict[str, Any]] = None
    ) -> PromptCheckResult:
        """
        Kiểm tra câu lệnh người dùng hoặc lệnh bash mà AI Agent dự định chạy.
        1. Gửi tới TypeSafe API (nếu có key và kết nối thông suốt, timeout <= 3s).
        2. Nếu API không phản hồi, tự động chuyển sang Fallback Heuristics.
        """
        if not prompt_or_command or not prompt_or_command.strip():
            return PromptCheckResult(
                has_credential_leak=False,
                destructive_intent_score=1.0,
                action_verdict="allow",
                details=["Nội dung kiểm tra rỗng."],
                engine_source="local_fallback"
            )

        # Thử gọi TypeSafe Cloud API trước nếu có API Key
        if self.config.api.typesafe_api_key:
            cloud_res = self._call_typesafe_api_mode1(prompt_or_command, channel, context)
            if cloud_res is not None:
                self._record_audit_mode1(prompt_or_command, channel, cloud_res)
                return cloud_res

        # Sử dụng Bộ phân tích Offline Fallback
        fallback_res = self._offline_analyze_mode1(prompt_or_command, channel)
        self._record_audit_mode1(prompt_or_command, channel, fallback_res)
        return fallback_res

    # =========================================================================
    # CHẾ ĐỘ 2: CODE HEALTH & FUTURE RISK CHECK
    # =========================================================================

    def check_code_health(
        self,
        code_content: str,
        file_path: Optional[str] = None,
        channel: str = "ide_rules",
        context: Optional[Dict[str, Any]] = None
    ) -> CodeCheckResult:
        """
        Đoán trước các rủi ro mã nguồn trong tương lai (Future-Proof Code Inspection).
        Kiểm tra SQLi, Memory Leaks, N+1 Query, Race Condition, Missing Timeout.
        """
        if not code_content or not code_content.strip():
            return CodeCheckResult(
                future_security_risk=False,
                production_stability_score=1.0,
                architecture_flaw_type="clean_and_safe",
                maintainability_verdict="pass",
                engine_source="local_fallback"
            )

        # Thử gọi TypeSafe Cloud API nếu có cấu hình
        if self.config.api.typesafe_api_key:
            cloud_res = self._call_typesafe_api_mode2(code_content, file_path, channel, context)
            if cloud_res is not None:
                self._record_audit_mode2(code_content, file_path, channel, cloud_res)
                return cloud_res

        # Sử dụng Bộ phân tích Code Offline Fallback chuyên sâu
        fallback_res = self._offline_analyze_mode2(code_content, file_path)
        self._record_audit_mode2(code_content, file_path, channel, fallback_res)
        return fallback_res

    # =========================================================================
    # CỐ VẤN KIẾN TRÚC TIÊN LƯỢNG (PROACTIVE ARCHITECTURE ADVISOR)
    # =========================================================================

    def predict_architecture_advisory(self, user_prompt: str) -> Optional[ArchitectureAdvisory]:
        """
        Phân tích ý định (intent) trong câu chat của người dùng (ví dụ: 'thêm tính năng realtime'),
        chẩn đoán trước các nguy cơ kỹ thuật tương lai và tự động tạo ra khuyến nghị kiến trúc
        kèm các chỉ thị bắt buộc để Agent sinh code tối ưu ngay từ đầu.
        """
        if not user_prompt or not user_prompt.strip():
            return None

        prompt_lower = user_prompt.lower()

        # 1. Ý định Realtime / WebSocket / EventStream
        if re.search(r"(?i)\b(?:realtime|real-time|websocket|socket\.io|sse|server-sent|pubsub|pub/sub|thời\s+gian\s+thực)\b", prompt_lower):
            return ArchitectureAdvisory(
                detected_intent="realtime_streaming_architecture",
                intent_description="Phát triển tính năng truyền tải dữ liệu thời gian thực (Realtime/WebSocket)",
                risk_factors=[
                    "Nguy cơ rò rỉ bộ nhớ do lưu socket trong biến global không giải phóng khi client ngắt kết nối.",
                    "Race condition khi nhiều tiến trình/luồng cùng broadcast dữ liệu tới clients.",
                    "Treo kết nối (Zombie Connections) do thiếu cơ chế Heartbeat (Ping/Pong).",
                    "Reconnection Storm làm sập server khi hàng nghìn client cùng kết nối lại đồng loạt."
                ],
                recommended_patterns=[
                    "Thiết lập cơ chế Heartbeat (Ping/Pong chu kỳ 25-30 giây) kèm timeout tự ngắt kết nối chết.",
                    "Thu hồi triệt để tài nguyên, hủy đăng ký event listeners trong sự kiện disconnect/close.",
                    "Sử dụng Redis Pub/Sub hoặc Thread-safe Queue thay vì mảng toàn cục trần để sẵn sàng scale đa tiến trình.",
                    "Cấu hình Exponential Backoff có Jitter phía client khi reconnect."
                ],
                injected_prompt_directive=(
                    "[JEV ARCHITECTURAL GUARDRAIL - QUY TẮC BẮT BUỘC KHI XÂY DỰNG REALTIME]:\n"
                    "1. BẮT BUỘC cài đặt cơ chế Heartbeat Ping/Pong (timeout 30s) để dọn dẹp kết nối zombie.\n"
                    "2. BẮT BUỘC giải phóng toàn bộ listeners/sockets trong sự kiện disconnect để chống Memory Leak.\n"
                    "3. KHÔNG lưu socket connections vào biến toàn cục thô thiếu đồng bộ; hãy dùng cấu trúc quản lý tập trung Thread-safe hoặc Redis Pub/Sub.\n"
                    "4. Xử lý lỗi ngắt kết nối đột ngột một cách an toàn (Graceful Disconnection)."
                )
            )

        # 2. Ý định Truy vấn cơ sở dữ liệu / ORM / CRUD
        if re.search(r"(?i)\b(?:database|cơ\s+sở\s+dữ\s+liệu|csdl|bảng\s+dữ\s+liệu|truy\s+vấn|sql|query|orm|sqlite|postgresql|mysql|mongodb)\b", prompt_lower):
            return ArchitectureAdvisory(
                detected_intent="database_persistence_layer",
                intent_description="Thao tác cơ sở dữ liệu và truy vấn dữ liệu",
                risk_factors=[
                    "Lỗ hổng SQL Injection nghiêm trọng nếu ghép chuỗi truy vấn thô hoặc f-strings.",
                    "Lỗi hiệu năng N+1 Query làm quá tải server DB khi duyệt danh sách liên kết.",
                    "Cạn kiệt Connection Pool nếu không đóng kết nối sau khi dùng."
                ],
                recommended_patterns=[
                    "Sử dụng Parameterized Queries hoặc Prepared Statements.",
                    "Áp dụng Eager Loading (JOIN, select_related, IN query) thay vì truy vấn trong vòng lặp.",
                    "Luôn giới hạn số lượng bản ghi trả về bằng Pagination (LIMIT/OFFSET)."
                ],
                injected_prompt_directive=(
                    "[JEV ARCHITECTURAL GUARDRAIL - QUY TẮC BẮT BUỘC KHI THAO TÁC CƠ SỞ DỮ LIỆU]:\n"
                    "1. BẮT BUỘC dùng Parameterized Query: cursor.execute('... WHERE id = %s', (val,)). TUYỆT ĐỐI KHÔNG dùng f-string SQL.\n"
                    "2. BẮT BUỘC tránh lỗi N+1 Query: Không gọi query bên trong vòng lặp for/while; hãy dùng JOIN hoặc IN query.\n"
                    "3. Luôn sử dụng Connection Pool hoặc Context Manager để đảm bảo giải phóng kết nối."
                )
            )

        # 3. Ý định Gọi API mạng / Tích hợp bên ngoài
        if re.search(r"(?i)\b(?:gọi\s+api|call\s+api|tích\s+hợp\s+api|fetch|requests\.(?:get|post)|http\s+client|webhook|third-party)\b", prompt_lower):
            return ArchitectureAdvisory(
                detected_intent="external_network_integration",
                intent_description="Tích hợp mạng và gọi API bên thứ ba",
                risk_factors=[
                    "Treo thread pool làm sập dịch vụ (Denial of Service) khi bên thứ ba phản hồi chậm hoặc treo kết nối.",
                    "Rò rỉ API Keys bí mật vào mã nguồn hoặc log hệ thống."
                ],
                recommended_patterns=[
                    "Luôn cấu hình tham số timeout rõ ràng (ví dụ: timeout=5.0 hoặc 10.0).",
                    "Đọc API keys từ biến môi trường qua os.getenv() hoặc cấu hình bí mật.",
                    "Cài đặt cơ chế Retry với Exponential Backoff cho các mã lỗi 5xx."
                ],
                injected_prompt_directive=(
                    "[JEV ARCHITECTURAL GUARDRAIL - QUY TẮC BẮT BUỘC KHI GỌI API MẠNG]:\n"
                    "1. BẮT BUỘC thiết lập tham số 'timeout' rõ ràng (ví dụ: timeout=5.0) cho mọi request HTTP.\n"
                    "2. TUYỆT ĐỐI KHÔNG hardcode API Keys, Token trong mã nguồn; hãy sử dụng os.getenv().\n"
                    "3. Bắt ngoại lệ mạng (RequestException, TimeoutError) và xử lý fallback an toàn."
                )
            )

        # 4. Ý định Xác thực / Đăng nhập / Mật khẩu
        if re.search(r"(?i)\b(?:đăng\s+nhập|login|xác\s+thực|authentication|auth|mật\s+khẩu|password|jwt|token|session)\b", prompt_lower):
            return ArchitectureAdvisory(
                detected_intent="authentication_security",
                intent_description="Bảo mật xác thực người dùng và quản lý phiên",
                risk_factors=[
                    "Lưu trữ mật khẩu dạng thô (plaintext) hoặc băm bằng thuật toán lỗi thời (MD5, SHA1).",
                    "Token JWT không có thời hạn hết hạn hoặc bị tấn công Timing Attack khi so sánh bí mật."
                ],
                recommended_patterns=[
                    "Sử dụng Bcrypt hoặc Argon2id kèm Salt ngẫu nhiên để băm mật khẩu.",
                    "Cấu hình thời hạn 'exp' cho Access Token và bảo mật HttpOnly Cookie.",
                    "Sử dụng hmac.compare_digest() khi so sánh token bí mật."
                ],
                injected_prompt_directive=(
                    "[JEV ARCHITECTURAL GUARDRAIL - QUY TẮC BẮT BUỘC KHI XỬ LÝ XÁC THỰC]:\n"
                    "1. BẮT BUỘC sử dụng Bcrypt hoặc Argon2id với Salt ngẫu nhiên để băm mật khẩu. KHÔNG dùng MD5/SHA1.\n"
                    "2. Token JWT bắt buộc phải có thời hạn 'exp'.\n"
                    "3. Sử dụng hmac.compare_digest() khi kiểm tra token bí mật để chống Timing Attack."
                )
            )

        # 5. Ý định Xử lý đa luồng / Tác vụ nền
        if re.search(r"(?i)\b(?:background\s+task|tiến\s+trình\s+nền|đa\s+luồng|threading|asyncio|worker|hàng\s+đợi|celery|queue)\b", prompt_lower):
            return ArchitectureAdvisory(
                detected_intent="concurrency_and_background_jobs",
                intent_description="Xử lý đồng thời đa luồng và tác vụ chạy ngầm",
                risk_factors=[
                    "Race condition khi các luồng cùng cập nhật biến toàn cục mà không có Lock.",
                    "Worker crash làm mất mát tác vụ chưa được xác nhận (unacknowledged jobs)."
                ],
                recommended_patterns=[
                    "Bảo vệ tài nguyên dùng chung bằng threading.Lock() hoặc asyncio.Lock().",
                    "Bắt try/catch bên trong worker để một tác vụ lỗi không làm sập toàn bộ tiến trình nền.",
                    "Hỗ trợ dừng mềm (Graceful Shutdown) khi nhận tín hiệu SIGINT/SIGTERM."
                ],
                injected_prompt_directive=(
                    "[JEV ARCHITECTURAL GUARDRAIL - QUY TẮC BẮT BUỘC KHI XỬ LÝ ĐỒNG THỜI]:\n"
                    "1. BẮT BUỘC sử dụng Lock (threading.Lock hoặc asyncio.Lock) khi cập nhật tài nguyên chia sẻ.\n"
                    "2. Bao bọc logic bên trong worker bằng try...except để tránh sập toàn bộ hàng đợi khi gặp lỗi cục bộ.\n"
                    "3. Đảm bảo giải phóng tài nguyên sau khi worker hoàn thành."
                )
            )

        # 6. Ý định Upload tệp tin / Xử lý I/O tệp
        if re.search(r"(?i)\b(?:upload|tải\s+lên|multipart|file\s+handling|xử\s+lý\s+tệp|avatar|ảnh|image\s+upload|storage)\b", prompt_lower):
            return ArchitectureAdvisory(
                detected_intent="file_upload_and_storage",
                intent_description="Xử lý upload tệp tin và lưu trữ dữ liệu tập tin",
                risk_factors=[
                    "Lỗ hổng Path Traversal (tên file chứa '../') cho phép ghi đè file nhạy cảm hệ thống.",
                    "Tải lên mã độc (Web Shell / Executable) nếu chỉ kiểm tra đuôi file bề nổi mà không kiểm tra MIME thực tế.",
                    "Lỗi tràn bộ nhớ (Memory Exhaustion) hoặc cạn kiệt dung lượng đĩa do thiếu giới hạn kích thước tệp (Max File Size).",
                    "Rò rỉ tài nguyên File Descriptor (File Handle Leak) do không đóng stream sau khi đọc/ghi."
                ],
                recommended_patterns=[
                    "Đổi tên file ngẫu nhiên bằng UUID (ví dụ: uuid4() + extension an toàn) thay vì dùng tên gốc của người dùng.",
                    "Xác thực cả định dạng mở rộng (whitelist extensions) lẫn MIME type bằng magic bytes.",
                    "Luôn đặt giới hạn dung lượng tải lên tối đa (ví dụ: max_size = 5MB hoặc 10MB) và đọc theo luồng (chunk/stream).",
                    "Luôn sử dụng Context Manager (with open(...) hoặc try...finally) để đảm bảo đóng stream."
                ],
                injected_prompt_directive=(
                    "[JEV ARCHITECTURAL GUARDRAIL - QUY TẮC BẮT BUỘC KHI XỬ LÝ UPLOAD FILE]:\n"
                    "1. BẮT BUỘC đổi tên file bằng UUID ngẫu nhiên; TUYỆT ĐỐI KHÔNG dùng tên file gốc từ client để chống Path Traversal.\n"
                    "2. BẮT BUỘC kiểm tra kích thước file tối đa (Max Upload Limit) trước khi lưu.\n"
                    "3. Validate định dạng file theo Whitelist extension và MIME type an toàn.\n"
                    "4. Đọc/ghi stream theo chunks và sử dụng Context Manager để giải phóng tài nguyên I/O."
                )
            )

        # 7. Ý định Thanh toán / Giao dịch tiền tệ / Khấu trừ số dư
        if re.search(r"(?i)\b(?:thanh\s+toán|payment|checkout|tiền|money|giao\s+dịch|transaction|ví|wallet|balance|trừ\s+tiền|vnpay|momo|stripe|paypal)\b", prompt_lower):
            return ArchitectureAdvisory(
                detected_intent="payment_and_financial_transactions",
                intent_description="Xử lý giao dịch thanh toán và biến động số dư tài chính",
                risk_factors=[
                    "Lỗi trừ tiền 2 lần (Double Spending) do người dùng ấn nhiều lần hoặc mạng chập chờn gửi lại request.",
                    "Thiếu tính Idempotency: Webhook bên thứ ba gọi lại nhiều lần gây cộng dồn tiền sai.",
                    "Lỗi làm tròn dấu phẩy động (Floating-Point Precision Error) khi dùng kiểu float để tính tiền.",
                    "Race condition khi 2 giao dịch rút tiền đồng thời vượt quá số dư thực tế."
                ],
                recommended_patterns=[
                    "Bắt buộc sử dụng Idempotency Key (UUID) cho mỗi giao dịch.",
                    "Tuyệt đối KHÔNG dùng kiểu float/double để lưu tiền; hãy dùng Integer (đơn vị xu/cent) hoặc Decimal.",
                    "Sử dụng Database Transaction cô lập (SELECT FOR UPDATE hoặc Serializable) để khóa dòng dữ liệu khi cập nhật số dư.",
                    "Xác thực chữ ký số (Webhook Signature / HMAC) của cổng thanh toán trước khi cập nhật trạng thái đơn."
                ],
                injected_prompt_directive=(
                    "[JEV ARCHITECTURAL GUARDRAIL - QUY TẮC BẮT BUỘC KHI XỬ LÝ THANH TOÁN / GIAO DỊCH]:\n"
                    "1. BẮT BUỘC dùng cơ chế Idempotency Key để chống lặp giao dịch (Double Charge).\n"
                    "2. TUYỆT ĐỐI KHÔNG dùng kiểu float/double tính tiền; dùng Integer hoặc Decimal chính xác.\n"
                    "3. Bắt buộc dùng Database Transaction có Khóa Bi quan (Pessimistic Lock: SELECT FOR UPDATE) khi trừ số dư.\n"
                    "4. Luôn kiểm tra chữ ký số HMAC của webhook thanh toán bên thứ ba."
                )
            )

        # 8. Ý định Bộ nhớ đệm / Caching
        if re.search(r"(?i)\b(?:cache|caching|redis|memcached|lru|bộ\s+nhớ\s+đệm)\b", prompt_lower):
            return ArchitectureAdvisory(
                detected_intent="caching_and_performance_optimization",
                intent_description="Quản lý bộ nhớ đệm (Caching) và tối ưu hóa hiệu năng",
                risk_factors=[
                    "Cache Stampede (Thundering Herd): Hàng nghìn request đồng thời đổ vào DB khi cache key hết hạn.",
                    "Dữ liệu lỗi thời (Stale Data) do quên xóa cache khi cập nhật dữ liệu gốc trong database.",
                    "Cache Penetration: Kẻ tấn công truy vấn liên tục ID không tồn tại làm query xuyên thủng cache xuống DB."
                ],
                recommended_patterns=[
                    "Áp dụng TTL có độ lệch ngẫu nhiên (Jitter: ví dụ 300s + random(0, 30s)) để tránh hết hạn đồng loạt.",
                    "Chủ động xóa hoặc cập nhật cache ngay khi có thao tác Mutation (CUD - Create/Update/Delete).",
                    "Cache kết quả rỗng (Null/Empty Cache) có TTL ngắn cho các truy vấn không tìm thấy dữ liệu."
                ],
                injected_prompt_directive=(
                    "[JEV ARCHITECTURAL GUARDRAIL - QUY TẮC BẮT BUỘC KHI DÙNG CACHING]:\n"
                    "1. BẮT BUỘC gắn TTL ngẫu nhiên (Jitter) khi lưu cache để tránh Cache Stampede.\n"
                    "2. Luôn có cơ chế Invalidate Cache (xóa cache) ngay khi dữ liệu gốc bị cập nhật/xóa.\n"
                    "3. Cache kết quả null có TTL ngắn để chống Cache Penetration."
                )
            )

        # 9. Ý định Nhận dữ liệu đầu vào Form / API Input Validation
        if re.search(r"(?i)\b(?:form|biểu\s+mẫu|input\s+validation|xác\s+thực\s+dữ\s+liệu|nhập\s+liệu|sanitize|xss)\b", prompt_lower):
            return ArchitectureAdvisory(
                detected_intent="input_validation_and_sanitization",
                intent_description="Xác thực và làm sạch dữ liệu đầu vào của người dùng",
                risk_factors=[
                    "Lỗ hổng Cross-Site Scripting (XSS) khi hiển thị dữ liệu người dùng thô lên giao diện HTML.",
                    "ReDoS (Regular Expression Denial of Service) khi dùng regex phức tạp để kiểm tra chuỗi đầu vào.",
                    "Chỉ kiểm tra dữ liệu ở phía Client (Frontend) mà bỏ qua xác thực ở Backend."
                ],
                recommended_patterns=[
                    "Bắt buộc xác thực dữ liệu ở cả 2 đầu, đặc biệt là Backend bằng Schema Validation (Zod, Pydantic, Joi).",
                    "Luôn encode hoặc sanitize HTML entities trước khi render ra DOM.",
                    "Giới hạn độ dài tối đa của mọi trường văn bản (Max String Length)."
                ],
                injected_prompt_directive=(
                    "[JEV ARCHITECTURAL GUARDRAIL - QUY TẮC BẮT BUỘC KHI XỬ LÝ FORM & INPUT]:\n"
                    "1. BẮT BUỘC kiểm tra và xác thực dữ liệu chặt chẽ ở Backend (dùng Schema Validator như Zod/Pydantic).\n"
                    "2. Giới hạn độ dài tối đa (maxLength) cho mọi trường chuỗi nhập vào.\n"
                    "3. Encode HTML an toàn chống XSS trước khi render dữ liệu động ra giao diện."
                )
            )

        return None

    # =========================================================================
    # LOGIC KẾT NỐI TYPESAFE API (HTTP POST /v1/systemone)
    # =========================================================================

    def _call_typesafe_api_mode1(
        self,
        text: str,
        channel: str,
        context: Optional[Dict[str, Any]]
    ) -> Optional[PromptCheckResult]:
        """Gửi request thẩm định Mode 1 tới OpenRouter hoặc TypeSafe API."""
        api_key = self.config.api.typesafe_api_key
        if not api_key:
            return None

        # Trường hợp sử dụng OpenRouter API
        if api_key.startswith("sk-" + "or-"):
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/vanthiet1/JevGuarAgent",
                "X-Title": "JevGuarAgent"
            }
            payload = {
                "model": getattr(self.config.api, "model", "deepseek/deepseek-chat"),
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a SecOps & Code Integrity AI engine. Analyze the given prompt or command for security risks, secret leaks, and destructive commands. Reply ONLY with valid JSON having keys: has_credential_leak (bool), destructive_intent_score (float 1-10), action_verdict (allow/warn_user/block_immediately), details (list of strings), remediation (string or null)."
                    },
                    {"role": "user", "content": text}
                ],
                "response_format": {"type": "json_object"}
            }
            try:
                body_data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(url, data=body_data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.config.api.timeout_seconds) as resp:
                    if resp.status == 200:
                        content_str = resp.read().decode("utf-8")
                        data = json.loads(content_str)
                        content = data["choices"][0]["message"]["content"]
                        parsed = json.loads(content)
                        return PromptCheckResult(
                            has_credential_leak=bool(parsed.get("has_credential_leak", False)),
                            destructive_intent_score=float(parsed.get("destructive_intent_score", 1.0)),
                            action_verdict=str(parsed.get("action_verdict", "allow")),
                            details=parsed.get("details", []),
                            remediation=parsed.get("remediation"),
                            engine_source="openrouter_cloud",
                            raw_json=parsed
                        )
            except Exception:
                pass
            return None

        # Trường hợp sử dụng TypeSafe Enterprise API
        url = self.config.api.typesafe_api_url
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Jev-Omnichannel-Guardrail/1.0"
        }
        payload = {
            "mode": "prompt_and_action_check",
            "input_text": text,
            "channel": channel,
            "context": context or {},
        }
        try:
            body_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=body_data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=self.config.api.timeout_seconds) as resp:
                if resp.status == 200:
                    content_str = resp.read().decode("utf-8")
                    data = json.loads(content_str)
                    return PromptCheckResult(
                        has_credential_leak=bool(data.get("has_credential_leak", False)),
                        destructive_intent_score=float(data.get("destructive_intent_score", 1.0)),
                        action_verdict=str(data.get("action_verdict", "allow")),
                        details=data.get("details", []),
                        remediation=data.get("remediation"),
                        engine_source="typesafe_cloud",
                        raw_json=data
                    )
        except Exception:
            pass
        return None

    def _call_typesafe_api_mode2(
        self,
        code: str,
        file_path: Optional[str],
        channel: str,
        context: Optional[Dict[str, Any]]
    ) -> Optional[CodeCheckResult]:
        """Gửi request thẩm định Mode 2 tới TypeSafe API."""
        url = self.config.api.typesafe_api_url
        headers = {
            "Authorization": f"Bearer {self.config.api.typesafe_api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Jev-Omnichannel-Guardrail/1.0"
        }
        payload = {
            "mode": "code_health_check",
            "code_content": code,
            "file_path": file_path,
            "channel": channel,
            "context": context or {},
        }
        try:
            body_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=body_data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=self.config.api.timeout_seconds) as resp:
                if resp.status == 200:
                    content_str = resp.read().decode("utf-8")
                    data = json.loads(content_str)
                    return CodeCheckResult(
                        future_security_risk=bool(data.get("future_security_risk", False)),
                        production_stability_score=float(data.get("production_stability_score", 1.0)),
                        architecture_flaw_type=str(data.get("architecture_flaw_type", "clean_and_safe")),
                        maintainability_verdict=str(data.get("maintainability_verdict", "pass")),
                        leak_risk=float(data.get("leak_risk", 0.0)),
                        detected_flaws=data.get("detected_flaws", []),
                        remediation_suggestions=data.get("remediation_suggestions", []),
                        engine_source="typesafe_cloud"
                    )
        except Exception:
            pass
        return None

    # =========================================================================
    # BỘ PHÂN TÍCH OFFLINE FALLBACK MODE 1 (PROMPT & ACTION)
    # =========================================================================

    def _offline_analyze_mode1(self, text: str, channel: str) -> PromptCheckResult:
        """Phân tích bí mật rò rỉ và lệnh terminal nguy hiểm bằng Heuristics."""
        details = []
        has_leak = False
        max_destructive_score = 1.0

        # 1. Quét rò rỉ bí mật / token / credentials
        detected_secrets = self.detect_secrets(text)
        if detected_secrets:
            has_leak = True
            for s_name, s_match in detected_secrets:
                details.append(f"Phát hiện rò rỉ bí mật [{s_name}]: {s_match}")

        # 2. Quét các lệnh Terminal hủy diệt nghiêm trọng (BLOCK)
        # a. Lệnh rm phá hoại root / home / system dirs
        if self._is_destructive_rm_root(text):
            details.append("Chặn lệnh phá hoại nghiêm trọng [rm đệ quy trên thư mục gốc hoặc người dùng]")
            max_destructive_score = max(max_destructive_score, 10.0)

        # b. Lệnh ghi đè đĩa hoặc định dạng ổ cứng
        if re.search(r"(?i)\b(?:dd\s+if=/dev/(?:zero|urandom|null)|mkfs(?:\.[a-z0-9]+)?\s+/dev/|fdisk\s+/dev/|wipefs\b)", text):
            details.append("Chặn lệnh phá hoại nghiêm trọng [Ghi đè hoặc phá hủy phân vùng ổ đĩa]")
            max_destructive_score = max(max_destructive_score, 10.0)

        # c. Fork bomb
        if re.search(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:|fork\s+while\s+fork", text):
            details.append("Chặn lệnh phá hoại nghiêm trọng [Fork Bomb làm tê liệt tài nguyên]")
            max_destructive_score = max(max_destructive_score, 10.0)

        # d. Chmod toàn quyền nguy hiểm
        if re.search(r"(?i)\bchmod\s+(?:-[a-z]*R[a-z]*\s+)?(?:777|a\+rwx)\s+(?:/|/\*|/etc|/var|/usr)(?:\s|$|;)", text):
            details.append("Chặn lệnh phá hoại nghiêm trọng [Phá vỡ phân quyền hệ điều hành chmod 777 -R]")
            max_destructive_score = max(max_destructive_score, 9.5)

        # e. Tải và thực thi script trực tiếp vào shell (Exfiltration / RCE pipe)
        if re.search(r"(?i)\b(?:curl|wget)\s+[^|;&]+\s*\|\s*(?:ba|z|da)?sh(?:\s|$)", text):
            details.append("Chặn lệnh phá hoại nghiêm trọng [Tải và thực thi mã độc qua pipe curl|bash]")
            max_destructive_score = max(max_destructive_score, 9.5)

        # f. Truy cập file mật khẩu nhạy cảm của hệ điều hành
        if re.search(r"(?i)\b(?:cat|head|tail|less|more|nano|vim?)\s+(?:/etc/shadow|/etc/sudoers)\b", text):
            details.append("Chặn thao tác nguy hiểm [Đọc file cấu hình bảo mật /etc/shadow hoặc sudoers]")
            max_destructive_score = max(max_destructive_score, 9.0)

        # g. Vô hiệu hóa tường lửa và bảo mật
        if re.search(r"(?i)\b(?:ufw\s+disable|iptables\s+-F|setenforce\s+0)\b", text):
            details.append("Chặn lệnh nguy hiểm [Vô hiệu hóa tường lửa hoặc SELinux]")
            max_destructive_score = max(max_destructive_score, 9.0)

        # h. Xóa sạch cơ sở dữ liệu (DROP DATABASE / TRUNCATE)
        if re.search(r"(?i)\b(?:DROP\s+DATABASE|DROP\s+TABLE(?:\s+IF\s+EXISTS)?\s+\w+|TRUNCATE\s+TABLE)\b", text):
            details.append("Chặn lệnh phá hoại nghiêm trọng [DROP DATABASE hoặc DROP TABLE]")
            max_destructive_score = max(max_destructive_score, 9.5)

        # 3. Quét các lệnh có rủi ro vừa phải cần cảnh báo (WARN USER)
        if max_destructive_score < 8.0:
            if re.search(r"(?i)\bdocker\s+(?:rm\s+-f|system\s+prune\s+-a|kill)\b", text):
                details.append("Cảnh báo rủi ro [Xóa hoặc dừng cưỡng bức toàn bộ container Docker]")
                max_destructive_score = max(max_destructive_score, 6.5)

            if re.search(r"(?i)\bgit\s+(?:reset\s+--hard|clean\s+-[a-z]*f[a-z]*d[a-z]*|push\s+-[a-z]*f\b|push\s+--force)", text):
                details.append("Cảnh báo rủi ro [Thao tác Git có thể làm mất dữ liệu mã nguồn không thể hoàn tác]")
                max_destructive_score = max(max_destructive_score, 6.5)

            if re.search(r"(?i)\b(?:killall\s+-9|pkill\s+-9|kill\s+-9\s+-1)\b", text):
                details.append("Cảnh báo rủi ro [Hủy tiến trình cưỡng bức hàng loạt]")
                max_destructive_score = max(max_destructive_score, 6.0)

            # rm -rf trên thư mục con trong dự án
            if re.search(r"(?i)\brm\s+-[a-z]*r[a-z]*f[a-z]*\s+[a-zA-Z0-9_.-]+", text) and max_destructive_score < 5.5:
                details.append("Cảnh báo rủi ro [Xóa tệp/thư mục đệ quy qua rm -rf]")
                max_destructive_score = max(max_destructive_score, 5.5)

            # Đọc file bí mật cục bộ
            if re.search(r"(?i)\b(?:cat|tail|head)\s+(?:\.env|\.env\.[a-z]+|id_rsa|id_ed25519)\b", text):
                details.append("Cảnh báo rủi ro [Hiển thị nội dung tệp bí mật .env hoặc SSH key]")
                max_destructive_score = max(max_destructive_score, 6.5)

        # Đưa ra phán quyết (Verdict)
        if has_leak or max_destructive_score >= 8.5:
            action_verdict = "block_immediately"
            remediation = (
                "Hủy bỏ câu lệnh chứa bí mật hoặc lệnh phá hủy hệ thống. "
                "Tuyệt đối không chạy lệnh xóa gốc (rm -rf /) hoặc dán secrets vào prompt."
            )
        elif max_destructive_score >= 5.0:
            action_verdict = "warn_user"
            remediation = "Cần xác nhận từ người dùng trước khi thực thi lệnh có tác dụng phụ lớn."
        else:
            action_verdict = "allow"
            remediation = None

        return PromptCheckResult(
            has_credential_leak=has_leak,
            destructive_intent_score=round(max_destructive_score, 1),
            action_verdict=action_verdict,
            details=details if details else ["Câu lệnh an toàn."],
            remediation=remediation,
            engine_source="local_fallback"
        )

    def _is_destructive_rm_root(self, cmd: str) -> bool:
        """Kiểm tra xem lệnh rm có cờ đệ quy và nhắm vào root/home/system dirs không."""
        if not re.search(r"(?i)\brm\b", cmd):
            return False
        has_recursive = bool(re.search(r"(?i)(?:-[a-z]*r|--recursive)", cmd))
        has_root_target = bool(re.search(
            r"(?:(?<=\s)|^)(?:/|/\*|~|~\*|\$HOME|\${HOME}|/etc|/var|/usr|/bin|/sbin)(?:\s|$|;)",
            cmd
        ))
        return has_recursive and has_root_target

    # =========================================================================
    # BỘ PHÂN TÍCH OFFLINE FALLBACK MODE 2 (CODE HEALTH & FUTURE RISKS)
    # =========================================================================

    def _offline_analyze_mode2(self, code: str, file_path: Optional[str]) -> CodeCheckResult:
        """
        Chẩn đoán chuyên sâu các nguy cơ tiềm ẩn trong code:
        - Rò rỉ bí mật mã hóa cứng (Hardcoded Secrets).
        - SQL Injection qua chuỗi động / f-strings.
        - Memory / Resource Leaks (mở file/socket không đóng).
        - N+1 Query Patterns (gọi query trong vòng lặp).
        - Race Conditions (biến toàn cục chia sẻ thiếu Lock).
        - Thiếu timeout khi gọi mạng / HTTP (Production Freeze).
        """
        detected_flaws = []
        remediations = []
        security_risk = False
        stability_score = 1.0
        flaw_type = "clean_and_safe"
        leak_risk = 0.0

        # 1. Kiểm tra bí mật trong mã nguồn
        secrets_found = self.detect_secrets(code)
        if secrets_found:
            security_risk = True
            leak_risk = 1.0
            stability_score = max(stability_score, 9.0)
            flaw_type = "dependency_or_security_flaw"
            for s_name, s_match in secrets_found:
                detected_flaws.append(f"[Lộ Secret] Khóa nhạy cảm ({s_name}): {s_match}")
            remediations.append("Đưa các API keys, passwords vào biến môi trường (.env) và sử dụng os.getenv().")

        # 2. Phân tích cú pháp AST cho tệp Python nếu khả dụng
        is_python = True
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in [".py", ".pyw"]:
                is_python = False

        if is_python:
            ast_flaws, ast_remediations, ast_stability, ast_security, ast_type = self._ast_inspect_python(code)
            detected_flaws.extend(ast_flaws)
            remediations.extend(ast_remediations)
            stability_score = max(stability_score, ast_stability)
            if ast_security:
                security_risk = True
            if ast_type != "clean_and_safe":
                flaw_type = ast_type

        # 3. Phân tích Heuristics đa ngôn ngữ (JavaScript, TypeScript, Go, Java, Python, SQL)
        poly_flaws, poly_remediations, poly_stability, poly_security, poly_type = self._polyglot_regex_inspect(code)
        detected_flaws.extend(poly_flaws)
        remediations.extend(poly_remediations)
        stability_score = max(stability_score, poly_stability)
        if poly_security:
            security_risk = True
        if flaw_type == "clean_and_safe" and poly_type != "clean_and_safe":
            flaw_type = poly_type

        # 4. Xác định phán quyết (Verdict)
        if stability_score >= 7.5 or security_risk or leak_risk > 0.6:
            maintainability_verdict = "reject_force_agent_rewrite"
        elif stability_score >= 4.5:
            maintainability_verdict = "warn_dev_needs_refactor"
        else:
            maintainability_verdict = "pass"

        return CodeCheckResult(
            future_security_risk=security_risk,
            production_stability_score=round(stability_score, 1),
            architecture_flaw_type=flaw_type,
            maintainability_verdict=maintainability_verdict,
            leak_risk=round(leak_risk, 2),
            detected_flaws=detected_flaws if detected_flaws else ["Mã nguồn đạt chuẩn an toàn."],
            remediation_suggestions=remediations,
            engine_source="local_fallback"
        )

    def detect_secrets(self, text: str) -> List[Tuple[str, str]]:
        """Nhận diện các mẫu secret trong văn bản và che đi ký tự nhạy cảm."""
        found = []
        for name, pattern, _ in SECRET_PATTERNS:
            for match in re.finditer(pattern, text):
                raw_match = match.group(0)
                if len(raw_match) > 10:
                    masked = raw_match[:4] + "*" * (len(raw_match) - 8) + raw_match[-4:]
                else:
                    masked = "***SECRET***"
                found.append((name, masked))
        return found

    def _ast_inspect_python(self, code: str) -> Tuple[List[str], List[str], float, bool, str]:
        """Phân tích AST sâu cho mã Python để tìm lỗi thiết kế và rủi ro sập hệ thống."""
        flaws = []
        remediations = []
        stability_score = 1.0
        security_risk = False
        flaw_type = "clean_and_safe"

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return flaws, remediations, stability_score, security_risk, flaw_type

        class CodeVisitor(ast.NodeVisitor):
            def __init__(self):
                self.in_loop = 0
                self.has_sqli = False
                self.has_missing_timeout = False
                self.has_n_plus_one = False
                self.has_unclosed_open = False
                self.open_in_with = set()
                self.all_open_calls = []

            def visit_With(self, node):
                for item in node.items:
                    if isinstance(item.context_expr, ast.Call):
                        func = item.context_expr.func
                        if isinstance(func, ast.Name) and func.id == "open":
                            self.open_in_with.add(item.context_expr)
                self.generic_visit(node)

            def visit_AsyncWith(self, node):
                for item in node.items:
                    if isinstance(item.context_expr, ast.Call):
                        func = item.context_expr.func
                        if isinstance(func, ast.Name) and func.id == "open":
                            self.open_in_with.add(item.context_expr)
                self.generic_visit(node)

            def visit_For(self, node):
                self.in_loop += 1
                self.generic_visit(node)
                self.in_loop -= 1

            def visit_While(self, node):
                self.in_loop += 1
                self.generic_visit(node)
                self.in_loop -= 1

            def visit_JoinedStr(self, node):
                # Phát hiện bất kỳ f-string nào chứa từ khóa SQL nối biến trực tiếp
                text_chunks = []
                for val in node.values:
                    if isinstance(val, ast.Constant) and isinstance(val.value, str):
                        text_chunks.append(val.value)
                combined = " ".join(text_chunks).upper()
                if any(k in combined for k in ["SELECT", "INSERT INTO", "UPDATE", "DELETE FROM"]):
                    # Có ít nhất 1 biểu thức biến được ghép vào f-string
                    if any(not isinstance(val, ast.Constant) for val in node.values):
                        self.has_sqli = True
                self.generic_visit(node)

            def visit_Call(self, node):
                func_name = self._get_call_name(node.func)
                
                # 1. N+1 Query: Gọi DB trong vòng lặp
                if self.in_loop > 0 and func_name:
                    if any(term in func_name.lower() for term in [
                        "execute", "query", "filter_by", "find_one", "objects.get", "objects.filter"
                    ]):
                        self.has_n_plus_one = True

                # 2. SQLi qua execute()
                if func_name and any(term in func_name.lower() for term in ["execute", "raw_query"]):
                    if node.args:
                        first_arg = node.args[0]
                        if isinstance(first_arg, ast.JoinedStr):
                            self.has_sqli = True
                        elif isinstance(first_arg, ast.BinOp) and isinstance(first_arg.op, (ast.Mod, ast.Add)):
                            self.has_sqli = True

                # 3. Missing Timeout khi gọi HTTP
                if func_name and any(func_name.startswith(pfx) for pfx in [
                    "requests.get", "requests.post", "requests.put", "requests.delete",
                    "urllib.request.urlopen", "session.get", "session.post"
                ]):
                    has_timeout = any(kw.arg == "timeout" for kw in node.keywords)
                    if not has_timeout:
                        self.has_missing_timeout = True

                # 4. Ghi nhận open() để kiểm tra xem có trong with không
                if func_name == "open":
                    self.all_open_calls.append(node)

                self.generic_visit(node)

            def _get_call_name(self, func_node) -> Optional[str]:
                if isinstance(func_node, ast.Name):
                    return func_node.id
                elif isinstance(func_node, ast.Attribute):
                    val = self._get_call_name(func_node.value)
                    return f"{val}.{func_node.attr}" if val else func_node.attr
                return None

        visitor = CodeVisitor()
        try:
            visitor.visit(tree)
        except Exception:
            pass

        # Kiểm tra unclosed open()
        for c in visitor.all_open_calls:
            if c not in visitor.open_in_with:
                visitor.has_unclosed_open = True
                break

        # Đánh giá kết quả từ AST
        if visitor.has_sqli:
            security_risk = True
            stability_score = max(stability_score, 9.0)
            flaw_type = "dependency_or_security_flaw"
            flaws.append("[Lỗ hổng SQLi] Phát hiện nối chuỗi trực tiếp (f-string / concat) trong câu lệnh execute().")
            remediations.append("Sử dụng Parameterized Query: cursor.execute('SELECT * FROM tbl WHERE id = %s', (val,))")

        if visitor.has_n_plus_one:
            stability_score = max(stability_score, 8.0)
            flaw_type = "resource_leak_or_dos_risk"
            flaws.append("[N+1 Query Issue] Phát hiện truy vấn cơ sở dữ liệu lặp đi lặp lại bên trong vòng lặp.")
            remediations.append("Sử dụng Eager Loading, JOIN, hoặc IN query (select_related, prefetch_related).")

        if visitor.has_missing_timeout:
            stability_score = max(stability_score, 7.5)
            flaw_type = "resource_leak_or_dos_risk"
            flaws.append("[Thiếu Network Timeout] Gọi API mạng qua HTTP không cấu hình tham số 'timeout'.")
            remediations.append("Thêm tham số timeout rõ ràng (ví dụ: timeout=5.0) để ngăn cạn kiệt luồng kết nối.")

        if visitor.has_unclosed_open:
            stability_score = max(stability_score, 7.5)
            flaw_type = "resource_leak_or_dos_risk"
            flaws.append("[Nguy cơ Rò rỉ Tài nguyên] Mở tệp bằng open() không dùng khối 'with' có thể gây cạn kiệt File Descriptor.")
            remediations.append("Sử dụng 'with open(...) as f:' để tài nguyên luôn được giải phóng tự động.")

        return flaws, remediations, stability_score, security_risk, flaw_type

    def _polyglot_regex_inspect(self, code: str) -> Tuple[List[str], List[str], float, bool, str]:
        """Kiểm tra quy tắc Heuristics đa ngôn ngữ qua biểu thức chính quy."""
        flaws = []
        remediations = []
        stability_score = 1.0
        security_risk = False
        flaw_type = "clean_and_safe"

        # 1. SQL Injection trong đa ngôn ngữ (JS, Go, PHP, Java, Python f-string SQL)
        sqli_patterns = [
            (
                r"(?i)f\"[^\"]*(?:SELECT|INSERT|UPDATE|DELETE)\b[^\"]*\{.+?\}[^\"]*\"",
                "Ghép biến trực tiếp vào chuỗi truy vấn SQL bằng f-string (nháy kép)."
            ),
            (
                r"(?i)f'[^']*(?:SELECT|INSERT|UPDATE|DELETE)\b[^']*\{.+?\}[^']*'",
                "Ghép biến trực tiếp vào chuỗi truy vấn SQL bằng f-string (nháy đơn)."
            ),
            (
                r"(?i)(?:query|execute|raw)\s*\(\s*['\"][^'\"]*WHERE[^'\"]*=\s*['\"]\s*\+",
                "Nối chuỗi truy vấn SQL bằng toán tử '+'."
            ),
            (
                r"(?i)(?:query|execute)\s*\(\s*`[^`]*\$\{.+?\}[^`]*`\s*\)",
                "Ghép biến trực tiếp vào Template String SQL trong JavaScript/TypeScript."
            ),
            (
                r"(?i)db\.Query\s*\(\s*fmt\.Sprintf\s*\(",
                "Ghép chuỗi SQL qua fmt.Sprintf() trong Go."
            )
        ]
        for pat, desc in sqli_patterns:
            if re.search(pat, code):
                security_risk = True
                stability_score = max(stability_score, 9.0)
                flaw_type = "dependency_or_security_flaw"
                flaws.append(f"[SQL Injection Đa ngôn ngữ] {desc}")
                remediations.append("Chuyển sang Prepared Statement hoặc Parameterized Binding.")

        # 2. Missing Timeout trong JavaScript fetch & axios
        if re.search(r"(?i)\bfetch\s*\([^,)]+\)(?![\s\S]*?signal\b)", code):
            stability_score = max(stability_score, 6.0)
            flaws.append("[Thiếu Network Timeout] Hàm fetch() không sử dụng AbortController hoặc timeout signal.")
            remediations.append("Truyền { signal: AbortSignal.timeout(5000) } vào fetch().")

        # 3. Race Condition & Mutex Check
        if re.search(r"(?i)(?:threading\.Thread|asyncio\.create_task|go\s+func)", code):
            if re.search(r"(?i)\bglobal\s+[a-zA-Z0-9_]+", code) and not re.search(r"(?i)(?:Lock|Mutex|Semaphore)", code):
                stability_score = max(stability_score, 8.0)
                flaw_type = "broken_logic_or_race_condition"
                flaws.append("[Race Condition] Sửa đổi biến toàn cục trong đa luồng / async mà không có cơ chế Lock.")
                remediations.append("Sử dụng threading.Lock() hoặc asyncio.Lock() khi truy cập tài nguyên chia sẻ.")

        # 4. Dangerous Command Execution in Code (Command Injection)
        if re.search(r"(?i)(?:os\.system|subprocess\.call|child_process\.exec)\s*\(\s*f?['\"][^'\"]*\{.+?\}", code):
            security_risk = True
            stability_score = max(stability_score, 9.5)
            flaw_type = "dependency_or_security_flaw"
            flaws.append("[Lỗ hổng Command Injection] Thực thi lệnh hệ điều hành với tham số chưa được escape.")
            remediations.append("Dùng subprocess.run(['cmd', arg], check=True) thay vì ghép chuỗi shell thô.")

        return flaws, remediations, stability_score, security_risk, flaw_type

    # =========================================================================
    # GHI AUDIT TRAIL LOG
    # =========================================================================

    def _record_audit_mode1(self, text: str, channel: str, res: PromptCheckResult) -> None:
        """Ghi sự kiện Mode 1 vào audit log."""
        advisory = self.predict_architecture_advisory(text)
        jev_response = res.to_dict()
        if advisory:
            jev_response["predicted_edge_cases"] = advisory.to_dict()

        self.logger.log_event(
            event_type="prompt_and_action_check",
            channel=channel,
            verdict=res.action_verdict,
            risk_score=res.destructive_intent_score,
            details={
                "has_credential_leak": res.has_credential_leak,
                "engine_source": res.engine_source,
                "issues": res.details,
                "remediation": res.remediation,
                "predicted_edge_cases": advisory.to_dict() if advisory else None,
                "jev_response": jev_response,
            },
            raw_snippet=text
        )

    def _record_audit_mode2(
        self,
        code: str,
        file_path: Optional[str],
        channel: str,
        res: CodeCheckResult
    ) -> None:
        """Ghi sự kiện Mode 2 vào audit log."""
        jev_response = res.to_dict()
        self.logger.log_event(
            event_type="code_health_check",
            channel=channel,
            verdict=res.maintainability_verdict,
            risk_score=res.production_stability_score,
            details={
                "file_path": file_path,
                "future_security_risk": res.future_security_risk,
                "architecture_flaw_type": res.architecture_flaw_type,
                "leak_risk": res.leak_risk,
                "detected_flaws": res.detected_flaws,
                "remediation_suggestions": res.remediation_suggestions,
                "engine_source": res.engine_source,
                "jev_response": jev_response,
            },
            raw_snippet=code
        )
