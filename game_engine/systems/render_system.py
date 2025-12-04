"""RenderSystem: handles all turtle-based rendering."""

import turtle
from typing import Dict, Optional
from ..core.system import GameSystem
from ..core.component import Transform, Renderable


class RenderSystem(GameSystem):
    """Manages rendering of all entities."""
    
    def __init__(self, entity_manager, component_registry, screen):
        super().__init__(entity_manager, component_registry)
        self.screen = screen
        self.priority = 100  # Run last
        self._turtle_pool: Dict[str, turtle.Turtle] = {}
        self._static_drawn = False
    
    def update(self, dt: float):
        """Render all entities."""
        # Draw static elements once
        if not self._static_drawn:
            self._draw_static()
            self._static_drawn = True
        
        # Clear all turtles
        for t in self._turtle_pool.values():
            t.clear()
        
        # Get all entities with Transform and Renderable
        entity_ids = self.component_registry.get_entities_with("Transform", "Renderable")
        
        for entity_id in entity_ids:
            transform = self.entity_manager.get_component(entity_id, "Transform")
            renderable = self.entity_manager.get_component(entity_id, "Renderable")
            
            if not transform or not renderable:
                continue
            
            # Get or create turtle for this entity
            turtle_obj = renderable.turtle_ref
            if not turtle_obj:
                turtle_obj = self._get_turtle(entity_id)
                renderable.turtle_ref = turtle_obj
            
            # Update turtle state
            turtle_obj.penup()
            turtle_obj.goto(transform.x, transform.y)
            turtle_obj.setheading(transform.angle)
            turtle_obj.shape(renderable.shape)
            turtle_obj.color(renderable.color)
            turtle_obj.shapesize(renderable.size)
            turtle_obj.showturtle()
        
        # Update screen
        self.screen.update()
    
    def _get_turtle(self, entity_id: str) -> turtle.Turtle:
        """Get or create a turtle for an entity."""
        if entity_id not in self._turtle_pool:
            t = turtle.Turtle()
            t.hideturtle()
            t.speed(0)
            t.penup()
            self._turtle_pool[entity_id] = t
        return self._turtle_pool[entity_id]
    
    def _draw_static(self):
        """Draw static arena elements."""
        # Draw arena boundary
        boundary = turtle.Turtle()
        boundary.hideturtle()
        boundary.speed(0)
        boundary.penup()
        boundary.color("gray")
        boundary.pensize(3)
        
        # Draw rectangle boundary
        arena_size = 800
        boundary.goto(-arena_size // 2, -arena_size // 2)
        boundary.pendown()
        boundary.goto(arena_size // 2, -arena_size // 2)
        boundary.goto(arena_size // 2, arena_size // 2)
        boundary.goto(-arena_size // 2, arena_size // 2)
        boundary.goto(-arena_size // 2, -arena_size // 2)
        boundary.penup()
        
        # Draw grid (optional)
        grid = turtle.Turtle()
        grid.hideturtle()
        grid.speed(0)
        grid.penup()
        grid.color("darkgray")
        grid.pensize(1)
        
        grid_size = 100
        for x in range(-arena_size // 2, arena_size // 2 + 1, grid_size):
            grid.goto(x, -arena_size // 2)
            grid.pendown()
            grid.goto(x, arena_size // 2)
            grid.penup()
        
        for y in range(-arena_size // 2, arena_size // 2 + 1, grid_size):
            grid.goto(-arena_size // 2, y)
            grid.pendown()
            grid.goto(arena_size // 2, y)
            grid.penup()
    
    def on_entity_removed(self, entity_id: str):
        """Clean up turtle when entity is removed."""
        if entity_id in self._turtle_pool:
            turtle_obj = self._turtle_pool[entity_id]
            turtle_obj.hideturtle()
            turtle_obj.clear()
            # Keep turtle in pool for reuse
