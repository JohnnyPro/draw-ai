import math
import typing

class SVGDrawer:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.elements = []

    def _get_style_attributes(self, fill_color: typing.Optional[str], stroke_color: typing.Optional[str], stroke_width: int):
        style = []
        if fill_color:
            style.append(f"fill:{fill_color}")
        else:
            style.append("fill:none")

        if stroke_color and stroke_width > 0:
            style.append(f"stroke:{stroke_color}")
            style.append(f"stroke-width:{stroke_width}")
        else:
            style.append("stroke:none")
        return ";".join(style)

    def draw_line(self, x1: int, y1: int, x2: int, y2: int, color: str, width: int):
        self.elements.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke:{color};stroke-width:{width}" />')

    def draw_arc(self, center_x: int, center_y: int, radius: int, start_angle: int, end_angle: int, color: str, width: int):
        # Normalize angles to be between 0 and 360
        start_angle %= 360
        end_angle %= 360

        # Ensure end_angle is greater than start_angle for path calculation if it's a "forward" arc
        if end_angle < start_angle:
            end_angle += 360

        start_angle_rad = math.radians(start_angle)
        end_angle_rad = math.radians(end_angle)

        start_x = center_x + radius * math.cos(start_angle_rad)
        start_y = center_y + radius * math.sin(start_angle_rad)

        end_x = center_x + radius * math.cos(end_angle_rad)
        end_y = center_y + radius * math.sin(end_angle_rad)

        # large-arc-flag: 1 if arc is > 180 degrees, 0 otherwise
        large_arc_flag = 1 if (end_angle - start_angle) > 180 else 0
        # sweep-flag: 1 for clockwise, 0 for counter-clockwise.
        # Assuming counter-clockwise progression for positive angle increase.
        sweep_flag = 0

        path_data = (
            f"M {start_x},{start_y} "
            f"A {radius},{radius} 0 {large_arc_flag},{sweep_flag} {end_x},{end_y}"
        )
        self.elements.append(f'<path d="{path_data}" style="fill:none;stroke:{color};stroke-width:{width}" />')


    def draw_circle(self, center_x: int, center_y: int, radius: int, fill_color: typing.Optional[str], stroke_color: typing.Optional[str], stroke_width: int):
        style = self._get_style_attributes(fill_color, stroke_color, stroke_width)
        self.elements.append(f'<circle cx="{center_x}" cy="{center_y}" r="{radius}" style="{style}" />')

    def draw_triangle(self, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, fill_color: typing.Optional[str], stroke_color: typing.Optional[str], stroke_width: int):
        points = f"{x1},{y1} {x2},{y2} {x3},{y3}"
        style = self._get_style_attributes(fill_color, stroke_color, stroke_width)
        self.elements.append(f'<polygon points="{points}" style="{style}" />')

    def draw_rectangle(self, x: int, y: int, width: int, height: int, fill_color: typing.Optional[str], stroke_color: typing.Optional[str], stroke_width: int):
        style = self._get_style_attributes(fill_color, stroke_color, stroke_width)
        self.elements.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" style="{style}" />')

    def draw_star(self, center_x: int, center_y: int, outer_radius: int, inner_radius: int, points: int, fill_color: typing.Optional[str], stroke_color: typing.Optional[str], stroke_width: int):
        if points < 3:
            raise ValueError("A star must have at least 3 points.")

        star_points = []
        for i in range(2 * points):
            angle = math.pi / points * i
            r = outer_radius if i % 2 == 0 else inner_radius
            # SVG uses standard Cartesian coordinates, positive Y is down
            x = center_x + r * math.sin(angle)
            y = center_y + r * math.cos(angle)
            star_points.append(f"{x},{y}")

        points_str = " ".join(star_points)
        style = self._get_style_attributes(fill_color, stroke_color, stroke_width)
        self.elements.append(f'<polygon points="{points_str}" style="{style}" />')

    def save(self, filename: str):
        svg_content = (
            f'<svg width="{self.width}" height="{self.height}" xmlns="http://www.w3.org/2000/svg">\n'
            + "".join(self.elements) + 
            '\n</svg>'
        )
        with open(filename, 'w') as f:
            f.write(svg_content)
