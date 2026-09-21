#!/usr/bin/env bash
# =============================================================================
# uninstall.sh
# Kịch bản gỡ bỏ Jev Omnichannel Guardrail (JOG) sạch sẽ.
# =============================================================================
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Đang gỡ bỏ JOG khỏi hệ thống..."

# 1. Hủy kích hoạt Guardrail khỏi dự án mục tiêu (IDE rules & Git hooks)
python3 "$PROJECT_DIR/bin/jog" deactivate || true


# 2. Xóa cấu hình PATH trong shell rc
SHELL_RC="$HOME/.bashrc"
if [ -f "$SHELL_RC" ]; then
    sed -i "\|$PROJECT_DIR/bin|d" "$SHELL_RC" 2>/dev/null || true
    sed -i "\|alias jog=|d" "$SHELL_RC" 2>/dev/null || true
    sed -i "\|# === Jev Omnichannel Guardrail|d" "$SHELL_RC" 2>/dev/null || true
    echo "✓ Đã xóa cấu hình khỏi $SHELL_RC."
fi

echo "✓ Gỡ bỏ hoàn tất!"
