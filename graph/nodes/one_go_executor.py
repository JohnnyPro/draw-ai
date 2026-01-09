"""
One-Go Executor Node

Executes the one-go (single-call) drawing strategy.
Wraps the core logic from one-go.py.
"""

import os
import re
from datetime import datetime

from google import genai

from graph.state import DrawState

# Import existing drawing infrastructure
from base_draw import DrawingConfig
from svg import SVGDraw
from turtle_draw import TurtleDraw
from pillow_draw import PillowDraw


OUTPUT_DIRECTORY = "./outputs"
DEFAULT_CANVAS_WIDTH = 800
DEFAULT_CANVAS_HEIGHT = 800
DEFAULT_BACKGROUND = "white"


def _create_renderer(backend: str, config: DrawingConfig):
    """Factory function to create the appropriate drawing backend."""
    backends = {
        "svg": SVGDraw,
        "turtle": TurtleDraw,
        "pillow": PillowDraw,
    }
    if backend not in backends:
        raise ValueError(f"Unknown backend: {backend}")
    
    renderer = backends[backend](config)
    renderer.initialize()
    return renderer


def _extract_code(response: str) -> str:
    """Extract drawing code from LLM response."""
    code_match = re.search(r'```(?:svg|xml|html|python)?\s*([\s\S]*?)\s*```', response)
    if code_match:
        return code_match.group(1)
    if re.search(r'<(circle|rect|ellipse|line|polyline|polygon|path|text)\s', response, re.IGNORECASE):
        return response
    return response


def execute_one_go(state: DrawState) -> DrawState:
    """
    Execute the one-go drawing strategy.
    
    Uses a single LLM call to generate the entire drawing.
    
    Expects:
        - refined_prompt or original_prompt
        - backend
    
    Sets:
        - output_path
        - error (if failed)
    """
    prompt = state.get("refined_prompt") or state.get("original_prompt", "")
    backend = state.get("backend", "pillow")
    
    try:
        os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
        
        # Create renderer
        config = DrawingConfig(
            width=DEFAULT_CANVAS_WIDTH,
            height=DEFAULT_CANVAS_HEIGHT,
            background=DEFAULT_BACKGROUND
        )
        renderer = _create_renderer(backend, config)
        
        # Build prompts
        backend_instructions = renderer.system_prompt_instructions
        
        system_prompt = f"""You are an expert drawing AI that generates a complete drawing in one go.
Your task is to generate a set of raw drawing elements based on the user's request.
{backend_instructions}

- You MUST generate ALL the elements for the entire drawing at once.
- Do NOT use multiple stages, objects, or iterations.
- Your output should be ONLY the raw drawing elements, not a full script or file.
- The coordinate system is a {config.width}x{config.height} canvas with (0,0) at the top-left."""

        prompt_for_llm = f"""Canvas Dimensions: {config.width}x{config.height}
Background Color: {config.background}
Drawing Backend: {renderer.backend_name}

User's Request: Draw "{prompt}"

Generate the complete set of drawing elements for this entire scene now."""

        # Call LLM
        client = genai.Client()
        response = client.models.generate_content(
            model="models/gemini-latest",
            contents=f"{system_prompt}\n\n{prompt_for_llm}",
        )
        
        drawing_code = _extract_code(response.text)
        if not drawing_code:
            raise ValueError("LLM did not return any drawing code.")
        
        # Add code to renderer
        elements_added = renderer.add_code("full_drawing", drawing_code)
        print(f"  [One-Go] Added {elements_added} element(s) to the canvas.")
        
        # Save output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext_map = {"svg": "svg", "turtle": "eps", "pillow": "png"}
        ext = ext_map.get(backend, "png")
        filename = f"graph_one_go_{timestamp}.{ext}"
        filepath = os.path.join(OUTPUT_DIRECTORY, filename)
        
        renderer.save(filepath)
        renderer.cleanup()
        
        print(f"  [One-Go] ✅ Drawing saved to: {filepath}")
        
        return {
            **state,
            "output_path": filepath,
            "error": None,
        }
        
    except Exception as e:
        print(f"  [One-Go] ❌ Error: {e}")
        return {
            **state,
            "output_path": None,
            "error": str(e),
        }
