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

## 🚀 4. Hướng Dẫn Cài Đặt & Sử Dụng Từ A Đến Z (Step-by-Step Guide)

### Bước 1: Clone mã nguồn dự án về máy
Mở terminal và clone repository về máy tính của bạn:
```bash
git clone https://github.com/vanthiet1/JevGuarAgent.git
cd JevGuarAgent
```

---

### Bước 2: Cài đặt và kích hoạt bộ công cụ toàn cục
Chạy script cài đặt tự động 1-Click:
```bash
bash install.sh
source ~/.bashrc
```
> 💡 **Tác vụ thực thi tự động:**
> - Tự động đăng ký các lệnh toàn cục `guar`, `guard`, `jog` vào thư mục `~/.local/bin`.
> - Cấp quyền thực thi (`chmod +x`) cho toàn bộ launcher và module nhị phân.
> - Giờ đây bạn có thể đứng ở **bất kỳ thư mục nào** trên máy tính và gõ trực tiếp `guar`!

Kiểm tra bộ test tự động để đảm bảo môi trường đạt 100% tiêu chuẩn an toàn:
```bash
python3 tests/run_all_tests.py
# Kết quả mong đợi: 32/32 tests PASSED!
```

---

### Bước 3: Cấu hình Biến Môi Trường (.env) & Hướng Dẫn Lấy API Key Từ OpenRouter

#### 🛡️ Triết lý Zero-Trust:
> **Lưu ý quan trọng:** JevGuarAgent hoạt động **100% độc lập ở chế độ Offline (Local Fallback)** mà không cần kết nối mạng hay bất kỳ API key nào (vẫn quét regex SecOps, phân tích AST Python, và phỏng đoán 9 domain kiến trúc cực chuẩn).  
> Khi cung cấp thêm **OpenRouter API Key**, hệ thống sẽ kích hoạt thêm khả năng suy luận ngữ cảnh sâu từ các mô hình AI tiên tiến nhất (Claude 3.5 Sonnet, DeepSeek V3, GPT-4o, Gemini 2.0 Flash) để phân tích logic nghiệp vụ phức tạp.

#### 1. Tạo tệp `.env`:
Sao chép từ tệp mẫu `.env.example` đã chuẩn bị sẵn:
```bash
cp .env.example .env
```

#### 2. Các biến cấu hình chính trong `.env`:
```env
# 1. API Key từ OpenRouter (Khuyên dùng) hoặc TypeSafe
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TYPESAFE_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 2. Model LLM muốn sử dụng (Mặc định: deepseek/deepseek-chat hoặc anthropic/claude-3.5-sonnet)
JOG_LLM_MODEL=deepseek/deepseek-chat

# 3. Cấu hình Local Proxy & Audit Log (Mặc định đã tối ưu)
JOG_PROXY_HOST=127.0.0.1
JOG_PROXY_PORT=8080
JOG_AUDIT_LOG=.jog/logs/audit.log

# 4. Ngưỡng cảnh báo an toàn
JOG_LEAK_THRESHOLD=0.6
JOG_STABILITY_THRESHOLD=7.5
```

#### 3. Hướng dẫn chi tiết từng bước lấy API Key từ OpenRouter.ai:

> [!TIP]
> **⚡ Đường dẫn nhanh lấy API Key OpenRouter trong 30 giây:**  
> 👉 Truy cập trực tiếp: **[https://openrouter.ai/settings/keys](https://openrouter.ai/settings/keys)**  
> *(Chỉ cần đăng nhập bằng Google/GitHub ➔ Bấm **"Create Key"** ➔ Copy chuỗi `sk-or-v1-...` dán vào `.env` là hoàn tất!)*
1. **Truy cập trang chủ:** Mở trình duyệt và truy cập [https://openrouter.ai/](https://openrouter.ai/).
2. **Đăng ký / Đăng nhập:**
   - Bấm vào nút **Sign In** (hoặc **Sign Up**) ở góc trên cùng bên phải.
   - Bạn có thể đăng nhập nhanh bằng tài khoản **Google** hoặc **GitHub**.
3. **Mở trang quản lý Keys:**
   - Nhấp vào biểu tượng **Avatar tài khoản** ở góc trên cùng bên phải ➔ Chọn **Keys**.
   - Hoặc truy cập đường link trực tiếp: [https://openrouter.ai/settings/keys](https://openrouter.ai/settings/keys).
4. **Tạo API Key mới:**
   - Bấm nút **"Create Key"**.
   - Đặt tên gợi nhớ cho key (ví dụ: `JevGuarAgent`).
   - *(Tùy chọn)* Đặt Credit Limit nếu muốn giới hạn hạn mức chi tiêu.
   - Bấm nút **Create**.
5. **Sao chép Key:**
   - Một chuỗi token có tiền tố `sk-or-v1-...` sẽ xuất hiện trên màn hình. Bấm **Copy**.
   - ⚠️ *Lưu ý: Chuỗi key chỉ hiển thị 1 lần duy nhất lúc tạo vì lý do an toàn.*
6. **Dán Key vào `.env`:**
   - Mở tệp `.env` và dán chuỗi vừa copy vào:
     ```env
     OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
     ```
7. *(Tùy chọn nạp Credit / Sử dụng Model Miễn Phí):*
   - Bạn có thể vào mục [Credits](https://openrouter.ai/credits) nạp $5 - $10 để dùng các model trả phí cao cấp như `anthropic/claude-3.5-sonnet`.
   - Hoặc dùng các mô hình chi phí siêu rẻ / miễn phí: `deepseek/deepseek-chat`, `meta-llama/llama-3.3-70b-instruct:free`, `google/gemini-2.0-flash`.

> 💡 **Project-Level Discovery:** JevGuarAgent có cơ chế tự động tìm kiếm `.env` thông minh. Bạn có thể đặt file `.env` tại thư mục của `JevGuarAgent` HOẶC đặt trong thư mục dự án mục tiêu bạn đang phát triển (`wedding-manager`, `ecommerce`, ...), hệ thống đều tự động nhận diện chính xác!

---

### Bước 4: Kích hoạt bảo vệ cho bất kỳ dự án nào (`guar active`)
Mỗi khi bạn tạo hoặc clone một dự án mã nguồn mới cần bảo vệ (ví dụ: `wedding-manager`, `ecommerce`, `crm-api`), bạn chỉ cần:

```bash
# Cách 1: Đứng tại thư mục dự án và bật bảo vệ 1-Click:
guar active

# Cách 2: Bật bảo vệ đồng thời mở Terminal Monitor Realtime quan sát trực tiếp:
guar active -w

# Cách 3: Hoặc chỉ định đường dẫn cụ thể từ bất kỳ đâu:
guar active /path/to/my-project
```
> 🎉 **Xong!** Dự án của bạn lập tức được kích hoạt đồng thời cả **AI Agent IDE Rules** (`.agents/`) và **Git Pre-commit Hook** (`.git/hooks/pre-commit`).

---

### Bước 5: Mở Màn Hình Giám Sát Thời Gian Thực (`guar watch`)
Để theo dõi luồng prompt gửi lên, rủi ro bị chặn và các edge cases được phỏng đoán tức thì:
```bash
guar watch
# (Hoặc alias: guar monitor, guar live)
```
> 💡 *Mẹo:* Hãy mở một cửa sổ/tab terminal riêng (Split Pane) và chạy lệnh này để xem radar bảo vệ hoạt động liên tục!

---

### Bước 6: Tương tác cùng AI Agent trong IDE (Cursor, Antigravity, VS Code, Claude Code)

Có 2 cách tích hợp tùy theo nhu cầu của bạn:

#### Cách A: Tích hợp tự nhiên qua `.agents/` (Khuyên dùng)
* Sau khi chạy `guar active`, các tệp `.agents/rules/jog_guardrail.md` và `.agents/skills/jog-guard/SKILL.md` đã tự động liên kết vào dự án.
* Bạn chỉ cần chat và giao nhiệm vụ cho Agent như bình thường. Agent sẽ tự động tham khảo guardrail trước khi đề xuất hoặc thực thi mã lệnh.

#### Cách B: Chặn cứng tầng mạng qua Local Proxy (:8080)
1. Khởi động Proxy:
   ```bash
   guar proxy start --port 8080
   # Hoặc chạy ngầm dưới nền:
   nohup guar proxy start --port 8080 > .jog/logs/proxy.log 2>&1 &
   ```
2. Cấu hình IDE (Cursor Settings / Continue / Antigravity):
   * Đặt **Base URL** của LLM Provider thành: `http://127.0.0.1:8080/v1`
   * Mọi request chat sẽ đi xuyên qua JOG Proxy. Nếu phát hiện code lỗi hoặc nguy hiểm, Proxy lập tức trả về mã `HTTP 403` kích hoạt cơ chế Self-Correction bắt Agent tự sửa lại mã nguồn an toàn trước khi hiển thị cho bạn.

---

### Bước 7: Kiểm tra trạng thái & Nhật ký kiểm toán bảo mật
```bash
# Xem trạng thái kích hoạt của dự án:
guar status

# Xem 20 sự kiện kiểm toán bảo mật gần nhất:
guar audit

# Thử nghiệm quét lệnh shell thủ công:
guar check prompt "rm -rf /"

# Thử nghiệm quét file mã nguồn tìm lỗi tiềm ẩn:
guar check code "src/lib/db.ts"
```

---

## 📂 5. Cấu Trúc Thư Mục Dự Án Thực Tế (Real-World Project Structure)

Trong một dự án thực tế thông thường (ví dụ: dự án `wedding-manager` hoặc `my-project`), thư mục clone **`JevGuarAgent/`** sẽ **nằm cùng cấp với thư mục `.agents/`** tại thư mục gốc của dự án như sau:

```text
my-project/ (hoặc wedding-manager/)           <-- 📁 Thư mục gốc của dự án thực tế bạn đang phát triển
│
├── .agents/                                  <-- 🛡️ Thư mục IDE Rules & Skills (NẰM CÙNG CẤP VỚI JevGuarAgent)
│   │                                              (Được tự động liên kết khi bạn chạy 'guar active')
│   ├── rules/
│   │   └── jog_guardrail.md                  <-- Quy tắc chỉ đạo AI Agent phải kiểm duyệt prompt & phỏng đoán kiến trúc
│   └── skills/
│       └── jog-guard/
│           └── SKILL.md                      <-- Kỹ năng tích hợp JOG Guardrail để Agent tự tra cứu và thực thi
│
├── .git/                                     <-- 🌳 Quản lý phiên bản mã nguồn Git
│   └── hooks/
│       └── pre-commit                        <-- Hook tự động kích hoạt khi 'git commit', chặn rò rỉ secret & code lỗi
│
├── .jog/                                     <-- 📊 Dữ liệu kiểm toán & nhật ký runtime của Guardrail
│   └── logs/
│       └── audit.log                         <-- File nhật ký ghi lại toàn bộ prompt, verdict, rủi ro & phỏng đoán edge cases
│
├── JevGuarAgent/                             <-- 🚀 BỘ CÔNG CỤ GUARDRAIL (NẰM CÙNG CẤP VỚI .agents/)
│   ├── bin/                                  <-- Bộ công cụ CLI: guar, jog, claude, codex, gemini
│   ├── config/
│   │   └── jog_config.json                   <-- Cấu hình ngưỡng bảo mật, cổng mạng, upstream
│   ├── hooks/
│   │   └── pre-commit                        <-- File hook mẫu chuẩn bị triển khai
│   ├── jog/                                  <-- 🧠 BỘ NÃO CỐT LÕI (Python Engine)
│   │   ├── __init__.py                       # Khởi tạo gói JOG
│   │   ├── config.py                         # Module đọc cấu hình & tự động dò tìm .env
│   │   ├── jev_engine.py                     # Phân tích AST, regex SecOps, phỏng đoán 9 domain kiến trúc
│   │   ├── intercept_cli.py                  # Module đánh chặn lệnh CLI phá hoại
│   │   ├── local_proxy.py                    # Local Intercepting HTTP Proxy (:8080)
│   │   ├── logger.py                         # Trình ghi log kiểm toán & giao diện ANSI Terminal Monitor
│   │   └── pre_commit_guard.py               # Module bảo vệ tầng Git trước khi commit
│   ├── tests/                                <-- 🧪 Bộ kiểm thử tự động toàn diện (32/32 tests passed)
│   ├── .env.example                          <-- File mẫu cấu hình biến môi trường
│   ├── .env                                  <-- File chứa OPENROUTER_API_KEY (Được .gitignore bảo vệ tuyệt đối)
│   ├── guar                                  <-- Trình khởi chạy nhanh trực tiếp tại chỗ
│   ├── install.sh                            <-- Script cài đặt toàn cục 1-Click
│   ├── requirements.txt                      <-- Thư viện phụ thuộc
│   └── README.md                             <-- Toàn bộ tài liệu hướng dẫn vận hành
│
├── src/ (hoặc app/, lib/, components/)       <-- 💻 Toàn bộ mã nguồn sản phẩm thực tế của bạn
├── package.json (hoặc requirements.txt...)   <-- File quản lý thư viện của dự án chính
└── .env                                      <-- (Tùy chọn) File môi trường của dự án chính (JOG tự động nhận diện)
```

### 💡 Mối quan hệ tương hỗ giữa `.agents/` và `JevGuarAgent/`:
1. **`.agents/` là "Bộ Rễ Chỉ Đạo" cho AI IDE**:
   - Khi bạn mở dự án trong Cursor, Antigravity, hoặc VS Code, IDE sẽ tự động nạp các tệp trong thư mục `.agents/rules/` và `.agents/skills/`.
   - AI Agent sẽ đọc các quy tắc này và biết rằng: *“Trước khi chạy lệnh terminal hoặc chỉnh sửa code, mình bắt buộc phải hỏi qua bộ não JOG Guardrail nằm ở JevGuarAgent”*.
2. **`JevGuarAgent/` là "Bộ Não Phòng Thủ & Cố Vấn"**:
   - Nằm cạnh `.agents/`, đóng vai trò là động cơ thực thi. Nó quét mã bằng AST Python, đối soát regex zero-trust, liên lạc với OpenRouter API để dự báo các tình huống edge cases (Idempotency, Race Condition, Memory Leak) và trả kết quả về cho Agent.
3. **`.git/hooks/pre-commit` là "Chiếc Khiên Chặn Cuối"**:
   - Đảm bảo ngay cả khi Agent lỡ tạo code lỗi hoặc bạn vô tình commit file `.env`, lệnh `git commit` sẽ bị chặn cứng ngay tại máy của bạn trước khi kịp đẩy lên GitHub.

---

## 🧪 6. Bộ Kiểm Thử Tự Động (Test Suite)

Dự án đi kèm bộ kiểm thử tự động toàn diện **32 bài test** kiểm tra từng ngóc ngách của hệ thống phòng thủ:

```bash
# Chạy toàn bộ test suite tự động (32/32 tests passed):
python3 tests/run_all_tests.py
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
