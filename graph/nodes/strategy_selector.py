"""
Strategy Selector Node

Decides between one-go (fast, single-call) and tool-call (multi-step) strategies.
"""

from google import genai

from graph.state import DrawState


# Keywords that suggest simple drawings (one-go)
SIMPLE_KEYWORDS = [
    "circle", "square", "rectangle", "triangle", "line",
    "dot", "oval", "ellipse", "star", "heart",
    "arrow", "cross", "plus", "minus",
]

# Keywords that suggest complex drawings (tool-call)
COMPLEX_KEYWORDS = [
    "scene", "landscape", "portrait", "house", "building",
    "person", "animal", "face", "tree", "forest",
    "city", "room", "garden", "ocean", "mountain",
    "detailed", "realistic", "complex", "multiple",
]


def _quick_complexity_check(prompt: str) -> str | None:
    """
    Quick keyword-based check for obvious cases.
    Returns "one-go", "tool-call", or None if uncertain.
    """
    prompt_lower = prompt.lower()
    words = prompt_lower.split()
    
    # Check for explicit complexity indicators
    if any(kw in prompt_lower for kw in COMPLEX_KEYWORDS):
        return "tool-call"
    
    # Check for simple geometric shapes
    simple_count = sum(1 for kw in SIMPLE_KEYWORDS if kw in prompt_lower)
    if simple_count > 0 and len(words) < 10:
        return "one-go"
    
    return None


def _get_strategy_prompt(user_prompt: str) -> str:
    """Create the strategy selection prompt for the LLM."""
    return f"""Classify this drawing request by complexity.

Request: "{user_prompt}"

Choose ONE strategy:
- ONE-GO: For simple shapes, basic geometric figures, single objects, quick sketches
- TOOL-CALL: For complex scenes, multiple objects, detailed artwork, compositions

Respond with ONLY one word: ONE-GO or TOOL-CALL"""


def select_strategy(state: DrawState) -> DrawState:
    """
    Select the drawing strategy based on prompt complexity.
    
    Sets:
        - strategy: Literal["one-go", "tool-call"]
    """
    prompt = state.get("refined_prompt") or state.get("original_prompt", "")
    
    # Try quick check first
    quick_result = _quick_complexity_check(prompt)
    if quick_result:
        return {
            **state,
            "strategy": quick_result,
        }
    
    # Use LLM for uncertain cases
    try:
        client = genai.Client()
        response = client.models.generate_content(
            model="models/gemini-flash-latest",
            contents=_get_strategy_prompt(prompt),
        )
        
        result = response.text.strip().upper()
        
        if "ONE-GO" in result or "ONEGO" in result:
            strategy = "one-go"
        elif "TOOL-CALL" in result or "TOOLCALL" in result:
            strategy = "tool-call"
        else:
            # Default to one-go for speed
            strategy = "one-go"
        
        return {
            **state,
            "strategy": strategy,
        }
        
    except Exception as e:
        # On error, default to one-go (faster, simpler)
        print(f"Warning: Strategy selection failed: {e}")
        return {
            **state,
            "strategy": "one-go",
        }
