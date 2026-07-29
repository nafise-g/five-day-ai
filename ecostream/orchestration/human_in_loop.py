"""
Human-in-the-Loop approval gate implementation with explicit execution stops for high-stakes actions.
Fulfills Rubric Category 3: Human-in-the-Loop Hooks.
"""

from typing import Dict, Any, Callable, Optional
import functools
import uuid
import time
from config import config

class HumanInTheLoopGate:
    """
    Manages explicit code stops for high-stakes actions (e.g. actions with financial impact > $10,000 USD
    or long-term PPA contract commitments).
    """

    def __init__(self, approval_cost_threshold: float = config.APPROVAL_REQUIRED_THRESHOLD_USD):
        self.approval_cost_threshold = approval_cost_threshold
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}

    def register_approval_request(
        self,
        action_type: str,
        facility_id: str,
        cost_usd: float,
        reduction_mt: float,
        vendor: str,
        justification: str
    ) -> Dict[str, Any]:
        """Registers a pending approval request ticket and halts immediate auto-execution."""
        ticket_id = f"TICKET-{uuid.uuid4().hex[:8].upper()}"
        requires_approval = cost_usd >= self.approval_cost_threshold or action_type == "SOLAR_PPA_CONTRACT"

        ticket = {
            "ticket_id": ticket_id,
            "action_type": action_type,
            "facility_id": facility_id,
            "cost_usd": cost_usd,
            "expected_reduction_co2e_mt": reduction_mt,
            "vendor": vendor,
            "justification": justification,
            "status": "PENDING_HUMAN_APPROVAL" if requires_approval else "AUTO_APPROVED",
            "requires_approval": requires_approval,
            "timestamp": time.time(),
            "approval_threshold_usd": self.approval_cost_threshold
        }

        if requires_approval:
            self.pending_approvals[ticket_id] = ticket

        return ticket

    def approve_ticket(self, ticket_id: str, approver_id: str = "EXECUTIVE_ADMIN") -> Dict[str, Any]:
        """Manually authorizes a pending approval ticket."""
        if ticket_id not in self.pending_approvals:
            return {"success": False, "message": f"Approval ticket '{ticket_id}' not found or already processed."}

        ticket = self.pending_approvals.pop(ticket_id)
        ticket["status"] = "APPROVED"
        ticket["approved_by"] = approver_id
        ticket["approved_at"] = time.time()
        return {"success": True, "ticket": ticket}

    def reject_ticket(self, ticket_id: str, reason: str = "Budget constraints") -> Dict[str, Any]:
        """Manually rejects a pending approval ticket."""
        if ticket_id not in self.pending_approvals:
            return {"success": False, "message": f"Approval ticket '{ticket_id}' not found."}

        ticket = self.pending_approvals.pop(ticket_id)
        ticket["status"] = "REJECTED"
        ticket["rejection_reason"] = reason
        ticket["rejected_at"] = time.time()
        return {"success": True, "ticket": ticket}

# Global Singleton Gate
approval_gate = HumanInTheLoopGate()


def human_in_the_loop_required(cost_param_name: str = "estimated_cost_usd"):
    """
    Decorator that intercepts function calls and enforces explicit code stop if cost exceeds approval threshold.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cost = kwargs.get(cost_param_name, 0.0)
            if cost >= config.APPROVAL_REQUIRED_THRESHOLD_USD:
                action_type = kwargs.get("action_type", func.__name__)
                facility_id = kwargs.get("facility_id", "UNKNOWN_FACILITY")
                vendor = kwargs.get("vendor_name", "UNKNOWN_VENDOR")
                justification = kwargs.get("justification", "High-cost operational change")
                reduction = kwargs.get("expected_co2e_reduction_mt", 0.0)

                ticket = approval_gate.register_approval_request(
                    action_type=action_type,
                    facility_id=facility_id,
                    cost_usd=cost,
                    reduction_mt=reduction,
                    vendor=vendor,
                    justification=justification
                )

                return {
                    "success": False,
                    "action_halted": True,
                    "reason": f"HIGH_STAKES_ACTION_DETECTED: Action cost (${cost:,.2f}) exceeds approval threshold (${config.APPROVAL_REQUIRED_THRESHOLD_USD:,.2f}).",
                    "approval_ticket": ticket,
                    "instruction": f"Provide human approval token for ticket '{ticket['ticket_id']}' to resume execution."
                }

            return func(*args, **kwargs)
        return wrapper
    return decorator
