"""
AI Brain component - Enemy behavior and decision making.

The AISystem reads this component to determine enemy behavior.
Different behavior types have different logic in the system.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Tuple


class AIBehavior(Enum):
    """Types of AI behavior patterns."""
    NONE = auto()        # No AI (player-controlled or static)
    CHASER = auto()      # Rush directly at target
    TURRET = auto()      # Stationary, rotate and shoot
    SWARM = auto()       # Flocking/boids behavior
    PATROL = auto()      # Move between waypoints
    BOSS = auto()        # Multi-phase boss behavior
    ORBIT = auto()       # Circle around target
    FLEE = auto()        # Run away from target
    WANDER = auto()      # Random movement


class AIState(Enum):
    """Current state in AI state machine."""
    IDLE = auto()
    SEEKING = auto()     # Looking for target
    CHASING = auto()     # Moving toward target
    ATTACKING = auto()   # Attacking target
    FLEEING = auto()     # Running away
    STUNNED = auto()     # Temporarily disabled
    DEAD = auto()        # Dead/dying


@dataclass
class AIBrain:
    """
    AI decision-making component.
    
    Attributes:
        behavior: The type of AI behavior to use
        state: Current state in the behavior state machine
        target_id: Entity ID of current target (usually player)
        
        awareness_range: Distance at which AI becomes aware of target
        attack_range: Distance at which AI can attack
        preferred_range: Distance AI tries to maintain (for orbit/flee)
        
        attack_cooldown: Time between attacks
        state_timer: Generic timer for state transitions
        
    Behavior Details:
        CHASER: Moves directly toward target, attacks when in range
        TURRET: Stationary, rotates to face target, fires when in range
        SWARM: Uses boids rules (cohesion, separation, alignment)
        PATROL: Follows waypoints, chases if player in range
        BOSS: Uses phase-based state machine
        ORBIT: Circles target at preferred_range
    """
    behavior: AIBehavior = AIBehavior.CHASER
    state: AIState = AIState.IDLE
    target_id: Optional[str] = None
    
    # Detection ranges
    awareness_range: float = 400.0
    attack_range: float = 200.0
    preferred_range: float = 150.0
    
    # Combat
    attack_cooldown: float = 1.0
    current_attack_cooldown: float = 0.0
    
    # State timing
    state_timer: float = 0.0
    state_duration: float = 0.0
    
    # Movement modifiers
    speed_multiplier: float = 1.0
    turn_speed: float = 180.0  # degrees per second
    
    # Patrol waypoints (for PATROL behavior)
    waypoints: List[Tuple[float, float]] = field(default_factory=list)
    current_waypoint: int = 0
    waypoint_threshold: float = 20.0
    
    # Swarm/flocking parameters (for SWARM behavior)
    cohesion_weight: float = 1.0
    separation_weight: float = 1.5
    alignment_weight: float = 1.0
    separation_distance: float = 40.0
    neighbor_distance: float = 100.0
    
    # Boss phase (for BOSS behavior)
    boss_phase: int = 0
    max_phase: int = 3
    phase_hp_thresholds: List[float] = field(default_factory=lambda: [0.66, 0.33, 0.0])
    
    # Line of sight
    requires_los: bool = False  # If True, only attack when target visible
    has_los: bool = True
    
    @property
    def can_attack(self) -> bool:
        """Check if AI can attack right now."""
        return (
            self.current_attack_cooldown <= 0 and
            self.state not in (AIState.STUNNED, AIState.DEAD, AIState.FLEEING) and
            (not self.requires_los or self.has_los)
        )
    
    def change_state(self, new_state: AIState, duration: float = 0.0) -> None:
        """Transition to a new AI state."""
        self.state = new_state
        self.state_timer = 0.0
        self.state_duration = duration
    
    def advance_waypoint(self) -> Tuple[float, float]:
        """Move to next waypoint and return its position."""
        if not self.waypoints:
            return (0.0, 0.0)
        
        self.current_waypoint = (self.current_waypoint + 1) % len(self.waypoints)
        return self.waypoints[self.current_waypoint]
    
    def get_current_waypoint(self) -> Optional[Tuple[float, float]]:
        """Get current waypoint position."""
        if not self.waypoints:
            return None
        return self.waypoints[self.current_waypoint]


@dataclass
class BossPhase:
    """
    Configuration for a boss phase.
    Used by AISystem to determine boss behavior per phase.
    """
    phase_number: int = 0
    hp_threshold: float = 1.0  # Phase ends when HP drops below this %
    attack_pattern: str = "basic"  # Pattern name for attack selection
    speed_multiplier: float = 1.0
    damage_multiplier: float = 1.0
    spawn_minions: bool = False
    minion_count: int = 0
    special_ability: str = ""
