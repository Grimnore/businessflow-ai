# BusinessFlow AI 🤖
### A Multi-Agent System for Controlled Automation of Inventory Restocking
**Team NeuroNekos | IIT Madras | Microsoft AI Unlocked — Track 4: Agent Teamwork**

---

## Architecture

```
Supplier Email
     │
     ▼
Azure Function Trigger (HTTP / Event Grid)
     │
     ▼
┌─────────────────────────────────────────┐
│          Agent Orchestrator              │
│     (Semantic Kernel / AutoGen)          │
└────┬──────────────┬──────────────┬───────┘
     │              │              │
     ▼              ▼              ▼
┌─────────┐  ┌──────────┐  ┌─────────────┐
│ Planner │  │Retriever │  │Policy Layer │
│  Agent  │  │  Agent   │  │ (Governance)│
└────┬────┘  └────┬─────┘  └──────┬──────┘
     │             │               │
     └─────────────┴───────────────┘
                   │
                   ▼
            ┌─────────────┐
            │  Executor   │
            │   Agent     │
            └──────┬──────┘
                   │
                   ▼
          Azure SQL Database
          + Approval Dashboard
```

---

## Project Structure

```
businessflow-ai/
├── planner_agent/
│   ├── __init__.py
│   └── planner.py          ← Planner Agent (Azure OpenAI, Pydantic)
├── tests/
│   └── test_planner.py     ← Full test suite (offline, mocked)
├── function_app.py         ← Azure Functions HTTP trigger
├── demo.py                 ← Quick local demo script
├── requirements.txt
├── .env.example            ← Copy to .env and fill in credentials
└── README.md
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure credentials
```bash
cp .env.example .env
# Edit .env with your Azure OpenAI endpoint, API key, and deployment name
```

### 3. Run the demo
```bash
python demo.py
```

### 4. Run tests (no Azure credentials needed)
```bash
pytest tests/ -v
```

### 5. Run the Azure Function locally
```bash
func start
# Then POST to http://localhost:7071/api/planner
```

---

## Planner Agent — What it does

The Planner Agent is the **first step** in the BusinessFlow AI pipeline.

Given a raw supplier email, it:
1. Calls **Azure OpenAI** (GPT-4o) with a structured function-calling prompt
2. Extracts: supplier info, SKU IDs, quantities, unit prices, delivery dates
3. Returns a validated **`ExecutionPlan`** Pydantic model
4. Attaches a **confidence score** so the Policy Layer can flag ambiguous emails

### Example Input
```
Hi, we can supply:
- SKU-TSH-001: 300 units @ ₹180/unit
- SKU-JNS-042: 150 units @ ₹650/unit
Delivery: 15 July 2025
```

### Example Output
```json
{
  "plan_id": "a1b2c3d4",
  "supplier_name": "Sunrise Textiles Pvt. Ltd.",
  "supplier_email": "ramesh@sunrise-textiles.in",
  "line_items": [
    { "sku_id": "SKU-TSH-001", "quantity": 300, "unit_price": 180.0, "total_cost": 54000.0 },
    { "sku_id": "SKU-JNS-042", "quantity": 150, "unit_price": 650.0, "total_cost": 97500.0 }
  ],
  "total_order_value": 151500.0,
  "confidence_score": 0.97,
  "delivery_date": "2025-07-15"
}
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI / LLM | Azure OpenAI (GPT-4o) |
| Orchestration | Microsoft Semantic Kernel |
| Trigger | Azure Functions |
| Database | Azure SQL |
| Deployment | Azure Container Apps |
| Email Integration | Microsoft Graph API |
| Auth | Azure Active Directory (RBAC) |

---

## Next Steps (Build Order)

- [x] **Planner Agent** — Email parsing & ExecutionPlan generation
- [ ] **Retriever Agent** — Azure SQL stock/threshold lookup
- [ ] **Policy Layer** — Governance rules engine (₹50k threshold)
- [ ] **Executor Agent** — DB updates, PO creation, audit logging
- [ ] **Approval Dashboard** — Web UI for flagged orders
- [ ] **Graph API Integration** — Live email monitoring
