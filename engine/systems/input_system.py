"""
Input System - Keyboard input handling and action mapping.

Translates raw keyboard events into game actions.
Keeps input handling separate from game logic.

Updated Controls:
- WASD: Omnidirectional movement (move in all directions)
- Arrow keys: Aim direction (replacement for mouse)
- Mouse: Aim direction (player faces cursor)
- Space: Fire
- R: Reload
- Escape: Pause
"""

from __future__ import annotations
import turtle
import math
from typing import TYPE_CHECKING, Dict, Set, Callable, Optional
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
    # Omnidirectional movement (WASD)
    MOVE_UP = auto()       # W - Move up
    MOVE_DOWN = auto()     # S - Move down
    MOVE_LEFT = auto()     # A - Move left
    MOVE_RIGHT = auto()    # D - Move right
    
    # Aiming (Arrow keys as mouse replacement)
    AIM_UP = auto()
    AIM_DOWN = auto()
    AIM_LEFT = auto()
    AIM_RIGHT = auto()
    
    # Legacy rotation (still available)
    ROTATE_LEFT = auto()
    ROTATE_RIGHT = auto()
    
    # Combat
    FIRE = auto()
    RELOAD = auto()
    DASH = auto()  # For double jump/dash upgrade
    
    # Menu
    PAUSE = auto()
    QUIT = auto()
    CONFIRM = auto()
    CANCEL = auto()
    
    # Alternative movement (strafing)
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
        aim_angle: Current aim angle (from arrow keys or mouse)
        using_mouse_aim: Whether mouse is being used for aiming
    """
    actions_held: Set[GameAction] = field(default_factory=set)
    actions_pressed: Set[GameAction] = field(default_factory=set)
    actions_released: Set[GameAction] = field(default_factory=set)
    mouse_x: float = 0.0
    mouse_y: float = 0.0
    mouse_clicked: bool = False
    aim_angle: float = 90.0  # Default facing up
    using_mouse_aim: bool = False
    arrow_aim_x: float = 0.0  # Arrow key aim direction
    arrow_aim_y: float = 0.0
    
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
    Handles keyboard and mouse input, translates to game actions.
    
    Features:
    - WASD for omnidirectional movement (move in any direction)
    - Mouse for aiming (player faces cursor position)
    - Arrow keys as mouse replacement for aiming
    - Key-to-action mapping (configurable)
    - Held, pressed, and released state tracking
    - Applies input to player entity
    
    Control Scheme:
    - W/A/S/D: Move up/left/down/right (omnidirectional)
    - Arrow keys: Aim direction (alternative to mouse)
    - Mouse: Aim direction (player faces cursor)
    - Space: Fire
    - R: Reload
    - Shift: Dash (if upgrade available)
    - Escape: Pause
    - Q: Quit
    """
    
    # Default key bindings - WASD for omnidirectional movement
    DEFAULT_BINDINGS = {
        # WASD for movement (omnidirectional)
        "w": GameAction.MOVE_UP,
        "s": GameAction.MOVE_DOWN,
        "a": GameAction.MOVE_LEFT,
        "d": GameAction.MOVE_RIGHT,
        
        # Arrow keys for aiming (mouse replacement)
        "Up": GameAction.AIM_UP,
        "Down": GameAction.AIM_DOWN,
        "Left": GameAction.AIM_LEFT,
        "Right": GameAction.AIM_RIGHT,
        
        # Actions
        "space": GameAction.FIRE,
        "r": GameAction.RELOAD,
        "Shift_L": GameAction.DASH,
        "Shift_R": GameAction.DASH,
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
        
        # Mouse tracking
        self._mouse_enabled = True
        self._last_mouse_x = 0.0
        self._last_mouse_y = 0.0
        self._mouse_button_down = False
        
        # Arrow key aim smoothing
        self._arrow_aim_speed = 180.0  # Degrees per second
    
    def initialize(self) -> None:
        """Set up input bindings."""
        # Apply default bindings
        for key, action in self.DEFAULT_BINDINGS.items():
            self.bind_key(key, action)
        
        # Set up keyboard listeners
        self.screen.listen()
        
        # Set up mouse tracking
        self._setup_mouse_tracking()
    
    def _setup_mouse_tracking(self) -> None:
        """Set up mouse motion and click tracking."""
        try:
            # Track mouse motion
            self.screen.cv.bind('<Motion>', self._on_mouse_motion)
            
            # Track mouse clicks using canvas binding (more reliable, doesn't conflict with menu)
            self.screen.cv.bind('<Button-1>', self._on_mouse_click_event)
            self.screen.cv.bind('<ButtonRelease-1>', self._on_mouse_release_event)
        except Exception:
            # Mouse tracking may not be available in all environments
            self._mouse_enabled = False
    
    def _on_mouse_motion(self, event) -> None:
        """Handle mouse motion event."""
        try:
            # Get canvas position and convert to turtle coordinates
            canvas = self.screen.cv
            x = event.x - canvas.winfo_width() / 2
            y = canvas.winfo_height() / 2 - event.y
            
            # Check if mouse has moved significantly BEFORE updating last position
            if abs(x - self._last_mouse_x) > 3 or abs(y - self._last_mouse_y) > 3:
                self.state.using_mouse_aim = True
            
            # Update state
            self.state.mouse_x = x
            self.state.mouse_y = y
            self._last_mouse_x = x
            self._last_mouse_y = y
        except Exception:
            pass
    
    def _on_mouse_click(self, x: float, y: float) -> None:
        """Handle mouse click event (legacy turtle handler)."""
        self.state.mouse_clicked = True
        self.state.mouse_x = x
        self.state.mouse_y = y
    
    def _on_mouse_click_event(self, event) -> None:
        """Handle mouse button press event from canvas."""
        try:
            canvas = self.screen.cv
            x = event.x - canvas.winfo_width() / 2
            y = canvas.winfo_height() / 2 - event.y
            
            self.state.mouse_clicked = True
            self.state.mouse_x = x
            self.state.mouse_y = y
            self._mouse_button_down = True
        except Exception:
            pass
    
    def _on_mouse_release_event(self, event) -> None:
        """Handle mouse button release event from canvas."""
        self._mouse_button_down = False
    
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
                
                # If arrow key is pressed, switch to arrow aiming
                if action in (GameAction.AIM_UP, GameAction.AIM_DOWN, 
                              GameAction.AIM_LEFT, GameAction.AIM_RIGHT):
                    self.state.using_mouse_aim = False
                
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
        
        # Get movement speed
        move_speed = physics.acceleration if physics else 500.0
        
        # === OMNIDIRECTIONAL MOVEMENT (WASD) ===
        # Movement is independent of facing direction
        accel_x = 0.0
        accel_y = 0.0
        
        if self.state.is_action_held(GameAction.MOVE_UP):
            accel_y += move_speed
        if self.state.is_action_held(GameAction.MOVE_DOWN):
            accel_y -= move_speed
        if self.state.is_action_held(GameAction.MOVE_LEFT):
            accel_x -= move_speed
        if self.state.is_action_held(GameAction.MOVE_RIGHT):
            accel_x += move_speed
        
        # Normalize diagonal movement
        if accel_x != 0 and accel_y != 0:
            magnitude = math.sqrt(accel_x**2 + accel_y**2)
            accel_x = (accel_x / magnitude) * move_speed
            accel_y = (accel_y / magnitude) * move_speed
        
        # Apply movement
        if physics:
            physics.accel_x = accel_x
            physics.accel_y = accel_y
        else:
            velocity.vx = accel_x
            velocity.vy = accel_y
        
        # === AIMING (Mouse or Arrow Keys) ===
        # Check if arrow keys are being used for aiming
        aim_x = 0.0
        aim_y = 0.0
        
        if self.state.is_action_held(GameAction.AIM_UP):
            aim_y += 1.0
        if self.state.is_action_held(GameAction.AIM_DOWN):
            aim_y -= 1.0
        if self.state.is_action_held(GameAction.AIM_LEFT):
            aim_x -= 1.0
        if self.state.is_action_held(GameAction.AIM_RIGHT):
            aim_x += 1.0
        
        # If arrow keys are held, use arrow key aiming
        if aim_x != 0 or aim_y != 0:
            target_angle = math.degrees(math.atan2(aim_y, aim_x))
            
            # Smooth rotation towards target
            current = transform.angle
            diff = self._angle_difference(current, target_angle)
            
            max_rotation = self._arrow_aim_speed * dt
            if abs(diff) <= max_rotation:
                transform.angle = target_angle
            else:
                transform.angle += max_rotation if diff > 0 else -max_rotation
            
            # Keep angle in 0-360 range
            transform.angle = transform.angle % 360
        elif self._mouse_enabled:
            # Default: Always aim at mouse cursor
            target_angle = self._calculate_mouse_aim_angle(transform)
            if target_angle is not None:
                transform.angle = target_angle
        
        # === LEGACY ROTATION (if needed) ===
        turn_speed = physics.angular_acceleration if physics else 360.0
        
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
        
        # === COMBAT ===
        if weapon:
            # Fire on space key held OR mouse button held
            weapon.is_firing = (
                self.state.is_action_held(GameAction.FIRE) or 
                self._mouse_button_down
            )
            
            if self.state.is_action_pressed(GameAction.RELOAD):
                weapon.start_reload()
        
        # Clear per-frame state at end
        self.state.clear_frame_state()
    
    def _calculate_mouse_aim_angle(self, transform: Transform) -> Optional[float]:
        """Calculate the angle to face the mouse cursor."""
        try:
            dx = self.state.mouse_x - transform.x
            dy = self.state.mouse_y - transform.y
            
            # Only skip if mouse is very close to player to avoid jitter
            distance_sq = dx * dx + dy * dy
            if distance_sq > 100:  # More than 10 pixels away
                return math.degrees(math.atan2(dy, dx))
        except Exception:
            pass
        return None
    
    def _angle_difference(self, current: float, target: float) -> float:
        """Calculate the shortest angle difference between two angles."""
        diff = (target - current + 180) % 360 - 180
        return diff
    
    def enable_mouse(self, enabled: bool = True) -> None:
        """Enable or disable mouse input."""
        self._mouse_enabled = enabled
    
    def rebind_keys(self) -> None:
        """Re-register all key bindings. Call after menu hides to restore bindings."""
        for key, action in self._key_to_action.items():
            try:
                self.screen.onkeypress(lambda k=key: self._on_key_press(k), key)
                self.screen.onkeyrelease(lambda k=key: self._on_key_release(k), key)
            except Exception:
                pass
        self.screen.listen()
    
    def cleanup(self) -> None:
        """Unbind all keys."""
        for key in list(self._key_to_action.keys()):
            try:
                self.screen.onkeypress(None, key)
                self.screen.onkeyrelease(None, key)
            except:
                pass
        
        # Clean up mouse bindings
        try:
            self.screen.cv.unbind('<Motion>')
            self.screen.cv.unbind('<Button-1>')
            self.screen.cv.unbind('<ButtonRelease-1>')
        except:
            pass
