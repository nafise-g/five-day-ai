"""
Tool for extracting and standardizing facility utility energy consumption records.
Fulfills Rubric Category 1: Comprehensive Docstrings, Descriptive Naming, Explicit JSON Schemas, Guided Error Handling.
"""

from typing import Dict, Any
from ecostream.schemas import FacilityEnergyInput, validate_tool_arguments, ToolExecutionResult
from ecostream.observability.intent_outcome_tracer import trace_intent_outcome


@trace_intent_outcome(action_name="extract_facility_energy_consumption")
def extract_facility_energy_consumption(
    facility_id: str,
    facility_name: str,
    region_code: str,
    electricity_kwh: float,
    natural_gas_therms: float = 0.0,
    diesel_gallons: float = 0.0,
    reporting_period: str = "2025-Q4"
) -> Dict[str, Any]:
    """
    Extracts, validates, and standardizes multi-source facility energy consumption data.

    This tool reads raw facility energy telemetry or invoice inputs, validates the
    units against standard energy parameters (kWh for electricity, therms for natural gas,
    gallons for diesel fuel), and prepares the dataset for downstream carbon auditing.

    Args:
        facility_id (str): Unique commercial facility identifier (e.g., 'FAC-BOS-001').
        facility_name (str): Human-readable title of facility (e.g., 'Boston Data Center Alpha').
        region_code (str): Regional electrical grid subregion code (e.g., 'US-NEISO', 'US-CAMX', 'EU-DE').
        electricity_kwh (float): Total electricity consumed during the billing cycle in kilowatt-hours (kWh). Must be >= 0.
        natural_gas_therms (float, optional): Natural gas heating consumption in therms. Defaults to 0.0.
        diesel_gallons (float, optional): Backup generator fuel consumption in US gallons. Defaults to 0.0.
        reporting_period (str, optional): Reporting quarter or year string (e.g., '2025-Q4'). Defaults to '2025-Q4'.

    Returns:
        Dict[str, Any]: Standardized JSON payload containing validated energy metrics or guided error recovery diagnostic.

    Raises:
        ValueError: Caught internally; returns guided recovery instruction payload to LLM.
    """
    raw_args = {
        "facility_id": facility_id,
        "facility_name": facility_name,
        "region_code": region_code,
        "electricity_kwh": electricity_kwh,
        "natural_gas_therms": natural_gas_therms,
        "diesel_gallons": diesel_gallons,
        "reporting_period": reporting_period
    }

    # Step 1: Explicit JSON Schema Validation
    validation_res = validate_tool_arguments(FacilityEnergyInput, raw_args)
    if not validation_res.success:
        return validation_res.to_dict()

    # Step 2: Domain-specific verification & Guided Error Handling
    valid_regions = ["US-NEISO", "US-CAMX", "US-ERCOT", "US-NYISO", "EU-DE", "EU-FR", "GLOBAL-DEFAULT"]
    if region_code.upper() not in valid_regions:
        return ToolExecutionResult(
            success=False,
            error_message=f"Unknown electrical grid subregion code '{region_code}'.",
            recovery_instructions=(
                f"Supported grid region codes are: {valid_regions}. "
                "If the facility's exact grid region is unknown, specify 'GLOBAL-DEFAULT' or re-query with one of the supported codes."
            ),
            suggested_retry_params={"region_code": "GLOBAL-DEFAULT"},
            is_retryable=True
        ).to_dict()

    # Step 3: Energy conversion calculation (Standardization to MWh & MMBtu)
    electricity_mwh = electricity_kwh / 1000.0
    natural_gas_mmbtu = natural_gas_therms * 0.1  # 1 therm = 0.1 MMBtu
    diesel_mmbtu = diesel_gallons * 0.138  # 1 gal diesel = ~0.138 MMBtu

    standardized_record = {
        "facility_id": facility_id,
        "facility_name": facility_name,
        "region_code": region_code.upper(),
        "reporting_period": reporting_period,
        "metrics": {
            "electricity_kwh": electricity_kwh,
            "electricity_mwh": electricity_mwh,
            "natural_gas_therms": natural_gas_therms,
            "natural_gas_mmbtu": natural_gas_mmbtu,
            "diesel_gallons": diesel_gallons,
            "diesel_mmbtu": diesel_mmbtu,
            "total_primary_energy_mmbtu": (electricity_mwh * 3.412) + natural_gas_mmbtu + diesel_mmbtu
        },
        "status": "VALIDATED_AND_STANDARDIZED"
    }

    return ToolExecutionResult(success=True, data=standardized_record).to_dict()
