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

    def draw_line(self, x1: int, y1: int, x2: int, y2: int, color: str = 'black', width: int = 1):
        self.elements.append(f'<line x1="{int(x1)}" y1="{int(y1)}" x2="{int(x2)}" y2="{int(y2)}" style="stroke:{color};stroke-width:{int(width)}" />')

    def draw_arc(self, center_x: int, center_y: int, radius: int, start_angle: int, end_angle: int, color: str = 'black', width: int = 1):
        # Normalize angles to be between 0 and 360
        start_angle = int(start_angle) % 360
        end_angle = int(end_angle) % 360
        center_x, center_y, radius = int(center_x), int(center_y), int(radius)

        # Ensure end_angle is greater than start_angle for path calculation if it's a "forward" arc
        if end_angle <= start_angle:
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
        # SVG 'A' path command sweep-flag: 1 for positive-angle direction (counter-clockwise)
        sweep_flag = 1

        path_data = (
            f"M {start_x},{start_y} "
            f"A {radius},{radius} 0 {large_arc_flag},{sweep_flag} {end_x},{end_y}"
        )
        self.elements.append(f'<path d="{path_data}" style="fill:none;stroke:{color};stroke-width:{int(width)}" />')


    def draw_circle(self, center_x: int, center_y: int, radius: int, fill_color: typing.Optional[str] = None, stroke_color: typing.Optional[str] = None, stroke_width: int = 1):
        style = self._get_style_attributes(fill_color, stroke_color, int(stroke_width))
        self.elements.append(f'<circle cx="{int(center_x)}" cy="{int(center_y)}" r="{int(radius)}" style="{style}" />')

    def draw_triangle(self, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, fill_color: typing.Optional[str] = None, stroke_color: typing.Optional[str] = None, stroke_width: int = 1):
        points = f"{int(x1)},{int(y1)} {int(x2)},{int(y2)} {int(x3)},{int(y3)}"
        style = self._get_style_attributes(fill_color, stroke_color, int(stroke_width))
        self.elements.append(f'<polygon points="{points}" style="{style}" />')

    def draw_rectangle(self, x: int, y: int, width: int, height: int, fill_color: typing.Optional[str] = None, stroke_color: typing.Optional[str] = None, stroke_width: int = 1):
        style = self._get_style_attributes(fill_color, stroke_color, int(stroke_width))
        self.elements.append(f'<rect x="{int(x)}" y="{int(y)}" width="{int(width)}" height="{int(height)}" style="{style}" />')

    def draw_star(self, center_x: int, center_y: int, outer_radius: int, inner_radius: int, points: int, fill_color: typing.Optional[str] = None, stroke_color: typing.Optional[str] = None, stroke_width: int = 1):
        if points < 3:
            return # Or raise error

        center_x, center_y, outer_radius, inner_radius, points = int(center_x), int(center_y), int(outer_radius), int(inner_radius), int(points)

        star_points = []
        for i in range(2 * points):
            angle = math.pi / points * i
            # Adjust angle so the top point of the star is pointing up
            angle -= math.pi / 2
            r = outer_radius if i % 2 == 0 else inner_radius
            
            x = center_x + r * math.cos(angle)
            y = center_y + r * math.sin(angle)
            star_points.append(f"{x},{y}")

        points_str = " ".join(star_points)
        style = self._get_style_attributes(fill_color, stroke_color, int(stroke_width))
        self.elements.append(f'<polygon points="{points_str}" style="{style}" />')

    def save(self, filename: str):
        svg_content = (
            f'<svg width="{self.width}" height="{self.height}" xmlns="http://www.w3.org/2000/svg">\n'
            + "".join(self.elements) + 
            '\n</svg>'
        )
        with open(filename, 'w') as f:
            f.write(svg_content)
