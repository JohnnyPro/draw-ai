import math
from PIL import Image, ImageDraw
import typing

class PillowDrawer:
    def __init__(self, width: int, height: int, background_color: str = 'white'):
        self.image = Image.new('RGB', (width, height), color=background_color)
        self.draw = ImageDraw.Draw(self.image)

    def draw_line(self, x1: int, y1: int, x2: int, y2: int, color: str, width: int):
        self.draw.line([(x1, y1), (x2, y2)], fill=color, width=width)

    def draw_arc(self, center_x: int, center_y: int, radius: int, start_angle: int, end_angle: int, color: str, width: int):
        # Pillow's arc uses a bounding box, angles are in degrees
        bbox = [center_x - radius, center_y - radius, center_x + radius, center_y + radius]
        self.draw.arc(bbox, start_angle, end_angle, fill=color, width=width)

    def draw_circle(self, center_x: int, center_y: int, radius: int, fill_color: typing.Optional[str], stroke_color: typing.Optional[str], stroke_width: int):
        bbox = [center_x - radius, center_y - radius, center_x + radius, center_y + radius]
        if fill_color:
            self.draw.ellipse(bbox, fill=fill_color, outline=stroke_color if stroke_color and stroke_width > 0 else None, width=stroke_width if stroke_color and stroke_width > 0 else 0)
        elif stroke_color and stroke_width > 0:
            self.draw.ellipse(bbox, outline=stroke_color, width=stroke_width)

    def draw_triangle(self, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, fill_color: typing.Optional[str], stroke_color: typing.Optional[str], stroke_width: int):
        points = [(x1, y1), (x2, y2), (x3, y3)]
        if fill_color:
            self.draw.polygon(points, fill=fill_color)
        if stroke_color and stroke_width > 0:
            # Pillow's polygon outline does not support width directly, so draw lines manually.
            self.draw.line([points[0], points[1]], fill=stroke_color, width=stroke_width)
            self.draw.line([points[1], points[2]], fill=stroke_color, width=stroke_width)
            self.draw.line([points[2], points[0]], fill=stroke_color, width=stroke_width)


    def draw_rectangle(self, x: int, y: int, width: int, height: int, fill_color: typing.Optional[str], stroke_color: typing.Optional[str], stroke_width: int):
        bbox = [x, y, x + width, y + height]
        if fill_color:
            self.draw.rectangle(bbox, fill=fill_color, outline=stroke_color if stroke_color and stroke_width > 0 else None, width=stroke_width if stroke_color and stroke_width > 0 else 0)
        elif stroke_color and stroke_width > 0:
            self.draw.rectangle(bbox, outline=stroke_color, width=stroke_width)

    def draw_star(self, center_x: int, center_y: int, outer_radius: int, inner_radius: int, points: int, fill_color: typing.Optional[str], stroke_color: typing.Optional[str], stroke_width: int):
        if points < 3:
            raise ValueError("A star must have at least 3 points.")

        star_points = []
        for i in range(2 * points):
            angle = math.pi / points * i
            r = outer_radius if i % 2 == 0 else inner_radius
            x = center_x + r * math.sin(angle)
            y = center_y - r * math.cos(angle)
            star_points.append((x, y))

        if fill_color:
            self.draw.polygon(star_points, fill=fill_color)
        if stroke_color and stroke_width > 0:
            # Pillow's polygon outline does not support width directly, so draw lines manually.
            for i in range(len(star_points)):
                self.draw.line([star_points[i], star_points[(i + 1) % len(star_points)]], fill=stroke_color, width=stroke_width)

    def save(self, filename: str):
        self.image.save(filename)
