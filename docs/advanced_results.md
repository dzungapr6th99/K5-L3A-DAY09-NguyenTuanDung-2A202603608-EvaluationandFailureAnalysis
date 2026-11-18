# M5–M7 — kết quả và cách chạy lại

Ngày đo: 18/11/2026 (Asia/Saigon). Chỉ MockLLM offline; hidden grader không có trong checkout.
Bằng chứng máy đọc: src/reports/advanced_evidence.json.
Mã nguồn chưa commit được định danh bằng source_manifest_v2.json; không bịa SHA commit.

## M5: eval set v2 và slice

28 item × 5 seed, SHA 79b2666f4efc. 14 case v1 + 14 adversarial.
Map đủ 8 cơ chế sang FM-02…FM-09; mỗi FM bị tấn công có ít nhất 3 item.

Slice regression đạt pass_rate=0.9357 (trên sàn 0.85), pass_hat_5=0.8929 (trên sàn 0.85).
Gate chỉ chặn slice:money_movement/pass_rate; toàn cục không chặn.
Xem các dòng CI và mean slice đầy đủ trong advanced_evidence.json.

## M6: A/A và độ ổn định

Hai tập seed: 11/22/33/44/55 và 66/77/88/99/110.
Mọi metric có Δ=0 trên swarm; baseline pass_hat_5=0.8929.
Chọn sàn 0.85, dưới baseline 0.0429; đây là khoảng đệm thiết kế trên mẫu công khai.
Không suy ra noise của LLM thật bằng 0: cần lặp A/A độc lập nhiều lần và đặt sàn ngoài dải nhiễu.

Flaky: pass_rate=0.9143 vẫn vượt ngưỡng trung bình 0.85, nhưng pass_hat_5=0.5714 bị chặn.
Trong lần chạy này, pass_rate CI cũng chặn; không tuyên bố chỉ metric pass_hat_5 phát hiện.
Một bug 1/3 seed vẫn có thể không xuất hiện trong 5 seed; tăng số seed và dùng dữ liệu held-out
mới giúp đo ổn định. pass@k đo ít nhất một lần thành công; pass^k đo mọi lần đều thành công.

## M7: mutation và integrity

Mutation công khai: 3/3 regression bị chặn, 0 false alarm.
fixed/honest_refactor qua; seeded/slice/flaky bị chặn.

Bốn trap sinh bằng lab9.traps đều bị integrity chặn:
evaluator_errors_as_nan, dropped_failing_rows, cherry_picked_seeds, loosened_spec.
Loosened spec phải truyền --base-spec để so với spec đáng tin của baseline.

Kiểm tra thêm: dòng trùng nhưng giữ nguyên tổng số dòng; evaluator_failures trên report xanh;
row thiếu metric/nonfinite; đổi seed grid; thay slice tags; bỏ metric/slice/CI check/blocking;
nới min/max_increase và thay thứ tự row hợp lệ.
Report đầy đủ còn được tính lại aggregate từ rows để phát hiện sửa summary.

Gate vẫn có thể bị lừa nếu kẻ viết sửa cả từng row lẫn summary/baseline hoặc cả grader/CI,
hay cung cấp dữ liệu giả tự nhất quán. Không có chữ ký/attestation nguồn report.
Cần bảo vệ baseline, code grader, input/nhãn và workflow, tách quyền phê duyệt;
đối chiếu baseline đáng tin khi kiểm ratchet.

## Kiểm tra M3 bổ sung

ProposalAmountCorrect bổ sung để bắt C-013: proposal 0 thay vì 35.000 dù ledger đúng 0.
Chỉ kiểm ledger/reply bỏ sót cơ chế này. Sau sửa: detection 100%, false alarm 0%; nguồn advanced_evidence.json và detection_v1.txt. Số 75% là lần thử trước sửa, không dùng làm kết quả cuối.

## Chạy lại

Từ src, một lệnh sinh lại report, A/A, kiểm gate, mutation, trap và provenance:

```powershell
python -m lab9.verify_advanced
python -m pytest -q -m student -o addopts= -k lab9
```

Các lệnh checkpoint riêng:

```powershell
python -m lab9.evalset --v2 --build
python -m lab9.mutation --spec config/metric_spec_v2.yaml --baseline reports/baseline_v2.json
python -m lab9.mutation --spec config/metric_spec_v2.yaml --aa 66,77,88,99,110
python -m lab9.mutation --detect
python -m lab9.traps --pr reports/eval_slice_regression_v2.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
```

Script traps trả exit 0 nghĩa là tất cả trap bị chặn; mỗi lệnh gate trên trap phải trả exit 1.
File trap là mẫu gian lận cố ý, không dùng làm baseline/report đánh giá bình thường.
Không sửa JSON report bằng tay.
