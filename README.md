# 🛡️ Jev Omnichannel Guardrail (JOG) `v1.0.0`

> Tối ưu chất lượng mã nguồn, ngăn chặn ảo giác do AI gây ra và tiết kiệm token cho các AI agent khi viết code (Cursor, VS Code, Antigravity, Claude Code, Codex).

---

## ⚡ 1. Khởi Chạy Lần Đầu

> 💡 **Tự động 100% (Zero-Setup):**
> - **Máy đã có Python:** Chạy thông thường ngay lập tức.
> - **Máy chưa có Python:** Lệnh sẽ **tự động tải và cài đặt Python** rồi tự khởi động bảo vệ luôn.
> - **Không cần cài thư viện ngoài:** 100% chạy bằng thư viện chuẩn Python (không cần `pip install`).

Khi vừa clone về, mở terminal tại thư mục dự án và chạy:
* **Trên Windows:**
  ```cmd
  .\guar active
  ```
* **Trên macOS / Linux:**
  ```bash
  ./guar active
  ```
*(Hệ thống sẽ tự kích hoạt bảo vệ và tự động đăng ký lệnh `guar` vào máy để từ lần sau bạn có thể gõ trực tiếp `guar active` ở bất cứ đâu).*

---

## 📋 2. Các Câu Lệnh Chạy

| Chức năng | Câu lệnh |
| :--- | :--- |
| **Kích hoạt bảo vệ** | `guar active` |
| **Kiểm tra trạng thái** | `guar status` |
| **Hủy kích hoạt** | `guar deactive` |

---

## 🔑 3. Cách Lấy API Key Cho JEV & Cấu Hình `.env`

*(Mặc định hệ thống chạy **Offline 100% miễn phí** không bắt buộc cần key. Nếu muốn kích hoạt thêm AI Cloud Reasoning, làm theo các bước sau):*

1. **Lấy API Key:** Truy cập **[https://openrouter.ai/settings/keys](https://openrouter.ai/settings/keys)** (hoặc [https://typesafe.ai](https://typesafe.ai)) ➔ Đăng nhập ➔ Bấm **"Create Key"** ➔ Copy token dạng `sk-or-v1-...`.
2. **Cấu hình file `.env`:**
   - Sao chép hoặc đổi tên file `.env.example` thành `.env`:
     ```bash
     cp .env.example .env
     ```
   - Lấy key theo hướng dẫn ở bước 1 và điền vào file `.env`:
     ```env
     OPENROUTER_API_KEY=<lấy_key_theo_hướng_dẫn_ở_bước_1>
     ```
