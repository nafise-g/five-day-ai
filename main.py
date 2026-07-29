"""
Main Entrypoint Demonstration Script for EcoStream AI Agent.
Demonstrates end-to-end multi-agent orchestration, model routing, audit tool execution,
guardrail validation, persistent memory, human-in-the-loop gating, and structured logging.
"""

import sys
import json
import asyncio
from ecostream.orchestration.coordinator import EcoStreamCoordinatorAgent
from ecostream.orchestration.human_in_loop import approval_gate
from ecostream.observability.json_logger import logger

def print_banner():
    print("=" * 80)
    print(" ECOSTREAM AI: ENTERPRISE SUSTAINABILITY & CARBON FOOTPRINT AUDIT AGENT ")
    print(" Built with Google Agent Development Kit (ADK) & Gemini 2.5 Models ")
    print("=" * 80)

async def run_demo():
    print_banner()

    # Initialize Master Coordinator Agent
    agent = EcoStreamCoordinatorAgent()
    session_id = "SESSION-DEMO-2026"

    print("\n[STEP 1]: Initiating Enterprise Scope 1 & Scope 2 Audit Pipeline...")
    
    # Facility Data Input
    sample_facility_data = {
        "facility_id": "FAC-BOS-001",
        "facility_name": "Boston Enterprise Technology Hub",
        "region_code": "US-NEISO",
        "electricity_kwh": 125000.0,
        "natural_gas_therms": 850.0,
        "diesel_gallons": 150.0,
        "reporting_period": "2025-Q4"
    }

    user_query = "Audit quarterly GHG emissions for Boston Tech Hub and submit remediation proposal if non-compliant."

    # Run audit pipeline
    audit_response = agent.run_sustainability_audit(
        session_id=session_id,
        user_prompt=user_query,
        facility_input_data=sample_facility_data,
        proposed_action={
            "action_type": "SOLAR_PPA_CONTRACT",
            "estimated_cost_usd": 45000.0,
            "expected_co2e_reduction_mt": 120.0,
            "vendor_name": "Northeast Clean Energy Inc",
            "justification": "Procure 450 MWh annual solar power to eliminate Scope 2 location emissions."
        }
    )

    print("\n" + "=" * 80)
    print(" AUDIT EXECUTION SUMMARY & ROUTING ")
    print("=" * 80)
    print(f"Session ID:              {audit_response['session_id']}")
    print(f"Selected Model:          {audit_response['routing']['selected_model']} ({audit_response['routing']['complexity_tier']})")
    print(f"Routing Rationale:       {audit_response['routing']['reason']}")
    print(f"Input Guardrails:        {audit_response['guardrails_status']}")

    emissions = audit_response['audit']['emissions_audit']['data']
    compliance = audit_response['audit']['compliance_audit']['data']

    print("\n" + "=" * 80)
    print(" CARBON EMISSIONS & GHG PROTOCOL AUDIT ")
    print("=" * 80)
    print(f"Facility:                {emissions['facility_id']} ({emissions['region_code']} Grid)")
    print(f"Reporting Period:        {emissions['reporting_period']}")
    print(f"Grid Emission Factor:    {emissions['emission_factor_used_kg_per_kwh']} kg CO2e / kWh")
    print(f"Scope 1 Emissions:       {emissions['scope1_co2e_mt']} Metric Tons CO2e")
    print(f"Scope 2 Emissions:       {emissions['scope2_co2e_mt']} Metric Tons CO2e")
    print(f"Total Footprint:         {emissions['total_co2e_mt']} Metric Tons CO2e")
    print(f"Compliance Status:       {'COMPLIANT' if compliance['is_ghg_compliant'] else 'NON-COMPLIANT'}")

    ticket = audit_response['strategy']['approval_ticket_submission']['data']
    print("\n" + "=" * 80)
    print(" HUMAN-IN-THE-LOOP EXECUTIVE APPROVAL GATE ")
    print("=" * 80)
    print(f"Approval Ticket ID:      {ticket['ticket_id']}")
    print(f"Action Proposed:         {ticket['action_type']} with {ticket['vendor']}")
    print(f"Estimated Cost:          ${ticket['cost_usd']:,.2f} USD (Threshold: ${ticket['approval_threshold_usd']:,.2f} USD)")
    print(f"Status:                  {ticket['status']}")
    print(f"Requires Approval:       {ticket['requires_approval']}")

    # Demonstrate Human Ticket Authorization
    if ticket['requires_approval']:
        print(f"\n[HUMAN-IN-THE-LOOP HOOK]: Halting execution. Simulating Executive Approval for '{ticket['ticket_id']}'...")
        approval_res = approval_gate.approve_ticket(ticket['ticket_id'], approver_id="VP_SUSTAINABILITY_CHIEF")
        print(f"Approval Outcome:        {approval_res['ticket']['status']} by {approval_res['ticket']['approved_by']}")

    # Allow async memory consolidation task to complete
    await asyncio.sleep(0.1)

    print("\n" + "=" * 80)
    print(" DEMONSTRATION COMPLETED SUCCESSFULLY ")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_demo())
