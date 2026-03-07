"""
BusinessFlow AI — Full 4-Stage Pipeline Demo
=============================================
Planner  →  Retriever  →  Policy Layer  →  Executor Agent

Usage:
    py -3.12 demo_full.py
"""

import os
from dotenv import load_dotenv
load_dotenv()

USE_MOCK_PLAN = os.getenv("AZURE_OPENAI_API_KEY") is None


def get_plan():
    if USE_MOCK_PLAN:
        from dataclasses import dataclass, field

        @dataclass
        class _Item:
            sku_id: str
            product_name: str
            quantity: int
            unit_price: float
            total_cost: float

        @dataclass
        class _Plan:
            plan_id: str = "demo-plan-001"
            supplier_name: str = "Sunrise Textiles Pvt. Ltd."
            supplier_email: str = "ramesh@sunrise-textiles.in"
            email_subject: str = "Restocking Confirmation – June 2025"
            line_items: list = field(default_factory=list)
            total_order_value: float = 40000.0
            confidence_score: float = 0.97
            delivery_date: str = "2025-07-15"

        plan = _Plan()
        plan.line_items = [
            _Item("SKU-BAG-011", "Canvas Tote Bag",  50,  230.0, 11500.0),
            _Item("SKU-JNS-042", "Denim Jeans",      30,  650.0, 19500.0),
            _Item("SKU-SNK-007", "Sports Sneakers",   8, 1200.0,  9600.0),
        ]
        return plan
    else:
        from planner_agent.planner import PlannerAgent
        EMAIL = """Hi, please supply:
        SKU-BAG-011 Canvas Tote Bag x50 @ Rs.230
        SKU-JNS-042 Denim Jeans x30 @ Rs.650
        SKU-SNK-007 Sports Sneakers x8 @ Rs.1200
        Delivery: 2025-07-15. ramesh@sunrise-textiles.in"""
        return PlannerAgent().parse_email(email_body=EMAIL, subject="Restocking Confirmation")


def divider(title=""):
    if title:
        pad = (58 - len(title) - 2) // 2
        print(f"\n{'='*pad} {title} {'='*pad}")
    else:
        print("=" * 62)


def main():
    divider()
    print("  BusinessFlow AI — Complete Pipeline Demo")
    print("  Planner → Retriever → Policy Layer → Executor Agent")
    divider()

    # ── STAGE 1: Planner ─────────────────────────────────────────
    print("\n[STAGE 1] Planner Agent — Parsing supplier email")
    print("-" * 50)
    if USE_MOCK_PLAN:
        print("  (No Azure key — using mock plan)")
    plan = get_plan()
    print(f"  Plan ID     : {plan.plan_id}")
    print(f"  Supplier    : {plan.supplier_name}")
    print(f"  Email       : {plan.supplier_email}")
    print(f"  Items       : {len(plan.line_items)}")
    print(f"  Order Value : Rs.{plan.total_order_value:,.2f}")
    print(f"  Confidence  : {plan.confidence_score * 100:.0f}%")

    # ── STAGE 2: Retriever ───────────────────────────────────────
    print("\n[STAGE 2] Retriever Agent — Fetching inventory")
    print("-" * 50)
    from retriever_agent.retriever import RetrieverAgent
    context = RetrieverAgent(backend="mock").retrieve(plan)
    icons = {"OUT_OF_STOCK": "🔴", "LOW_STOCK": "🟡", "ADEQUATE": "🟢"}
    for s in context.sku_contexts:
        icon = icons.get(s.stock_status, "?")
        print(f"  {icon} [{s.sku_id}] {s.product_name}")
        print(f"      Stock: {s.current_stock} | Threshold: {s.reorder_threshold} | {s.stock_status}")

    # ── STAGE 3: Policy Layer ────────────────────────────────────
    print("\n[STAGE 3] Policy Layer — Evaluating governance rules")
    print("-" * 50)
    from policy_layer.policy import PolicyLayer, PolicyConfig, Decision
    policy = PolicyLayer(PolicyConfig(auto_approve_limit=50000.0))
    decision = policy.evaluate(plan, context)

    verdict_icons = {
        Decision.AUTO_APPROVE: "✅",
        Decision.ESCALATE:     "⚠️ ",
        Decision.REJECT:       "❌",
    }
    print(f"  {verdict_icons[decision.decision]} VERDICT: {decision.decision.value}")
    for r in decision.reasons:
        print(f"  Reason : {r}")
    print("\n  Rule Audit Trail:")
    for r in decision.rule_results:
        status = "FIRED  " if r.triggered else "passed "
        print(f"    [{status}] {r.rule_name:<25} {r.reason[:52]}")

    # ── STAGE 4: Executor Agent ──────────────────────────────────
    print("\n[STAGE 4] Executor Agent — Executing approved actions")
    print("-" * 50)

    if decision.decision != Decision.AUTO_APPROVE:
        print(f"  ⚠️  Order not auto-approved ({decision.decision.value}).")
        print(f"  Escalated to: {decision.requires_approval_from}")
        print("  Skipping execution — would await dashboard approval.")
    else:
        from executor_agent.executor import ExecutorAgent, MockNotifier
        notifier = MockNotifier()
        agent = ExecutorAgent(backend="mock", notifier=notifier)
        result = agent.execute(plan, context, decision)

        status_icon = "✅" if result.success else "❌"
        print(f"  {status_icon} Execution: {'SUCCESS' if result.success else 'FAILED'}")

        if result.success:
            print(f"\n  📦 Purchase Orders Created ({result.orders_created}):")
            for po in result.purchase_orders:
                print(f"    [{po.po_id}] {po.sku_id} | qty={po.quantity_ordered} "
                      f"| Rs.{po.total_cost:,.2f} | {po.status}")

            print(f"\n  📊 Inventory Updates:")
            for u in result.inventory_updates:
                print(f"    {u['sku_id']}: {u['old_stock']} → {u['new_stock']} (+{u['added']})")

            if result.skipped_items:
                print(f"\n  ⏭️  Skipped Items:")
                for s in result.skipped_items:
                    print(f"    - {s}")

            print(f"\n  📧 Notification: {'Sent' if result.notification_sent else 'Failed'}")
            if notifier.sent:
                print(f"    To      : {notifier.sent[0]['to']}")
                print(f"    Subject : {notifier.sent[0]['subject']}")

            print(f"\n  📋 Audit Log ({len(result.audit_entries)} entries):")
            for entry in result.audit_entries:
                print(f"    [{entry.created_at[11:19]}] {entry.action:<22} {entry.details[:48]}")

            print(f"\n  💰 Total Executed Value: Rs.{result.total_executed_value:,.2f}")

    # ── Pipeline summary ─────────────────────────────────────────
    divider("PIPELINE COMPLETE")
    print(f"  Plan       : {plan.plan_id}")
    print(f"  Supplier   : {plan.supplier_name}")
    print(f"  Order Value: Rs.{plan.total_order_value:,.2f}")
    print(f"  Decision   : {decision.decision.value}")
    if decision.decision == Decision.AUTO_APPROVE:
        print(f"  Executed   : {result.orders_created} POs | Rs.{result.total_executed_value:,.2f}")
        print(f"  Time saved : ~25 minutes of manual ops work")
    divider()
    print()


if __name__ == "__main__":
    main()