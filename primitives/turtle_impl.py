import turtle
import typing
import math

class TurtleDrawer:
    def __init__(self, width: int, height: int, background_color: str = 'white'):
        self.screen = turtle.Screen()
        self.screen.setup(width=width, height=height)
        self.screen.bgcolor(background_color)
        # Set origin to top-left, Y increases downwards to match other drawing libs
        self.screen.setworldcoordinates(0, height, width, 0)
        self.screen.tracer(0) # Turn off screen updates for faster drawing

        self.pen = turtle.Turtle()
        self.pen.speed(0) # Fastest speed
        self.pen.penup()

    def _set_pen_style(self, color: typing.Optional[str], width: int):
        if color and width > 0:
            self.pen.pencolor(color)
            self.pen.pensize(width)
            self.pen.showturtle()
        else:
            self.pen.penup() # Effectively no stroke if no color or width 0
            self.pen.hideturtle()


    def _set_fill_style(self, fill_color: typing.Optional[str]):
        if fill_color:
            self.pen.fillcolor(fill_color)
        # No explicit 'unset' fill color, just control begin_fill/end_fill outside

    def draw_line(self, x1: int, y1: int, x2: int, y2: int, color: str, width: int):
        self._set_pen_style(color, width)
        self.pen.penup()
        self.pen.goto(x1, y1)
        self.pen.pendown()
        self.pen.goto(x2, y2)
        self.pen.penup()

    def draw_arc(self, center_x: int, center_y: int, radius: int, start_angle: int, end_angle: int, color: str, width: int):
        self._set_pen_style(color, width)
        self.pen.penup()

        # Move to the starting point of the arc on the circumference
        self.pen.goto(center_x, center_y)
        self.pen.setheading(start_angle) # Face the start angle direction
        self.pen.forward(radius) # Move to circumference
        # Adjust heading to be tangent for drawing counter-clockwise with positive radius
        self.pen.setheading(start_angle + 90)

        self.pen.pendown()
        extent = end_angle - start_angle
        self.pen.circle(radius, extent=extent)
        self.pen.penup()


    def draw_circle(self, center_x: int, center_y: int, radius: int, fill_color: typing.Optional[str], stroke_color: typing.Optional[str], stroke_width: int):
        self.pen.penup()
        # Go to the 'top' of the circle in this coord system for circle drawing
        self.pen.goto(center_x, center_y - radius)

        # Set fill and stroke
        self._set_fill_style(fill_color)
        self._set_pen_style(stroke_color, stroke_width)

        if fill_color:
            self.pen.begin_fill()
        self.pen.pendown()
        self.pen.circle(radius)
        self.pen.penup()
        if fill_color:
            self.pen.end_fill()


    def draw_triangle(self, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, fill_color: typing.Optional[str], stroke_color: typing.Optional[str], stroke_width: int):
        self._set_fill_style(fill_color)
        self._set_pen_style(stroke_color, stroke_width)

        self.pen.penup()
        self.pen.goto(x1, y1)
        self.pen.pendown()
        if fill_color:
            self.pen.begin_fill()
        self.pen.goto(x2, y2)
        self.pen.goto(x3, y3)
        self.pen.goto(x1, y1) # Close the triangle
        if fill_color:
            self.pen.end_fill()
        self.pen.penup()

    def draw_rectangle(self, x: int, y: int, width: int, height: int, fill_color: typing.Optional[str], stroke_color: typing.Optional[str], stroke_width: int):
        self._set_fill_style(fill_color)
        self._set_pen_style(stroke_color, stroke_width)

        self.pen.penup()
        self.pen.goto(x, y)
        self.pen.pendown()
        if fill_color:
            self.pen.begin_fill()
        self.pen.goto(x + width, y)
        self.pen.goto(x + width, y + height) # Y increases downwards due to setworldcoordinates
        self.pen.goto(x, y + height)
        self.pen.goto(x, y) # Close the rectangle
        if fill_color:
            self.pen.end_fill()
        self.pen.penup()

    def draw_star(self, center_x: int, center_y: int, outer_radius: int, inner_radius: int, points: int, fill_color: typing.Optional[str], stroke_color: typing.Optional[str], stroke_width: int):
        if points < 3:
            raise ValueError("A star must have at least 3 points.")

        self._set_fill_style(fill_color)
        self._set_pen_style(stroke_color, stroke_width)

        self.pen.penup()

        star_points = []
        for i in range(2 * points):
            angle = math.pi / points * i
            r = outer_radius if i % 2 == 0 else inner_radius
            x = center_x + r * math.sin(angle)
            y = center_y + r * math.cos(angle) # Y-axis direction is handled by world coordinates
            star_points.append((x, y))

        self.pen.goto(star_points[0])
        self.pen.pendown()
        if fill_color:
            self.pen.begin_fill()
        for i in range(1, len(star_points)):
            self.pen.goto(star_points[i])
        self.pen.goto(star_points[0]) # Close the shape
        if fill_color:
            self.pen.end_fill()
        self.pen.penup()

    def save(self, filename: str):
        self.screen.update()
        # For actual image file output from turtle, it typically requires saving as Postscript (.eps)
        # and then converting using an external tool (e.g., Ghostscript).
        # We will save to a Postscript file and the filename should reflect that.
        # The user will need to convert this .eps file to a raster image (like PNG) if desired.
        if not filename.lower().endswith(".eps"):
            filename += ".eps"
        self.screen.getcanvas().postscript(file=filename)

    def done(self):
        self.screen.exitonclick()
