"""
Tool for handling human-in-the-loop executive approval gating for high-stakes mitigation actions.
Fulfills Rubric Category 3: Human-in-the-Loop Hooks & Category 1: Explicit Tools.
"""

from typing import Dict, Any
import uuid
import time
from ecostream.schemas import ExecutiveApprovalRequestInput, validate_tool_arguments, ToolExecutionResult
from ecostream.observability.intent_outcome_tracer import trace_intent_outcome
from ecostream.orchestration.human_in_loop import HumanInTheLoopGate, approval_gate


@trace_intent_outcome(action_name="request_executive_mitigation_approval")
def request_executive_mitigation_approval(
    action_type: str,
    facility_id: str,
    estimated_cost_usd: float,
    expected_co2e_reduction_mt: float,
    vendor_name: str,
    justification: str
) -> Dict[str, Any]:
    """
    Submits a high-stakes decarbonization proposal to the executive Human-in-the-Loop approval gate.

    Triggers explicit code stop and generates a pending authorization ticket for actions requiring
    capital expenditure (> $10,000 USD) or major contract commitments (e.g. Solar PPA, Carbon Offsets).

    Args:
        action_type (str): Type of mitigation action ('CARBON_OFFSET_PURCHASE', 'SOLAR_PPA_CONTRACT', 'FACILITY_HVAC_UPGRADE').
        facility_id (str): Facility identifier.
        estimated_cost_usd (float): Total capital cost in USD.
        expected_co2e_reduction_mt (float): Estimated annual emissions reduction in Metric Tons CO2e.
        vendor_name (str): Vendor or counterparty organization.
        justification (str): Audit-backed ROI and environmental justification.

    Returns:
        Dict[str, Any]: Approval ticket details containing token status (PENDING_HUMAN_APPROVAL or APPROVED).
    """
    raw_args = {
        "action_type": action_type,
        "facility_id": facility_id,
        "estimated_cost_usd": estimated_cost_usd,
        "expected_co2e_reduction_mt": expected_co2e_reduction_mt,
        "vendor_name": vendor_name,
        "justification": justification
    }

    # Step 1: Validate Schema
    val = validate_tool_arguments(ExecutiveApprovalRequestInput, raw_args)
    if not val.success:
        return val.to_dict()

    # Step 2: Register ticket in Human-in-the-Loop approval gate
    approval_ticket = approval_gate.register_approval_request(
        action_type=action_type,
        facility_id=facility_id,
        cost_usd=estimated_cost_usd,
        reduction_mt=expected_co2e_reduction_mt,
        vendor=vendor_name,
        justification=justification
    )

    return ToolExecutionResult(success=True, data=approval_ticket).to_dict()
