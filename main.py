"""
LLM-Driven Programmatic Image Generation (SVG Prototype)

An AI-powered drawing application that:
- Accepts natural language drawing prompts
- Uses Gemini LLM to create high-level drawing plans and generate SVG code
- Maintains explicit drawing state with controlled iteration
- Outputs SVG files
"""

import os
import json
import time
import re
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

import svgwrite
from dotenv import load_dotenv
import google.generativeai as genai

# ============================================================================
# Configuration Parameters
# ============================================================================

MAX_ITERATIONS = 30
MIN_LLM_CALL_INTERVAL_SECONDS = 2.0
DEFAULT_CANVAS_WIDTH = 800
DEFAULT_CANVAS_HEIGHT = 800
OUTPUT_DIRECTORY = "./outputs"
DEBUG_MODE = True

# ============================================================================
# Enums and Data Classes
# ============================================================================


class ObjectStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class DrawingStage(Enum):
    LAYOUT = "layout"
    MAIN_SHAPES = "main_shapes"
    DETAILS = "details"


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
    svg_element_count: int = 0

    def to_dict(self) -> dict:
        return {
            "canvas": {
                "width": self.plan.canvas_width,
                "height": self.plan.canvas_height,
            },
            "current_stage": self.current_stage.value,
            "total_iterations": self.total_iterations,
            "svg_element_count": self.svg_element_count,
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
# SVG Renderer
# ============================================================================


class SVGRenderer:
    """Handles SVG canvas creation and element addition."""

    def __init__(self, width: int, height: int, background: str = "white"):
        self.width = width
        self.height = height
        self.background = background
        self.drawing = svgwrite.Drawing(size=(f"{width}px", f"{height}px"))

        # Add background
        self.drawing.add(
            self.drawing.rect(insert=(0, 0), size=(width, height), fill=background)
        )

        # Object groups
        self.object_groups: dict[str, svgwrite.container.Group] = {}
        self.element_count = 0

    def get_or_create_group(self, object_id: str) -> svgwrite.container.Group:
        """Get or create a group for an object."""
        if object_id not in self.object_groups:
            group = self.drawing.g(id=object_id)
            self.drawing.add(group)
            self.object_groups[object_id] = group
        return self.object_groups[object_id]

    def add_svg_code(self, object_id: str, svg_code: str) -> int:
        """Add SVG elements from code string to an object's group."""
        group = self.get_or_create_group(object_id)

        elements_added = 0

        # Parse and add various SVG elements
        elements_added += self._parse_and_add_circles(group, svg_code)
        elements_added += self._parse_and_add_ellipses(group, svg_code)
        elements_added += self._parse_and_add_rects(group, svg_code)
        elements_added += self._parse_and_add_lines(group, svg_code)
        elements_added += self._parse_and_add_polylines(group, svg_code)
        elements_added += self._parse_and_add_polygons(group, svg_code)
        elements_added += self._parse_and_add_paths(group, svg_code)
        elements_added += self._parse_and_add_texts(group, svg_code)

        self.element_count += elements_added
        return elements_added

    def _parse_and_add_circles(
        self, group: svgwrite.container.Group, svg_code: str
    ) -> int:
        """Parse and add circle elements."""
        count = 0
        pattern = r'<circle\s+([^>]*)/?>'
        for match in re.finditer(pattern, svg_code, re.IGNORECASE):
            attrs = self._parse_attributes(match.group(1))
            try:
                cx = float(attrs.get("cx", 0))
                cy = float(attrs.get("cy", 0))
                r = float(attrs.get("r", 10))
                fill = attrs.get("fill", "none")
                stroke = attrs.get("stroke", "black")
                stroke_width = attrs.get("stroke-width", "1")

                circle = self.drawing.circle(
                    center=(cx, cy),
                    r=r,
                    fill=fill,
                    stroke=stroke,
                    stroke_width=stroke_width,
                )
                group.add(circle)
                count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_and_add_ellipses(
        self, group: svgwrite.container.Group, svg_code: str
    ) -> int:
        """Parse and add ellipse elements."""
        count = 0
        pattern = r'<ellipse\s+([^>]*)/?>'
        for match in re.finditer(pattern, svg_code, re.IGNORECASE):
            attrs = self._parse_attributes(match.group(1))
            try:
                cx = float(attrs.get("cx", 0))
                cy = float(attrs.get("cy", 0))
                rx = float(attrs.get("rx", 10))
                ry = float(attrs.get("ry", 10))
                fill = attrs.get("fill", "none")
                stroke = attrs.get("stroke", "black")
                stroke_width = attrs.get("stroke-width", "1")

                ellipse = self.drawing.ellipse(
                    center=(cx, cy),
                    r=(rx, ry),
                    fill=fill,
                    stroke=stroke,
                    stroke_width=stroke_width,
                )
                group.add(ellipse)
                count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_and_add_rects(
        self, group: svgwrite.container.Group, svg_code: str
    ) -> int:
        """Parse and add rectangle elements."""
        count = 0
        pattern = r'<rect\s+([^>]*)/?>'
        for match in re.finditer(pattern, svg_code, re.IGNORECASE):
            attrs = self._parse_attributes(match.group(1))
            try:
                x = float(attrs.get("x", 0))
                y = float(attrs.get("y", 0))
                width = float(attrs.get("width", 10))
                height = float(attrs.get("height", 10))
                fill = attrs.get("fill", "none")
                stroke = attrs.get("stroke", "black")
                stroke_width = attrs.get("stroke-width", "1")
                rx = attrs.get("rx")
                ry = attrs.get("ry")

                rect = self.drawing.rect(
                    insert=(x, y),
                    size=(width, height),
                    fill=fill,
                    stroke=stroke,
                    stroke_width=stroke_width,
                )
                if rx:
                    rect["rx"] = rx
                if ry:
                    rect["ry"] = ry
                group.add(rect)
                count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_and_add_lines(
        self, group: svgwrite.container.Group, svg_code: str
    ) -> int:
        """Parse and add line elements."""
        count = 0
        pattern = r'<line\s+([^>]*)/?>'
        for match in re.finditer(pattern, svg_code, re.IGNORECASE):
            attrs = self._parse_attributes(match.group(1))
            try:
                x1 = float(attrs.get("x1", 0))
                y1 = float(attrs.get("y1", 0))
                x2 = float(attrs.get("x2", 0))
                y2 = float(attrs.get("y2", 0))
                stroke = attrs.get("stroke", "black")
                stroke_width = attrs.get("stroke-width", "1")

                line = self.drawing.line(
                    start=(x1, y1), end=(x2, y2), stroke=stroke, stroke_width=stroke_width
                )
                group.add(line)
                count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_and_add_polylines(
        self, group: svgwrite.container.Group, svg_code: str
    ) -> int:
        """Parse and add polyline elements."""
        count = 0
        pattern = r'<polyline\s+([^>]*)/?>'
        for match in re.finditer(pattern, svg_code, re.IGNORECASE):
            attrs = self._parse_attributes(match.group(1))
            try:
                points_str = attrs.get("points", "")
                points = self._parse_points(points_str)
                fill = attrs.get("fill", "none")
                stroke = attrs.get("stroke", "black")
                stroke_width = attrs.get("stroke-width", "1")

                polyline = self.drawing.polyline(
                    points=points, fill=fill, stroke=stroke, stroke_width=stroke_width
                )
                group.add(polyline)
                count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_and_add_polygons(
        self, group: svgwrite.container.Group, svg_code: str
    ) -> int:
        """Parse and add polygon elements."""
        count = 0
        pattern = r'<polygon\s+([^>]*)/?>'
        for match in re.finditer(pattern, svg_code, re.IGNORECASE):
            attrs = self._parse_attributes(match.group(1))
            try:
                points_str = attrs.get("points", "")
                points = self._parse_points(points_str)
                fill = attrs.get("fill", "none")
                stroke = attrs.get("stroke", "black")
                stroke_width = attrs.get("stroke-width", "1")

                polygon = self.drawing.polygon(
                    points=points, fill=fill, stroke=stroke, stroke_width=stroke_width
                )
                group.add(polygon)
                count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_and_add_paths(
        self, group: svgwrite.container.Group, svg_code: str
    ) -> int:
        """Parse and add path elements."""
        count = 0
        pattern = r'<path\s+([^>]*)/?>'
        for match in re.finditer(pattern, svg_code, re.IGNORECASE):
            attrs = self._parse_attributes(match.group(1))
            try:
                d = attrs.get("d", "")
                fill = attrs.get("fill", "none")
                stroke = attrs.get("stroke", "black")
                stroke_width = attrs.get("stroke-width", "1")

                path = self.drawing.path(
                    d=d, fill=fill, stroke=stroke, stroke_width=stroke_width
                )
                group.add(path)
                count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_and_add_texts(
        self, group: svgwrite.container.Group, svg_code: str
    ) -> int:
        """Parse and add text elements."""
        count = 0
        pattern = r'<text\s+([^>]*)>([^<]*)</text>'
        for match in re.finditer(pattern, svg_code, re.IGNORECASE):
            attrs = self._parse_attributes(match.group(1))
            text_content = match.group(2)
            try:
                x = float(attrs.get("x", 0))
                y = float(attrs.get("y", 0))
                fill = attrs.get("fill", "black")
                font_size = attrs.get("font-size", "16px")

                text = self.drawing.text(
                    text_content, insert=(x, y), fill=fill, font_size=font_size
                )
                group.add(text)
                count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_attributes(self, attr_string: str) -> dict[str, str]:
        """Parse SVG attributes from a string."""
        attrs = {}
        # Match attribute="value" or attribute='value'
        pattern = r'(\w+(?:-\w+)*)\s*=\s*["\']([^"\']*)["\']'
        for match in re.finditer(pattern, attr_string):
            attrs[match.group(1)] = match.group(2)
        return attrs

    def _parse_points(self, points_str: str) -> list[tuple[float, float]]:
        """Parse points string into list of coordinate tuples."""
        points = []
        # Handle both "x1,y1 x2,y2" and "x1 y1 x2 y2" formats
        coords = re.findall(r'[-\d.]+', points_str)
        for i in range(0, len(coords) - 1, 2):
            points.append((float(coords[i]), float(coords[i + 1])))
        return points

    def save(self, filepath: str) -> None:
        """Save the SVG to a file."""
        self.drawing.saveas(filepath)


# ============================================================================
# Drawing Controller
# ============================================================================


class DrawingController:
    """Controls the iterative drawing process."""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.state: Optional[DrawingState] = None
        self.renderer: Optional[SVGRenderer] = None

    def create_plan(self, user_prompt: str) -> DrawingPlan:
        """Create a high-level drawing plan from user prompt."""
        system_prompt = """You are an AI assistant that creates structured drawing plans.
You MUST respond with ONLY valid JSON, no other text.

Create a drawing plan with the following structure:
{
    "canvas": {
        "width": <number>,
        "height": <number>,
        "background": "<color (use valid SVG/CSS names with no spaces, e.g., 'skyblue' instead of 'sky blue', or Hex codes)>"
    },
    "objects": [
        {
            "id": "<unique_id>",
            "type": "<object_type>",
            "description": "<brief description>",
            "approx_position": "<position like 'center', 'top-left', etc>",
            "size": "<small/medium/large>"
        }
    ],
    "composition": "<how objects relate to each other>",
    "style": "<art style description>"
}

Keep the plan simple with 2-5 objects maximum.
Use simple, descriptive IDs like "sun", "tree", "house".
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
            object_states[obj["id"]] = ObjectState(
                id=obj["id"],
                obj_type=obj.get("type", "object"),
                description=obj.get("description", ""),
                approx_position=obj.get("approx_position", "center"),
                size=obj.get("size", "medium"),
            )

        self.state = DrawingState(plan=plan, object_states=object_states)
        self.renderer = SVGRenderer(
            plan.canvas_width, plan.canvas_height, plan.background
        )

    def run_drawing_loop(self) -> None:
        """Execute the main drawing loop."""
        if self.state is None or self.renderer is None:
            raise RuntimeError("State not initialized")

        stages = [DrawingStage.LAYOUT, DrawingStage.MAIN_SHAPES, DrawingStage.DETAILS]

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

                    # Mark as completed after details stage
                    if stage == DrawingStage.DETAILS:
                        obj_state.status = ObjectStatus.COMPLETED

                if DEBUG_MODE:
                    print(
                        f"    Elements: {self.renderer.element_count}, "
                        f"Iterations: {self.state.total_iterations}"
                    )

    def _generate_object_stage(
        self, obj_id: str, obj_state: ObjectState, stage: DrawingStage
    ) -> bool:
        """Generate SVG code for an object at a specific stage."""
        system_prompt = """You are an SVG drawing assistant.
Generate SVG code for drawing shapes. Follow these STRICT rules:

1. Output ONLY raw SVG elements (circle, rect, ellipse, line, polyline, polygon, path, text)
2. Do NOT include <svg> tags or canvas definitions
3. Do NOT modify or reference other objects
4. Use coordinates within the canvas bounds
5. Keep shapes simple and clear
6. Use appropriate colors and stroke widths. IMPORTANT: Colors MUST be valid SVG/CSS names with NO SPACES (e.g., use 'skyblue', NOT 'sky blue') or use Hex codes (e.g., '#87CEEB').

Canvas size: {width}x{height} pixels

Stage instructions:
- LAYOUT: Create rough positioning with simple placeholder shapes
- MAIN_SHAPES: Refine the primary geometry with correct proportions
- DETAILS: Add finishing touches, features, and decorations
""".format(
            width=self.state.plan.canvas_width, height=self.state.plan.canvas_height
        )

        user_prompt = f"""Generate SVG code for object: {obj_id}
Current stage: {stage.value}

Object details:
- Type: {obj_state.obj_type}
- Description: {obj_state.description}
- Position: {obj_state.approx_position}
- Size: {obj_state.size}

Drawing composition: {self.state.plan.composition}
Style: {self.state.plan.style}

Current drawing state:
{json.dumps(self.state.to_dict(), indent=2)}

Generate SVG code ONLY for this object and stage. Output raw SVG elements only."""

        if DEBUG_MODE:
            print(f"  [Drawing] {obj_id} - {stage.value}")

        try:
            response = self.llm_client.call_llm(system_prompt, user_prompt)

            # Extract SVG code
            svg_code = self._extract_svg_code(response)

            if svg_code:
                elements_added = self.renderer.add_svg_code(obj_id, svg_code)
                if DEBUG_MODE:
                    print(f"    Added {elements_added} element(s)")

                # Update bounding box estimate based on position
                self._update_bounding_box(obj_state)

                return elements_added > 0
            else:
                if DEBUG_MODE:
                    print("    No valid SVG code found in response")
                return False

        except Exception as e:
            if DEBUG_MODE:
                print(f"    Error: {e}")
            return False

    def _extract_svg_code(self, response: str) -> str:
        """Extract SVG code from LLM response."""
        # Try to find SVG in code blocks
        svg_match = re.search(r'```(?:svg|xml|html)?\s*([\s\S]*?)\s*```', response)
        if svg_match:
            return svg_match.group(1)

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
    print("🖼️  LLM-Driven SVG Drawing Application")
    print("=" * 60)
    print()

    # Initialize LLM client
    llm_client = LLMClient(api_key)
    controller = DrawingController(llm_client)

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

            # Initialize state
            controller.initialize_state(plan)

            # Run drawing loop
            controller.run_drawing_loop()

            # Save output
            drawing_count += 1
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"drawing_{drawing_count:03d}_{timestamp}.svg"
            filepath = controller.save_output(filename)

            print()
            print("=" * 60)
            print(f"✅ Drawing saved to: {filepath}")
            print(f"   Total iterations: {controller.state.total_iterations}")
            print(f"   Total elements: {controller.renderer.element_count}")
            print("=" * 60)

        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\nError during drawing: {e}")
            if DEBUG_MODE:
                import traceback

                traceback.print_exc()
            print("Let's try again with a new prompt.\n")


if __name__ == "__main__":
    main()
