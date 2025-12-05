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

from .config import GameConfig, DEFAULT_CONFIG, ArenaTheme, THEME_PALETTES
from .prefabs import create_player, create_arena_obstacles


# Upgrade synergy definitions
UPGRADE_SYNERGIES = {
    "geometry_master": {
        "name": "GEOMETRY MASTER",
        "required": ["multishot", "ricochet", "piercing"],
        "color": "#ff00ff",
        "description": "Bullets leave rainbow trails"
    },
    "unstoppable": {
        "name": "UNSTOPPABLE",
        "required": ["armor", "hp", "regeneration"],
        "color": "#ffaa00",
        "description": "Metallic sheen + extra glow"
    },
    "berserker": {
        "name": "BERSERKER",
        "required": ["damage", "fire_rate", "speed"],
        "color": "#ff0000",
        "description": "Glass cannon mode"
    },
    "technomancer": {
        "name": "TECHNOMANCER",
        "required": ["shield_regen", "time_dilation", "ally_drone"],
        "color": "#00ffff",
        "description": "Tech mastery"
    }
}


class RoboArena:
    """
    Main game class for Robo-Arena.
    
    Orchestrates the game setup, UI, menu system, and game-specific logic.
    Features:
    - Advanced menu system
    - Wave-based progression
    - Dynamic difficulty
    - Upgrade synergies
    - Narrative framing
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
        
        # Narrative state
        self.show_narrative = False
        self.narrative_text = ""
        self.narrative_timer = 0.0
        
        # Synergy state
        self.active_synergies: list = []
        self.synergy_check_timer = 0.0
        
        # Boss intro state
        self.show_boss_intro = False
        self.boss_name = ""
        self.boss_intro_timer = 0.0
        
        # Special event state
        self.show_event_text = False
        self.event_text = ""
        self.event_timer = 0.0
        
        # Game state
        self.game_started = False
        self.is_paused = False
        
        # Arena theme (changes per wave range)
        self.current_theme = ArenaTheme.GRID
    
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
        
        # Re-enable input system key bindings (menu may have overwritten them)
        input_system = self.game_loop.get_system(InputSystem)
        if input_system:
            input_system.rebind_keys()
    
    def _restart_game(self) -> None:
        """Restart the game."""
        self._start_new_game()
    
    def _resume_game(self) -> None:
        """Resume the paused game."""
        self.is_paused = False
        self.game_loop.change_state(GameState.RUNNING)
        self.menu.hide()
        
        # Re-enable input system key bindings (menu may have overwritten them)
        input_system = self.game_loop.get_system(InputSystem)
        if input_system:
            input_system.rebind_keys()
    
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
        
        # Draw HUD - positioned at BOTTOM of screen to not block spawn areas
        hw = self.config.arena.width / 2
        hh = self.config.arena.height / 2
        
        # Wave/Score info - bottom left corner (compact)
        if wave_system:
            self._draw_text(
                f"W:{wave_system.current_wave} | Score:{wave_system.score} | E:{wave_system.enemies_remaining}",
                -hw + 10, -hh + 35,
                align="left",
                size=11,
                color="#aaaaaa"
            )
        
        # Player health - bottom center
        player = self.game_loop.entities.get_named("player")
        if player:
            health = self.game_loop.entities.get_component(player, Health)
            shield = self.game_loop.entities.get_component(player, Shield)
            upgrades = self.game_loop.entities.get_component(player, PlayerUpgrades)
            
            # Health bar at bottom center
            if health:
                self._draw_health_bar(
                    -60, -hh + 55,
                    120, 12,
                    health.health_percent,
                    "#00ff00", "#333333"
                )
                self._draw_text(
                    f"HP: {int(health.hp)}/{int(health.max_hp)}",
                    0, -hh + 52,
                    size=9,
                    color="#ffffff"
                )
            
            # Shield bar below health
            if shield and shield.max_hp > 0:
                self._draw_health_bar(
                    -50, -hh + 38,
                    100, 8,
                    shield.shield_percent,
                    "#4444ff", "#222244"
                )
            
            # Draw upgrade display on the RIGHT side (vertical strip)
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
        
        # Boss introduction
        if self.show_boss_intro:
            self.boss_intro_timer -= dt
            if self.boss_intro_timer <= 0:
                self.show_boss_intro = False
            else:
                # Draw boss intro overlay
                self._draw_text(
                    "⚠ BOSS APPROACHING ⚠",
                    0, 80,
                    size=16,
                    color="#ff4444"
                )
                self._draw_text(
                    self.boss_name,
                    0, 50,
                    size=32,
                    color="#ff8800"
                )
                self._draw_text(
                    "ENGAGE",
                    0, 15,
                    size=14,
                    color="#ffffff"
                )
        
        # Narrative text
        if self.show_narrative:
            self.narrative_timer -= dt
            if self.narrative_timer <= 0:
                self.show_narrative = False
            else:
                # Draw narrative overlay
                lines = self.narrative_text.split('\n')
                y_start = 30 + len(lines) * 10
                for i, line in enumerate(lines):
                    self._draw_text(
                        line,
                        0, y_start - i * 20,
                        size=12,
                        color="#aaaaaa"
                    )
        
        # Special event notification
        wave_system = self.game_loop.get_system(WaveSystem)
        if wave_system and wave_system.event_active:
            event_colors = {
                "energy_surge": "#ffff00",
                "gold_rush": "#ffd700",
                "enemy_mutation": "#ff0044"
            }
            event_names = {
                "energy_surge": "⚡ ENERGY SURGE ⚡",
                "gold_rush": "💰 GOLD RUSH 💰",
                "enemy_mutation": "☠ ENEMY MUTATION ☠"
            }
            color = event_colors.get(wave_system.event_type, "#ffffff")
            name = event_names.get(wave_system.event_type, "SPECIAL EVENT")
            self._draw_text(
                name,
                0, hh - 40,
                size=14,
                color=color
            )
        
        # Synergy badges (check periodically)
        self.synergy_check_timer += dt
        if self.synergy_check_timer >= 1.0:  # Check every second
            self.synergy_check_timer = 0
            if upgrades:
                self._check_upgrade_synergies(upgrades)
        
        # Draw active synergies
        if self.active_synergies:
            synergy_y = hh - 25
            for synergy in self.active_synergies[:2]:  # Max 2 shown
                self._draw_text(
                    f"[{synergy['name']}]",
                    0, synergy_y,
                    size=10,
                    color=synergy['color']
                )
                synergy_y -= 15
        
        # Controls hint - bottom
        self._draw_text(
            "WASD: Move | Mouse/Click: Shoot | ESC: Pause",
            0, -hh + 15,
            size=10,
            color="#666666"
        )
    
    def _draw_upgrade_display(self, upgrades: PlayerUpgrades, hw: float, hh: float) -> None:
        """Draw the upgrade stacks display on the RIGHT side - thin vertical strip."""
        if upgrades.total_stacks == 0:
            return
        
        # Draw upgrade stats on the RIGHT side (thin vertical strip, doesn't block gameplay)
        y_offset = 0  # Start at middle-right
        x_pos = hw - 8  # Right edge
        
        # Show key upgrades as compact icons
        upgrades_to_show = [
            ("D", upgrades.damage_multiplier - 1.0, 20, "#ff4444"),  # D = Damage
            ("F", 1.0 - upgrades.fire_rate_multiplier, 15, "#ffaa00"),  # F = Fire rate
            ("S", upgrades.speed_multiplier - 1.0, 10, "#00ffff"),  # S = Speed
            ("H", upgrades.max_hp_bonus, 150, "#00ff00"),  # H = HP
            ("A", upgrades.armor_bonus, 30, "#888888"),  # A = Armor
        ]
        
        active_count = sum(1 for _, v, _, _ in upgrades_to_show if v > 0)
        if active_count > 0:
            y_offset = (active_count * 18) // 2
        
        for icon_label, value, max_val, color in upgrades_to_show:
            if value > 0:
                # Calculate bar width based on percentage of max
                pct = min(1.0, value / (max_val * 0.05) if max_val < 50 else value / max_val)
                
                # Draw vertical bar (thin)
                bar_height = 14
                bar_width = 4
                
                # Background
                self.ui_turtle.goto(x_pos, y_offset - bar_height//2)
                self.ui_turtle.pendown()
                self.ui_turtle.pensize(bar_width)
                self.ui_turtle.pencolor("#333333")
                self.ui_turtle.setheading(90)
                self.ui_turtle.forward(bar_height)
                self.ui_turtle.penup()
                
                # Fill
                if pct > 0:
                    self.ui_turtle.goto(x_pos, y_offset - bar_height//2)
                    self.ui_turtle.pendown()
                    self.ui_turtle.pencolor(color)
                    self.ui_turtle.forward(bar_height * pct)
                    self.ui_turtle.penup()
                
                # Letter icon
                self._draw_text(
                    icon_label,
                    x_pos - 12, y_offset - 5,
                    size=8,
                    color=color,
                    align="center"
                )
                
                y_offset -= 18
    
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
        wave_num = event.wave_number
        
        # Check for boss wave
        if wave_num % 5 == 0:
            self._show_boss_intro(wave_num)
        else:
            self.current_wave_text = f"Wave {wave_num}"
            self.show_wave_text = True
            self.wave_text_timer = 2.0
        
        # Update upgrade system with current wave
        upgrade_system = self.game_loop.get_system(UpgradeSystem)
        if upgrade_system:
            upgrade_system.set_wave(wave_num)
        
        # Update arena theme based on wave progression
        self._update_arena_theme(wave_num)
        
        # Check for special narrative moments
        self._check_narrative_trigger(wave_num)
    
    def _show_boss_intro(self, wave_num: int) -> None:
        """Show boss introduction sequence."""
        boss_names = {
            5: "THE CONSTRUCTOR",
            10: "THE SHADOW",
            15: "THE ARCHITECT",
            20: "THE FINAL TRIAL"
        }
        
        self.boss_name = boss_names.get(wave_num, f"BOSS WAVE {wave_num}")
        self.show_boss_intro = True
        self.boss_intro_timer = 3.0
        self.show_wave_text = False
    
    def _update_arena_theme(self, wave_num: int) -> None:
        """Update arena theme based on wave number."""
        # Change theme every few waves for visual variety
        if wave_num <= 3:
            new_theme = ArenaTheme.GRID
        elif wave_num <= 5:
            new_theme = ArenaTheme.CRYSTAL
        elif wave_num <= 7:
            new_theme = ArenaTheme.VOID
        elif wave_num <= 10:
            new_theme = ArenaTheme.CORRUPTED
        elif wave_num <= 15:
            new_theme = ArenaTheme.FORGE
        else:
            new_theme = ArenaTheme.NEXUS
        
        if new_theme != self.current_theme:
            self.current_theme = new_theme
            # Update render system theme
            render_system = self.game_loop.get_system(RenderSystem)
            if render_system:
                render_system.set_arena_theme(new_theme)
    
    def _check_narrative_trigger(self, wave_num: int) -> None:
        """Check if a narrative moment should be shown."""
        narratives = {
            1: "You are a lone defense unit in a corrupted sector.\nSurvive. Evolve. Transcend.",
            5: "The first guardian approaches.\nDestroy it to regain control.",
            10: "Darkness gathers. The Shadow emerges.",
            15: "The Architect orchestrates the chaos.\nPrepare for the final push.",
            20: "This is the Final Trial.\nEverything you've learned will be tested."
        }
        
        if wave_num in narratives:
            self.narrative_text = narratives[wave_num]
            self.show_narrative = True
            self.narrative_timer = 4.0
    
    def _check_upgrade_synergies(self, upgrades) -> None:
        """Check if player has achieved any upgrade synergies."""
        from engine.components.upgrades import UpgradeType
        
        self.active_synergies.clear()
        
        # Map upgrade types to simple names for synergy checking
        type_mapping = {
            UpgradeType.MULTISHOT: "multishot",
            UpgradeType.RICOCHET: "ricochet",
            UpgradeType.PIERCING: "piercing",
            UpgradeType.ARMOR_PLUS: "armor",
            UpgradeType.HP_PLUS: "hp",
            UpgradeType.REGENERATION: "regeneration",
            UpgradeType.DAMAGE_PLUS: "damage",
            UpgradeType.FIRE_RATE_PLUS: "fire_rate",
            UpgradeType.SPEED_PLUS: "speed",
            UpgradeType.SHIELD_REGEN: "shield_regen",
            UpgradeType.TIME_DILATION: "time_dilation",
            UpgradeType.ALLY_DRONE: "ally_drone",
        }
        
        # Get list of upgrade types the player has
        player_upgrade_names = set()
        for upgrade_type in upgrades.upgrades.keys():
            if upgrade_type in type_mapping:
                player_upgrade_names.add(type_mapping[upgrade_type])
        
        # Check each synergy
        for synergy_id, synergy in UPGRADE_SYNERGIES.items():
            required = set(synergy["required"])
            if required.issubset(player_upgrade_names):
                self.active_synergies.append(synergy)
    
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
    print()
    print("═" * 55)
    print("           ╔═══════════════════════════╗")
    print("           ║      R O B O - A R E N A   ║")
    print("           ╚═══════════════════════════╝")
    print("═" * 55)
    print()
    print("         THE ARENA PROTOCOL")
    print()
    print("  You are a lone defense unit in a corrupted sector.")
    print("  Wave after wave of hostile entities approach.")
    print("  You can't retreat.")
    print()
    print("  You can only upgrade.")
    print()
    print("  Survive. Evolve. Transcend.")
    print()
    print("─" * 55)
    print("  CONTROLS:")
    print("    W/A/S/D     - Move (omnidirectional)")
    print("    Mouse       - Aim (player faces cursor)")
    print("    Click/Space - Fire")
    print("    R           - Reload")
    print("    Escape      - Pause Menu")
    print()
    print("  UPGRADE SYSTEM:")
    print("    • Kill enemies to collect upgrade drops")
    print("    • Upgrades stack for increased power")
    print("    • Taking damage = 50% chance to lose a stack")
    print("    • Bosses every 5 waves (guaranteed epic drops)")
    print()
    print("  ENEMY TYPES:")
    print("    Blue    = Swarmer (fast, weak)")
    print("    Green   = Scout (ranged)")
    print("    Red     = Heavy (slow, tanky)")
    print("    Purple  = Specialist (unique mechanics)")
    print("    Orange  = Elite (dangerous)")
    print("─" * 55)
    print()
    
    # Create and run game
    game = RoboArena()
    game.setup()
    game.run()


if __name__ == "__main__":
    main()
