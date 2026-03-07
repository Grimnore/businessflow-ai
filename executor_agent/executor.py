"""
BusinessFlow AI — Executor Agent
==================================
The final agent in the pipeline. Takes a PolicyDecision that has been
approved (either AUTO_APPROVE or human-approved via the Dashboard) and
performs all required actions:

  1. Updates inventory stock levels in the database
  2. Creates purchase order records
  3. Writes a full audit log entry for every action
  4. Sends an email notification via Microsoft Graph API (or mock)

Two backends supported:
  - MockExecutor  : in-memory, zero setup, for dev/testing
  - AzureSQLExecutor: real Azure SQL via pyodbc

ExecutionResult is the final output — a complete record of what was done.

Pipeline position:
    PolicyDecision (APPROVED)
        → ExecutorAgent.execute()
            → update_inventory()
            → create_purchase_orders()
            → write_audit_log()
            → send_notification()
        → ExecutionResult
"""

from __future__ import annotations

import logging
import os
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class PurchaseOrder:
    """A single purchase order record created by the Executor Agent."""
    po_id:            str
    plan_id:          str
    sku_id:           str
    supplier_name:    str
    supplier_email:   str
    quantity_ordered: int
    unit_price:       float
    total_cost:       float
    status:           str = "EXECUTED"     # EXECUTED | PENDING_APPROVAL
    created_at:       str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    executed_at:      Optional[str] = None


@dataclass
class AuditEntry:
    """A single audit log entry."""
    log_id:     str
    plan_id:    str
    agent:      str        # PLANNER | RETRIEVER | POLICY | EXECUTOR
    action:     str
    details:    str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ExecutionResult:
    """
    Complete record of what the Executor Agent did.
    This is the final output of the entire BusinessFlow AI pipeline.
    """
    plan_id:           str
    success:           bool
    purchase_orders:   list[PurchaseOrder] = field(default_factory=list)
    audit_entries:     list[AuditEntry]    = field(default_factory=list)
    inventory_updates: list[dict]          = field(default_factory=list)   # {sku_id, old_stock, new_stock}
    skipped_items:     list[str]           = field(default_factory=list)   # items not executed
    notification_sent: bool = False
    error_message:     Optional[str] = None
    executed_at:       str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def total_executed_value(self) -> float:
        return sum(po.total_cost for po in self.purchase_orders)

    @property
    def orders_created(self) -> int:
        return len(self.purchase_orders)

    def summary(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        lines = [
            f"ExecutionResult [{status}] for plan {self.plan_id}",
            f"  Orders created    : {self.orders_created}",
            f"  Total value       : Rs.{self.total_executed_value:,.2f}",
            f"  Inventory updates : {len(self.inventory_updates)}",
            f"  Notification sent : {self.notification_sent}",
        ]
        if self.skipped_items:
            lines.append(f"  Skipped           : {', '.join(self.skipped_items)}")
        if self.error_message:
            lines.append(f"  Error             : {self.error_message}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Abstract DB Backend
# ---------------------------------------------------------------------------

class ExecutorDB(ABC):
    """Abstract interface for executor database operations."""

    @abstractmethod
    def update_stock(self, sku_id: str, quantity_to_add: int) -> tuple[int, int]:
        """Add quantity to current stock. Returns (old_stock, new_stock)."""
        ...

    @abstractmethod
    def create_purchase_order(self, po: PurchaseOrder) -> bool:
        """Insert a PO record. Returns True on success."""
        ...

    @abstractmethod
    def write_audit_log(self, entry: AuditEntry) -> bool:
        """Insert an audit log entry. Returns True on success."""
        ...

    @abstractmethod
    def get_current_stock(self, sku_id: str) -> Optional[int]:
        """Get current stock level for a SKU."""
        ...


# ---------------------------------------------------------------------------
# Mock Executor DB (zero setup, for dev & testing)
# ---------------------------------------------------------------------------

class MockExecutorDB(ExecutorDB):
    """
    In-memory mock for development and testing.
    Starts with the same inventory as MockDB in the Retriever Agent.
    """

    def __init__(self):
        # Mirror the MockDB inventory
        self._inventory: dict[str, int] = {
            "SKU-TSH-001": 45,
            "SKU-JNS-042": 12,
            "SKU-SNK-007": 0,
            "SKU-CAP-003": 200,
            "SKU-BAG-011": 8,
        }
        self._purchase_orders: list[dict] = []
        self._audit_log: list[dict] = []
        logger.info("MockExecutorDB initialised with %d SKUs", len(self._inventory))

    def get_current_stock(self, sku_id: str) -> Optional[int]:
        return self._inventory.get(sku_id)

    def update_stock(self, sku_id: str, quantity_to_add: int) -> tuple[int, int]:
        if sku_id not in self._inventory:
            raise ValueError(f"SKU {sku_id} not found in inventory")
        old_stock = self._inventory[sku_id]
        new_stock = old_stock + quantity_to_add
        self._inventory[sku_id] = new_stock
        logger.info("Stock updated | %s: %d → %d (+%d)", sku_id, old_stock, new_stock, quantity_to_add)
        return old_stock, new_stock

    def create_purchase_order(self, po: PurchaseOrder) -> bool:
        self._purchase_orders.append({
            "po_id": po.po_id, "plan_id": po.plan_id, "sku_id": po.sku_id,
            "supplier_name": po.supplier_name, "quantity": po.quantity_ordered,
            "unit_price": po.unit_price, "total_cost": po.total_cost,
            "status": po.status, "created_at": po.created_at,
        })
        logger.info("PO created | po_id=%s sku=%s qty=%d total=Rs.%.2f",
                    po.po_id, po.sku_id, po.quantity_ordered, po.total_cost)
        return True

    def write_audit_log(self, entry: AuditEntry) -> bool:
        self._audit_log.append({
            "log_id": entry.log_id, "plan_id": entry.plan_id,
            "agent": entry.agent, "action": entry.action,
            "details": entry.details, "created_at": entry.created_at,
        })
        logger.debug("Audit | agent=%s action=%s", entry.agent, entry.action)
        return True

    # ── Inspection helpers for tests ──────────────────────────────
    def get_all_purchase_orders(self) -> list[dict]:
        return self._purchase_orders.copy()

    def get_audit_log(self, plan_id: str | None = None) -> list[dict]:
        if plan_id:
            return [e for e in self._audit_log if e["plan_id"] == plan_id]
        return self._audit_log.copy()

    def get_stock(self, sku_id: str) -> Optional[int]:
        return self._inventory.get(sku_id)


# ---------------------------------------------------------------------------
# Azure SQL Executor DB (production)
# ---------------------------------------------------------------------------

class AzureSQLExecutorDB(ExecutorDB):
    """
    Production Azure SQL backend.
    Uses the same schema as retriever_agent/schema.sql.

    Required env vars:
        AZURE_SQL_SERVER, AZURE_SQL_DATABASE,
        AZURE_SQL_USERNAME, AZURE_SQL_PASSWORD
    """

    def __init__(self):
        try:
            import pyodbc
        except ImportError:
            raise ImportError("pyodbc is required. Install: pip install pyodbc")

        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={os.environ['AZURE_SQL_SERVER']};"
            f"DATABASE={os.environ['AZURE_SQL_DATABASE']};"
            f"UID={os.environ['AZURE_SQL_USERNAME']};"
            f"PWD={os.environ['AZURE_SQL_PASSWORD']};"
            "Encrypt=yes;TrustServerCertificate=no;"
        )
        self._conn = __import__("pyodbc").connect(conn_str)
        self._conn.autocommit = False  # Use explicit transactions
        logger.info("AzureSQLExecutorDB connected")

    def get_current_stock(self, sku_id: str) -> Optional[int]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT current_stock FROM inventory WHERE sku_id = ?", sku_id)
        row = cursor.fetchone()
        return row.current_stock if row else None

    def update_stock(self, sku_id: str, quantity_to_add: int) -> tuple[int, int]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT current_stock FROM inventory WHERE sku_id = ?", sku_id)
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"SKU {sku_id} not found")
        old_stock = row.current_stock
        new_stock = old_stock + quantity_to_add
        cursor.execute(
            "UPDATE inventory SET current_stock = ?, updated_at = GETUTCDATE() WHERE sku_id = ?",
            new_stock, sku_id
        )
        return old_stock, new_stock

    def create_purchase_order(self, po: PurchaseOrder) -> bool:
        cursor = self._conn.cursor()
        cursor.execute(
            """INSERT INTO purchase_orders
               (po_id, plan_id, sku_id, supplier_name, supplier_email,
                quantity_ordered, unit_price, total_cost, status, created_at, executed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETUTCDATE(), GETUTCDATE())""",
            po.po_id, po.plan_id, po.sku_id, po.supplier_name, po.supplier_email,
            po.quantity_ordered, po.unit_price, po.total_cost, po.status,
        )
        return True

    def write_audit_log(self, entry: AuditEntry) -> bool:
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT INTO audit_log (plan_id, agent, action, details) VALUES (?, ?, ?, ?)",
            entry.plan_id, entry.agent, entry.action, entry.details,
        )
        return True

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


# ---------------------------------------------------------------------------
# Notification Backend (Mock)
# ---------------------------------------------------------------------------

class MockNotifier:
    """Mock email notifier — logs instead of sending real emails."""

    def __init__(self):
        self.sent: list[dict] = []

    def send(self, to: str, subject: str, body: str) -> bool:
        self.sent.append({"to": to, "subject": subject, "body": body})
        logger.info("MOCK EMAIL sent | to=%s subject=%s", to, subject)
        return True


# ---------------------------------------------------------------------------
# Executor Agent
# ---------------------------------------------------------------------------

class ExecutorAgent:
    """
    Executes all actions for an approved PolicyDecision.

    Usage:
        # Dev mode (no Azure needed)
        agent = ExecutorAgent()

        # Production
        agent = ExecutorAgent(backend="azure_sql")

        result = agent.execute(plan, stock_context, decision)
        print(result.summary())
    """

    def __init__(self, backend: str | None = None, notifier=None):
        mode = backend or os.getenv("EXECUTOR_BACKEND", "mock")
        if mode == "azure_sql":
            self._db: ExecutorDB = AzureSQLExecutorDB()
            logger.info("ExecutorAgent using AzureSQLExecutorDB")
        else:
            self._db = MockExecutorDB()
            logger.info("ExecutorAgent using MockExecutorDB")

        self._notifier = notifier or MockNotifier()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(self, plan, stock_context, decision) -> ExecutionResult:
        """
        Execute all approved actions from a PolicyDecision.

        Args:
            plan:          ExecutionPlan from the Planner Agent
            stock_context: StockContext from the Retriever Agent
            decision:      PolicyDecision (must be AUTO_APPROVE or manually approved)

        Returns:
            ExecutionResult — complete record of all actions taken
        """
        from policy_layer.policy import Decision

        if decision.decision not in (Decision.AUTO_APPROVE,):
            # Only execute auto-approved decisions
            # (Manually approved ones from the dashboard set decision to AUTO_APPROVE before calling)
            logger.warning("Execution blocked | decision=%s | plan_id=%s",
                          decision.decision.value, plan.plan_id)
            return ExecutionResult(
                plan_id=plan.plan_id,
                success=False,
                error_message=f"Cannot execute — decision is {decision.decision.value}, not AUTO_APPROVE",
            )

        logger.info("Executing plan | plan_id=%s | items=%d | value=Rs.%.2f",
                    plan.plan_id, len(plan.line_items), plan.total_order_value)

        result = ExecutionResult(plan_id=plan.plan_id, success=True)

        # Log pipeline start
        self._audit(result, plan.plan_id, "PIPELINE_START",
                   f"Executing approved plan. Supplier: {plan.supplier_name}. "
                   f"Items: {len(plan.line_items)}. Value: Rs.{plan.total_order_value:,.2f}")

        # Process each line item
        for item in plan.line_items:
            sku_ctx = stock_context.get_sku(item.sku_id)

            # Skip items that shouldn't be executed
            if not sku_ctx or not sku_ctx.found:
                result.skipped_items.append(f"{item.sku_id} — not found in DB")
                continue
            if not sku_ctx.needs_restock:
                result.skipped_items.append(f"{item.sku_id} — stock adequate, skipped")
                continue

            try:
                # 1. Update inventory
                old_stock, new_stock = self._db.update_stock(item.sku_id, item.quantity)
                result.inventory_updates.append({
                    "sku_id":    item.sku_id,
                    "old_stock": old_stock,
                    "new_stock": new_stock,
                    "added":     item.quantity,
                })
                self._audit(result, plan.plan_id, "STOCK_UPDATED",
                           f"{item.sku_id}: stock {old_stock} → {new_stock} (+{item.quantity})")

                # 2. Create purchase order
                po = PurchaseOrder(
                    po_id=str(uuid.uuid4())[:8].upper(),
                    plan_id=plan.plan_id,
                    sku_id=item.sku_id,
                    supplier_name=plan.supplier_name,
                    supplier_email=plan.supplier_email,
                    quantity_ordered=item.quantity,
                    unit_price=item.unit_price,
                    total_cost=item.total_cost,
                    status="EXECUTED",
                    executed_at=datetime.now(timezone.utc).isoformat(),
                )
                self._db.create_purchase_order(po)
                result.purchase_orders.append(po)
                self._audit(result, plan.plan_id, "PO_CREATED",
                           f"PO {po.po_id} | {item.sku_id} | qty={item.quantity} | "
                           f"Rs.{item.total_cost:,.2f}")

            except Exception as exc:
                logger.error("Error executing item %s: %s", item.sku_id, exc)
                result.skipped_items.append(f"{item.sku_id} — execution error: {str(exc)}")
                self._audit(result, plan.plan_id, "EXECUTION_ERROR",
                           f"Failed to execute {item.sku_id}: {str(exc)}")

        # Commit if using real DB
        if hasattr(self._db, "commit"):
            self._db.commit()

        # 3. Send notification
        result.notification_sent = self._send_notification(plan, result)

        # 4. Log completion
        self._audit(result, plan.plan_id, "PIPELINE_COMPLETE",
                   f"Execution complete. POs created: {result.orders_created}. "
                   f"Total: Rs.{result.total_executed_value:,.2f}. "
                   f"Skipped: {len(result.skipped_items)}")

        logger.info("Execution complete | plan_id=%s | orders=%d | value=Rs.%.2f",
                    plan.plan_id, result.orders_created, result.total_executed_value)
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _audit(self, result: ExecutionResult, plan_id: str, action: str, details: str):
        entry = AuditEntry(
            log_id=str(uuid.uuid4())[:8],
            plan_id=plan_id,
            agent="EXECUTOR",
            action=action,
            details=details,
        )
        self._db.write_audit_log(entry)
        result.audit_entries.append(entry)

    def _send_notification(self, plan, result: ExecutionResult) -> bool:
        subject = f"BusinessFlow AI — Order Executed: {plan.plan_id}"
        body = (
            f"Plan ID     : {plan.plan_id}\n"
            f"Supplier    : {plan.supplier_name}\n"
            f"Orders      : {result.orders_created} POs created\n"
            f"Total Value : Rs.{result.total_executed_value:,.2f}\n\n"
            f"Items executed:\n"
        )
        for po in result.purchase_orders:
            body += f"  - {po.sku_id}: qty={po.quantity_ordered} @ Rs.{po.unit_price}/unit\n"
        if result.skipped_items:
            body += f"\nSkipped: {', '.join(result.skipped_items)}"

        return self._notifier.send(
            to=plan.supplier_email,
            subject=subject,
            body=body,
        )