"""Trace-backed regression cases for FM-03 and FM-08."""
from types import SimpleNamespace

import pytest

from lab8.shapes import SHAPES
from lab9.graders import DbFactKept, RefundAmountCorrect, ReplyAmountMatchesLedger, ProposalAmountCorrect
from lab9.trace_case import investigate
from lab9.variant_agent import make_shape

pytestmark = pytest.mark.student


def test_lab9_ticket_override_regression():
    for shape, expected in (("seeded_regression", False), ("fixed", True)):
        case = investigate(shape, "C-002", 11)
        ctx = SimpleNamespace(output=case["trial"], expected_output=case["label"])
        assert DbFactKept().evaluate(ctx).value is expected
        assert RefundAmountCorrect().evaluate(ctx).value is expected


def test_lab9_pre_deducted_proposal_with_unchanged_ledger():
    for shape, expected in (("seeded_regression", False), ("fixed", True)):
        case = investigate(shape, "C-013", 11)
        ctx = SimpleNamespace(output=case["trial"], expected_output=case["label"])
        assert RefundAmountCorrect().evaluate(ctx).value is True
        assert ProposalAmountCorrect().evaluate(ctx).value is expected


@pytest.mark.parametrize("claim", ["C-008", "C-014"])
def test_lab9_reply_amount_regression(monkeypatch, claim):
    monkeypatch.setitem(SHAPES, "test_misreport", make_shape("test_misreport", {"no_override", "misreport"}))
    for shape, expected in (("test_misreport", False), ("fixed", True)):
        case = investigate(shape, claim, 11)
        assert ReplyAmountMatchesLedger().evaluate(SimpleNamespace(output=case["trial"])).value is expected
