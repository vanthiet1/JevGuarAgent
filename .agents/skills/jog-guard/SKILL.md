---
name: jog-guard
description: Jev Omnichannel Guardrail integration skill. Use this skill to inspect shell commands for destructive actions/secret leaks and inspect source code for future stability risks (SQLi, memory leaks, unclosed streams, missing timeouts) before applying changes.
---

# JOG Guardrail Skill

Skill này hướng dẫn AI Agent phối hợp cùng hệ thống **Jev Omnichannel Guardrail (JOG)** đặt tại `./bin/jog`.

## Cách thức sử dụng

### 1. Kiểm tra an toàn lệnh Shell / Bash
Chạy lệnh sau từ thư mục dự án:
```bash
./bin/jog check prompt --json "<câu_lệnh_cần_chạy>"
```

**Cách đọc kết quả JSON:**
- `action_verdict`:
  - `"allow"`: Lệnh hoàn toàn an toàn, có thể thực thi.
  - `"warn_user"`: Lệnh có tác dụng phụ, cần thông báo và hỏi ý kiến người dùng trước.
  - `"block_immediately"`: Lệnh nguy hiểm (phá hoại hoặc lộ bí mật). **Hủy ngay lập tức**.

### 2. Kiểm tra sức khỏe mã nguồn (Code Health & Future Risks)
Chạy lệnh sau để Jev chẩn đoán:
```bash
./bin/jog check code --json "<đường_dẫn_tệp_hoặc_đoạn_mã>"
```

**Cách đọc kết quả JSON:**
- `maintainability_verdict`:
  - `"pass"`: Code an toàn, đạt chuẩn.
  - `"warn_dev_needs_refactor"`: Code có thể tối ưu thêm.
  - `"reject_force_agent_rewrite"`: Code có rủi ro nghiêm trọng (SQL Injection, Memory Leak, N+1 Query, thiếu timeout).
- `detected_flaws`: Danh sách các lỗi kiến trúc Jev đã phát hiện.
- `remediation_suggestions`: Hướng dẫn cụ thể để Agent sửa lại code.
