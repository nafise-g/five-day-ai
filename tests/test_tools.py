"""
Unit tests for EcoStream domain tools, schema validation, and error recovery.
"""

import unittest
from ecostream.tools.energy_extractor import extract_facility_energy_consumption
from ecostream.tools.carbon_auditor import calculate_facility_scope2_emissions, audit_ghg_compliance_records
from ecostream.tools.approval_workflow import request_executive_mitigation_approval

class TestEcoStreamTools(unittest.TestCase):

    def test_energy_extractor_valid(self):
        res = extract_facility_energy_consumption(
            facility_id="FAC-BOS-001",
            facility_name="Boston Center",
            region_code="US-NEISO",
            electricity_kwh=100000.0,
            natural_gas_therms=500.0
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["metrics"]["electricity_mwh"], 100.0)
        self.assertEqual(res["data"]["metrics"]["natural_gas_mmbtu"], 50.0)

    def test_energy_extractor_guided_error_invalid_region(self):
        res = extract_facility_energy_consumption(
            facility_id="FAC-001",
            facility_name="Test",
            region_code="INVALID_GRID_99",
            electricity_kwh=500.0
        )
        self.assertFalse(res["success"])
        self.assertIn("Unknown electrical grid", res["error_message"])
        self.assertIn("recovery_instructions", res)
        self.assertTrue(res["is_retryable"])

    def test_carbon_auditor_calculations(self):
        res = calculate_facility_scope2_emissions(
            facility_id="FAC-BOS-001",
            region_code="US-NEISO",
            electricity_kwh=100000.0,
            natural_gas_therms=500.0
        )
        self.assertTrue(res["success"])
        data = res["data"]
        self.assertEqual(data["scope2_co2e_mt"], 23.0) # 100,000 * 0.230 / 1000
        self.assertEqual(data["scope1_co2e_mt"], 2.653) # 500 * 5.306 / 1000

    def test_human_in_loop_high_cost_trigger(self):
        res = request_executive_mitigation_approval(
            action_type="SOLAR_PPA_CONTRACT",
            facility_id="FAC-TX-999",
            estimated_cost_usd=75000.0,
            expected_co2e_reduction_mt=300.0,
            vendor_name="SolarCorp",
            justification="Offset Scope 2 emissions."
        )
        self.assertTrue(res["success"])
        ticket = res["data"]
        self.assertEqual(ticket["status"], "PENDING_HUMAN_APPROVAL")
        self.assertTrue(ticket["requires_approval"])

if __name__ == "__main__":
    unittest.main()
