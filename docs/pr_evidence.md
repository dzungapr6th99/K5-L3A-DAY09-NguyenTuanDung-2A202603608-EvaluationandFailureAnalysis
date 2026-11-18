# Bằng chứng để đưa vào mô tả PR

## Thay đổi

Hoàn thiện M5–M7: eval set v2, slice gate, pass@k/pass^k, kiểm integrity và ratchet.
Bổ sung ProposalAmountCorrect để M3 giải thích được lỗi tính proposal mà ledger host đã chặn.
Cập nhật eval card, taxonomy, judge audit, trace case, PRD và harness map.

Code nền: 8f32411d19c31794adc7af07d113a8fb64166da7; thay đổi tại thời điểm đo chưa commit.
Hash snapshot và từng file: src/reports/source_manifest_v2.json.
Các nhận xét audit/đề xuất trách nhiệm do AI hỗ trợ, chưa phải phê duyệt nhóm.

## Kiểm tra local ngày 18/11/2026

- Core theo bộ lọc CI: 15 passed.
- Advanced theo bộ lọc CI: 24 passed.
- Eval set v1/v2: 0 problem(s).
- Core ci_check: exit 0.
- Gate swarm/fixed: exit 0.
- M3 detection: 100%; false alarms: 0%.
- A/A hai bộ seed: mọi metric Δ=0.
- Mutation: 3/3, false alarms 0.
- Slice regression chỉ bị money_movement chặn.

Core seeded_regression (xem src/reports/core_gate.txt):

```text
pass_rate 0.7143, Δ -0.271, CI [-0.500, -0.057]
exit 1 — blocked: refund_amount_correct, pass_rate, reply_amount_matches_ledger
```

Advanced mutation (xem src/reports/mutation_v2.txt):

```text
fixed: merge
honest_refactor: merge
seeded_regression: block
slice_regression: block (slice:money_movement/pass_rate)
flaky_regression: block
mutation score 3/3 · false alarms 0
```

Bốn lần gọi gate riêng (xem src/reports/gate_traps_v2.txt):

```text
evaluator_errors_as_nan: exit 1 — blocked: integrity
dropped_failing_rows: exit 1 — blocked: integrity
cherry_picked_seeds: exit 1 — blocked: integrity
loosened_spec: exit 1 — blocked: integrity (có --base-spec)
```

Chạy lại từ src:

```powershell
python -m lab9.verify_advanced
python -m pytest -q -m student -o addopts= -k lab9
```

Không có kết quả hidden grader hoặc LLM thật. CI trên GitHub sau thay đổi này chưa được chạy từ môi trường local.
