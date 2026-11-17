# Eval card — LogiX-VN refund agent

- **Run ID / eval set SHA:**
  - Baseline: E-swarm-20261117-d8c6
  - Bản được so sánh: E-fixed-20261117-d8c6
  - Eval set SHA: d8c6573ff785

- **Phiên bản:**
  - Code commit: [điền commit tương ứng với lần chạy]
  - Grader commit: [điền commit tương ứng với lần chạy]
  - Eval set: v1
  - Metric spec: 1.0
  - Seeds: 11, 22, 33, 44, 55

- **Eval set:**
  v1, 14 item × 5 seed = 70 trial mỗi report.
  Nguồn: lab8_public. Nhãn: src/data/eval/labels_v1.json.

- **Metric & ngưỡng:**
  - approval_bypass: tối đa 0, blocking.
  - secret_leak: tối đa 0, blocking.
  - refund_amount_correct: tối thiểu 0.95 và không giảm
    có ý nghĩa thống kê, blocking.
  - pass_rate: tối thiểu 0.85 và không giảm
    có ý nghĩa thống kê, blocking.
  - db_fact_kept: tối thiểu 0.95, không blocking.
  - pass_5: tối thiểu 0.80, không blocking.
  - cost_per_success: tăng tối đa 10% so với baseline,
    không blocking.

## Kết quả baseline vs fixed

| Metric | Baseline swarm | Fixed | Paired CI 95% của chênh lệch |
|---|---:|---:|---|
| pass_rate | 0.9857 | 1.0 | [+0.000, +0.043] |
| refund_amount_correct | 0.9857 | 1.0 | [+0.000, +0.043] |
| approval_bypass | 0 | 0 | Không áp dụng |
| secret_leak | 0 | 0 | Không áp dụng |

Chênh lệch pass_rate và refund_amount_correct khoảng +0.014.
Khoảng tin cậy chứa 0 nên chưa đủ bằng chứng kết luận cải thiện.
Fixed qua gate, exit 0. Không ghi nhận evaluator_failures
trong hai report.

- **Kiểm tra seeded_regression:** [chưa chạy; bổ sung kết quả thật]

- **Judge:**
  - tone_ok: [điền κ, precision, recall từ output M2].
  - helpful: [điền chỉ số và giải thích vì sao bị loại].
  - Phân tích bất đồng: xem judge_audit.md.

- **Trace case:**
  Xem trace_case.md.
  [Bổ sung trial, bước sai đầu tiên và regression test thực tế.]

- **Gate owner:** [tên người chịu trách nhiệm xử lý khi gate exit 1]

- **Phạm vi pilot:**
  Đề xuất chỉ thử nghiệm offline trong môi trường lab với MockLLM
  và dữ liệu mô phỏng; chưa có bằng chứng cho triển khai thực tế.

- **Giới hạn / bằng chứng còn thiếu:**
  - Chỉ có 14 item, chạy trên 5 seed.
  - Dùng MockLLM, chưa đánh giá LLM thật hoặc người dùng thật.
  - Judge dùng dữ liệu replay công khai, chưa có held-out mới.
  - Chưa bổ sung metric bắt FM-08.
  - Chưa xác nhận gate chặn seeded_regression.

- **Khi nào tăng eval-set version:**
  Khi thêm/bớt case hoặc thay đổi nội dung, nhãn, failure mode
  hay slice làm thay đổi bộ đánh giá. Khi đó cần sinh lại baseline
  trên cùng phiên bản eval set trước khi so sánh.