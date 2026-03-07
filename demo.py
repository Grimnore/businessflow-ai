"""
BusinessFlow AI — Pipeline Demo (Planner + Retriever + Policy Layer)
"""
import os
from dotenv import load_dotenv
load_dotenv()

USE_MOCK_PLAN = os.getenv("AZURE_OPENAI_API_KEY") is None

def get_plan():
    if USE_MOCK_PLAN:
        print("No Azure OpenAI key found - using mock plan\n")
        from dataclasses import dataclass, field

        @dataclass
        class _Item:
            sku_id: str; product_name: str; quantity: int; unit_price: float; total_cost: float

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
        EMAIL = "Hi, supply: SKU-TSH-001 x300 @Rs180, SKU-JNS-042 x150 @Rs650, SKU-SNK-007 x80 @Rs1200. Delivery 2025-07-15. ramesh@sunrise-textiles.in"
        return PlannerAgent().parse_email(email_body=EMAIL, subject="Restocking Confirmation")


def main():
    print("\n" + "="*62)
    print("  BusinessFlow AI - Full Pipeline Demo")
    print("  Planner  ->  Retriever  ->  Policy Layer")
    print("="*62)

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
        print(f"  {icons.get(s.stock_status,'?')} [{s.sku_id}] {s.product_name} | Stock: {s.current_stock} | Status: {s.stock_status}")
    print(f"\n  Total DB Stock Value: Rs.{context.total_current_stock_value:,.2f}")

    print("\n[STAGE 3] Policy Layer")
    print("-"*40)
    from policy_layer.policy import PolicyLayer, PolicyConfig
    policy = PolicyLayer(PolicyConfig(auto_approve_limit=50000.0))
    decision = policy.evaluate(plan, context)

    icons2 = {"AUTO_APPROVE": "[APPROVED]", "ESCALATE": "[ESCALATED]", "REJECT": "[REJECTED]"}
    print(f"\n  {icons2.get(decision.decision.value,'?')} VERDICT: {decision.decision.value}")
    print(f"  Order Value : Rs.{decision.total_order_value:,.2f}")
    for r in decision.reasons:
        print(f"  Reason      : {r}")

    if decision.needs_human:
        print(f"\n  >> Escalated to: {decision.requires_approval_from}")
        for item in decision.escalated_items:
            print(f"     - {item}")

    if decision.auto_approved_items:
        print("\n  >> Auto-approved:")
        for item in decision.auto_approved_items:
            print(f"     - {item}")

    print("\n  Rule Audit Trail:")
    for r in decision.rule_results:
        status = "FIRED  " if r.triggered else "passed "
        print(f"    [{status}] {r.rule_name:<25} | {r.reason[:55]}")

    # Bonus: small order demo
    print("\n" + "-"*62)
    print("  BONUS: Small order Rs.11,500 (SKU-BAG-011 x50)")
    print("-"*62)
    from dataclasses import dataclass, field

    @dataclass
    class _SI:
        sku_id: str = "SKU-BAG-011"; product_name: str = "Canvas Tote Bag"
        quantity: int = 50; unit_price: float = 230.0; total_cost: float = 11500.0

    @dataclass
    class _SP:
        plan_id: str = "demo-plan-002"; supplier_name: str = "Test"
        supplier_email: str = "t@t.com"; email_subject: str = "Small"
        line_items: list = field(default_factory=list)
        total_order_value: float = 11500.0; confidence_score: float = 0.92
        delivery_date: str = "2025-07-20"

    sp = _SP(); sp.line_items = [_SI()]
    sc = RetrieverAgent(backend="mock").retrieve(sp)
    sd = policy.evaluate(sp, sc)
    print(f"  {icons2.get(sd.decision.value,'?')} VERDICT: {sd.decision.value}")
    print(f"  Rs.{sd.total_order_value:,.2f} | Reason: {sd.reasons[0]}")
    print("="*62 + "\n")

if __name__ == "__main__":
    main()