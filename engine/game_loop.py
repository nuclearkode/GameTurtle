"""
Game Loop - Main engine orchestrator.

Controls frame timing, system execution order, and game state management.
"""

from __future__ import annotations
import time
import turtle
from typing import Optional, List, Callable
from enum import Enum, auto
from dataclasses import dataclass

from .core import EntityManager, SystemManager, EventBus, GameSystem
from .core.events import GameStateEvent


class GameState(Enum):
    """High-level game states."""
    INITIALIZING = auto()
    RUNNING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()
    QUIT = auto()


@dataclass
class FrameStats:
    """Statistics about frame timing."""
    frame_count: int = 0
    total_time: float = 0.0
    dt: float = 0.0
    fps: float = 0.0
    avg_fps: float = 0.0
    min_dt: float = float('inf')
    max_dt: float = 0.0


class GameLoop:
    """
    Main game loop and engine orchestrator.
    
    Responsibilities:
    - Initialize turtle screen
    - Manage game state
    - Control frame timing (target FPS, dt)
    - Call systems in order
    - Handle starting, pausing, quitting
    
    Usage:
        loop = GameLoop(title="My Game", width=800, height=600)
        loop.setup()  # Add systems and create entities
        loop.run()    # Start the game
    
    Frame Order:
        1. Calculate dt
        2. Poll input / update input state
        3. Call systems in priority order
        4. Flush deferred entity destruction
        5. Flush deferred events
        6. Update screen
        7. Sleep to maintain target FPS
    """
    
    def __init__(
        self,
        title: str = "Robo-Arena",
        width: int = 800,
        height: int = 600,
        target_fps: int = 60,
        background_color: str = "black"
    ):
        self.title = title
        self.width = width
        self.height = height
        self.target_fps = target_fps
        self.target_dt = 1.0 / target_fps
        self.background_color = background_color
        
        # Core engine components
        self.screen: Optional[turtle.Screen] = None
        self.entity_manager: Optional[EntityManager] = None
        self.event_bus: Optional[EventBus] = None
        self.system_manager: Optional[SystemManager] = None
        
        # State
        self.state = GameState.INITIALIZING
        self.frame_stats = FrameStats()
        self._last_frame_time = 0.0
        self._running = False
        
        # Callbacks
        self._on_update_callbacks: List[Callable[[float], None]] = []
        self._on_state_change_callbacks: List[Callable[[GameState], None]] = []
    
    def initialize(self) -> None:
        """Initialize the engine and turtle screen."""
        # Create turtle screen
        self.screen = turtle.Screen()
        self.screen.setup(self.width + 50, self.height + 50)
        self.screen.title(self.title)
        self.screen.bgcolor(self.background_color)
        self.screen.tracer(0)  # Manual updates only
        
        # Hide default turtle
        turtle.hideturtle()
        
        # Create engine components
        self.entity_manager = EntityManager()
        self.event_bus = EventBus()
        self.system_manager = SystemManager(self.entity_manager, self.event_bus)
        
        # Subscribe to game state events
        self.event_bus.subscribe(GameStateEvent, self._on_game_state_event)
        
        self.state = GameState.RUNNING
    
    def add_system(self, system: GameSystem) -> GameSystem:
        """Add a system to the engine."""
        if self.system_manager is None:
            raise RuntimeError("Engine not initialized - call initialize() first")
        return self.system_manager.add_system(system)
    
    def get_system(self, system_type: type) -> Optional[GameSystem]:
        """Get a system by type."""
        if self.system_manager:
            return self.system_manager.get_system(system_type)
        return None
    
    def on_update(self, callback: Callable[[float], None]) -> None:
        """Register a callback to be called each frame."""
        self._on_update_callbacks.append(callback)
    
    def on_state_change(self, callback: Callable[[GameState], None]) -> None:
        """Register a callback for game state changes."""
        self._on_state_change_callbacks.append(callback)
    
    def _on_game_state_event(self, event: GameStateEvent) -> None:
        """Handle game state event from systems."""
        if event.state == "game_over":
            self.change_state(GameState.GAME_OVER)
        elif event.state == "victory":
            self.change_state(GameState.VICTORY)
        elif event.state == "paused":
            self.change_state(GameState.PAUSED)
        elif event.state == "playing":
            self.change_state(GameState.RUNNING)
    
    def change_state(self, new_state: GameState) -> None:
        """Change the game state."""
        old_state = self.state
        self.state = new_state
        
        for callback in self._on_state_change_callbacks:
            callback(new_state)
    
    def run(self) -> None:
        """Start the main game loop."""
        if self.screen is None:
            self.initialize()
        
        self._running = True
        self._last_frame_time = time.time()
        
        try:
            while self._running and self.state != GameState.QUIT:
                self._frame()
        except turtle.Terminator:
            pass
        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()
    
    def _frame(self) -> None:
        """Execute one frame."""
        # Calculate delta time
        current_time = time.time()
        dt = current_time - self._last_frame_time
        self._last_frame_time = current_time
        
        # Clamp dt to prevent spiral of death
        dt = min(dt, 0.1)  # Max 100ms per frame
        
        # Update frame stats
        self._update_stats(dt)
        
        # Skip update if paused (but still render)
        if self.state == GameState.RUNNING:
            # Update systems
            if self.system_manager:
                self.system_manager.update(dt)
            
            # Custom update callbacks
            for callback in self._on_update_callbacks:
                callback(dt)
            
            # Flush entity destruction
            if self.entity_manager:
                self.entity_manager.flush_destroyed()
            
            # Flush deferred events
            if self.event_bus:
                self.event_bus.flush_events()
        
        # Update screen (always, even when paused)
        if self.screen:
            self.screen.update()
        
        # Frame rate limiting
        elapsed = time.time() - current_time
        sleep_time = self.target_dt - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)
    
    def _update_stats(self, dt: float) -> None:
        """Update frame statistics."""
        self.frame_stats.frame_count += 1
        self.frame_stats.total_time += dt
        self.frame_stats.dt = dt
        self.frame_stats.fps = 1.0 / dt if dt > 0 else 0
        self.frame_stats.avg_fps = (
            self.frame_stats.frame_count / self.frame_stats.total_time
            if self.frame_stats.total_time > 0 else 0
        )
        self.frame_stats.min_dt = min(self.frame_stats.min_dt, dt)
        self.frame_stats.max_dt = max(self.frame_stats.max_dt, dt)
    
    def stop(self) -> None:
        """Stop the game loop."""
        self._running = False
        self.state = GameState.QUIT
    
    def pause(self) -> None:
        """Pause the game."""
        if self.state == GameState.RUNNING:
            self.change_state(GameState.PAUSED)
    
    def resume(self) -> None:
        """Resume the game."""
        if self.state == GameState.PAUSED:
            self.change_state(GameState.RUNNING)
    
    def toggle_pause(self) -> None:
        """Toggle pause state."""
        if self.state == GameState.RUNNING:
            self.pause()
        elif self.state == GameState.PAUSED:
            self.resume()
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        if self.system_manager:
            self.system_manager.cleanup()
        
        if self.screen:
            try:
                self.screen.bye()
            except:
                pass
    
    @property
    def entities(self) -> EntityManager:
        """Access the entity manager."""
        if self.entity_manager is None:
            raise RuntimeError("Engine not initialized")
        return self.entity_manager
    
    @property
    def events(self) -> EventBus:
        """Access the event bus."""
        if self.event_bus is None:
            raise RuntimeError("Engine not initialized")
        return self.event_bus
    
    @property
    def systems(self) -> SystemManager:
        """Access the system manager."""
        if self.system_manager is None:
            raise RuntimeError("Engine not initialized")
        return self.system_manager
