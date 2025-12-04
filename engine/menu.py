"""
Advanced Menu System - Main menu, pause menu, and game over screens.

Features:
- Main menu with Start, Quit buttons
- Pause menu with Resume, Restart, Quit buttons
- Game over screen with Restart, Quit buttons
- Victory screen with stats and buttons
- Proper window close (X button) handling
- Keyboard and mouse navigation
"""

from __future__ import annotations
import turtle
import sys
from typing import Optional, Callable, List, Dict, Tuple
from enum import Enum, auto
from dataclasses import dataclass


class MenuState(Enum):
    """Current menu state."""
    HIDDEN = auto()
    MAIN_MENU = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()
    OPTIONS = auto()


@dataclass
class MenuButton:
    """A clickable menu button."""
    text: str
    x: float
    y: float
    width: float = 200
    height: float = 50
    callback: Optional[Callable[[], None]] = None
    color: str = "#444466"
    hover_color: str = "#6666aa"
    text_color: str = "#ffffff"
    selected: bool = False
    
    def contains_point(self, px: float, py: float) -> bool:
        """Check if a point is inside the button."""
        half_w = self.width / 2
        half_h = self.height / 2
        return (self.x - half_w <= px <= self.x + half_w and
                self.y - half_h <= py <= self.y + half_h)


class MenuSystem:
    """
    Advanced menu system with multiple screens and proper quit handling.
    
    Features:
    - Main menu (before game starts)
    - Pause menu (during gameplay)
    - Game over / Victory screens
    - Button hover effects
    - Keyboard navigation (up/down + Enter)
    - Mouse click support
    - Proper window close handling
    """
    
    def __init__(self, screen: turtle.Screen, arena_width: int = 800, arena_height: int = 600):
        self.screen = screen
        self.arena_width = arena_width
        self.arena_height = arena_height
        
        # State
        self.state = MenuState.MAIN_MENU
        self.is_active = True
        
        # Buttons for each menu
        self.main_menu_buttons: List[MenuButton] = []
        self.pause_buttons: List[MenuButton] = []
        self.game_over_buttons: List[MenuButton] = []
        self.victory_buttons: List[MenuButton] = []
        
        # Selected button index (for keyboard navigation)
        self.selected_index = 0
        
        # Turtle for rendering
        self._menu_turtle: Optional[turtle.Turtle] = None
        
        # Callbacks
        self._on_start: Optional[Callable[[], None]] = None
        self._on_restart: Optional[Callable[[], None]] = None
        self._on_resume: Optional[Callable[[], None]] = None
        self._on_quit: Optional[Callable[[], None]] = None
        
        # Stats for end screens
        self.final_score = 0
        self.final_wave = 0
        self.total_kills = 0
        
        # Window close flag
        self._window_closed = False
        
    def initialize(self) -> None:
        """Set up the menu system."""
        # Create menu turtle
        self._menu_turtle = turtle.Turtle()
        self._menu_turtle.hideturtle()
        self._menu_turtle.penup()
        self._menu_turtle.speed(0)
        
        # Create buttons
        self._create_buttons()
        
        # Set up input handlers
        self._setup_input()
        
        # Handle window close (X button)
        self._setup_window_close_handler()
        
    def _setup_window_close_handler(self) -> None:
        """Set up handler for window X button."""
        try:
            # Get the root Tk window
            root = self.screen.getcanvas().winfo_toplevel()
            
            # Set the protocol for window close
            root.protocol("WM_DELETE_WINDOW", self._on_window_close)
        except Exception:
            pass
    
    def _on_window_close(self) -> None:
        """Handle window X button click."""
        self._window_closed = True
        self.quit_game()
    
    def _create_buttons(self) -> None:
        """Create all menu buttons."""
        center_x = 0
        
        # Main menu buttons
        self.main_menu_buttons = [
            MenuButton(
                text="START GAME",
                x=center_x, y=50,
                width=250, height=60,
                callback=self._start_game,
                color="#228822"
            ),
            MenuButton(
                text="QUIT",
                x=center_x, y=-50,
                width=250, height=60,
                callback=self.quit_game,
                color="#882222"
            ),
        ]
        
        # Pause menu buttons
        self.pause_buttons = [
            MenuButton(
                text="RESUME",
                x=center_x, y=80,
                width=250, height=60,
                callback=self._resume_game,
                color="#226688"
            ),
            MenuButton(
                text="RESTART",
                x=center_x, y=0,
                width=250, height=60,
                callback=self._restart_game,
                color="#666622"
            ),
            MenuButton(
                text="QUIT TO DESKTOP",
                x=center_x, y=-80,
                width=250, height=60,
                callback=self.quit_game,
                color="#882222"
            ),
        ]
        
        # Game over buttons
        self.game_over_buttons = [
            MenuButton(
                text="TRY AGAIN",
                x=center_x, y=-50,
                width=250, height=60,
                callback=self._restart_game,
                color="#228822"
            ),
            MenuButton(
                text="QUIT",
                x=center_x, y=-130,
                width=250, height=60,
                callback=self.quit_game,
                color="#882222"
            ),
        ]
        
        # Victory buttons
        self.victory_buttons = [
            MenuButton(
                text="PLAY AGAIN",
                x=center_x, y=-80,
                width=250, height=60,
                callback=self._restart_game,
                color="#228822"
            ),
            MenuButton(
                text="QUIT",
                x=center_x, y=-160,
                width=250, height=60,
                callback=self.quit_game,
                color="#882222"
            ),
        ]
    
    def _setup_input(self) -> None:
        """Set up keyboard and mouse input."""
        self.screen.listen()
        
        # Keyboard navigation
        self.screen.onkeypress(self._navigate_up, "Up")
        self.screen.onkeypress(self._navigate_up, "w")
        self.screen.onkeypress(self._navigate_down, "Down")
        self.screen.onkeypress(self._navigate_down, "s")
        self.screen.onkeypress(self._select_button, "Return")
        self.screen.onkeypress(self._select_button, "space")
        self.screen.onkeypress(self._handle_escape, "Escape")
        
        # Mouse click
        self.screen.onclick(self._on_click)
    
    def _get_current_buttons(self) -> List[MenuButton]:
        """Get the buttons for the current menu state."""
        if self.state == MenuState.MAIN_MENU:
            return self.main_menu_buttons
        elif self.state == MenuState.PAUSED:
            return self.pause_buttons
        elif self.state == MenuState.GAME_OVER:
            return self.game_over_buttons
        elif self.state == MenuState.VICTORY:
            return self.victory_buttons
        return []
    
    def _navigate_up(self) -> None:
        """Navigate up in the menu."""
        if self.state == MenuState.HIDDEN:
            return
        
        buttons = self._get_current_buttons()
        if buttons:
            self.selected_index = (self.selected_index - 1) % len(buttons)
            self._update_selection()
    
    def _navigate_down(self) -> None:
        """Navigate down in the menu."""
        if self.state == MenuState.HIDDEN:
            return
        
        buttons = self._get_current_buttons()
        if buttons:
            self.selected_index = (self.selected_index + 1) % len(buttons)
            self._update_selection()
    
    def _update_selection(self) -> None:
        """Update button selection states."""
        buttons = self._get_current_buttons()
        for i, button in enumerate(buttons):
            button.selected = (i == self.selected_index)
        self.render()
    
    def _select_button(self) -> None:
        """Activate the selected button."""
        if self.state == MenuState.HIDDEN:
            return
        
        buttons = self._get_current_buttons()
        if buttons and 0 <= self.selected_index < len(buttons):
            button = buttons[self.selected_index]
            if button.callback:
                button.callback()
    
    def _handle_escape(self) -> None:
        """Handle escape key."""
        if self.state == MenuState.PAUSED:
            self._resume_game()
        elif self.state == MenuState.HIDDEN:
            self.show_pause_menu()
    
    def _on_click(self, x: float, y: float) -> None:
        """Handle mouse click."""
        if self.state == MenuState.HIDDEN:
            return
        
        buttons = self._get_current_buttons()
        for i, button in enumerate(buttons):
            if button.contains_point(x, y):
                self.selected_index = i
                self._update_selection()
                if button.callback:
                    button.callback()
                break
    
    def _start_game(self) -> None:
        """Start a new game."""
        self.state = MenuState.HIDDEN
        if self._on_start:
            self._on_start()
        self.clear()
    
    def _resume_game(self) -> None:
        """Resume the current game."""
        self.state = MenuState.HIDDEN
        if self._on_resume:
            self._on_resume()
        self.clear()
    
    def _restart_game(self) -> None:
        """Restart the game."""
        self.state = MenuState.HIDDEN
        if self._on_restart:
            self._on_restart()
        self.clear()
    
    def quit_game(self) -> None:
        """Quit the game properly."""
        self.is_active = False
        
        if self._on_quit:
            self._on_quit()
        
        try:
            # Clean up turtle
            if self._menu_turtle:
                self._menu_turtle.hideturtle()
            
            # Close the screen properly
            self.screen.bye()
        except Exception:
            pass
        
        # Force exit
        sys.exit(0)
    
    def set_callbacks(
        self,
        on_start: Optional[Callable[[], None]] = None,
        on_restart: Optional[Callable[[], None]] = None,
        on_resume: Optional[Callable[[], None]] = None,
        on_quit: Optional[Callable[[], None]] = None
    ) -> None:
        """Set menu callbacks."""
        self._on_start = on_start
        self._on_restart = on_restart
        self._on_resume = on_resume
        self._on_quit = on_quit
    
    def show_main_menu(self) -> None:
        """Show the main menu."""
        self.state = MenuState.MAIN_MENU
        self.selected_index = 0
        self._update_selection()
        self.render()
    
    def show_pause_menu(self) -> None:
        """Show the pause menu."""
        self.state = MenuState.PAUSED
        self.selected_index = 0
        self._update_selection()
        self.render()
    
    def show_game_over(self, score: int = 0, wave: int = 0, kills: int = 0) -> None:
        """Show the game over screen."""
        self.final_score = score
        self.final_wave = wave
        self.total_kills = kills
        self.state = MenuState.GAME_OVER
        self.selected_index = 0
        self._update_selection()
        self.render()
    
    def show_victory(self, score: int = 0, wave: int = 0, kills: int = 0) -> None:
        """Show the victory screen."""
        self.final_score = score
        self.final_wave = wave
        self.total_kills = kills
        self.state = MenuState.VICTORY
        self.selected_index = 0
        self._update_selection()
        self.render()
    
    def hide(self) -> None:
        """Hide the menu."""
        self.state = MenuState.HIDDEN
        self.clear()
    
    def render(self) -> None:
        """Render the current menu."""
        if self.state == MenuState.HIDDEN:
            self.clear()
            return
        
        if not self._menu_turtle:
            return
        
        t = self._menu_turtle
        t.clear()
        
        # Draw semi-transparent overlay
        self._draw_overlay()
        
        # Draw title and content based on state
        if self.state == MenuState.MAIN_MENU:
            self._draw_main_menu()
        elif self.state == MenuState.PAUSED:
            self._draw_pause_menu()
        elif self.state == MenuState.GAME_OVER:
            self._draw_game_over()
        elif self.state == MenuState.VICTORY:
            self._draw_victory()
        
        # Draw buttons
        self._draw_buttons(self._get_current_buttons())
        
        try:
            self.screen.update()
        except Exception:
            pass
    
    def _draw_overlay(self) -> None:
        """Draw a semi-transparent overlay."""
        t = self._menu_turtle
        hw = self.arena_width / 2
        hh = self.arena_height / 2
        
        # Dark overlay (simulate transparency with color)
        t.goto(-hw, -hh)
        t.color("#000000")
        t.begin_fill()
        for _ in range(2):
            t.forward(self.arena_width)
            t.left(90)
            t.forward(self.arena_height)
            t.left(90)
        t.end_fill()
    
    def _draw_main_menu(self) -> None:
        """Draw main menu content."""
        t = self._menu_turtle
        
        # Title
        t.goto(0, 150)
        t.color("#00ff88")
        t.write("ROBO-ARENA", align="center", font=("Arial", 48, "bold"))
        
        # Subtitle
        t.goto(0, 100)
        t.color("#888888")
        t.write("A Top-Down Arena Shooter", align="center", font=("Arial", 16, "normal"))
        
        # Controls hint
        t.goto(0, -180)
        t.color("#666666")
        t.write("WASD: Move | Arrow Keys/Mouse: Aim | Space: Fire", 
                align="center", font=("Arial", 12, "normal"))
        t.goto(0, -210)
        t.write("Use ↑↓ or W/S to navigate, Enter to select", 
                align="center", font=("Arial", 12, "normal"))
    
    def _draw_pause_menu(self) -> None:
        """Draw pause menu content."""
        t = self._menu_turtle
        
        # Title
        t.goto(0, 180)
        t.color("#ffffff")
        t.write("PAUSED", align="center", font=("Arial", 36, "bold"))
    
    def _draw_game_over(self) -> None:
        """Draw game over screen."""
        t = self._menu_turtle
        
        # Title
        t.goto(0, 180)
        t.color("#ff4444")
        t.write("GAME OVER", align="center", font=("Arial", 48, "bold"))
        
        # Stats
        t.goto(0, 100)
        t.color("#ffffff")
        t.write(f"Wave Reached: {self.final_wave}", align="center", font=("Arial", 20, "normal"))
        
        t.goto(0, 60)
        t.write(f"Final Score: {self.final_score:,}", align="center", font=("Arial", 24, "bold"))
        
        t.goto(0, 20)
        t.color("#888888")
        t.write(f"Enemies Defeated: {self.total_kills}", align="center", font=("Arial", 16, "normal"))
    
    def _draw_victory(self) -> None:
        """Draw victory screen."""
        t = self._menu_turtle
        
        # Title
        t.goto(0, 200)
        t.color("#00ff00")
        t.write("VICTORY!", align="center", font=("Arial", 48, "bold"))
        
        t.goto(0, 150)
        t.color("#ffff00")
        t.write("You survived all waves!", align="center", font=("Arial", 20, "normal"))
        
        # Stats
        t.goto(0, 80)
        t.color("#ffffff")
        t.write(f"Final Score: {self.final_score:,}", align="center", font=("Arial", 28, "bold"))
        
        t.goto(0, 40)
        t.color("#888888")
        t.write(f"Total Enemies Defeated: {self.total_kills}", align="center", font=("Arial", 16, "normal"))
    
    def _draw_buttons(self, buttons: List[MenuButton]) -> None:
        """Draw menu buttons."""
        t = self._menu_turtle
        
        for button in buttons:
            # Button background
            color = button.hover_color if button.selected else button.color
            
            half_w = button.width / 2
            half_h = button.height / 2
            
            t.goto(button.x - half_w, button.y - half_h)
            t.color(color)
            t.begin_fill()
            for _ in range(2):
                t.forward(button.width)
                t.left(90)
                t.forward(button.height)
                t.left(90)
            t.end_fill()
            
            # Button border
            border_color = "#ffffff" if button.selected else "#888888"
            t.goto(button.x - half_w, button.y - half_h)
            t.pendown()
            t.pensize(3 if button.selected else 1)
            t.color(border_color)
            for _ in range(2):
                t.forward(button.width)
                t.left(90)
                t.forward(button.height)
                t.left(90)
            t.penup()
            
            # Button text
            t.goto(button.x, button.y - 10)
            t.color(button.text_color)
            t.write(button.text, align="center", font=("Arial", 18, "bold"))
            
            # Selection indicator
            if button.selected:
                t.goto(button.x - half_w - 20, button.y - 8)
                t.color("#ffff00")
                t.write("▶", align="center", font=("Arial", 20, "normal"))
    
    def clear(self) -> None:
        """Clear the menu display."""
        if self._menu_turtle:
            self._menu_turtle.clear()
    
    def is_window_closed(self) -> bool:
        """Check if window was closed."""
        return self._window_closed
    
    def update(self, dt: float) -> None:
        """Update menu (for animations or effects)."""
        pass  # Could add button hover effects here
