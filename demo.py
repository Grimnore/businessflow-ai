"""
BusinessFlow AI — Pipeline Demo (Planner + Retriever)
======================================================
Shows the first two agents working together end-to-end.

Usage:
    py -3.12 demo.py
"""

import os
from dotenv import load_dotenv
load_dotenv()

USE_MOCK_PLAN = os.getenv("AZURE_OPENAI_API_KEY") is None

DEMO_EMAIL = """
Hi Team,
We can supply the following items:
1. Cotton T-Shirt (White, L)   | SKU: SKU-TSH-001 | Qty: 300 units | Rs.180/unit
2. Denim Jeans (32W)           | SKU: SKU-JNS-042 | Qty: 150 units | Rs.650/unit
3. Sports Sneakers (Size 9)    | SKU: SKU-SNK-007 | Qty: 80 units  | Rs.1200/unit
Expected delivery: 2025-07-15. Payment terms: Net 30.
Ramesh Kumar | ramesh@sunrise-textiles.in
"""

def get_plan():
    if USE_MOCK_PLAN:
        print("No Azure OpenAI key found - using mock plan\n")
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
            email_subject: str = "Restocking Confirmation"
            line_items: list = field(default_factory=list)
            total_order_value: float = 247500.0
            confidence_score: float = 0.97
            delivery_date: str = "2025-07-15"

        plan = _Plan()
        plan.line_items = [
            _Item("SKU-TSH-001", "Cotton T-Shirt",  300, 180.0,  54000.0),
            _Item("SKU-JNS-042", "Denim Jeans",     150, 650.0,  97500.0),
            _Item("SKU-SNK-007", "Sports Sneakers",  80, 1200.0, 96000.0),
        ]
        return plan
    else:
        from planner_agent.planner import PlannerAgent
        return PlannerAgent().parse_email(email_body=DEMO_EMAIL, subject="Restocking Confirmation")


def main():
    print("\n" + "="*60)
    print("  BusinessFlow AI - Pipeline Demo")
    print("  Stage 1: Planner  ->  Stage 2: Retriever")
    print("="*60)

    print("\n[STAGE 1] Planner Agent")
    print("-"*40)
    plan = get_plan()
    print(f"  Plan ID     : {plan.plan_id}")
    print(f"  Supplier    : {plan.supplier_name}")
    print(f"  Items       : {len(plan.line_items)}")
    print(f"  Order Value : Rs.{plan.total_order_value:,.2f}")
    print(f"  Confidence  : {plan.confidence_score * 100:.0f}%")

    print("\n[STAGE 2] Retriever Agent")
    print("-"*40)
    from retriever_agent.retriever import RetrieverAgent
    context = RetrieverAgent(backend="mock").retrieve(plan)

    icons = {"OUT_OF_STOCK": "[RED]", "LOW_STOCK": "[YELLOW]", "ADEQUATE": "[GREEN]"}
    for s in context.sku_contexts:
        print(f"\n  {icons.get(s.stock_status, '?')} [{s.sku_id}] {s.product_name}")
        print(f"     Stock: {s.current_stock} | Threshold: {s.reorder_threshold} | Status: {s.stock_status}")
        print(f"     Internal Cost: Rs.{s.unit_cost:,.2f}/unit | Lead: {s.supplier_lead_days} days")

    print(f"\n  Total DB Stock Value: Rs.{context.total_current_stock_value:,.2f}")
    print("\n  Next: Policy Layer will evaluate against the Rs.50,000 threshold")
    print("="*60)

if __name__ == "__main__":
    main()