import typing

def draw_line(x1: int, y1: int, x2: int, y2: int, color: str, width: int):
    """
    Draws a straight line from point (x1, y1) to point (x2, y2).

    :param x1: The x-coordinate of the starting point.
    :param y1: The y-coordinate of the starting point.
    :param x2: The x-coordinate of the ending point.
    :param y2: The y-coordinate of the ending point.
    :param color: The color of the line in a format like 'red' or '#FF0000'.
    :param width: The width of the line.
    """
    pass

def draw_arc(center_x: int, center_y: int, radius: int, start_angle: int, end_angle: int, color: str, width: int):
    """
    Draws an arc (a portion of a circle's circumference).

    :param center_x: The x-coordinate of the center of the circle from which the arc is derived.
    :param center_y: The y-coordinate of the center of the circle.
    :param radius: The radius of the circle.
    :param start_angle: The starting angle of the arc in degrees. 0 degrees is at the 3 o'clock position.
    :param end_angle: The ending angle of the arc in degrees.
    :param color: The color of the arc.
    :param width: The width of the arc's line.
    """
    pass

def draw_circle(center_x: int, center_y: int, radius: int, fill_color: typing.Optional[str], stroke_color: typing.Optional[str], stroke_width: int):
    """
    Draws a circle.

    :param center_x: The x-coordinate of the center of the circle.
    :param center_y: The y-coordinate of the center of the circle.
    :param radius: The radius of the circle.
    :param fill_color: The color to fill the circle with. Use None for no fill.
    :param stroke_color: The color of the circle's outline. Use None for no outline.
    :param stroke_width: The width of the circle's outline.
    """
    pass

def draw_triangle(x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, fill_color: typing.Optional[str], stroke_color: typing.Optional[str], stroke_width: int):
    """
    Draws a triangle using the three provided points as vertices.

    :param x1: The x-coordinate of the first vertex.
    :param y1: The y-coordinate of the first vertex.
    :param x2: The x-coordinate of the second vertex.
    :param y2: The y-coordinate of the second vertex.
    :param x3: The x-coordinate of the third vertex.
    :param y3: The y-coordinate of the third vertex.
    :param fill_color: The color to fill the triangle with. Use None for no fill.
    :param stroke_color: The color of the triangle's outline. Use None for no outline.
    :param stroke_width: The width of the triangle's outline.
    """
    pass

def draw_rectangle(x: int, y: int, width: int, height: int, fill_color: typing.Optional[str], stroke_color: typing.Optional[str], stroke_width: int):
    """
    Draws a rectangle.

    :param x: The x-coordinate of the top-left corner of the rectangle.
    :param y: The y-coordinate of the top-left corner of the rectangle.
    :param width: The width of the rectangle.
    :param height: The height of the rectangle.
    :param fill_color: The color to fill the rectangle with. Use None for no fill.
    :param stroke_color: The color of the rectangle's outline. Use None for no outline.
    :param stroke_width: The width of the rectangle's outline.
    """
    pass

def draw_star(center_x: int, center_y: int, outer_radius: int, inner_radius: int, points: int, fill_color: typing.Optional[str], stroke_color: typing.Optional[str], stroke_width: int):
    """
    Draws a star shape.

    :param center_x: The x-coordinate of the center of the star.
    :param center_y: The y-coordinate of the center of the star.
    :param outer_radius: The distance from the center to the outer points of the star.
    :param inner_radius: The distance from the center to the inner points of the star.
    :param points: The number of points on the star.
    :param fill_color: The color to fill the star with. Use None for no fill.
    :param stroke_color: The color of the star's outline. Use None for no outline.
    :param stroke_width: The width of the star's outline.
    """
    pass
