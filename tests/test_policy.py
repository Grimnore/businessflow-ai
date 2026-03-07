"""
Tests for BusinessFlow AI — Policy Layer
=========================================
Run with:  pytest tests/ -v

All tests are fully offline — no Azure calls needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pytest

from policy_layer.policy import (
    Decision,
    PolicyConfig,
    PolicyDecision,
    PolicyLayer,
    RuleResult,
    rule_cost_threshold,
    rule_low_confidence,
    rule_missing_skus,
    rule_stock_adequacy,
    rule_unit_price_anomaly,
)
from retriever_agent.retriever import MockDB, RetrieverAgent, SKUContext, StockContext


# ---------------------------------------------------------------------------
# Stubs — minimal plan and line item objects
# ---------------------------------------------------------------------------

@dataclass
class _LineItem:
    sku_id: str
    product_name: str = "Test Product"
    quantity: int = 100
    unit_price: float = 200.0
    total_cost: float = 20000.0


@dataclass
class _Plan:
    plan_id: str = "test-plan-001"
    supplier_name: str = "Test Supplier"
    supplier_email: str = "supplier@test.com"
    email_subject: str = "Test"
    line_items: list = field(default_factory=list)
    total_order_value: float = 20000.0
    confidence_score: float = 0.95
    delivery_date: str = "2025-07-15"


def _make_plan(**kwargs) -> _Plan:
    p = _Plan(**kwargs)
    if not p.line_items:
        p.line_items = [_LineItem(sku_id="SKU-TSH-001")]
    return p


def _make_stock(skus: list[SKUContext], missing=None) -> StockContext:
    return StockContext(plan_id="test-plan-001", sku_contexts=skus, missing_skus=missing or [])


def _sku(sku_id="SKU-TSH-001", stock=45, threshold=50, cost=160.0, found=True) -> SKUContext:
    return SKUContext(
        sku_id=sku_id, product_name="Test", current_stock=stock,
        reorder_threshold=threshold, unit_cost=cost, found=found
    )


CFG = PolicyConfig(auto_approve_limit=50000.0, min_confidence=0.70, max_unit_price_ratio=2.0)


# ---------------------------------------------------------------------------
# Rule: missing_skus
# ---------------------------------------------------------------------------

class TestRuleMissingSkus:
    def test_rejects_when_sku_missing(self):
        plan = _make_plan()
        ctx = _make_stock([_sku(found=False)], missing=["SKU-TSH-001"])
        result = rule_missing_skus(plan, ctx, CFG)
        assert result.triggered is True
        assert result.decision == Decision.REJECT

    def test_passes_when_all_found(self):
        plan = _make_plan()
        ctx = _make_stock([_sku()])
        result = rule_missing_skus(plan, ctx, CFG)
        assert result.triggered is False
        assert result.decision is None


# ---------------------------------------------------------------------------
# Rule: low_confidence
# ---------------------------------------------------------------------------

class TestRuleLowConfidence:
    def test_escalates_below_threshold(self):
        plan = _make_plan(confidence_score=0.50)
        ctx = _make_stock([_sku()])
        result = rule_low_confidence(plan, ctx, CFG)
        assert result.triggered is True
        assert result.decision == Decision.ESCALATE

    def test_passes_at_threshold(self):
        plan = _make_plan(confidence_score=0.70)
        ctx = _make_stock([_sku()])
        result = rule_low_confidence(plan, ctx, CFG)
        assert result.triggered is False

    def test_passes_above_threshold(self):
        plan = _make_plan(confidence_score=0.95)
        ctx = _make_stock([_sku()])
        result = rule_low_confidence(plan, ctx, CFG)
        assert result.triggered is False


# ---------------------------------------------------------------------------
# Rule: stock_adequacy
# ---------------------------------------------------------------------------

class TestRuleStockAdequacy:
    def test_rejects_when_all_adequate(self):
        # stock=200 > threshold=40 — adequate
        plan = _make_plan()
        ctx = _make_stock([_sku(stock=200, threshold=40)])
        result = rule_stock_adequacy(plan, ctx, CFG)
        assert result.triggered is True
        assert result.decision == Decision.REJECT

    def test_passes_when_all_need_restock(self):
        # stock=10 < threshold=50 — needs restock
        plan = _make_plan()
        ctx = _make_stock([_sku(stock=10, threshold=50)])
        result = rule_stock_adequacy(plan, ctx, CFG)
        assert result.triggered is False

    def test_flags_but_does_not_block_partial_adequacy(self):
        # One needs restock, one adequate — should flag but not block
        plan = _make_plan()
        ctx = _make_stock([
            _sku(sku_id="SKU-001", stock=10, threshold=50),   # needs restock
            _sku(sku_id="SKU-002", stock=200, threshold=40),  # adequate
        ])
        result = rule_stock_adequacy(plan, ctx, CFG)
        assert result.triggered is True
        assert result.decision is None   # Flags but doesn't block


# ---------------------------------------------------------------------------
# Rule: cost_threshold
# ---------------------------------------------------------------------------

class TestRuleCostThreshold:
    def test_auto_approves_below_limit(self):
        plan = _make_plan(total_order_value=30000.0)
        ctx = _make_stock([_sku()])
        result = rule_cost_threshold(plan, ctx, CFG)
        assert result.triggered is True
        assert result.decision == Decision.AUTO_APPROVE

    def test_escalates_at_limit(self):
        plan = _make_plan(total_order_value=50000.0)
        ctx = _make_stock([_sku()])
        result = rule_cost_threshold(plan, ctx, CFG)
        assert result.triggered is True
        assert result.decision == Decision.ESCALATE

    def test_escalates_above_limit(self):
        plan = _make_plan(total_order_value=247500.0)
        ctx = _make_stock([_sku()])
        result = rule_cost_threshold(plan, ctx, CFG)
        assert result.triggered is True
        assert result.decision == Decision.ESCALATE


# ---------------------------------------------------------------------------
# Rule: unit_price_anomaly
# ---------------------------------------------------------------------------

class TestRuleUnitPriceAnomaly:
    def test_escalates_on_price_anomaly(self):
        # Supplier charges ₹500 but our cost is ₹100 — 5× ratio
        plan = _make_plan()
        plan.line_items = [_LineItem(sku_id="SKU-TSH-001", unit_price=500.0)]
        ctx = _make_stock([_sku(sku_id="SKU-TSH-001", cost=100.0)])
        result = rule_unit_price_anomaly(plan, ctx, CFG)
        assert result.triggered is True
        assert result.decision == Decision.ESCALATE

    def test_passes_on_normal_price(self):
        # Supplier charges ₹180 but our cost is ₹160 — 1.125× — within 2× limit
        plan = _make_plan()
        plan.line_items = [_LineItem(sku_id="SKU-TSH-001", unit_price=180.0)]
        ctx = _make_stock([_sku(sku_id="SKU-TSH-001", cost=160.0)])
        result = rule_unit_price_anomaly(plan, ctx, CFG)
        assert result.triggered is False

    def test_passes_at_exactly_2x(self):
        plan = _make_plan()
        plan.line_items = [_LineItem(sku_id="SKU-TSH-001", unit_price=320.0)]
        ctx = _make_stock([_sku(sku_id="SKU-TSH-001", cost=160.0)])
        result = rule_unit_price_anomaly(plan, ctx, CFG)
        assert result.triggered is False   # exactly 2× is not anomalous


# ---------------------------------------------------------------------------
# PolicyLayer integration tests
# ---------------------------------------------------------------------------

class TestPolicyLayer:

    def _agent_retrieve(self, *sku_ids):
        """Helper: build a plan + retrieve stock context from MockDB."""
        @dataclass
        class _Item:
            sku_id: str
            product_name: str = "P"
            quantity: int = 100
            unit_price: float = 200.0
            total_cost: float = 20000.0

        @dataclass
        class _P:
            plan_id: str = "plan-001"
            line_items: list = field(default_factory=list)
            total_order_value: float = 20000.0
            confidence_score: float = 0.95

        plan = _P()
        plan.line_items = [_Item(sku_id=s) for s in sku_ids]
        from retriever_agent.retriever import RetrieverAgent
        ctx = RetrieverAgent(backend="mock").retrieve(plan)
        return plan, ctx

    def test_auto_approve_small_low_stock_order(self):
        """Small order for low-stock items → AUTO_APPROVE."""
        plan, ctx = self._agent_retrieve("SKU-TSH-001")  # LOW_STOCK, cheap
        plan.total_order_value = 20000.0   # under ₹50K
        policy = PolicyLayer(PolicyConfig(auto_approve_limit=50000.0))
        decision = policy.evaluate(plan, ctx)
        assert decision.decision == Decision.AUTO_APPROVE
        assert decision.is_approved

    def test_escalate_large_order(self):
        """Large order value → ESCALATE."""
        plan, ctx = self._agent_retrieve("SKU-TSH-001")
        plan.total_order_value = 247500.0   # over ₹50K
        policy = PolicyLayer(PolicyConfig(auto_approve_limit=50000.0))
        decision = policy.evaluate(plan, ctx)
        assert decision.decision == Decision.ESCALATE
        assert decision.needs_human
        assert decision.requires_approval_from == "Operations Manager"

    def test_reject_missing_sku(self):
        """Unknown SKU → REJECT immediately."""
        plan, ctx = self._agent_retrieve("SKU-FAKE-999")
        policy = PolicyLayer()
        decision = policy.evaluate(plan, ctx)
        assert decision.decision == Decision.REJECT
        assert decision.is_rejected

    def test_escalate_low_confidence(self):
        """Low confidence plan → ESCALATE."""
        plan, ctx = self._agent_retrieve("SKU-TSH-001")
        plan.confidence_score = 0.45
        plan.total_order_value = 10000.0  # Would normally auto-approve
        policy = PolicyLayer()
        decision = policy.evaluate(plan, ctx)
        assert decision.decision == Decision.ESCALATE

    def test_reject_adequate_stock(self):
        """All items have adequate stock → REJECT (no restock needed)."""
        plan = _make_plan(total_order_value=10000.0)
        # SKU-CAP-003 has stock=200, threshold=40 — clearly adequate
        plan.line_items = [_LineItem(sku_id="SKU-CAP-003")]
        from retriever_agent.retriever import RetrieverAgent
        ctx = RetrieverAgent(backend="mock").retrieve(plan)
        policy = PolicyLayer()
        decision = policy.evaluate(plan, ctx)
        assert decision.decision == Decision.REJECT

    def test_decision_has_audit_trail(self):
        """Every decision must include a full rule audit trail."""
        plan, ctx = self._agent_retrieve("SKU-TSH-001")
        plan.total_order_value = 20000.0
        policy = PolicyLayer()
        decision = policy.evaluate(plan, ctx)
        assert len(decision.rule_results) > 0
        assert all(isinstance(r, RuleResult) for r in decision.rule_results)

    def test_summary_is_string(self):
        plan, ctx = self._agent_retrieve("SKU-TSH-001")
        plan.total_order_value = 20000.0
        policy = PolicyLayer()
        decision = policy.evaluate(plan, ctx)
        assert isinstance(decision.summary(), str)
        assert plan.plan_id in decision.summary()

    def test_configurable_threshold(self):
        """Custom threshold: ₹10K limit should escalate a ₹20K order."""
        plan, ctx = self._agent_retrieve("SKU-TSH-001")
        plan.total_order_value = 20000.0
        policy = PolicyLayer(PolicyConfig(auto_approve_limit=10000.0))
        decision = policy.evaluate(plan, ctx)
        assert decision.decision == Decision.ESCALATE