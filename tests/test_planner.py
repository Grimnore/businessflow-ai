"""
Tests for BusinessFlow AI — Planner Agent
==========================================
Run with:  pytest tests/ -v

Uses unittest.mock to avoid real Azure OpenAI calls — runs fully offline.

"""

from __future__ import annotations

import json
import uuid
from unittest.mock import MagicMock, patch

import pytest

from planner_agent.planner import ExecutionPlan, LineItem, PlannerAgent


# ---------------------------------------------------------------------------
# Fixtures & Helpers
# ---------------------------------------------------------------------------

SAMPLE_EMAIL = """
Hi Team,

We can supply the following items immediately:

1. Cotton T-Shirt (White, L)   | SKU: SKU-TSH-001 | Qty: 300 units | Rate: ₹180/unit
2. Denim Jeans (32W)           | SKU: SKU-JNS-042 | Qty: 150 units | Rate: ₹650/unit
3. Sports Sneakers (Size 9)    | SKU: SKU-SNK-007 | Qty: 80 units  | Rate: ₹1,200/unit

Expected delivery: 2025-07-15. Payment terms: Net 30.

Best regards,
Ramesh Kumar | ramesh@sunrise-textiles.in
"""

SAMPLE_SUBJECT = "Restocking Confirmation – June 2025"


def _mock_openai_response(extracted_data: dict):
    tool_call = MagicMock()
    tool_call.function.arguments = json.dumps(extracted_data)
    message = MagicMock()
    message.tool_calls = [tool_call]
    message.content = None
    choice = MagicMock()
    choice.message = message
    choice.finish_reason = "tool_calls"
    response = MagicMock()
    response.choices = [choice]
    return response


EXTRACTED_FIXTURE = {
    "supplier_name":  "Sunrise Textiles Pvt. Ltd.",
    "supplier_email": "ramesh@sunrise-textiles.in",
    "email_subject":  SAMPLE_SUBJECT,
    "delivery_date":  "2025-07-15",
    "special_instructions": "Payment terms: Net 30",
    "confidence_score": 0.97,
    "line_items": [
        {"sku_id": "SKU-TSH-001", "product_name": "Cotton T-Shirt",   "quantity": 300, "unit_price": 180.0,  "total_cost": 54000.0},
        {"sku_id": "SKU-JNS-042", "product_name": "Denim Jeans",      "quantity": 150, "unit_price": 650.0,  "total_cost": 97500.0},
        {"sku_id": "SKU-SNK-007", "product_name": "Sports Sneakers",  "quantity": 80,  "unit_price": 1200.0, "total_cost": 96000.0},
    ],
}


# ---------------------------------------------------------------------------
# Unit Tests — LineItem
# ---------------------------------------------------------------------------

class TestLineItem:
    def test_total_cost_computed_when_missing(self):
        item = LineItem(sku_id="SKU-001", product_name="Widget", quantity=10, unit_price=100.0)
        assert item.total_cost == 1000.0

    def test_total_cost_preserved_when_given(self):
        item = LineItem(sku_id="SKU-001", product_name="Widget", quantity=10, unit_price=100.0, total_cost=999.0)
        assert item.total_cost == 999.0

    def test_quantity_must_be_positive(self):
        with pytest.raises(Exception):
            LineItem(sku_id="SKU-001", product_name="Widget", quantity=0)

    def test_optional_price_fields(self):
        item = LineItem(sku_id="SKU-001", product_name="Widget", quantity=5)
        assert item.unit_price is None
        assert item.total_cost is None


# ---------------------------------------------------------------------------
# Unit Tests — ExecutionPlan
# ---------------------------------------------------------------------------

class TestExecutionPlan:
    def test_total_order_value_computed(self):
        items = [
            LineItem(sku_id="SKU-001", product_name="A", quantity=10, unit_price=100.0),
            LineItem(sku_id="SKU-002", product_name="B", quantity=5,  unit_price=200.0),
        ]
        plan = ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            supplier_name="Test Supplier",
            supplier_email="test@supplier.com",
            email_subject="Test",
            line_items=items,
            confidence_score=0.9,
            raw_email_snippet="test",
        )
        assert plan.total_order_value == 2000.0

    def test_confidence_score_bounds(self):
        with pytest.raises(Exception):
            ExecutionPlan(
                plan_id="x", supplier_name="S", supplier_email="s@s.com",
                email_subject="S",
                line_items=[LineItem(sku_id="X", product_name="X", quantity=1)],
                confidence_score=1.5,   # invalid — > 1.0
                raw_email_snippet="x",
            )

    def test_plan_serializes_to_json(self):
        items = [LineItem(sku_id="SKU-001", product_name="Widget", quantity=5, unit_price=200.0)]
        plan = ExecutionPlan(
            plan_id="abc-123",
            supplier_name="Test Co",
            supplier_email="test@test.com",
            email_subject="Test Subject",
            line_items=items,
            confidence_score=0.95,
            raw_email_snippet="snippet",
        )
        serialised = plan.model_dump_json()
        import json as _json
        data = _json.loads(serialised)
        assert data["plan_id"] == "abc-123"
        assert data["total_order_value"] == 1000.0


# ---------------------------------------------------------------------------
# Unit Tests — PlannerAgent
# ---------------------------------------------------------------------------

class TestPlannerAgent:

    @patch("planner_agent.planner.AzureOpenAI")
    def test_parse_email_happy_path(self, mock_azure_cls):
        mock_client = MagicMock()
        mock_azure_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response(EXTRACTED_FIXTURE)

        agent = PlannerAgent(azure_endpoint="https://test.openai.azure.com", api_key="fake", deployment_name="gpt-4o")
        plan = agent.parse_email(email_body=SAMPLE_EMAIL, subject=SAMPLE_SUBJECT)

        assert isinstance(plan, ExecutionPlan)
        assert plan.supplier_name == "Sunrise Textiles Pvt. Ltd."
        assert len(plan.line_items) == 3
        assert plan.total_order_value == pytest.approx(247500.0)
        assert plan.confidence_score == 0.97
        assert plan.delivery_date == "2025-07-15"

    @patch("planner_agent.planner.AzureOpenAI")
    def test_custom_plan_id_is_preserved(self, mock_azure_cls):
        mock_client = MagicMock()
        mock_azure_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response(EXTRACTED_FIXTURE)

        agent = PlannerAgent(azure_endpoint="https://x.openai.azure.com", api_key="k", deployment_name="d")
        plan = agent.parse_email(SAMPLE_EMAIL, plan_id="my-plan-123")
        assert plan.plan_id == "my-plan-123"

    @patch("planner_agent.planner.AzureOpenAI")
    def test_raw_snippet_capped_at_500_chars(self, mock_azure_cls):
        mock_client = MagicMock()
        mock_azure_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response(EXTRACTED_FIXTURE)

        agent = PlannerAgent(azure_endpoint="https://x.openai.azure.com", api_key="k", deployment_name="d")
        plan = agent.parse_email("x" * 1000)
        assert len(plan.raw_email_snippet) == 500

    @patch("planner_agent.planner.AzureOpenAI")
    def test_raises_when_no_tool_call(self, mock_azure_cls):
        mock_client = MagicMock()
        mock_azure_cls.return_value = mock_client
        message = MagicMock()
        message.tool_calls = None
        message.content = "I cannot process this."
        choice = MagicMock()
        choice.message = message
        choice.finish_reason = "stop"
        response = MagicMock()
        response.choices = [choice]
        mock_client.chat.completions.create.return_value = response

        agent = PlannerAgent(azure_endpoint="https://x.openai.azure.com", api_key="k", deployment_name="d")
        with pytest.raises(ValueError, match="tool call"):
            agent.parse_email("Some email body")

    @patch("planner_agent.planner.AzureOpenAI")
    def test_low_confidence_email_still_parses(self, mock_azure_cls):
        """Low-confidence emails parse successfully — Policy Layer handles rejection."""
        mock_client = MagicMock()
        mock_azure_cls.return_value = mock_client
        fixture = {**EXTRACTED_FIXTURE, "confidence_score": 0.45}
        mock_client.chat.completions.create.return_value = _mock_openai_response(fixture)

        agent = PlannerAgent(azure_endpoint="https://x.openai.azure.com", api_key="k", deployment_name="d")
        plan = agent.parse_email("Vague email...")
        assert plan.confidence_score == 0.45