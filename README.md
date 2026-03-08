# ⚡ BusinessFlow AI

**Autonomous Inventory Restocking via Multi-Agent Pipeline**
---

## What It Does

BusinessFlow AI reads supplier emails, checks live inventory, evaluates order policy, and places purchase orders automatically — flagging only the orders that genuinely need a human decision.

A ₹10,000 restock from a verified supplier? Handled in under 60 seconds, no interruption.  
A ₹2,50,000 order from a new supplier? Flagged to the manager with full context and one-click approval.

---

## Architecture

```
Supplier Email
      ↓
Azure Function Trigger
      ↓
Agent Orchestrator (Semantic Kernel)
      ↓
┌─────────────────────────────────────┐
│  Planner Agent  │  Retriever Agent  │
│  Extract SKU    │  Fetch Inventory  │
│  + Quantity     │  from Azure SQL   │
└─────────────────────────────────────┘
      ↓
Policy Layer
  ├── Stock below threshold?
  ├── Order cost acceptable?
  └── Stock sufficient → STOP
      ↓
Executor Agent
  Create Purchase Order + Update Inventory
      ↓
Azure SQL Database
      ↓
Approval Dashboard (Streamlit)
```

---

## Policy Logic

```python
def evaluate(stock, threshold, quantity, unit_cost):
    if stock >= threshold:
        return "NO_ORDER_NEEDED"
    total_cost = quantity * unit_cost
    if total_cost < 50000:
        return "AUTO_APPROVE"
    return "REQUIRES_APPROVAL"
```

---

## Components

| Component | File | Tests |
|---|---|---|
| Planner Agent | `planner_agent/planner.py` | 12/12 ✅ |
| Retriever Agent | `retriever_agent/retriever.py` | 25/25 ✅ |
| Policy Layer | `policy_layer/policy.py` | 22/22 ✅ |
| Executor Agent | `executor_agent/executor.py` | 20/20 ✅ |
| Approval Dashboard | `dashboard.py` | — |

**Total: 79/79 tests passing**

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI & Reasoning | Azure OpenAI (GPT-4o) |
| Agent Orchestration | Microsoft Semantic Kernel |
| Email Trigger | Azure Functions |
| Database | Azure SQL |
| Approval Dashboard | Streamlit |
| Auth & Governance | Azure Active Directory |

---

## Project Structure

```
businessflow-ai/
├── planner_agent/
│   ├── __init__.py
│   └── planner.py          # Extracts SKU + quantity from supplier emails
├── retriever_agent/
│   ├── __init__.py
│   ├── retriever.py        # Fetches live inventory from Azure SQL
│   └── schema.sql
├── policy_layer/
│   ├── __init__.py
│   └── policy.py           # Governance: stock check + cost check
├── executor_agent/
│   ├── __init__.py
│   └── executor.py         # Creates POs, updates inventory
├── tests/
│   ├── test_planner.py
│   ├── test_retriever.py
│   ├── test_policy.py
│   └── test_executor.py
├── function_app.py         # Azure Function HTTP trigger
├── demo.py                 # 3-stage pipeline demo
├── demo_full.py            # Full 4-stage pipeline demo
├── dashboard.py            # Streamlit approval dashboard
├── requirements.txt
└── .env.example
```

---

## Quick Start

```bash
git clone https://github.com/Grimnore/businessflow-ai.git
cd businessflow-ai

# Python 3.12 required
py -3.12 -m pip install -r requirements.txt

cp .env.example .env

# Run full pipeline demo (mock mode — no Azure credentials needed)
py -3.12 demo_full.py

# Run all tests
py -3.12 -m pytest tests/ -v

# Launch approval dashboard
streamlit run dashboard.py
```

---

## Environment Variables

```env
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT=gpt-4o

AZURE_SQL_SERVER=
AZURE_SQL_DATABASE=
AZURE_SQL_USERNAME=
AZURE_SQL_PASSWORD=

RETRIEVER_BACKEND=mock
EXECUTOR_BACKEND=mock

POLICY_AUTO_APPROVE_THRESHOLD=50000
POLICY_MIN_CONFIDENCE=0.70
POLICY_MAX_UNIT_PRICE_RATIO=2.0

GRAPH_TENANT_ID=
GRAPH_CLIENT_ID=
GRAPH_CLIENT_SECRET=
GRAPH_MONITORED_MAILBOX=
```

---

## Demo Output (mock mode)

```
[PLANNER]   Extracted 3 line items from supplier email
[RETRIEVER] SKU-BAG-011: stock=8,  threshold=25 → LOW
            SKU-JNS-042: stock=12, threshold=30 → LOW
            SKU-SNK-007: stock=0,  threshold=20 → OUT OF STOCK
[POLICY]    Total cost ₹40,000 → AUTO_APPROVE
[EXECUTOR]  3 purchase orders created
            SKU-BAG-011: 8  → 58 units
            SKU-JNS-042: 12 → 42 units
            SKU-SNK-007: 0  → 8  units
[NOTIFY]    Supplier notified: ramesh@sunrise-textiles.in
```

---

## Approval Dashboard

Live: `https://businessflow-ai.streamlit.app`

---
