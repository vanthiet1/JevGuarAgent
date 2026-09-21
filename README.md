# 🛡️ JevGuarAgent (JOG)

> **Hệ thống Guardrail Đa Kênh Toàn Diện & Cố Vấn Kiến Trúc Tiên Lượng Cho AI Coding Agents**  
> *Bảo vệ an toàn cho: Cursor, Antigravity, Claude Code, Codex, Gemini CLI, VS Code*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Tests: 32/32 Passed](https://img.shields.io/badge/Tests-32%2F32%20Passed-brightgreen.svg)](#)

---

## ⚡ Bảng Tra Cứu Câu Lệnh Nhanh (Cheat Sheet)

| Câu lệnh | Kênh | Công dụng |
| :--- | :--- | :--- |
| `guar active` | **Toàn diện** | **Bật bảo vệ 1-Click** (Tự động liên kết IDE Rules `.agents/` & Git Pre-Commit Hook) |
| `guar active -w` | **Toàn diện + Live** | **Bật bảo vệ & Mở Terminal Monitor Realtime** xem trực tiếp prompt & phản hồi |
| `guar watch` | **Realtime** | **Mở màn hình radar thời gian thực** (Live stream prompt, rủi ro, dự đoán edge cases) |
| `guar status` | **Hệ thống** | **Kiểm tra trạng thái bảo vệ** (Rules IDE, Git Hook, Proxy) |
| `guar check prompt "<lệnh>"` | **Prompt & CLI** | Quét phá hoại, rò rỉ secret và **phỏng đoán toàn bộ edge cases kiến trúc** |
| `guar check code "<file>"` | **Mã nguồn (AST)** | Quét lỗ hổng: SQLi, N+1 Query, Resource Leak, Race Condition, Missing Timeout |
| `guar proxy start [--port 8080]` | **Proxy HTTP** | Khởi động Local Proxy chặn cứng HTTP 403, kích hoạt AI Self-Correction |
| `guar audit [-n 20]` | **Audit Log** | Xem lịch sử sự kiện kiểm toán bảo mật |
| `guar deactive` | **Hệ thống** | **Gỡ bỏ bảo vệ sạch sẽ** khỏi dự án |

---

## 🚀 Cài Đặt & Sử Dụng Nhanh (Quick Start)

### 1. Clone & Cài đặt công cụ toàn cục
```bash
git clone https://github.com/vanthiet1/JevGuarAgent.git
cd JevGuarAgent
bash install.sh && source ~/.bashrc
```
> Lệnh `guar` sẽ sẵn sàng sử dụng trên toàn hệ thống.

### 2. Cấu hình OpenRouter API Key (Tùy chọn)
JevGuarAgent hoạt động **100% Offline (Local Fallback)** mà không cần internet hay API Key. Khi có thêm OpenRouter Key, hệ thống mở rộng thêm sức mạnh suy luận ngữ cảnh sâu từ các mô hình AI hàng đầu (Claude 3.5, GPT-4o, DeepSeek).

```bash
cp .env.example .env
```
👉 **Lấy API Key trong 30 giây:** Truy cập **[https://openrouter.ai/settings/keys](https://openrouter.ai/settings/keys)** ➔ Bấm **"Create Key"** ➔ Copy token `sk-or-v1-...` và dán vào `.env`:
```env
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key-here
```

### 3. Kích hoạt bảo vệ cho dự án của bạn
Đứng tại thư mục dự án bất kỳ (ví dụ: `wedding-manager`, `my-project`):
```bash
# Bật bảo vệ 1-Click:
guar active

# Hoặc vừa bật bảo vệ vừa mở Terminal Monitor Realtime:
guar active -w
```

---

## 📂 Cấu Trúc Trong Một Dự Án Thực Tế

Trong dự án thực tế, thư mục clone `JevGuarAgent/` **nằm cùng cấp với thư mục `.agents/`** tại thư mục gốc:

```text
my-project/ (hoặc wedding-manager/)           <-- Thư mục gốc dự án thực tế
│
├── .agents/                                  <-- IDE Rules & Skills (Tự tạo khi 'guar active')
│   ├── rules/jog_guardrail.md                # Chỉ đạo AI Agent luôn kiểm duyệt qua JOG
│   └── skills/jog-guard/SKILL.md             # Kỹ năng tra cứu an toàn cho Agent
│
├── .git/hooks/pre-commit                     <-- Git Hook chặn rò rỉ secret & code lỗi khi commit
├── .jog/logs/audit.log                       <-- Nhật ký ghi lại toàn bộ prompt & edge cases
│
├── JevGuarAgent/                             <-- BỘ CÔNG CỤ GUARDRAIL (NẰM CÙNG CẤP VỚI .agents/)
│   ├── bin/                                  # Công cụ CLI (guar, jog, claude, codex, gemini)
│   ├── config/jog_config.json                # Cấu hình ngưỡng bảo mật, ports
│   ├── jog/                                  # Lõi AI Engine, AST Parser, Proxy, Git Guard
│   ├── tests/                                # Bộ 32 bài test tự động
│   ├── .env.example                          # File mẫu cấu hình
│   ├── .env                                  # File chứa OPENROUTER_API_KEY
│   └── install.sh                            # Script cài đặt toàn cục
│
├── src/                                      <-- Toàn bộ mã nguồn sản phẩm thực tế của bạn
├── package.json                              <-- Cấu hình dự án
└── .env                                      <-- Biến môi trường dự án (JOG tự nhận diện)
```

---

## 🏛️ 4 Kênh Bảo Vệ Toàn Diện (Omnichannel)

1. **Terminal CLI Interceptor**: Chặn đứng các lệnh nguy hiểm (`rm -rf /`, fork bomb, curl|bash) và cảnh báo rò rỉ secrets (API Keys, Token) ngay khi gõ trên terminal.
2. **Proactive Architecture Advisory**: Phỏng đoán trước các tình huống rủi ro kiến trúc (Idempotency, Race Condition, Webhook Signature, Memory Leak...) trước khi Agent viết code.
3. **Local Intercepting Proxy (:8080)**: Chặn đứng response nguy hiểm bằng mã HTTP 403, kích hoạt vòng lặp **AI Self-Correction** buộc Agent tự sửa mã an toàn.
4. **Git Pre-Commit Guard**: Quét AST và regex trên toàn bộ file staged, ngăn chặn triệt để mã nguồn lỗi hoặc file nhạy cảm lọt lên GitHub.

---

## 🧪 Kiểm Thử Tự Động (Test Suite)

Hệ thống đi kèm bộ kiểm thử toàn diện **32 bài test** tự động:
```bash
python3 tests/run_all_tests.py
# Kết quả: 32/32 tests PASSED!
```

---

## 📄 Bản Quyền
Phát hành theo giấy phép **MIT License**.
