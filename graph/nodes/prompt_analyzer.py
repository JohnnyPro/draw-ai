"""
Prompt Analyzer Node

Analyzes the user's prompt for clarity and determines if clarification is needed.
"""

import re
from google import genai

from graph.state import DrawState


# Indicators of vague prompts
VAGUE_PATTERNS = [
    r"\bsomething\b",
    r"\banything\b",
    r"\bcool\b",
    r"\bnice\b",
    r"\brandom\b",
    r"\bwhatever\b",
]


def _get_analysis_prompt(user_prompt: str) -> str:
    """Create the analysis prompt for the LLM."""
    return f"""Analyze this drawing request and determine its clarity.

User's request: "{user_prompt}"

Rate the clarity from 0.0 to 1.0 where:
- 1.0 = Crystal clear, specific, actionable (e.g., "a red circle in the center")
- 0.7-0.9 = Mostly clear with minor ambiguity
- 0.4-0.6 = Somewhat vague, could use clarification
- 0.0-0.3 = Very vague or contradictory

If the request is unclear (score < 0.8), provide ONE specific clarifying question.

Respond in this exact format:
CONFIDENCE: <number between 0.0 and 1.0>
NEEDS_CLARIFICATION: <true or false>
QUESTION: <clarifying question if needed, or "none">
REFINED_PROMPT: <a cleaner version of the prompt if possible, or the original>"""


def _parse_analysis_response(response: str, original_prompt: str) -> dict:
    """Parse the LLM's analysis response."""
    result = {
        "confidence": 0.5,
        "needs_clarification": True,
        "clarification_question": None,
        "refined_prompt": original_prompt,
    }
    
    lines = response.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("CONFIDENCE:"):
            try:
                result["confidence"] = float(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("NEEDS_CLARIFICATION:"):
            value = line.split(":", 1)[1].strip().lower()
            result["needs_clarification"] = value == "true"
        elif line.startswith("QUESTION:"):
            question = line.split(":", 1)[1].strip()
            if question.lower() != "none":
                result["clarification_question"] = question
        elif line.startswith("REFINED_PROMPT:"):
            result["refined_prompt"] = line.split(":", 1)[1].strip()
    
    return result


def _quick_vagueness_check(prompt: str) -> bool:
    """Quick regex-based check for obviously vague prompts."""
    prompt_lower = prompt.lower()
    for pattern in VAGUE_PATTERNS:
        if re.search(pattern, prompt_lower):
            return True
    return len(prompt.split()) < 3


def analyze_prompt(state: DrawState) -> DrawState:
    """
    Analyze the user's prompt for clarity.
    
    Sets:
        - confidence: float (0-1)
        - needs_clarification: bool
        - clarification_question: str | None
        - refined_prompt: str | None
    """
    original_prompt = state.get("original_prompt", "")
    
    # Quick check for obviously vague prompts
    if _quick_vagueness_check(original_prompt):
        return {
            **state,
            "confidence": 0.3,
            "needs_clarification": True,
            "clarification_question": "Could you be more specific about what you'd like me to draw?",
            "refined_prompt": original_prompt,
        }
    
    # Use LLM for deeper analysis
    try:
        client = genai.Client()
        response = client.models.generate_content(
            model="models/gemini-latest",
            contents=_get_analysis_prompt(original_prompt),
        )
        
        analysis = _parse_analysis_response(response.text, original_prompt)
        
        return {
            **state,
            "confidence": analysis["confidence"],
            "needs_clarification": analysis["needs_clarification"],
            "clarification_question": analysis["clarification_question"],
            "refined_prompt": analysis["refined_prompt"],
        }
        
    except Exception as e:
        # On error, be conservative and ask for clarification
        print(f"Warning: Prompt analysis failed: {e}")
        return {
            **state,
            "confidence": 0.5,
            "needs_clarification": True,
            "clarification_question": "Could you please describe what you'd like me to draw in more detail?",
            "refined_prompt": original_prompt,
        }
