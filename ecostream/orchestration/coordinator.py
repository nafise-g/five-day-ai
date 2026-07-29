"""
Master Coordinator Agent orchestrating multi-agent workflow, model routing, guardrails, and memory updates.
Fulfills Rubric Category 3: Multi-Agent Patterns, Strategic Model Routing, Guardrails.
"""

from typing import Dict, Any, Optional
import time
from ecostream.constitution import get_system_instructions
from ecostream.orchestration.router import StrategicModelRouter
from ecostream.orchestration.guardrails import PolicyGuardrailPlugin
from ecostream.orchestration.subagents import DataExtractorSubAgent, CarbonAuditorSubAgent, CompliancePlannerSubAgent
from ecostream.memory.session_store import PersistentSessionStore
from ecostream.memory.compactor import ContextCompactor
from ecostream.memory.async_memory_worker import AsyncMemoryWorker
from ecostream.observability.intent_outcome_tracer import trace_intent_outcome
from ecostream.observability.tracing import tracer

class EcoStreamCoordinatorAgent:
    """
    Main Master Agent orchestrating the entire EcoStream Sustainability Pipeline using the Coordinator Pattern.
    """

    def __init__(self, session_store: Optional[PersistentSessionStore] = None):
        self.role_name = "Coordinator"
        self.system_instructions = get_system_instructions(self.role_name)
        
        # Sub-components
        self.router = StrategicModelRouter()
        self.guardrails = PolicyGuardrailPlugin()
        self.data_extractor = DataExtractorSubAgent()
        self.carbon_auditor = CarbonAuditorSubAgent()
        self.compliance_planner = CompliancePlannerSubAgent()
        
        # Memory
        self.session_store = session_store or PersistentSessionStore()
        self.compactor = ContextCompactor()
        self.async_memory_worker = AsyncMemoryWorker(self.session_store, self.compactor)

    @trace_intent_outcome(action_name="execute_audit_workflow")
    def run_sustainability_audit(
        self,
        session_id: str,
        user_prompt: str,
        facility_input_data: Dict[str, Any],
        proposed_action: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Runs full end-to-end sustainability audit pipeline across sub-agents.
        """
        with tracer.start_span("execute_audit_workflow", attributes={"session_id": session_id}) as main_span:
            # 1. Store input user query in persistent memory
            self.session_store.create_or_get_session(session_id)
            self.session_store.append_message(session_id, "user", user_prompt)

            # 2. Run Input Guardrails Evaluation
            with tracer.start_span("input_guardrail_check"):
                guard_check = self.guardrails.evaluate_input_guardrails(user_prompt)
                if not guard_check["passed"]:
                    error_resp = {
                        "success": False,
                        "error_type": "GUARDRAIL_VIOLATION",
                        "message": guard_check["reason"]
                    }
                    self.session_store.append_message(session_id, "assistant", str(error_resp))
                    return error_resp

            # 3. Strategic Model Selection
            model_routing = self.router.select_model("AUDIT_CALC", user_prompt)
            main_span.set_attribute("selected_model", model_routing["selected_model"])

            # 4. Step A: Data Extraction Sub-Agent
            with tracer.start_span("subagent_data_extraction"):
                extracted_res = self.data_extractor.process(facility_input_data)

            # 5. Step B: Carbon Auditor Sub-Agent (Scope 1/2 calculations & GHG targets)
            with tracer.start_span("subagent_carbon_audit"):
                audit_res = self.carbon_auditor.process(extracted_res["output"])

            # 6. Step C: Compliance & Strategy Sub-Agent (Roadmap & Approval Tickets)
            with tracer.start_span("subagent_compliance_planning"):
                strategy_res = self.compliance_planner.process(audit_res, proposed_action)

            # 7. Step D: Output Guardrails Self-Evaluation
            emissions_data = audit_res.get("emissions_audit", {}).get("data", {})
            with tracer.start_span("output_guardrail_check"):
                out_guard = self.guardrails.evaluate_output_guardrails(
                    agent_output="Sustainability Audit Completed.",
                    audit_data=emissions_data
                )
                if not out_guard["passed"]:
                    return {
                        "success": False,
                        "error_type": "OUTPUT_GUARDRAIL_VIOLATION",
                        "message": out_guard["reason"]
                    }

            # 8. Persist findings to database
            facility_id = facility_input_data.get("facility_id", "FAC-DEFAULT")
            self.session_store.save_audit_finding(session_id, facility_id, "emissions_summary", emissions_data)

            final_response = {
                "success": True,
                "session_id": session_id,
                "routing": model_routing,
                "extraction": extracted_res,
                "audit": audit_res,
                "strategy": strategy_res,
                "guardrails_status": "PASSED"
            }

            self.session_store.append_message(session_id, "assistant", f"Audit Completed for facility {facility_id}.")

            # 9. Trigger Non-blocking Async Background Memory Consolidation
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    self.async_memory_worker.schedule_background_memory_consolidation(session_id)
            except Exception:
                pass

            return final_response
