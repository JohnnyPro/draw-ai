"""
LLM-Driven Programmatic Image Generation (One-Go Version)

A simplified, non-iterative version of the drawing application that:
- Accepts a natural language drawing prompt.
- Uses the Gemini LLM to generate a complete drawing in a single call.
- Reuses the existing drawing backends (SVG, Turtle).
- Outputs a final image file.
"""

import os
import json
import time
import re
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
import google.generativeai as genai

from base_draw import BaseDraw, DrawingConfig
from svg import SVGDraw
from turtle_draw import TurtleDraw

# ============================================================================
# Configuration Parameters
# ============================================================================

MIN_LLM_CALL_INTERVAL_SECONDS = 2.0
DEFAULT_CANVAS_WIDTH = 800
DEFAULT_CANVAS_HEIGHT = 800
DEFAULT_BACKGROUND = "white"
OUTPUT_DIRECTORY = "./outputs"
DEBUG_MODE = True

# Drawing backend selection: "svg" or "turtle"
DRAWING_BACKEND = "turtle"

# ============================================================================
# LLM Abstraction Layer (Copied from main.py)
# ============================================================================


class LLMClient:
    """Abstraction layer for LLM calls with rate limiting."""

    def __init__(self, api_key: str, min_interval: float = MIN_LLM_CALL_INTERVAL_SECONDS):
        self.min_interval = min_interval
        self.last_call_timestamp: Optional[float] = None

        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def _enforce_rate_limit(self) -> None:
        """Sleep if needed to respect rate limits."""
        if self.last_call_timestamp is not None:
            elapsed = time.time() - self.last_call_timestamp
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                if DEBUG_MODE:
                    print(f"  [Rate limit] Sleeping for {sleep_time:.2f}s...")
                time.sleep(sleep_time)

    def call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Make an LLM call with rate limiting."""
        self._enforce_rate_limit()
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        try:
            response = self.model.generate_content(full_prompt)
            self.last_call_timestamp = time.time()
            return response.text
        except Exception as e:
            self.last_call_timestamp = time.time()
            raise RuntimeError(f"LLM call failed: {e}")

# ============================================================================
# Drawing Backend Factory (Copied from main.py)
# ============================================================================


def create_renderer(backend: str, config: DrawingConfig) -> BaseDraw:
    """Factory function to create the appropriate drawing backend."""
    backends = {
        "svg": SVGDraw,
        "turtle": TurtleDraw,
    }
    if backend not in backends:
        raise ValueError(f"Unknown backend: {backend}. Available: {list(backends.keys())}")
    
    renderer = backends[backend](config)
    renderer.initialize()
    return renderer

# ============================================================================
# One-Go Drawing Logic
# ============================================================================


def _extract_code(response: str) -> str:
    """Extract drawing code from LLM response."""
    code_match = re.search(r'```(?:svg|xml|html)?\s*([\s\S]*?)\s*```', response)
    if code_match:
        return code_match.group(1)
    # Look for SVG elements directly as a fallback
    if re.search(r'<(circle|rect|ellipse|line|polyline|polygon|path|text)\s', response, re.IGNORECASE):
        return response
    return response


def generate_one_go(llm_client: LLMClient, user_prompt: str, backend: str) -> str:
    """
    Generates a complete drawing from a prompt in a single LLM call.

    Args:
        llm_client: The LLM client instance.
        user_prompt: The user's drawing description.
        backend: The drawing backend to use ("svg" or "turtle").

    Returns:
        The filepath of the saved drawing.
    """
    print(f"\n[One-Go] Using {backend.upper()} backend to draw: '{user_prompt}'")

    # 1. Create the drawing renderer
    config = DrawingConfig(
        width=DEFAULT_CANVAS_WIDTH,
        height=DEFAULT_CANVAS_HEIGHT,
        background=DEFAULT_BACKGROUND
    )
    renderer = create_renderer(backend, config)

    # 2. Craft the "one-go" prompt
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

User's Request: Draw "{user_prompt}"

Generate the complete set of drawing elements for this entire scene now."""

    # 3. Call the LLM
    if DEBUG_MODE:
        print("  [LLM] Generating full drawing code...")
    
    response_text = llm_client.call_llm(system_prompt, prompt_for_llm)
    drawing_code = _extract_code(response_text)

    if not drawing_code:
        raise ValueError("LLM did not return any drawing code.")

    if DEBUG_MODE:
        print(f"  [LLM] Received {len(drawing_code)} characters of code.")

    # 4. Add the code to the renderer
    elements_added = renderer.add_code("full_drawing", drawing_code)
    print(f"  [Renderer] Added {elements_added} element(s) to the canvas.")

    # 5. Save the output
    drawing_count = len(os.listdir(OUTPUT_DIRECTORY)) + 1
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = "svg" if backend == "svg" else "eps"
    filename = f"one_go_{drawing_count:03d}_{timestamp}.{ext}"
    
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIRECTORY, filename)
    renderer.save(filepath)

    # 6. Handle display and cleanup
    if backend == "turtle":
        print("\nClose the Turtle graphics window to continue.")
        renderer.show()
    
    renderer.cleanup()
    
    return filepath

# ============================================================================
# Main Application
# ============================================================================


def main():
    """Main application entry point."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found. Please set it in your .env file.")
        return

    print("=" * 60)
    print("🖼️  One-Go Drawing Application")
    print("=" * 60)

    llm_client = LLMClient(api_key)

    while True:
        try:
            prompt = input("\nWhat would you like me to draw in one go? (or Ctrl+C to exit)\n> ")
            if not prompt.strip():
                continue

            filepath = generate_one_go(llm_client, prompt, DRAWING_BACKEND)

            print("\n" + "=" * 60)
            print(f"✅ Drawing saved to: {filepath}")
            print("=" * 60)

        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            if DEBUG_MODE:
                import traceback
                traceback.print_exc()
            print("Please try a different prompt.")

if __name__ == "__main__":
    main()
