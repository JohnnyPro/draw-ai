"""
Tool-Call Executor Node

Executes the tool-call (multi-step) drawing strategy.
Wraps the core logic from tool-call.py.
"""

import os
import inspect
from datetime import datetime

from google import genai
from google.genai import types

from graph.state import DrawState

# Import drawing implementations
from primitives.pillow_impl import PillowDrawer
from primitives.svg_impl import SVGDrawer
from primitives.turtle_impl import TurtleDrawer
from primitives import definitions


OUTPUT_DIRECTORY = "./outputs"
DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 800


def _load_primitive_tools():
    """Load drawable functions from definitions module."""
    tools = []
    for name, func in inspect.getmembers(definitions, inspect.isfunction):
        if name.startswith("draw_"):
            tools.append(func)
    return tools


def _create_drawer(backend: str, width: int, height: int):
    """Create the appropriate drawer based on backend."""
    drawers = {
        "pillow": PillowDrawer,
        "svg": SVGDrawer,
        "turtle": TurtleDrawer,
    }
    if backend not in drawers:
        raise ValueError(f"Unknown backend: {backend}")
    return drawers[backend](width, height)


def _execute_drawing_function(drawer, function_name: str, **kwargs):
    """Execute a drawing function on the drawer."""
    func = getattr(drawer, function_name, None)
    if func:
        func(**kwargs)
    else:
        print(f"  [Tool-Call] Warning: Function {function_name} not found in drawer.")


def execute_tool_call(state: DrawState) -> DrawState:
    """
    Execute the tool-call drawing strategy.
    
    Uses LLM function calling for multi-step drawing.
    
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
        
        # Load tools
        primitive_tools = _load_primitive_tools()
        if not primitive_tools:
            raise ValueError("No drawing primitives found.")
        
        # Call LLM with tools
        client = genai.Client()
        response = client.models.generate_content(
            model="models/gemini-latest",
            contents=prompt,
            config=types.GenerateContentConfig(tools=primitive_tools)
        )
        
        # Create drawer
        drawer = _create_drawer(backend, DEFAULT_WIDTH, DEFAULT_HEIGHT)
        
        # Process function calls
        has_calls = False
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    has_calls = True
                    function_call = part.function_call
                    args_dict = {key: value for key, value in function_call.args.items()}
                    print(f"  [Tool-Call] Executing: {function_call.name}({args_dict})")
                    _execute_drawing_function(drawer, function_call.name, **args_dict)
                elif part.text:
                    print(f"  [Tool-Call] LLM said: {part.text}")
        
        if not has_calls:
            raise ValueError("LLM did not return any drawing instructions.")
        
        # Save output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext_map = {"svg": "svg", "turtle": "eps", "pillow": "png"}
        ext = ext_map.get(backend, "png")
        filename = f"graph_tool_call_{timestamp}.{ext}"
        filepath = os.path.join(OUTPUT_DIRECTORY, filename)
        
        drawer.save(filepath)
        
        print(f"  [Tool-Call] ✅ Drawing saved to: {filepath}")
        
        return {
            **state,
            "output_path": filepath,
            "error": None,
        }
        
    except Exception as e:
        print(f"  [Tool-Call] ❌ Error: {e}")
        return {
            **state,
            "output_path": None,
            "error": str(e),
        }
