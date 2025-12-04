"""
Input System - Keyboard input handling and action mapping.

Translates raw keyboard events into game actions.
Keeps input handling separate from game logic.
"""

from __future__ import annotations
import turtle
from typing import TYPE_CHECKING, Dict, Set, Callable
from enum import Enum, auto
from dataclasses import dataclass, field

from ..core.system import GameSystem, SystemPriority
from ..components.transform import Transform
from ..components.physics import Physics, Velocity
from ..components.weapon import Weapon
from ..components.tags import PlayerTag

if TYPE_CHECKING:
    from ..core.entity import Entity


class GameAction(Enum):
    """High-level game actions."""
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    ROTATE_LEFT = auto()
    ROTATE_RIGHT = auto()
    FIRE = auto()
    RELOAD = auto()
    PAUSE = auto()
    QUIT = auto()
    CONFIRM = auto()
    CANCEL = auto()
    
    # Alternative movement (WASD for strafe-based movement)
    STRAFE_LEFT = auto()
    STRAFE_RIGHT = auto()


@dataclass
class InputState:
    """
    Current state of all inputs.
    
    Attributes:
        actions_held: Set of actions currently being held
        actions_pressed: Set of actions pressed this frame
        actions_released: Set of actions released this frame
        mouse_x: Mouse X position (if using mouse)
        mouse_y: Mouse Y position (if using mouse)
        mouse_clicked: Whether mouse was clicked this frame
    """
    actions_held: Set[GameAction] = field(default_factory=set)
    actions_pressed: Set[GameAction] = field(default_factory=set)
    actions_released: Set[GameAction] = field(default_factory=set)
    mouse_x: float = 0.0
    mouse_y: float = 0.0
    mouse_clicked: bool = False
    
    def is_action_held(self, action: GameAction) -> bool:
        """Check if an action is currently being held."""
        return action in self.actions_held
    
    def is_action_pressed(self, action: GameAction) -> bool:
        """Check if an action was pressed this frame."""
        return action in self.actions_pressed
    
    def is_action_released(self, action: GameAction) -> bool:
        """Check if an action was released this frame."""
        return action in self.actions_released
    
    def clear_frame_state(self) -> None:
        """Clear per-frame state (pressed/released)."""
        self.actions_pressed.clear()
        self.actions_released.clear()
        self.mouse_clicked = False


class InputSystem(GameSystem):
    """
    Handles keyboard input and translates to game actions.
    
    Features:
    - Key-to-action mapping (configurable)
    - Held, pressed, and released state tracking
    - Applies input to player entity
    - Support for multiple control schemes
    
    Default Controls:
    - Arrow keys: Move/Rotate
    - WASD: Move/Rotate
    - Space: Fire
    - R: Reload
    - Escape: Pause
    """
    
    # Default key bindings
    DEFAULT_BINDINGS = {
        # Arrow keys
        "Up": GameAction.MOVE_UP,
        "Down": GameAction.MOVE_DOWN,
        "Left": GameAction.ROTATE_LEFT,
        "Right": GameAction.ROTATE_RIGHT,
        
        # WASD
        "w": GameAction.MOVE_UP,
        "s": GameAction.MOVE_DOWN,
        "a": GameAction.ROTATE_LEFT,
        "d": GameAction.ROTATE_RIGHT,
        
        # Alternative: WASD for strafing
        # "a": GameAction.STRAFE_LEFT,
        # "d": GameAction.STRAFE_RIGHT,
        
        # Actions
        "space": GameAction.FIRE,
        "r": GameAction.RELOAD,
        "Escape": GameAction.PAUSE,
        "Return": GameAction.CONFIRM,
        "q": GameAction.QUIT,
    }
    
    def __init__(self, screen: turtle.Screen):
        super().__init__(priority=SystemPriority.INPUT)
        self.screen = screen
        self.state = InputState()
        
        # Key bindings
        self._key_to_action: Dict[str, GameAction] = {}
        self._action_to_keys: Dict[GameAction, Set[str]] = {}
        
        # Callbacks for special actions
        self._action_callbacks: Dict[GameAction, Callable[[], None]] = {}
        
        # Track raw key states
        self._keys_down: Set[str] = set()
    
    def initialize(self) -> None:
        """Set up input bindings."""
        # Apply default bindings
        for key, action in self.DEFAULT_BINDINGS.items():
            self.bind_key(key, action)
        
        # Set up keyboard listeners
        self.screen.listen()
    
    def bind_key(self, key: str, action: GameAction) -> None:
        """Bind a key to an action."""
        self._key_to_action[key] = action
        
        if action not in self._action_to_keys:
            self._action_to_keys[action] = set()
        self._action_to_keys[action].add(key)
        
        # Register with turtle
        self.screen.onkeypress(lambda k=key: self._on_key_press(k), key)
        self.screen.onkeyrelease(lambda k=key: self._on_key_release(k), key)
    
    def unbind_key(self, key: str) -> None:
        """Unbind a key."""
        if key in self._key_to_action:
            action = self._key_to_action[key]
            del self._key_to_action[key]
            if action in self._action_to_keys:
                self._action_to_keys[action].discard(key)
            
            self.screen.onkeypress(None, key)
            self.screen.onkeyrelease(None, key)
    
    def set_action_callback(
        self,
        action: GameAction,
        callback: Callable[[], None]
    ) -> None:
        """Set a callback for when an action is pressed."""
        self._action_callbacks[action] = callback
    
    def _on_key_press(self, key: str) -> None:
        """Handle key press event."""
        if key not in self._keys_down:
            self._keys_down.add(key)
            
            action = self._key_to_action.get(key)
            if action:
                self.state.actions_held.add(action)
                self.state.actions_pressed.add(action)
                
                # Call action callback if registered
                if action in self._action_callbacks:
                    self._action_callbacks[action]()
    
    def _on_key_release(self, key: str) -> None:
        """Handle key release event."""
        self._keys_down.discard(key)
        
        action = self._key_to_action.get(key)
        if action:
            # Only remove from held if no other keys for this action are down
            other_keys = self._action_to_keys.get(action, set())
            if not any(k in self._keys_down for k in other_keys):
                self.state.actions_held.discard(action)
            self.state.actions_released.add(action)
    
    def update(self, dt: float) -> None:
        """Apply input to player entity."""
        # Find player entity
        player = self.entities.get_named("player")
        if not player:
            # Try finding by tag
            for entity in self.entities.get_entities_with(PlayerTag):
                player = entity
                break
        
        if not player:
            self.state.clear_frame_state()
            return
        
        # Get player components
        transform = self.entities.get_component(player, Transform)
        velocity = self.entities.get_component(player, Velocity)
        physics = self.entities.get_component(player, Physics)
        weapon = self.entities.get_component(player, Weapon)
        
        if not transform or not velocity:
            self.state.clear_frame_state()
            return
        
        # Movement
        move_speed = physics.acceleration if physics else 500.0
        turn_speed = physics.angular_acceleration if physics else 360.0
        
        # Forward/backward movement
        if self.state.is_action_held(GameAction.MOVE_UP):
            fx, fy = transform.forward_vector()
            if physics:
                physics.accel_x = fx * move_speed
                physics.accel_y = fy * move_speed
            else:
                velocity.vx = fx * move_speed
                velocity.vy = fy * move_speed
        elif self.state.is_action_held(GameAction.MOVE_DOWN):
            fx, fy = transform.forward_vector()
            if physics:
                physics.accel_x = -fx * move_speed * 0.5  # Slower backward
                physics.accel_y = -fy * move_speed * 0.5
            else:
                velocity.vx = -fx * move_speed * 0.5
                velocity.vy = -fy * move_speed * 0.5
        else:
            if physics:
                physics.accel_x = 0
                physics.accel_y = 0
        
        # Rotation
        if self.state.is_action_held(GameAction.ROTATE_LEFT):
            if physics:
                physics.angular_accel = turn_speed
            else:
                velocity.angular = turn_speed
        elif self.state.is_action_held(GameAction.ROTATE_RIGHT):
            if physics:
                physics.angular_accel = -turn_speed
            else:
                velocity.angular = -turn_speed
        else:
            if physics:
                physics.angular_accel = 0
            velocity.angular = 0
        
        # Strafing (alternative movement)
        if self.state.is_action_held(GameAction.STRAFE_LEFT):
            rx, ry = transform.right_vector()
            if physics:
                physics.accel_x -= rx * move_speed * 0.7
                physics.accel_y -= ry * move_speed * 0.7
        if self.state.is_action_held(GameAction.STRAFE_RIGHT):
            rx, ry = transform.right_vector()
            if physics:
                physics.accel_x += rx * move_speed * 0.7
                physics.accel_y += ry * move_speed * 0.7
        
        # Firing
        if weapon:
            weapon.is_firing = self.state.is_action_held(GameAction.FIRE)
            
            if self.state.is_action_pressed(GameAction.RELOAD):
                weapon.start_reload()
        
        # Clear per-frame state at end
        self.state.clear_frame_state()
    
    def cleanup(self) -> None:
        """Unbind all keys."""
        for key in list(self._key_to_action.keys()):
            try:
                self.screen.onkeypress(None, key)
                self.screen.onkeyrelease(None, key)
            except:
                pass
