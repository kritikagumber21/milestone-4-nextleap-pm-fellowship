import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.guardrails import check_guardrails

assert check_guardrails("should I buy HDFC large cap?")["action"] == "refuse_advice"
assert check_guardrails("which fund gave higher returns?")["action"] == "refuse_performance"
assert check_guardrails("My PAN is ABCDE1234F")["action"] == "refuse_pii"
assert check_guardrails("expense ratio of HDFC Large Cap")["action"] == "allow"

print("guardrail checks passed")
