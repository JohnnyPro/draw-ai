"""
State definition for the DrawAI LangGraph.
"""

from typing import TypedDict, Literal, Any


class DrawState(TypedDict, total=False):
    """
    State object that flows through the LangGraph.
    
    All fields are optional (total=False) to allow incremental updates.
    """
    # Input
    original_prompt: str
    
    # Prompt Refinement
    refined_prompt: str | None
    confidence: float | None
    needs_clarification: bool
    clarification_question: str | None
    
    # Strategy & Backend Selection
    strategy: Literal["one-go", "tool-call"] | None
    backend: Literal["pillow", "svg", "turtle"]
    backend_reason: str | None
    
    # Execution
    drawing_plan: dict[str, Any] | None
    output_path: str | None
    
    # Metadata
    error: str | None
