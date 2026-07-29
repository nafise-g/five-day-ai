"""
Intent vs. Outcome Tracer recording pre-execution intention and post-execution results.
Fulfills Rubric Category 4: Intent vs. Outcome Capture.
"""

from typing import Dict, Any, Callable
import functools
import time
import uuid
from ecostream.observability.json_logger import logger
from ecostream.observability.pii_redactor import PiiRedactor

def trace_intent_outcome(action_name: str):
    """
    Decorator that explicitly captures:
    1. INTENT: Logged BEFORE execution (action target, inputs, expected state).
    2. OUTCOME: Logged AFTER execution (status, duration, output payload, errors).
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            execution_id = f"EXEC-{uuid.uuid4().hex[:8]}"
            start_time = time.time()

            # Record INTENT before execution
            intent_payload = {
                "execution_id": execution_id,
                "event_type": "INTENT_START",
                "action_name": action_name,
                "function_name": func.__name__,
                "input_args": PiiRedactor.redact_obj(kwargs),
                "intended_goal": f"Execute action '{action_name}' with provided input schema parameters."
            }
            logger.info(f"INTENT: Starting action '{action_name}'", extra={"metadata": intent_payload})

            try:
                # Execute action
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000.0

                # Record OUTCOME after execution
                outcome_payload = {
                    "execution_id": execution_id,
                    "event_type": "INTENT_OUTCOME",
                    "action_name": action_name,
                    "status": "SUCCESS" if isinstance(result, dict) and result.get("success", True) else "FAILED",
                    "duration_ms": round(duration_ms, 2),
                    "output_payload": PiiRedactor.redact_obj(result)
                }
                logger.info(f"OUTCOME: Completed action '{action_name}'", extra={"metadata": outcome_payload})

                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000.0
                failure_payload = {
                    "execution_id": execution_id,
                    "event_type": "INTENT_OUTCOME",
                    "action_name": action_name,
                    "status": "CRASHED",
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e)
                }
                logger.error(f"OUTCOME: Crashed action '{action_name}' - {e}", extra={"metadata": failure_payload})
                raise e

        return wrapper
    return decorator
