"""
LLM-Driven Programmatic Image Generation

An AI-powered drawing application that:
- Accepts natural language drawing prompts
- Uses Gemini LLM to create high-level drawing plans and generate drawing code
- Supports multiple drawing backends (SVG, Turtle) via the BaseDraw interface
- Maintains explicit drawing state with controlled iteration
- Outputs image files
"""

import os
import json
import time
import re
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum
import atexit

from dotenv import load_dotenv
import google.generativeai as genai

from base_draw import BaseDraw, DrawingConfig
from svg import SVGDraw
from turtle_draw import TurtleDraw
from live_viewer import LiveViewer


# ============================================================================
# Configuration Parameters
# ============================================================================

MAX_ITERATIONS = 30
MIN_LLM_CALL_INTERVAL_SECONDS = 2.0
DEFAULT_CANVAS_WIDTH = 800
DEFAULT_CANVAS_HEIGHT = 800
OUTPUT_DIRECTORY = "./outputs"
DEBUG_MODE = True

# Drawing backend selection: "svg" or "turtle"
DRAWING_BACKEND = "turtle"

# ============================================================================
# Enums and Data Classes
# ============================================================================


class ObjectStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class DrawingStage(Enum):
    LAYOUT = "layout"
    RENDER = "render"  # Combined main shapes + details


@dataclass
class BoundingBox:
    x_min: float = 0
    y_min: float = 0
    x_max: float = 0
    y_max: float = 0

    def to_dict(self) -> dict:
        return {
            "x_min": self.x_min,
            "y_min": self.y_min,
            "x_max": self.x_max,
            "y_max": self.y_max,
        }


@dataclass
class AnchorPoints:
    start: tuple[float, float] = (0, 0)
    end: tuple[float, float] = (0, 0)

    def to_dict(self) -> dict:
        return {"start": list(self.start), "end": list(self.end)}


@dataclass
class ObjectState:
    id: str
    obj_type: str
    description: str
    approx_position: str
    size: str
    status: ObjectStatus = ObjectStatus.NOT_STARTED
    bounding_box: BoundingBox = field(default_factory=BoundingBox)
    anchor_points: AnchorPoints = field(default_factory=AnchorPoints)
    iteration_count: int = 0
    current_stage: DrawingStage = DrawingStage.LAYOUT

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.obj_type,
            "description": self.description,
            "approx_position": self.approx_position,
            "size": self.size,
            "status": self.status.value,
            "bounding_box": self.bounding_box.to_dict(),
            "anchor_points": self.anchor_points.to_dict(),
            "iteration_count": self.iteration_count,
            "current_stage": self.current_stage.value,
        }


@dataclass
class DrawingPlan:
    canvas_width: int
    canvas_height: int
    background: str
    objects: list[dict]
    composition: str
    style: str


@dataclass
class DrawingState:
    plan: DrawingPlan
    object_states: dict[str, ObjectState]
    current_stage: DrawingStage = DrawingStage.LAYOUT
    total_iterations: int = 0
    element_count: int = 0

    def to_dict(self) -> dict:
        return {
            "canvas": {
                "width": self.plan.canvas_width,
                "height": self.plan.canvas_height,
            },
            "current_stage": self.current_stage.value,
            "total_iterations": self.total_iterations,
            "element_count": self.element_count,
            "objects": {
                obj_id: obj.to_dict() for obj_id, obj in self.object_states.items()
            },
        }


# ============================================================================
# LLM Abstraction Layer
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
# Drawing Backend Factory
# ============================================================================


def create_renderer(backend: str, config: DrawingConfig) -> BaseDraw:
    """
    Factory function to create the appropriate drawing backend.
    
    Args:
        backend: Backend name ("svg" or "turtle")
        config: Drawing configuration
        
    Returns:
        A BaseDraw implementation instance
    """
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
# Drawing Controller
# ============================================================================


class DrawingController:
    """Controls the iterative drawing process using any BaseDraw backend."""

    def __init__(self, llm_client: LLMClient, backend: str = DRAWING_BACKEND, live_preview_filepath: Optional[str] = None):
        self.llm_client = llm_client
        self.backend = backend
        self.state: Optional[DrawingState] = None
        self.renderer: Optional[BaseDraw] = None
        self.live_preview_filepath = live_preview_filepath

    def create_plan(self, user_prompt: str) -> DrawingPlan:
        """Create a high-level drawing plan from user prompt."""
        system_prompt = """You are an AI assistant that creates structured drawing plans.
You MUST respond with ONLY valid JSON, no other text.

IMPORTANT RULES:
1. MINIMIZE the number of objects. Only include objects the user EXPLICITLY asked for.
2. If the user asks for "a cat", create ONE object called "cat" - do NOT split into separate objects for eyes, ears, body, etc.
3. Prefer SINGLE OBJECT drawings. Only add multiple objects if the user explicitly mentions them (e.g., "a cat and a dog").
4. Each object MUST have explicit bounding_box coordinates in pixels.

Create a drawing plan with the following structure:
{
    "canvas": {
        "width": <number, typically 800>,
        "height": <number, typically 800>,
        "background": "<color (use valid SVG/CSS color names with no spaces, e.g., 'skyblue' or Hex codes like '#87CEEB')>"
    },
    "objects": [
        {
            "id": "<unique_id>",
            "type": "<object_type>",
            "description": "<detailed description including all features like eyes, ears, etc.>",
            "bounding_box": {
                "x": <left edge x coordinate in pixels>,
                "y": <top edge y coordinate in pixels>,
                "width": <width in pixels>,
                "height": <height in pixels>
            }
        }
    ],
    "composition": "<how objects relate to each other, or 'single object' if only one>",
    "style": "<art style description>"
}

Remember: FEWER OBJECTS IS BETTER. Combine related parts into single objects.
Use simple, descriptive IDs like "cat", "tree", "house".
"""

        user_msg = f"Create a drawing plan for: {user_prompt}"

        if DEBUG_MODE:
            print("\n[Planning] Generating drawing plan...")

        response = self.llm_client.call_llm(system_prompt, user_msg)

        # Extract JSON from response
        plan_dict = self._extract_json(response)

        if plan_dict is None:
            # Retry once
            if DEBUG_MODE:
                print("  [Retry] Invalid JSON, retrying...")
            response = self.llm_client.call_llm(system_prompt, user_msg)
            plan_dict = self._extract_json(response)

        if plan_dict is None:
            raise ValueError("Failed to get valid JSON plan from LLM")

        # Create DrawingPlan
        canvas = plan_dict.get("canvas", {})
        return DrawingPlan(
            canvas_width=canvas.get("width", DEFAULT_CANVAS_WIDTH),
            canvas_height=canvas.get("height", DEFAULT_CANVAS_HEIGHT),
            background=canvas.get("background", "white"),
            objects=plan_dict.get("objects", []),
            composition=plan_dict.get("composition", ""),
            style=plan_dict.get("style", "simple"),
        )

    def _extract_json(self, response: str) -> Optional[dict]:
        """Extract JSON from LLM response."""
        # Try to find JSON in the response
        # First, try parsing the whole response
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try to find JSON block in markdown
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find raw JSON object
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def initialize_state(self, plan: DrawingPlan) -> None:
        """Initialize drawing state from plan."""
        object_states = {}
        for obj in plan.objects:
            # Parse bounding box from plan if provided
            bbox_data = obj.get("bounding_box", {})
            bbox = BoundingBox(
                x_min=bbox_data.get("x", 0),
                y_min=bbox_data.get("y", 0),
                x_max=bbox_data.get("x", 0) + bbox_data.get("width", 200),
                y_max=bbox_data.get("y", 0) + bbox_data.get("height", 200),
            )
            
            object_states[obj["id"]] = ObjectState(
                id=obj["id"],
                obj_type=obj.get("type", "object"),
                description=obj.get("description", ""),
                approx_position=obj.get("approx_position", "center"),
                size=obj.get("size", "medium"),
                bounding_box=bbox,
            )

        self.state = DrawingState(plan=plan, object_states=object_states)
        
        # Create renderer using factory
        config = DrawingConfig(
            width=plan.canvas_width,
            height=plan.canvas_height,
            background=plan.background,
        )
        self.renderer = create_renderer(self.backend, config)
        
        # Create an empty drawing for the live viewer to start with
        if self.live_preview_filepath and self.renderer:
            self.renderer.save(self.live_preview_filepath)

    def run_drawing_loop(self) -> None:
        """Execute the main drawing loop."""
        if self.state is None or self.renderer is None:
            raise RuntimeError("State not initialized")

        stages = [DrawingStage.LAYOUT, DrawingStage.RENDER]

        for stage in stages:
            self.state.current_stage = stage

            if DEBUG_MODE:
                print(f"\n[Stage] {stage.value.upper()}")

            for obj_id, obj_state in self.state.object_states.items():
                if self.state.total_iterations >= MAX_ITERATIONS:
                    if DEBUG_MODE:
                        print(f"  [Warning] Max iterations ({MAX_ITERATIONS}) reached")
                    return

                if obj_state.status == ObjectStatus.COMPLETED:
                    continue

                obj_state.current_stage = stage
                obj_state.status = ObjectStatus.IN_PROGRESS

                success = self._generate_object_stage(obj_id, obj_state, stage)

                if success:
                    obj_state.iteration_count += 1
                    self.state.total_iterations += 1

                    # Mark as completed after render stage
                    if stage == DrawingStage.RENDER:
                        obj_state.status = ObjectStatus.COMPLETED

                # Update element count from renderer
                self.state.element_count = self.renderer.element_count

                if DEBUG_MODE:
                    print(
                        f"    Elements: {self.state.element_count}, "
                        f"Iterations: {self.state.total_iterations}"
                    )

    def _generate_object_stage(
        self, obj_id: str, obj_state: ObjectState, stage: DrawingStage
    ) -> bool:
        """Generate drawing code for an object at a specific stage."""
        # Get backend-specific system prompt instructions
        backend_instructions = self.renderer.system_prompt_instructions
        
        system_prompt = f"""{backend_instructions}

Canvas size: {self.state.plan.canvas_width}x{self.state.plan.canvas_height} pixels

Stage instructions:
- LAYOUT: Draw a simple outline/placeholder within the bounding box to establish the object's position
- RENDER: Draw the COMPLETE object with ALL features and details, staying within the bounding box coordinates
"""

        # Get bounding box info
        bbox = obj_state.bounding_box
        bbox_info = f"""Bounding Box (MUST draw within these coordinates):
- Left (x): {bbox.x_min}
- Top (y): {bbox.y_min}
- Right: {bbox.x_max}
- Bottom: {bbox.y_max}
- Width: {bbox.x_max - bbox.x_min}
- Height: {bbox.y_max - bbox.y_min}
- Center X: {(bbox.x_min + bbox.x_max) / 2}
- Center Y: {(bbox.y_min + bbox.y_max) / 2}"""

        user_prompt = f"""Generate drawing code for object: {obj_id}
Current stage: {stage.value}

Object details:
- Type: {obj_state.obj_type}
- Description: {obj_state.description}

{bbox_info}

Drawing composition: {self.state.plan.composition}
Style: {self.state.plan.style}

CRITICAL: All shapes MUST be positioned within the bounding box coordinates above.
Generate drawing code ONLY for this object and stage. Output raw SVG-like elements only."""

        if DEBUG_MODE:
            print(f"  [Drawing] {obj_id} - {stage.value}")

        try:
            response = self.llm_client.call_llm(system_prompt, user_prompt)

            # Extract code from response
            code = self._extract_code(response)

            if code:
                elements_added = self.renderer.add_code(obj_id, code)
                if DEBUG_MODE:
                    print(f"    Added {elements_added} element(s)")

                # Update bounding box estimate based on position
                self._update_bounding_box(obj_state)
                
                # Update live preview
                if self.live_preview_filepath and self.renderer:
                    self.renderer.save(self.live_preview_filepath)

                return elements_added > 0
            else:
                if DEBUG_MODE:
                    print("    No valid code found in response")
                return False

        except Exception as e:
            if DEBUG_MODE:
                print(f"    Error: {e}")
            return False

    def _extract_code(self, response: str) -> str:
        """Extract drawing code from LLM response."""
        # Try to find code in code blocks
        code_match = re.search(r'```(?:svg|xml|html)?\s*([\s\S]*?)\s*```', response)
        if code_match:
            return code_match.group(1)

        # Look for SVG elements directly
        if re.search(r'<(circle|rect|ellipse|line|polyline|polygon|path|text)\s', response, re.IGNORECASE):
            return response

        return response

    def _update_bounding_box(self, obj_state: ObjectState) -> None:
        """Update bounding box estimate based on position and size."""
        canvas_w = self.state.plan.canvas_width
        canvas_h = self.state.plan.canvas_height

        # Size multipliers
        size_map = {"small": 0.15, "medium": 0.25, "large": 0.4}
        size_mult = size_map.get(obj_state.size, 0.25)

        obj_w = canvas_w * size_mult
        obj_h = canvas_h * size_mult

        # Position mapping
        pos = obj_state.approx_position.lower()
        if "center" in pos:
            cx, cy = canvas_w / 2, canvas_h / 2
        elif "top" in pos:
            cy = canvas_h * 0.25
            cx = canvas_w / 2
        elif "bottom" in pos:
            cy = canvas_h * 0.75
            cx = canvas_w / 2
        else:
            cx, cy = canvas_w / 2, canvas_h / 2

        if "left" in pos:
            cx = canvas_w * 0.25
        elif "right" in pos:
            cx = canvas_w * 0.75

        obj_state.bounding_box = BoundingBox(
            x_min=cx - obj_w / 2,
            y_min=cy - obj_h / 2,
            x_max=cx + obj_w / 2,
            y_max=cy + obj_h / 2,
        )
        obj_state.anchor_points = AnchorPoints(
            start=(cx - obj_w / 2, cy), end=(cx + obj_w / 2, cy)
        )

    def save_output(self, filename: str) -> str:
        """Save the current drawing to a file."""
        if self.renderer is None:
            raise RuntimeError("Renderer not initialized")

        os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
        filepath = os.path.join(OUTPUT_DIRECTORY, filename)
        self.renderer.save(filepath)
        return filepath

    def cleanup(self) -> None:
        """Clean up renderer resources."""
        if self.renderer is not None:
            self.renderer.cleanup()


# ============================================================================
# Main Application
# ============================================================================


def main():
    """Main application entry point."""
    # Load environment variables
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        print("Please set it in your .env file.")
        return

    print("=" * 60)
    print(f"🖼️  LLM-Driven Drawing Application ({DRAWING_BACKEND.upper()} backend)")
    print("=" * 60)
    print()

    # Initialize LLM client
    llm_client = LLMClient(api_key)
    
    # --- Live Viewer Setup ---
    live_preview_filepath = None
    if DRAWING_BACKEND == "svg":
        LIVE_VIEWER_PORT = 8008
        LIVE_SVG_FILENAME = "live_drawing.svg"
        
        # Ensure output directory exists
        os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
        
        live_viewer = LiveViewer(LIVE_VIEWER_PORT, OUTPUT_DIRECTORY, LIVE_SVG_FILENAME)
        live_viewer.start()
        atexit.register(live_viewer.stop)
        
        live_preview_filepath = os.path.join(OUTPUT_DIRECTORY, LIVE_SVG_FILENAME)
        
    controller = DrawingController(llm_client, backend=DRAWING_BACKEND, live_preview_filepath=live_preview_filepath)

    drawing_count = 0

    while True:
        try:
            # Get user input
            if drawing_count == 0:
                prompt = input("What would you like me to draw?\n> ")
            else:
                prompt = input(
                    "\nDraw something else? (enter description or Ctrl+C to exit)\n> "
                )

            if not prompt.strip():
                print("Please enter a drawing description.")
                continue

            print()

            # Create drawing plan
            plan = controller.create_plan(prompt)

            if DEBUG_MODE:
                print(f"\n[Plan] Canvas: {plan.canvas_width}x{plan.canvas_height}")
                print(f"[Plan] Objects: {[obj['id'] for obj in plan.objects]}")
                print(f"[Plan] Style: {plan.style}")

            # Initialize state and renderer
            controller.initialize_state(plan)

            # Run drawing loop
            controller.run_drawing_loop()

            # Save final output
            drawing_count += 1
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # File extension based on backend
            ext = "svg" if DRAWING_BACKEND == "svg" else "eps"
            filename = f"drawing_{drawing_count:03d}_{timestamp}.{ext}"
            filepath = controller.save_output(filename)

            print()
            print("=" * 60)
            print(f"✅ Drawing saved to: {filepath}")
            if controller.state:
                print(f"   Total iterations: {controller.state.total_iterations}")
                print(f"   Total elements: {controller.state.element_count}")
            print("=" * 60)

            # For turtle, wait for the user to close the window
            if DRAWING_BACKEND == "turtle" and controller.renderer:
                controller.renderer.show()

            # Cleanup for next drawing
            controller.cleanup()

        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            if controller.renderer:
                controller.cleanup()
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            if DEBUG_MODE:
                import traceback
                traceback.print_exc()
            print("Let's try again with a new prompt.\n")
            if controller.renderer:
                controller.cleanup()


if __name__ == "__main__":
    main()
