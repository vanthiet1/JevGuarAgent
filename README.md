# 🛡️ Jev Omnichannel Guardrail (JOG) `v1.0.0`

> Tối ưu chất lượng mã nguồn và tiết kiệm token cho các AI agent khi viết code (Cursor, VS Code, Antigravity, Claude Code, Codex).

---

## ⚡ 1. Các Câu Lệnh Chạy

| Hệ điều hành | Kích hoạt bảo vệ | Kiểm tra trạng thái | Hủy kích hoạt |
| :--- | :--- | :--- | :--- |
| **Windows (CMD / PowerShell)** | `.\guar active` | `.\guar status` | `.\guar deactive` |
| **macOS / Linux** | `./guar active` | `./guar status` | `./guar deactive` |
| **Universal (Mọi OS)** | `python guar.py active` | `python guar.py status` | `python guar.py deactive` |

> **Chạy nhanh 1 bước:**
> Chạy `.\guar active` (Windows) hoặc `./guar active` (Mac/Linux) để tự động kích hoạt toàn bộ bảo vệ.

---

## 🔑 2. Cách Lấy API Key Cho JEV & Cấu Hình `.env`

*(Mặc định hệ thống chạy **Offline 100% miễn phí** không bắt buộc cần key. Nếu muốn kích hoạt thêm AI Cloud Reasoning, làm theo các bước sau):*

1. **Lấy API Key:** Truy cập **[https://openrouter.ai/settings/keys](https://openrouter.ai/settings/keys)** (hoặc [https://typesafe.ai](https://typesafe.ai)) ➔ Đăng nhập ➔ Bấm **"Create Key"** ➔ Copy token dạng `sk-or-v1-...`.
2. **Cấu hình file `.env`:**
   - Khi tải/clone về, sao chép hoặc đổi tên file `.env.example` thành `.env`:
     ```bash
     cp .env.example .env
     ```
   - Dán API Key vừa lấy vào file `.env`:
     ```env
     OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
     ```
   *(🔒 **Bảo mật:** File `.env` chứa key bí mật đã được cấu hình trong `.gitignore`, Git sẽ tự động bỏ qua và không đọc/commit file này).*

