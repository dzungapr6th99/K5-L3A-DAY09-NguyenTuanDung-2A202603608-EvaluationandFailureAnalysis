# Judge audit

Số liệu tính lại từ CSV replay bằng lab9.judge.calibrate. FAIL là positive.

| Tiêu chí | n | κ | Precision | Recall | Đạt floors κ≥0.6, P≥0.8, R≥0.7 | Quyết định |
|---|---:|---:|---:|---:|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | Có | Có thể dùng cho tone trong phạm vi replay |
| helpful | 100 | 0.375 | 1.000 | 0.300 | Không | Không dùng làm gate |

Tone: TP=24, FP=4, FN=6, TN=66.
Helpful: TP=9, FP=0, FN=21, TN=70. Precision cao không bù được 21/30 lỗi bị bỏ sót.

## Năm bất đồng — nhận xét nháp do AI hỗ trợ, cần người học rà soát

Nhãn/note lấy từ CSV. Nhận xét dưới đây không phải lý do trực tiếp do judge xuất ra,
và không phải năm đánh giá người mới độc lập.

| Case | Judge | Human | Nhận xét ai hợp lý | Làm rõ rubric |
|---|---|---|---|---|
| H-008 | PASS | FAIL | Human phù hợp nếu áp dụng tone trang trọng: “nha”, “check giúp em” khá thân mật | Nêu mức thân mật được phép; không cấm đại từ “em” trong mọi ngữ cảnh |
| H-017 | PASS | FAIL | Note dựa vào khách lớn tuổi; reply riêng lẻ không chứng minh tuổi, nên kết luận phụ thuộc ngữ cảnh bổ sung | Cung cấp ngữ cảnh hoặc quy ước xưng hô trung tính, tránh bắt judge đoán tuổi |
| H-029 | PASS | FAIL | Human hợp lý: “không cần nhắn thêm” mang giọng gạt bỏ dù đầu câu lịch sự | Chấm toàn câu, không để từ “Dạ” che cách nói ra lệnh |
| H-042 | FAIL | PASS | Human hợp lý về tone: câu lịch sự, không nhất thiết cần lời xin lỗi | Không bắt xin lỗi trong mọi thông báo; tách kiểm tone khỏi kiểm tiền |
| H-051 | FAIL | PASS | Theo note cho phép từ “refund”, human hợp lý | Công bố thuật ngữ được phép, không tự phạt mọi từ tiếng Anh |

## Kết luận

Tone đạt floors trên tập replay, vẫn có báo nhầm/bỏ sót và chưa có held-out.
Helpful không đủ điều kiện làm gate; cần sửa rubric về tính hữu ích và đánh giá lại với nhãn người mới.
Không sửa nhãn chỉ để tăng điểm. Tiền và approval luôn chấm bằng code.

Chạy từ src:

```powershell
python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 5
python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5
```

Helpful exit 1 là kết quả calibration dự kiến.
