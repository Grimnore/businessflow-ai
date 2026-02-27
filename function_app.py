"""
BusinessFlow AI — Azure Function Entry Point
=============================================
Triggered by Microsoft Graph API / Event Grid when a new email
arrives in the monitored mailbox.

Trigger options (configure in function.json):
  - Timer trigger (polling)          → for quick demo
  - Event Grid trigger               → for production
  - HTTP trigger                     → for manual testing

This file uses an HTTP trigger so it's easy to test locally and
during the hackathon demo.
"""

import json
import logging
import os
import uuid

import azure.functions as func

from planner_agent.planner import PlannerAgent, ExecutionPlan

logger = logging.getLogger(__name__)

# Initialise agent once (cold-start optimisation)
_agent: PlannerAgent | None = None


def _get_agent() -> PlannerAgent:
    global _agent
    if _agent is None:
        _agent = PlannerAgent()
    return _agent


# ---------------------------------------------------------------------------
# HTTP Trigger  (POST /api/planner)
# ---------------------------------------------------------------------------

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="planner", methods=["POST"])
def planner_trigger(req: func.HttpRequest) -> func.HttpResponse:
    """
    Accepts a JSON payload representing an inbound supplier email.

    Expected body:
    {
        "subject": "Re: Stock Replenishment - June Batch",
        "body":    "Hi, we can supply 500 units of SKU-1042 ...",
        "from":    "supplier@example.com"   // optional metadata
    }

    Returns:
        200 + ExecutionPlan JSON on success
        400 on bad input
        500 on internal error
    """
    request_id = str(uuid.uuid4())[:8]
    logger.info("[%s] Planner trigger received", request_id)

    # --- Parse request -------------------------------------------------------
    try:
        payload = req.get_json()
    except ValueError:
        return _error(400, "Request body must be valid JSON")

    email_body = payload.get("body", "").strip()
    subject    = payload.get("subject", "").strip()

    if not email_body:
        return _error(400, "Field 'body' is required and must not be empty")

    # --- Run Planner Agent ---------------------------------------------------
    try:
        agent = _get_agent()
        plan: ExecutionPlan = agent.parse_email(
            email_body=email_body,
            subject=subject,
            plan_id=request_id,
        )
    except Exception as exc:
        logger.exception("[%s] Planner Agent failed", request_id)
        return _error(500, f"Planner Agent error: {str(exc)}")

    # --- Return plan ---------------------------------------------------------
    logger.info("[%s] Plan produced | items=%d | total=₹%.2f", request_id, len(plan.line_items), plan.total_order_value)

    return func.HttpResponse(
        body=plan.json(indent=2),
        status_code=200,
        mimetype="application/json",
    )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _error(status: int, message: str) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps({"error": message}),
        status_code=status,
        mimetype="application/json",
    )
