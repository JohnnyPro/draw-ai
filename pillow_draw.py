"""
Pillow (PIL) Drawing Backend

Implements the BaseDraw interface using the Pillow library for raster image output.
"""

import re
import math
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from base_draw import BaseDraw, DrawingConfig


class PillowDraw(BaseDraw):
    """Pillow (PIL) drawing backend."""

    def __init__(self, config: DrawingConfig):
        super().__init__(config)
        self.image: Optional[Image.Image] = None
        self.draw: Optional[ImageDraw.ImageDraw] = None

    @property
    def backend_name(self) -> str:
        return "pillow"

    @property
    def supported_elements(self) -> list[str]:
        return ["circle", "ellipse", "rect", "line", "polyline", "polygon", "path", "text"]

    @property
    def system_prompt_instructions(self) -> str:
        return """You are a Pillow (PIL) drawing assistant.
Generate SVG-like code that will be translated to Pillow drawing commands. Follow these STRICT rules:

1. Output ONLY raw SVG-like elements (circle, rect, ellipse, line, polyline, polygon, path, text).
2. Use a standard SVG coordinate system (0,0 at top-left, y increases downward). Coordinates will be translated automatically.
3. Keep shapes simple. Complex paths with Bezier curves (Q, C) will be approximated with straight lines.
4. For smooth curves, prefer using polygons with many points.
5. Colors MUST be valid SVG/CSS color names (e.g., 'skyblue', 'red') or Hex codes (e.g., '#87CEEB'). 'none' can be used for no fill.

Example valid elements:
<circle cx="100" cy="100" r="50" fill="red" stroke="black" stroke-width="2"/>
<rect x="50" y="50" width="100" height="80" fill="blue" stroke="black"/>
<polygon points="100,10 40,198 190,78" fill="lime" stroke="purple"/>
<text x="100" y="100" fill="black" font-size="16px">Hello</text>"""

    def initialize(self) -> None:
        """Initialize the Pillow image and drawing context."""
        self.image = Image.new("RGB", (self.width, self.height), self.background)
        self.draw = ImageDraw.Draw(self.image)
        self.element_count = 0

    def get_or_create_group(self, object_id: str) -> None:
        """Pillow doesn't have groups, but we track elements per object."""
        if object_id not in self.object_groups:
            self.object_groups[object_id] = []

    def add_code(self, object_id: str, code: str) -> int:
        """Parse SVG-like code and draw using Pillow."""
        elements_added = 0
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

    def _parse_color(self, color_str: str) -> Optional[str]:
        """Return color string if valid, else None."""
        if not color_str or color_str.lower() == 'none':
            return None
        return color_str
    
    def _parse_and_add_circles(self, object_id: str, code: str) -> int:
        count = 0
        pattern = r'<circle\s+([^>]*)/?>'
        for match in re.finditer(pattern, code, re.IGNORECASE):
            attrs = self._parse_attributes(match.group(1))
            try:
                if self.draw_circle(object_id, float(attrs.get("cx", 0)), float(attrs.get("cy", 0)), float(attrs.get("r", 10)),
                                     attrs.get("fill", "none"), attrs.get("stroke", "black"), float(attrs.get("stroke-width", "1"))):
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
                if self.draw_ellipse(object_id, float(attrs.get("cx", 0)), float(attrs.get("cy", 0)), float(attrs.get("rx", 10)), float(attrs.get("ry", 10)),
                                      attrs.get("fill", "none"), attrs.get("stroke", "black"), float(attrs.get("stroke-width", "1"))):
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
                if self.draw_rect(object_id, float(attrs.get("x", 0)), float(attrs.get("y", 0)), float(attrs.get("width", 10)), float(attrs.get("height", 10)),
                                   attrs.get("fill", "none"), attrs.get("stroke", "black"), float(attrs.get("stroke-width", "1"))):
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
                if self.draw_line(object_id, float(attrs.get("x1", 0)), float(attrs.get("y1", 0)), float(attrs.get("x2", 0)), float(attrs.get("y2", 0)),
                                   attrs.get("stroke", "black"), float(attrs.get("stroke-width", "1"))):
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
                points = self._parse_points(attrs.get("points", ""))
                if self.draw_polyline(object_id, points, attrs.get("fill", "none"), attrs.get("stroke", "black"), float(attrs.get("stroke-width", "1"))):
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
                points = self._parse_points(attrs.get("points", ""))
                if self.draw_polygon(object_id, points, attrs.get("fill", "none"), attrs.get("stroke", "black"), float(attrs.get("stroke-width", "1"))):
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
                if self.draw_path(object_id, attrs.get("d", ""), attrs.get("fill", "none"), attrs.get("stroke", "black"), float(attrs.get("stroke-width", "1"))):
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
                if self.draw_text(object_id, float(attrs.get("x", 0)), float(attrs.get("y", 0)), text_content, attrs.get("fill", "black"), attrs.get("font-size", "16px")):
                    count += 1
            except (ValueError, KeyError):
                continue
        return count

    def draw_circle(self, object_id: str, cx: float, cy: float, r: float, fill: str, stroke: str, stroke_width: float) -> bool:
        self.get_or_create_group(object_id)
        box = (cx - r, cy - r, cx + r, cy + r)
        self.draw.ellipse(box, fill=self._parse_color(fill), outline=self._parse_color(stroke), width=int(stroke_width))
        self.object_groups[object_id].append(("circle", {"cx": cx, "cy": cy, "r": r}))
        return True

    def draw_ellipse(self, object_id: str, cx: float, cy: float, rx: float, ry: float, fill: str, stroke: str, stroke_width: float) -> bool:
        self.get_or_create_group(object_id)
        box = (cx - rx, cy - ry, cx + rx, cy + ry)
        self.draw.ellipse(box, fill=self._parse_color(fill), outline=self._parse_color(stroke), width=int(stroke_width))
        self.object_groups[object_id].append(("ellipse", {"cx": cx, "cy": cy, "rx": rx, "ry": ry}))
        return True

    def draw_rect(self, object_id: str, x: float, y: float, width: float, height: float, fill: str, stroke: str, stroke_width: float, rx: Optional[float] = None, ry: Optional[float] = None) -> bool:
        self.get_or_create_group(object_id)
        self.draw.rectangle((x, y, x + width, y + height), fill=self._parse_color(fill), outline=self._parse_color(stroke), width=int(stroke_width))
        self.object_groups[object_id].append(("rect", {"x": x, "y": y, "width": width, "height": height}))
        return True

    def draw_line(self, object_id: str, x1: float, y1: float, x2: float, y2: float, stroke: str, stroke_width: float) -> bool:
        self.get_or_create_group(object_id)
        self.draw.line((x1, y1, x2, y2), fill=self._parse_color(stroke), width=int(stroke_width))
        self.object_groups[object_id].append(("line", {"x1": x1, "y1": y1, "x2": x2, "y2": y2}))
        return True

    def draw_polyline(self, object_id: str, points: list[tuple[float, float]], fill: str, stroke: str, stroke_width: float) -> bool:
        self.get_or_create_group(object_id)
        if self._parse_color(fill): # Polylines are not filled in SVG, but Pillow can fill them if we close the shape
            self.draw.polygon(points, fill=self._parse_color(fill))
        self.draw.line(points, fill=self._parse_color(stroke), width=int(stroke_width))
        self.object_groups[object_id].append(("polyline", {"points": points}))
        return True

    def draw_polygon(self, object_id: str, points: list[tuple[float, float]], fill: str, stroke: str, stroke_width: float) -> bool:
        self.get_or_create_group(object_id)
        self.draw.polygon(points, fill=self._parse_color(fill), outline=self._parse_color(stroke), width=int(stroke_width))
        self.object_groups[object_id].append(("polygon", {"points": points}))
        return True

    def draw_path(self, object_id: str, d: str, fill: str, stroke: str, stroke_width: float) -> bool:
        """Approximates an SVG path with line segments."""
        self.get_or_create_group(object_id)
        tokens = re.findall(r'[MmLlHhVvCcSsQqTtAaZz]|[-\d.]+', d)
        points = []
        current_x, current_y = 0.0, 0.0
        i = 0
        while i < len(tokens):
            cmd = tokens[i]
            i += 1
            if cmd in 'Mm':
                if points: self.draw.line(points, fill=self._parse_color(stroke), width=int(stroke_width))
                points = []
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                if cmd == 'm': x += current_x; y += current_y
                points.append((x,y)); current_x, current_y = x, y
            elif cmd in 'Ll':
                x, y = float(tokens[i]), float(tokens[i + 1]); i += 2
                if cmd == 'l': x += current_x; y += current_y
                points.append((x,y)); current_x, current_y = x, y
            elif cmd in 'Hh':
                x = float(tokens[i]); i += 1
                if cmd == 'h': x += current_x
                points.append((x, current_y)); current_x = x
            elif cmd in 'Vv':
                y = float(tokens[i]); i += 1
                if cmd == 'v': y += current_y
                points.append((current_x, y)); current_y = y
            elif cmd in 'Zz':
                if points: self.draw.polygon(points, fill=self._parse_color(fill), outline=self._parse_color(stroke), width=int(stroke_width))
                points = []
            elif cmd in 'CcSsQqTt': # Approximate curves with lines
                num_params = {'C': 6, 'c': 6, 'S': 4, 's': 4, 'Q': 4, 'q': 4, 'T': 2, 't': 2}[cmd]
                x, y = float(tokens[i + num_params - 2]), float(tokens[i + num_params - 1])
                i += num_params
                if cmd.islower(): x += current_x; y += current_y
                points.append((x, y)); current_x, current_y = x, y
            elif cmd in 'Aa':
                i += 7 # Skip arcs
        if points: self.draw.line(points, fill=self._parse_color(stroke), width=int(stroke_width))
        self.object_groups[object_id].append(("path", {"d": d}))
        return True

    def draw_text(self, object_id: str, x: float, y: float, text: str, fill: str, font_size: str) -> bool:
        self.get_or_create_group(object_id)
        try:
            size = int(re.match(r'(\d+)', font_size).group(1)) if re.match(r'(\d+)', font_size) else 16
            font = ImageFont.truetype("arial.ttf", size)
        except IOError:
            font = ImageFont.load_default()
        self.draw.text((x, y), text, fill=self._parse_color(fill), font=font)
        self.object_groups[object_id].append(("text", {"x": x, "y": y, "text": text}))
        return True

    def save(self, filepath: str) -> None:
        if self.image:
            self.image.save(filepath)

    def show(self) -> None:
        if self.image:
            self.image.show()

    def cleanup(self) -> None:
        self.image = None
        self.draw = None
