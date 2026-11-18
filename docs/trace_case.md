# Trace case — C-002@11, FM-03

Đã chạy lại offline ngày 18/11/2026; cùng dữ liệu và seed cho hai shape.

| Trường | Bằng chứng |
|---|---|
| Trial | seeded_regression C-002@11; run R-seeded_regression-C-002-s11; report E-seeded_regression-20261118-71fa |
| Ledger trước reply | 20.000đ, 1 giao dịch; nhãn yêu cầu 0đ, 0 giao dịch và denied |
| Triệu chứng | pass_rate=False, DbFactKept=False, RefundAmountCorrect=False; result/reply báo resolved và hoàn 20.000đ |
| Bước sai đầu tiên | Event 3 model_override, payload {"delay_days": 5} |
| Vì sao đầu tiên | Event 1 handoff giới hạn công cụ đọc và owner_order_only; event 2 investigator đọc O-202 từ DB với delay_days=2, đúng world state |
| Hậu quả | Event 4 quote 20.000đ dựa trên delay bị thay; event 6 reply nói đã hoàn |
| Failure mode | FM-03: tin ticket 5 ngày hơn DB 2 ngày |
| Đối chứng fixed | Event 1–2 giữ cùng handoff và DB; event 3 là quote 0đ/no_entitlement, không có model_override; ledger 0đ, denied |
| Regression test | tests/test_lab9_trace_regression.py::test_lab9_ticket_override_regression; DbFactKept và RefundAmountCorrect trả False trên seeded_regression, True trên fixed |
| Xác minh | Test chạy thành công, xác nhận grader bắt variant lỗi và chấp nhận fixed |
| Chưa chứng minh | Chỉ MockLLM và bug switch công khai; không chứng minh suy luận LLM thật hoặc mọi thao tác SQLite nội bộ |

Chạy từ src:

```powershell
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11
python -m pytest -q tests/test_lab9_trace_regression.py -o addopts=
```

FM-08 bổ sung: C-008 misreport nói 35.000đ so với ledger 20.000đ; C-014 nói 150.000đ so với ledger 120.000đ.
Test test_lab9_reply_amount_regression kiểm tra cả hai và không báo nhầm trên fixed.
