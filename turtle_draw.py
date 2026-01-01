"""
Turtle Drawing Backend

Implements the BaseDraw interface using Python's turtle graphics module.
Note: Turtle uses a different coordinate system (center origin, y-up) so we convert.
"""

import re
import math
import turtle as t
from typing import Optional
from pathlib import Path

from base_draw import BaseDraw, DrawingConfig


class TurtleDraw(BaseDraw):
    """Turtle graphics drawing backend using Python's turtle module."""

    def __init__(self, config: DrawingConfig):
        super().__init__(config)
        self.screen: Optional[t.Screen] = None
        self.turtle: Optional[t.Turtle] = None
        self._initialized = False

    @property
    def backend_name(self) -> str:
        return "turtle"

    @property
    def supported_elements(self) -> list[str]:
        return ["circle", "ellipse", "rect", "line", "polyline", "polygon", "path", "text"]

    @property
    def system_prompt_instructions(self) -> str:
        return """You are a Turtle graphics drawing assistant.
Generate SVG-like code that will be translated to turtle commands. Follow these STRICT rules:

1. Output SVG-like elements (circle, rect, ellipse, line, polyline, polygon, path, text)
2. Use standard SVG coordinate system (0,0 at top-left, y increases downward)
3. Coordinates will be automatically converted for turtle (center origin, y-up)
4. Keep shapes simple - turtle draws by moving a pen
5. For complex curves, use polylines with many points instead of bezier curves
6. Colors MUST be valid color names with NO SPACES (e.g., 'skyblue', NOT 'sky blue') or Hex codes (e.g., '#87CEEB')

IMPORTANT for Turtle backend:
- Paths with bezier curves (Q, C commands) will be approximated with straight lines
- Complex paths may not render exactly as in SVG
- Prefer simple shapes: circles, rectangles, polygons, and polylines
- For smooth curves, use polygons with many points

Example valid elements:
<circle cx="100" cy="100" r="50" fill="red" stroke="black" stroke-width="2"/>
<rect x="50" y="50" width="100" height="80" fill="blue" stroke="black"/>
<polygon points="100,10 40,198 190,78" fill="lime" stroke="purple"/>
<polyline points="0,40 40,40 40,80 80,80" fill="none" stroke="red"/>
<text x="100" y="100" fill="black" font-size="16px">Hello</text>"""

    def _svg_to_turtle_coords(self, x: float, y: float) -> tuple[float, float]:
        """
        Convert SVG coordinates to turtle coordinates.
        SVG: (0,0) at top-left, y increases downward
        Turtle: (0,0) at center, y increases upward
        """
        # Translate so center of canvas is at origin
        tx = x - self.width / 2
        ty = self.height / 2 - y  # Flip y-axis
        return tx, ty

    def _parse_color(self, color: str) -> str:
        """Parse and validate color, returning a turtle-compatible color."""
        if not color or color.lower() == "none":
            return ""
        # Remove spaces from color names
        return color.replace(" ", "").lower()

    def initialize(self) -> None:
        """Initialize the turtle graphics window."""
        self.screen = t.Screen()
        self.screen.setup(width=self.width + 50, height=self.height + 50)
        self.screen.setworldcoordinates(
            -self.width / 2 - 25, -self.height / 2 - 25,
            self.width / 2 + 25, self.height / 2 + 25
        )
        self.screen.bgcolor(self._parse_color(self.background) or "white")
        self.screen.title("LLM Drawing - Turtle Backend")
        # Enable animation with a small delay (0 = fastest but still visible)
        self.screen.tracer(1, 10)  # Update after every shape, 10ms delay

        self.turtle = t.Turtle()
        self.turtle.speed(3)  # Medium speed for visibility
        self.turtle.hideturtle()
        self.turtle.penup()

        self._initialized = True
        self.element_count = 0

    def get_or_create_group(self, object_id: str) -> None:
        """Turtle doesn't have groups, but we track elements per object."""
        if object_id not in self.object_groups:
            self.object_groups[object_id] = []

    def add_code(self, object_id: str, code: str) -> int:
        """Parse SVG-like code and draw using turtle."""
        elements_added = 0

        # Parse and add various elements
        elements_added += self._parse_and_add_circles(object_id, code)
        elements_added += self._parse_and_add_ellipses(object_id, code)
        elements_added += self._parse_and_add_rects(object_id, code)
        elements_added += self._parse_and_add_lines(object_id, code)
        elements_added += self._parse_and_add_polylines(object_id, code)
        elements_added += self._parse_and_add_polygons(object_id, code)
        elements_added += self._parse_and_add_paths(object_id, code)
        elements_added += self._parse_and_add_texts(object_id, code)

        # Update screen
        if self.screen:
            self.screen.update()

        self.element_count += elements_added
        return elements_added

    def _parse_attributes(self, attr_string: str) -> dict[str, str]:
        """Parse SVG attributes from a string."""
        attrs = {}
        pattern = r'(\w+(?:-\w+)*)\s*=\s*["\']([^"\']*)["\']'
        for match in re.finditer(pattern, attr_string):
            attrs[match.group(1)] = match.group(2)
        return attrs

    def _parse_points(self, points_str: str) -> list[tuple[float, float]]:
        """Parse points string into list of coordinate tuples."""
        points = []
        coords = re.findall(r'[-\d.]+', points_str)
        for i in range(0, len(coords) - 1, 2):
            points.append((float(coords[i]), float(coords[i + 1])))
        return points

    def _parse_and_add_circles(self, object_id: str, code: str) -> int:
        count = 0
        pattern = r'<circle\s+([^>]*)/?>'
        for match in re.finditer(pattern, code, re.IGNORECASE):
            attrs = self._parse_attributes(match.group(1))
            try:
                cx = float(attrs.get("cx", 0))
                cy = float(attrs.get("cy", 0))
                r = float(attrs.get("r", 10))
                fill = attrs.get("fill", "none")
                stroke = attrs.get("stroke", "black")
                stroke_width = float(attrs.get("stroke-width", "1"))
                if self.draw_circle(object_id, cx, cy, r, fill, stroke, stroke_width):
                    count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_and_add_ellipses(self, object_id: str, code: str) -> int:
        count = 0
        pattern = r'<ellipse\s+([^>]*)/?>'
        for match in re.finditer(pattern, code, re.IGNORECASE):
            attrs = self._parse_attributes(match.group(1))
            try:
                cx = float(attrs.get("cx", 0))
                cy = float(attrs.get("cy", 0))
                rx = float(attrs.get("rx", 10))
                ry = float(attrs.get("ry", 10))
                fill = attrs.get("fill", "none")
                stroke = attrs.get("stroke", "black")
                stroke_width = float(attrs.get("stroke-width", "1"))
                if self.draw_ellipse(object_id, cx, cy, rx, ry, fill, stroke, stroke_width):
                    count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_and_add_rects(self, object_id: str, code: str) -> int:
        count = 0
        pattern = r'<rect\s+([^>]*)/?>'
        for match in re.finditer(pattern, code, re.IGNORECASE):
            attrs = self._parse_attributes(match.group(1))
            try:
                x = float(attrs.get("x", 0))
                y = float(attrs.get("y", 0))
                width = float(attrs.get("width", 10))
                height = float(attrs.get("height", 10))
                fill = attrs.get("fill", "none")
                stroke = attrs.get("stroke", "black")
                stroke_width = float(attrs.get("stroke-width", "1"))
                if self.draw_rect(object_id, x, y, width, height, fill, stroke, stroke_width):
                    count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_and_add_lines(self, object_id: str, code: str) -> int:
        count = 0
        pattern = r'<line\s+([^>]*)/?>'
        for match in re.finditer(pattern, code, re.IGNORECASE):
            attrs = self._parse_attributes(match.group(1))
            try:
                x1 = float(attrs.get("x1", 0))
                y1 = float(attrs.get("y1", 0))
                x2 = float(attrs.get("x2", 0))
                y2 = float(attrs.get("y2", 0))
                stroke = attrs.get("stroke", "black")
                stroke_width = float(attrs.get("stroke-width", "1"))
                if self.draw_line(object_id, x1, y1, x2, y2, stroke, stroke_width):
                    count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_and_add_polylines(self, object_id: str, code: str) -> int:
        count = 0
        pattern = r'<polyline\s+([^>]*)/?>'
        for match in re.finditer(pattern, code, re.IGNORECASE):
            attrs = self._parse_attributes(match.group(1))
            try:
                points_str = attrs.get("points", "")
                points = self._parse_points(points_str)
                fill = attrs.get("fill", "none")
                stroke = attrs.get("stroke", "black")
                stroke_width = float(attrs.get("stroke-width", "1"))
                if self.draw_polyline(object_id, points, fill, stroke, stroke_width):
                    count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_and_add_polygons(self, object_id: str, code: str) -> int:
        count = 0
        pattern = r'<polygon\s+([^>]*)/?>'
        for match in re.finditer(pattern, code, re.IGNORECASE):
            attrs = self._parse_attributes(match.group(1))
            try:
                points_str = attrs.get("points", "")
                points = self._parse_points(points_str)
                fill = attrs.get("fill", "none")
                stroke = attrs.get("stroke", "black")
                stroke_width = float(attrs.get("stroke-width", "1"))
                if self.draw_polygon(object_id, points, fill, stroke, stroke_width):
                    count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_and_add_paths(self, object_id: str, code: str) -> int:
        count = 0
        pattern = r'<path\s+([^>]*)/?>'
        for match in re.finditer(pattern, code, re.IGNORECASE):
            attrs = self._parse_attributes(match.group(1))
            try:
                d = attrs.get("d", "")
                fill = attrs.get("fill", "none")
                stroke = attrs.get("stroke", "black")
                stroke_width = float(attrs.get("stroke-width", "1"))
                if self.draw_path(object_id, d, fill, stroke, stroke_width):
                    count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_and_add_texts(self, object_id: str, code: str) -> int:
        count = 0
        pattern = r'<text\s+([^>]*)>([^<]*)</text>'
        for match in re.finditer(pattern, code, re.IGNORECASE):
            attrs = self._parse_attributes(match.group(1))
            text_content = match.group(2)
            try:
                x = float(attrs.get("x", 0))
                y = float(attrs.get("y", 0))
                fill = attrs.get("fill", "black")
                font_size = attrs.get("font-size", "16px")
                if self.draw_text(object_id, x, y, text_content, fill, font_size):
                    count += 1
            except (ValueError, KeyError):
                continue
        return count

    # === Direct drawing methods ===

    def draw_circle(self, object_id: str, cx: float, cy: float, r: float,
                    fill: str = "none", stroke: str = "black", stroke_width: float = 1) -> bool:
        """Draw a circle using turtle."""
        try:
            self.get_or_create_group(object_id)
            tx, ty = self._svg_to_turtle_coords(cx, cy - r)  # Start at bottom of circle

            self.turtle.penup()
            self.turtle.goto(tx, ty - r)  # Position at bottom

            # Set stroke
            stroke_color = self._parse_color(stroke)
            if stroke_color:
                self.turtle.pencolor(stroke_color)
                self.turtle.pensize(stroke_width)
                self.turtle.pendown()
            else:
                self.turtle.penup()

            # Set fill
            fill_color = self._parse_color(fill)
            if fill_color:
                self.turtle.fillcolor(fill_color)
                self.turtle.begin_fill()

            # Draw circle
            self.turtle.circle(r)

            if fill_color:
                self.turtle.end_fill()

            self.turtle.penup()
            self.object_groups[object_id].append(("circle", {"cx": cx, "cy": cy, "r": r}))
            return True
        except Exception:
            return False

    def draw_ellipse(self, object_id: str, cx: float, cy: float, rx: float, ry: float,
                     fill: str = "none", stroke: str = "black", stroke_width: float = 1) -> bool:
        """Draw an ellipse using turtle (approximated with polygon)."""
        try:
            self.get_or_create_group(object_id)

            # Generate points for ellipse approximation
            points = []
            num_segments = 36
            for i in range(num_segments):
                angle = 2 * math.pi * i / num_segments
                x = cx + rx * math.cos(angle)
                y = cy + ry * math.sin(angle)
                points.append((x, y))

            return self.draw_polygon(object_id, points, fill, stroke, stroke_width)
        except Exception:
            return False

    def draw_rect(self, object_id: str, x: float, y: float, width: float, height: float,
                  fill: str = "none", stroke: str = "black", stroke_width: float = 1,
                  rx: Optional[float] = None, ry: Optional[float] = None) -> bool:
        """Draw a rectangle using turtle."""
        try:
            self.get_or_create_group(object_id)

            # Rectangle corners (in SVG coordinates)
            points = [
                (x, y),
                (x + width, y),
                (x + width, y + height),
                (x, y + height)
            ]

            return self.draw_polygon(object_id, points, fill, stroke, stroke_width)
        except Exception:
            return False

    def draw_line(self, object_id: str, x1: float, y1: float, x2: float, y2: float,
                  stroke: str = "black", stroke_width: float = 1) -> bool:
        """Draw a line using turtle."""
        try:
            self.get_or_create_group(object_id)
            tx1, ty1 = self._svg_to_turtle_coords(x1, y1)
            tx2, ty2 = self._svg_to_turtle_coords(x2, y2)

            stroke_color = self._parse_color(stroke)
            if not stroke_color:
                stroke_color = "black"

            self.turtle.penup()
            self.turtle.goto(tx1, ty1)
            self.turtle.pencolor(stroke_color)
            self.turtle.pensize(stroke_width)
            self.turtle.pendown()
            self.turtle.goto(tx2, ty2)
            self.turtle.penup()

            self.object_groups[object_id].append(("line", {"x1": x1, "y1": y1, "x2": x2, "y2": y2}))
            return True
        except Exception:
            return False

    def draw_polyline(self, object_id: str, points: list[tuple[float, float]],
                      fill: str = "none", stroke: str = "black", stroke_width: float = 1) -> bool:
        """Draw a polyline using turtle."""
        if not points:
            return False

        try:
            self.get_or_create_group(object_id)

            stroke_color = self._parse_color(stroke)
            fill_color = self._parse_color(fill)

            # Convert first point
            tx, ty = self._svg_to_turtle_coords(points[0][0], points[0][1])
            self.turtle.penup()
            self.turtle.goto(tx, ty)

            if stroke_color:
                self.turtle.pencolor(stroke_color)
                self.turtle.pensize(stroke_width)
                self.turtle.pendown()

            if fill_color:
                self.turtle.fillcolor(fill_color)
                self.turtle.begin_fill()

            # Draw to each point
            for px, py in points[1:]:
                tx, ty = self._svg_to_turtle_coords(px, py)
                self.turtle.goto(tx, ty)

            if fill_color:
                self.turtle.end_fill()

            self.turtle.penup()
            self.object_groups[object_id].append(("polyline", {"points": points}))
            return True
        except Exception:
            return False

    def draw_polygon(self, object_id: str, points: list[tuple[float, float]],
                     fill: str = "none", stroke: str = "black", stroke_width: float = 1) -> bool:
        """Draw a polygon using turtle."""
        if not points:
            return False

        try:
            self.get_or_create_group(object_id)

            stroke_color = self._parse_color(stroke)
            fill_color = self._parse_color(fill)

            # Convert first point
            tx, ty = self._svg_to_turtle_coords(points[0][0], points[0][1])
            self.turtle.penup()
            self.turtle.goto(tx, ty)

            if stroke_color:
                self.turtle.pencolor(stroke_color)
                self.turtle.pensize(stroke_width)
                self.turtle.pendown()

            if fill_color:
                self.turtle.fillcolor(fill_color)
                self.turtle.begin_fill()

            # Draw to each point
            for px, py in points[1:]:
                tx, ty = self._svg_to_turtle_coords(px, py)
                self.turtle.goto(tx, ty)

            # Close polygon
            tx, ty = self._svg_to_turtle_coords(points[0][0], points[0][1])
            self.turtle.goto(tx, ty)

            if fill_color:
                self.turtle.end_fill()

            self.turtle.penup()
            self.object_groups[object_id].append(("polygon", {"points": points}))
            return True
        except Exception:
            return False

    def draw_path(self, object_id: str, d: str,
                  fill: str = "none", stroke: str = "black", stroke_width: float = 1) -> bool:
        """
        Draw an SVG path using turtle.
        This is a simplified implementation that handles basic path commands.
        """
        try:
            self.get_or_create_group(object_id)

            stroke_color = self._parse_color(stroke)
            fill_color = self._parse_color(fill)

            if stroke_color:
                self.turtle.pencolor(stroke_color)
                self.turtle.pensize(stroke_width)

            if fill_color:
                self.turtle.fillcolor(fill_color)
                self.turtle.begin_fill()

            # Parse path commands (simplified)
            self._execute_path_commands(d, stroke_color is not None)

            if fill_color:
                self.turtle.end_fill()

            self.turtle.penup()
            self.object_groups[object_id].append(("path", {"d": d}))
            return True
        except Exception:
            return False

    def _execute_path_commands(self, d: str, draw_stroke: bool) -> None:
        """Execute SVG path commands."""
        # Tokenize the path
        tokens = re.findall(r'[MmLlHhVvCcSsQqTtAaZz]|[-\d.]+', d)

        current_x, current_y = 0.0, 0.0
        start_x, start_y = 0.0, 0.0
        i = 0

        while i < len(tokens):
            cmd = tokens[i]

            if cmd in 'Mm':
                # Move to
                i += 1
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                if cmd == 'm':  # Relative
                    x += current_x
                    y += current_y
                tx, ty = self._svg_to_turtle_coords(x, y)
                self.turtle.penup()
                self.turtle.goto(tx, ty)
                current_x, current_y = x, y
                start_x, start_y = x, y
                if draw_stroke:
                    self.turtle.pendown()

            elif cmd in 'Ll':
                # Line to
                i += 1
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                if cmd == 'l':  # Relative
                    x += current_x
                    y += current_y
                tx, ty = self._svg_to_turtle_coords(x, y)
                self.turtle.goto(tx, ty)
                current_x, current_y = x, y

            elif cmd in 'Hh':
                # Horizontal line
                i += 1
                x = float(tokens[i])
                i += 1
                if cmd == 'h':  # Relative
                    x += current_x
                tx, ty = self._svg_to_turtle_coords(x, current_y)
                self.turtle.goto(tx, ty)
                current_x = x

            elif cmd in 'Vv':
                # Vertical line
                i += 1
                y = float(tokens[i])
                i += 1
                if cmd == 'v':  # Relative
                    y += current_y
                tx, ty = self._svg_to_turtle_coords(current_x, y)
                self.turtle.goto(tx, ty)
                current_y = y

            elif cmd in 'Zz':
                # Close path
                i += 1
                tx, ty = self._svg_to_turtle_coords(start_x, start_y)
                self.turtle.goto(tx, ty)
                current_x, current_y = start_x, start_y

            elif cmd in 'CcQqSsTt':
                # Curves - approximate with lines for simplicity
                # Skip the control points and just go to the end point
                i += 1
                if cmd in 'Cc':  # Cubic bezier (6 params)
                    if i + 5 < len(tokens):
                        x, y = float(tokens[i + 4]), float(tokens[i + 5])
                        i += 6
                        if cmd == 'c':
                            x += current_x
                            y += current_y
                        tx, ty = self._svg_to_turtle_coords(x, y)
                        self.turtle.goto(tx, ty)
                        current_x, current_y = x, y
                elif cmd in 'Qq':  # Quadratic bezier (4 params)
                    if i + 3 < len(tokens):
                        x, y = float(tokens[i + 2]), float(tokens[i + 3])
                        i += 4
                        if cmd == 'q':
                            x += current_x
                            y += current_y
                        tx, ty = self._svg_to_turtle_coords(x, y)
                        self.turtle.goto(tx, ty)
                        current_x, current_y = x, y
                elif cmd in 'SsTt':  # Smooth curves (4 or 2 params)
                    if i + 1 < len(tokens):
                        x, y = float(tokens[i]), float(tokens[i + 1])
                        i += 2
                        if cmd.islower():
                            x += current_x
                            y += current_y
                        tx, ty = self._svg_to_turtle_coords(x, y)
                        self.turtle.goto(tx, ty)
                        current_x, current_y = x, y

            elif cmd in 'Aa':
                # Arc - simplified, skip for now
                i += 8  # Skip all arc parameters

            else:
                # Try to parse as number (continuation of previous command)
                i += 1

    def draw_text(self, object_id: str, x: float, y: float, text: str,
                  fill: str = "black", font_size: str = "16px") -> bool:
        """Draw text using turtle."""
        try:
            self.get_or_create_group(object_id)
            tx, ty = self._svg_to_turtle_coords(x, y)

            # Parse font size
            size = 16
            if font_size:
                size_match = re.match(r'(\d+)', font_size)
                if size_match:
                    size = int(size_match.group(1))

            fill_color = self._parse_color(fill) or "black"

            self.turtle.penup()
            self.turtle.goto(tx, ty)
            self.turtle.pencolor(fill_color)
            self.turtle.write(text, font=("Arial", size, "normal"))

            self.object_groups[object_id].append(("text", {"x": x, "y": y, "text": text}))
            return True
        except Exception:
            return False

    def save(self, filepath: str) -> None:
        """Save the turtle drawing as an image."""
        if self.screen:
            try:
                # Try to save as PostScript (eps)
                ps_path = filepath.replace('.svg', '.eps').replace('.png', '.eps')
                canvas = self.screen.getcanvas()
                canvas.postscript(file=ps_path)
                print(f"[Turtle] Saved as PostScript: {ps_path}")
            except Exception as e:
                print(f"[Turtle] Could not save: {e}")

    def show(self) -> None:
        """Display the turtle window and wait for user to close it."""
        if self.screen:
            self.screen.update()
            print("[Turtle] Drawing complete. Close the window to continue.")
            try:
                t.done()
            except t.Terminator:
                # This exception is raised when the window is closed, which is expected.
                pass

    def cleanup(self) -> None:
        """Clean up turtle resources."""
        try:
            if self.screen:
                self.screen.bye()
        except Exception:
            pass
        self.screen = None
        self.turtle = None
        self._initialized = False
