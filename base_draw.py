"""
Base Drawing Class

Abstract base class that defines the interface for all drawing backends.
Concrete implementations (SVG, Turtle, etc.) must inherit from this class.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class DrawingConfig:
    """Configuration for drawing operations."""
    width: int = 800
    height: int = 800
    background: str = "white"


class BaseDraw(ABC):
    """
    Abstract base class for drawing backends.
    
    All drawing implementations must inherit from this class and implement
    the required abstract methods. This allows main.py to work with any
    drawing backend without knowing the implementation details.
    """

    def __init__(self, config: DrawingConfig):
        self.config = config
        self.width = config.width
        self.height = config.height
        self.background = config.background
        self.element_count = 0
        self.object_groups: dict[str, list] = {}

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Return the name of the drawing backend (e.g., 'svg', 'turtle')."""
        pass

    @property
    @abstractmethod
    def supported_elements(self) -> list[str]:
        """Return list of supported SVG-like element names."""
        pass

    @property
    @abstractmethod
    def system_prompt_instructions(self) -> str:
        """
        Return backend-specific instructions for the LLM system prompt.
        This helps the LLM generate code appropriate for this backend.
        """
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the drawing canvas/window."""
        pass

    @abstractmethod
    def get_or_create_group(self, object_id: str) -> None:
        """Create or get a group/layer for an object."""
        pass

    @abstractmethod
    def add_code(self, object_id: str, code: str) -> int:
        """
        Parse and add drawing code (SVG elements or turtle commands) for an object.
        
        Args:
            object_id: Identifier for the object being drawn
            code: The drawing code to parse and execute
            
        Returns:
            Number of elements/commands successfully added
        """
        pass

    @abstractmethod
    def draw_circle(self, object_id: str, cx: float, cy: float, r: float,
                    fill: str = "none", stroke: str = "black", stroke_width: float = 1) -> bool:
        """Draw a circle."""
        pass

    @abstractmethod
    def draw_ellipse(self, object_id: str, cx: float, cy: float, rx: float, ry: float,
                     fill: str = "none", stroke: str = "black", stroke_width: float = 1) -> bool:
        """Draw an ellipse."""
        pass

    @abstractmethod
    def draw_rect(self, object_id: str, x: float, y: float, width: float, height: float,
                  fill: str = "none", stroke: str = "black", stroke_width: float = 1,
                  rx: Optional[float] = None, ry: Optional[float] = None) -> bool:
        """Draw a rectangle."""
        pass

    @abstractmethod
    def draw_line(self, object_id: str, x1: float, y1: float, x2: float, y2: float,
                  stroke: str = "black", stroke_width: float = 1) -> bool:
        """Draw a line."""
        pass

    @abstractmethod
    def draw_polyline(self, object_id: str, points: list[tuple[float, float]],
                      fill: str = "none", stroke: str = "black", stroke_width: float = 1) -> bool:
        """Draw a polyline (connected lines)."""
        pass

    @abstractmethod
    def draw_polygon(self, object_id: str, points: list[tuple[float, float]],
                     fill: str = "none", stroke: str = "black", stroke_width: float = 1) -> bool:
        """Draw a polygon (closed shape)."""
        pass

    @abstractmethod
    def draw_path(self, object_id: str, d: str,
                  fill: str = "none", stroke: str = "black", stroke_width: float = 1) -> bool:
        """Draw a path using SVG path data."""
        pass

    @abstractmethod
    def draw_text(self, object_id: str, x: float, y: float, text: str,
                  fill: str = "black", font_size: str = "16px") -> bool:
        """Draw text."""
        pass

    @abstractmethod
    def save(self, filepath: str) -> None:
        """Save the drawing to a file."""
        pass

    @abstractmethod
    def show(self) -> None:
        """Display the drawing (if applicable)."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources (close windows, etc.)."""
        pass

    def get_canvas_info(self) -> dict:
        """Return information about the canvas for LLM context."""
        return {
            "width": self.width,
            "height": self.height,
            "background": self.background,
            "backend": self.backend_name,
            "element_count": self.element_count,
        }
