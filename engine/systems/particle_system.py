"""
Particle System

Creates and manages visual particle effects.
"""

import random
import math
from engine.core.system import GameSystem
from engine.core.component import Particle, Transform, Renderable, Lifetime


class ParticleSystem(GameSystem):
    """
    Simple particle system for visual effects.
    
    Responsibilities:
    - Create particle entities
    - Update particle lifetimes
    - Handle fading and shrinking
    """
    
    def __init__(self, entity_manager, priority: int = 80):
        super().__init__(entity_manager, priority)
    
    def update(self, dt: float) -> None:
        """Update all particles."""
        particles = self.entity_manager.query_entities(Particle, Renderable)
        
        for entity in particles:
            particle = entity.get_component(Particle)
            renderable = entity.get_component(Renderable)
            
            # Update lifetime
            particle.time_alive += dt
            
            # Calculate fade (0 = invisible, 1 = fully visible)
            life_percent = particle.time_alive / particle.lifetime
            alpha = 1.0 - life_percent
            
            # Apply fading by adjusting color brightness (simplified)
            if alpha <= 0:
                renderable.visible = False
            
            # Apply shrinking
            if particle.shrink_rate > 0:
                renderable.size *= (1.0 - particle.shrink_rate * dt)
                if renderable.size < 0.1:
                    renderable.visible = False
    
    def create_explosion(self, x: float, y: float, count: int = 10, 
                        color: str = "orange") -> None:
        """Create an explosion effect at a position."""
        for _ in range(count):
            # Random direction and speed
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            # Create particle
            particle_entity = self.entity_manager.create_entity()
            
            self.entity_manager.add_component(particle_entity.id, Transform(
                x=x, y=y, vx=vx, vy=vy
            ))
            
            self.entity_manager.add_component(particle_entity.id, Particle(
                lifetime=random.uniform(0.3, 0.8),
                time_alive=0.0,
                fade_rate=2.0,
                shrink_rate=1.5
            ))
            
            self.entity_manager.add_component(particle_entity.id, Renderable(
                shape="circle",
                color=color,
                size=random.uniform(0.3, 0.8),
                layer=10,  # High layer for effects
                visible=True
            ))
            
            self.entity_manager.add_component(particle_entity.id, Lifetime(
                max_lifetime=random.uniform(0.3, 0.8),
                time_alive=0.0
            ))
    
    def create_trail(self, x: float, y: float, color: str = "white") -> None:
        """Create a single trail particle (for continuous effects)."""
        particle_entity = self.entity_manager.create_entity()
        
        self.entity_manager.add_component(particle_entity.id, Transform(x=x, y=y))
        
        self.entity_manager.add_component(particle_entity.id, Particle(
            lifetime=0.2,
            time_alive=0.0,
            fade_rate=5.0,
            shrink_rate=2.0
        ))
        
        self.entity_manager.add_component(particle_entity.id, Renderable(
            shape="circle",
            color=color,
            size=0.3,
            layer=9,
            visible=True
        ))
        
        self.entity_manager.add_component(particle_entity.id, Lifetime(
            max_lifetime=0.2,
            time_alive=0.0
        ))
