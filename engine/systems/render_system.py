"""
Render System

Handles all visual rendering using turtle graphics.
"""

import turtle
from engine.core.system import GameSystem
from engine.core.component import Transform, Renderable, Health, Shield
from typing import Dict, List


class TurtlePool:
    """
    Object pool for turtle objects to improve performance.
    Reuses turtle instances instead of creating/destroying them.
    """
    
    def __init__(self, screen):
        self.screen = screen
        self.available: List[turtle.Turtle] = []
        self.in_use: Dict[str, turtle.Turtle] = {}  # entity_id -> turtle
    
    def acquire(self, entity_id: str) -> turtle.Turtle:
        """Get a turtle for an entity."""
        if self.available:
            t = self.available.pop()
        else:
            t = turtle.Turtle()
            t.speed(0)
            t.penup()
        
        self.in_use[entity_id] = t
        t.showturtle()
        return t
    
    def release(self, entity_id: str) -> None:
        """Release a turtle back to the pool."""
        if entity_id in self.in_use:
            t = self.in_use[entity_id]
            t.hideturtle()
            self.available.append(t)
            del self.in_use[entity_id]
    
    def get(self, entity_id: str) -> turtle.Turtle:
        """Get the turtle currently assigned to an entity."""
        return self.in_use.get(entity_id)
    
    def clear(self) -> None:
        """Clear all turtles."""
        for t in self.in_use.values():
            t.hideturtle()
        for t in self.available:
            t.hideturtle()
        self.in_use.clear()
        self.available.clear()


class RenderSystem(GameSystem):
    """
    Renders entities using turtle graphics.
    
    Responsibilities:
    - Create/destroy turtle objects for entities
    - Update turtle positions and headings
    - Set colors and shapes
    - Sort by layer for proper rendering order
    - Handle visibility
    """
    
    def __init__(self, entity_manager, screen, priority: int = 90):
        super().__init__(entity_manager, priority)
        self.screen = screen
        self.turtle_pool = TurtlePool(screen)
        
        # Setup screen for performance
        self.screen.tracer(0)  # Manual updates
        self.screen.bgcolor("black")
        
        # Background turtle for static elements
        self.bg_turtle = turtle.Turtle()
        self.bg_turtle.speed(0)
        self.bg_turtle.hideturtle()
        self.bg_turtle.penup()
        self._draw_background()
    
    def _draw_background(self) -> None:
        """Draw static background elements (arena border, grid, etc.)."""
        self.bg_turtle.clear()
        self.bg_turtle.color("dark gray")
        
        # Draw arena border
        self.bg_turtle.penup()
        self.bg_turtle.goto(-390, -290)
        self.bg_turtle.pendown()
        self.bg_turtle.pensize(2)
        for _ in range(2):
            self.bg_turtle.forward(780)
            self.bg_turtle.left(90)
            self.bg_turtle.forward(580)
            self.bg_turtle.left(90)
        self.bg_turtle.penup()
        
        # Draw grid (optional, subtle)
        self.bg_turtle.color("dim gray")
        self.bg_turtle.pensize(1)
        
        # Vertical lines
        for x in range(-350, 400, 50):
            self.bg_turtle.goto(x, -300)
            self.bg_turtle.pendown()
            self.bg_turtle.goto(x, 300)
            self.bg_turtle.penup()
        
        # Horizontal lines
        for y in range(-250, 300, 50):
            self.bg_turtle.goto(-400, y)
            self.bg_turtle.pendown()
            self.bg_turtle.goto(400, y)
            self.bg_turtle.penup()
    
    def update(self, dt: float) -> None:
        """Update all renderable entities."""
        # Get all entities with transform and renderable components
        entities = self.entity_manager.query_entities(Transform, Renderable)
        
        # Sort by layer (lower layers drawn first)
        entities.sort(key=lambda e: e.get_component(Renderable).layer)
        
        # Track which entities are currently being rendered
        active_entity_ids = set()
        
        for entity in entities:
            transform = entity.get_component(Transform)
            renderable = entity.get_component(Renderable)
            
            if not renderable.visible:
                # Hide turtle if entity is invisible
                if renderable.turtle_ref:
                    renderable.turtle_ref.hideturtle()
                continue
            
            active_entity_ids.add(entity.id)
            
            # Get or create turtle for this entity
            if not renderable.turtle_ref:
                renderable.turtle_ref = self.turtle_pool.acquire(entity.id)
                self._setup_turtle(renderable.turtle_ref, renderable)
            
            t = renderable.turtle_ref
            
            # Update position
            t.goto(transform.x, transform.y)
            
            # Update heading (turtle 0° = right, our 0° = right, so direct mapping)
            t.setheading(transform.angle)
            
            # Update color (may change due to damage, status effects, etc.)
            self._update_turtle_appearance(entity, t, renderable)
            
            # Ensure visible
            t.showturtle()
        
        # Release turtles for entities that no longer exist or are not renderable
        for entity_id in list(self.turtle_pool.in_use.keys()):
            if entity_id not in active_entity_ids:
                self.turtle_pool.release(entity_id)
        
        # Update screen
        self.screen.update()
    
    def _setup_turtle(self, t: turtle.Turtle, renderable: Renderable) -> None:
        """Initial setup of a turtle's appearance."""
        t.shape(renderable.shape)
        t.color(renderable.color)
        t.shapesize(renderable.size, renderable.size)
        t.penup()
    
    def _update_turtle_appearance(self, entity, t: turtle.Turtle, renderable: Renderable) -> None:
        """Update turtle appearance (color, size) based on entity state."""
        # Base color
        color = renderable.color
        
        # Flash red if recently damaged (invulnerable)
        health = entity.get_component(Health)
        if health and health.invulnerable_time > 0:
            # Flash between red and white
            if int(health.invulnerable_time * 10) % 2 == 0:
                color = "red"
            else:
                color = "white"
        
        t.color(color)
        t.shapesize(renderable.size, renderable.size)
    
    def on_entity_destroyed(self, entity_id: str) -> None:
        """Clean up turtle when entity is destroyed."""
        self.turtle_pool.release(entity_id)
    
    def draw_text(self, x: float, y: float, text: str, color: str = "white", 
                  align: str = "center", font: tuple = ("Arial", 16, "normal")) -> None:
        """Draw text on screen."""
        self.bg_turtle.goto(x, y)
        self.bg_turtle.color(color)
        self.bg_turtle.write(text, align=align, font=font)
    
    def clear_text(self) -> None:
        """Clear all text (redraw background)."""
        self._draw_background()
