"""
BusinessFlow AI — Approval Dashboard
Team NeuroNekos | Microsoft AI Unlocked Hackathon
Run: streamlit run dashboard.py
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import streamlit as st

st.set_page_config(
    page_title="BusinessFlow AI · NeuroNekos",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --navy:      #080F1A;
    --navydark:  #050C14;
    --navymid:   #0F1E30;
    --navycard:  #0D1A28;
    --navylight: #162436;
    --cyan:      #00D4E0;
    --cyandk:    #00A8B5;
    --amber:     #F5A623;
    --amberdk:   #C8841A;
    --green:     #00D68F;
    --red:       #FF4D6A;
    --white:     #FFFFFF;
    --offwhite:  #DCE9F0;
    --muted:     #6B8FA8;
    --border:    #142030;
    --borderbr:  #1A2E42;
}

/* ── Reset & base ── */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    background-color: var(--navy) !important;
    color: var(--offwhite) !important;
}
.stApp { background-color: var(--navy) !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: var(--navydark) !important;
    border-right: 1px solid var(--border) !important;
    padding: 0 !important;
}
[data-testid="stSidebar"] > div { padding: 0 !important; }
[data-testid="stSidebar"] * { color: var(--offwhite) !important; }
section[data-testid="stSidebar"] .block-container { padding: 1rem !important; }

/* Sidebar toggle */
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    background-color: var(--cyan) !important;
    border: none !important;
    border-radius: 0 8px 8px 0 !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    width: 24px !important;
    height: 48px !important;
    align-items: center !important;
    justify-content: center !important;
    z-index: 9999 !important;
    box-shadow: 2px 0 12px rgba(0,212,224,0.3) !important;
}
[data-testid="collapsedControl"]:hover { background-color: #00f0fc !important; box-shadow: 2px 0 18px rgba(0,212,224,0.5) !important; }
[data-testid="collapsedControl"] svg { fill: var(--navy) !important; width: 14px !important; height: 14px !important; }

/* ── Main content padding ── */
.main-wrap { padding: 1.8rem 2.2rem; }

/* ── Brand header ── */
.brand-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 2.2rem;
    background: var(--navydark);
    border-bottom: 1px solid var(--border);
    position: sticky; top: 0; z-index: 100;
}
.brand-left { display: flex; align-items: center; gap: 1rem; }
.brand-logo {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.3rem;
    font-weight: 800;
    color: var(--white);
    letter-spacing: -0.02em;
}
.brand-logo span { color: var(--cyan); }
.brand-team {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: var(--muted);
    background: var(--navylight);
    border: 1px solid var(--border);
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    letter-spacing: 0.08em;
}
.brand-right {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: var(--muted);
    display: flex; align-items: center; gap: 0.5rem;
}
.live-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 6px var(--green);
    display: inline-block;
}

/* ── Sidebar brand ── */
.sb-brand {
    padding: 1.4rem 1.2rem 1rem 1.2rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 0.5rem;
}
.sb-logo {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.1rem;
    font-weight: 800;
    color: var(--white);
    letter-spacing: -0.01em;
}
.sb-logo span { color: var(--cyan); }
.sb-team {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    color: var(--amber);
    margin-top: 0.25rem;
    letter-spacing: 0.06em;
}
.sb-tagline {
    font-size: 0.72rem;
    color: var(--muted);
    margin-top: 0.3rem;
    line-height: 1.4;
}

/* ── Section header ── */
.sec-hdr {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--muted);
    margin: 1.2rem 0 0.6rem 0;
    padding-bottom: 0.35rem;
    border-bottom: 1px solid var(--border);
}

/* ── Stat cards ── */
.stat-card {
    background: var(--navycard);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.1rem 1.3rem;
    position: relative;
    overflow: hidden;
    height: 100%;
}
.stat-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent, var(--cyan)), transparent);
}
.stat-label { font-size: 0.72rem; color: var(--muted); margin-bottom: 0.3rem; font-weight: 500; }
.stat-val {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.9rem;
    font-weight: 800;
    color: var(--accent, var(--cyan));
    line-height: 1;
    letter-spacing: -0.02em;
}
.stat-sub { font-size: 0.7rem; color: var(--muted); margin-top: 0.3rem; }

/* ── Order cards ── */
.ord-card {
    background: var(--navycard);
    border: 1px solid var(--borderbr);
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}
.ord-card:hover { border-color: var(--cyan); }
.ord-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--stripe, var(--amber));
}

/* ── Auto cards ── */
.auto-card {
    background: var(--navycard);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.3rem;
    margin-bottom: 0.65rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.15s;
}
.auto-card:hover { border-color: var(--green); }
.auto-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--green);
}

/* ── Badges ── */
.badge {
    display: inline-flex; align-items: center; gap: 0.3rem;
    padding: 0.2rem 0.65rem;
    border-radius: 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem; font-weight: 600;
    letter-spacing: 0.04em;
}
.badge-pending  { background: rgba(245,166,35,0.12);  color: var(--amber); border: 1px solid rgba(245,166,35,0.3); }
.badge-approved { background: rgba(0,214,143,0.12);   color: var(--green); border: 1px solid rgba(0,214,143,0.3); }
.badge-rejected { background: rgba(255,77,106,0.1);   color: var(--red);   border: 1px solid rgba(255,77,106,0.3); }
.badge-auto     { background: rgba(0,212,224,0.1);    color: var(--cyan);  border: 1px solid rgba(0,212,224,0.3); }

/* ── Flag / info boxes ── */
.flag-box {
    background: rgba(245,166,35,0.05);
    border: 1px solid rgba(245,166,35,0.18);
    border-left: 3px solid var(--amber);
    border-radius: 6px;
    padding: 0.65rem 0.9rem;
    margin: 0.7rem 0;
    font-size: 0.8rem;
    color: var(--offwhite);
    line-height: 1.5;
}
.flag-box strong { color: var(--amber); }

.info-box {
    background: rgba(0,212,224,0.04);
    border: 1px solid rgba(0,212,224,0.15);
    border-left: 3px solid var(--cyan);
    border-radius: 6px;
    padding: 0.65rem 0.9rem;
    font-size: 0.78rem;
    color: var(--muted);
    line-height: 1.5;
}

.success-box {
    background: rgba(0,214,143,0.07);
    border: 1px solid rgba(0,214,143,0.2);
    border-left: 3px solid var(--green);
    border-radius: 6px;
    padding: 0.65rem 0.9rem;
    font-size: 0.8rem;
    line-height: 1.5;
}

/* ── Item rows ── */
.item-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.5rem 0.85rem;
    background: var(--navylight);
    border-radius: 6px;
    margin-bottom: 0.28rem;
    border: 1px solid var(--border);
}
.item-name { font-size: 0.85rem; color: var(--offwhite); font-weight: 500; }
.item-meta { font-size: 0.72rem; color: var(--muted); margin-left: 0.6rem; }
.item-price { font-family: 'JetBrains Mono', monospace; font-size: 0.88rem; font-weight: 600; }

/* ── Check list ── */
.chk-row { display: flex; align-items: flex-start; gap: 0.5rem; padding: 0.3rem 0; font-size: 0.8rem; }
.chk-ok   { color: var(--green);  font-size: 0.95rem; margin-top: 0.05rem; }
.chk-warn { color: var(--amber);  font-size: 0.95rem; margin-top: 0.05rem; }

/* ── Menu toggle button ── */
div[data-testid="stButton"] button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid #1A2E42 !important;
    color: #00D4E0 !important;
    font-size: 1.2rem !important;
    padding: 0.3rem 0.6rem !important;
    border-radius: 8px !important;
    line-height: 1 !important;
    min-height: unset !important;
}
div[data-testid="stButton"] button[kind="secondary"]:hover {
    background: rgba(0,212,224,0.1) !important;
    border-color: #00D4E0 !important;
}

/* ── Buttons ── */
.stButton > button {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.85rem !important; font-weight: 600 !important;
    border-radius: 7px !important; border: none !important;
    padding: 0.55rem 1.4rem !important;
    transition: all 0.15s !important;
    letter-spacing: 0.01em !important;
}
.btn-approve > button { background: var(--green) !important; color: #000 !important; }
.btn-approve > button:hover { background: #00f0a0 !important; box-shadow: 0 0 16px rgba(0,214,143,0.4) !important; }
.btn-decline > button { background: transparent !important; color: var(--red) !important; border: 1px solid var(--red) !important; }
.btn-decline > button:hover { background: rgba(255,77,106,0.08) !important; }

/* ── Toasts ── */
.toast         { background: rgba(0,214,143,0.08); border: 1px solid rgba(0,214,143,0.25); border-left: 4px solid var(--green); border-radius: 8px; padding: 0.85rem 1.1rem; font-size: 0.83rem; color: var(--green); margin-bottom: 1.1rem; }
.toast-decline { background: rgba(255,77,106,0.07); border: 1px solid rgba(255,77,106,0.22); border-left: 4px solid var(--red); color: var(--red); }

/* ── Activity log ── */
.act-row { display: flex; gap: 0.9rem; padding: 0.5rem 0; border-bottom: 1px solid var(--border); align-items: flex-start; }
.act-time   { font-family: 'JetBrains Mono', monospace; color: var(--muted); min-width: 60px; font-size: 0.68rem; padding-top: 0.12rem; }
.act-who    { min-width: 100px; font-size: 0.75rem; font-weight: 600; }
.act-what   { min-width: 150px; font-size: 0.75rem; font-weight: 600; }
.act-detail { font-size: 0.75rem; color: var(--muted); }

/* ── Pipeline status strip ── */
.pipeline-strip {
    display: flex; align-items: center; gap: 0;
    background: var(--navycard);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    margin: 1rem 0 1.4rem 0;
}
.pip-step {
    flex: 1; padding: 0.6rem 0.4rem;
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    color: var(--muted);
    border-right: 1px solid var(--border);
    position: relative;
}
.pip-step:last-child { border-right: none; }
.pip-step.active { color: var(--cyan); background: rgba(0,212,224,0.05); }
.pip-step.done   { color: var(--green); }
.pip-icon { font-size: 0.9rem; display: block; margin-bottom: 0.2rem; }

/* ── Empty states ── */
.empty { text-align: center; padding: 3.5rem 2rem; color: var(--muted); }
.empty-icon  { font-size: 2.5rem; margin-bottom: 0.7rem; }
.empty-title { font-size: 1rem; font-weight: 600; color: var(--offwhite); margin-bottom: 0.3rem; }

/* Sidebar toggle — bottom padding fix + clean button */
section[data-testid="stSidebar"] > div:first-child {
    padding-bottom: 120px !important;
}
[data-testid="collapsedControl"] {
    z-index: 99999 !important;
    background: #00D4E0 !important;
    border-radius: 0 8px 8px 0 !important;
}
[data-testid="collapsedControl"] svg { fill: #080F1A !important; }

/* Expander */
[data-testid="stExpander"] { border: 1px solid var(--border) !important; border-radius: 8px !important; background: var(--navycard) !important; }
details summary { font-size: 0.8rem !important; font-family: 'Plus Jakarta Sans', sans-serif !important; }
hr { border-color: var(--border) !important; }
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
    plan_id: str; supplier_name: str; supplier_email: str; email_subject: str
    total_order_value: float; delivery_date: str; handled_at: str
    line_items: list; reason: str

@dataclass
class ActivityEntry:
    timestamp: str; who: str; what: str; detail: str; plan_id: str; color: str = "#6B8FA8"


# ── Seed data ─────────────────────────────────────────────────────────────────

def init_state():
    if "orders"      not in st.session_state: st.session_state.orders      = _seed_orders()
    if "auto_orders" not in st.session_state: st.session_state.auto_orders = _seed_auto()
    if "activity"    not in st.session_state: st.session_state.activity    = _seed_activity()
    if "toast"       not in st.session_state: st.session_state.toast       = None

def _seed_orders():
    return [
        PendingOrder(
            plan_id="ORD-2025-003", supplier_name="Sunrise Textiles Pvt. Ltd.",
            supplier_email="ramesh@sunrise-textiles.in",
            email_subject="Restocking Confirmation – June Batch",
            total_order_value=247500.0, delivery_date="15 Jul 2025",
            submitted_at="Today, 9:14 AM",
            flagged_reason="Order total ₹2,47,500 is above your ₹50,000 auto-approve limit. Your sign-off is needed before we place it.",
            line_items=[
                LineItem("SKU-TSH-001","Cotton T-Shirt (White, L)",300,180.0,54000.0),
                LineItem("SKU-JNS-042","Denim Jeans (32W)",150,650.0,97500.0),
                LineItem("SKU-SNK-007","Sports Sneakers (Size 9)",80,1200.0,96000.0),
            ],
            policy_checks=[
                PolicyCheck("Supplier recognised",       True,  "Sunrise Textiles is on your approved supplier list."),
                PolicyCheck("All products found",        True,  "All 3 SKUs exist in your Azure SQL inventory."),
                PolicyCheck("All items need restocking", True,  "T-Shirts, Jeans & Sneakers are all below threshold."),
                PolicyCheck("Prices look normal",        True,  "Supplier prices are within your usual range."),
                PolicyCheck("Order value",               False, "₹2,47,500 exceeds the ₹50,000 auto-approve limit."),
            ],
        ),
        PendingOrder(
            plan_id="ORD-2025-004", supplier_name="Metro Fabrics Co.",
            supplier_email="orders@metrofabrics.com",
            email_subject="Urgent Restock – Cap & Bag",
            total_order_value=68000.0, delivery_date="28 Jun 2025",
            submitted_at="Today, 11:02 AM",
            flagged_reason="The supplier email had some unclear sections. Please verify the quantities before we proceed.",
            line_items=[
                LineItem("SKU-CAP-003","Snapback Cap (Assorted)",400,95.0,38000.0),
                LineItem("SKU-BAG-011","Canvas Tote Bag",130,230.0,29900.0),
            ],
            policy_checks=[
                PolicyCheck("Supplier recognised",       True,  "Metro Fabrics Co. is on your approved list."),
                PolicyCheck("All products found",        True,  "Both SKUs exist in your inventory."),
                PolicyCheck("All items need restocking", True,  "Caps and Tote Bags are running low."),
                PolicyCheck("Prices look normal",        True,  "Prices are within normal range."),
                PolicyCheck("Email clarity",             False, "Email had unclear sections — please review quantities."),
                PolicyCheck("Order value",               False, "₹68,000 exceeds the ₹50,000 auto-approve limit."),
            ],
        ),
    ]

def _seed_auto():
    return [
        AutoOrder(
            plan_id="ORD-2025-001", supplier_name="QuickStitch Supplies",
            supplier_email="supply@quickstitch.in",
            email_subject="Weekly Restock – Accessories",
            total_order_value=11500.0, delivery_date="22 Jun 2025",
            handled_at="Today, 8:30 AM",
            reason="Under ₹50,000, supplier verified, stock was low, prices normal. Placed automatically.",
            line_items=[LineItem("SKU-BAG-011","Canvas Tote Bag",50,230.0,11500.0)],
        ),
        AutoOrder(
            plan_id="ORD-2025-002", supplier_name="ThreadWorks India",
            supplier_email="orders@threadworks.in",
            email_subject="Low Stock Replenishment – June",
            total_order_value=19500.0, delivery_date="24 Jun 2025",
            handled_at="Today, 10:15 AM",
            reason="Under ₹50,000, all checks passed. Order placed without interrupting you.",
            line_items=[LineItem("SKU-JNS-042","Denim Jeans (32W)",30,650.0,19500.0)],
        ),
        AutoOrder(
            plan_id="ORD-2025-005", supplier_name="Fabric First Co.",
            supplier_email="restock@fabricfirst.com",
            email_subject="T-Shirt Restock Request",
            total_order_value=9600.0, delivery_date="21 Jun 2025",
            handled_at="Today, 7:45 AM",
            reason="Small order, fully verified. Handled automatically — no action needed.",
            line_items=[LineItem("SKU-SNK-007","Sports Sneakers (Size 8)",8,1200.0,9600.0)],
        ),
    ]

def _seed_activity():
    return [
        ActivityEntry("7:45 AM","AI Pipeline","Email processed","Fabric First Co. — 1 item extracted (SKU-SNK-007).","ORD-2025-005","#00D4E0"),
        ActivityEntry("7:45 AM","AI Pipeline","Order placed automatically","₹9,600 order placed. Stock will update on delivery.","ORD-2025-005","#00D68F"),
        ActivityEntry("8:30 AM","AI Pipeline","Email processed","QuickStitch Supplies — 1 item extracted (SKU-BAG-011).","ORD-2025-001","#00D4E0"),
        ActivityEntry("8:30 AM","AI Pipeline","Order placed automatically","₹11,500 order placed with QuickStitch. No action needed.","ORD-2025-001","#00D68F"),
        ActivityEntry("9:14 AM","AI Pipeline","Email processed","Sunrise Textiles — 3 items extracted. Value ₹2,47,500.","ORD-2025-003","#00D4E0"),
        ActivityEntry("9:14 AM","AI Pipeline","Sent for your review","₹2,47,500 exceeds ₹50,000 limit. Awaiting your approval.","ORD-2025-003","#F5A623"),
        ActivityEntry("10:15 AM","AI Pipeline","Email processed","ThreadWorks India — 1 item extracted (SKU-JNS-042).","ORD-2025-002","#00D4E0"),
        ActivityEntry("10:15 AM","AI Pipeline","Order placed automatically","₹19,500 order placed. No action needed from you.","ORD-2025-002","#00D68F"),
        ActivityEntry("11:02 AM","AI Pipeline","Email processed","Metro Fabrics — 2 items, email unclear in places.","ORD-2025-004","#00D4E0"),
        ActivityEntry("11:02 AM","AI Pipeline","Sent for your review","Unclear email + above limit. Awaiting your approval.","ORD-2025-004","#F5A623"),
    ]

def _now():
    try:    return datetime.now().strftime("%-I:%M %p")
    except: return datetime.now().strftime("%H:%M")

def add_activity(plan_id, who, what, detail, color):
    st.session_state.activity.append(ActivityEntry(_now(), who, what, detail, plan_id, color))

def fmt_inr(v):
    return f"₹{v/100000:.2f}L" if v >= 100000 else f"₹{v:,.0f}"

def stock_label(sku_id):
    d = {"SKU-TSH-001":("🟡","Low"),"SKU-JNS-042":("🟡","Low"),
         "SKU-SNK-007":("🔴","Out of stock"),"SKU-CAP-003":("🟢","OK"),"SKU-BAG-011":("🟡","Low")}
    return d.get(sku_id, ("⚪","Unknown"))


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        # Brand
        st.markdown("""
        <div class="sb-brand">
            <div class="sb-logo">BusinessFlow<span>AI</span></div>
            <div class="sb-team">⚡ NEURONEKOS · IIT MADRAS</div>
            <div class="sb-tagline">Approval Dashboard — Manager View</div>
        </div>
        """, unsafe_allow_html=True)

        orders   = st.session_state.orders
        auto     = st.session_state.auto_orders
        pending  = [o for o in orders if o.status == "PENDING"]
        approved = [o for o in orders if o.status == "APPROVED"]

        st.markdown('<div class="sec-hdr" style="margin-top:0.8rem">Navigation</div>', unsafe_allow_html=True)
        page = st.radio("", [
            "🏠  Overview",
            "🔔  Needs Approval",
            "🤖  Auto-Handled",
            "✅  Approved",
            "❌  Declined",
            "📋  Activity Log",
        ], label_visibility="collapsed")

        st.markdown('<div class="sec-hdr">Today</div>', unsafe_allow_html=True)
        auto_v  = sum(o.total_order_value for o in auto)
        wait_v  = sum(o.total_order_value for o in pending)

        st.markdown(f"""
        <div style="display:flex;flex-direction:column;gap:0.45rem">
            <div style="background:#0D1A28;border:1px solid #142030;border-radius:8px;padding:0.7rem 0.9rem;border-left:3px solid #F5A623">
                <div style="font-size:0.65rem;color:#6B8FA8;font-family:'JetBrains Mono',monospace">AWAITING REVIEW</div>
                <div style="font-size:1.3rem;font-weight:800;color:#F5A623;font-family:'Plus Jakarta Sans',sans-serif;line-height:1">{len(pending)}</div>
                <div style="font-size:0.67rem;color:#6B8FA8">{fmt_inr(wait_v)} pending</div>
            </div>
            <div style="background:#0D1A28;border:1px solid #142030;border-radius:8px;padding:0.7rem 0.9rem;border-left:3px solid #00D68F">
                <div style="font-size:0.65rem;color:#6B8FA8;font-family:'JetBrains Mono',monospace">AUTO-HANDLED</div>
                <div style="font-size:1.3rem;font-weight:800;color:#00D68F;font-family:'Plus Jakarta Sans',sans-serif;line-height:1">{len(auto)}</div>
                <div style="font-size:0.67rem;color:#6B8FA8">{fmt_inr(auto_v)} placed</div>
            </div>
            <div style="background:#0D1A28;border:1px solid #142030;border-radius:8px;padding:0.7rem 0.9rem;border-left:3px solid #00D4E0">
                <div style="font-size:0.65rem;color:#6B8FA8;font-family:'JetBrains Mono',monospace">YOU APPROVED</div>
                <div style="font-size:1.3rem;font-weight:800;color:#00D4E0;font-family:'Plus Jakarta Sans',sans-serif;line-height:1">{len(approved)}</div>
                <div style="font-size:0.67rem;color:#6B8FA8">orders today</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sec-hdr">Pipeline</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:0.73rem;color:#6B8FA8;line-height:2;font-family:'JetBrains Mono',monospace">
            📧 Email received<br>
            🧠 Planner extracts SKU<br>
            📦 Retriever checks stock<br>
            🛡️ Policy evaluates cost<br>
            ⚡ Executor places order<br>
            🗄️ Azure SQL updated<br>
            📊 Dashboard updated
        </div>
        <div style='padding-bottom: 120px'></div>
        """, unsafe_allow_html=True)

        return page


# ── Brand header bar ──────────────────────────────────────────────────────────

def render_header(subtitle=""):
    col_menu, col_brand = st.columns([0.06, 0.94])
    with col_menu:
        st.markdown("<div style='padding-top:0.3rem'>", unsafe_allow_html=True)
        if st.button("☰", key="menu_toggle", help="Open / close navigation"):
            # Toggle sidebar state
            if "sidebar_open" not in st.session_state:
                st.session_state.sidebar_open = True
            else:
                st.session_state.sidebar_open = not st.session_state.sidebar_open
        st.markdown("</div>", unsafe_allow_html=True)
    with col_brand:
        sub_html = f"<div style='font-size:0.78rem;color:#6B8FA8;margin-left:0.5rem'>/ {subtitle}</div>" if subtitle else ""
        st.markdown(f"""
        <div class="brand-bar" style="position:static;border-radius:10px;margin-bottom:0.2rem">
            <div class="brand-left">
                <div class="brand-logo">BusinessFlow<span>AI</span></div>
                <div class="brand-team">NEURONEKOS · IIT MADRAS</div>
                {sub_html}
            </div>
            <div class="brand-right">
                <span class="live-dot"></span> Pipeline Active · Microsoft AI Unlocked
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── Pipeline strip ────────────────────────────────────────────────────────────

def render_pipeline():
    st.markdown("""
    <div class="pipeline-strip">
        <div class="pip-step done"><span class="pip-icon">📧</span>Email In</div>
        <div class="pip-step done"><span class="pip-icon">🧠</span>Planner</div>
        <div class="pip-step done"><span class="pip-icon">📦</span>Retriever</div>
        <div class="pip-step done"><span class="pip-icon">🛡️</span>Policy</div>
        <div class="pip-step active"><span class="pip-icon">⚡</span>Executor</div>
        <div class="pip-step active"><span class="pip-icon">🗄️</span>Azure SQL</div>
        <div class="pip-step active"><span class="pip-icon">📊</span>Dashboard</div>
    </div>
    """, unsafe_allow_html=True)


# ── Order card ────────────────────────────────────────────────────────────────

def render_order_card(order, show_actions=True):
    stripe = {"PENDING":"#F5A623","APPROVED":"#00D68F","REJECTED":"#FF4D6A"}.get(order.status,"#00D4E0")
    bcls   = {"PENDING":"badge-pending","APPROVED":"badge-approved","REJECTED":"badge-rejected"}.get(order.status,"")
    blbl   = {"PENDING":"⚠ Awaiting Approval","APPROVED":"✓ Approved","REJECTED":"✕ Declined"}.get(order.status,order.status)

    st.markdown(f"""
    <div class="ord-card" style="--stripe:{stripe}">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.7rem">
            <div>
                <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:1.05rem;font-weight:700;color:#fff">{order.supplier_name}</div>
                <div style="font-size:0.77rem;color:#6B8FA8;margin-top:0.1rem">{order.email_subject}</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:0.62rem;color:#6B8FA8;margin-top:0.2rem">{order.plan_id} · {order.submitted_at}</div>
                <div style="margin-top:0.45rem"><span class="badge {bcls}">{blbl}</span></div>
            </div>
            <div style="text-align:right">
                <div style="font-size:0.65rem;color:#6B8FA8;text-transform:uppercase;letter-spacing:0.08em;font-family:'JetBrains Mono',monospace">Order Total</div>
                <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:1.5rem;font-weight:800;color:#F5A623;letter-spacing:-0.02em">{fmt_inr(order.total_order_value)}</div>
                <div style="font-size:0.72rem;color:#6B8FA8">Delivery {order.delivery_date}</div>
            </div>
        </div>
        <div class="flag-box"><strong>Why this needs your attention:</strong> {order.flagged_reason}</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(f"📦  Order details — {len(order.line_items)} products · {fmt_inr(order.total_order_value)}"):
        st.markdown('<div style="font-size:0.78rem;font-weight:600;color:#6B8FA8;margin-bottom:0.45rem">Products being ordered</div>', unsafe_allow_html=True)
        for item in order.line_items:
            icon, lbl = stock_label(item.sku_id)
            st.markdown(f"""
            <div class="item-row">
                <div><span class="item-name">{item.product_name}</span>
                <span class="item-meta">{icon} {lbl} · {item.sku_id}</span></div>
                <div style="text-align:right;display:flex;align-items:center;gap:0.8rem">
                <span style="font-size:0.75rem;color:#6B8FA8">{item.quantity} × ₹{item.unit_price:,.0f}</span>
                <span class="item-price" style="color:#F5A623">{fmt_inr(item.total_cost)}</span></div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.78rem;font-weight:600;color:#6B8FA8;margin-bottom:0.4rem">What our AI already verified</div>', unsafe_allow_html=True)
        for chk in order.policy_checks:
            icon = "✓" if chk.passed else "⚠"
            cls  = "chk-ok" if chk.passed else "chk-warn"
            col  = "#6B8FA8" if chk.passed else "#DCE9F0"
            st.markdown(f"""<div class="chk-row">
                <span class="{cls}">{icon}</span>
                <div><span style="font-weight:600;color:{col}">{chk.label}</span>
                <span style="color:#6B8FA8"> — {chk.note}</span></div>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""<div class="info-box" style="margin-top:0.8rem">
            📧 Supplier contact: <span style="color:#00D4E0">{order.supplier_email}</span>
        </div>""", unsafe_allow_html=True)

    if show_actions and order.status == "PENDING":
        st.markdown("<div style='margin-top:0.7rem'></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1.4, 0.9, 3])
        with c1:
            st.markdown('<div class="btn-approve">', unsafe_allow_html=True)
            if st.button("✓  Approve & Place", key=f"app_{order.plan_id}"):
                _approve(order); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="btn-decline">', unsafe_allow_html=True)
            if st.button("✕  Decline", key=f"dec_{order.plan_id}"):
                _decline(order); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    if order.status == "APPROVED" and order.execution_result:
        r = order.execution_result
        st.markdown(f"""<div class="success-box" style="margin-top:0.6rem">
            <span style="color:#00D68F;font-weight:700">✓ Order placed</span>
            <span style="color:#6B8FA8"> — {r['orders_created']} POs created · {fmt_inr(r['total_value'])} committed ·
            Supplier notified · Approved by {order.reviewed_by} at {order.reviewed_at}</span>
        </div>""", unsafe_allow_html=True)

    if order.status == "REJECTED":
        st.markdown(f"""<div style="background:rgba(255,77,106,0.05);border:1px solid rgba(255,77,106,0.18);
            border-left:3px solid #FF4D6A;border-radius:6px;padding:0.65rem 0.9rem;margin-top:0.6rem;font-size:0.8rem">
            <span style="color:#FF4D6A;font-weight:700">✕ Declined</span>
            <span style="color:#6B8FA8"> — No stock changes made. Declined by {order.reviewed_by} at {order.reviewed_at}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:0.3rem'></div>", unsafe_allow_html=True)


# ── Auto-order card ───────────────────────────────────────────────────────────

def render_auto_card(order: AutoOrder):
    st.markdown(f"""
    <div class="auto-card">
        <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div>
                <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:0.98rem;font-weight:700;color:#fff">{order.supplier_name}</div>
                <div style="font-size:0.75rem;color:#6B8FA8;margin-top:0.08rem">{order.email_subject}</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:0.6rem;color:#6B8FA8;margin-top:0.15rem">{order.plan_id} · {order.handled_at}</div>
                <div style="margin-top:0.35rem"><span class="badge badge-auto">🤖 Auto-handled</span></div>
            </div>
            <div style="text-align:right">
                <div style="font-size:0.65rem;color:#6B8FA8;font-family:'JetBrains Mono',monospace;text-transform:uppercase;letter-spacing:0.06em">Placed</div>
                <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:1.3rem;font-weight:800;color:#00D4E0;letter-spacing:-0.02em">{fmt_inr(order.total_order_value)}</div>
                <div style="font-size:0.7rem;color:#6B8FA8">Delivery {order.delivery_date}</div>
            </div>
        </div>
        <div class="info-box" style="margin-top:0.6rem">✓ {order.reason}</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(f"📦  Details — {len(order.line_items)} product{'s' if len(order.line_items)>1 else ''}"):
        for item in order.line_items:
            icon, lbl = stock_label(item.sku_id)
            st.markdown(f"""<div class="item-row">
                <div><span class="item-name">{item.product_name}</span>
                <span class="item-meta">{icon} Was {lbl} · {item.sku_id}</span></div>
                <div style="display:flex;align-items:center;gap:0.8rem">
                <span style="font-size:0.75rem;color:#6B8FA8">{item.quantity} × ₹{item.unit_price:,.0f}</span>
                <span class="item-price" style="color:#00D4E0">{fmt_inr(item.total_cost)}</span></div>
            </div>""", unsafe_allow_html=True)
        st.markdown(f"""<div class="info-box" style="margin-top:0.7rem">
            📧 <span style="color:#00D4E0">{order.supplier_email}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:0.2rem'></div>", unsafe_allow_html=True)


# ── Actions ───────────────────────────────────────────────────────────────────

def _approve(order):
    now = _now()
    order.status, order.reviewed_at, order.reviewed_by = "APPROVED", now, "Operations Manager"
    total = sum(i.total_cost for i in order.line_items)
    order.execution_result = {"orders_created": len(order.line_items), "total_value": total}
    add_activity(order.plan_id,"You","Approved order",f"{order.supplier_name} — {fmt_inr(total)} committed.","#00D68F")
    add_activity(order.plan_id,"AI Pipeline","POs created & sent",f"{len(order.line_items)} purchase orders written to Azure SQL. Supplier notified.","#00D4E0")
    st.session_state.toast = ("approve", order.supplier_name, total)

def _decline(order):
    now = _now()
    order.status, order.reviewed_at, order.reviewed_by = "REJECTED", now, "Operations Manager"
    add_activity(order.plan_id,"You","Declined order",f"{order.supplier_name} — no stock changes made.","#FF4D6A")
    st.session_state.toast = ("decline", order.supplier_name, order.total_order_value)


# ── Pages ─────────────────────────────────────────────────────────────────────

def page_overview():
    render_header("Overview")
    st.markdown('<div class="main-wrap">', unsafe_allow_html=True)

    orders  = st.session_state.orders
    auto    = st.session_state.auto_orders
    pending = [o for o in orders if o.status == "PENDING"]
    approved= [o for o in orders if o.status == "APPROVED"]
    total_auto_v = sum(o.total_order_value for o in auto)
    total_pend_v = sum(o.total_order_value for o in pending)

    st.markdown("""
    <div style="margin-bottom:1rem">
        <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:1.6rem;font-weight:800;color:#fff;letter-spacing:-0.02em">
            Good morning 👋
        </div>
        <div style="font-size:0.88rem;color:#6B8FA8;margin-top:0.15rem">
            Here's what BusinessFlow AI handled for you today.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.toast:
        kind, name, val = st.session_state.toast
        if kind == "approve":
            st.markdown(f'<div class="toast">✓ Order from <strong>{name}</strong> approved — {fmt_inr(val)} committed to Azure SQL.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="toast toast-decline">✕ Order from <strong>{name}</strong> declined. No changes made.</div>', unsafe_allow_html=True)
        st.session_state.toast = None

    render_pipeline()

    # Stats row
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"""<div class="stat-card" style="--accent:#F5A623">
        <div class="stat-label">🔔 Awaiting review</div>
        <div class="stat-val">{len(pending)}</div>
        <div class="stat-sub">{fmt_inr(total_pend_v)} pending</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="stat-card" style="--accent:#00D68F">
        <div class="stat-label">🤖 AI auto-handled</div>
        <div class="stat-val">{len(auto)}</div>
        <div class="stat-sub">{fmt_inr(total_auto_v)} placed</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="stat-card" style="--accent:#00D4E0">
        <div class="stat-label">✅ You approved</div>
        <div class="stat-val">{len(approved)}</div>
        <div class="stat-sub">orders today</div></div>""", unsafe_allow_html=True)
    with c4:
        saved = len(auto) * 25
        st.markdown(f"""<div class="stat-card" style="--accent:#6B8FA8">
        <div class="stat-label">⏱ Time saved</div>
        <div class="stat-val">~{saved}m</div>
        <div class="stat-sub">of manual processing</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.6rem'></div>", unsafe_allow_html=True)

    # Two column split
    col_l, col_r = st.columns([1.05, 1], gap="large")

    with col_l:
        st.markdown(f"""<div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.8rem">
            <div style="width:8px;height:8px;border-radius:50%;background:#F5A623;box-shadow:0 0 8px #F5A623"></div>
            <span style="font-family:'Plus Jakarta Sans',sans-serif;font-size:0.95rem;font-weight:700;color:#fff">Needs Your Approval</span>
            <span class="badge badge-pending">{len(pending)}</span>
        </div>""", unsafe_allow_html=True)

        if not pending:
            st.markdown("""<div class="empty"><div class="empty-icon">🎉</div>
                <div class="empty-title">All caught up!</div>
                <div style="font-size:0.8rem">No orders need your attention.</div></div>""", unsafe_allow_html=True)
        else:
            for o in pending: render_order_card(o, show_actions=True)

    with col_r:
        st.markdown(f"""<div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.8rem">
            <span style="font-size:0.95rem">🤖</span>
            <span style="font-family:'Plus Jakarta Sans',sans-serif;font-size:0.95rem;font-weight:700;color:#fff">AI Handled Automatically</span>
            <span class="badge badge-auto">{len(auto)}</span>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""<div class="info-box" style="margin-bottom:0.8rem">
            💡 These were placed automatically — under ₹50,000, verified, prices normal.
            <span style="color:#00D68F"> You saved ~{len(auto)*25} mins today.</span>
        </div>""", unsafe_allow_html=True)

        for o in auto: render_auto_card(o)

    st.markdown('</div>', unsafe_allow_html=True)


def page_needs_approval():
    render_header("Needs Approval")
    st.markdown('<div class="main-wrap">', unsafe_allow_html=True)
    orders  = [o for o in st.session_state.orders if o.status == "PENDING"]
    total_v = sum(o.total_order_value for o in orders)

    st.markdown(f"""<div style="margin-bottom:1rem">
        <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:1.5rem;font-weight:800;color:#fff;letter-spacing:-0.02em">Needs Your Approval</div>
        <div style="font-size:0.85rem;color:#6B8FA8;margin-top:0.1rem">Orders flagged by the Policy Layer — review and decide.</div>
    </div>""", unsafe_allow_html=True)

    if st.session_state.toast:
        kind, name, val = st.session_state.toast
        if kind == "approve": st.markdown(f'<div class="toast">✓ <strong>{name}</strong> approved — {fmt_inr(val)} committed.</div>', unsafe_allow_html=True)
        else: st.markdown(f'<div class="toast toast-decline">✕ <strong>{name}</strong> declined. No changes made.</div>', unsafe_allow_html=True)
        st.session_state.toast = None

    if not orders:
        st.markdown("""<div class="empty"><div class="empty-icon">🎉</div>
            <div class="empty-title">All caught up!</div>
            <div style="font-size:0.82rem">No orders need your attention right now.</div></div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True); return

    c1, c2 = st.columns(2)
    with c1: st.markdown(f"""<div class="stat-card" style="--accent:#F5A623">
        <div class="stat-label">Orders waiting</div><div class="stat-val">{len(orders)}</div>
        <div class="stat-sub">need your sign-off</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="stat-card" style="--accent:#FF4D6A">
        <div class="stat-label">Value pending</div><div class="stat-val">{fmt_inr(total_v)}</div>
        <div class="stat-sub">awaiting commitment</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.2rem'></div>", unsafe_allow_html=True)
    for o in orders: render_order_card(o, show_actions=True)
    st.markdown('</div>', unsafe_allow_html=True)


def page_auto():
    render_header("Auto-Handled by AI")
    st.markdown('<div class="main-wrap">', unsafe_allow_html=True)
    auto   = st.session_state.auto_orders
    auto_v = sum(o.total_order_value for o in auto)

    st.markdown("""<div style="margin-bottom:1rem">
        <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:1.5rem;font-weight:800;color:#fff;letter-spacing:-0.02em">Auto-Handled by AI 🤖</div>
        <div style="font-size:0.85rem;color:#6B8FA8;margin-top:0.1rem">Orders BusinessFlow AI placed on your behalf — no action needed.</div>
    </div>""", unsafe_allow_html=True)

    if not auto:
        st.markdown('<div class="empty"><div class="empty-icon">📭</div><div class="empty-title">None yet today</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True); return

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"""<div class="stat-card" style="--accent:#00D68F">
        <div class="stat-label">Orders handled</div><div class="stat-val">{len(auto)}</div>
        <div class="stat-sub">without interrupting you</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="stat-card" style="--accent:#00D4E0">
        <div class="stat-label">Total placed</div><div class="stat-val">{fmt_inr(auto_v)}</div>
        <div class="stat-sub">written to Azure SQL</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="stat-card" style="--accent:#6B8FA8">
        <div class="stat-label">Time saved</div><div class="stat-val">~{len(auto)*25}m</div>
        <div class="stat-sub">of manual processing</div></div>""", unsafe_allow_html=True)

    st.markdown(f"""<div class="info-box" style="margin:1rem 0 1.2rem 0">
        <strong style="color:#00D4E0">Auto-approval rules:</strong> Order under ₹50,000 · Supplier on approved list ·
        Stock below threshold · Prices within normal range. Anything outside → sent to you.
    </div>""", unsafe_allow_html=True)

    for o in auto: render_auto_card(o)
    st.markdown('</div>', unsafe_allow_html=True)


def page_approved():
    render_header("Approved Orders")
    st.markdown('<div class="main-wrap">', unsafe_allow_html=True)
    orders = [o for o in st.session_state.orders if o.status == "APPROVED"]

    st.markdown("""<div style="margin-bottom:1rem">
        <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:1.5rem;font-weight:800;color:#fff;letter-spacing:-0.02em">Approved by You ✅</div>
        <div style="font-size:0.85rem;color:#6B8FA8;margin-top:0.1rem">Stock will update in Azure SQL when orders arrive.</div>
    </div>""", unsafe_allow_html=True)

    if not orders:
        st.markdown('<div class="empty"><div class="empty-icon">📭</div><div class="empty-title">No approved orders yet</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True); return

    total = sum(o.total_order_value for o in orders)
    c1, c2 = st.columns(2)
    with c1: st.markdown(f"""<div class="stat-card" style="--accent:#00D68F">
        <div class="stat-label">Approved</div><div class="stat-val">{len(orders)}</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="stat-card" style="--accent:#00D68F">
        <div class="stat-label">Total committed</div><div class="stat-val">{fmt_inr(total)}</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
    for o in orders: render_order_card(o, show_actions=False)
    st.markdown('</div>', unsafe_allow_html=True)


def page_declined():
    render_header("Declined Orders")
    st.markdown('<div class="main-wrap">', unsafe_allow_html=True)
    orders = [o for o in st.session_state.orders if o.status == "REJECTED"]

    st.markdown("""<div style="margin-bottom:1rem">
        <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:1.5rem;font-weight:800;color:#fff;letter-spacing:-0.02em">Declined Orders ❌</div>
        <div style="font-size:0.85rem;color:#6B8FA8;margin-top:0.1rem">No stock changes were made for these orders.</div>
    </div>""", unsafe_allow_html=True)

    if not orders:
        st.markdown('<div class="empty"><div class="empty-icon">📭</div><div class="empty-title">No declined orders</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True); return

    for o in orders: render_order_card(o, show_actions=False)
    st.markdown('</div>', unsafe_allow_html=True)


def page_activity():
    render_header("Activity Log")
    st.markdown('<div class="main-wrap">', unsafe_allow_html=True)

    st.markdown("""<div style="margin-bottom:1rem">
        <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:1.5rem;font-weight:800;color:#fff;letter-spacing:-0.02em">Activity Log 📋</div>
        <div style="font-size:0.85rem;color:#6B8FA8;margin-top:0.1rem">Full audit trail — every AI action and every decision you made.</div>
    </div>""", unsafe_allow_html=True)

    activity = list(reversed(st.session_state.activity))
    orders   = st.session_state.orders
    auto     = st.session_state.auto_orders
    all_map  = {**{o.plan_id: o.supplier_name for o in orders}, **{o.plan_id: o.supplier_name for o in auto}}
    all_ids  = list(dict.fromkeys(e.plan_id for e in st.session_state.activity))
    options  = ["All suppliers"] + [f"{all_map.get(p,p)} ({p})" for p in all_ids if p in all_map]

    selected = st.selectbox("Filter", options, label_visibility="collapsed")
    if selected != "All suppliers":
        pid = next((p for p in all_ids if f"({p})" in selected), None)
        if pid: activity = [a for a in activity if a.plan_id == pid]

    st.markdown(f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.65rem;color:#6B8FA8;margin:0.5rem 0 0.4rem 0">{len(activity)} EVENTS</div>', unsafe_allow_html=True)

    icons = {"AI Pipeline":"🤖","You":"👤"}
    for e in activity:
        st.markdown(f"""<div class="act-row">
            <span class="act-time">{e.timestamp}</span>
            <span class="act-who" style="color:{e.color}">{icons.get(e.who,"📌")} {e.who}</span>
            <span class="act-what" style="color:{e.color}">{e.what}</span>
            <span class="act-detail">{e.detail}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    init_state()
    page = render_sidebar()
    if   "Overview"  in page: page_overview()
    elif "Approval"  in page: page_needs_approval()
    elif "Auto"      in page: page_auto()
    elif "Approved"  in page: page_approved()
    elif "Declined"  in page: page_declined()
    elif "Activity"  in page: page_activity()

if __name__ == "__main__":
    main()