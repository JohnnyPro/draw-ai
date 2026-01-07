import math
from PIL import Image, ImageDraw
import typing

class PillowDrawer:
    def __init__(self, width: int, height: int, background_color: str = 'white'):
        self.image = Image.new('RGB', (width, height), color=background_color)
        self.draw = ImageDraw.Draw(self.image)

    def draw_line(self, x1: int, y1: int, x2: int, y2: int, color: str = 'black', width: int = 1):
        self.draw.line([(int(x1), int(y1)), (int(x2), int(y2))], fill=color, width=int(width))

    def draw_arc(self, center_x: int, center_y: int, radius: int, start_angle: int, end_angle: int, color: str = 'black', width: int = 1):
        # Pillow's arc uses a bounding box, angles are in degrees
        center_x, center_y, radius = int(center_x), int(center_y), int(radius)
        bbox = [center_x - radius, center_y - radius, center_x + radius, center_y + radius]
        self.draw.arc(bbox, int(start_angle), int(end_angle), fill=color, width=int(width))

    def draw_circle(self, center_x: int, center_y: int, radius: int, fill_color: typing.Optional[str] = None, stroke_color: typing.Optional[str] = None, stroke_width: int = 1):
        center_x, center_y, radius, stroke_width = int(center_x), int(center_y), int(radius), int(stroke_width)
        bbox = [center_x - radius, center_y - radius, center_x + radius, center_y + radius]
        # Use a simplified logic: draw fill, then draw outline if specified
        if fill_color:
            self.draw.ellipse(bbox, fill=fill_color)
        if stroke_color and stroke_width > 0:
            self.draw.ellipse(bbox, outline=stroke_color, width=stroke_width)

    def draw_triangle(self, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, fill_color: typing.Optional[str] = None, stroke_color: typing.Optional[str] = None, stroke_width: int = 1):
        points = [(int(x1), int(y1)), (int(x2), int(y2)), (int(x3), int(y3))]
        stroke_width = int(stroke_width)
        if fill_color:
            self.draw.polygon(points, fill=fill_color)
        if stroke_color and stroke_width > 0:
            # Pillow's polygon outline does not support width directly, so draw lines manually.
            self.draw.line([points[0], points[1]], fill=stroke_color, width=stroke_width)
            self.draw.line([points[1], points[2]], fill=stroke_color, width=stroke_width)
            self.draw.line([points[2], points[0]], fill=stroke_color, width=stroke_width)


    def draw_rectangle(self, x: int, y: int, width: int, height: int, fill_color: typing.Optional[str] = None, stroke_color: typing.Optional[str] = None, stroke_width: int = 1):
        x, y, width, height, stroke_width = int(x), int(y), int(width), int(height), int(stroke_width)
        bbox = [x, y, x + width, y + height]
        if fill_color:
            self.draw.rectangle(bbox, fill=fill_color)
        if stroke_color and stroke_width > 0:
            self.draw.rectangle(bbox, outline=stroke_color, width=stroke_width)

    def draw_star(self, center_x: int, center_y: int, outer_radius: int, inner_radius: int, points: int, fill_color: typing.Optional[str] = None, stroke_color: typing.Optional[str] = None, stroke_width: int = 1):
        if points < 3:
            return # Or raise error

        center_x, center_y, outer_radius, inner_radius, points, stroke_width = int(center_x), int(center_y), int(outer_radius), int(inner_radius), int(points), int(stroke_width)

        star_points = []
        for i in range(2 * points):
            angle = math.pi / points * i
            r = outer_radius if i % 2 == 0 else inner_radius
            x = center_x + r * math.sin(angle)
            y = center_y - r * math.cos(angle)
            star_points.append((int(x), int(y)))

        if fill_color:
            self.draw.polygon(star_points, fill=fill_color)
        if stroke_color and stroke_width > 0:
            # Pillow's polygon outline does not support width directly, so draw lines manually.
            for i in range(len(star_points)):
                self.draw.line([star_points[i], star_points[(i + 1) % len(star_points)]], fill=stroke_color, width=stroke_width)

    def save(self, filename: str):
        self.image.save(filename)
