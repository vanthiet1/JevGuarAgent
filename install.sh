#!/usr/bin/env bash
# =============================================================================
# install.sh
# Kịch bản cài đặt tự động toàn diện cho Jev Omnichannel Guardrail (JOG).
# =============================================================================
set -e

# Màu hiển thị
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${CYAN}${BOLD}"
cat << "EOF"
╔═════════════════════════════════════════════════════════════════════════════╗
║                   🛡️   JEV OMNICHANNEL GUARDRAIL (JOG)                      ║
║                 SecOps & AI Code Integrity Defense System                   ║
╚═════════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${BLUE}[1/5] Thư mục dự án:${NC} $PROJECT_DIR"

# 1. Kiểm tra môi trường Python 3
echo -e "${BLUE}[2/5] Kiểm tra môi trường Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Lỗi: Không tìm thấy python3 trên hệ thống. Vui lòng cài đặt Python 3.8+!${NC}"
    exit 1
fi
PYTHON_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}✓ Đã tìm thấy Python version: $PYTHON_VER${NC}"

# 2. Phân quyền thực thi cho các file kịch bản và shims
echo -e "${BLUE}[3/5] Cấp quyền thực thi chmod +x cho các kịch bản và shims...${NC}"
chmod +x "$PROJECT_DIR/bin/"* 2>/dev/null || true
chmod +x "$PROJECT_DIR/hooks/"* 2>/dev/null || true
chmod +x "$PROJECT_DIR/"*.sh 2>/dev/null || true
echo -e "${GREEN}✓ Đã phân quyền thực thi thành công.${NC}"

# 3. Khởi tạo thư mục kiểm toán bảo mật cục bộ
mkdir -p "$PROJECT_DIR/.jog/logs"
mkdir -p "$HOME/.jog/logs"

# 4. Kích hoạt toàn diện Guardrail cho dự án (IDE Rules + Git Pre-Commit Hook)
echo -e "${BLUE}[4/5] Kích hoạt Guardrail cho dự án...${NC}"
python3 "$PROJECT_DIR/bin/jog" activate || true


# 5. Thiết lập đường dẫn môi trường (PATH & Alias)
# 5. Thiết lập Universal CLI Launcher 'guar' và 'guard' vào ~/.local/bin
echo -e "${BLUE}[5/5] Cấu hình lệnh 'guar' và 'guard'...${NC}"
mkdir -p "$HOME/.local/bin"
cat << 'EOF' > "$HOME/.local/bin/guar"
#!/usr/bin/env bash
set -e
if [ -f "./JevGuarAgent/bin/jog" ]; then
    exec python3 "./JevGuarAgent/bin/jog" "$@"
elif [ -f "./bin/jog" ] && [ -d "./jog" ]; then
    exec python3 "./bin/jog" "$@"
elif [ -f "../JevGuarAgent/bin/jog" ]; then
    exec python3 "../JevGuarAgent/bin/jog" "$@"
else
    # Fallback to JevGuarAgent in current repo or default path
    FALLBACK="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/bin/jog"
    if [ -f "$FALLBACK" ]; then
        exec python3 "$FALLBACK" "$@"
    fi
    echo "❌ Không tìm thấy JevGuarAgent trong dự án hiện tại!"
    echo "👉 Hãy đảm bảo bạn đã copy thư mục JevGuarAgent vào thư mục dự án này."
    exit 1
fi
EOF
chmod +x "$HOME/.local/bin/guar"
ln -sf "$HOME/.local/bin/guar" "$HOME/.local/bin/guard"

SHELL_RC="$HOME/.bashrc"
if [ -n "$ZSH_VERSION" ] || [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

EXPORT_LINE="export PATH=\"$HOME/.local/bin:$PROJECT_DIR/bin:\$PATH\""
ALIAS_LINES="alias jog=\"$PROJECT_DIR/bin/jog\"
alias guar=\"guar\"
alias guard=\"guar\""

if ! grep -q "alias guar=" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "# === Jev Omnichannel Guardrail (JOG) ===" >> "$SHELL_RC"
    echo "$EXPORT_LINE" >> "$SHELL_RC"
    echo "$ALIAS_LINES" >> "$SHELL_RC"
    echo -e "${GREEN}✓ Đã tự động thêm lệnh 'guar' và 'guard' vào: $SHELL_RC${NC}"
else
    echo -e "${GREEN}✓ Lệnh 'guar' đã được cấu hình trước đó trong: $SHELL_RC${NC}"
fi

echo -e "\n${GREEN}${BOLD}🎉 CÀI ĐẶT JEV OMNICHANNEL GUARDRAIL THÀNH CÔNG! 🎉${NC}\n"

# In bảng hướng dẫn sử dụng và cấu hình IDE chi tiết
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════════"
echo -e "📖 HƯỚNG DẪN CẤU HÌNH CHO CÁC KÊNH TƯƠNG TÁC AI (OMNICHANNEL)"
echo -e "═══════════════════════════════════════════════════════════════════════════════${NC}"

echo -e "\n${BOLD}1. Kích hoạt môi trường trong Terminal hiện tại:${NC}"
echo -e "   ${YELLOW}source $SHELL_RC${NC}"
echo -e "   Hoặc export thủ công:"
echo -e "   ${YELLOW}export PATH=\"$PROJECT_DIR/bin:\$PATH\"${NC}"

echo -e "\n${BOLD}2. Cấu hình TypeSafe API Key (Tùy chọn nếu muốn dùng Cloud Analysis):${NC}"
echo -e "   ${YELLOW}export TYPESAFE_API_KEY=\"your_api_key_here\"${NC}"
echo -e "   ${BLUE}(Lưu ý: Nếu không có key hoặc mất mạng, JOG sẽ tự động kích hoạt Engine Offline Heuristics an toàn)${NC}"

echo -e "\n${BOLD}3. Khởi động Local Intercepting Proxy cho Cursor / Antigravity / VS Code:${NC}"
echo -e "   ${YELLOW}jog proxy start --port 8080${NC}"
echo -e "   Hoặc chạy nền:"
echo -e "   ${YELLOW}nohup jog proxy start --port 8080 > .jog/logs/proxy.log 2>&1 &${NC}"

echo -e "\n${BOLD}4. Cấu hình IDE đón đầu phản hồi Auto-Feedback:${NC}"
echo -e "   • ${BOLD}Cursor IDE:${NC}"
echo -e "     Vào Settings -> Models -> Override OpenAI Base URL:"
echo -e "     ${GREEN}http://127.0.0.1:8080/v1${NC}"
echo -e "   • ${BOLD}Antigravity / Continue / Cline / VS Code:${NC}"
echo -e "     Đặt Base URL của mô hình thành: ${GREEN}http://127.0.0.1:8080/v1${NC}"

echo -e "\n${BOLD}5. Kiểm tra thử nghiệm tính năng bảo vệ:${NC}"
echo -e "   • Quét lệnh Terminal nguy hiểm:  ${YELLOW}jog check prompt 'rm -rf /'${NC}"
echo -e "   • Quét mã nguồn lỗi tương lai:   ${YELLOW}jog check code 'def f(): f=open(\"a.txt\")'${NC}"
echo -e "   • Xem nhật ký kiểm toán:         ${YELLOW}jog audit${NC}"
echo -e "   • Chạy toàn bộ kịch bản demo:    ${YELLOW}bash demo.sh${NC}"

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}\n"
