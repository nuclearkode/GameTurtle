"""
Robo-Arena Main Entry Point

A top-down arena shooter demonstrating the Turtle Arena Game Engine.
Features:
- Advanced menu system with Start, Restart, Quit buttons
- WASD omnidirectional movement + Mouse/Arrow aim
- Permanent Active Upgrade System with degradation
- Wave-based progression
"""

from __future__ import annotations
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import turtle
from typing import Optional

from engine import GameLoop
from engine.game_loop import GameState
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
from engine.systems.upgrade_system import UpgradeSystem
from engine.core.events import (
    WaveStartEvent,
    WaveCompleteEvent,
    DeathEvent,
    GameStateEvent,
)
from engine.components.tags import PlayerTag
from engine.components.health import Health, Shield
from engine.components.upgrades import PlayerUpgrades
from engine.menu import MenuSystem, MenuState

from .config import GameConfig, DEFAULT_CONFIG
from .prefabs import create_player, create_arena_obstacles


class RoboArena:
    """
    Main game class for Robo-Arena.
    
    Orchestrates the game setup, UI, menu system, and game-specific logic.
    """
    
    def __init__(self, config: Optional[GameConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self.game_loop: Optional[GameLoop] = None
        self.menu: Optional[MenuSystem] = None
        
        # UI state
        self.ui_turtle: Optional[turtle.Turtle] = None
        self.show_wave_text = False
        self.wave_text_timer = 0.0
        self.current_wave_text = ""
        
        # Game state
        self.game_started = False
        self.is_paused = False
    
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
        
        # Set up proper window close handling
        self._setup_window_close()
        
        # Add systems in order
        self._add_systems()
        
        # Subscribe to events
        self._subscribe_events()
        
        # Set up UI
        self._setup_ui()
        
        # Register update callback for UI
        self.game_loop.on_update(self._update_ui)
        
        # Create and show menu
        self._setup_menu()
        
        # Show main menu first
        self.menu.show_main_menu()
    
    def _setup_window_close(self) -> None:
        """Set up proper window close (X button) handling."""
        try:
            root = self.game_loop.screen.getcanvas().winfo_toplevel()
            root.protocol("WM_DELETE_WINDOW", self._on_window_close)
        except Exception:
            pass
    
    def _on_window_close(self) -> None:
        """Handle window X button click."""
        self._cleanup_and_quit()
    
    def _cleanup_and_quit(self) -> None:
        """Clean up and quit the game properly."""
        try:
            # Stop game loop
            if self.game_loop:
                self.game_loop.stop()
            
            # Clean up screen
            if self.game_loop and self.game_loop.screen:
                try:
                    self.game_loop.screen.bye()
                except Exception:
                    pass
        except Exception:
            pass
        
        # Force exit
        sys.exit(0)
    
    def _add_systems(self) -> None:
        """Add all game systems."""
        cfg = self.config
        loop = self.game_loop
        
        # Input (first)
        loop.add_system(InputSystem(loop.screen))
        
        # Upgrade system (before other systems apply)
        loop.add_system(UpgradeSystem())
        
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
    
    def _setup_menu(self) -> None:
        """Set up the menu system."""
        self.menu = MenuSystem(
            self.game_loop.screen,
            self.config.arena.width,
            self.config.arena.height
        )
        self.menu.initialize()
        
        # Set callbacks
        self.menu.set_callbacks(
            on_start=self._start_new_game,
            on_restart=self._restart_game,
            on_resume=self._resume_game,
            on_quit=self._cleanup_and_quit
        )
    
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
        player = create_player(entities, 0, 0, self.config)
        
        # Add upgrades component to player
        entities.add_component(player, PlayerUpgrades())
        
        # Create some obstacles
        create_arena_obstacles(
            entities,
            self.config.arena.width,
            self.config.arena.height,
            obstacle_count=5
        )
    
    def _start_new_game(self) -> None:
        """Start a new game."""
        self.game_started = True
        self.is_paused = False
        
        # Clear all existing entities except player
        self._clear_entities()
        
        # Create entities
        self._create_entities()
        
        # Reset upgrade system
        upgrade_system = self.game_loop.get_system(UpgradeSystem)
        if upgrade_system:
            upgrade_system.reset_player_upgrades()
        
        # Start wave system
        wave_system = self.game_loop.get_system(WaveSystem)
        if wave_system:
            wave_system.start_game()
        
        # Resume game state
        self.game_loop.change_state(GameState.RUNNING)
        
        # Hide menu
        self.menu.hide()
    
    def _restart_game(self) -> None:
        """Restart the game."""
        self._start_new_game()
    
    def _resume_game(self) -> None:
        """Resume the paused game."""
        self.is_paused = False
        self.game_loop.change_state(GameState.RUNNING)
        self.menu.hide()
    
    def _pause_game(self) -> None:
        """Pause the game."""
        if not self.game_started:
            return
        
        if self.game_loop.state == GameState.RUNNING:
            self.is_paused = True
            self.game_loop.change_state(GameState.PAUSED)
            self.menu.show_pause_menu()
    
    def _clear_entities(self) -> None:
        """Clear all game entities."""
        if self.game_loop and self.game_loop.entity_manager:
            # Get all entities and destroy them
            for entity in list(self.game_loop.entities):
                try:
                    self.game_loop.entities.destroy_entity(entity)
                except Exception:
                    pass
            
            # Flush destroyed entities
            try:
                self.game_loop.entities.flush_destroyed()
            except Exception:
                pass
    
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
        
        # Check for pause input
        self._check_pause_input()
        
        # Don't draw game UI if menu is active
        if self.menu and self.menu.state != MenuState.HIDDEN:
            self.ui_turtle.clear()
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
            upgrades = self.game_loop.entities.get_component(player, PlayerUpgrades)
            
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
            
            # Draw upgrade display
            if upgrades:
                self._draw_upgrade_display(upgrades, hw, hh)
        
        # Wave announcement
        if self.show_wave_text:
            self.wave_text_timer -= dt
            if self.wave_text_timer <= 0:
                self.show_wave_text = False
            else:
                self._draw_text(
                    self.current_wave_text,
                    0, 50,
                    size=28,
                    color="#ffffff"
                )
        
        # Controls hint
        self._draw_text(
            "WASD: Move | Arrows/Mouse: Aim | Space: Fire | ESC: Pause | Q: Quit",
            0, -hh + 15,
            size=12,
            color="#888888"
        )
    
    def _draw_upgrade_display(self, upgrades: PlayerUpgrades, hw: float, hh: float) -> None:
        """Draw the upgrade stacks display."""
        if upgrades.total_stacks == 0:
            return
        
        # Draw upgrade stats on the left side
        y_offset = hh - 90
        
        # Show key upgrades
        upgrades_to_show = [
            ("⚔️ DMG", upgrades.damage_multiplier - 1.0, 20, "#ff4444"),
            ("🔫 FR", 1.0 - upgrades.fire_rate_multiplier, 15, "#ffaa00"),
            ("🏃 SPD", upgrades.speed_multiplier - 1.0, 10, "#00ffff"),
            ("💚 HP+", upgrades.max_hp_bonus, 150, "#00ff00"),
            ("🛡️ ARM", upgrades.armor_bonus, 30, "#888888"),
        ]
        
        for icon_label, value, max_val, color in upgrades_to_show:
            if value > 0:
                # Calculate bar width based on percentage of max
                pct = min(1.0, value / (max_val * 0.05) if max_val < 50 else value / max_val)
                
                # Draw bar background
                self.ui_turtle.goto(-hw + 10, y_offset)
                self.ui_turtle.pendown()
                self.ui_turtle.pensize(8)
                self.ui_turtle.pencolor("#333333")
                self.ui_turtle.forward(60)
                self.ui_turtle.penup()
                
                # Draw bar fill
                if pct > 0:
                    self.ui_turtle.goto(-hw + 10, y_offset)
                    self.ui_turtle.pendown()
                    self.ui_turtle.pencolor(color)
                    self.ui_turtle.forward(60 * pct)
                    self.ui_turtle.penup()
                
                # Draw label
                if value < 1:
                    self._draw_text(
                        f"{icon_label}: +{value*100:.0f}%",
                        -hw + 75, y_offset - 4,
                        size=9,
                        color=color,
                        align="left"
                    )
                else:
                    self._draw_text(
                        f"{icon_label}: +{value:.0f}",
                        -hw + 75, y_offset - 4,
                        size=9,
                        color=color,
                        align="left"
                    )
                
                y_offset -= 15
    
    def _check_pause_input(self) -> None:
        """Check for pause input."""
        # Input system handles ESC through action callback
        pass
    
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
        
        # Update upgrade system with current wave
        upgrade_system = self.game_loop.get_system(UpgradeSystem)
        if upgrade_system:
            upgrade_system.set_wave(event.wave_number)
    
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
        wave_system = self.game_loop.get_system(WaveSystem)
        
        if event.state == "game_over":
            self.game_loop.change_state(GameState.GAME_OVER)
            
            score = wave_system.score if wave_system else 0
            wave = wave_system.current_wave if wave_system else 0
            kills = wave_system.kills if wave_system else 0
            
            self.menu.show_game_over(score, wave, kills)
            
        elif event.state == "victory":
            self.game_loop.change_state(GameState.VICTORY)
            
            score = wave_system.score if wave_system else 0
            wave = wave_system.current_wave if wave_system else 0
            kills = wave_system.kills if wave_system else 0
            
            self.menu.show_victory(score, wave, kills)
            
        elif event.state == "paused":
            self._pause_game()
    
    def run(self) -> None:
        """Run the game."""
        if not self.game_loop:
            self.setup()
        
        # Set up ESC key for pause
        input_system = self.game_loop.get_system(InputSystem)
        if input_system:
            from engine.systems.input_system import GameAction
            input_system.set_action_callback(
                GameAction.PAUSE,
                self._toggle_pause
            )
            input_system.set_action_callback(
                GameAction.QUIT,
                self._handle_quit_key
            )
        
        self.game_loop.run()
    
    def _toggle_pause(self) -> None:
        """Toggle pause state."""
        if not self.game_started:
            return
        
        if self.menu.state == MenuState.HIDDEN:
            self._pause_game()
        elif self.menu.state == MenuState.PAUSED:
            self._resume_game()
    
    def _handle_quit_key(self) -> None:
        """Handle Q key press."""
        if self.menu.state == MenuState.HIDDEN:
            # Show pause menu instead of quitting immediately
            self._pause_game()
        else:
            # In menu, quit immediately
            self._cleanup_and_quit()


def main():
    """Main entry point."""
    print("=" * 50)
    print("  ROBO-ARENA")
    print("  A Turtle Arena Shooter")
    print("=" * 50)
    print()
    print("Controls:")
    print("  W/A/S/D       - Move (omnidirectional)")
    print("  Arrow Keys    - Aim direction")
    print("  Mouse         - Aim direction (alternative)")
    print("  Space/Click   - Fire")
    print("  R             - Reload")
    print("  Escape        - Pause Menu")
    print("  Q             - Quit")
    print()
    print("Upgrades drop from enemies!")
    print("Take damage = 50% chance to lose an upgrade stack")
    print()
    
    # Create and run game
    game = RoboArena()
    game.setup()
    game.run()


if __name__ == "__main__":
    main()
