"""
jog/config.py
==============
Mô-đun quản lý cấu hình tập trung cho toàn bộ hệ thống Jev Omnichannel Guardrail.
Hỗ trợ nạp cấu hình từ file JSON mặc định, file tùy chỉnh của người dùng,
và ưu tiên ghi đè bằng các biến môi trường (Environment Variables).
"""

import os
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any


def safe_getcwd() -> Path:
    """Trả về thư mục làm việc an toàn, tự động xử lý khi thư mục hiện tại bị xóa."""
    try:
        return Path(os.getcwd()).resolve()
    except (FileNotFoundError, OSError):
        pwd = os.environ.get("PWD")
        if pwd and os.path.exists(pwd):
            return Path(pwd).resolve()
        return Path(__file__).resolve().parent.parent


@dataclass
class ApiConfig:
    """Cấu hình kết nối tới TypeSafe AI hoặc OpenRouter API."""
    typesafe_api_url: str = "https://api.typesafe.ai/v1/systemone"
    typesafe_api_key: Optional[str] = None
    timeout_seconds: float = 3.0
    enable_offline_fallback: bool = True
    model: str = "deepseek/deepseek-chat" 




@dataclass
class GitHookConfig:
    """Cấu hình ngưỡng phát hiện cho Git Pre-commit Hook."""
    leak_risk_threshold: float = 0.6
    production_stability_threshold: float = 7.5
    block_on_reject_verdict: bool = True
    ignored_paths: list = field(default_factory=lambda: ["tests/*", "*.md", "demo.sh", "test_*.sh"])


@dataclass
class CliConfig:
    """Cấu hình xử lý cho CLI Interceptor & Shims."""
    require_confirmation_on_warn: bool = True
    auto_abort_on_block: bool = True


@dataclass
class LoggingConfig:
    """Cấu hình lưu vết kiểm toán (Audit Trail Logging)."""
    audit_log_file: str = ".jog/logs/audit.log"
    log_level: str = "INFO"


@dataclass
class JogConfig:
    """Cấu hình tổng hợp của hệ thống JOG."""
    api: ApiConfig = field(default_factory=ApiConfig)
    git_hook: GitHookConfig = field(default_factory=GitHookConfig)
    cli: CliConfig = field(default_factory=CliConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    base_dir: Path = field(default_factory=safe_getcwd)

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi cấu hình sang dạng dictionary."""
        return {
            "api": {
                "typesafe_api_url": self.api.typesafe_api_url,
                "typesafe_api_key": "***" if self.api.typesafe_api_key else None,
                "timeout_seconds": self.api.timeout_seconds,
                "enable_offline_fallback": self.api.enable_offline_fallback,
            },
            "git_hook": {
                "leak_risk_threshold": self.git_hook.leak_risk_threshold,
                "production_stability_threshold": self.git_hook.production_stability_threshold,
                "block_on_reject_verdict": self.git_hook.block_on_reject_verdict,
            },
            "cli": {
                "require_confirmation_on_warn": self.cli.require_confirmation_on_warn,
                "auto_abort_on_block": self.cli.auto_abort_on_block,
            },
            "logging": {
                "audit_log_file": self.logging.audit_log_file,
                "log_level": self.logging.log_level,
            }
        }


def find_config_file(custom_path: Optional[str] = None) -> Optional[Path]:
    """
    Tìm file cấu hình theo thứ tự ưu tiên:
    1. Đường dẫn tùy chỉnh do tham số truyền vào
    2. Biến môi trường $JOG_CONFIG_PATH
    3. File .jog_config.json tại thư mục hiện tại
    4. File config/jog_config.json trong cây mã nguồn
    5. ~/.jog/jog_config.json trong thư mục home
    """
    candidates = []
    if custom_path:
        candidates.append(Path(custom_path))
    if os.environ.get("JOG_CONFIG_PATH"):
        candidates.append(Path(os.environ["JOG_CONFIG_PATH"]))
    
    current_dir = safe_getcwd()
    candidates.append(current_dir / ".jog_config.json")
    candidates.append(current_dir / "config" / "jog_config.json")
    
    module_dir = Path(__file__).resolve().parent.parent
    candidates.append(module_dir / "config" / "jog_config.json")
    candidates.append(Path.home() / ".jog" / "jog_config.json")

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def get_git_root() -> Optional[Path]:
    """Tìm thư mục gốc của Git repository hiện tại (nếu đang trong một repo)."""
    try:
        import subprocess
        proc = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return Path(proc.stdout.strip()).resolve()
    except Exception:
        pass
    return None


def load_env_files(search_dirs: Optional[list] = None) -> Dict[str, str]:
    """
    Tự động tìm kiếm và nạp các tệp biến môi trường (.env, .env.local, .env.development, .env.production).
    Hỗ trợ tìm kiếm thông minh từ:
      1. Thư mục làm việc hiện tại của người dùng (Path.cwd())
      2. Thư mục gốc Git của dự án người dùng (Git Root của source dự án họ)
      3. Thư mục cài đặt JOG Core
      4. Thư mục cấu hình cá nhân (~/.jog)
    Thứ tự ưu tiên nạp đè: .env.local > .env.development > .env
    Tự động export vào os.environ để toàn bộ tiến trình hệ thống đọc được.
    """
    if search_dirs is None:
        search_dirs = [safe_getcwd()]
        
        # Tự động phát hiện thư mục gốc của repository dự án mà dev đang làm việc
        git_root = get_git_root()
        if git_root and git_root not in search_dirs:
            search_dirs.append(git_root)
            
        jog_core = Path(__file__).resolve().parent.parent
        if jog_core not in search_dirs:
            search_dirs.append(jog_core)
            
        search_dirs.append(Path.home() / ".jog")

    env_names = [".env", ".env.development", ".env.production", ".env.local"]
    merged_vars: Dict[str, str] = {}

    for d in search_dirs:
        if not d or not d.exists():
            continue
        for name in env_names:
            env_path = d / name
            if env_path.is_file():
                try:
                    with open(env_path, "r", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith("#"):
                                continue
                            if "=" in line:
                                k, v = line.split("=", 1)
                                k, v = k.strip(), v.strip()
                                if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                                    v = v[1:-1]
                                merged_vars[k] = v
                                # Đưa vào os.environ nếu chưa được set thủ công từ trước
                                if k not in os.environ or not os.environ[k]:
                                    os.environ[k] = v
                except Exception:
                    pass

    return merged_vars


def load_config(config_path: Optional[str] = None) -> JogConfig:
    """
    Nạp cấu hình và hợp nhất (merge) các giá trị theo thứ tự:
    Mặc định -> File .env/.env.local -> File JSON -> Biến môi trường hệ thống.
    """
    # 1. Tự động nạp toàn bộ các file .env / .env.local nếu có
    env_vars = load_env_files()

    config = JogConfig()
    cfg_file = find_config_file(config_path)

    if cfg_file and cfg_file.exists():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Nạp ApiConfig
                api_data = data.get("api", {})
                if "typesafe_api_url" in api_data:
                    config.api.typesafe_api_url = str(api_data["typesafe_api_url"])
                if "typesafe_api_key" in api_data and api_data["typesafe_api_key"]:
                    config.api.typesafe_api_key = str(api_data["typesafe_api_key"])
                if "timeout_seconds" in api_data:
                    config.api.timeout_seconds = float(api_data["timeout_seconds"])
                if "enable_offline_fallback" in api_data:
                    config.api.enable_offline_fallback = bool(api_data["enable_offline_fallback"])


                # Nạp GitHookConfig
                hook_data = data.get("git_hook", {})
                if "leak_risk_threshold" in hook_data:
                    config.git_hook.leak_risk_threshold = float(hook_data["leak_risk_threshold"])
                if "production_stability_threshold" in hook_data:
                    config.git_hook.production_stability_threshold = float(hook_data["production_stability_threshold"])
                if "block_on_reject_verdict" in hook_data:
                    config.git_hook.block_on_reject_verdict = bool(hook_data["block_on_reject_verdict"])
                if "ignored_paths" in hook_data and isinstance(hook_data["ignored_paths"], list):
                    config.git_hook.ignored_paths = list(hook_data["ignored_paths"])

                # Nạp CliConfig
                cli_data = data.get("cli", {})
                if "require_confirmation_on_warn" in cli_data:
                    config.cli.require_confirmation_on_warn = bool(cli_data["require_confirmation_on_warn"])
                if "auto_abort_on_block" in cli_data:
                    config.cli.auto_abort_on_block = bool(cli_data["auto_abort_on_block"])

                # Nạp LoggingConfig
                log_data = data.get("logging", {})
                if "audit_log_file" in log_data:
                    config.logging.audit_log_file = str(log_data["audit_log_file"])
                if "log_level" in log_data:
                    config.logging.log_level = str(log_data["log_level"])
        except Exception as e:
            # Nếu có lỗi khi đọc file JSON, ghi nhận và tiếp tục với biến môi trường
            pass

    # Ghi đè bằng biến môi trường (Environment Variables có độ ưu tiên cao nhất)
    env_api_key = os.environ.get("TYPESAFE_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    if env_api_key:
        config.api.typesafe_api_key = env_api_key.strip()
    
    env_model = os.environ.get("JOG_LLM_MODEL")
    if env_model:
        config.api.model = env_model.strip()

    env_api_url = os.environ.get("TYPESAFE_API_URL")
    if env_api_url:
        config.api.typesafe_api_url = env_api_url.strip()


    env_audit_log = os.environ.get("JOG_AUDIT_LOG")
    if env_audit_log:
        config.logging.audit_log_file = env_audit_log.strip()

    return config
