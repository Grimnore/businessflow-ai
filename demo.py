"""
BusinessFlow AI — Quick Demo
=============================
Run this script locally to test the Planner Agent end-to-end
against a real Azure OpenAI deployment.

Usage:
    1. Copy .env.example → .env and fill in your credentials
    2. pip install -r requirements.txt
    3. python demo.py
"""

import json
import os
from dotenv import load_dotenv

load_dotenv()

from planner_agent.planner import PlannerAgent

# ── Demo email ────────────────────────────────────────────────────────────────
DEMO_EMAIL = """
Subject: Restocking Confirmation – June 2025 Batch

Hi Team,

We are pleased to confirm availability for your upcoming restocking cycle.
Please find the details below:

1. Cotton T-Shirt (White, L)     | SKU: SKU-TSH-001 | Qty: 300 units | ₹180/unit
2. Denim Jeans (32W)             | SKU: SKU-JNS-042 | Qty: 150 units | ₹650/unit
3. Sports Sneakers (Size 9)      | SKU: SKU-SNK-007 | Qty: 80 units  | ₹1,200/unit

Expected delivery: 15th July 2025
Payment terms: Net 30 days from invoice date.

Kindly confirm your order at the earliest.

Best regards,
Ramesh Kumar
Sunrise Textiles Pvt. Ltd.
ramesh@sunrise-textiles.in | +91 98765 43210
"""

DEMO_SUBJECT = "Restocking Confirmation – June 2025 Batch"


def main():
    print("\n" + "="*60)
    print("  BusinessFlow AI — Planner Agent Demo")
    print("="*60)

    print("\n📧  Input Email:")
    print("-"*40)
    print(DEMO_EMAIL.strip())

    print("\n🤖  Running Planner Agent...")
    agent = PlannerAgent()
    plan = agent.parse_email(email_body=DEMO_EMAIL, subject=DEMO_SUBJECT)

    print("\n✅  Execution Plan Generated:")
    print("-"*40)
    plan_dict = json.loads(plan.json())

    print(f"  Plan ID       : {plan_dict['plan_id']}")
    print(f"  Supplier      : {plan_dict['supplier_name']} <{plan_dict['supplier_email']}>")
    print(f"  Delivery Date : {plan_dict['delivery_date']}")
    print(f"  Confidence    : {plan_dict['confidence_score'] * 100:.0f}%")
    print(f"\n  Line Items ({len(plan_dict['line_items'])}):")
    for i, item in enumerate(plan_dict['line_items'], 1):
        cost = f"₹{item['total_cost']:,.0f}" if item.get('total_cost') else "N/A"
        print(f"    {i}. [{item['sku_id']}] {item['product_name']}")
        print(f"       Qty: {item['quantity']} × ₹{item['unit_price']} = {cost}")

    print(f"\n  💰 Total Order Value : ₹{plan_dict['total_order_value']:,.2f}")

    # Policy check preview
    threshold = float(os.getenv("POLICY_AUTO_APPROVE_THRESHOLD", 50000))
    if plan.total_order_value >= threshold:
        print(f"\n  🔴 POLICY: Order exceeds ₹{threshold:,.0f} → Requires manual approval")
    else:
        print(f"\n  🟢 POLICY: Order within ₹{threshold:,.0f} → Will auto-execute")

    print("\n  📋 Full JSON Plan:")
    print(plan.json(indent=2))
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
