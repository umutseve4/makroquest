"""Case engine (M1.6).

A case is defined in a YAML template (`data/cases/*.yaml`) and played as
start -> evidence -> hint -> answer -> score. The engine is pure Python;
the API layer wires it to FastAPI and the RAG hint agent.
"""

from makroquest.cases.engine import CaseEngine, SessionError
from makroquest.cases.loader import Case, CaseValidationError, load_case, load_cases

__all__ = [
    "Case",
    "CaseEngine",
    "CaseValidationError",
    "SessionError",
    "load_case",
    "load_cases",
]
