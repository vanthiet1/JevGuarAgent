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
2. **Tạo file `.env`:** Tạo file `.env` tại thư mục dự án và dán key vào:

```env
# Khóa xác thực TypeSafe AI / OpenRouter API (Thay bằng key bạn vừa lấy ở bước 1)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
