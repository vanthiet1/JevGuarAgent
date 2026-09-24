
import os
import sys
import shutil
import argparse
import json
from pathlib import Path
from typing import List, Optional

from jog.config import load_config
from jog.logger import JogLogger, get_logger
from jog.jev_engine import JevEngine, PromptCheckResult

def find_real_binary(binary_name: str, skip_dir: Optional[str] = None) -> Optional[str]:
    env_override = os.environ.get(f"JOG_REAL_{binary_name.upper()}_BIN")
    if env_override and os.path.isfile(env_override) and os.access(env_override, os.X_OK):
        return env_override

    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    resolved_skip = os.path.abspath(skip_dir) if skip_dir else None

    for d in path_dirs:
        if not d:
            continue
        abs_d = os.path.abspath(d)
        if resolved_skip and abs_d == resolved_skip:
            continue

        if ".jog/bin" in abs_d or abs_d.endswith("/JevGuarAgent/bin"):
            continue

        candidate = os.path.join(abs_d, binary_name)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    return None

def extract_prompt_from_args(args: List[str]) -> str:
    if not args:
        return ""

    return " ".join(args)

def run_cli_interceptor(target_binary: str, raw_args: List[str]) -> int:
    config = load_config()
    logger = get_logger(config.logging.audit_log_file)
    engine = JevEngine(config)

    prompt_text = extract_prompt_from_args(raw_args)

    piped_stdin = ""
    if not sys.stdin.isatty():
        try:
            piped_stdin = sys.stdin.read()
            if piped_stdin.strip():
                prompt_text = f"{prompt_text}\n{piped_stdin}".strip()
        except Exception:
            pass

    if not prompt_text:

        this_dir = str(Path(__file__).resolve().parent.parent / "bin")
        real_bin = find_real_binary(target_binary, skip_dir=this_dir)
        if real_bin:
            JogLogger.print_safe_pass("CLI", f"Bắt đầu phiên làm việc an toàn với {target_binary}")
            os.execv(real_bin, [real_bin] + raw_args)
        else:
            JogLogger.print_banner()
            print(f"[JOG CLI] Đã khởi tạo shim bảo vệ cho {target_binary}. Không phát hiện tham số nguy hiểm.")
            return 0

    try:
        current_cwd = os.getcwd()
    except (FileNotFoundError, OSError):
        current_cwd = os.environ.get("PWD", str(Path(__file__).resolve().parent.parent))

    result: PromptCheckResult = engine.check_prompt_and_action(
        prompt_or_command=prompt_text,
        channel=f"cli_{target_binary}",
        context={"target_binary": target_binary, "cwd": current_cwd}
    )

    if result.action_verdict == "block_immediately":

        JogLogger.print_block_alert(
            title=f"Lệnh gọi '{target_binary}' bị chặn do vi phạm chính sách an toàn",
            reason="\n".join(f"  • {item}" for item in result.details),
            remediation=result.remediation
        )
        print("\033[36m\033[1m[JEV ENGINE JSON PHẢN HỒI]:\033[0m", file=sys.stderr)
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), file=sys.stderr)
        return 1

    elif result.action_verdict == "warn_user":

        JogLogger.print_warn_alert(
            title=f"Phát hiện thao tác tiềm ẩn rủi ro khi chạy '{target_binary}'",
            warnings=result.details
        )
        print("\033[33m\033[1m[JEV ENGINE JSON PHẢN HỒI]:\033[0m", file=sys.stderr)
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), file=sys.stderr)
        

        if config.cli.require_confirmation_on_warn:
            try:
                prompt_msg = "\033[33m\033[1m[?] Bạn có chắc chắn muốn cho phép thực thi lệnh này không? [y/N]: \033[0m"
                choice = input(prompt_msg).strip().lower()
                if choice not in ["y", "yes"]:
                    print("\033[31m[JOG CLI] Thao tác đã bị người dùng hủy bỏ (Aborted).\033[0m", file=sys.stderr)
                    return 130
            except (KeyboardInterrupt, EOFError):
                print("\n\033[31m[JOG CLI] Nhận tín hiệu ngắt. Hủy thực thi.\033[0m", file=sys.stderr)
                return 130

    this_dir = str(Path(__file__).resolve().parent.parent / "bin")
    real_bin = find_real_binary(target_binary, skip_dir=this_dir)

    if real_bin:

        os.execv(real_bin, [real_bin] + raw_args)
    else:

        JogLogger.print_safe_pass("CLI", f"Lệnh an toàn (Kiểm tra hoàn tất). Điểm phá hoại: {result.destructive_intent_score}/10")
        if os.environ.get("JOG_TEST_MODE") == "1":
            print(f"[JOG TEST MODE] Cho phép chạy: {target_binary} {' '.join(raw_args)}")
        return 0

def main():
    parser = argparse.ArgumentParser(
        description="JOG CLI Interceptor - Đánh chặn và bảo vệ lệnh thực thi của AI Agent"
    )
    parser.add_argument(
        "--target",
        type=str,
        default="bash",
        help="Tên binary gốc cần bảo vệ (claude, codex, gemini, bash...)"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Chỉ kiểm tra chuỗi lệnh mà không chuyển tiếp sang binary thật"
    )
    parser.add_argument(
        "cmd_args",
        nargs=argparse.REMAINDER,
        help="Tham số và lệnh truyền cho binary"
    )

    args = parser.parse_args()

    passed_args = args.cmd_args
    if passed_args and passed_args[0] == "--":
        passed_args = passed_args[1:]

    if args.check_only:
        config = load_config()
        engine = JevEngine(config)
        prompt = " ".join(passed_args)
        res = engine.check_prompt_and_action(prompt, channel="cli_check")
        print(f"Verdict: {res.action_verdict}")
        print(f"Destructive Score: {res.destructive_intent_score}")
        print(f"Credential Leak: {res.has_credential_leak}")
        for d in res.details:
            print(f" - {d}")
        sys.exit(0 if res.action_verdict == "allow" else (1 if res.action_verdict == "block_immediately" else 2))

    sys.exit(run_cli_interceptor(args.target, passed_args))

if __name__ == "__main__":
    main()
