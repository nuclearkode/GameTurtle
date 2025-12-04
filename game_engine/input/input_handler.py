"""Input state management and key mapping."""

from dataclasses import dataclass, field
from typing import Set, Dict


@dataclass
class InputState:
    """Current frame input state."""
    move_up: bool = False
    move_down: bool = False
    move_left: bool = False
    move_right: bool = False
    rotate_left: bool = False
    rotate_right: bool = False
    fire: bool = False
    _pressed_keys: Set[str] = field(default_factory=set)
    
    def is_key_pressed(self, key: str) -> bool:
        """Check if a key is currently pressed."""
        return key in self._pressed_keys


class InputHandler:
    """Handles input events and maintains input state."""
    
    # Key mappings
    KEY_MOVE_UP = "w"
    KEY_MOVE_DOWN = "s"
    KEY_MOVE_LEFT = "a"
    KEY_MOVE_RIGHT = "d"
    KEY_ROTATE_LEFT = "q"
    KEY_ROTATE_RIGHT = "e"
    KEY_FIRE = "space"
    
    def __init__(self, screen):
        self.screen = screen
        self.state = InputState()
        self._setup_listeners()
    
    def _setup_listeners(self):
        """Setup turtle key listeners."""
        self.screen.onkeypress(self._on_key_press, self.KEY_MOVE_UP)
        self.screen.onkeypress(self._on_key_press, self.KEY_MOVE_DOWN)
        self.screen.onkeypress(self._on_key_press, self.KEY_MOVE_LEFT)
        self.screen.onkeypress(self._on_key_press, self.KEY_MOVE_RIGHT)
        self.screen.onkeypress(self._on_key_press, self.KEY_ROTATE_LEFT)
        self.screen.onkeypress(self._on_key_press, self.KEY_ROTATE_RIGHT)
        self.screen.onkeypress(self._on_key_press, self.KEY_FIRE)
        
        self.screen.onkeyrelease(self._on_key_release, self.KEY_MOVE_UP)
        self.screen.onkeyrelease(self._on_key_release, self.KEY_MOVE_DOWN)
        self.screen.onkeyrelease(self._on_key_release, self.KEY_MOVE_LEFT)
        self.screen.onkeyrelease(self._on_key_release, self.KEY_MOVE_RIGHT)
        self.screen.onkeyrelease(self._on_key_release, self.KEY_ROTATE_LEFT)
        self.screen.onkeyrelease(self._on_key_release, self.KEY_ROTATE_RIGHT)
        self.screen.onkeyrelease(self._on_key_release, self.KEY_FIRE)
        
        self.screen.listen()
    
    def _on_key_press(self, key: str):
        """Handle key press."""
        self.state._pressed_keys.add(key)
        self._update_state()
    
    def _on_key_release(self, key: str):
        """Handle key release."""
        self.state._pressed_keys.discard(key)
        self._update_state()
    
    def _update_state(self):
        """Update input state based on pressed keys."""
        keys = self.state._pressed_keys
        
        self.state.move_up = self.KEY_MOVE_UP in keys
        self.state.move_down = self.KEY_MOVE_DOWN in keys
        self.state.move_left = self.KEY_MOVE_LEFT in keys
        self.state.move_right = self.KEY_MOVE_RIGHT in keys
        self.state.rotate_left = self.KEY_ROTATE_LEFT in keys
        self.state.rotate_right = self.KEY_ROTATE_RIGHT in keys
        self.state.fire = self.KEY_FIRE in keys
    
    def update(self):
        """Update input state (called each frame)."""
        # Turtle handles key events asynchronously, so we just update state
        self._update_state()
