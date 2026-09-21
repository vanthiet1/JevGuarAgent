#!/usr/bin/env python3
"""
tests/run_all_tests.py
======================
Kịch bản thực thi toàn bộ bài kiểm thử tự động của JOG.
Tổng hợp kết quả và hiển thị báo cáo chi tiết cho SecOps / AI Engineers.
"""

import sys
import unittest
import time
from pathlib import Path

# Đảm bảo đường dẫn gốc nằm trong sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.test_engine import TestJevEngineMode1, TestJevEngineMode2
from tests.test_cli import TestCliInterceptor
from tests.test_proxy import TestLocalProxy
from tests.test_pre_commit import TestPreCommitGuard


def run_full_suite() -> int:
    """Nạp tất cả các test case và thực thi."""
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    suite.addTests(loader.loadTestsFromTestCase(TestJevEngineMode1))
    suite.addTests(loader.loadTestsFromTestCase(TestJevEngineMode2))
    suite.addTests(loader.loadTestsFromTestCase(TestCliInterceptor))
    suite.addTests(loader.loadTestsFromTestCase(TestLocalProxy))
    suite.addTests(loader.loadTestsFromTestCase(TestPreCommitGuard))

    print("\n" + "=" * 75)
    print("🧪  KHỞI CHẠY BỘ KIỂM THỬ TỰ ĐỘNG TOÀN DIỆN JEV GUARDRAIL (JOG)")
    print("=" * 75)
    print(f"Tổng số bài kiểm tra đã nạp: {suite.countTestCases()}")
    print("-" * 75 + "\n")

    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    duration = time.time() - start_time

    print("\n" + "=" * 75)
    print("📊  BÁO CÁO TỔNG KẾT KIỂM THỬ AN TOÀN")
    print("=" * 75)
    print(f"• Tổng số bài kiểm tra : {result.testsRun}")
    print(f"• Thành công            : {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"• Thất bại (Failures)   : {len(result.failures)}")
    print(f"• Lỗi (Errors)          : {len(result.errors)}")
    print(f"• Thời gian thực thi    : {duration:.2f} giây")

    if result.wasSuccessful():
        print("\n🎉 KẾT QUẢ: 100% CÁC BÀI KIỂM THỬ ĐÃ VƯỢT QUA! HỆ THỐNG SẴN SÀNG!")
        print("=" * 75 + "\n")
        return 0
    else:
        print("\n❌ KẾT QUẢ: CÓ BÀI KIỂM THỬ KHÔNG ĐẠT TIÊU CHUẨN!")
        print("=" * 75 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_full_suite())
