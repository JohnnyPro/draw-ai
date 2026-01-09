"""
LLM-Driven Programmatic Image Generation (One-Go Version)

A simplified, non-iterative version of the drawing application that:
- Accepts a natural language drawing prompt.
- Uses the Gemini LLM to generate a complete drawing in a single call.
- Reuses the existing drawing backends (SVG, Turtle, Pillow).
- Outputs a final image file.
- Includes a live viewer for SVG and Pillow backends.
"""

import os
import re
import atexit
from datetime import datetime
from typing import Optional

from google import genai

from base_draw import BaseDraw, DrawingConfig
from svg import SVGDraw
from turtle_draw import TurtleDraw
from pillow_draw import PillowDraw
from live_viewer import LiveViewer

# ============================================================================
# Configuration Parameters
# ============================================================================

MIN_LLM_CALL_INTERVAL_SECONDS = 2.0
DEFAULT_CANVAS_WIDTH = 800
DEFAULT_CANVAS_HEIGHT = 800
DEFAULT_BACKGROUND = "white"
OUTPUT_DIRECTORY = "./outputs"
DEBUG_MODE = True

# Drawing backend selection: "svg", "turtle", or "pillow"
DRAWING_BACKEND = "pillow"

# ============================================================================
# LLM Abstraction Layer (Copied from main.py)
# ============================================================================


class LLMClient:
    """Abstraction layer for LLM calls with rate limiting."""

    def __init__(self, min_interval: float = MIN_LLM_CALL_INTERVAL_SECONDS):
        self.min_interval = min_interval
        self.last_call_timestamp: Optional[float] = None
        self.client = genai.Client()

    def _enforce_rate_limit(self) -> None:
        if self.last_call_timestamp is not None:
            elapsed = datetime.now().timestamp() - self.last_call_timestamp
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                if DEBUG_MODE:
                    print(f"  [Rate limit] Sleeping for {sleep_time:.2f}s...")
                time.sleep(sleep_time)

    def call_llm(self, system_prompt: str, user_prompt: str) -> str:
        self._enforce_rate_limit()
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        try:
            response = self.client.models.generate_content(
                model="models/gemini-flash-latest",
                contents=full_prompt
            )
            self.last_call_timestamp = datetime.now().timestamp()
            return response.text
        except Exception as e:
            self.last_call_timestamp = datetime.now().timestamp()
            raise RuntimeError(f"LLM call failed: {e}")

# ============================================================================
# Drawing Backend Factory
# ============================================================================


def create_renderer(backend: str, config: DrawingConfig) -> BaseDraw:
    """Factory function to create the appropriate drawing backend."""
    backends = {
        "svg": SVGDraw,
        "turtle": TurtleDraw,
        "pillow": PillowDraw,
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
    code_match = re.search(r'```(?:svg|xml|html|python)?\s*([\s\S]*?)\s*```', response)
    if code_match:
        return code_match.group(1)
    if re.search(r'<(circle|rect|ellipse|line|polyline|polygon|path|text)\s', response, re.IGNORECASE):
        return response
    return response


def generate_one_go(llm_client: LLMClient, user_prompt: str, backend: str, live_preview_filepath: Optional[str] = None) -> str:
    """
    Generates a complete drawing from a prompt in a single LLM call.
    """
    print(f"\n[One-Go] Using {backend.upper()} backend to draw: '{user_prompt}'")

    # 1. Create the drawing renderer
    config = DrawingConfig(width=DEFAULT_CANVAS_WIDTH, height=DEFAULT_CANVAS_HEIGHT, background=DEFAULT_BACKGROUND)
    renderer = create_renderer(backend, config)

    # Create an initial empty file for the live viewer
    if live_preview_filepath:
        renderer.save(live_preview_filepath)

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

    # 4. Add the code to the renderer and update live view
    elements_added = renderer.add_code("full_drawing", drawing_code)
    print(f"  [Renderer] Added {elements_added} element(s) to the canvas.")
    if live_preview_filepath:
        renderer.save(live_preview_filepath)

    # 5. Save the final output
    file_count = len([name for name in os.listdir(OUTPUT_DIRECTORY) if name.startswith("one_go_")])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    ext_map = {"svg": "svg", "turtle": "eps", "pillow": "png"}
    ext = ext_map.get(backend, "png")
    filename = f"one_go_{file_count + 1:03d}_{timestamp}.{ext}"
    
    filepath = os.path.join(OUTPUT_DIRECTORY, filename)
    renderer.save(filepath)

    # 6. Handle display and cleanup
    if backend == "turtle":
        print("\nClose the Turtle graphics window to continue.")
        renderer.show()
    elif backend == "pillow":
        renderer.show() # Open in default image viewer
    
    renderer.cleanup()
    
    return filepath

# ============================================================================
# Main Application
# ============================================================================


def main():
    """Main application entry point."""
    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not found. Please set it in your .env file.")
        return

    print("=" * 60)
    print(f"🖼️  One-Go Drawing Application ({DRAWING_BACKEND.upper()} backend)")
    print("=" * 60)

    llm_client = LLMClient()

    # --- Live Viewer Setup ---
    live_preview_filepath = None
    if DRAWING_BACKEND in ["svg", "pillow"]:
        ext_map = {"svg": "svg", "pillow": "png"}
        ext = ext_map[DRAWING_BACKEND]
        LIVE_FILENAME = f"live_drawing.{ext}"
        LIVE_VIEWER_PORT = 8008
        
        os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
        
        live_viewer = LiveViewer(LIVE_VIEWER_PORT, OUTPUT_DIRECTORY, LIVE_FILENAME)
        live_viewer.start()
        atexit.register(live_viewer.stop)
        
        live_preview_filepath = os.path.join(OUTPUT_DIRECTORY, LIVE_FILENAME)

    while True:
        try:
            prompt = input("\nWhat would you like me to draw in one go? (or Ctrl+C to exit)\n> ")
            if not prompt.strip():
                continue

            filepath = generate_one_go(llm_client, prompt, DRAWING_BACKEND, live_preview_filepath)

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
