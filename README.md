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

## 🔑 2. Cách Lấy API Key Cho JEV

*(Mặc định hệ thống chạy **Offline 100% miễn phí** không bắt buộc cần key. Nếu muốn kích hoạt thêm AI Cloud Reasoning, làm như sau):*

1. Truy cập: **[https://openrouter.ai/settings/keys](https://openrouter.ai/settings/keys)**
2. Đăng nhập bằng tài khoản **Google** hoặc **GitHub**.
3. Bấm **"Create Key"** ➔ đặt tên ➔ Copy chuỗi key (dạng `sk-or-v1-...`).
4. Tạo file `.env` tại thư mục dự án và dán vào:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
