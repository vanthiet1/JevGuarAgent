
import os
import sys
import fnmatch
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

from jog.config import JogConfig, load_config
from jog.logger import JogLogger, get_logger
from jog.jev_engine import JevEngine, CodeCheckResult, PromptCheckResult


MAX_SCAN_FILE_SIZE = 5 * 1024 * 1024

def run_git_cmd(args: List[str], timeout: float = 10.0) -> Tuple[int, str]:
    try:
        proc = subprocess.run(
            ["git"] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False
        )
        return proc.returncode, proc.stdout
    except Exception as e:
        return -1, str(e)

def get_staged_files() -> List[Tuple[str, str]]:
    code, output = run_git_cmd(["diff", "--cached", "--name-status"], timeout=10.0)
    if code != 0 or not output.strip():
        return []

    files = []
    for line in output.strip().splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            status, path = parts[0], parts[1]
            if status != "D":

                if "\t" in path:
                    path = path.split("\t")[-1]
                files.append((status, path))
    return files

def get_staged_content(file_path: str) -> Optional[str]:
    try:
        if os.path.exists(file_path) and os.path.getsize(file_path) > MAX_SCAN_FILE_SIZE:
            return None
    except Exception:
        pass
    code, content = run_git_cmd(["show", f":{file_path}"], timeout=15.0)
    return content if code == 0 else None

def get_staged_diff(file_path: str) -> str:
    code, diff = run_git_cmd(["diff", "--cached", "-U0", "--", file_path], timeout=15.0)
    return diff if code == 0 else ""

def execute_pre_commit_guard() -> int:
    config: JogConfig = load_config()
    logger = get_logger(config.logging.audit_log_file)
    engine = JevEngine(config)

    staged_files = get_staged_files()
    if not staged_files:

        return 0

    has_violation = False
    violations_summary: List[Dict[str, Any]] = []

    print(f"\n🛡️  [JOG GIT GUARD] Đang quét an toàn {len(staged_files)} tệp chuẩn bị commit...", file=sys.stderr)

    ignored_patterns = getattr(config.git_hook, "ignored_paths", ["tests/*", "*.md", "demo.sh", "bin/*", "*.bat", "*.cmd", "*.ps1"])

    for status, file_path in staged_files:
        file_basename = os.path.basename(file_path).lower()

        is_ignored = any(
            fnmatch.fnmatch(file_path, pat) or fnmatch.fnmatch(file_basename, pat)
            for pat in ignored_patterns
        )

        is_safe_template = file_basename in [".env.example", ".env.sample", ".env.template"] or file_basename.endswith((".example", ".sample", ".template"))
        sensitive_files = getattr(config.git_hook, "sensitive_filenames", [])
        if not is_safe_template:
            if any(file_basename == s.lower() for s in sensitive_files) or file_basename.startswith(".env"):
                has_violation = True
                violations_summary.append({
                    "file": file_path,
                    "reason": "Phát hiện tệp bí mật nguy hiểm cấm commit (.env / Private Key / Credentials).",
                    "leak_risk": 1.0,
                    "stability_score": 10.0,
                    "flaws": [f"Tệp '{file_path}' nằm trong danh mục cấm đưa lên Git."],
                    "remediations": [f"Chạy lệnh: git reset HEAD {file_path} và thêm vào file .gitignore."]
                })
                continue

        if is_ignored:
            continue

        staged_content = get_staged_content(file_path)
        if staged_content is None:
            continue

        diff_content = get_staged_diff(file_path)

        diff_mode1 = engine.check_prompt_and_action(diff_content, channel="git_hook_diff")
        code_mode2 = engine.check_code_health(staged_content, file_path=file_path, channel="git_hook_code")

        leak_risk = 1.0 if diff_mode1.has_credential_leak else code_mode2.leak_risk
        stability_score = code_mode2.production_stability_score

        leak_threshold = config.git_hook.leak_risk_threshold
        stability_threshold = config.git_hook.production_stability_threshold

        is_file_rejected = False
        rejection_reasons = []

        if leak_risk > leak_threshold:
            is_file_rejected = True
            rejection_reasons.append(f"Nguy cơ rò rỉ bí mật vượt ngưỡng an toàn (leak_risk: {leak_risk} > {leak_threshold}).")

        if stability_score >= stability_threshold:
            is_file_rejected = True
            rejection_reasons.append(f"Nguy cơ sập hệ thống trong tương lai (stability_score: {stability_score} >= {stability_threshold}).")

        if code_mode2.maintainability_verdict == "reject_force_agent_rewrite":
            is_file_rejected = True
            if not rejection_reasons:
                rejection_reasons.append("Phán quyết từ chối từ JevEngine (reject_force_agent_rewrite).")

        if is_file_rejected:
            has_violation = True
            all_flaws = list(diff_mode1.details) + list(code_mode2.detected_flaws)
            violations_summary.append({
                "file": file_path,
                "reason": " | ".join(rejection_reasons),
                "leak_risk": leak_risk,
                "stability_score": stability_score,
                "flaws": all_flaws,
                "remediations": code_mode2.remediation_suggestions or [diff_mode1.remediation or "Sửa đổi mã nguồn trước khi commit."]
            })

    if has_violation:
        print("\n" + "=" * 75, file=sys.stderr)
        print("🚨 [JOG GIT GUARDRAIL] COMMIT BỊ CHẶN VÌ KHÔNG ĐẠT TIÊU CHUẨN AN TOÀN!", file=sys.stderr)
        print("=" * 75, file=sys.stderr)

        for v in violations_summary:
            print(f"\n❌ TỆP VI PHẠM: {v['file']}", file=sys.stderr)
            print(f"   • Lý do chặn : {v['reason']}", file=sys.stderr)
            print(f"   • Leak Risk   : {v['leak_risk']} (Ngưỡng tối đa: {config.git_hook.leak_risk_threshold})", file=sys.stderr)
            print(f"   • Stability   : {v['stability_score']}/10 (Ngưỡng tối đa: {config.git_hook.production_stability_threshold})", file=sys.stderr)
            print("   • Chi tiết lỗi phát hiện:", file=sys.stderr)
            for f in v["flaws"]:
                print(f"       - {f}", file=sys.stderr)
            print("   💡 Hướng dẫn sửa đổi cho Agent / Dev:", file=sys.stderr)
            for r in v["remediations"]:
                print(f"       -> {r}", file=sys.stderr)

        print("\n" + "=" * 75, file=sys.stderr)
        print("🚫 Thao tác git commit đã bị hủy bỏ an toàn.", file=sys.stderr)
        print("=" * 75 + "\n", file=sys.stderr)

        logger.log_event(
            event_type="git_commit_block",
            channel="git_hook",
            verdict="block",
            risk_score=max(v["stability_score"] for v in violations_summary),
            details={"blocked_files": [v["file"] for v in violations_summary]}
        )
        return 1

    JogLogger.print_safe_pass("GIT", "Tất cả các tệp staged đều vượt qua kiểm tra an toàn.")
    return 0

def main():
    sys.exit(execute_pre_commit_guard())

if __name__ == "__main__":
    main()
