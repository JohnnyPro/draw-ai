"""
SVG Drawing Backend

Implements the BaseDraw interface using svgwrite for SVG output.
"""

import re
from typing import Optional

import svgwrite

from base_draw import BaseDraw, DrawingConfig


class SVGDraw(BaseDraw):
    """SVG drawing backend using svgwrite library."""

    def __init__(self, config: DrawingConfig):
        super().__init__(config)
        self.drawing: Optional[svgwrite.Drawing] = None
        self._groups: dict[str, svgwrite.container.Group] = {}

    @property
    def backend_name(self) -> str:
        return "svg"

    @property
    def supported_elements(self) -> list[str]:
        return ["circle", "ellipse", "rect", "line", "polyline", "polygon", "path", "text"]

    @property
    def system_prompt_instructions(self) -> str:
        return """You are an SVG drawing assistant.
Generate SVG code for drawing shapes. Follow these STRICT rules:

1. Output ONLY raw SVG elements (circle, rect, ellipse, line, polyline, polygon, path, text)
2. Do NOT include <svg> tags or canvas definitions
3. Do NOT modify or reference other objects
4. Use coordinates within the canvas bounds
5. Keep shapes simple and clear
6. Use appropriate colors and stroke widths. IMPORTANT: Colors MUST be valid SVG/CSS names with NO SPACES (e.g., use 'skyblue', NOT 'sky blue') or use Hex codes (e.g., '#87CEEB').

Example valid elements:
<circle cx="100" cy="100" r="50" fill="red" stroke="black" stroke-width="2"/>
<rect x="50" y="50" width="100" height="80" fill="blue" stroke="black"/>
<path d="M 100 100 L 200 200 Q 250 150 300 200" fill="none" stroke="green"/>
<ellipse cx="200" cy="200" rx="60" ry="40" fill="yellow"/>
<polygon points="100,10 40,198 190,78 10,78 160,198" fill="lime" stroke="purple"/>
<text x="100" y="100" fill="black" font-size="16px">Hello</text>"""

    def initialize(self) -> None:
        """Initialize the SVG drawing canvas."""
        self.drawing = svgwrite.Drawing(size=(f"{self.width}px", f"{self.height}px"))
        # Add background
        self.drawing.add(
            self.drawing.rect(insert=(0, 0), size=(self.width, self.height), fill=self.background)
        )
        self._groups = {}
        self.element_count = 1  # Count background

    def get_or_create_group(self, object_id: str) -> svgwrite.container.Group:
        """Get or create a group for an object."""
        if object_id not in self._groups:
            group = self.drawing.g(id=object_id)
            self.drawing.add(group)
            self._groups[object_id] = group
            if object_id not in self.object_groups:
                self.object_groups[object_id] = []
        return self._groups[object_id]

    def add_code(self, object_id: str, code: str) -> int:
        """Parse SVG code and add elements to the drawing."""
        elements_added = 0

        # Parse and add various SVG elements
        elements_added += self._parse_and_add_circles(object_id, code)
        elements_added += self._parse_and_add_ellipses(object_id, code)
        elements_added += self._parse_and_add_rects(object_id, code)
        elements_added += self._parse_and_add_lines(object_id, code)
        elements_added += self._parse_and_add_polylines(object_id, code)
        elements_added += self._parse_and_add_polygons(object_id, code)
        elements_added += self._parse_and_add_paths(object_id, code)
        elements_added += self._parse_and_add_texts(object_id, code)

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

    def _parse_and_add_circles(self, object_id: str, svg_code: str) -> int:
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

                if self.draw_circle(object_id, cx, cy, r, fill, stroke, float(stroke_width)):
                    count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_and_add_ellipses(self, object_id: str, svg_code: str) -> int:
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

                if self.draw_ellipse(object_id, cx, cy, rx, ry, fill, stroke, float(stroke_width)):
                    count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_and_add_rects(self, object_id: str, svg_code: str) -> int:
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
                rx = float(attrs["rx"]) if "rx" in attrs else None
                ry = float(attrs["ry"]) if "ry" in attrs else None

                if self.draw_rect(object_id, x, y, width, height, fill, stroke, float(stroke_width), rx, ry):
                    count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_and_add_lines(self, object_id: str, svg_code: str) -> int:
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

                if self.draw_line(object_id, x1, y1, x2, y2, stroke, float(stroke_width)):
                    count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_and_add_polylines(self, object_id: str, svg_code: str) -> int:
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

                if self.draw_polyline(object_id, points, fill, stroke, float(stroke_width)):
                    count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_and_add_polygons(self, object_id: str, svg_code: str) -> int:
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

                if self.draw_polygon(object_id, points, fill, stroke, float(stroke_width)):
                    count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_and_add_paths(self, object_id: str, svg_code: str) -> int:
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

                if self.draw_path(object_id, d, fill, stroke, float(stroke_width)):
                    count += 1
            except (ValueError, KeyError):
                continue
        return count

    def _parse_and_add_texts(self, object_id: str, svg_code: str) -> int:
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

                if self.draw_text(object_id, x, y, text_content, fill, font_size):
                    count += 1
            except (ValueError, KeyError):
                continue
        return count

    # === Direct drawing methods ===

    def draw_circle(self, object_id: str, cx: float, cy: float, r: float,
                    fill: str = "none", stroke: str = "black", stroke_width: float = 1) -> bool:
        """Draw a circle."""
        try:
            group = self.get_or_create_group(object_id)
            circle = self.drawing.circle(
                center=(cx, cy), r=r, fill=fill, stroke=stroke, stroke_width=stroke_width
            )
            group.add(circle)
            self.object_groups[object_id].append(("circle", {"cx": cx, "cy": cy, "r": r}))
            return True
        except Exception:
            return False

    def draw_ellipse(self, object_id: str, cx: float, cy: float, rx: float, ry: float,
                     fill: str = "none", stroke: str = "black", stroke_width: float = 1) -> bool:
        """Draw an ellipse."""
        try:
            group = self.get_or_create_group(object_id)
            ellipse = self.drawing.ellipse(
                center=(cx, cy), r=(rx, ry), fill=fill, stroke=stroke, stroke_width=stroke_width
            )
            group.add(ellipse)
            self.object_groups[object_id].append(("ellipse", {"cx": cx, "cy": cy, "rx": rx, "ry": ry}))
            return True
        except Exception:
            return False

    def draw_rect(self, object_id: str, x: float, y: float, width: float, height: float,
                  fill: str = "none", stroke: str = "black", stroke_width: float = 1,
                  rx: Optional[float] = None, ry: Optional[float] = None) -> bool:
        """Draw a rectangle."""
        try:
            group = self.get_or_create_group(object_id)
            rect = self.drawing.rect(
                insert=(x, y), size=(width, height), fill=fill, stroke=stroke, stroke_width=stroke_width
            )
            if rx is not None:
                rect["rx"] = rx
            if ry is not None:
                rect["ry"] = ry
            group.add(rect)
            self.object_groups[object_id].append(("rect", {"x": x, "y": y, "width": width, "height": height}))
            return True
        except Exception:
            return False

    def draw_line(self, object_id: str, x1: float, y1: float, x2: float, y2: float,
                  stroke: str = "black", stroke_width: float = 1) -> bool:
        """Draw a line."""
        try:
            group = self.get_or_create_group(object_id)
            line = self.drawing.line(start=(x1, y1), end=(x2, y2), stroke=stroke, stroke_width=stroke_width)
            group.add(line)
            self.object_groups[object_id].append(("line", {"x1": x1, "y1": y1, "x2": x2, "y2": y2}))
            return True
        except Exception:
            return False

    def draw_polyline(self, object_id: str, points: list[tuple[float, float]],
                      fill: str = "none", stroke: str = "black", stroke_width: float = 1) -> bool:
        """Draw a polyline."""
        try:
            group = self.get_or_create_group(object_id)
            polyline = self.drawing.polyline(points=points, fill=fill, stroke=stroke, stroke_width=stroke_width)
            group.add(polyline)
            self.object_groups[object_id].append(("polyline", {"points": points}))
            return True
        except Exception:
            return False

    def draw_polygon(self, object_id: str, points: list[tuple[float, float]],
                     fill: str = "none", stroke: str = "black", stroke_width: float = 1) -> bool:
        """Draw a polygon."""
        try:
            group = self.get_or_create_group(object_id)
            polygon = self.drawing.polygon(points=points, fill=fill, stroke=stroke, stroke_width=stroke_width)
            group.add(polygon)
            self.object_groups[object_id].append(("polygon", {"points": points}))
            return True
        except Exception:
            return False

    def draw_path(self, object_id: str, d: str,
                  fill: str = "none", stroke: str = "black", stroke_width: float = 1) -> bool:
        """Draw a path."""
        try:
            group = self.get_or_create_group(object_id)
            path = self.drawing.path(d=d, fill=fill, stroke=stroke, stroke_width=stroke_width)
            group.add(path)
            self.object_groups[object_id].append(("path", {"d": d}))
            return True
        except Exception:
            return False

    def draw_text(self, object_id: str, x: float, y: float, text: str,
                  fill: str = "black", font_size: str = "16px") -> bool:
        """Draw text."""
        try:
            group = self.get_or_create_group(object_id)
            text_elem = self.drawing.text(text, insert=(x, y), fill=fill, font_size=font_size)
            group.add(text_elem)
            self.object_groups[object_id].append(("text", {"x": x, "y": y, "text": text}))
            return True
        except Exception:
            return False

    def save(self, filepath: str) -> None:
        """Save the SVG to a file."""
        if self.drawing is not None:
            self.drawing.saveas(filepath)

    def show(self) -> None:
        """Display the drawing (SVG doesn't have a built-in display)."""
        print(f"[SVG] Drawing complete. Use save() to export the file.")

    def cleanup(self) -> None:
        """Clean up resources."""
        self.drawing = None
        self._groups = {}
