# 🛡️ Jev Omnichannel Guardrail (JOG) `v1.0.0`

> Hệ thống Guardrail bảo vệ mã nguồn và theo dõi prompt cho AI Coding Agents (Cursor, VS Code, Antigravity, Claude Code, Codex).

---

## ⚡ 1. Các Câu Lệnh Chạy

| Hệ điều hành | Kích hoạt bảo vệ | Xem Radar theo dõi (Watch) | Bảng gõ Prompt test | Hủy kích hoạt |
| :--- | :--- | :--- | :--- | :--- |
| **Windows (CMD / PowerShell)** | `.\guar active` | `.\guar watch` | `.\guar console` | `.\guar deactive` |
| **macOS / Linux** | `./guar active` | `./guar watch` | `./guar console` | `./guar deactive` |
| **Universal (Mọi OS)** | `python guar.py active` | `python guar.py watch` | `python guar.py console` | `python guar.py deactive` |

> **Chạy nhanh 1 bước:**
> Chạy `.\guar active` (Windows) hoặc `./guar active` (Mac/Linux) để tự động liên kết rule, cấu hình VS Code và bật radar theo dõi prompt trực tiếp.

---

## 🔑 2. Cách Lấy API Key Cho JEV & Cấu Hình `.env`

*(Mặc định hệ thống chạy **Offline 100% miễn phí** không bắt buộc cần key. Nếu muốn kích hoạt thêm AI Cloud Reasoning, làm theo các bước sau):*

1. **Lấy API Key:** Truy cập **[https://openrouter.ai/settings/keys](https://openrouter.ai/settings/keys)** (hoặc [https://typesafe.ai](https://typesafe.ai)) ➔ Đăng nhập ➔ Bấm **"Create Key"** ➔ Copy token dạng `sk-or-v1-...`.
2. **Tạo file `.env`:** Tạo file `.env` tại thư mục dự án (hoặc sao chép từ `.env.example`) và điền đầy đủ cấu hình như sau:

```env
# ==============================================================================
# Jev Omnichannel Guardrail (JOG) - Cấu hình biến môi trường
# ==============================================================================

# 1. Khóa xác thực TypeSafe AI / OpenRouter API (Thay bằng key bạn vừa lấy ở bước 1)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TYPESAFE_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Địa chỉ endpoint TypeSafe API
TYPESAFE_API_URL=https://api.typesafe.ai/v1/systemone

# 2. Cấu hình Local Intercepting Proxy
JOG_PROXY_HOST=127.0.0.1
JOG_PROXY_PORT=8080

# 3. Đường dẫn lưu vết kiểm toán bảo mật (Audit Log)
JOG_AUDIT_LOG=.jog/logs/audit.log
```
