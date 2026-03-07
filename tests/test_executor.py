"""
Tests for BusinessFlow AI — Executor Agent
===========================================
Run with:  pytest tests/ -v

All tests fully offline — no Azure calls needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pytest

from executor_agent.executor import (
    AuditEntry,
    ExecutionResult,
    ExecutorAgent,
    MockExecutorDB,
    MockNotifier,
    PurchaseOrder,
)
from policy_layer.policy import Decision, PolicyConfig, PolicyDecision, PolicyLayer
from retriever_agent.retriever import RetrieverAgent


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

@dataclass
class _Item:
    sku_id: str
    product_name: str = "Test Product"
    quantity: int = 100
    unit_price: float = 200.0
    total_cost: float = 20000.0


@dataclass
class _Plan:
    plan_id: str = "exec-plan-001"
    supplier_name: str = "Sunrise Textiles"
    supplier_email: str = "ramesh@sunrise-textiles.in"
    email_subject: str = "Test"
    line_items: list = field(default_factory=list)
    total_order_value: float = 20000.0
    confidence_score: float = 0.95
    delivery_date: str = "2025-07-15"


def _approved_decision(plan_id="exec-plan-001", value=20000.0) -> PolicyDecision:
    """Build a pre-approved PolicyDecision."""
    return PolicyDecision(
        plan_id=plan_id,
        decision=Decision.AUTO_APPROVE,
        reasons=["Within auto-approve limit"],
        rule_results=[],
        total_order_value=value,
    )


def _full_pipeline(sku_ids: list[str], total_value: float, confidence=0.95):
    """Run the full Retriever + Policy pipeline and return plan, ctx, decision."""
    plan = _Plan(total_order_value=total_value, confidence_score=confidence)
    plan.line_items = [_Item(sku_id=s) for s in sku_ids]

    ctx = RetrieverAgent(backend="mock").retrieve(plan)
    decision = PolicyLayer(PolicyConfig(auto_approve_limit=50000.0)).evaluate(plan, ctx)
    return plan, ctx, decision


# ---------------------------------------------------------------------------
# MockExecutorDB unit tests
# ---------------------------------------------------------------------------

class TestMockExecutorDB:
    def test_get_known_stock(self):
        db = MockExecutorDB()
        assert db.get_stock("SKU-TSH-001") == 45

    def test_update_stock_returns_old_and_new(self):
        db = MockExecutorDB()
        old, new = db.update_stock("SKU-TSH-001", 100)
        assert old == 45
        assert new == 145

    def test_update_stock_persists(self):
        db = MockExecutorDB()
        db.update_stock("SKU-TSH-001", 50)
        assert db.get_stock("SKU-TSH-001") == 95

    def test_update_unknown_sku_raises(self):
        db = MockExecutorDB()
        with pytest.raises(ValueError):
            db.update_stock("SKU-FAKE-999", 10)

    def test_create_purchase_order(self):
        db = MockExecutorDB()
        po = PurchaseOrder(
            po_id="PO-001", plan_id="plan-001", sku_id="SKU-TSH-001",
            supplier_name="Test", supplier_email="t@t.com",
            quantity_ordered=100, unit_price=180.0, total_cost=18000.0,
        )
        assert db.create_purchase_order(po) is True
        orders = db.get_all_purchase_orders()
        assert len(orders) == 1
        assert orders[0]["sku_id"] == "SKU-TSH-001"

    def test_write_audit_log(self):
        db = MockExecutorDB()
        entry = AuditEntry(log_id="L001", plan_id="plan-001", agent="EXECUTOR",
                           action="TEST", details="test entry")
        assert db.write_audit_log(entry) is True
        logs = db.get_audit_log("plan-001")
        assert len(logs) == 1
        assert logs[0]["action"] == "TEST"


# ---------------------------------------------------------------------------
# ExecutorAgent tests
# ---------------------------------------------------------------------------

class TestExecutorAgent:

    def test_execute_approved_small_order(self):
        """AUTO_APPROVE decision → full execution."""
        plan, ctx, decision = _full_pipeline(["SKU-BAG-011"], total_value=11500.0)
        assert decision.decision == Decision.AUTO_APPROVE

        agent = ExecutorAgent(backend="mock")
        result = agent.execute(plan, ctx, decision)

        assert result.success is True
        assert result.orders_created == 1
        assert result.total_executed_value > 0
        assert len(result.inventory_updates) == 1

    def test_stock_increases_after_execution(self):
        """Inventory should go up after execution."""
        plan, ctx, decision = _full_pipeline(["SKU-BAG-011"], total_value=11500.0)

        db = MockExecutorDB()
        old_stock = db.get_stock("SKU-BAG-011")

        notifier = MockNotifier()
        agent = ExecutorAgent(backend="mock", notifier=notifier)
        agent._db = db  # inject our db instance

        result = agent.execute(plan, ctx, decision)
        new_stock = db.get_stock("SKU-BAG-011")

        assert new_stock > old_stock
        update = result.inventory_updates[0]
        assert update["sku_id"] == "SKU-BAG-011"
        assert update["new_stock"] == update["old_stock"] + update["added"]

    def test_purchase_orders_created(self):
        """One PO should be created per executed line item."""
        plan, ctx, decision = _full_pipeline(["SKU-BAG-011"], total_value=11500.0)
        db = MockExecutorDB()
        agent = ExecutorAgent(backend="mock")
        agent._db = db
        result = agent.execute(plan, ctx, decision)

        pos = db.get_all_purchase_orders()
        assert len(pos) == 1
        assert pos[0]["sku_id"] == "SKU-BAG-011"
        assert pos[0]["status"] == "EXECUTED"

    def test_audit_log_written(self):
        """At least pipeline start, item actions, and completion should be logged."""
        plan, ctx, decision = _full_pipeline(["SKU-BAG-011"], total_value=11500.0)
        db = MockExecutorDB()
        agent = ExecutorAgent(backend="mock")
        agent._db = db
        result = agent.execute(plan, ctx, decision)

        logs = db.get_audit_log(plan.plan_id)
        assert len(logs) >= 3   # start + stock_update + po_created + complete
        actions = [l["action"] for l in logs]
        assert "PIPELINE_START"    in actions
        assert "PIPELINE_COMPLETE" in actions

    def test_notification_sent(self):
        """Notification should be sent after execution."""
        plan, ctx, decision = _full_pipeline(["SKU-BAG-011"], total_value=11500.0)
        notifier = MockNotifier()
        agent = ExecutorAgent(backend="mock", notifier=notifier)
        result = agent.execute(plan, ctx, decision)

        assert result.notification_sent is True
        assert len(notifier.sent) == 1
        assert plan.supplier_email in notifier.sent[0]["to"]

    def test_blocks_non_approved_decision(self):
        """ESCALATE or REJECT decisions must NOT be executed."""
        plan, ctx, decision = _full_pipeline(["SKU-TSH-001"], total_value=247500.0)
        assert decision.decision == Decision.ESCALATE

        agent = ExecutorAgent(backend="mock")
        result = agent.execute(plan, ctx, decision)

        assert result.success is False
        assert result.orders_created == 0
        assert result.error_message is not None

    def test_skips_adequate_stock_items(self):
        """Items with adequate stock should be skipped, not executed."""
        plan = _Plan(total_order_value=5000.0)
        plan.line_items = [_Item(sku_id="SKU-CAP-003")]  # stock=200, threshold=40 — adequate
        ctx = RetrieverAgent(backend="mock").retrieve(plan)

        # Force an approved decision (bypass policy for this test)
        decision = _approved_decision(plan_id=plan.plan_id, value=5000.0)

        agent = ExecutorAgent(backend="mock")
        result = agent.execute(plan, ctx, decision)

        # Should succeed but skip the item (stock adequate)
        assert result.orders_created == 0
        assert len(result.skipped_items) == 1
        assert "adequate" in result.skipped_items[0].lower()

    def test_execution_result_summary_is_string(self):
        plan, ctx, decision = _full_pipeline(["SKU-BAG-011"], total_value=11500.0)
        agent = ExecutorAgent(backend="mock")
        result = agent.execute(plan, ctx, decision)
        summary = result.summary()
        assert isinstance(summary, str)
        assert plan.plan_id in summary

    def test_multiple_items_executed(self):
        """Multiple low-stock items in one plan should all get POs."""
        plan = _Plan(total_order_value=40000.0)
        plan.line_items = [
            _Item(sku_id="SKU-BAG-011", total_cost=11500.0),
            _Item(sku_id="SKU-JNS-042", total_cost=20000.0),
        ]
        ctx = RetrieverAgent(backend="mock").retrieve(plan)
        decision = _approved_decision(plan_id=plan.plan_id, value=40000.0)

        db = MockExecutorDB()
        agent = ExecutorAgent(backend="mock")
        agent._db = db
        result = agent.execute(plan, ctx, decision)

        assert result.orders_created == 2
        assert len(result.inventory_updates) == 2

    def test_po_has_correct_supplier_info(self):
        """PO should carry supplier name and email from the plan."""
        plan, ctx, decision = _full_pipeline(["SKU-BAG-011"], total_value=11500.0)
        db = MockExecutorDB()
        agent = ExecutorAgent(backend="mock")
        agent._db = db
        agent.execute(plan, ctx, decision)

        pos = db.get_all_purchase_orders()
        assert pos[0]["supplier_name"] == plan.supplier_name

    def test_execution_result_total_value(self):
        """total_executed_value should equal sum of all PO costs."""
        plan, ctx, decision = _full_pipeline(["SKU-BAG-011"], total_value=11500.0)
        agent = ExecutorAgent(backend="mock")
        result = agent.execute(plan, ctx, decision)

        expected = sum(po.total_cost for po in result.purchase_orders)
        assert result.total_executed_value == expected

    def test_rejected_decision_produces_no_pos(self):
        """A REJECT decision must not create any purchase orders."""
        plan, ctx, decision = _full_pipeline(["SKU-FAKE-999"], total_value=5000.0)
        assert decision.decision.value == "REJECT"

        db = MockExecutorDB()
        agent = ExecutorAgent(backend="mock")
        agent._db = db
        agent.execute(plan, ctx, decision)

        assert len(db.get_all_purchase_orders()) == 0

    def test_audit_log_contains_stock_updated_action(self):
        """STOCK_UPDATED action must appear in audit log after execution."""
        plan, ctx, decision = _full_pipeline(["SKU-BAG-011"], total_value=11500.0)
        db = MockExecutorDB()
        agent = ExecutorAgent(backend="mock")
        agent._db = db
        agent.execute(plan, ctx, decision)

        actions = [e["action"] for e in db.get_audit_log(plan.plan_id)]
        assert "STOCK_UPDATED" in actions

    def test_audit_log_contains_po_created_action(self):
        """PO_CREATED action must appear in audit log after execution."""
        plan, ctx, decision = _full_pipeline(["SKU-BAG-011"], total_value=11500.0)
        db = MockExecutorDB()
        agent = ExecutorAgent(backend="mock")
        agent._db = db
        agent.execute(plan, ctx, decision)

        actions = [e["action"] for e in db.get_audit_log(plan.plan_id)]
        assert "PO_CREATED" in actions