"""
Renderable component - Visual representation of entities.

This component holds all data needed by the RenderSystem to draw
an entity using Python's turtle graphics.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Any


class RenderShape(Enum):
    """Available shapes for rendering."""
    CIRCLE = "circle"
    SQUARE = "square"
    TRIANGLE = "triangle"
    ARROW = "arrow"
    TURTLE = "turtle"
    CLASSIC = "classic"  # Classic turtle arrow shape
    
    # Special shapes for different entity types
    DIAMOND = "diamond"  # Pickups/consumables
    STAR = "star"  # Special items
    HEXAGON = "hexagon"  # Advanced enemies
    
    # Custom shapes (registered separately)
    CUSTOM = "custom"
    
    # Text-based shapes (uses text_symbol field)
    TEXT = "text"


class RenderLayer(Enum):
    """
    Render layers for draw ordering.
    Lower values are drawn first (background).
    """
    BACKGROUND = 0
    FLOOR = 10
    OBSTACLE = 20
    POWERUP = 30
    PROJECTILE = 40
    ENEMY = 50
    PLAYER = 60
    EFFECT = 70
    UI = 80


@dataclass
class Renderable:
    """
    Visual representation data for an entity.
    
    Attributes:
        shape: The shape type to render
        color: Fill color (name or hex)
        outline_color: Outline color (name or hex)
        size: Size multiplier (1.0 = default turtle size)
        visible: Whether to render this entity
        layer: Render layer for ordering
        turtle_id: Internal reference to the turtle object (managed by RenderSystem)
        text_symbol: For TEXT shape, the character/symbol to display
        
    Size Notes:
        - Default turtle size is 20x20 pixels
        - size=1.0 means 20px, size=2.0 means 40px
        - Use shapesize(size, size) in turtle
        
    Color Examples:
        - Named: "red", "blue", "green", "white", "black"
        - Hex: "#FF0000", "#00FF00"
    """
    shape: RenderShape = RenderShape.CIRCLE
    color: str = "white"
    outline_color: str = "white"
    size: float = 1.0
    visible: bool = True
    layer: RenderLayer = RenderLayer.ENEMY
    
    # For TEXT shape - the symbol/letter to display
    text_symbol: str = ""
    
    # For glow/pulse effects
    glow: bool = False
    pulse_speed: float = 2.0  # Pulse cycles per second
    
    # Internal state managed by RenderSystem
    turtle_id: Optional[int] = field(default=None, repr=False)
    _turtle_ref: Optional[Any] = field(default=None, repr=False)
    _text_turtle_ref: Optional[Any] = field(default=None, repr=False)
    
    # Animation state
    flash_timer: float = 0.0
    flash_color: str = "white"
    original_color: str = field(default="", repr=False)
    _pulse_time: float = 0.0
    
    def flash(self, duration: float = 0.1, color: str = "white") -> None:
        """
        Trigger a color flash (e.g., when hit).
        The RenderSystem will handle the actual color change.
        """
        self.flash_timer = duration
        self.flash_color = color
        if not self.original_color:
            self.original_color = self.color


@dataclass
class TextRenderable:
    """
    Text rendering component for UI elements.
    
    Separate from Renderable because text has different properties.
    """
    text: str = ""
    font_family: str = "Arial"
    font_size: int = 16
    font_style: str = "normal"  # "normal", "bold", "italic"
    color: str = "white"
    align: str = "center"  # "left", "center", "right"
    visible: bool = True
    layer: RenderLayer = RenderLayer.UI
    
    # Internal state
    turtle_id: Optional[int] = field(default=None, repr=False)
    _turtle_ref: Optional[Any] = field(default=None, repr=False)
