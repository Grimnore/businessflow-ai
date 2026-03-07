"""
BusinessFlow AI — Policy Layer
================================
The governance engine that sits between the Retriever Agent and the
Executor Agent. It evaluates every ExecutionPlan + StockContext pair
against a set of configurable rules and returns a PolicyDecision.

Decision outcomes:
  AUTO_APPROVE  → Executor Agent proceeds immediately
  ESCALATE      → Held for human approval in the Dashboard
  REJECT        → Blocked entirely (with reason)

Rules evaluated (in order):
  1. Missing SKU rule      — reject if any SKU not found in DB
  2. Low confidence rule   — escalate if planner confidence < threshold
  3. Stock adequacy rule   — reject if stock is already adequate (no restock needed)
  4. Cost threshold rule   — escalate if total order cost >= auto-approve limit
  5. Unit price rule       — escalate if any single SKU unit price seems anomalous

All thresholds are configurable via env vars or constructor args.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & Constants
# ---------------------------------------------------------------------------

class Decision(str, Enum):
    AUTO_APPROVE = "AUTO_APPROVE"   # Executor proceeds immediately
    ESCALATE     = "ESCALATE"       # Held for human approval
    REJECT       = "REJECT"         # Blocked entirely


DEFAULT_AUTO_APPROVE_LIMIT   = 50_000.0   # INR — orders below this auto-execute
DEFAULT_MIN_CONFIDENCE       = 0.70       # plans below this are escalated
DEFAULT_MAX_UNIT_PRICE_RATIO = 2.0        # flag if supplier price > 2x our internal cost


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class RuleResult:
    """Result of evaluating a single policy rule."""
    rule_name:   str
    triggered:   bool                    # True if the rule fired
    decision:    Optional[Decision]      # Decision if triggered, else None
    reason:      str                     # Human-readable explanation
    severity:    str = "INFO"            # INFO | WARNING | CRITICAL


@dataclass
class PolicyDecision:
    """
    Final output of the Policy Layer.
    Passed to the Executor Agent or the Approval Dashboard.
    """
    plan_id:        str
    decision:       Decision
    reasons:        list[str]            # All triggered rule reasons
    rule_results:   list[RuleResult]     # Full audit of every rule evaluated
    evaluated_at:   str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_order_value: float = 0.0
    requires_approval_from: Optional[str] = None   # e.g. "Operations Manager"
    auto_approved_items:    list[str] = field(default_factory=list)
    escalated_items:        list[str] = field(default_factory=list)
    rejected_items:         list[str] = field(default_factory=list)

    @property
    def is_approved(self) -> bool:
        return self.decision == Decision.AUTO_APPROVE

    @property
    def needs_human(self) -> bool:
        return self.decision == Decision.ESCALATE

    @property
    def is_rejected(self) -> bool:
        return self.decision == Decision.REJECT

    def summary(self) -> str:
        icon = {"AUTO_APPROVE": "✅", "ESCALATE": "⚠️", "REJECT": "❌"}[self.decision.value]
        lines = [
            f"{icon} PolicyDecision for plan {self.plan_id}",
            f"   Decision : {self.decision.value}",
            f"   Value    : ₹{self.total_order_value:,.2f}",
        ]
        for r in self.reasons:
            lines.append(f"   Reason   : {r}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Individual Rule Functions
# ---------------------------------------------------------------------------

def rule_missing_skus(plan, stock_context, cfg: "PolicyConfig") -> RuleResult:
    """REJECT if any SKU from the email was not found in the database."""
    if not stock_context.all_found:
        missing = ", ".join(stock_context.missing_skus)
        return RuleResult(
            rule_name="missing_skus",
            triggered=True,
            decision=Decision.REJECT,
            reason=f"SKUs not found in inventory DB: {missing}. Cannot process unknown items.",
            severity="CRITICAL",
        )
    return RuleResult(rule_name="missing_skus", triggered=False, decision=None,
                      reason="All SKUs found in inventory DB", severity="INFO")


def rule_low_confidence(plan, stock_context, cfg: "PolicyConfig") -> RuleResult:
    """ESCALATE if the Planner Agent's confidence score is below threshold."""
    if plan.confidence_score < cfg.min_confidence:
        return RuleResult(
            rule_name="low_confidence",
            triggered=True,
            decision=Decision.ESCALATE,
            reason=(
                f"Planner confidence {plan.confidence_score:.0%} is below "
                f"minimum threshold {cfg.min_confidence:.0%}. "
                "Email may be ambiguous — human review required."
            ),
            severity="WARNING",
        )
    return RuleResult(rule_name="low_confidence", triggered=False, decision=None,
                      reason=f"Planner confidence {plan.confidence_score:.0%} is acceptable",
                      severity="INFO")


def rule_stock_adequacy(plan, stock_context, cfg: "PolicyConfig") -> RuleResult:
    """
    REJECT individual SKUs where current stock is already above threshold.
    If ALL SKUs have adequate stock, reject the whole plan.
    If SOME have adequate stock, note them but don't block.
    """
    adequate_skus = [
        s.sku_id for s in stock_context.sku_contexts
        if s.found and not s.needs_restock
    ]
    if len(adequate_skus) == len([s for s in stock_context.sku_contexts if s.found]):
        return RuleResult(
            rule_name="stock_adequacy",
            triggered=True,
            decision=Decision.REJECT,
            reason=(
                f"All SKUs have adequate stock: {', '.join(adequate_skus)}. "
                "No restocking needed at this time."
            ),
            severity="WARNING",
        )
    if adequate_skus:
        return RuleResult(
            rule_name="stock_adequacy",
            triggered=True,
            decision=None,   # Doesn't block — just flags
            reason=f"Some SKUs have adequate stock (will be noted): {', '.join(adequate_skus)}",
            severity="INFO",
        )
    return RuleResult(rule_name="stock_adequacy", triggered=False, decision=None,
                      reason="All SKUs require restocking", severity="INFO")


def rule_cost_threshold(plan, stock_context, cfg: "PolicyConfig") -> RuleResult:
    """
    AUTO_APPROVE if total order cost < threshold.
    ESCALATE if total order cost >= threshold.
    """
    total = plan.total_order_value
    if total >= cfg.auto_approve_limit:
        return RuleResult(
            rule_name="cost_threshold",
            triggered=True,
            decision=Decision.ESCALATE,
            reason=(
                f"Total order value ₹{total:,.2f} meets or exceeds "
                f"auto-approve limit ₹{cfg.auto_approve_limit:,.2f}. "
                "Requires management approval."
            ),
            severity="WARNING",
        )
    return RuleResult(
        rule_name="cost_threshold",
        triggered=True,
        decision=Decision.AUTO_APPROVE,
        reason=(
            f"Total order value ₹{total:,.2f} is within "
            f"auto-approve limit ₹{cfg.auto_approve_limit:,.2f}."
        ),
        severity="INFO",
    )


def rule_unit_price_anomaly(plan, stock_context, cfg: "PolicyConfig") -> RuleResult:
    """
    ESCALATE if any supplier unit price is more than N× our internal cost.
    Protects against price gouging or data entry errors.
    """
    anomalies = []
    for item in plan.line_items:
        sku_ctx = stock_context.get_sku(item.sku_id)
        if not sku_ctx or not sku_ctx.found:
            continue
        if item.unit_price and sku_ctx.unit_cost > 0:
            ratio = item.unit_price / sku_ctx.unit_cost
            if ratio > cfg.max_unit_price_ratio:
                anomalies.append(
                    f"{item.sku_id}: supplier ₹{item.unit_price:.2f} vs "
                    f"internal ₹{sku_ctx.unit_cost:.2f} ({ratio:.1f}×)"
                )

    if anomalies:
        return RuleResult(
            rule_name="unit_price_anomaly",
            triggered=True,
            decision=Decision.ESCALATE,
            reason=(
                f"Unit price anomaly detected — supplier price exceeds "
                f"{cfg.max_unit_price_ratio}× internal cost: {'; '.join(anomalies)}"
            ),
            severity="WARNING",
        )
    return RuleResult(rule_name="unit_price_anomaly", triggered=False, decision=None,
                      reason="All unit prices within acceptable range", severity="INFO")


# ---------------------------------------------------------------------------
# Policy Configuration
# ---------------------------------------------------------------------------

@dataclass
class PolicyConfig:
    """
    Configurable thresholds for the Policy Layer.
    Defaults can be overridden via env vars or constructor args.
    """
    auto_approve_limit:   float = field(default_factory=lambda: float(os.getenv("POLICY_AUTO_APPROVE_THRESHOLD", DEFAULT_AUTO_APPROVE_LIMIT)))
    min_confidence:       float = field(default_factory=lambda: float(os.getenv("POLICY_MIN_CONFIDENCE", DEFAULT_MIN_CONFIDENCE)))
    max_unit_price_ratio: float = field(default_factory=lambda: float(os.getenv("POLICY_MAX_UNIT_PRICE_RATIO", DEFAULT_MAX_UNIT_PRICE_RATIO)))
    approver_role:        str   = "Operations Manager"

    def summary(self) -> str:
        return (
            f"PolicyConfig: auto_approve_limit=₹{self.auto_approve_limit:,.0f} "
            f"min_confidence={self.min_confidence:.0%} "
            f"max_unit_price_ratio={self.max_unit_price_ratio}×"
        )


# ---------------------------------------------------------------------------
# Policy Layer
# ---------------------------------------------------------------------------

# Ordered list of rules — evaluated top to bottom
# A REJECT or ESCALATE from any rule short-circuits further evaluation
# (except stock_adequacy which can fire without blocking)
RULES = [
    rule_missing_skus,
    rule_low_confidence,
    rule_stock_adequacy,
    rule_cost_threshold,
    rule_unit_price_anomaly,
]


class PolicyLayer:
    """
    Evaluates an ExecutionPlan + StockContext against governance rules
    and returns a PolicyDecision.

    Usage:
        policy = PolicyLayer()
        decision = policy.evaluate(plan, stock_context)
        print(decision.summary())
    """

    def __init__(self, config: PolicyConfig | None = None):
        self.config = config or PolicyConfig()
        logger.info("PolicyLayer initialised | %s", self.config.summary())

    def evaluate(self, plan, stock_context) -> PolicyDecision:
        """
        Run all rules against the plan and stock context.

        Args:
            plan:          ExecutionPlan from the Planner Agent
            stock_context: StockContext from the Retriever Agent

        Returns:
            PolicyDecision with final verdict and full audit trail
        """
        logger.info("Evaluating plan | plan_id=%s | value=₹%.2f", plan.plan_id, plan.total_order_value)

        rule_results: list[RuleResult] = []
        final_decision: Optional[Decision] = None
        reasons: list[str] = []

        for rule_fn in RULES:
            result = rule_fn(plan, stock_context, self.config)
            rule_results.append(result)

            logger.debug("Rule %-25s triggered=%-5s decision=%s",
                        result.rule_name, result.triggered, result.decision)

            if result.triggered and result.decision in (Decision.REJECT, Decision.ESCALATE):
                # Hard stop — first binding decision wins
                if result.decision == Decision.REJECT:
                    final_decision = Decision.REJECT
                    reasons.append(result.reason)
                    break   # REJECTs are final — no need to evaluate further
                elif result.decision == Decision.ESCALATE:
                    if final_decision != Decision.REJECT:
                        final_decision = Decision.ESCALATE
                        reasons.append(result.reason)
                    # Continue evaluating — might find more reasons to escalate

            elif result.triggered and result.decision == Decision.AUTO_APPROVE:
                if final_decision is None:
                    final_decision = Decision.AUTO_APPROVE
                    reasons.append(result.reason)

        # Default to ESCALATE if no rule produced a clear decision
        if final_decision is None:
            final_decision = Decision.ESCALATE
            reasons.append("No rule produced a clear auto-approval — defaulting to escalation for safety.")

        # Build item-level lists for the dashboard
        auto_items, escalated_items, rejected_items = self._categorize_items(
            plan, stock_context, final_decision
        )

        decision = PolicyDecision(
            plan_id=plan.plan_id,
            decision=final_decision,
            reasons=reasons,
            rule_results=rule_results,
            total_order_value=plan.total_order_value,
            requires_approval_from=self.config.approver_role if final_decision == Decision.ESCALATE else None,
            auto_approved_items=auto_items,
            escalated_items=escalated_items,
            rejected_items=rejected_items,
        )

        logger.info(
            "PolicyDecision | plan_id=%s | decision=%s | value=₹%.2f",
            plan.plan_id, final_decision.value, plan.total_order_value
        )
        return decision

    def _categorize_items(self, plan, stock_context, decision: Decision):
        """Assign each line item to the appropriate category for dashboard display."""
        auto_items, escalated_items, rejected_items = [], [], []

        for item in plan.line_items:
            sku_ctx = stock_context.get_sku(item.sku_id)
            label = f"{item.sku_id} ({item.product_name}, qty={item.quantity})"

            if not sku_ctx or not sku_ctx.found:
                rejected_items.append(label + " — NOT FOUND IN DB")
            elif not sku_ctx.needs_restock:
                rejected_items.append(label + " — STOCK ADEQUATE")
            elif decision == Decision.AUTO_APPROVE:
                auto_items.append(label)
            elif decision == Decision.ESCALATE:
                escalated_items.append(label)
            else:
                rejected_items.append(label)

        return auto_items, escalated_items, rejected_items