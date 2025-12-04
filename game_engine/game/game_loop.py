"""
GameLoop - main game loop with timing, frame management, system updates.
"""

import time
import turtle
from game_engine.core.entity import EntityManager
from game_engine.core.registry import ComponentRegistry
from game_engine.core.system import SystemManager
from game_engine.input.input_handler import InputState, InputHandler, InputAction
from game_engine.game.game_state import GameState, GameStateType
from game_engine.systems.physics import PhysicsSystem
from game_engine.systems.collision import CollisionSystem
from game_engine.systems.render import RenderSystem
from game_engine.systems.ai import AISystem
from game_engine.systems.weapon import WeaponSystem
from game_engine.systems.health import HealthSystem
from game_engine.systems.wave import WaveSystem
from game_engine.core.component import (
    Transform, Renderable, Collider, Physics, Health, Weapon, InputState as InputStateComp
)


class GameLoop:
    """
    Main game loop orchestrator.
    Handles timing, system updates, frame management.
    """
    
    def __init__(self, screen: turtle.Screen, target_fps: int = 60):
        self.screen = screen
        self.target_fps = target_fps
        self.frame_time = 1.0 / target_fps
        
        # Core ECS
        self.entity_manager = EntityManager()
        self.registry = ComponentRegistry()
        self.system_manager = SystemManager()
        
        # Game state
        self.game_state = GameState()
        self.input_state = InputState()
        self.input_handler = InputHandler(screen, self.input_state)
        
        # Player ID (set after creation)
        self.player_id = None
        
        # Arena bounds
        self.arena_bounds = (-400, -400, 400, 400)
        
        # Setup systems
        self._setup_systems()
        
        # Create player
        self._create_player()
    
    def _setup_systems(self) -> None:
        """Register all systems in priority order"""
        # Lower priority = runs first
        self.system_manager.register_system(
            PhysicsSystem(self.entity_manager, self.registry),
            priority=10
        )
        
        self.system_manager.register_system(
            AISystem(self.entity_manager, self.registry, ""),  # Player ID set later
            priority=20
        )
        
        self.system_manager.register_system(
            WeaponSystem(self.entity_manager, self.registry, self.input_state),
            priority=30
        )
        
        self.system_manager.register_system(
            CollisionSystem(self.entity_manager, self.registry, self.arena_bounds),
            priority=40
        )
        
        self.system_manager.register_system(
            HealthSystem(self.entity_manager, self.registry),
            priority=50
        )
        
        self.system_manager.register_system(
            WaveSystem(self.entity_manager, self.registry, "", self.arena_bounds),  # Player ID set later
            priority=60
        )
        
        self.system_manager.register_system(
            RenderSystem(self.entity_manager, self.registry, self.screen),
            priority=100  # Render last
        )
    
    def _create_player(self) -> None:
        """Create the player entity"""
        self.player_id = self.entity_manager.create_entity()
        
        # Transform
        transform = Transform(x=0.0, y=0.0, angle=0.0)
        self.entity_manager.add_component(self.player_id, transform)
        self.registry.register(self.player_id, transform)
        
        # Renderable
        renderable = Renderable(
            shape="triangle",
            color="blue",
            size=1.5
        )
        self.entity_manager.add_component(self.player_id, renderable)
        self.registry.register(self.player_id, renderable)
        
        # Collider
        collider = Collider(
            radius=12.0,
            mask=0x0004,  # Player mask
            tags={"player"}
        )
        self.entity_manager.add_component(self.player_id, collider)
        self.registry.register(self.player_id, collider)
        
        # Physics
        physics = Physics(
            mass=1.0,
            friction=0.92,
            max_speed=200.0,
            acceleration=400.0
        )
        self.entity_manager.add_component(self.player_id, physics)
        self.registry.register(self.player_id, physics)
        
        # Health
        health = Health(hp=100.0, max_hp=100.0)
        self.entity_manager.add_component(self.player_id, health)
        self.registry.register(self.player_id, health)
        
        # Weapon
        weapon = Weapon(
            fire_rate=5.0,  # 5 shots per second
            damage=15.0,
            projectile_speed=400.0,
            spread=2.0,
            bullet_count=1,
            range=800.0
        )
        self.entity_manager.add_component(self.player_id, weapon)
        self.registry.register(self.player_id, weapon)
        
        # Update system references with player ID
        ai_system = self.system_manager.get_system(AISystem)
        ai_system.player_id = self.player_id
        
        wave_system = self.system_manager.get_system(WaveSystem)
        wave_system.player_id = self.player_id
    
    def _handle_input(self, dt: float) -> None:
        """Handle player input and update player movement"""
        if not self.game_state.is_playing():
            return
        
        transform = self.entity_manager.get_component(self.player_id, Transform)
        physics = self.entity_manager.get_component(self.player_id, Physics)
        
        if not transform or not physics:
            return
        
        # Handle pause
        if self.input_state.is_active(InputAction.PAUSE):
            self.game_state.toggle_pause()
            self.input_state.set_active(InputAction.PAUSE, False)  # Consume input
        
        # Handle quit
        if self.input_state.is_active(InputAction.QUIT):
            self.game_state.state = GameStateType.GAME_OVER
        
        # Movement
        move_x, move_y = 0.0, 0.0
        
        if self.input_state.is_active(InputAction.MOVE_UP):
            move_y += 1.0
        if self.input_state.is_active(InputAction.MOVE_DOWN):
            move_y -= 1.0
        if self.input_state.is_active(InputAction.MOVE_LEFT):
            move_x -= 1.0
        if self.input_state.is_active(InputAction.MOVE_RIGHT):
            move_x += 1.0
        
        # Normalize movement vector
        if move_x != 0 or move_y != 0:
            from game_engine.utils.math_utils import normalize
            move_x, move_y = normalize(move_x, move_y)
            
            # Apply acceleration
            transform.vx += move_x * physics.acceleration * dt
            transform.vy += move_y * physics.acceleration * dt
        
        # Rotation
        if self.input_state.is_active(InputAction.ROTATE_LEFT):
            transform.angular_velocity = -180.0  # degrees per second
        elif self.input_state.is_active(InputAction.ROTATE_RIGHT):
            transform.angular_velocity = 180.0
        else:
            transform.angular_velocity = 0.0
        
        # Face movement direction if moving
        if move_x != 0 or move_y != 0:
            from game_engine.utils.math_utils import angle_between
            transform.angle = angle_between(0, 0, move_x, move_y)
    
    def _draw_arena(self) -> None:
        """Draw arena boundaries and background"""
        t = turtle.Turtle()
        t.hideturtle()
        t.speed(0)
        t.penup()
        
        min_x, min_y, max_x, max_y = self.arena_bounds
        
        # Draw boundary
        t.color("gray")
        t.pensize(3)
        t.goto(min_x, min_y)
        t.pendown()
        t.goto(max_x, min_y)
        t.goto(max_x, max_y)
        t.goto(min_x, max_y)
        t.goto(min_x, min_y)
        t.penup()
        
        # Draw grid (optional)
        t.color("darkgray")
        t.pensize(1)
        grid_spacing = 50
        for x in range(int(min_x), int(max_x) + 1, grid_spacing):
            t.goto(x, min_y)
            t.pendown()
            t.goto(x, max_y)
            t.penup()
        for y in range(int(min_y), int(max_y) + 1, grid_spacing):
            t.goto(min_x, y)
            t.pendown()
            t.goto(max_x, y)
            t.penup()
    
    def run(self) -> None:
        """Main game loop"""
        # Setup screen
        self.screen.tracer(0)  # Disable auto-update
        self.screen.bgcolor("black")
        self.screen.title("Robo Arena - ECS Game Engine")
        
        # Draw arena (static)
        self._draw_arena()
        
        # Game loop
        last_time = time.time()
        running = True
        
        while running:
            # Calculate delta time
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            # Cap dt to prevent large jumps
            dt = min(dt, 0.1)  # Max 100ms
            
            # Handle input
            self._handle_input(dt)
            
            # Update systems if playing
            if self.game_state.is_playing():
                self.system_manager.update_all(dt)
            
            # Flush entity destruction (and cleanup render system)
            render_system = self.system_manager.get_system(RenderSystem)
            for entity_id in list(self.entity_manager._pending_destruction):
                render_system.cleanup_entity(entity_id)
            self.entity_manager.flush_destruction(self.registry)
            
            # Update screen
            self.screen.update()
            
            # Check game over
            if self.game_state.state == GameStateType.GAME_OVER:
                running = False
            
            # Sleep to cap FPS
            sleep_time = self.frame_time - (time.time() - current_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # Cleanup
        self.screen.bye()
