import typing

def draw_line(x1: int, y1: int, x2: int, y2: int, color: str = 'black', width: int = 1):
    """
    Draws a straight line from a starting point to an ending point.

    :param x1: The x-coordinate of the starting point.
    :param y1: The y-coordinate of the starting point.
    :param x2: The x-coordinate of the ending point.
    :param y2: The y-coordinate of the ending point.
    :param color: The color of the line (e.g., 'red', '#FF0000'). Defaults to 'black'.
    :param width: The width of the line in pixels. Defaults to 1.
    """
    pass

def draw_arc(center_x: int, center_y: int, radius: int, start_angle: int, end_angle: int, color: str = 'black', width: int = 1):
    """
    Draws an arc, which is a portion of the circumference of a circle.

    :param center_x: The x-coordinate of the center of the circle from which the arc is taken.
    :param center_y: The y-coordinate of the center of the circle.
    :param radius: The radius of the circle.
    :param start_angle: The starting angle of the arc in degrees. 0 degrees is at the 3 o'clock position, increasing counter-clockwise.
    :param end_angle: The ending angle of the arc in degrees.
    :param color: The color of the arc's line (e.g., 'green', '#00FF00'). Defaults to 'black'.
    :param width: The width of the arc's line in pixels. Defaults to 1.
    """
    pass

def draw_circle(center_x: int, center_y: int, radius: int, fill_color: typing.Optional[str] = None, stroke_color: typing.Optional[str] = None, stroke_width: int = 1):
    """
    Draws a circle on the canvas. You can specify a fill color and/or an outline (stroke).

    :param center_x: The x-coordinate for the center of the circle.
    :param center_y: The y-coordinate for the center of the circle.
    :param radius: The radius of the circle in pixels.
    :param fill_color: Optional. The color to fill the inside of the circle (e.g., 'red', '#FF0000'). If omitted, the circle will not be filled.
    :param stroke_color: Optional. The color for the circle's outline (e.g., 'blue', '#0000FF'). If omitted, the circle will have no outline.
    :param stroke_width: Optional. The width of the outline in pixels. Defaults to 1. Only applies if 'stroke_color' is specified.
    """
    pass

def draw_triangle(x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, fill_color: typing.Optional[str] = None, stroke_color: typing.Optional[str] = None, stroke_width: int = 1):
    """
    Draws a triangle using three specified points as its vertices.

    :param x1: The x-coordinate of the first vertex.
    :param y1: The y-coordinate of the first vertex.
    :param x2: The x-coordinate of the second vertex.
    :param y2: The y-coordinate of the second vertex.
    :param x3: The x-coordinate of the third vertex.
    :param y3: The y-coordinate of the third vertex.
    :param fill_color: Optional. The color to fill the inside of the triangle (e.g., 'yellow'). If omitted, the triangle will not be filled.
    :param stroke_color: Optional. The color for the triangle's outline. If omitted, the triangle will have no outline.
    :param stroke_width: Optional. The width of the outline in pixels. Defaults to 1. Only applies if 'stroke_color' is specified.
    """
    pass

def draw_rectangle(x: int, y: int, width: int, height: int, fill_color: typing.Optional[str] = None, stroke_color: typing.Optional[str] = None, stroke_width: int = 1):
    """
    Draws a rectangle on the canvas.

    :param x: The x-coordinate of the top-left corner of the rectangle.
    :param y: The y-coordinate of the top-left corner of the rectangle.
    :param width: The width of the rectangle in pixels.
    :param height: The height of the rectangle in pixels.
    :param fill_color: Optional. The color to fill the inside of the rectangle (e.g., 'purple'). If omitted, the rectangle will not be filled.
    :param stroke_color: Optional. The color for the rectangle's outline. If omitted, the rectangle will have no outline.
    :param stroke_width: Optional. The width of the outline in pixels. Defaults to 1. Only applies if 'stroke_color' is specified.
    """
    pass

def draw_star(center_x: int, center_y: int, outer_radius: int, inner_radius: int, points: int, fill_color: typing.Optional[str] = None, stroke_color: typing.Optional[str] = None, stroke_width: int = 1):
    """
    Draws a star shape, defined by its center, radii, and number of points.

    :param center_x: The x-coordinate of the center of the star.
    :param center_y: The y-coordinate of the center of the star.
    :param outer_radius: The distance from the center to the outer points of the star.
    :param inner_radius: The distance from the center to the inner points of the star. Must be less than outer_radius.
    :param points: The number of points on the star (e.g., 5 for a classic star).
    :param fill_color: Optional. The color to fill the inside of the star. If omitted, the star will not be filled.
    :param stroke_color: Optional. The color for the star's outline. If omitted, the star will have no outline.
    :param stroke_width: Optional. The width of the outline in pixels. Defaults to 1. Only applies if 'stroke_color' is specified.
    """
    pass
