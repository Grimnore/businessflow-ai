"""
BusinessFlow AI — Planner Agent
================================
Parses incoming supplier emails using Azure OpenAI and produces a
structured ExecutionPlan that downstream agents (Retriever, Policy,
Executor) can act upon.

Flow:
    raw email text
        → PlannerAgent.parse_email()
            → Azure OpenAI (function-calling / structured output)
        → ExecutionPlan (Pydantic model)
        → published to shared queue / returned to orchestrator
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from openai import AzureOpenAI
from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Models  (Pydantic v2)
# ---------------------------------------------------------------------------

class LineItem(BaseModel):
    """A single SKU mentioned in the supplier email."""
    sku_id: str = Field(..., description="Stock Keeping Unit identifier")
    product_name: str = Field(..., description="Human-readable product name")
    quantity: int = Field(..., gt=0, description="Number of units offered/shipped")
    unit_price: Optional[float] = Field(None, description="Price per unit in INR, if stated")
    total_cost: Optional[float] = Field(None, description="Total cost in INR, if calculable")

    @model_validator(mode="after")
    def compute_total(self) -> "LineItem":
        if self.total_cost is None and self.unit_price is not None and self.quantity:
            self.total_cost = round(self.unit_price * self.quantity, 2)
        return self


class ExecutionPlan(BaseModel):
    """Structured output produced by the Planner Agent."""
    plan_id: str = Field(..., description="Unique plan identifier (UUID-like)")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    supplier_name: str = Field(..., description="Name of the supplier")
    supplier_email: str = Field(..., description="Supplier's email address")
    email_subject: str = Field(..., description="Subject line of the email")
    line_items: list[LineItem] = Field(..., min_length=1)
    delivery_date: Optional[str] = Field(None, description="Expected delivery date (ISO format if possible)")
    special_instructions: Optional[str] = Field(None, description="Any special notes from the supplier")
    total_order_value: float = Field(0.0, description="Sum of all line item costs")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Parser confidence 0-1")
    raw_email_snippet: str = Field(..., description="First 500 chars of original email for audit")

    @model_validator(mode="after")
    def compute_order_total(self) -> "ExecutionPlan":
        total = sum(i.total_cost for i in self.line_items if i.total_cost is not None)
        self.total_order_value = round(total, 2)
        return self


# ---------------------------------------------------------------------------
# Azure OpenAI tool / function schema
# ---------------------------------------------------------------------------

EXTRACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_execution_plan",
        "description": (
            "Extract all relevant procurement data from a supplier email and "
            "return it as a structured execution plan."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "supplier_name": {"type": "string"},
                "supplier_email": {"type": "string"},
                "email_subject": {"type": "string"},
                "line_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "sku_id":        {"type": "string"},
                            "product_name":  {"type": "string"},
                            "quantity":      {"type": "integer"},
                            "unit_price":    {"type": "number"},
                            "total_cost":    {"type": "number"},
                        },
                        "required": ["sku_id", "product_name", "quantity"],
                    },
                },
                "delivery_date":         {"type": "string"},
                "special_instructions":  {"type": "string"},
                "confidence_score": {
                    "type": "number",
                    "description": "Your confidence in the extraction, 0.0 to 1.0",
                },
            },
            "required": [
                "supplier_name", "supplier_email", "email_subject",
                "line_items", "confidence_score",
            ],
        },
    },
}

SYSTEM_PROMPT = """You are the Planner Agent of BusinessFlow AI, an intelligent
inventory automation system for Indian e-commerce SMEs.

Your job is to read a supplier email and extract all procurement-relevant data
with high accuracy. Always:
- Infer SKU IDs from context if not explicitly stated (e.g. SKU-PROD-001).
- Convert all prices to INR. If currency is ambiguous, assume INR.
- Parse dates into ISO 8601 format (YYYY-MM-DD) where possible.
- Set confidence_score < 0.7 if the email is ambiguous or missing key fields.
- Never hallucinate quantities or prices; use null if uncertain.
"""


# ---------------------------------------------------------------------------
# Planner Agent
# ---------------------------------------------------------------------------

class PlannerAgent:
    """
    Wraps Azure OpenAI to parse supplier emails into ExecutionPlan objects.

    Usage:
        agent = PlannerAgent()
        plan = agent.parse_email(raw_email, subject="Re: Stock Replenishment")
        print(plan.model_dump_json(indent=2))
    """

    def __init__(
        self,
        azure_endpoint: str | None = None,
        api_key: str | None = None,
        deployment_name: str | None = None,
        api_version: str = "2024-02-15-preview",
    ):
        self.deployment = deployment_name or os.environ["AZURE_OPENAI_DEPLOYMENT"]
        self.client = AzureOpenAI(
            azure_endpoint=azure_endpoint or os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=api_key or os.environ["AZURE_OPENAI_API_KEY"],
            api_version=api_version,
        )
        logger.info("PlannerAgent initialised | deployment=%s", self.deployment)

    def parse_email(
        self,
        email_body: str,
        subject: str = "",
        plan_id: str | None = None,
    ) -> ExecutionPlan:
        import uuid
        plan_id = plan_id or str(uuid.uuid4())
        user_message = self._build_user_message(email_body, subject)
        logger.info("Calling Azure OpenAI | plan_id=%s | email_len=%d", plan_id, len(email_body))

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            tools=[EXTRACTION_TOOL],
            tool_choice={"type": "function", "function": {"name": "extract_execution_plan"}},
            temperature=0,
            max_tokens=1500,
        )

        extracted = self._parse_tool_response(response)
        plan = self._build_plan(extracted, plan_id, email_body, subject)
        logger.info(
            "ExecutionPlan created | plan_id=%s | items=%d | total=₹%.2f | confidence=%.2f",
            plan.plan_id, len(plan.line_items), plan.total_order_value, plan.confidence_score,
        )
        return plan

    def _build_user_message(self, body: str, subject: str) -> str:
        return (
            f"Subject: {subject}\n\n"
            f"--- EMAIL BODY ---\n{body}\n--- END ---\n\n"
            "Please extract the procurement data using the extract_execution_plan function."
        )

    def _parse_tool_response(self, response) -> dict:
        choice = response.choices[0]
        tool_calls = getattr(choice.message, "tool_calls", None)
        if not tool_calls:
            raise ValueError(
                "Azure OpenAI did not return a tool call. "
                f"Finish reason: {choice.finish_reason}. "
                f"Content: {choice.message.content}"
            )
        return json.loads(tool_calls[0].function.arguments)

    def _build_plan(self, extracted: dict, plan_id: str, email_body: str, subject: str) -> ExecutionPlan:
        line_items = [LineItem(**item) for item in extracted.get("line_items", [])]
        return ExecutionPlan(
            plan_id=plan_id,
            supplier_name=extracted["supplier_name"],
            supplier_email=extracted["supplier_email"],
            email_subject=extracted.get("email_subject") or subject,
            line_items=line_items,
            delivery_date=extracted.get("delivery_date"),
            special_instructions=extracted.get("special_instructions"),
            confidence_score=extracted["confidence_score"],
            raw_email_snippet=email_body[:500],
        )
