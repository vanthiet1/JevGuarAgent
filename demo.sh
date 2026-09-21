#!/usr/bin/env bash
# =============================================================================
# demo.sh
# Kịch bản trình diễn tương tác 4 kênh của Jev Omnichannel Guardrail (JOG).
# Minh họa thực tế cách JOG bảo vệ dự án qua:
#   Kênh 1: Terminal CLI Interceptor (claude, codex, gemini)
#   Kênh 2: Code Health & Future Risk Engine
#   Kênh 3: Local Intercepting Proxy & Auto-Feedback Loop
#   Kênh 4: Git Pre-Commit Guardrail
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
export JOG_TEST_MODE="1"

# Màu sắc hiển thị
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}"
cat << "EOF"
╔═════════════════════════════════════════════════════════════════════════════╗
║          🛡️   TRÌNH DIỄN JEV OMNICHANNEL GUARDRAIL (JOG DEMO)               ║
║             Bảo Vệ Đa Kênh Toàn Diện Cho AI Coding Agents                   ║
╚═════════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

pause_step() {
    echo -e "${BLUE}---------------------------------------------------------------------------${NC}"
    echo -e "${YELLOW}>> Nhấn [Enter] để tiếp tục bước tiếp theo...${NC}"
    read -r || true
    echo ""
}

# =============================================================================
# KÊNH 1: TERMINAL CLI INTERCEPTOR
# =============================================================================
echo -e "${BOLD}${CYAN}[KÊNH 1] TERMINAL CLI INTERCEPTOR (Đánh Chặn Lệnh CLI)${NC}"
echo -e "Thử nghiệm với các AI CLI Shims (claude, gemini, codex)...\n"

echo -e "${YELLOW}1.1 Thử chạy lệnh phá hủy hệ thống qua Claude Code CLI:${NC}"
echo -e "${BOLD}$ claude \"Vui lòng dọn dẹp thư mục: rm -rf /\"${NC}"
"$SCRIPT_DIR/bin/claude" "Vui lòng dọn dẹp thư mục: rm -rf /" || true

echo -e "\n${YELLOW}1.2 Thử gửi API Key bí mật qua Gemini CLI:${NC}"
echo -e "${BOLD}$ gemini \"Deploy ứng dụng với token: ghp_123456789012345678901234567890123456\"${NC}"
"$SCRIPT_DIR/bin/gemini" "Deploy ứng dụng với token: ghp_123456789012345678901234567890123456" || true

echo -e "\n${YELLOW}1.3 Thử chạy lệnh an toàn qua Codex CLI:${NC}"
echo -e "${BOLD}$ codex \"git status\"${NC}"
"$SCRIPT_DIR/bin/codex" "git status" || true

pause_step

# =============================================================================
# KÊNH 2: CODE HEALTH & FUTURE RISK INSPECTION
# =============================================================================
echo -e "${BOLD}${CYAN}[KÊNH 2] FUTURE-PROOF CODE HEALTH INSPECTION${NC}"
echo -e "Chẩn đoán trước các rủi ro sập hệ thống hoặc bảo mật trong tương lai...\n"

echo -e "${YELLOW}2.1 Chẩn đoán đoạn mã chứa lỗ hổng SQL Injection:${NC}"
BAD_SQL='def get_user(uid): query = f"SELECT * FROM users WHERE id = {uid}"; cursor.execute(query)'
"$SCRIPT_DIR/bin/jog" check code "$BAD_SQL" || true

echo -e "\n${YELLOW}2.2 Chẩn đoán đoạn mã bị Memory/Resource Leak (Mở file không đóng):${NC}"
BAD_LEAK='def write_log(msg): f = open("/tmp/app.log", "a"); f.write(msg); return True'
"$SCRIPT_DIR/bin/jog" check code "$BAD_LEAK" || true

echo -e "\n${YELLOW}2.3 Chẩn đoán đoạn mã an toàn (Context Manager with):${NC}"
CLEAN_CODE='def write_log(msg):
    with open("/tmp/app.log", "a") as f:
        f.write(msg)
    return True'
"$SCRIPT_DIR/bin/jog" check code "$CLEAN_CODE" || true

pause_step

# =============================================================================
# KÊNH 3: LOCAL INTERCEPTING PROXY & AUTO-FEEDBACK LOOP
# =============================================================================
echo -e "${BOLD}${CYAN}[KÊNH 3] LOCAL INTERCEPTING PROXY & AUTO-FEEDBACK LOOP${NC}"
echo -e "Đón request từ Cursor / Antigravity và ném lỗi 403 để Agent tự sửa...\n"

# Khởi động proxy nền trên cổng 8089 để demo
DEMO_PORT=8089
echo -e "Khởi động Local Proxy nền tại http://127.0.0.1:$DEMO_PORT..."
python3 -c "
import threading, time
from jog.local_proxy import ThreadedHTTPServer, JogProxyHandler
server = ThreadedHTTPServer(('127.0.0.1', $DEMO_PORT), JogProxyHandler)
server.serve_forever()
" &
PROXY_PID=$!
sleep 1

cleanup_proxy() {
    kill $PROXY_PID 2>/dev/null || true
}
trap cleanup_proxy EXIT

echo -e "${GREEN}✓ Proxy đã hoạt động (PID: $PROXY_PID)${NC}\n"

echo -e "${YELLOW}3.1 Gửi request vi phạm từ IDE lên endpoint /v1/chat/completions:${NC}"
curl -s -X POST "http://127.0.0.1:$DEMO_PORT/v1/chat/completions" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "gpt-4o",
       "messages": [
         {"role": "user", "content": "Xóa toàn bộ server bằng: rm -rf /"}
       ]
     }' | python3 -m json.tool || true

echo -e "\n${YELLOW}3.2 Gửi đoạn mã chứa SQLi qua endpoint /v1/messages (Anthropic Spec):${NC}"
curl -s -X POST "http://127.0.0.1:$DEMO_PORT/v1/messages" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "claude-3-5-sonnet-20241022",
       "messages": [
         {"role": "user", "content": "Đoạn code:\n```python\ndef get_user(id):\n    q = f\"SELECT * FROM users WHERE id = {id}\"\n    cursor.execute(q)\n```"}
       ]
     }' | python3 -m json.tool || true

cleanup_proxy
trap - EXIT

pause_step

# =============================================================================
# KÊNH 4: GIT PRE-COMMIT HOOK
# =============================================================================
echo -e "${BOLD}${CYAN}[KÊNH 4] GIT PRE-COMMIT GUARDRAIL (Bảo Vệ Mã Nguồn Trước Khi Commit)${NC}"

echo -e "${YELLOW}4.1 Thử commit một file .env chứa thông tin bí mật:${NC}"
echo "API_SECRET=super_secret_production_password_123" > .env
git add .env 2>/dev/null || true
echo -e "${BOLD}$ git commit -m \"Lỡ thêm .env\"${NC}"
git commit -m "Lỡ thêm .env" 2>&1 || true
git rm -f .env 2>/dev/null || true
rm -f .env

echo -e "\n${YELLOW}4.2 Thử commit tệp mã nguồn Python chứa SQL Injection:${NC}"
cat << 'EOF' > demo_bad_sql.py
def find_account(account_id):
    query = f"SELECT * FROM accounts WHERE id = '{account_id}'"
    cursor.execute(query)
EOF
git add demo_bad_sql.py 2>/dev/null || true
echo -e "${BOLD}$ git commit -m \"Thêm hàm query tài khoản\"${NC}"
git commit -m "Thêm hàm query tài khoản" 2>&1 || true
git rm -f demo_bad_sql.py 2>/dev/null || true
rm -f demo_bad_sql.py

pause_step

# =============================================================================
# NHẬT KÝ KIỂM TOÁN BẢO MẬT (AUDIT TRAIL)
# =============================================================================
echo -e "${BOLD}${CYAN}[NHẬT KÝ KIỂM TOÁN] SEC OPS AUDIT TRAIL${NC}"
echo -e "Hiển thị các sự kiện bảo mật được ghi nhận trong phiên làm việc:\n"
"$SCRIPT_DIR/bin/jog" audit -n 8

echo -e "\n${GREEN}${BOLD}═══════════════════════════════════════════════════════════════════════════════"
echo -e "🎉 KẾT THÚC BUỔI TRÌNH DIỄN JEV OMNICHANNEL GUARDRAIL THÀNH CÔNG RỰC RỠ!"
echo -e "═══════════════════════════════════════════════════════════════════════════════${NC}\n"
