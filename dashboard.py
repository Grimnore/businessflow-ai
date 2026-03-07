"""
BusinessFlow AI — Approval Dashboard (Business-Friendly)
Run: streamlit run dashboard.py
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import streamlit as st

st.set_page_config(page_title="BusinessFlow AI", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=DM+Sans:wght@300;400;500;600;700&display=swap');
:root { --navy:#0D1B2A; --navymid:#1B2F45; --navycard:#162436; --cyan:#00C2CB; --green:#00C896; --yellow:#FFB800; --red:#FF5A5A; --white:#FFFFFF; --offwhite:#E8F4F8; --muted:#8BAABB; --border:#1E3A4F; }
html,body,[class*="css"] { font-family:'DM Sans',sans-serif; background-color:var(--navy)!important; color:var(--offwhite)!important; }
.stApp { background-color:var(--navy)!important; }
#MainMenu,footer,header { visibility:hidden; }
.block-container { padding:1.5rem 2rem 2rem 2rem!important; max-width:1400px; }
[data-testid="stSidebar"] { background-color:var(--navymid)!important; border-right:1px solid var(--border); }
[data-testid="stSidebar"] * { color:var(--offwhite)!important; }
[data-testid="collapsedControl"] { background-color:var(--navymid)!important; border:1px solid var(--border)!important; border-radius:0 8px 8px 0!important; width:1.8rem!important; height:2.5rem!important; top:50%!important; transform:translateY(-50%)!important; }
[data-testid="collapsedControl"]:hover { background-color:var(--cyan)!important; }
[data-testid="collapsedControl"] svg { fill:var(--cyan)!important; }
[data-testid="collapsedControl"]:hover svg { fill:var(--navy)!important; }
.metric-card { background:var(--navycard); border:1px solid var(--border); border-radius:10px; padding:1.2rem 1.4rem; position:relative; overflow:hidden; height:100%; }
.metric-card::before { content:''; position:absolute; top:0; left:0; width:100%; height:3px; background:var(--accent-color,var(--cyan)); }
.metric-label { font-size:0.78rem; color:var(--muted); margin-bottom:0.3rem; font-weight:500; }
.metric-value { font-family:'JetBrains Mono',monospace; font-size:2rem; font-weight:700; color:var(--accent-color,var(--cyan)); line-height:1; }
.metric-sub { font-size:0.72rem; color:var(--muted); margin-top:0.3rem; }
.order-card { background:var(--navycard); border:1px solid var(--border); border-radius:12px; padding:1.6rem; margin-bottom:1.2rem; position:relative; overflow:hidden; }
.order-card::before { content:''; position:absolute; top:0; left:0; width:100%; height:4px; background:var(--status-color,var(--yellow)); }
.auto-card { background:var(--navycard); border:1px solid var(--border); border-radius:10px; padding:1.1rem 1.3rem; margin-bottom:0.7rem; position:relative; overflow:hidden; }
.auto-card::before { content:''; position:absolute; top:0; left:0; width:100%; height:3px; background:var(--green); }
.badge { display:inline-block; padding:0.22rem 0.7rem; border-radius:20px; font-size:0.7rem; font-weight:600; }
.badge-pending  { background:rgba(255,184,0,0.15);  color:var(--yellow); border:1px solid rgba(255,184,0,0.35); }
.badge-approved { background:rgba(0,200,150,0.15);  color:var(--green);  border:1px solid rgba(0,200,150,0.35); }
.badge-rejected { background:rgba(255,90,90,0.12);  color:var(--red);    border:1px solid rgba(255,90,90,0.35); }
.badge-auto     { background:rgba(0,194,203,0.12);  color:var(--cyan);   border:1px solid rgba(0,194,203,0.35); }
.flag-box { background:rgba(255,184,0,0.06); border:1px solid rgba(255,184,0,0.22); border-left:3px solid var(--yellow); border-radius:6px; padding:0.7rem 1rem; margin:0.8rem 0; font-size:0.82rem; color:var(--offwhite); }
.flag-box strong { color:var(--yellow); }
.auto-box { background:rgba(0,200,150,0.05); border:1px solid rgba(0,200,150,0.18); border-left:3px solid var(--green); border-radius:6px; padding:0.55rem 0.85rem; margin:0.5rem 0 0 0; font-size:0.78rem; color:#8BAABB; }
.item-row { display:flex; justify-content:space-between; align-items:center; padding:0.55rem 0.9rem; background:var(--navymid); border-radius:7px; margin-bottom:0.3rem; }
.item-name { font-size:0.88rem; color:var(--offwhite); font-weight:500; }
.item-price { font-family:'JetBrains Mono',monospace; font-size:0.9rem; color:var(--yellow); font-weight:700; }
.auto-item-price { font-family:'JetBrains Mono',monospace; font-size:0.9rem; color:var(--cyan); font-weight:700; }
.check-item { display:flex; align-items:flex-start; gap:0.55rem; padding:0.35rem 0; font-size:0.82rem; }
.check-ok   { color:var(--green);  font-size:1rem; margin-top:0.05rem; }
.check-warn { color:var(--yellow); font-size:1rem; margin-top:0.05rem; }
.stButton > button { font-family:'DM Sans',sans-serif!important; font-size:0.88rem!important; font-weight:700!important; border-radius:8px!important; border:none!important; padding:0.6rem 1.6rem!important; transition:all 0.15s ease!important; }
.approve-btn > button { background:var(--green)!important; color:#000!important; }
.approve-btn > button:hover { background:#00e0a8!important; }
.reject-btn  > button { background:transparent!important; color:var(--red)!important; border:1px solid var(--red)!important; }
.toast        { background:rgba(0,200,150,0.1); border:1px solid rgba(0,200,150,0.35); border-left:4px solid var(--green); border-radius:8px; padding:0.9rem 1.2rem; font-size:0.85rem; color:var(--green); margin-bottom:1.2rem; }
.toast-reject { background:rgba(255,90,90,0.08); border:1px solid rgba(255,90,90,0.3); border-left:4px solid var(--red); color:var(--red); }
.section-hdr { font-size:0.7rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; color:var(--muted); margin:1.4rem 0 0.7rem 0; padding-bottom:0.4rem; border-bottom:1px solid var(--border); }
.empty-state { text-align:center; padding:3rem 2rem; color:var(--muted); }
.empty-icon  { font-size:2.8rem; margin-bottom:0.8rem; }
.empty-title { font-size:1.05rem; font-weight:600; color:var(--offwhite); margin-bottom:0.4rem; }
.audit-row    { display:flex; gap:1rem; padding:0.55rem 0; border-bottom:1px solid var(--border); align-items:flex-start; }
.audit-time   { font-family:'JetBrains Mono',monospace; color:var(--muted); min-width:65px; font-size:0.72rem; padding-top:0.1rem; }
.audit-who    { min-width:110px; font-size:0.78rem; font-weight:600; }
.audit-what   { font-size:0.78rem; font-weight:600; min-width:160px; }
.audit-detail { color:var(--muted); font-size:0.78rem; }
.divider-label { display:flex; align-items:center; gap:0.7rem; margin:1.5rem 0 0.8rem 0; }
.divider-label span { font-size:0.7rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; color:var(--muted); white-space:nowrap; }
.divider-label::before,.divider-label::after { content:''; flex:1; height:1px; background:var(--border); }
hr { border-color:var(--border)!important; margin:1rem 0!important; }
[data-testid="stExpander"] { border:1px solid var(--border)!important; border-radius:8px!important; background:var(--navycard)!important; }
details summary { font-size:0.82rem!important; }
</style>
""", unsafe_allow_html=True)

# ── Data models ───────────────────────────────────────────────────────────────

@dataclass
class LineItem:
    sku_id: str; product_name: str; quantity: int; unit_price: float; total_cost: float

@dataclass
class PolicyCheck:
    label: str; passed: bool; note: str

@dataclass
class PendingOrder:
    plan_id: str; supplier_name: str; supplier_email: str; email_subject: str
    total_order_value: float; delivery_date: str; submitted_at: str
    flagged_reason: str; line_items: list; policy_checks: list
    status: str = "PENDING"
    reviewed_by: Optional[str] = None; reviewed_at: Optional[str] = None
    execution_result: Optional[dict] = None

@dataclass
class AutoOrder:
    """An order that was fully handled by the AI — no human needed."""
    plan_id: str; supplier_name: str; supplier_email: str; email_subject: str
    total_order_value: float; delivery_date: str; handled_at: str
    line_items: list; reason: str   # Why it was auto-approved

@dataclass
class ActivityEntry:
    timestamp: str; who: str; what: str; detail: str; plan_id: str; color: str = "#8BAABB"

# ── Session state ─────────────────────────────────────────────────────────────

def init_state():
    if "orders"      not in st.session_state: st.session_state.orders      = _seed_orders()
    if "auto_orders" not in st.session_state: st.session_state.auto_orders = _seed_auto_orders()
    if "activity"    not in st.session_state: st.session_state.activity    = _seed_activity()
    if "toast"       not in st.session_state: st.session_state.toast       = None

def _seed_orders():
    return [
        PendingOrder(
            plan_id="ORD-2025-003", supplier_name="Sunrise Textiles Pvt. Ltd.",
            supplier_email="ramesh@sunrise-textiles.in",
            email_subject="Restocking Confirmation – June Batch",
            total_order_value=247500.0, delivery_date="15 July 2025", submitted_at="Today, 9:14 AM",
            flagged_reason="This order is above your ₹50,000 auto-approve limit and needs your sign-off before we place it.",
            line_items=[
                LineItem("SKU-TSH-001","Cotton T-Shirt (White, L)",300,180.0,54000.0),
                LineItem("SKU-JNS-042","Denim Jeans (32W)",150,650.0,97500.0),
                LineItem("SKU-SNK-007","Sports Sneakers (Size 9)",80,1200.0,96000.0),
            ],
            policy_checks=[
                PolicyCheck("Supplier recognised",       True,  "Sunrise Textiles is in your approved supplier list."),
                PolicyCheck("All products found",        True,  "All 3 items exist in your inventory system."),
                PolicyCheck("All items need restocking", True,  "T-Shirts, Jeans & Sneakers are all running low."),
                PolicyCheck("Prices look normal",        True,  "Supplier prices are within your usual range."),
                PolicyCheck("Order value",               False, "₹2,47,500 exceeds your ₹50,000 auto-approve limit — needs your approval."),
            ],
        ),
        PendingOrder(
            plan_id="ORD-2025-004", supplier_name="Metro Fabrics Co.",
            supplier_email="orders@metrofabrics.com",
            email_subject="Urgent Restock – Cap & Bag",
            total_order_value=68000.0, delivery_date="28 June 2025", submitted_at="Today, 11:02 AM",
            flagged_reason="The supplier email was unclear in a few places. Please verify the order details before we proceed.",
            line_items=[
                LineItem("SKU-CAP-003","Snapback Cap (Assorted)",400,95.0,38000.0),
                LineItem("SKU-BAG-011","Canvas Tote Bag (Natural)",130,230.0,29900.0),
            ],
            policy_checks=[
                PolicyCheck("Supplier recognised",       True,  "Metro Fabrics Co. is in your approved supplier list."),
                PolicyCheck("All products found",        True,  "Both items exist in your inventory system."),
                PolicyCheck("All items need restocking", True,  "Caps and Tote Bags are running low."),
                PolicyCheck("Prices look normal",        True,  "Supplier prices are within your usual range."),
                PolicyCheck("Email clarity",             False, "The email had some unclear sections — please review the quantities."),
                PolicyCheck("Order value",               False, "₹68,000 exceeds your ₹50,000 auto-approve limit — needs your approval."),
            ],
        ),
    ]

def _seed_auto_orders():
    """Orders the AI handled entirely on its own today."""
    return [
        AutoOrder(
            plan_id="ORD-2025-001", supplier_name="QuickStitch Supplies",
            supplier_email="supply@quickstitch.in",
            email_subject="Weekly Restock – Accessories",
            total_order_value=11500.0, delivery_date="22 June 2025",
            handled_at="Today, 8:30 AM",
            reason="Order was under ₹50,000, all items were verified, and prices were normal. Placed automatically.",
            line_items=[
                LineItem("SKU-BAG-011","Canvas Tote Bag (Natural)",50,230.0,11500.0),
            ],
        ),
        AutoOrder(
            plan_id="ORD-2025-002", supplier_name="ThreadWorks India",
            supplier_email="orders@threadworks.in",
            email_subject="Low Stock Replenishment – June",
            total_order_value=19500.0, delivery_date="24 June 2025",
            handled_at="Today, 10:15 AM",
            reason="Order was under ₹50,000, both items needed restocking, and supplier is on your approved list.",
            line_items=[
                LineItem("SKU-JNS-042","Denim Jeans (32W)",30,650.0,19500.0),
            ],
        ),
        AutoOrder(
            plan_id="ORD-2025-005", supplier_name="Fabric First Co.",
            supplier_email="restock@fabricfirst.com",
            email_subject="T-Shirt Restock Request",
            total_order_value=9600.0, delivery_date="21 June 2025",
            handled_at="Today, 7:45 AM",
            reason="Small order under ₹50,000. All items verified and prices were within normal range.",
            line_items=[
                LineItem("SKU-SNK-007","Sports Sneakers (Size 8)",8,1200.0,9600.0),
            ],
        ),
    ]

def _seed_activity():
    return [
        ActivityEntry("7:45 AM", "AI System","New order received",  "Processed email from Fabric First Co. Found 1 item to restock.","ORD-2025-005","#00C2CB"),
        ActivityEntry("7:45 AM", "AI System","Order placed automatically","₹9,600 order placed with Fabric First Co. No action needed from you.","ORD-2025-005","#00C896"),
        ActivityEntry("8:30 AM", "AI System","New order received",  "Processed email from QuickStitch Supplies. Found 1 item to restock.","ORD-2025-001","#00C2CB"),
        ActivityEntry("8:30 AM", "AI System","Order placed automatically","₹11,500 order placed with QuickStitch Supplies. No action needed from you.","ORD-2025-001","#00C896"),
        ActivityEntry("9:14 AM", "AI System","New order received",  "Processed email from Sunrise Textiles. Found 3 items to restock.","ORD-2025-003","#00C2CB"),
        ActivityEntry("9:14 AM", "AI System","Sent for your review","Order value ₹2,47,500 is above the ₹50,000 limit. Waiting for your approval.","ORD-2025-003","#FFB800"),
        ActivityEntry("10:15 AM","AI System","New order received",  "Processed email from ThreadWorks India. Found 1 item to restock.","ORD-2025-002","#00C2CB"),
        ActivityEntry("10:15 AM","AI System","Order placed automatically","₹19,500 order placed with ThreadWorks India. No action needed from you.","ORD-2025-002","#00C896"),
        ActivityEntry("11:02 AM","AI System","New order received",  "Processed email from Metro Fabrics. Found 2 items to restock.","ORD-2025-004","#00C2CB"),
        ActivityEntry("11:02 AM","AI System","Sent for your review","Email was unclear and order value is above limit. Waiting for your approval.","ORD-2025-004","#FFB800"),
    ]

def _now():
    try:    return datetime.now().strftime("%-I:%M %p")
    except: return datetime.now().strftime("%H:%M")

def add_activity(plan_id, who, what, detail, color="#8BAABB"):
    st.session_state.activity.append(ActivityEntry(_now(), who, what, detail, plan_id, color))

def fmt_inr(v):
    return f"₹{v/100000:.2f}L" if v >= 100000 else f"₹{v:,.0f}"

def stock_label(sku_id):
    d = {"SKU-TSH-001":("🟡","Running low"),"SKU-JNS-042":("🟡","Running low"),
         "SKU-SNK-007":("🔴","Out of stock"),"SKU-CAP-003":("🟢","Well stocked"),"SKU-BAG-011":("🟡","Running low")}
    return d.get(sku_id, ("⚪","Unknown"))

# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("""<div style="padding:0.4rem 0 1.6rem 0">
            <div style="font-size:1.15rem;font-weight:700;color:#fff">⚡ BusinessFlow<span style="color:#00C2CB">AI</span></div>
            <div style="font-size:0.72rem;color:#8BAABB;margin-top:0.15rem">Smart Inventory Assistant</div>
        </div>""", unsafe_allow_html=True)

        orders      = st.session_state.orders
        auto_orders = st.session_state.auto_orders
        pending     = [o for o in orders if o.status == "PENDING"]
        approved    = [o for o in orders if o.status == "APPROVED"]

        st.markdown('<div class="section-hdr">Menu</div>', unsafe_allow_html=True)
        page = st.radio("", [
            "🔔  Needs Your Attention",
            "🤖  Auto-Handled by AI",
            "✅  Approved by You",
            "❌  Declined Orders",
            "📋  Activity Log",
        ], label_visibility="collapsed")

        # Summary
        st.markdown('<div class="section-hdr">Today\'s Overview</div>', unsafe_allow_html=True)
        auto_val  = sum(o.total_order_value for o in auto_orders)
        wait_val  = sum(o.total_order_value for o in pending)

        st.markdown(f"""
        <div style="display:flex;flex-direction:column;gap:0.5rem">
            <div style="background:#162436;border:1px solid #1E3A4F;border-radius:8px;padding:0.75rem 1rem">
                <div style="font-size:0.7rem;color:#8BAABB">🤖 AI handled automatically</div>
                <div style="display:flex;align-items:baseline;gap:0.5rem;margin-top:0.15rem">
                    <span style="font-size:1.4rem;font-weight:700;color:#00C896;font-family:'JetBrains Mono',monospace">{len(auto_orders)}</span>
                    <span style="font-size:0.75rem;color:#8BAABB">orders · {fmt_inr(auto_val)}</span>
                </div>
            </div>
            <div style="background:#162436;border:1px solid #1E3A4F;border-radius:8px;padding:0.75rem 1rem">
                <div style="font-size:0.7rem;color:#8BAABB">🔔 Waiting for you</div>
                <div style="display:flex;align-items:baseline;gap:0.5rem;margin-top:0.15rem">
                    <span style="font-size:1.4rem;font-weight:700;color:#FFB800;font-family:'JetBrains Mono',monospace">{len(pending)}</span>
                    <span style="font-size:0.75rem;color:#8BAABB">orders · {fmt_inr(wait_val)}</span>
                </div>
            </div>
            <div style="background:#162436;border:1px solid #1E3A4F;border-radius:8px;padding:0.75rem 1rem">
                <div style="font-size:0.7rem;color:#8BAABB">✅ You approved</div>
                <div style="display:flex;align-items:baseline;gap:0.5rem;margin-top:0.15rem">
                    <span style="font-size:1.4rem;font-weight:700;color:#00C2CB;font-family:'JetBrains Mono',monospace">{len(approved)}</span>
                    <span style="font-size:0.75rem;color:#8BAABB">orders today</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-hdr">How It Works</div>', unsafe_allow_html=True)
        st.markdown("""<div style="font-size:0.78rem;color:#8BAABB;line-height:2.1">
            📧 Reads your supplier emails<br>
            📦 Checks your stock levels<br>
            ✅ Places small orders automatically<br>
            🔔 Flags large orders for you
        </div>""", unsafe_allow_html=True)

        return page

# ── Order card (for pending / approved / rejected) ────────────────────────────

def render_order_card(order, show_actions=True):
    sc   = {"PENDING":"#FFB800","APPROVED":"#00C896","REJECTED":"#FF5A5A"}.get(order.status,"#00C2CB")
    bcls = {"PENDING":"badge-pending","APPROVED":"badge-approved","REJECTED":"badge-rejected"}.get(order.status,"")
    blbl = {"PENDING":"⚠ Needs your approval","APPROVED":"✓ Approved by you","REJECTED":"✕ Declined"}.get(order.status,order.status)

    st.markdown(f"""
    <div class="order-card" style="--status-color:{sc}">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.8rem">
            <div>
                <div style="font-size:1.05rem;font-weight:700;color:#fff">{order.supplier_name}</div>
                <div style="font-size:0.8rem;color:#8BAABB;margin-top:0.12rem">{order.email_subject}</div>
                <div style="margin-top:0.45rem"><span class="badge {bcls}">{blbl}</span></div>
            </div>
            <div style="text-align:right">
                <div style="font-size:0.68rem;color:#8BAABB;text-transform:uppercase;letter-spacing:0.06em">Order Total</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:1.45rem;font-weight:700;color:#FFB800">{fmt_inr(order.total_order_value)}</div>
                <div style="font-size:0.73rem;color:#8BAABB">Delivery by {order.delivery_date}</div>
                <div style="font-size:0.7rem;color:#8BAABB;margin-top:0.05rem">Received {order.submitted_at}</div>
            </div>
        </div>
        <div class="flag-box"><strong>Why this needs your attention:</strong><br>{order.flagged_reason}</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(f"📦  View order details — {len(order.line_items)} products"):
        st.markdown('<div style="font-size:0.82rem;font-weight:600;color:#8BAABB;margin-bottom:0.5rem">Products being ordered</div>', unsafe_allow_html=True)
        for item in order.line_items:
            icon, lbl = stock_label(item.sku_id)
            st.markdown(f"""<div class="item-row">
                <div><span class="item-name">{item.product_name}</span>
                <span style="font-size:0.72rem;color:#8BAABB;margin-left:0.7rem">{icon} {lbl} in your warehouse</span></div>
                <div style="text-align:right">
                <span style="font-size:0.8rem;color:#8BAABB">{item.quantity} units @ ₹{item.unit_price:,.0f}</span>
                <span class="item-price" style="margin-left:1rem">{fmt_inr(item.total_cost)}</span></div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.82rem;font-weight:600;color:#8BAABB;margin-bottom:0.4rem">What we already checked for you</div>', unsafe_allow_html=True)
        for check in order.policy_checks:
            icon = "✓" if check.passed else "⚠"
            cls  = "check-ok" if check.passed else "check-warn"
            col  = "#8BAABB" if check.passed else "#E8F4F8"
            st.markdown(f"""<div class="check-item">
                <span class="{cls}">{icon}</span>
                <div><span style="font-weight:600;color:{col}">{check.label}</span>
                <span style="color:#8BAABB"> — {check.note}</span></div>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""<div style="margin-top:0.8rem;padding:0.6rem 0.9rem;background:rgba(0,194,203,0.06);
            border:1px solid rgba(0,194,203,0.18);border-radius:6px;font-size:0.78rem;color:#8BAABB">
            📧 Supplier contact: <span style="color:#00C2CB">{order.supplier_email}</span></div>""", unsafe_allow_html=True)

    if show_actions and order.status == "PENDING":
        st.markdown("<div style='margin-top:0.7rem'></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1.5, 0.9, 3])
        with c1:
            st.markdown('<div class="approve-btn">', unsafe_allow_html=True)
            if st.button("✓  Approve & Place Order", key=f"approve_{order.plan_id}"):
                _approve(order); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="reject-btn">', unsafe_allow_html=True)
            if st.button("✕  Decline", key=f"reject_{order.plan_id}"):
                _reject(order); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    if order.status == "APPROVED" and order.execution_result:
        r = order.execution_result
        st.markdown(f"""<div style="background:rgba(0,200,150,0.08);border:1px solid rgba(0,200,150,0.22);
            border-left:3px solid #00C896;border-radius:6px;padding:0.7rem 1rem;margin-top:0.6rem;font-size:0.82rem">
            <span style="color:#00C896;font-weight:700">✓ Order placed successfully</span>
            <span style="color:#8BAABB"> — {r['orders_created']} purchase orders created, {fmt_inr(r['total_value'])} committed.
            Supplier notified. Approved by {order.reviewed_by} at {order.reviewed_at}.</span></div>""", unsafe_allow_html=True)

    if order.status == "REJECTED":
        st.markdown(f"""<div style="background:rgba(255,90,90,0.06);border:1px solid rgba(255,90,90,0.18);
            border-left:3px solid #FF5A5A;border-radius:6px;padding:0.7rem 1rem;margin-top:0.6rem;font-size:0.82rem">
            <span style="color:#FF5A5A;font-weight:700">✕ Order declined</span>
            <span style="color:#8BAABB"> — No stock changes made.
            Declined by {order.reviewed_by} at {order.reviewed_at}.</span></div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:0.4rem'></div>", unsafe_allow_html=True)


# ── Auto-order card ───────────────────────────────────────────────────────────

def render_auto_card(order: AutoOrder):
    st.markdown(f"""
    <div class="auto-card">
        <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div>
                <div style="font-size:1rem;font-weight:700;color:#fff">{order.supplier_name}</div>
                <div style="font-size:0.78rem;color:#8BAABB;margin-top:0.1rem">{order.email_subject}</div>
                <div style="margin-top:0.4rem"><span class="badge badge-auto">🤖 Handled automatically</span></div>
            </div>
            <div style="text-align:right">
                <div style="font-size:0.68rem;color:#8BAABB;text-transform:uppercase;letter-spacing:0.06em">Order Total</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:1.3rem;font-weight:700;color:#00C2CB">{fmt_inr(order.total_order_value)}</div>
                <div style="font-size:0.72rem;color:#8BAABB">Delivery by {order.delivery_date}</div>
                <div style="font-size:0.7rem;color:#8BAABB;margin-top:0.05rem">Placed {order.handled_at}</div>
            </div>
        </div>
        <div class="auto-box">✓ {order.reason}</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(f"📦  View details — {len(order.line_items)} product{'s' if len(order.line_items)>1 else ''}"):
        st.markdown('<div style="font-size:0.82rem;font-weight:600;color:#8BAABB;margin-bottom:0.5rem">Products ordered</div>', unsafe_allow_html=True)
        for item in order.line_items:
            icon, lbl = stock_label(item.sku_id)
            st.markdown(f"""<div class="item-row">
                <div><span class="item-name">{item.product_name}</span>
                <span style="font-size:0.72rem;color:#8BAABB;margin-left:0.7rem">{icon} Was {lbl}</span></div>
                <div style="text-align:right">
                <span style="font-size:0.8rem;color:#8BAABB">{item.quantity} units @ ₹{item.unit_price:,.0f}</span>
                <span class="auto-item-price" style="margin-left:1rem">{fmt_inr(item.total_cost)}</span></div>
            </div>""", unsafe_allow_html=True)
        st.markdown(f"""<div style="margin-top:0.8rem;padding:0.6rem 0.9rem;background:rgba(0,194,203,0.05);
            border:1px solid rgba(0,194,203,0.15);border-radius:6px;font-size:0.78rem;color:#8BAABB">
            📧 <span style="color:#00C2CB">{order.supplier_email}</span></div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:0.3rem'></div>", unsafe_allow_html=True)


# ── Actions ───────────────────────────────────────────────────────────────────

def _approve(order):
    now = _now()
    order.status, order.reviewed_at, order.reviewed_by = "APPROVED", now, "Operations Manager"
    total = sum(i.total_cost for i in order.line_items)
    order.execution_result = {"orders_created": len(order.line_items), "total_value": total}
    add_activity(order.plan_id,"You","Approved order",f"Approved {order.supplier_name} order. {fmt_inr(total)} committed.","#00C896")
    add_activity(order.plan_id,"AI System","Order placed",f"Purchase orders created. Supplier notified by email.","#00C2CB")
    st.session_state.toast = ("approve", order.supplier_name, total)

def _reject(order):
    now = _now()
    order.status, order.reviewed_at, order.reviewed_by = "REJECTED", now, "Operations Manager"
    add_activity(order.plan_id,"You","Declined order",f"Declined {order.supplier_name} order. No stock changes made.","#FF5A5A")
    st.session_state.toast = ("reject", order.supplier_name, order.total_order_value)

# ── Pages ─────────────────────────────────────────────────────────────────────

def page_pending():
    orders  = [o for o in st.session_state.orders if o.status == "PENDING"]
    total_v = sum(o.total_order_value for o in orders)
    auto    = st.session_state.auto_orders
    auto_v  = sum(o.total_order_value for o in auto)

    st.markdown("""<div style="margin-bottom:0.2rem">
        <div style="font-size:1.5rem;font-weight:700;color:#fff">Good morning 👋</div>
        <div style="font-size:0.88rem;color:#8BAABB;margin-top:0.1rem">
            Here's what happened with your inventory today.
        </div>
    </div>""", unsafe_allow_html=True)

    if st.session_state.toast:
        kind, name, val = st.session_state.toast
        if kind == "approve":
            st.markdown(f'<div class="toast">✓ Done! Order from <strong>{name}</strong> approved and placed — {fmt_inr(val)} committed.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="toast toast-reject">✕ Order from <strong>{name}</strong> declined. No changes were made.</div>', unsafe_allow_html=True)
        st.session_state.toast = None

    # Top metrics row
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"""<div class="metric-card" style="--accent-color:#FFB800">
        <div class="metric-label">🔔 Waiting for you</div>
        <div class="metric-value">{len(orders)}</div>
        <div class="metric-sub">{fmt_inr(total_v)} total value</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="metric-card" style="--accent-color:#00C896">
        <div class="metric-label">🤖 AI handled today</div>
        <div class="metric-value">{len(auto)}</div>
        <div class="metric-sub">{fmt_inr(auto_v)} placed automatically</div></div>""", unsafe_allow_html=True)
    with c3:
        approved = [o for o in st.session_state.orders if o.status=="APPROVED"]
        st.markdown(f"""<div class="metric-card" style="--accent-color:#00C2CB">
        <div class="metric-label">✅ You approved</div>
        <div class="metric-value">{len(approved)}</div>
        <div class="metric-sub">orders today</div></div>""", unsafe_allow_html=True)
    with c4:
        total_all = total_v + auto_v + sum(o.total_order_value for o in approved)
        st.markdown(f"""<div class="metric-card" style="--accent-color:#8BAABB">
        <div class="metric-label">📦 Total orders today</div>
        <div class="metric-value">{len(orders)+len(auto)+len(approved)}</div>
        <div class="metric-sub">{fmt_inr(total_all)} across all orders</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.4rem'></div>", unsafe_allow_html=True)

    # Two-column layout: Needs attention LEFT, Auto-handled RIGHT
    col_left, col_right = st.columns([1.1, 1], gap="large")

    with col_left:
        st.markdown(f"""<div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.8rem">
            <div style="width:10px;height:10px;border-radius:50%;background:#FFB800;
                box-shadow:0 0 8px #FFB800;animation:pulse 1.5s infinite"></div>
            <span style="font-size:0.9rem;font-weight:700;color:#fff">Needs Your Approval</span>
            <span style="background:rgba(255,184,0,0.15);color:#FFB800;border:1px solid rgba(255,184,0,0.3);
                border-radius:20px;padding:0.1rem 0.6rem;font-size:0.72rem;font-weight:700">{len(orders)}</span>
        </div>""", unsafe_allow_html=True)

        if not orders:
            st.markdown("""<div class="empty-state" style="padding:2.5rem 1rem">
                <div class="empty-icon">🎉</div>
                <div class="empty-title">All caught up!</div>
                <div style="font-size:0.82rem">No orders need your attention right now.</div>
            </div>""", unsafe_allow_html=True)
        else:
            for order in orders:
                render_order_card(order, show_actions=True)

    with col_right:
        st.markdown(f"""<div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.8rem">
            <span style="font-size:1rem">🤖</span>
            <span style="font-size:0.9rem;font-weight:700;color:#fff">Handled Automatically</span>
            <span style="background:rgba(0,200,150,0.15);color:#00C896;border:1px solid rgba(0,200,150,0.3);
                border-radius:20px;padding:0.1rem 0.6rem;font-size:0.72rem;font-weight:700">{len(auto)}</span>
        </div>""", unsafe_allow_html=True)

        if not auto:
            st.markdown("""<div class="empty-state" style="padding:2.5rem 1rem">
                <div class="empty-icon">📭</div>
                <div class="empty-title">No auto-handled orders yet</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div style="background:rgba(0,200,150,0.05);border:1px solid rgba(0,200,150,0.18);
                border-radius:8px;padding:0.7rem 1rem;margin-bottom:0.8rem;font-size:0.8rem;color:#8BAABB">
                💡 These orders were placed automatically because they were small, verified, and safe.
                <span style="color:#00C896"> You saved ~{len(auto)*25} minutes of manual work today.</span>
            </div>""", unsafe_allow_html=True)
            for order in auto:
                render_auto_card(order)


def page_auto():
    auto   = st.session_state.auto_orders
    auto_v = sum(o.total_order_value for o in auto)
    total_items = sum(len(o.line_items) for o in auto)

    st.markdown('<div style="font-size:1.5rem;font-weight:700;color:#fff;margin-bottom:0.2rem">Auto-Handled Orders 🤖</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.88rem;color:#8BAABB;margin-bottom:1.2rem">Orders BusinessFlow AI placed on your behalf today — no action needed from you.</div>', unsafe_allow_html=True)

    if not auto:
        st.markdown('<div class="empty-state"><div class="empty-icon">📭</div><div class="empty-title">No auto-handled orders yet today</div></div>', unsafe_allow_html=True)
        return

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"""<div class="metric-card" style="--accent-color:#00C896">
        <div class="metric-label">Orders handled</div><div class="metric-value">{len(auto)}</div>
        <div class="metric-sub">without interrupting you</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="metric-card" style="--accent-color:#00C2CB">
        <div class="metric-label">Total placed</div><div class="metric-value">{fmt_inr(auto_v)}</div>
        <div class="metric-sub">across {total_items} products</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="metric-card" style="--accent-color:#8BAABB">
        <div class="metric-label">Time saved</div><div class="metric-value">~{len(auto)*25}m</div>
        <div class="metric-sub">of manual email processing</div></div>""", unsafe_allow_html=True)

    st.markdown(f"""<div style="background:rgba(0,200,150,0.06);border:1px solid rgba(0,200,150,0.2);
        border-radius:8px;padding:0.8rem 1.1rem;margin:1rem 0 1.2rem 0;font-size:0.83rem;color:#8BAABB">
        💡 <strong style="color:#00C896">How auto-approval works:</strong>
        BusinessFlow AI places orders automatically when they are under ₹50,000,
        the supplier is on your approved list, all products exist in your system,
        and prices are within the normal range. Anything outside these rules comes to you for approval.
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-hdr">All auto-handled orders today</div>', unsafe_allow_html=True)
    for order in auto:
        render_auto_card(order)


def page_approved():
    orders = [o for o in st.session_state.orders if o.status=="APPROVED"]
    st.markdown('<div style="font-size:1.5rem;font-weight:700;color:#fff;margin-bottom:0.2rem">Approved by You ✅</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.88rem;color:#8BAABB;margin-bottom:1.2rem">Orders you personally approved — stock will update when they arrive.</div>', unsafe_allow_html=True)
    if not orders:
        st.markdown('<div class="empty-state"><div class="empty-icon">📭</div><div class="empty-title">No approved orders yet</div><div style="font-size:0.82rem">Orders you approve will appear here.</div></div>', unsafe_allow_html=True)
        return
    total = sum(o.total_order_value for o in orders)
    c1, c2 = st.columns(2)
    with c1: st.markdown(f"""<div class="metric-card" style="--accent-color:#00C896">
        <div class="metric-label">Orders approved</div><div class="metric-value">{len(orders)}</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="metric-card" style="--accent-color:#00C896">
        <div class="metric-label">Total committed</div><div class="metric-value">{fmt_inr(total)}</div></div>""", unsafe_allow_html=True)
    st.markdown("<div style='margin:1rem 0'></div>", unsafe_allow_html=True)
    for order in orders: render_order_card(order, show_actions=False)


def page_rejected():
    orders = [o for o in st.session_state.orders if o.status=="REJECTED"]
    st.markdown('<div style="font-size:1.5rem;font-weight:700;color:#fff;margin-bottom:0.2rem">Declined Orders ❌</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.88rem;color:#8BAABB;margin-bottom:1.2rem">Orders you declined — no stock changes were made.</div>', unsafe_allow_html=True)
    if not orders:
        st.markdown('<div class="empty-state"><div class="empty-icon">📭</div><div class="empty-title">No declined orders</div></div>', unsafe_allow_html=True)
        return
    for order in orders: render_order_card(order, show_actions=False)


def page_activity():
    st.markdown('<div style="font-size:1.5rem;font-weight:700;color:#fff;margin-bottom:0.2rem">Activity Log 📋</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.88rem;color:#8BAABB;margin-bottom:1.2rem">Everything that happened today — what the AI did automatically, and what you decided.</div>', unsafe_allow_html=True)

    activity = list(reversed(st.session_state.activity))
    all_ids  = list(dict.fromkeys(e.plan_id for e in st.session_state.activity))
    orders   = st.session_state.orders
    auto     = st.session_state.auto_orders
    all_orders = {**{o.plan_id: o.supplier_name for o in orders}, **{o.plan_id: o.supplier_name for o in auto}}
    options  = ["All suppliers"] + [f"{all_orders.get(p, p)} ({p})" for p in all_ids if p in all_orders]

    selected = st.selectbox("Filter by supplier", options, label_visibility="collapsed")
    if selected != "All suppliers":
        pid = next((p for p in all_ids if f"({p})" in selected), None)
        if pid: activity = [a for a in activity if a.plan_id == pid]

    st.markdown(f'<div style="font-size:0.75rem;color:#8BAABB;margin:0.5rem 0 0.3rem 0">{len(activity)} events</div>', unsafe_allow_html=True)

    icons = {"AI System":"🤖","You":"👤"}
    for e in activity:
        st.markdown(f"""<div class="audit-row">
            <span class="audit-time">{e.timestamp}</span>
            <span class="audit-who" style="color:{e.color}">{icons.get(e.who,"📌")} {e.who}</span>
            <span class="audit-what" style="color:{e.color}">{e.what}</span>
            <span class="audit-detail">{e.detail}</span>
        </div>""", unsafe_allow_html=True)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    init_state()
    page = render_sidebar()
    if   "Attention" in page: page_pending()
    elif "Auto"      in page: page_auto()
    elif "Approved"  in page: page_approved()
    elif "Declined"  in page: page_rejected()
    elif "Activity"  in page: page_activity()

if __name__ == "__main__":
    main()