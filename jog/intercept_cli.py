
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

def is_jog_shim(path: str) -> bool:
    try:
        resolved = os.path.realpath(path)
        resolved_norm = resolved.replace("\\", "/")
        if "JevGuarAgent" in resolved_norm or ".jog" in resolved_norm:
            return True
        with open(path, "rb") as f:
            head = f.read(1024).decode("utf-8", errors="ignore")
            if "guar.py" in head or "bin/jog" in head or "JevGuarAgent" in head or "JOG CLI" in head:
                return True
    except Exception:
        pass
    return False

def find_real_binary(binary_name: str, skip_dir: Optional[str] = None) -> Optional[str]:
    env_override = os.environ.get(f"JOG_REAL_{binary_name.upper()}_BIN")
    if env_override and os.path.isfile(env_override) and not is_jog_shim(env_override):
        return env_override

    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    resolved_skip = os.path.abspath(skip_dir) if skip_dir else None

    for d in path_dirs:
        if not d:
            continue
        abs_d = os.path.abspath(d)
        if resolved_skip and abs_d == resolved_skip:
            continue

        norm_d = abs_d.replace("\\", "/")
        if ".jog/bin" in norm_d or norm_d.endswith("/JevGuarAgent/bin"):
            continue

        candidate = shutil.which(binary_name, path=abs_d)
        if candidate and os.path.isfile(candidate):
            if is_jog_shim(candidate):
                continue
            return candidate

    return None

def extract_prompt_from_args(args: List[str]) -> str:
    if not args:
        return ""

    return " ".join(args)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        os.system("")
    except Exception:
        pass

def spawn_real_binary(real_bin: str, args: List[str]) -> int:
    if sys.platform == "win32":
        import subprocess
        if real_bin.lower().endswith(".ps1"):
            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", real_bin] + args
            return subprocess.call(cmd)
        is_script = real_bin.lower().endswith((".cmd", ".bat"))
        return subprocess.call([real_bin] + args, shell=is_script)
    else:
        os.execv(real_bin, [real_bin] + args)

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
            return spawn_real_binary(real_bin, raw_args)
        else:
            JogLogger.print_safe_pass("CLI", "Đã trả kết quả: đang phân tích và thực thi... (Điểm rủi ro: 1.0/10 - An toàn)")
            print(f"[JOG CLI] Đã khởi tạo phiên làm việc cho '{target_binary}'. Chưa cài đặt binary gốc trên hệ thống.")
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
        score = result.destructive_intent_score
        desc = "An toàn" if score <= 3.0 else ("Cảnh báo" if score <= 6.9 else "Cực kỳ nghiêm trọng")
        leak_vi = "Có" if result.has_credential_leak else "Không"
        remediation_vi = result.remediation if result.remediation else "Không có"

        print("\n\033[36m\033[1m[KẾT QUẢ ĐÁNH GIÁ TỪ JEV GUARDRAIL]:\033[0m", file=sys.stderr)
        print("1 - Kết luận hành động: Chặn ngay lập tức", file=sys.stderr)
        print(f"2 - Điểm số ý định phá hoại: {score}/10 ({desc})", file=sys.stderr)
        print(f"3 - Phát hiện lộ bí mật / API Key: {leak_vi}", file=sys.stderr)
        print(f"4 - Nguồn thẩm định: {result.engine_source}", file=sys.stderr)
        print("5 - Chi tiết phân tích:", file=sys.stderr)
        for d in result.details:
            print(f"    • {d}", file=sys.stderr)
        print(f"6 - Hướng dẫn sửa đổi: {remediation_vi}\n", file=sys.stderr)
        return 1

    elif result.action_verdict == "warn_user":

        JogLogger.print_warn_alert(
            title=f"Phát hiện thao tác tiềm ẩn rủi ro khi chạy '{target_binary}'",
            warnings=result.details
        )
        score = result.destructive_intent_score
        desc = "An toàn" if score <= 3.0 else ("Cảnh báo" if score <= 6.9 else "Cực kỳ nghiêm trọng")
        leak_vi = "Có" if result.has_credential_leak else "Không"
        remediation_vi = result.remediation if result.remediation else "Không có"

        print("\n\033[33m\033[1m[KẾT QUẢ ĐÁNH GIÁ TỪ JEV GUARDRAIL]:\033[0m", file=sys.stderr)
        print("1 - Kết luận hành động: Cảnh báo rủi ro", file=sys.stderr)
        print(f"2 - Điểm số ý định phá hoại: {score}/10 ({desc})", file=sys.stderr)
        print(f"3 - Phát hiện lộ bí mật / API Key: {leak_vi}", file=sys.stderr)
        print(f"4 - Nguồn thẩm định: {result.engine_source}", file=sys.stderr)
        print("5 - Chi tiết phân tích:", file=sys.stderr)
        for d in result.details:
            print(f"    • {d}", file=sys.stderr)
        print(f"6 - Hướng dẫn sửa đổi: {remediation_vi}\n", file=sys.stderr)
        

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

    score = result.destructive_intent_score
    desc = "An toàn" if score <= 3.0 else ("Cảnh báo" if score <= 6.9 else "Cực kỳ nghiêm trọng")
    JogLogger.print_safe_pass("CLI", f"Đã trả kết quả: đang phân tích và thực thi... (Điểm rủi ro: {score}/10 - {desc})")

    this_dir = str(Path(__file__).resolve().parent.parent / "bin")
    real_bin = find_real_binary(target_binary, skip_dir=this_dir)

    if real_bin:
        return spawn_real_binary(real_bin, raw_args)
    else:
        if os.environ.get("JOG_TEST_MODE") == "1":
            print(f"[JOG TEST MODE] Cho phép chạy: {target_binary} {' '.join(raw_args)}")
        else:
            print(f"[JOG CLI] Lệnh '{target_binary}' đã được bảo vệ. (Chưa cài đặt binary gốc trên hệ thống).")
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
