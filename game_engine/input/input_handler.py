"""
Input handling - maps turtle key events to game actions.
Separates input from game logic.
"""

from dataclasses import dataclass, field
from typing import Set
import turtle


class InputAction:
    """Input action constants"""
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    ROTATE_LEFT = "rotate_left"
    ROTATE_RIGHT = "rotate_right"
    FIRE = "fire"
    PAUSE = "pause"
    QUIT = "quit"


@dataclass
class InputState:
    """Current input state - which actions are active"""
    active_actions: Set[str] = field(default_factory=set)
    
    def is_active(self, action: str) -> bool:
        """Check if an action is currently active"""
        return action in self.active_actions
    
    def set_active(self, action: str, active: bool) -> None:
        """Set action active state"""
        if active:
            self.active_actions.add(action)
        else:
            self.active_actions.discard(action)
    
    def clear(self) -> None:
        """Clear all active actions"""
        self.active_actions.clear()


class InputHandler:
    """
    Handles keyboard input via turtle.
    Maps keys to actions and updates InputState.
    """
    
    def __init__(self, screen: turtle.Screen, input_state: InputState):
        self.screen = screen
        self.input_state = input_state
        self._setup_key_bindings()
    
    def _setup_key_bindings(self) -> None:
        """Set up key bindings"""
        # Movement
        self.screen.onkeypress(
            lambda: self.input_state.set_active(InputAction.MOVE_UP, True),
            "w"
        )
        self.screen.onkeyrelease(
            lambda: self.input_state.set_active(InputAction.MOVE_UP, False),
            "w"
        )
        
        self.screen.onkeypress(
            lambda: self.input_state.set_active(InputAction.MOVE_DOWN, True),
            "s"
        )
        self.screen.onkeyrelease(
            lambda: self.input_state.set_active(InputAction.MOVE_DOWN, False),
            "s"
        )
        
        self.screen.onkeypress(
            lambda: self.input_state.set_active(InputAction.MOVE_LEFT, True),
            "a"
        )
        self.screen.onkeyrelease(
            lambda: self.input_state.set_active(InputAction.MOVE_LEFT, False),
            "a"
        )
        
        self.screen.onkeypress(
            lambda: self.input_state.set_active(InputAction.MOVE_RIGHT, True),
            "d"
        )
        self.screen.onkeyrelease(
            lambda: self.input_state.set_active(InputAction.MOVE_RIGHT, False),
            "d"
        )
        
        # Rotation
        self.screen.onkeypress(
            lambda: self.input_state.set_active(InputAction.ROTATE_LEFT, True),
            "q"
        )
        self.screen.onkeyrelease(
            lambda: self.input_state.set_active(InputAction.ROTATE_LEFT, False),
            "q"
        )
        
        self.screen.onkeypress(
            lambda: self.input_state.set_active(InputAction.ROTATE_RIGHT, True),
            "e"
        )
        self.screen.onkeyrelease(
            lambda: self.input_state.set_active(InputAction.ROTATE_RIGHT, False),
            "e"
        )
        
        # Fire
        self.screen.onkeypress(
            lambda: self.input_state.set_active(InputAction.FIRE, True),
            "space"
        )
        self.screen.onkeyrelease(
            lambda: self.input_state.set_active(InputAction.FIRE, False),
            "space"
        )
        
        # Pause/Quit
        self.screen.onkeypress(
            lambda: self.input_state.set_active(InputAction.PAUSE, True),
            "p"
        )
        self.screen.onkeypress(
            lambda: self.input_state.set_active(InputAction.QUIT, True),
            "Escape"
        )
        
        self.screen.listen()
