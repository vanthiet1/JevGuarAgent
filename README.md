# 🛡️ Jev Omnichannel Guardrail (JOG)

> **Hệ thống Guardrail Đa Kênh Bảo Vệ Toàn Diện & Cố Vấn Kiến Trúc Tiên Lượng Cho AI Coding Agents**  
> *Chuẩn hóa an toàn cho: Cursor, Antigravity IDE, Claude Code, Codex, Gemini CLI, VS Code*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![SecOps: Certified](https://img.shields.io/badge/SecOps-Zero--Trust-green.svg)](#)
[![Architecture: Proactive-Advisor](https://img.shields.io/badge/Architecture-Proactive--Advisor-blueviolet.svg)](#)
[![Tests: 32/32 Passed](https://img.shields.io/badge/Tests-32%2F32%20Passed-brightgreen.svg)](#)

---

## ⚡ Bảng Tra Cứu Câu Lệnh Nhanh (Cheat Sheet)

Chỉ cần copy thư mục `JevGuarAgent` vào bất kỳ dự án nào, bạn có thể thực thi ngay:

| Câu lệnh | Kênh tác động | Công dụng chi tiết |
| :--- | :--- | :--- |
| `guar active` | **Toàn diện** | **Bật khiên bảo vệ 1-Click** (Tự động liên kết IDE Rules `.agents/` & Git Pre-Commit Hook) |
| `guar active -w` | **Toàn diện + Live** | **Bật bảo vệ & Mở Terminal Monitor Realtime** theo dõi trực tiếp mọi prompt gửi lên và phản hồi |
| `guar watch` | **Realtime Monitor** | **Mở màn hình giám sát thời gian thực** (Live stream prompt, rủi ro, dự đoán edge cases) |
| `guar status` | **Hệ thống** | **Kiểm tra trạng thái bảo vệ** (Rules IDE: BẬT/TẮT, Git Hook: BẬT/TẮT, Proxy: BẬT/TẮT) |
| `guar check prompt "<lệnh/ý định>"` | **Prompt & CLI** | Quét mức độ phá hoại, rò rỉ secret và **phỏng đoán toàn bộ edge cases kiến trúc** |
| `guar check code "<tệp/đoạn mã>"` | **Mã nguồn (AST)** | Quét lỗ hổng tiềm ẩn: SQLi, N+1 Query, Resource Leak, Race Condition, Missing Timeout |
| `guar proxy start [--port 8080]` | **IDE / GUI Proxy** | Khởi động Local Intercepting Proxy chặn cứng HTTP 403 và kích hoạt Self-Correction Loop |
| `guar audit [-n 20]` | **Audit Log** | Xem lịch sử sự kiện kiểm toán bảo mật và dấu vết các lệnh bị chặn |
| `guar deactive` | **Hệ thống** | **Hủy kích hoạt bảo vệ**, gỡ bỏ rules và git hook sạch sẽ khỏi dự án |

*(💡 Mẹo: Bạn có thể gõ `guar active`, `guard active`, `jog activate`, hoặc `./guar active` tùy ý).*

---

## 📌 1. Vấn Đề Cốt Lõi & Triết Lý Bảo Vệ

Khi lập trình cùng các **AI Coding Agent tự hành** (như Claude Code, Cursor Composer, Antigravity Agent, Codex), rủi ro lớn nhất không chỉ nằm ở việc **lộ lọt secrets ngay tại lúc gõ lệnh**, mà nằm ở **các lỗi rủi ro kiến trúc tương lai (Future Risks & Edge Cases)** mà Agent vô tình đưa vào hệ thống:
* ⚠️ **Lỗi hiệu năng âm thầm:** N+1 Query làm nghẽn DB, Memory Leak do socket/file stream không giải phóng.
* ⚠️ **Lỗi treo hệ thống (Denial of Service):** Gọi API mạng thiếu `timeout`, không có Retry Exponential Backoff.
* ⚠️ **Lỗi nghiệp vụ chết người:** Trừ tiền 2 lần (Double Spending), thiếu Idempotency, sai số làm tròn số thập phân (float), Race Condition khi nhiều tiến trình cập nhật biến chung.
* ⚠️ **Lỗ hổng bảo mật nghiêm trọng:** SQL Injection qua chuỗi nối thô, Path Traversal khi upload file, XSS qua input form.

**Jev Omnichannel Guardrail (JOG)** giải quyết triệt để vấn đề này thông qua mô hình **Phòng thủ 3 Tầng**:
1. **Tầng 1 - Ngăn chặn tức thời (Instant Defense):** Chặn đứng mọi câu lệnh shell phá hoại (`rm -rf`, format disk, fork bomb) và quét sạch rò rỉ API Keys/Secrets trong prompt trước khi thực thi.
2. **Tầng 2 - Cố vấn kiến trúc & Phỏng đoán Edge Cases (Proactive Advisory):** Phân tích intent của câu chat, phỏng đoán trước toàn bộ các trường hợp góc (Edge Cases) của 9 nhóm tính năng trọng yếu và ép Agent tuân theo quy chuẩn an toàn.
3. **Tầng 3 - Tự động viết lại code sạch (Auto-Feedback Loop):** Khi code sinh ra vi phạm chuẩn kiến trúc, JOG từ chối và trả về chẩn đoán chi tiết để Agent tự động đọc hiểu và viết lại (Self-Correction) mà người dùng không cần phải can thiệp thủ công.

---

## 🏛️ 2. Kiến Trúc Đa Kênh Toàn Diện (Omnichannel Architecture)

```
                            +--------------------------------------------------+
                            |           CÁC KÊNH TƯƠNG TÁC (CHANNELS)          |
                            +------------------------+-------------------------+
                                                     |
            +----------------------------------------+----------------------------------------+
            |                                        |                                        |
            v                                        v                                        v
    [KÊNH 1: TERMINAL CLI]                  [KÊNH 2: IDE / GUI]                      [KÊNH 3: GIT HOOK]
    claude / codex / gemini              Cursor / Antigravity / VS Code               git commit -m ...
            |                                        |                                        |
            v                                        v                                        v
    [CLI Shim Interceptor]                 [Local Proxy :8080] / [.agents/]         [Pre-Commit Guard]
    (jog/intercept_cli.py)                 (local_proxy.py / rules)                (pre_commit_guard.py)
            |                                        |                                        |
            +----------------------------------------+----------------------------------------+
                                                     |
                                                     v
                                  +--------------------------------------+
                                  |    BỘ NÃO PHÂN TÍCH (JEV ENGINE)     |
                                  |         (jog/jev_engine.py)          |
                                  +------------------+-------------------+
                                                     |
                          +--------------------------+--------------------------+
                          |                                                     |
                          v (Ưu tiên nếu có Key)                                v (Fallback Ngoại tuyến)
               +----------------------+                              +----------------------+
               |     TypeSafe API     |                              |   Offline AST &      |
               |  POST /v1/systemone  |                              | Heuristics Analyzer  |
               +----------------------+                              +----------------------+
                          |                                                     |
                          +--------------------------+--------------------------+
                                                     |
                                                     v
                            +--------------------------------------------------+
                            |             CÁC PHÁN QUYẾT & HÀNH ĐỘNG           |
                            +------------------------+-------------------------+
                                                     |
    +-------------------+--------------------+--------------------+--------------------+
    |                   |                    |                    |                    |
    v                   v                    v                    v                    v
 [ALLOW]             [WARN]               [BLOCK]        [PROACTIVE ADVISOR]    [AUTO-FEEDBACK]
Thực thi minh bạch  Cảnh báo [y/N]       Chặn đứng lệnh  Phỏng đoán Edge Cases  Trả HTTP 403
(Zero Overhead)     In cảnh báo vàng     (Exit code = 1) & Ép Agent theo chuẩn  Ép Agent tự sửa
```

---

## 🔄 3. Chi Tiết Các Quy Trình Hoạt Động (Detailed Execution Flows)

### 🔹 Flow 1: Quy trình Kích hoạt 1-Click (`guar active`)
Quy trình giúp bất kỳ dự án nào lập tức sở hữu hệ thống phòng thủ mà không cần cấu hình phức tạp:

```
[Developer gõ: guar active]
       │
       ├──> 1. Nhận diện thư mục dự án mục tiêu (Target Project Discovery)
       │
       ├──> 2. Khởi tạo IDE Rules & Skills (.agents/)
       │      • Tạo .agents/rules/jog_guardrail.md (Quy tắc bắt buộc cho Agent)
       │      • Tạo .agents/skills/jog-guard/SKILL.md (Cung cấp cú pháp kiểm tra)
       │
       ├──> 3. Cài đặt Git Pre-Commit Hook (.git/hooks/pre-commit)
       │      • Tự động bind PYTHONPATH trỏ chính xác về JevGuarAgent
       │      • Phân quyền thực thi chmod +x
       │
       ├──> 4. Khởi tạo thư mục Audit Log (.jog/logs/)
       │
       └──> 5. Hiển thị Banner xác nhận: [✓] ACTIVATED
```

---

### 🔹 Flow 2: Quy trình Phỏng đoán Edge Cases & Cố vấn Kiến trúc (Proactive Advisory Flow)
Bảo đảm Agent không bao giờ viết code thiếu case, sót lỗi hay làm sập Production:

```
[User gửi yêu cầu tính năng] (VD: "Làm chức năng thanh toán", "Làm upload ảnh")
       │
       ▼
[JOG quét câu lệnh / Intent Classifier]
       │
       ├──> Nhận diện thuộc 1 trong 9 nhóm ý định kỹ thuật trọng yếu
       │
       ├──> Phỏng đoán toàn bộ Risk Factors & Edge Cases tiềm ẩn
       │
       ├──> Tổng hợp Recommended Patterns & Injected Directive
       │
       ▼
[Trả về mảng JSON 'predicted_edge_cases' cho Agent]
       │
       ▼
[Agent đọc danh sách Edge Cases làm tiêu chuẩn bắt buộc]
       │
       └──> Agent viết code chuẩn chỉnh, bao quát 100% các case ngay từ đầu!
```

**9 Nhóm Ý Định & Edge Cases JOG Tự Động Phỏng Đoán:**
1. 💳 **Thanh toán / Giao dịch (Payment):** Double Spending, Float rounding, Lặp webhook, Race condition trừ số dư $\rightarrow$ Ép dùng `Idempotency Key (UUID)`, `Integer/Decimal`, `Pessimistic Lock (SELECT FOR UPDATE)`.
2. 📁 **Upload tệp & Lưu trữ (Storage):** Path Traversal (`../`), Web Shell injection, Tràn đĩa Max File Size $\rightarrow$ Ép đổi tên bằng `UUID`, kiểm tra MIME magic bytes, đọc chunks với `Context Manager`.
3. ⚡ **Realtime / WebSocket:** Zombie connections, Rò rỉ RAM khi disconnect, Reconnection Storm $\rightarrow$ Ép có `Heartbeat Ping/Pong (30s)`, dọn sạch listener, `Exponential Backoff`.
4. 🗄️ **Database & CRUD:** N+1 Query, SQLi, Cạn kiệt Connection Pool $\rightarrow$ Ép dùng `Parameterized Query`, Eager Loading (`JOIN/IN`), phân trang `LIMIT/OFFSET`.
5. 🌐 **Gọi API bên ngoài:** Treo thread pool do thiếu timeout, rò rỉ secret $\rightarrow$ Ép có tham số `timeout`, `Try/Catch` mạng và Retry Backoff.
6. 🔒 **Xác thực & Bảo mật (Auth):** Băm MD5/SHA1 yếu, JWT thiếu `exp`, Timing Attack $\rightarrow$ Ép dùng `Bcrypt/Argon2id`, `hmac.compare_digest()`.
7. 🧵 **Đa luồng & Tiến trình nền (Worker):** Race condition biến chung, Worker crash mất job $\rightarrow$ Ép dùng `Lock()`, `Graceful Shutdown`.
8. ⚡ **Bộ nhớ đệm (Caching):** Cache Stampede (Thundering Herd), dữ liệu cũ (Stale Data) $\rightarrow$ Ép dùng `TTL Jitter`, Invalidation khi Mutation.
9. 📝 **Form & Dữ liệu người dùng (Validation):** XSS injection, ReDoS $\rightarrow$ Ép Schema Validation ở Backend (Zod/Pydantic), Encode HTML.

---

### 🔹 Flow 3: Quy trình Tự Động Sửa Lỗi (Auto-Feedback & Self-Correction Loop)
Cơ chế ép Agent tự động sửa lại mã nguồn sạch khi sinh code lỗi:

```
[Agent chuẩn bị ghi đè file code]
       │
       ▼
[JOG quét cú pháp qua Offline AST & Heuristics]
       │
       ├──> Phát hiện lỗi: SQL Injection / Unclosed Stream / Missing Timeout
       │
       ▼
[JOG Phán quyết: REJECT_FORCE_AGENT_REWRITE (HTTP 403)]
       │
       ▼
[Phản hồi JSON chi tiết cho Agent]:
       │  • detected_flaws: ["Mở file bằng open() không có Context Manager"]
       │  • remediation_suggestions: ["BẮT BUỘC dùng with open(...) as f:"]
       │
       ▼
[Agent đọc phản hồi lỗi và TỰ ĐỘNG VIẾT LẠI CODE SẠCH]
       │
       ▼
[Người dùng nhận được kết quả cuối cùng hoàn hảo, không còn lỗi tiềm ẩn]
```

---

### 🔹 Flow 4: Quy trình Bảo Vệ Tầng Git (Git Pre-Commit Guard Flow)
Chặn đứng việc vô tình commit file `.env`, private key hoặc mã nguồn nguy hiểm:

```
[Developer gõ: git commit -m "feat: update api"]
       │
       ▼
[Git Pre-Commit Hook kích hoạt tự động]
       │
       ├──> Lấy danh sách tệp đang staged (git diff --cached)
       ├──> Quét tên tệp nhạy cảm (.env, .pem, service-account.json, id_rsa...)
       ├──> Quét nội dung diff qua JevEngine (Mode 1: Secrets | Mode 2: Code Flaws)
       │
       ├──> NẾU CÓ VI PHẠM:
       │      ❌ HỦY BỎ COMMIT NGAY LẬP TỨC (Exit code = 1)
       │      🚨 In bảng chi tiết vi phạm & hướng dẫn khắc phục ra Terminal
       │      📋 Ghi sự kiện vào audit.log
       │
       └──> NẾU HỢP LỆ:
              ✅ Cho phép commit thực hiện minh bạch!
```

---

## 🚀 4. Hướng Dẫn Từng Bước Thực Hiện (Step-by-Step Guide)

### Bước 1: Cài đặt công cụ ban đầu (1 lần duy nhất trên máy)
Chạy script cài đặt tại thư mục của `JevGuarAgent`:
```bash
bash install.sh
source ~/.bashrc
```
Script sẽ tự động tạo lệnh toàn cục `guar` và `guard` trong `~/.local/bin`, phân quyền thực thi cho các file nhị phân và chuẩn bị thư mục logs.

---

### Bước 2: Kích hoạt bảo vệ cho bất kỳ dự án nào (`guar active`)
Mỗi khi bạn tạo hoặc clone một dự án mới (ví dụ: `my-web-app`, `ecommerce`, `wedding-manager`), bạn chỉ cần:
```bash
# Cách 1: Đứng tại thư mục dự án cần bảo vệ và gõ:
guar active

# Cách 2: Hoặc chỉ định đường dẫn cụ thể:
guar active /path/to/my-project
```
> 🎉 **Xong!** Dự án của bạn lập tức được kích hoạt đồng thời cả **AI Agent IDE Rules** và **Git Pre-commit Hook**.

---

### Bước 3: Cấu hình TypeSafe API Key (Tùy chọn)
JOG hoạt động **hoàn hảo 100% ở chế độ Offline (Zero-Trust Fallback)** mà không cần kết nối mạng hay API key.  
Nếu bạn muốn sử dụng thêm sức mạnh Cloud Analytics từ TypeSafe AI, chỉ cần thêm vào file `.env` hoặc `.env.local` của chính dự án bạn đang làm việc:
```env
TYPESAFE_API_KEY="your_typesafe_api_key_here"
```
JOG có cơ chế **Project-Level Discovery**, sẽ tự động đọc file `.env` của dự án hiện tại mà không cần cấu hình biến môi trường toàn cục.

---

### Bước 4: Tương tác cùng AI Agent trong IDE (Cursor, Antigravity, VS Code)

Có 2 cách tích hợp tùy theo nhu cầu của bạn:

#### Cách A: Tích hợp tự nhiên qua `.agents/` (Khuyên dùng)
* Sau khi chạy `guar active`, thư mục `.agents/rules/jog_guardrail.md` đã sẵn sàng.
* Bạn chat và ra lệnh cho Agent như bình thường. Agent sẽ tự động gọi ngầm `guar check prompt` và `guar check code` trước mỗi thao tác để kiểm duyệt an toàn và phỏng đoán edge cases.

#### Cách B: Chặn cứng tầng mạng qua Local Proxy (:8080)
1. Khởi động Proxy:
   ```bash
   guar proxy start --port 8080
   # Hoặc chạy ngầm:
   nohup guar proxy start --port 8080 > .jog/logs/proxy.log 2>&1 &
   ```
2. Cấu hình IDE (Cursor Settings / Antigravity / Continue):
   * Đặt **Base URL** của Model thành: `http://127.0.0.1:8080/v1`
   * Mọi request chat sẽ đi xuyên qua JOG Proxy. Nếu code lỗi, Proxy ném mã `HTTP 403` bắt Agent tự sửa lại code trước khi hiển thị cho bạn.

---

### Bước 5: Kiểm tra và xem nhật ký kiểm toán
```bash
# Xem trạng thái kích hoạt của dự án:
guar status

# Xem 20 sự kiện kiểm toán bảo mật gần nhất:
guar audit

# Thử nghiệm quét lệnh shell thủ công:
guar check prompt "rm -rf /"

# Thử nghiệm quét file mã nguồn:
guar check code "src/lib/db.ts"
```

---

## 📂 5. Cấu Trúc Thư Mục Dự Án

```text
JevGuarAgent/
├── .agents/                    # Cấu hình Antigravity IDE mẫu
│   ├── rules/
│   │   └── jog_guardrail.md    # Quy tắc bảo mật chuẩn cho AI Agents
│   └── skills/
│       └── jog-guard/
│           └── SKILL.md        # Kỹ năng tra cứu JOG cho Agent
├── bin/                        # Bộ nhị phân CLI & Interceptors
│   ├── claude                  # CLI Shim cho Claude Code
│   ├── codex                   # CLI Shim cho Codex
│   ├── gemini                  # CLI Shim cho Gemini CLI
│   ├── guar                    # Symlink lệnh tắt guar
│   └── jog                     # CLI quản trị trung tâm của JOG
├── config/
│   └── jog_config.json         # Cấu hình ngưỡng bảo vệ, ports, upstreams
├── hooks/
│   └── pre-commit              # Script Git Pre-commit hook template
├── jog/                        # Gói mã nguồn cốt lõi (Core Python Package)
│   ├── __init__.py             # Định nghĩa phiên bản JOG (v1.0.0)
│   ├── config.py               # Quản lý nạp cấu hình & discovery .env
│   ├── jev_engine.py           # Bộ não phân tích (AST, Heuristics, Intent Classifier)
│   ├── intercept_cli.py        # Module đánh chặn lệnh CLI
│   ├── local_proxy.py          # Module Local Intercepting HTTP Proxy (:8080)
│   ├── logger.py               # Module Audit Trail & Terminal UI
│   └── pre_commit_guard.py     # Module bảo vệ tầng Git
├── tests/                      # Bộ kiểm thử tự động toàn diện
│   ├── test_cli.py             # Kiểm thử CLI & lệnh activate/deactivate
│   ├── test_engine.py          # Kiểm thử AST, Secrets, Future Risks, Advisory
│   ├── test_pre_commit.py      # Kiểm thử Git Hook
│   ├── test_proxy.py           # Kiểm thử Local Proxy & Auto-Feedback
│   └── run_all_tests.py        # Runner chạy toàn bộ 32 test cases
├── demo.sh                     # Kịch bản trình diễn tương tác 4 kênh thực tế
├── guar                        # Trình khởi chạy nhanh trực tiếp tại gốc
├── install.sh                  # Kịch bản cài đặt tự động 1-Click
├── requirements.txt            # Danh sách thư viện phụ thuộc (requests, rich)
└── uninstall.sh                # Kịch bản gỡ bỏ JOG sạch sẽ
```

---

## 🧪 6. Bộ Kiểm Thử Tự Động (Test Suite)

Dự án đi kèm bộ kiểm thử tự động toàn diện **32 bài test** kiểm tra từng ngóc ngách của hệ thống phòng thủ:

```bash
# Chạy toàn bộ test suite:
python3 tests/run_all_tests.py

# Chạy kịch bản demo trực quan tương tác 4 kênh:
bash demo.sh
```

Kết quả kiểm thử:
```text
===========================================================================
🧪  KHỞI CHẠY BỘ KIỂM THỬ TỰ ĐỘNG TOÀN DIỆN JEV GUARDRAIL (JOG)
===========================================================================
Tổng số bài kiểm tra đã nạp: 32
---------------------------------------------------------------------------
test_credential_leaks_detected               ... ok
test_destructive_disk_format_blocked         ... ok
test_destructive_rm_root_blocked             ... ok
test_fork_bomb_blocked                       ... ok
test_rce_pipe_blocked                        ... ok
test_clean_python_code                       ... ok
test_missing_network_timeout_detected        ... ok
test_n_plus_one_query_detected               ... ok
test_proactive_architecture_advisory_realtime ... ok
test_race_condition_detected                 ... ok
test_sql_injection_detected                  ... ok
test_unclosed_file_resource_leak_detected    ... ok
test_activate_and_deactivate                 ... ok
...
Ran 32 tests in 3.452s
OK (100% Passed)
```

---

## 📄 7. Giấy Phép & Bản Quyền
Dự án được phân phối dưới giấy phép **MIT License**. Tự do sử dụng, tùy biến và tích hợp vào các môi trường doanh nghiệp hoặc dự án mã nguồn mở.
