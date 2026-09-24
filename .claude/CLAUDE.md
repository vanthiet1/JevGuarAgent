<!-- JOG_GUARDRAIL_START -->
# JOG Guardrail & Security Rules for AI Agent

> ⚠️ **CHỈ THỊ BẮT BUỘC ĐỐI VỚI AI AGENT / GITHUB COPILOT / CLAUDE / CURSOR**:
> Mỗi khi suy nghĩ, trả lời hoặc thực thi công cụ/mã nguồn, bạn BẮT BUỘC PHẢI xuất dòng thông báo đầu tiên trên chat:
> `🛡️ [Jev Guardrail] Đã trả kết quả: đang phân tích và thực thi... (Quyết định: ALLOW • Điểm rủi ro: 1.0/10 - An toàn)`

## 1. Phạm vi áp dụng
Quy tắc này bắt buộc đối với mọi AI Coding Agent hoạt động trong dự án.
Hệ thống sử dụng bộ não phòng thủ **Jev Omnichannel Guardrail (JOG)** đặt tại: `./bin/jog`.

---

## 2. Kiểm tra an toàn câu lệnh (Command Safety)
Trước khi thực thi các lệnh terminal có tác dụng phụ (xóa file, cài package lạ, cấu hình mạng, export secrets), Agent bắt buộc phải kiểm tra thông qua JOG:

```bash
./bin/jog check prompt --json "<câu_lệnh>"
```

* **Nếu `"action_verdict": "allow"`**: Được phép thực thi lệnh an toàn.
* **Nếu `"action_verdict": "warn_user"`**: Cảnh báo rủi ro tiềm ẩn và hỏi ý kiến người dùng trước khi chạy.
* **Nếu `"action_verdict": "block_immediately"`**: **TUYỆT ĐỐI KHÔNG CHẠY LỆNH NÀY**. Báo cáo ngay cho người dùng lý do vi phạm (lệnh phá hoại, rò rỉ secret, xóa file hệ thống).

---

## 3. Kiểm tra an toàn mã nguồn (Code Health & Future Risks)
Trước khi ghi đè hoặc tạo mới các file logic quan trọng, Agent sử dụng JOG để phân tích các rủi ro kiến trúc tương lai (SQL Injection, N+1 Query, Memory Leak, thiếu timeout HTTP):

```bash
./bin/jog check code --json "<đường_dẫn_tệp>"
```

* **Nếu `"maintainability_verdict": "pass"`**: Code đảm bảo chất lượng.
* **Nếu `"maintainability_verdict": "reject_force_agent_rewrite"`**:
  * Agent đọc kỹ mảng `detected_flaws` và `remediation_suggestions` do JOG trả về.
  * Tự động sửa lại code sạch (sử dụng Parameterized Query, gán timeout cho network fetch, giải phóng tài nguyên) trước khi cung cấp cho người dùng.

---

## 4. Phỏng đoán rủi ro & Xử lý trọn vẹn Edge Cases (Proactive Architecture Advisory)
Khi nhận yêu cầu phát triển tính năng từ người dùng (Realtime, Upload file, Thanh toán, Auth, Caching, DB Query, Background Jobs):
* Agent kiểm tra trước qua:
  ```bash
  ./bin/jog check prompt --json "<mô_tả_yêu_cầu>"
  ```
* Nếu trường `predicted_edge_cases` có dữ liệu:
  * Agent **BẮT BUỘC** đọc kỹ danh sách `risk_factors` (các trường hợp góc / edge cases tiềm ẩn như Double Spending, Race Condition, Unclosed File Descriptor, Missing Timeout, Cache Stampede...).
  * Agent thiết kế mã nguồn bao quát toàn diện các case này theo `recommended_patterns` và `injected_prompt_directive` ngay từ đầu, đảm bảo tính ổn định tuyệt đối trước khi bàn giao cho người dùng.

---

## 5. Quy chuẩn phản hồi người dùng (User Visibility & Status Directive)
Trong suốt quá trình suy nghĩ (Thinking) và thực thi công cụ/mã nguồn, mỗi khi chuẩn bị phân tích hoặc thực thi một hành động, Agent BẮT BUỘC phải xuất thông báo rõ ràng lên giao diện chat cho người dùng thấy:
`🛡️ [Jev Guardrail] Đã trả kết quả: đang phân tích và thực thi...`
kèm theo tóm tắt phán quyết kiểm tra an toàn (Ví dụ: `Quyết định: ALLOW • Điểm rủi ro: 1.0/10 (An toàn)`).

<!-- JOG_GUARDRAIL_END -->
