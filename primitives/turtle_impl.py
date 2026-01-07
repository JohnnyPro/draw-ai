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

    def draw_line(self, x1: int, y1: int, x2: int, y2: int, color: str = 'black', width: int = 1):
        self._set_pen_style(color, int(width))
        self.pen.penup()
        self.pen.goto(int(x1), int(y1))
        self.pen.pendown()
        self.pen.goto(int(x2), int(y2))
        self.pen.penup()

    def draw_arc(self, center_x: int, center_y: int, radius: int, start_angle: int, end_angle: int, color: str = 'black', width: int = 1):
        self._set_pen_style(color, int(width))
        self.pen.penup()

        # Move to the starting point of the arc on the circumference
        self.pen.goto(int(center_x), int(center_y))
        self.pen.setheading(int(start_angle)) # Face the start angle direction
        self.pen.forward(int(radius)) # Move to circumference
        # Adjust heading to be tangent for drawing counter-clockwise with positive radius
        self.pen.setheading(int(start_angle) + 90)

        self.pen.pendown()
        extent = int(end_angle) - int(start_angle)
        self.pen.circle(int(radius), extent=extent)
        self.pen.penup()


    def draw_circle(self, center_x: int, center_y: int, radius: int, fill_color: typing.Optional[str] = None, stroke_color: typing.Optional[str] = None, stroke_width: int = 1):
        center_x, center_y, radius, stroke_width = int(center_x), int(center_y), int(radius), int(stroke_width)
        self.pen.penup()
        # Go to the 'top' of the circle in this coord system for circle drawing
        self.pen.goto(center_x, center_y - radius)

        # Set fill and stroke
        self._set_fill_style(fill_color)
        self._set_pen_style(stroke_color, stroke_width)

        if fill_color:
            self.pen.begin_fill()
        
        # Only draw the outline if a stroke color is provided
        if stroke_color and stroke_width > 0:
            self.pen.pendown()
            self.pen.circle(radius)
            self.pen.penup()

        if fill_color:
            self.pen.end_fill()
            # If there was no stroke, we still need to draw the filled circle
            if not (stroke_color and stroke_width > 0):
                self.pen.goto(center_x, center_y - radius)
                self.pen.pendown()
                self.pen.circle(radius)
                self.pen.penup()



    def draw_triangle(self, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, fill_color: typing.Optional[str] = None, stroke_color: typing.Optional[str] = None, stroke_width: int = 1):
        self._set_fill_style(fill_color)
        self._set_pen_style(stroke_color, int(stroke_width))

        self.pen.penup()
        self.pen.goto(int(x1), int(y1))
        
        if fill_color:
            self.pen.begin_fill()
        
        if stroke_color or fill_color:
            self.pen.pendown()
            self.pen.goto(int(x2), int(y2))
            self.pen.goto(int(x3), int(y3))
            self.pen.goto(int(x1), int(y1)) # Close the triangle
            self.pen.penup()

        if fill_color:
            self.pen.end_fill()


    def draw_rectangle(self, x: int, y: int, width: int, height: int, fill_color: typing.Optional[str] = None, stroke_color: typing.Optional[str] = None, stroke_width: int = 1):
        self._set_fill_style(fill_color)
        self._set_pen_style(stroke_color, int(stroke_width))
        x, y, width, height = int(x), int(y), int(width), int(height)

        self.pen.penup()
        self.pen.goto(x, y)

        if fill_color:
            self.pen.begin_fill()

        if stroke_color or fill_color:
            self.pen.pendown()
            self.pen.goto(x + width, y)
            self.pen.goto(x + width, y + height) # Y increases downwards due to setworldcoordinates
            self.pen.goto(x, y + height)
            self.pen.goto(x, y) # Close the rectangle
            self.pen.penup()

        if fill_color:
            self.pen.end_fill()


    def draw_star(self, center_x: int, center_y: int, outer_radius: int, inner_radius: int, points: int, fill_color: typing.Optional[str] = None, stroke_color: typing.Optional[str] = None, stroke_width: int = 1):
        if points < 3:
            return

        center_x, center_y, outer_radius, inner_radius, points = int(center_x), int(center_y), int(outer_radius), int(inner_radius), int(points)
        self._set_fill_style(fill_color)
        self._set_pen_style(stroke_color, int(stroke_width))

        self.pen.penup()

        star_points = []
        for i in range(2 * points):
            angle = math.pi / points * i
            r = outer_radius if i % 2 == 0 else inner_radius
            x = center_x + r * math.sin(angle)
            y = center_y + r * math.cos(angle) # Y-axis direction is handled by world coordinates
            star_points.append((x, y))

        self.pen.goto(star_points[0])
        
        if fill_color:
            self.pen.begin_fill()
        
        if stroke_color or fill_color:
            self.pen.pendown()
            for i in range(1, len(star_points)):
                self.pen.goto(star_points[i])
            self.pen.goto(star_points[0]) # Close the shape
            self.pen.penup()
        
        if fill_color:
            self.pen.end_fill()

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
