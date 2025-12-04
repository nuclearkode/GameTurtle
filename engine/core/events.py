"""
Event system for decoupled communication between systems.

Design Philosophy:
- Systems should not directly depend on each other
- Events allow one-to-many communication
- Events can be immediate or queued for later processing
- Type-safe event handling via dataclasses
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Callable, Type, Any, Optional
from collections import defaultdict


@dataclass
class Event:
    """
    Base class for all events.
    
    Subclass this and add your event data as fields.
    Use @dataclass for automatic __init__ and other goodies.
    """
    pass


# Common built-in events

@dataclass
class EntityCreatedEvent(Event):
    """Fired when an entity is created."""
    entity_id: str


@dataclass
class EntityDestroyedEvent(Event):
    """Fired when an entity is marked for destruction."""
    entity_id: str


@dataclass 
class CollisionEvent(Event):
    """Fired when two entities collide."""
    entity_a_id: str
    entity_b_id: str
    normal_x: float = 0.0
    normal_y: float = 0.0
    penetration: float = 0.0


@dataclass
class DamageEvent(Event):
    """Fired when damage should be applied."""
    target_id: str
    source_id: Optional[str]
    amount: float
    damage_type: str = "normal"


@dataclass
class DeathEvent(Event):
    """Fired when an entity dies."""
    entity_id: str
    killer_id: Optional[str] = None


@dataclass
class WaveStartEvent(Event):
    """Fired when a new wave starts."""
    wave_number: int
    enemy_count: int


@dataclass
class WaveCompleteEvent(Event):
    """Fired when a wave is completed."""
    wave_number: int


@dataclass
class ProjectileFiredEvent(Event):
    """Fired when a projectile is created."""
    projectile_id: str
    owner_id: str
    x: float
    y: float
    angle: float


@dataclass
class UpgradeSelectedEvent(Event):
    """Fired when player selects an upgrade."""
    upgrade_type: str
    upgrade_value: float


@dataclass
class GameStateEvent(Event):
    """Fired for game state changes."""
    state: str  # "playing", "paused", "wave_complete", "game_over", "victory"


# Event handler type
EventHandler = Callable[[Event], None]


class EventBus:
    """
    Central event dispatcher for decoupled system communication.
    
    Features:
    - Subscribe to event types with callbacks
    - Fire events immediately or queue for later
    - One-shot subscriptions (auto-unsubscribe after first call)
    - Priority-based handler ordering
    
    Usage:
        bus = EventBus()
        
        # Subscribe
        bus.subscribe(DamageEvent, lambda e: apply_damage(e.target_id, e.amount))
        
        # Fire
        bus.emit(DamageEvent(target_id="enemy1", source_id="player", amount=10))
    """
    
    def __init__(self):
        # event_type -> list of (priority, handler, one_shot)
        self._handlers: Dict[Type[Event], List[tuple]] = defaultdict(list)
        self._queued_events: List[Event] = []
        self._handlers_dirty: Dict[Type[Event], bool] = {}
    
    def subscribe(
        self,
        event_type: Type[Event],
        handler: EventHandler,
        priority: int = 0,
        one_shot: bool = False
    ) -> Callable[[], None]:
        """
        Subscribe to an event type.
        
        Args:
            event_type: The Event subclass to subscribe to
            handler: Callback function(event) -> None
            priority: Lower values are called first
            one_shot: If True, auto-unsubscribe after first event
            
        Returns:
            Unsubscribe function - call it to remove the handler
        """
        entry = (priority, handler, one_shot)
        self._handlers[event_type].append(entry)
        self._handlers_dirty[event_type] = True
        
        def unsubscribe():
            handlers = self._handlers.get(event_type, [])
            if entry in handlers:
                handlers.remove(entry)
        
        return unsubscribe
    
    def emit(self, event: Event) -> None:
        """
        Fire an event immediately.
        
        All subscribed handlers are called synchronously in priority order.
        Exceptions in handlers are caught and logged to prevent cascade failures.
        
        Args:
            event: The event instance to emit
        """
        if event is None:
            return
            
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        
        if not handlers:
            return
        
        # Sort by priority if dirty
        if self._handlers_dirty.get(event_type, False):
            handlers.sort(key=lambda x: x[0])
            self._handlers_dirty[event_type] = False
        
        # Call handlers, collecting one-shots for removal
        to_remove = []
        for priority, handler, one_shot in handlers:
            try:
                handler(event)
            except Exception as e:
                # Log error but continue processing other handlers
                import sys
                print(f"[EventBus] Error in handler for {event_type.__name__}: {e}", file=sys.stderr)
            if one_shot:
                to_remove.append((priority, handler, one_shot))
        
        # Remove one-shot handlers
        for entry in to_remove:
            if entry in handlers:
                handlers.remove(entry)
    
    def emit_deferred(self, event: Event) -> None:
        """
        Queue an event for later processing.
        
        The event will be fired when flush_events() is called.
        Useful for avoiding issues during iteration.
        
        Args:
            event: The event instance to queue
        """
        self._queued_events.append(event)
    
    def flush_events(self) -> int:
        """
        Process all queued events.
        
        Returns:
            Number of events processed
        """
        count = len(self._queued_events)
        events = self._queued_events.copy()
        self._queued_events.clear()
        
        for event in events:
            self.emit(event)
        
        return count
    
    def clear_handlers(self, event_type: Optional[Type[Event]] = None) -> None:
        """
        Clear event handlers.
        
        Args:
            event_type: Specific type to clear, or None for all
        """
        if event_type:
            self._handlers.pop(event_type, None)
        else:
            self._handlers.clear()
    
    def clear_queue(self) -> None:
        """Clear all queued events without processing them."""
        self._queued_events.clear()
    
    def has_subscribers(self, event_type: Type[Event]) -> bool:
        """Check if any handlers are subscribed to an event type."""
        return bool(self._handlers.get(event_type))
