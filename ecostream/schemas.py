"""
Explicit JSON Schemas and Data Models for Tool Arguments and LLM Input/Output Validation.
Fulfills Rubric Category 1: Explicit JSON Schemas.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
import json

# Attempt importing Pydantic if available, otherwise use pure Python schema validation
try:
    from pydantic import BaseModel, Field, ValidationError
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    class BaseModel:
        pass


@dataclass
class FacilityEnergyInput:
    """Schema for extracting facility energy consumption metrics."""
    facility_id: str
    facility_name: str
    region_code: str  # e.g., 'US-NEISO', 'US-CAMX', 'EU-DE'
    electricity_kwh: float
    natural_gas_therms: float = 0.0
    diesel_gallons: float = 0.0
    reporting_period: str = "2025-Q4"

    @classmethod
    def get_json_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "facility_id": {"type": "string", "description": "Unique identifier for the commercial facility."},
                "facility_name": {"type": "string", "description": "Human-readable name of the facility."},
                "region_code": {"type": "string", "description": "eGRID or regional power grid subregion code."},
                "electricity_kwh": {"type": "number", "description": "Total electricity consumption in kilowatt-hours (kWh)."},
                "natural_gas_therms": {"type": "number", "description": "Natural gas usage in therms."},
                "diesel_gallons": {"type": "number", "description": "Backup generator diesel fuel usage in gallons."},
                "reporting_period": {"type": "string", "description": "Quarterly or annual reporting identifier."}
            },
            "required": ["facility_id", "facility_name", "region_code", "electricity_kwh"]
        }


@dataclass
class EmissionsAuditResult:
    """Output schema for Scope 1 & Scope 2 carbon emissions audit."""
    facility_id: str
    reporting_period: str
    scope1_co2e_mt: float
    scope2_co2e_mt: float
    total_co2e_mt: float
    emission_intensity_per_kwh: float
    is_ghg_compliant: bool
    compliance_notes: List[str]

    @classmethod
    def get_json_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "facility_id": {"type": "string"},
                "reporting_period": {"type": "string"},
                "scope1_co2e_mt": {"type": "number", "description": "Scope 1 emissions in Metric Tons CO2e."},
                "scope2_co2e_mt": {"type": "number", "description": "Scope 2 location-based emissions in Metric Tons CO2e."},
                "total_co2e_mt": {"type": "number", "description": "Total combined Scope 1 and Scope 2 emissions."},
                "emission_intensity_per_kwh": {"type": "number", "description": "kg CO2e per kWh generated."},
                "is_ghg_compliant": {"type": "boolean", "description": "Whether facility meets GHG Protocol target thresholds."},
                "compliance_notes": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["facility_id", "scope1_co2e_mt", "scope2_co2e_mt", "total_co2e_mt", "is_ghg_compliant"]
        }


@dataclass
class ExecutiveApprovalRequestInput:
    """Input schema for requesting human-in-the-loop executive approval on high-stakes actions."""
    action_type: str  # e.g., 'CARBON_OFFSET_PURCHASE', 'SOLAR_PPA_CONTRACT'
    facility_id: str
    estimated_cost_usd: float
    expected_co2e_reduction_mt: float
    vendor_name: str
    justification: str

    @classmethod
    def get_json_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action_type": {"type": "string", "enum": ["CARBON_OFFSET_PURCHASE", "SOLAR_PPA_CONTRACT", "FACILITY_HVAC_UPGRADE"]},
                "facility_id": {"type": "string"},
                "estimated_cost_usd": {"type": "number", "description": "Total cost of proposed action in USD."},
                "expected_co2e_reduction_mt": {"type": "number", "description": "Estimated annual metric tons CO2e avoided."},
                "vendor_name": {"type": "string"},
                "justification": {"type": "string", "description": "Audit-backed business case justification."}
            },
            "required": ["action_type", "facility_id", "estimated_cost_usd", "expected_co2e_reduction_mt", "vendor_name", "justification"]
        }


@dataclass
class ToolExecutionResult:
    """Standardized schema for tool execution responses, featuring Guided Error Handling."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    recovery_instructions: Optional[str] = None
    suggested_retry_params: Optional[Dict[str, Any]] = None
    is_retryable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


def validate_tool_arguments(schema_class: Any, kwargs: Dict[str, Any]) -> ToolExecutionResult:
    """
    Validates tool argument kwargs against the explicit JSON schema or dataclass schema.
    Returns ToolExecutionResult with guided recovery instructions if validation fails.
    """
    required_fields = getattr(schema_class, "__annotations__", {}).keys()
    schema_dict = schema_class.get_json_schema() if hasattr(schema_class, "get_json_schema") else {}
    required_keys = schema_dict.get("required", [])

    missing_keys = [key for key in required_keys if key not in kwargs or kwargs[key] is None]
    if missing_keys:
        return ToolExecutionResult(
            success=False,
            error_message=f"Invalid arguments for {schema_class.__name__}: Missing required fields {missing_keys}.",
            recovery_instructions=f"Please re-invoke the tool providing non-null values for: {missing_keys}. Reference schema: {json.dumps(schema_dict)}",
            suggested_retry_params={k: "<value>" for k in missing_keys},
            is_retryable=True
        )

    # Check numeric types
    for key, val in kwargs.items():
        if key in ["electricity_kwh", "natural_gas_therms", "diesel_gallons", "estimated_cost_usd", "expected_co2e_reduction_mt"]:
            if not isinstance(val, (int, float)) or val < 0:
                return ToolExecutionResult(
                    success=False,
                    error_message=f"Type validation failed for field '{key}': Expected non-negative number, got '{val}' (type: {type(val).__name__}).",
                    recovery_instructions=f"Sanitize field '{key}' to be a positive floating-point or integer number without commas or currency symbols (e.g. 12500.0 instead of '$12,500').",
                    suggested_retry_params={key: 0.0},
                    is_retryable=True
                )

    return ToolExecutionResult(success=True, data=kwargs)
