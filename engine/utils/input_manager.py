"""
Input management system.

Handles keyboard input and provides a clean interface for querying input state.
Decouples turtle's event system from game logic.
"""

from typing import Set, Dict, Callable
from enum import Enum


class InputAction(Enum):
    """Enumeration of game actions."""
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    ROTATE_LEFT = "rotate_left"
    ROTATE_RIGHT = "rotate_right"
    FIRE = "fire"
    PAUSE = "pause"
    UPGRADE_1 = "upgrade_1"
    UPGRADE_2 = "upgrade_2"
    UPGRADE_3 = "upgrade_3"


class InputManager:
    """
    Manages keyboard input state.
    
    Maps keys to actions and tracks which actions are currently active.
    """
    
    def __init__(self):
        # Current state of each action
        self.actions: Dict[InputAction, bool] = {action: False for action in InputAction}
        
        # Previous frame state (for detecting presses/releases)
        self.prev_actions: Dict[InputAction, bool] = {action: False for action in InputAction}
        
        # Key bindings (key -> action)
        self.key_bindings: Dict[str, InputAction] = {
            'w': InputAction.MOVE_UP,
            'Up': InputAction.MOVE_UP,
            's': InputAction.MOVE_DOWN,
            'Down': InputAction.MOVE_DOWN,
            'a': InputAction.MOVE_LEFT,
            'Left': InputAction.MOVE_LEFT,
            'd': InputAction.MOVE_RIGHT,
            'Right': InputAction.MOVE_RIGHT,
            'q': InputAction.ROTATE_LEFT,
            'e': InputAction.ROTATE_RIGHT,
            'space': InputAction.FIRE,
            'Escape': InputAction.PAUSE,
            '1': InputAction.UPGRADE_1,
            '2': InputAction.UPGRADE_2,
            '3': InputAction.UPGRADE_3,
        }
        
        # Reverse mapping (action -> keys)
        self.action_to_keys: Dict[InputAction, Set[str]] = {}
        for key, action in self.key_bindings.items():
            if action not in self.action_to_keys:
                self.action_to_keys[action] = set()
            self.action_to_keys[action].add(key)
    
    def setup_turtle_bindings(self, screen) -> None:
        """
        Set up turtle keyboard bindings.
        Call this after creating the turtle screen.
        """
        screen.listen()
        
        # Bind all keys
        for key in self.key_bindings.keys():
            screen.onkeypress(lambda k=key: self._on_key_press(k), key)
            screen.onkeyrelease(lambda k=key: self._on_key_release(k), key)
    
    def _on_key_press(self, key: str) -> None:
        """Handle key press event."""
        if key in self.key_bindings:
            action = self.key_bindings[key]
            self.actions[action] = True
    
    def _on_key_release(self, key: str) -> None:
        """Handle key release event."""
        if key in self.key_bindings:
            action = self.key_bindings[key]
            self.actions[action] = False
    
    def update(self) -> None:
        """Update input state. Call once per frame before processing input."""
        self.prev_actions = self.actions.copy()
    
    def is_action_active(self, action: InputAction) -> bool:
        """Check if an action is currently active (key held)."""
        return self.actions.get(action, False)
    
    def is_action_just_pressed(self, action: InputAction) -> bool:
        """Check if an action was just pressed this frame."""
        return self.actions.get(action, False) and not self.prev_actions.get(action, False)
    
    def is_action_just_released(self, action: InputAction) -> bool:
        """Check if an action was just released this frame."""
        return not self.actions.get(action, False) and self.prev_actions.get(action, False)
    
    def get_movement_vector(self) -> tuple:
        """
        Get normalized movement input as (x, y).
        Returns values in range [-1, 1].
        """
        x = 0.0
        y = 0.0
        
        if self.is_action_active(InputAction.MOVE_RIGHT):
            x += 1.0
        if self.is_action_active(InputAction.MOVE_LEFT):
            x -= 1.0
        if self.is_action_active(InputAction.MOVE_UP):
            y += 1.0
        if self.is_action_active(InputAction.MOVE_DOWN):
            y -= 1.0
        
        # Normalize diagonal movement
        if x != 0 and y != 0:
            length = (x * x + y * y) ** 0.5
            x /= length
            y /= length
        
        return x, y
    
    def get_rotation_input(self) -> float:
        """
        Get rotation input.
        Returns -1 for left, +1 for right, 0 for none.
        """
        rotation = 0.0
        if self.is_action_active(InputAction.ROTATE_LEFT):
            rotation -= 1.0
        if self.is_action_active(InputAction.ROTATE_RIGHT):
            rotation += 1.0
        return rotation
    
    def reset(self) -> None:
        """Reset all input state."""
        for action in self.actions:
            self.actions[action] = False
            self.prev_actions[action] = False
