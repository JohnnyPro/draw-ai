"""
Backend Router Node

Routes to the appropriate drawing backend (Pillow, SVG, Turtle).
Default is Pillow unless user explicitly requests otherwise.
"""

import re

from graph.state import DrawState


# Keywords for explicit backend requests
SVG_KEYWORDS = [
    "svg", "vector", "scalable", "icon", "logo", "diagram",
    "geometric", "sharp", "crisp", "clean lines",
]

TURTLE_KEYWORDS = [
    "turtle", "animation", "step by step", "step-by-step",
    "educational", "learn", "teaching", "show how",
]


def _detect_explicit_backend(prompt: str) -> tuple[str, str] | None:
    """
    Detect if user explicitly requested a specific backend.
    Returns (backend, reason) or None.
    """
    prompt_lower = prompt.lower()
    
    # Check for explicit turtle request (user must really want it)
    for kw in TURTLE_KEYWORDS:
        if kw in prompt_lower:
            return ("turtle", f"User requested turtle-style (keyword: '{kw}')")
    
    # Check for SVG hints
    for kw in SVG_KEYWORDS:
        if kw in prompt_lower:
            return ("svg", f"User requested vector/SVG style (keyword: '{kw}')")
    
    return None


def route_backend(state: DrawState) -> DrawState:
    """
    Route to the appropriate drawing backend.
    
    Priority:
    1. Explicit user request (turtle keywords, SVG keywords)
    2. Default to Pillow (best outcomes for most drawings)
    
    Sets:
        - backend: Literal["pillow", "svg", "turtle"]
        - backend_reason: str
    """
    prompt = state.get("refined_prompt") or state.get("original_prompt", "")
    
    # Check for explicit backend request
    explicit = _detect_explicit_backend(prompt)
    if explicit:
        backend, reason = explicit
        return {
            **state,
            "backend": backend,
            "backend_reason": reason,
        }
    
    # Default to Pillow - it has the best outcomes for most drawings
    return {
        **state,
        "backend": "pillow",
        "backend_reason": "Default backend (best for most drawings)",
    }
