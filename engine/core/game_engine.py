"""
Game Engine Orchestrator

Main game loop and engine management.
"""

import time
import turtle
from engine.core.entity import EntityManager
from engine.core.system import SystemManager
from engine.utils.input_manager import InputManager


class GameEngine:
    """
    Main game engine orchestrator.
    
    Responsibilities:
    - Initialize turtle screen and game systems
    - Run main game loop with fixed time step
    - Manage frame timing and FPS
    - Handle pause/resume
    - Coordinate system updates
    """
    
    def __init__(self, width: int = 800, height: int = 600, target_fps: int = 60):
        self.width = width
        self.height = height
        self.target_fps = target_fps
        self.target_frame_time = 1.0 / target_fps
        
        # Core managers
        self.entity_manager = EntityManager()
        self.system_manager = SystemManager()
        self.input_manager = InputManager()
        
        # Game state
        self.running = False
        self.paused = False
        
        # Timing
        self.current_time = time.time()
        self.accumulator = 0.0
        self.frame_count = 0
        self.fps = 0.0
        self.fps_update_time = 0.0
        
        # Turtle screen (created in initialize)
        self.screen = None
    
    def initialize(self) -> None:
        """Initialize turtle screen and setup."""
        # Create screen
        self.screen = turtle.Screen()
        self.screen.setup(width=self.width, height=self.height)
        self.screen.title("Robo-Arena")
        self.screen.bgcolor("black")
        self.screen.tracer(0)  # Manual updates for performance
        
        # Setup input
        self.input_manager.setup_turtle_bindings(self.screen)
        
        # Listen for pause/quit
        self.screen.onkeypress(self._toggle_pause, "Escape")
        self.screen.onkeypress(self._quit, "q")
        
        print("Game Engine initialized")
        print(f"Target FPS: {self.target_fps}")
        print(f"Screen size: {self.width}x{self.height}")
    
    def add_system(self, system) -> None:
        """Add a system to the engine."""
        self.system_manager.add_system(system)
    
    def start(self) -> None:
        """Start the game loop."""
        self.running = True
        self.current_time = time.time()
        
        print("Starting game loop...")
        self._game_loop()
    
    def stop(self) -> None:
        """Stop the game loop."""
        self.running = False
        print("Game loop stopped")
    
    def _game_loop(self) -> None:
        """Main game loop with fixed time step."""
        while self.running:
            # Calculate delta time
            new_time = time.time()
            frame_time = new_time - self.current_time
            self.current_time = new_time
            
            # Accumulate time
            self.accumulator += frame_time
            
            # Update FPS counter
            self.frame_count += 1
            self.fps_update_time += frame_time
            if self.fps_update_time >= 1.0:
                self.fps = self.frame_count / self.fps_update_time
                self.frame_count = 0
                self.fps_update_time = 0.0
            
            # Fixed time step updates
            max_steps = 5  # Prevent spiral of death
            steps = 0
            
            while self.accumulator >= self.target_frame_time and steps < max_steps:
                # Update input
                self.input_manager.update()
                
                # Check for pause
                if self.input_manager.is_action_just_pressed(
                    self.input_manager.actions.__class__.PAUSE
                ):
                    self._toggle_pause()
                
                # Update game logic (if not paused)
                if not self.paused:
                    self._update(self.target_frame_time)
                
                self.accumulator -= self.target_frame_time
                steps += 1
            
            # Render (always, even when paused)
            self._render()
            
            # Sleep to cap frame rate
            elapsed = time.time() - self.current_time
            sleep_time = self.target_frame_time - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            # Update turtle screen
            try:
                self.screen.update()
            except turtle.Terminator:
                self.running = False
                break
    
    def _update(self, dt: float) -> None:
        """Update all game systems."""
        # Update all systems
        self.system_manager.update_all(dt)
        
        # Process entity destruction queue
        self.entity_manager.process_destruction_queue()
    
    def _render(self) -> None:
        """Render frame (handled by RenderSystem)."""
        # Rendering is done by RenderSystem in update loop
        pass
    
    def _toggle_pause(self) -> None:
        """Toggle pause state."""
        self.paused = not self.paused
        if self.paused:
            print("Game paused")
        else:
            print("Game resumed")
    
    def _quit(self) -> None:
        """Quit the game."""
        self.stop()
    
    def get_fps(self) -> float:
        """Get current FPS."""
        return self.fps
    
    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self.screen.bye()
        except:
            pass
