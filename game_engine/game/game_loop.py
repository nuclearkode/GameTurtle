"""GameLoop: main game loop with timing and orchestration."""

import time
import turtle
from typing import Optional
from ..core.entity_manager import EntityManager
from ..core.component_registry import ComponentRegistry
from ..core.system_manager import SystemManager
from ..core.component import Transform, Renderable, Collider, Physics, Health, Weapon
from ..input import InputHandler
from ..systems import (
    PhysicsSystem,
    CollisionSystem,
    RenderSystem,
    AISystem,
    WeaponSystem,
    HealthSystem,
    WaveSystem,
)
from ..systems.player_controller_system import PlayerControllerSystem


class GameLoop:
    """Main game loop orchestrator."""
    
    def __init__(self, target_fps: float = 60.0, arena_size: float = 800):
        self.target_fps = target_fps
        self.arena_size = arena_size
        self.running = False
        self.paused = False
        
        # Setup turtle screen
        self.screen = turtle.Screen()
        self.screen.setup(width=arena_size + 100, height=arena_size + 100)
        self.screen.title("Robo-Arena: Advanced Turtle Game Engine")
        self.screen.bgcolor("black")
        self.screen.tracer(0)  # Disable automatic updates
        
        # Initialize managers
        self.entity_manager = EntityManager()
        self.component_registry = ComponentRegistry()
        self.system_manager = SystemManager()
        
        # Initialize input
        self.input_handler = InputHandler(self.screen)
        
        # Initialize systems
        self.physics_system = PhysicsSystem(self.entity_manager, self.component_registry)
        self.collision_system = CollisionSystem(self.entity_manager, self.component_registry)
        self.render_system = RenderSystem(self.entity_manager, self.component_registry, self.screen)
        self.ai_system = AISystem(self.entity_manager, self.component_registry)
        self.weapon_system = WeaponSystem(self.entity_manager, self.component_registry)
        self.health_system = HealthSystem(self.entity_manager, self.component_registry)
        self.wave_system = WaveSystem(self.entity_manager, self.component_registry, arena_size)
        self.player_controller = PlayerControllerSystem(
            self.entity_manager, self.component_registry,
            self.input_handler, self.weapon_system
        )
        
        # Register systems
        self.system_manager.register_system(self.wave_system)
        self.system_manager.register_system(self.physics_system)
        self.system_manager.register_system(self.player_controller)
        self.system_manager.register_system(self.ai_system)
        self.system_manager.register_system(self.weapon_system)
        self.system_manager.register_system(self.collision_system)
        self.system_manager.register_system(self.health_system)
        self.render_system.priority = 1000  # Render last
        self.system_manager.register_system(self.render_system)
        
        # Player entity ID
        self.player_id: Optional[str] = None
        
        # Setup exit handler
        self.screen.onkeypress(self.quit, "Escape")
        self.screen.listen()
    
    def create_player(self) -> str:
        """Create the player entity."""
        player_id = self.entity_manager.create_entity()
        
        # Transform
        transform = Transform(x=0.0, y=0.0, angle=0.0)
        self.entity_manager.add_component(player_id, transform)
        self.component_registry.register_component(player_id, "Transform")
        
        # Renderable
        renderable = Renderable(shape="triangle", color="cyan", size=1.5)
        self.entity_manager.add_component(player_id, renderable)
        self.component_registry.register_component(player_id, "Renderable")
        
        # Collider
        collider = Collider(radius=20.0, mask=0x0004, tags={"player"})
        self.entity_manager.add_component(player_id, collider)
        self.component_registry.register_component(player_id, "Collider")
        
        # Physics
        physics = Physics(mass=1.0, friction=0.92, max_speed=200.0, acceleration=150.0)
        self.entity_manager.add_component(player_id, physics)
        self.component_registry.register_component(player_id, "Physics")
        
        # Health
        health = Health(hp=100.0, max_hp=100.0)
        self.entity_manager.add_component(player_id, health)
        self.component_registry.register_component(player_id, "Health")
        
        # Weapon
        weapon = Weapon(
            fire_rate=3.0,
            damage=20.0,
            projectile_speed=400.0,
            spread=0.0,
            bullet_count=1,
            weapon_type="single"
        )
        self.entity_manager.add_component(player_id, weapon)
        self.component_registry.register_component(player_id, "Weapon")
        
        self.player_id = player_id
        self.ai_system.set_player_id(player_id)
        self.player_controller.set_player_id(player_id)
        
        return player_id
    
    def start(self):
        """Start the game loop."""
        # Create player
        self.create_player()
        
        # Start first wave
        self.wave_system.initialize()
        self.wave_system.start_next_wave()
        
        # Run game loop
        self.running = True
        self._game_loop()
    
    def _game_loop(self):
        """Main game loop."""
        last_time = time.time()
        frame_time = 1.0 / self.target_fps
        
        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            
            # Cap dt to prevent large jumps
            dt = min(dt, 0.1)
            
            if not self.paused:
                # Update input
                self.input_handler.update()
                
                # Update weapon system projectiles
                self.weapon_system.update_projectiles(dt)
                
                # Update all systems
                self.system_manager.update_all(dt)
                
                # Flush entity destruction
                self.entity_manager.flush_destruction()
                
                # Check for player death
                if self.player_id:
                    health = self.entity_manager.get_component(self.player_id, "Health")
                    if health and not health.is_alive():
                        print("Game Over!")
                        self.running = False
            
            # Sleep to cap FPS
            elapsed = time.time() - current_time
            sleep_time = frame_time - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            last_time = current_time
        
        self.screen.bye()
    
    def quit(self):
        """Quit the game."""
        self.running = False
    
    def pause(self):
        """Pause/unpause the game."""
        self.paused = not self.paused
