"""
Tests for BusinessFlow AI — Retriever Agent
============================================
Run with:  pytest tests/ -v

All tests use MockDB — no Azure SQL needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import MagicMock

import pytest

from retriever_agent.retriever import (
    AzureSQLDB,
    MockDB,
    RetrieverAgent,
    SKUContext,
    StockContext,
)


# ---------------------------------------------------------------------------
# Minimal ExecutionPlan stub (avoids importing full planner in tests)
# ---------------------------------------------------------------------------

@dataclass
class _LineItem:
    sku_id: str

@dataclass
class _Plan:
    plan_id: str
    line_items: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# SKUContext tests
# ---------------------------------------------------------------------------

class TestSKUContext:
    def _make(self, stock, threshold):
        return SKUContext(
            sku_id="SKU-001", product_name="Widget",
            current_stock=stock, reorder_threshold=threshold, unit_cost=100.0
        )

    def test_needs_restock_when_below_threshold(self):
        assert self._make(10, 20).needs_restock is True

    def test_needs_restock_when_at_threshold(self):
        assert self._make(20, 20).needs_restock is True

    def test_no_restock_when_above_threshold(self):
        assert self._make(50, 20).needs_restock is False

    def test_status_out_of_stock(self):
        assert self._make(0, 20).stock_status == "OUT_OF_STOCK"

    def test_status_low_stock(self):
        assert self._make(10, 20).stock_status == "LOW_STOCK"

    def test_status_adequate(self):
        assert self._make(100, 20).stock_status == "ADEQUATE"


# ---------------------------------------------------------------------------
# StockContext tests
# ---------------------------------------------------------------------------

class TestStockContext:
    def _make_context(self, skus: list[SKUContext], missing=None):
        return StockContext(plan_id="plan-001", sku_contexts=skus, missing_skus=missing or [])

    def test_all_found_when_no_missing(self):
        ctx = self._make_context([SKUContext("X", "P", 10, 5, 100.0)])
        assert ctx.all_found is True

    def test_not_all_found_when_missing(self):
        ctx = self._make_context([], missing=["SKU-999"])
        assert ctx.all_found is False

    def test_get_sku_returns_correct_item(self):
        s = SKUContext("SKU-001", "Widget", 10, 5, 100.0)
        ctx = self._make_context([s])
        assert ctx.get_sku("SKU-001") is s

    def test_get_sku_returns_none_for_unknown(self):
        ctx = self._make_context([])
        assert ctx.get_sku("SKU-999") is None

    def test_total_stock_value(self):
        skus = [
            SKUContext("A", "P1", current_stock=10, reorder_threshold=5, unit_cost=100.0),
            SKUContext("B", "P2", current_stock=5,  reorder_threshold=2, unit_cost=200.0),
        ]
        ctx = self._make_context(skus)
        assert ctx.total_current_stock_value == pytest.approx(2000.0)


# ---------------------------------------------------------------------------
# MockDB tests
# ---------------------------------------------------------------------------

class TestMockDB:
    def test_known_sku_returns_context(self):
        db = MockDB()
        ctx = db.get_sku_context("SKU-TSH-001")
        assert ctx is not None
        assert ctx.sku_id == "SKU-TSH-001"
        assert ctx.current_stock == 45

    def test_unknown_sku_returns_none(self):
        db = MockDB()
        assert db.get_sku_context("SKU-DOES-NOT-EXIST") is None

    def test_get_multiple_skus(self):
        db = MockDB()
        result = db.get_multiple_skus(["SKU-TSH-001", "SKU-JNS-042"])
        assert len(result) == 2
        assert "SKU-TSH-001" in result
        assert "SKU-JNS-042" in result

    def test_get_multiple_skus_skips_unknown(self):
        db = MockDB()
        result = db.get_multiple_skus(["SKU-TSH-001", "SKU-FAKE-999"])
        assert len(result) == 1
        assert "SKU-FAKE-999" not in result

    def test_add_and_retrieve_custom_sku(self):
        db = MockDB()
        db.add_sku("SKU-TEST-999", {
            "product_name": "Test Product",
            "current_stock": 5,
            "reorder_threshold": 10,
            "unit_cost": 50.0,
            "supplier_lead_days": 3,
        })
        ctx = db.get_sku_context("SKU-TEST-999")
        assert ctx is not None
        assert ctx.product_name == "Test Product"

    def test_update_stock(self):
        db = MockDB()
        db.update_stock("SKU-TSH-001", 999)
        ctx = db.get_sku_context("SKU-TSH-001")
        assert ctx.current_stock == 999


# ---------------------------------------------------------------------------
# RetrieverAgent tests
# ---------------------------------------------------------------------------

class TestRetrieverAgent:
    def _plan(self, *sku_ids):
        return _Plan(
            plan_id="test-plan-001",
            line_items=[_LineItem(sku_id=s) for s in sku_ids]
        )

    def test_retrieve_all_known_skus(self):
        agent = RetrieverAgent(backend="mock")
        plan = self._plan("SKU-TSH-001", "SKU-JNS-042")
        ctx = agent.retrieve(plan)

        assert isinstance(ctx, StockContext)
        assert len(ctx.sku_contexts) == 2
        assert ctx.all_found is True
        assert ctx.plan_id == "test-plan-001"

    def test_retrieve_marks_unknown_sku_as_missing(self):
        agent = RetrieverAgent(backend="mock")
        plan = self._plan("SKU-TSH-001", "SKU-FAKE-999")
        ctx = agent.retrieve(plan)

        assert "SKU-FAKE-999" in ctx.missing_skus
        assert ctx.all_found is False

    def test_missing_sku_has_placeholder_in_contexts(self):
        agent = RetrieverAgent(backend="mock")
        plan = self._plan("SKU-FAKE-999")
        ctx = agent.retrieve(plan)

        placeholder = ctx.get_sku("SKU-FAKE-999")
        assert placeholder is not None
        assert placeholder.found is False
        assert placeholder.current_stock == 0

    def test_out_of_stock_sku_detected(self):
        agent = RetrieverAgent(backend="mock")
        plan = self._plan("SKU-SNK-007")  # stock=0 in mock data
        ctx = agent.retrieve(plan)

        sneaker = ctx.get_sku("SKU-SNK-007")
        assert sneaker.stock_status == "OUT_OF_STOCK"
        assert sneaker.needs_restock is True

    def test_low_stock_sku_detected(self):
        agent = RetrieverAgent(backend="mock")
        plan = self._plan("SKU-BAG-011")  # stock=45, threshold=50
        ctx = agent.retrieve(plan)

        bag = ctx.get_sku("SKU-BAG-011")
        assert bag.stock_status == "LOW_STOCK"
        assert bag.needs_restock is True

    def test_adequate_stock_sku_detected(self):
        agent = RetrieverAgent(backend="mock")
        plan = self._plan("SKU-CAP-003")  # stock=200, threshold=40
        ctx = agent.retrieve(plan)

        cap = ctx.get_sku("SKU-CAP-003")
        assert cap.stock_status == "ADEQUATE"
        assert cap.needs_restock is False

    def test_summary_output_is_string(self):
        agent = RetrieverAgent(backend="mock")
        plan = self._plan("SKU-TSH-001", "SKU-SNK-007")
        ctx = agent.retrieve(plan)
        summary = ctx.summary()
        assert isinstance(summary, str)
        assert "SKU-TSH-001" in summary
        assert "SKU-SNK-007" in summary

    def test_empty_plan_returns_empty_context(self):
        agent = RetrieverAgent(backend="mock")
        plan = self._plan()  # no line items
        ctx = agent.retrieve(plan)
        assert len(ctx.sku_contexts) == 0
        assert ctx.all_found is True