"""
Robo-Arena Main Entry Point

A top-down arena shooter demonstrating the Turtle Arena Game Engine.
"""

from __future__ import annotations
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import turtle
from typing import Optional

from engine import GameLoop
from engine.systems import (
    PhysicsSystem,
    CollisionSystem,
    RenderSystem,
    InputSystem,
    AISystem,
    WeaponSystem,
    HealthSystem,
    WaveSystem,
    StatusEffectSystem,
    PathfindingSystem,
)
from engine.core.events import (
    WaveStartEvent,
    WaveCompleteEvent,
    DeathEvent,
    GameStateEvent,
)
from engine.components.tags import PlayerTag
from engine.components.health import Health, Shield

from .config import GameConfig, DEFAULT_CONFIG
from .prefabs import create_player, create_arena_obstacles


class RoboArena:
    """
    Main game class for Robo-Arena.
    
    Orchestrates the game setup, UI, and game-specific logic.
    """
    
    def __init__(self, config: Optional[GameConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self.game_loop: Optional[GameLoop] = None
        
        # UI state
        self.ui_turtle: Optional[turtle.Turtle] = None
        self.show_wave_text = False
        self.wave_text_timer = 0.0
        self.current_wave_text = ""
    
    def setup(self) -> None:
        """Set up the game."""
        cfg = self.config
        
        # Create game loop
        self.game_loop = GameLoop(
            title=cfg.title,
            width=cfg.arena.width,
            height=cfg.arena.height,
            target_fps=cfg.target_fps,
            background_color=cfg.arena.background_color
        )
        self.game_loop.initialize()
        
        # Add systems in order
        self._add_systems()
        
        # Subscribe to events
        self._subscribe_events()
        
        # Create initial entities
        self._create_entities()
        
        # Set up UI
        self._setup_ui()
        
        # Register update callback for UI
        self.game_loop.on_update(self._update_ui)
        
        # Start wave system
        wave_system = self.game_loop.get_system(WaveSystem)
        if wave_system:
            wave_system.start_game()
    
    def _add_systems(self) -> None:
        """Add all game systems."""
        cfg = self.config
        loop = self.game_loop
        
        # Input (first)
        loop.add_system(InputSystem(loop.screen))
        
        # AI and pathfinding
        loop.add_system(PathfindingSystem(
            cfg.arena.width, cfg.arena.height
        ))
        loop.add_system(AISystem())
        
        # Physics
        loop.add_system(PhysicsSystem(
            cfg.arena.width, cfg.arena.height
        ))
        
        # Weapons
        loop.add_system(WeaponSystem())
        
        # Collision
        loop.add_system(CollisionSystem(
            cfg.arena.width, cfg.arena.height
        ))
        
        # Health and damage
        loop.add_system(HealthSystem(
            i_frame_duration=cfg.i_frame_duration
        ))
        
        # Status effects
        loop.add_system(StatusEffectSystem())
        
        # Waves
        loop.add_system(WaveSystem(
            arena_width=cfg.arena.width,
            arena_height=cfg.arena.height,
            start_budget=cfg.wave.start_budget,
            budget_per_wave=cfg.wave.budget_per_wave,
            max_waves=cfg.wave.max_waves
        ))
        
        # Rendering (last)
        loop.add_system(RenderSystem(
            loop.screen,
            cfg.arena.width,
            cfg.arena.height,
            show_health_bars=cfg.show_health_bars,
            show_debug=cfg.show_debug_info
        ))
    
    def _subscribe_events(self) -> None:
        """Subscribe to game events."""
        events = self.game_loop.events
        
        events.subscribe(WaveStartEvent, self._on_wave_start)
        events.subscribe(WaveCompleteEvent, self._on_wave_complete)
        events.subscribe(DeathEvent, self._on_death)
        events.subscribe(GameStateEvent, self._on_game_state)
    
    def _create_entities(self) -> None:
        """Create initial game entities."""
        entities = self.game_loop.entities
        
        # Create player at center
        create_player(entities, 0, 0, self.config)
        
        # Create some obstacles
        create_arena_obstacles(
            entities,
            self.config.arena.width,
            self.config.arena.height,
            obstacle_count=5
        )
    
    def _setup_ui(self) -> None:
        """Set up UI elements."""
        self.ui_turtle = turtle.Turtle()
        self.ui_turtle.hideturtle()
        self.ui_turtle.penup()
        self.ui_turtle.speed(0)
    
    def _update_ui(self, dt: float) -> None:
        """Update UI each frame."""
        if not self.ui_turtle:
            return
        
        self.ui_turtle.clear()
        
        # Get game state
        wave_system = self.game_loop.get_system(WaveSystem)
        
        # Draw HUD
        hw = self.config.arena.width / 2
        hh = self.config.arena.height / 2
        
        # Wave and score
        if wave_system:
            self._draw_text(
                f"Wave: {wave_system.current_wave}",
                -hw + 10, hh - 25,
                align="left"
            )
            self._draw_text(
                f"Score: {wave_system.score}",
                -hw + 10, hh - 45,
                align="left"
            )
            self._draw_text(
                f"Enemies: {wave_system.enemies_remaining}",
                -hw + 10, hh - 65,
                align="left"
            )
        
        # Player health
        player = self.game_loop.entities.get_named("player")
        if player:
            health = self.game_loop.entities.get_component(player, Health)
            shield = self.game_loop.entities.get_component(player, Shield)
            
            if health:
                self._draw_health_bar(
                    hw - 150, hh - 25,
                    120, 15,
                    health.health_percent,
                    "#00ff00", "#ff0000"
                )
                self._draw_text(
                    f"HP: {int(health.hp)}/{int(health.max_hp)}",
                    hw - 90, hh - 22,
                    size=10
                )
            
            if shield and shield.max_hp > 0:
                self._draw_health_bar(
                    hw - 150, hh - 45,
                    120, 10,
                    shield.shield_percent,
                    "#4444ff", "#222266"
                )
                self._draw_text(
                    f"Shield: {int(shield.hp)}/{int(shield.max_hp)}",
                    hw - 90, hh - 43,
                    size=10
                )
        
        # Wave announcement
        if self.show_wave_text:
            self.wave_text_timer -= dt
            if self.wave_text_timer <= 0:
                self.show_wave_text = False
            else:
                # Fade effect
                alpha = min(1.0, self.wave_text_timer / 1.0)
                self._draw_text(
                    self.current_wave_text,
                    0, 50,
                    size=28,
                    color="#ffffff"
                )
        
        # Game over / Victory text
        if self.game_loop.state.name == "GAME_OVER":
            self._draw_text("GAME OVER", 0, 0, size=36, color="#ff0000")
            self._draw_text("Press Q to quit", 0, -40, size=16)
        elif self.game_loop.state.name == "VICTORY":
            self._draw_text("VICTORY!", 0, 0, size=36, color="#00ff00")
            if wave_system:
                self._draw_text(
                    f"Final Score: {wave_system.score}",
                    0, -40, size=20
                )
            self._draw_text("Press Q to quit", 0, -70, size=16)
        
        # Controls hint
        self._draw_text(
            "WASD/Arrows: Move | Space: Shoot | Q: Quit",
            0, -hh + 15,
            size=12,
            color="#888888"
        )
    
    def _draw_text(
        self,
        text: str,
        x: float,
        y: float,
        size: int = 14,
        color: str = "#ffffff",
        align: str = "center"
    ) -> None:
        """Draw text on the UI."""
        self.ui_turtle.goto(x, y)
        self.ui_turtle.pencolor(color)
        self.ui_turtle.write(text, align=align, font=("Arial", size, "normal"))
    
    def _draw_health_bar(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        percent: float,
        fill_color: str,
        bg_color: str
    ) -> None:
        """Draw a health/shield bar."""
        t = self.ui_turtle
        
        # Background
        t.goto(x, y)
        t.pendown()
        t.pensize(height)
        t.pencolor(bg_color)
        t.forward(width)
        t.penup()
        
        # Fill
        if percent > 0:
            t.goto(x, y)
            t.pendown()
            t.pencolor(fill_color)
            t.forward(width * percent)
            t.penup()
    
    def _on_wave_start(self, event: WaveStartEvent) -> None:
        """Handle wave start event."""
        self.current_wave_text = f"Wave {event.wave_number}"
        self.show_wave_text = True
        self.wave_text_timer = 2.0
    
    def _on_wave_complete(self, event: WaveCompleteEvent) -> None:
        """Handle wave complete event."""
        self.current_wave_text = "Wave Complete!"
        self.show_wave_text = True
        self.wave_text_timer = 2.0
    
    def _on_death(self, event: DeathEvent) -> None:
        """Handle death event."""
        # Check if player died
        player = self.game_loop.entities.get_named("player")
        if player and event.entity_id == player.id:
            self.game_loop.events.emit(GameStateEvent(state="game_over"))
    
    def _on_game_state(self, event: GameStateEvent) -> None:
        """Handle game state changes."""
        pass  # Handled by game loop
    
    def run(self) -> None:
        """Run the game."""
        if not self.game_loop:
            self.setup()
        
        self.game_loop.run()


def main():
    """Main entry point."""
    print("=" * 50)
    print("  ROBO-ARENA")
    print("  A Turtle Arena Shooter")
    print("=" * 50)
    print()
    print("Controls:")
    print("  W/Up Arrow    - Move Forward")
    print("  S/Down Arrow  - Move Backward")
    print("  A/Left Arrow  - Turn Left")
    print("  D/Right Arrow - Turn Right")
    print("  Space         - Fire")
    print("  Q             - Quit")
    print()
    print("Survive the waves of enemies!")
    print()
    
    # Create and run game
    game = RoboArena()
    game.setup()
    game.run()


if __name__ == "__main__":
    main()
