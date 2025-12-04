"""
Render System - Visual rendering using Python's turtle graphics.

This system manages turtle objects for all renderable entities
and updates their visual representation each frame.
"""

from __future__ import annotations
import turtle
from typing import TYPE_CHECKING, Dict, List, Optional, Any
from dataclasses import dataclass

from ..core.system import GameSystem, SystemPriority
from ..components.transform import Transform
from ..components.renderable import Renderable, RenderShape, RenderLayer, TextRenderable
from ..components.health import Health, Shield

if TYPE_CHECKING:
    from ..core.entity import Entity


@dataclass
class TurtleInfo:
    """Tracking info for a turtle object."""
    turtle_obj: turtle.Turtle
    entity_id: str
    layer: RenderLayer


class RenderSystem(GameSystem):
    """
    Handles all visual rendering using turtle graphics.
    
    Features:
    - Automatic turtle creation for renderable entities
    - Layer-based draw ordering
    - Flash effects for damage feedback
    - Health bar rendering
    - Object pooling for performance
    - Static background rendering
    
    Performance Notes:
    - Uses screen.tracer(0) for manual updates
    - Reuses turtle objects via pooling
    - Batches visual updates before screen.update()
    """
    
    def __init__(
        self,
        screen: turtle.Screen,
        arena_width: float = 800,
        arena_height: float = 600,
        show_health_bars: bool = True,
        show_debug: bool = False
    ):
        super().__init__(priority=SystemPriority.RENDER)
        self.screen = screen
        self.arena_width = arena_width
        self.arena_height = arena_height
        self.show_health_bars = show_health_bars
        self.show_debug = show_debug
        
        # Turtle management
        self._turtles: Dict[str, TurtleInfo] = {}  # entity_id -> TurtleInfo
        self._turtle_pool: List[turtle.Turtle] = []  # Recycled turtles
        self._next_turtle_id = 0
        
        # Health bar turtles (separate pool)
        self._health_bar_turtles: Dict[str, turtle.Turtle] = {}
        self._health_bar_pool: List[turtle.Turtle] = []
        
        # Background turtle for static elements
        self._background_turtle: Optional[turtle.Turtle] = None
        
        # UI layer turtle
        self._ui_turtle: Optional[turtle.Turtle] = None
        
        # Shape registration
        self._custom_shapes_registered = False
    
    def initialize(self) -> None:
        """Set up rendering system."""
        # Configure screen
        self.screen.tracer(0)  # Manual updates only
        self.screen.bgcolor("black")
        
        # Register custom shapes
        self._register_custom_shapes()
        
        # Create background turtle
        self._background_turtle = self._create_turtle()
        self._background_turtle.hideturtle()
        
        # Create UI turtle
        self._ui_turtle = self._create_turtle()
        self._ui_turtle.hideturtle()
        
        # Draw initial background
        self._draw_arena_background()
    
    def _register_custom_shapes(self) -> None:
        """Register custom turtle shapes."""
        if self._custom_shapes_registered:
            return
        
        # Robot shape (player)
        robot_shape = (
            (0, 15), (-10, -10), (-5, -10), (-5, -5),
            (5, -5), (5, -10), (10, -10)
        )
        try:
            self.screen.register_shape("robot", robot_shape)
        except turtle.TurtleGraphicsError:
            pass
        
        # Diamond shape
        diamond_shape = ((0, 12), (8, 0), (0, -12), (-8, 0))
        try:
            self.screen.register_shape("diamond", diamond_shape)
        except turtle.TurtleGraphicsError:
            pass
        
        self._custom_shapes_registered = True
    
    def _draw_arena_background(self) -> None:
        """Draw static arena elements."""
        t = self._background_turtle
        if not t:
            return
        
        t.clear()
        t.penup()
        t.speed(0)
        
        # Draw arena border
        hw = self.arena_width / 2
        hh = self.arena_height / 2
        
        t.goto(-hw, -hh)
        t.pendown()
        t.pensize(3)
        t.pencolor("#444444")
        
        for _ in range(2):
            t.forward(self.arena_width)
            t.left(90)
            t.forward(self.arena_height)
            t.left(90)
        
        t.penup()
        
        # Draw grid lines
        t.pensize(1)
        t.pencolor("#222222")
        grid_size = 50
        
        # Vertical lines
        for x in range(int(-hw), int(hw) + 1, grid_size):
            t.goto(x, -hh)
            t.pendown()
            t.goto(x, hh)
            t.penup()
        
        # Horizontal lines
        for y in range(int(-hh), int(hh) + 1, grid_size):
            t.goto(-hw, y)
            t.pendown()
            t.goto(hw, y)
            t.penup()
        
        t.hideturtle()
    
    def update(self, dt: float) -> None:
        """Render all entities."""
        # Collect entities to render
        render_list: List[tuple[Entity, Transform, Renderable]] = []
        
        for entity in self.entities.get_entities_with(Transform, Renderable):
            transform = self.entities.get_component(entity, Transform)
            renderable = self.entities.get_component(entity, Renderable)
            
            if transform and renderable and renderable.visible:
                render_list.append((entity, transform, renderable))
        
        # Sort by layer
        render_list.sort(key=lambda x: x[2].layer.value)
        
        # Track which entity turtles are still active
        active_entity_ids = set()
        
        # Render each entity
        for entity, transform, renderable in render_list:
            active_entity_ids.add(entity.id)
            
            # Update flash timer
            if renderable.flash_timer > 0:
                renderable.flash_timer -= dt
                if renderable.flash_timer <= 0 and renderable.original_color:
                    renderable.color = renderable.original_color
                    renderable.original_color = ""
            
            # Get or create turtle for this entity
            t = self._get_turtle_for_entity(entity, renderable)
            
            # Update turtle state
            self._update_turtle(t, transform, renderable)
        
        # Render health bars
        if self.show_health_bars:
            self._render_health_bars()
        
        # Clean up turtles for destroyed entities
        self._cleanup_turtles(active_entity_ids)
        
        # Final screen update
        self.screen.update()
    
    def _get_turtle_for_entity(self, entity: Entity, renderable: Renderable) -> turtle.Turtle:
        """Get or create a turtle for an entity."""
        if entity.id in self._turtles:
            return self._turtles[entity.id].turtle_obj
        
        # Get from pool or create new
        if self._turtle_pool:
            t = self._turtle_pool.pop()
            t.showturtle()
        else:
            t = self._create_turtle()
        
        # Store reference
        self._turtles[entity.id] = TurtleInfo(
            turtle_obj=t,
            entity_id=entity.id,
            layer=renderable.layer
        )
        renderable._turtle_ref = t
        
        return t
    
    def _create_turtle(self) -> turtle.Turtle:
        """Create a new turtle with default settings."""
        t = turtle.Turtle()
        t.speed(0)
        t.penup()
        t.hideturtle()
        return t
    
    def _update_turtle(
        self,
        t: turtle.Turtle,
        transform: Transform,
        renderable: Renderable
    ) -> None:
        """Update a turtle's visual state."""
        # Shape
        shape_name = self._get_shape_name(renderable.shape)
        if t.shape() != shape_name:
            try:
                t.shape(shape_name)
            except turtle.TurtleGraphicsError:
                t.shape("circle")
        
        # Color (handle flash)
        color = renderable.flash_color if renderable.flash_timer > 0 else renderable.color
        try:
            t.color(renderable.outline_color, color)
        except turtle.TurtleGraphicsError:
            t.color("white", "white")
        
        # Size
        t.shapesize(renderable.size * transform.scale, 
                   renderable.size * transform.scale)
        
        # Position and rotation
        t.goto(transform.x, transform.y)
        t.setheading(transform.angle)
        
        # Show
        if not t.isvisible():
            t.showturtle()
    
    def _get_shape_name(self, shape: RenderShape) -> str:
        """Convert RenderShape to turtle shape name."""
        shape_map = {
            RenderShape.CIRCLE: "circle",
            RenderShape.SQUARE: "square",
            RenderShape.TRIANGLE: "triangle",
            RenderShape.ARROW: "arrow",
            RenderShape.TURTLE: "turtle",
            RenderShape.CLASSIC: "classic",
        }
        return shape_map.get(shape, "circle")
    
    def _render_health_bars(self) -> None:
        """Render health bars above entities."""
        for entity in self.entities.get_entities_with(Transform, Health, Renderable):
            transform = self.entities.get_component(entity, Transform)
            health = self.entities.get_component(entity, Health)
            renderable = self.entities.get_component(entity, Renderable)
            
            if not all([transform, health, renderable]) or not renderable.visible:
                continue
            
            # Only show for enemies or if damaged
            if health.hp >= health.max_hp:
                # Hide health bar
                if entity.id in self._health_bar_turtles:
                    self._health_bar_turtles[entity.id].hideturtle()
                continue
            
            # Get or create health bar turtle
            if entity.id not in self._health_bar_turtles:
                if self._health_bar_pool:
                    hb = self._health_bar_pool.pop()
                else:
                    hb = self._create_turtle()
                self._health_bar_turtles[entity.id] = hb
            
            hb = self._health_bar_turtles[entity.id]
            self._draw_health_bar(hb, transform, health, renderable)
    
    def _draw_health_bar(
        self,
        t: turtle.Turtle,
        transform: Transform,
        health: Health,
        renderable: Renderable
    ) -> None:
        """Draw a health bar above an entity."""
        bar_width = 30 * renderable.size
        bar_height = 4
        offset_y = 20 * renderable.size
        
        x = transform.x - bar_width / 2
        y = transform.y + offset_y
        
        t.hideturtle()
        t.clear()
        t.penup()
        
        # Background (dark)
        t.goto(x, y)
        t.pendown()
        t.pensize(bar_height)
        t.pencolor("#333333")
        t.forward(bar_width)
        t.penup()
        
        # Health fill
        hp_width = bar_width * health.health_percent
        if hp_width > 0:
            # Color based on health
            if health.health_percent > 0.6:
                color = "#00ff00"
            elif health.health_percent > 0.3:
                color = "#ffff00"
            else:
                color = "#ff0000"
            
            t.goto(x, y)
            t.pendown()
            t.pencolor(color)
            t.forward(hp_width)
            t.penup()
        
    
    def _cleanup_turtles(self, active_entity_ids: set) -> None:
        """Recycle turtles for destroyed entities."""
        to_remove = []
        
        for entity_id, info in self._turtles.items():
            if entity_id not in active_entity_ids:
                to_remove.append(entity_id)
                info.turtle_obj.hideturtle()
                info.turtle_obj.clear()
                self._turtle_pool.append(info.turtle_obj)
        
        for entity_id in to_remove:
            del self._turtles[entity_id]
        
        # Also clean up health bars
        hb_to_remove = []
        for entity_id, hb in self._health_bar_turtles.items():
            if entity_id not in active_entity_ids:
                hb_to_remove.append(entity_id)
                hb.hideturtle()
                hb.clear()
                self._health_bar_pool.append(hb)
        
        for entity_id in hb_to_remove:
            del self._health_bar_turtles[entity_id]
    
    def cleanup(self) -> None:
        """Clean up all turtles."""
        for info in self._turtles.values():
            info.turtle_obj.hideturtle()
        self._turtles.clear()
        
        for t in self._turtle_pool:
            t.hideturtle()
        self._turtle_pool.clear()
        
        if self._background_turtle:
            self._background_turtle.hideturtle()
        if self._ui_turtle:
            self._ui_turtle.hideturtle()
    
    def draw_text(
        self,
        text: str,
        x: float,
        y: float,
        color: str = "white",
        font_size: int = 16,
        align: str = "center"
    ) -> None:
        """Draw text on the UI layer."""
        if not self._ui_turtle:
            return
        
        self._ui_turtle.goto(x, y)
        self._ui_turtle.pencolor(color)
        self._ui_turtle.write(
            text,
            align=align,
            font=("Arial", font_size, "normal")
        )
    
    def clear_ui(self) -> None:
        """Clear the UI layer."""
        if self._ui_turtle:
            self._ui_turtle.clear()
    
    def redraw_background(self) -> None:
        """Redraw the arena background."""
        self._draw_arena_background()
    
    def set_arena_size(self, width: float, height: float) -> None:
        """Update arena dimensions and redraw."""
        self.arena_width = width
        self.arena_height = height
        self._draw_arena_background()
