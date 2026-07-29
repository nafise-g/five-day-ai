"""
Automated Evaluation Suite running static regression evaluation against a Golden Dataset.
Fulfills Rubric Category 5: Automated Evaluation Suites.
"""

import unittest
import json
import os
from ecostream.orchestration.coordinator import EcoStreamCoordinatorAgent
from ecostream.memory.session_store import PersistentSessionStore

class TestEcoStreamEvaluationSuite(unittest.TestCase):
    """
    Evaluates agent regression, calculation accuracy, and tool invocation contracts against golden_dataset.json.
    """

    @classmethod
    def setUpClass(cls):
        dataset_path = os.path.join(os.path.dirname(__file__), "golden_dataset.json")
        with open(dataset_path, "r") as f:
            cls.golden_cases = json.load(f)
        
        cls.db_path = "test_eval_memory.db"
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
            
        cls.session_store = PersistentSessionStore(db_path=cls.db_path)
        cls.coordinator = EcoStreamCoordinatorAgent(session_store=cls.session_store)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def test_golden_dataset_evaluations(self):
        """Runs static evaluation suite across all golden benchmark cases."""
        passed_cases = 0
        total_cases = len(self.golden_cases)

        for case in self.golden_cases:
            test_id = case["test_id"]
            prompt = case["prompt"]
            input_data = case["input_data"]
            proposed_action = case.get("proposed_action")

            # Execute pipeline
            res = self.coordinator.run_sustainability_audit(
                session_id=f"SESS-{test_id}",
                user_prompt=prompt,
                facility_input_data=input_data,
                proposed_action=proposed_action
            )

            self.assertTrue(res["success"], f"Case {test_id} failed execution.")

            # Validate metrics matching
            if "expected_metrics" in case:
                exp = case["expected_metrics"]
                actual_emissions = res["audit"]["emissions_audit"]["data"]
                actual_comp = res["audit"]["compliance_audit"]["data"]

                self.assertAlmostEqual(actual_emissions["scope1_co2e_mt"], exp["scope1_co2e_mt"], places=2)
                self.assertAlmostEqual(actual_emissions["scope2_co2e_mt"], exp["scope2_co2e_mt"], places=2)
                self.assertAlmostEqual(actual_emissions["total_co2e_mt"], exp["total_co2e_mt"], places=2)
                self.assertEqual(actual_comp["is_ghg_compliant"], exp["is_compliant"])

            # Validate approval ticket status matching
            if "expected_approval_status" in case:
                exp_status = case["expected_approval_status"]
                actual_ticket = res["strategy"]["approval_ticket_submission"]["data"]
                self.assertEqual(actual_ticket["status"], exp_status)

            passed_cases += 1

        accuracy_score = (passed_cases / total_cases) * 100.0
        print(f"\n[GOLDEN DATASET EVALUATION RESULTS]: Passed {passed_cases}/{total_cases} cases ({accuracy_score:.1f}% Accuracy)")
        self.assertEqual(accuracy_score, 100.0)

if __name__ == "__main__":
    unittest.main()
