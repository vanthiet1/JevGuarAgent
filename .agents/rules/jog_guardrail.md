# JOG Guardrail Rule for Antigravity AI Agents

## Mục đích
Quy định bắt buộc dành cho mọi AI Coding Agent hoạt động trong dự án nhằm đảm bảo an toàn tuyệt đối, ngăn rò rỉ bí mật và ngăn sinh mã nguồn chứa rủi ro kiến trúc tương lai.

## Nguyên tắc hoạt động
1. **Kiểm tra câu lệnh trước khi chạy (Action Safety):**
   - Trước khi thực thi bất kỳ lệnh shell/bash nào tiềm ẩn tác dụng phụ, Agent có thể kiểm tra trước bằng lệnh:
     ```bash
     jog check prompt --json "<câu_lệnh>"
     ```
   - Nếu kết quả trả về `"action_verdict": "block_immediately"`, Agent **tuyệt đối không được thực thi lệnh đó** và phải thông báo lý do vi phạm cho người dùng.

2. **Kiểm tra mã nguồn trước khi ghi file (Code Health Inspection):**
   - Khi chuẩn bị sinh mã nguồn mới hoặc chỉnh sửa tệp, Agent có thể kiểm tra nhanh bằng lệnh:
     ```bash
     jog check code --json "<đường_dẫn_tệp_hoặc_đoạn_code>"
     ```
   - Nếu kết quả trả về `"maintainability_verdict": "reject_force_agent_rewrite"`:
     - Agent đọc mảng `"remediation_suggestions"` và `"detected_flaws"` trong JSON trả về của Jev.
     - Agent tự động viết lại code sạch (sử dụng Parameterized Queries thay vì SQL nối chuỗi, sử dụng `with open()`, thêm `timeout` vào HTTP calls).

3. **Cơ chế Local Proxy:**
   - Khi kết nối thông qua JOG Local Proxy (`http://127.0.0.1:8080/v1`):
   - Nếu nhận phản hồi `HTTP 403 Forbidden` với mã lỗi `jog_blocked_force_rewrite`, Agent phải phân tích trường `error.message` và tự động kích hoạt chu trình sửa lỗi (Self-Correction Loop).
