# BusinessFlow AI 🤖
### A Multi-Agent System for Controlled Automation of Inventory Restocking
**Team NeuroNekos | IIT Madras | Microsoft AI Unlocked — Track 4: Agent Teamwork**

---

## 🚦 Current Build Status

| Component | Status | Tests |
|---|---|---|
| Planner Agent | ✅ Done | 12/12 passing |
| Retriever Agent | ✅ Done | 25/25 passing |
| Policy Layer | 🔲 In Progress | — |
| Executor Agent | 🔲 Pending | — |
| Approval Dashboard | 🔲 Pending | — |
| Graph API Integration | 🔲 Pending | — |

**Total tests passing: 37/37 ✅**

---

## 🏗️ Architecture

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

## 📁 Project Structure

```
businessflow-ai/
├── planner_agent/
│   ├── __init__.py
│   └── planner.py          ← ✅ Planner Agent (Azure OpenAI, Pydantic v2)
├── retriever_agent/
│   ├── __init__.py
│   ├── retriever.py        ← ✅ Retriever Agent (MockDB + AzureSQL backends)
│   └── schema.sql          ← Azure SQL table definitions + seed data
├── tests/
│   ├── __init__.py
│   ├── test_planner.py     ← ✅ 12 tests (all offline/mocked)
│   └── test_retriever.py   ← ✅ 25 tests (all offline/mocked)
├── function_app.py         ← Azure Functions HTTP trigger
├── demo.py                 ← Pipeline demo (Planner + Retriever)
├── requirements.txt
├── .env.example            ← Copy to .env and fill in credentials
└── README.md
```

---

## ⚡ Quick Start

### 1. Requirements
- Python 3.12 (3.14 not supported yet due to pydantic-core wheel availability)
- Git

### 2. Clone and install
```bash
git clone https://github.com/Grimnore/businessflow-ai.git
cd businessflow-ai
py -3.12 -m pip install -r requirements.txt
```

### 3. Configure credentials (optional for now)
```bash
cp .env.example .env
# Fill in Azure OpenAI credentials only if running real API calls
# Leave blank to use mock mode
```

### 4. Run the pipeline demo (no Azure needed!)
```bash
py -3.12 demo.py
```

Expected output:
```
[STAGE 1] Planner Agent
  Plan ID     : demo-plan-001
  Supplier    : Sunrise Textiles Pvt. Ltd.
  Items       : 3
  Order Value : Rs.247,500.00

[STAGE 2] Retriever Agent
  [YELLOW] [SKU-TSH-001] Cotton T-Shirt — LOW_STOCK (45/50)
  [YELLOW] [SKU-JNS-042] Denim Jeans    — LOW_STOCK (12/30)
  [RED]    [SKU-SNK-007] Sneakers       — OUT_OF_STOCK (0/20)
```

### 5. Run all tests
```bash
py -3.12 -m pytest tests/ -v
# 37 passed ✅
```

---

## ✅ What's Built

### Planner Agent (`planner_agent/planner.py`)
The entry point of the pipeline. Takes a raw supplier email and produces a structured `ExecutionPlan`.

- Calls **Azure OpenAI (GPT-4o)** with function-calling for reliable structured extraction
- Extracts: supplier info, SKU IDs, quantities, unit prices, delivery dates
- Returns a validated **`ExecutionPlan`** Pydantic model with confidence score
- Triggered via **Azure Functions** HTTP endpoint (`function_app.py`)
- Fully testable offline via mocked Azure calls

**Key models:** `LineItem`, `ExecutionPlan`

### Retriever Agent (`retriever_agent/retriever.py`)
Enriches the ExecutionPlan with live inventory context from the database.

- **Two backends:** `MockDB` (zero setup, for dev) and `AzureSQLDB` (production)
- Switch via `RETRIEVER_BACKEND=mock` or `RETRIEVER_BACKEND=azure_sql` env var
- Batch-fetches all SKUs in a single DB call
- Returns a `StockContext` with stock levels, reorder thresholds, unit costs, lead times
- Detects `OUT_OF_STOCK`, `LOW_STOCK`, `ADEQUATE` status per SKU
- Handles missing SKUs gracefully with placeholders

**Key models:** `SKUContext`, `StockContext`

### Azure SQL Schema (`retriever_agent/schema.sql`)
Ready-to-run SQL script for Azure Portal Query Editor. Creates:
- `inventory` table with seed data (5 sample SKUs)
- `purchase_orders` table (used by Executor Agent)
- `audit_log` table (used by Executor Agent)

---

## 🔲 What's Coming Next

### Policy Layer
The governance rules engine. Evaluates the `StockContext` against configurable rules:
- Auto-approve orders under ₹50,000
- Escalate orders at or above ₹50,000 for human approval
- Flag low-confidence plans (< 0.7) for review
- Block orders for missing SKUs

### Executor Agent
Performs validated actions after policy approval:
- Updates inventory stock levels in Azure SQL
- Creates purchase order records
- Writes to audit log
- Sends email notifications via Microsoft Graph API

### Approval Dashboard
Web UI for flagged high-value orders:
- Lists pending approvals with full order context
- One-click approve / reject
- Audit trail viewer

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| AI / LLM | Azure OpenAI (GPT-4o) |
| Orchestration | Microsoft Semantic Kernel |
| Trigger | Azure Functions |
| Database | Azure SQL |
| Deployment | Azure Container Apps |
| Email Integration | Microsoft Graph API |
| Auth | Azure Active Directory (RBAC) |
| Validation | Pydantic v2 |
| Testing | pytest (37 tests, fully offline) |

---

## 🔑 Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
# Required for real Planner Agent calls
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# Required for production Retriever Agent
AZURE_SQL_SERVER=<your-server>.database.windows.net
AZURE_SQL_DATABASE=businessflow
AZURE_SQL_USERNAME=<username>
AZURE_SQL_PASSWORD=<password>

# Switch between mock and real DB
RETRIEVER_BACKEND=mock   # change to azure_sql for production
```

---

## 👥 Team

**NeuroNekos** — Undergraduate Data Science students, IIT Madras
- Track: Agent Teamwork (Track 4)
- Challenge: Microsoft AI Unlocked