"""
BusinessFlow AI — Retriever Agent
===================================
Given an ExecutionPlan from the Planner Agent, the Retriever Agent
queries the inventory database and enriches each LineItem with:

  - current_stock     : units currently in warehouse
  - reorder_threshold : minimum stock level before reorder is needed
  - unit_cost         : our internal cost per unit (may differ from supplier price)
  - last_reorder_date : when we last ordered this SKU
  - supplier_lead_days: typical delivery time in days

The enriched data is returned as a StockContext object, which the
Policy Layer uses to make approval/rejection decisions.

Two backends are supported:
  - MockDB   : in-memory dict, works with zero setup (default for dev/testing)
  - AzureSQLDB: real Azure SQL via pyodbc (used in production)

Switch via the RETRIEVER_BACKEND env var: "mock" (default) or "azure_sql"
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class SKUContext:
    """Inventory context for a single SKU, retrieved from the database."""
    sku_id: str
    product_name: str
    current_stock: int
    reorder_threshold: int
    unit_cost: float                        # our internal cost per unit (INR)
    last_reorder_date: Optional[str] = None # ISO date string
    supplier_lead_days: int = 7             # typical delivery time
    found: bool = True                      # False if SKU not in DB

    @property
    def needs_restock(self) -> bool:
        """True if current stock is at or below the reorder threshold."""
        return self.current_stock <= self.reorder_threshold

    @property
    def stock_status(self) -> str:
        if self.current_stock == 0:
            return "OUT_OF_STOCK"
        elif self.needs_restock:
            return "LOW_STOCK"
        else:
            return "ADEQUATE"


@dataclass
class StockContext:
    """
    Full enriched context for an ExecutionPlan.
    Contains one SKUContext per line item in the plan.
    """
    plan_id: str
    retrieved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sku_contexts: list[SKUContext] = field(default_factory=list)
    missing_skus: list[str] = field(default_factory=list)  # SKUs not found in DB

    @property
    def all_found(self) -> bool:
        return len(self.missing_skus) == 0

    @property
    def total_current_stock_value(self) -> float:
        return sum(s.current_stock * s.unit_cost for s in self.sku_contexts if s.found)

    def get_sku(self, sku_id: str) -> Optional[SKUContext]:
        return next((s for s in self.sku_contexts if s.sku_id == sku_id), None)

    def summary(self) -> str:
        lines = [f"StockContext for plan {self.plan_id}:"]
        for s in self.sku_contexts:
            lines.append(
                f"  [{s.sku_id}] {s.product_name}: "
                f"stock={s.current_stock} threshold={s.reorder_threshold} "
                f"status={s.stock_status}"
            )
        if self.missing_skus:
            lines.append(f"  ⚠ Missing SKUs: {', '.join(self.missing_skus)}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Abstract DB Backend
# ---------------------------------------------------------------------------

class InventoryDB(ABC):
    """Abstract interface for the inventory database."""

    @abstractmethod
    def get_sku_context(self, sku_id: str) -> Optional[SKUContext]:
        """Fetch inventory context for a single SKU. Returns None if not found."""
        ...

    @abstractmethod
    def get_multiple_skus(self, sku_ids: list[str]) -> dict[str, SKUContext]:
        """Fetch multiple SKUs in one call. Returns dict of sku_id → SKUContext."""
        ...


# ---------------------------------------------------------------------------
# Mock Backend (zero setup, for dev & testing)
# ---------------------------------------------------------------------------

# Realistic sample inventory for an Indian e-commerce SME
MOCK_INVENTORY: dict[str, dict] = {
    "SKU-TSH-001": {
        "product_name": "Cotton T-Shirt (White, L)",
        "current_stock": 45,
        "reorder_threshold": 50,
        "unit_cost": 160.0,
        "last_reorder_date": "2025-05-10",
        "supplier_lead_days": 5,
    },
    "SKU-JNS-042": {
        "product_name": "Denim Jeans (32W)",
        "current_stock": 12,
        "reorder_threshold": 30,
        "unit_cost": 580.0,
        "last_reorder_date": "2025-04-22",
        "supplier_lead_days": 7,
    },
    "SKU-SNK-007": {
        "product_name": "Sports Sneakers (Size 9)",
        "current_stock": 0,
        "reorder_threshold": 20,
        "unit_cost": 1050.0,
        "last_reorder_date": "2025-03-15",
        "supplier_lead_days": 10,
    },
    "SKU-CAP-003": {
        "product_name": "Baseball Cap (Black)",
        "current_stock": 200,
        "reorder_threshold": 40,
        "unit_cost": 95.0,
        "last_reorder_date": "2025-06-01",
        "supplier_lead_days": 4,
    },
    "SKU-BAG-011": {
        "product_name": "Canvas Tote Bag",
        "current_stock": 8,
        "reorder_threshold": 25,
        "unit_cost": 210.0,
        "last_reorder_date": "2025-05-28",
        "supplier_lead_days": 6,
    },
}


class MockDB(InventoryDB):
    """
    In-memory mock database for development and testing.
    No Azure setup required. Pre-loaded with realistic sample SKUs.
    """

    def __init__(self, inventory: dict | None = None):
        self._inventory = inventory or MOCK_INVENTORY
        logger.info("MockDB initialised with %d SKUs", len(self._inventory))

    def get_sku_context(self, sku_id: str) -> Optional[SKUContext]:
        data = self._inventory.get(sku_id)
        if not data:
            logger.warning("SKU not found in MockDB: %s", sku_id)
            return None
        return SKUContext(sku_id=sku_id, **data)

    def get_multiple_skus(self, sku_ids: list[str]) -> dict[str, SKUContext]:
        result = {}
        for sku_id in sku_ids:
            ctx = self.get_sku_context(sku_id)
            if ctx:
                result[sku_id] = ctx
        return result

    def add_sku(self, sku_id: str, data: dict) -> None:
        """Helper for tests — add a SKU to the mock inventory."""
        self._inventory[sku_id] = data

    def update_stock(self, sku_id: str, new_stock: int) -> None:
        """Helper to simulate stock updates."""
        if sku_id in self._inventory:
            self._inventory[sku_id]["current_stock"] = new_stock


# ---------------------------------------------------------------------------
# Azure SQL Backend (production)
# ---------------------------------------------------------------------------

class AzureSQLDB(InventoryDB):
    """
    Real Azure SQL backend via pyodbc.

    Required env vars:
        AZURE_SQL_SERVER   — e.g. myserver.database.windows.net
        AZURE_SQL_DATABASE — e.g. businessflow
        AZURE_SQL_USERNAME — SQL login username
        AZURE_SQL_PASSWORD — SQL login password

    Required SQL table (run schema.sql to create):
        CREATE TABLE inventory (
            sku_id              VARCHAR(50) PRIMARY KEY,
            product_name        VARCHAR(255) NOT NULL,
            current_stock       INT NOT NULL DEFAULT 0,
            reorder_threshold   INT NOT NULL DEFAULT 10,
            unit_cost           DECIMAL(10,2) NOT NULL,
            last_reorder_date   DATE,
            supplier_lead_days  INT NOT NULL DEFAULT 7
        );
    """

    def __init__(self):
        try:
            import pyodbc
        except ImportError:
            raise ImportError(
                "pyodbc is required for AzureSQLDB. "
                "Install it with: pip install pyodbc"
            )

        server   = os.environ["AZURE_SQL_SERVER"]
        database = os.environ["AZURE_SQL_DATABASE"]
        username = os.environ["AZURE_SQL_USERNAME"]
        password = os.environ["AZURE_SQL_PASSWORD"]

        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Encrypt=yes;TrustServerCertificate=no;"
        )
        self._conn = pyodbc.connect(conn_str)
        logger.info("AzureSQLDB connected | server=%s db=%s", server, database)

    def get_sku_context(self, sku_id: str) -> Optional[SKUContext]:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT sku_id, product_name, current_stock, reorder_threshold,
                   unit_cost, last_reorder_date, supplier_lead_days
            FROM   inventory
            WHERE  sku_id = ?
            """,
            sku_id,
        )
        row = cursor.fetchone()
        if not row:
            logger.warning("SKU not found in Azure SQL: %s", sku_id)
            return None

        return SKUContext(
            sku_id=row.sku_id,
            product_name=row.product_name,
            current_stock=row.current_stock,
            reorder_threshold=row.reorder_threshold,
            unit_cost=float(row.unit_cost),
            last_reorder_date=str(row.last_reorder_date) if row.last_reorder_date else None,
            supplier_lead_days=row.supplier_lead_days,
        )

    def get_multiple_skus(self, sku_ids: list[str]) -> dict[str, SKUContext]:
        if not sku_ids:
            return {}

        placeholders = ",".join("?" * len(sku_ids))
        cursor = self._conn.cursor()
        cursor.execute(
            f"""
            SELECT sku_id, product_name, current_stock, reorder_threshold,
                   unit_cost, last_reorder_date, supplier_lead_days
            FROM   inventory
            WHERE  sku_id IN ({placeholders})
            """,
            *sku_ids,
        )
        result = {}
        for row in cursor.fetchall():
            result[row.sku_id] = SKUContext(
                sku_id=row.sku_id,
                product_name=row.product_name,
                current_stock=row.current_stock,
                reorder_threshold=row.reorder_threshold,
                unit_cost=float(row.unit_cost),
                last_reorder_date=str(row.last_reorder_date) if row.last_reorder_date else None,
                supplier_lead_days=row.supplier_lead_days,
            )
        return result

    def close(self):
        self._conn.close()


# ---------------------------------------------------------------------------
# Retriever Agent
# ---------------------------------------------------------------------------

class RetrieverAgent:
    """
    Enriches an ExecutionPlan with live inventory context.

    Usage:
        # Dev mode (no Azure needed)
        agent = RetrieverAgent()

        # Production
        agent = RetrieverAgent(backend="azure_sql")

        context = agent.retrieve(plan)
        print(context.summary())
    """

    def __init__(self, backend: str | None = None):
        mode = backend or os.getenv("RETRIEVER_BACKEND", "mock")

        if mode == "azure_sql":
            self._db: InventoryDB = AzureSQLDB()
            logger.info("RetrieverAgent using AzureSQLDB backend")
        else:
            self._db = MockDB()
            logger.info("RetrieverAgent using MockDB backend")

    def retrieve(self, plan) -> StockContext:
        """
        Fetch inventory context for all SKUs in an ExecutionPlan.

        Args:
            plan: ExecutionPlan from the Planner Agent

        Returns:
            StockContext — enriched data for the Policy Layer
        """
        sku_ids = [item.sku_id for item in plan.line_items]
        logger.info("Retrieving context for %d SKUs | plan_id=%s", len(sku_ids), plan.plan_id)

        # Batch fetch — one DB call for all SKUs
        found = self._db.get_multiple_skus(sku_ids)

        sku_contexts = []
        missing = []

        for sku_id in sku_ids:
            if sku_id in found:
                sku_contexts.append(found[sku_id])
            else:
                missing.append(sku_id)
                # Add a placeholder so downstream agents know it's missing
                sku_contexts.append(SKUContext(
                    sku_id=sku_id,
                    product_name="UNKNOWN",
                    current_stock=0,
                    reorder_threshold=0,
                    unit_cost=0.0,
                    found=False,
                ))

        context = StockContext(
            plan_id=plan.plan_id,
            sku_contexts=sku_contexts,
            missing_skus=missing,
        )

        logger.info(
            "StockContext ready | found=%d missing=%d | plan_id=%s",
            len(found), len(missing), plan.plan_id,
        )
        return context