#!/usr/bin/env python3
"""
Engine Test Suite

Run this to verify the engine components work correctly.
Does not require a display (no turtle/tkinter).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.core import Entity, EntityManager, EventBus, SystemManager
from engine.components import (
    Transform, Velocity, Physics, Health, Shield,
    Weapon, WeaponType, Projectile, AIBrain, AIBehavior,
    Collider, ColliderType, CollisionMask,
    Renderable, RenderShape, StatusEffects, StatusEffect
)
from engine.systems import (
    PhysicsSystem, CollisionSystem, AISystem,
    WeaponSystem, HealthSystem, WaveSystem,
    StatusEffectSystem, PathfindingSystem
)
from engine.core.events import DamageEvent, DeathEvent, CollisionEvent


def test_entity_manager():
    """Test EntityManager functionality."""
    print("Testing EntityManager...")
    
    em = EntityManager()
    
    # Create entities
    e1 = em.create_entity(name="test1")
    e2 = em.create_entity()
    assert em.entity_count == 2
    
    # Add components
    em.add_component(e1, Transform(x=100, y=50))
    em.add_component(e1, Velocity(vx=10, vy=5))
    em.add_component(e2, Transform(x=-100, y=0))
    
    # Get components
    t1 = em.get_component(e1, Transform)
    assert t1.x == 100 and t1.y == 50
    
    # Query by component
    entities_with_transform = list(em.get_entities_with(Transform))
    assert len(entities_with_transform) == 2
    
    entities_with_velocity = list(em.get_entities_with(Velocity))
    assert len(entities_with_velocity) == 1
    
    # Named lookup
    assert em.get_named("test1") == e1
    
    # Tags
    em.add_tag(e1, "player")
    assert em.has_tag(e1, "player")
    assert list(em.get_entities_with_tag("player")) == [e1]
    
    # Destroy
    em.destroy_entity(e2)
    assert em.entity_count == 2  # Still there (deferred)
    em.flush_destroyed()
    assert em.entity_count == 1
    
    print("  ✓ EntityManager tests passed")


def test_event_bus():
    """Test EventBus functionality."""
    print("Testing EventBus...")
    
    bus = EventBus()
    received = []
    
    def on_damage(event):
        received.append(("damage", event.amount))
    
    def on_death(event):
        received.append(("death", event.entity_id))
    
    bus.subscribe(DamageEvent, on_damage)
    bus.subscribe(DeathEvent, on_death)
    
    bus.emit(DamageEvent(target_id="e1", source_id="e2", amount=25))
    bus.emit(DeathEvent(entity_id="e1"))
    
    assert len(received) == 2
    assert received[0] == ("damage", 25)
    assert received[1] == ("death", "e1")
    
    # Test deferred events
    bus.emit_deferred(DamageEvent(target_id="e2", source_id="e1", amount=10))
    assert len(received) == 2  # Not processed yet
    bus.flush_events()
    assert len(received) == 3
    
    print("  ✓ EventBus tests passed")


def test_components():
    """Test component functionality."""
    print("Testing Components...")
    
    # Transform
    t = Transform(x=0, y=0, angle=0)
    t.look_at(100, 100)
    assert abs(t.angle - 45) < 0.01
    assert abs(t.distance_to(100, 100) - 141.42) < 0.1
    
    # Health
    h = Health(hp=100, max_hp=100)
    assert h.health_percent == 1.0
    h.take_damage(30)
    assert h.hp == 70
    h.heal(50)
    assert h.hp == 100  # Clamped to max
    
    # Shield
    s = Shield(hp=50, max_hp=50)
    overflow = s.absorb_damage(30)
    assert s.hp == 20
    assert overflow == 0
    
    overflow = s.absorb_damage(50)
    assert s.hp == 0
    assert overflow == 30
    
    # Velocity
    v = Velocity(vx=3, vy=4)
    assert v.speed == 5.0
    
    # StatusEffects
    status = StatusEffects()
    status.apply_effect(StatusEffect.SLOW, duration=5.0, magnitude=0.5)
    assert status.has_effect(StatusEffect.SLOW)
    assert status.speed_modifier == 0.5
    
    print("  ✓ Component tests passed")


def test_physics_system():
    """Test PhysicsSystem."""
    print("Testing PhysicsSystem...")
    
    em = EntityManager()
    bus = EventBus()
    sm = SystemManager(em, bus)
    sm.add_system(PhysicsSystem(800, 600))
    
    entity = em.create_entity()
    em.add_component(entity, Transform(x=0, y=0))
    em.add_component(entity, Velocity(vx=100, vy=0))
    
    transform = em.get_component(entity, Transform)
    initial_x = transform.x
    
    # Simulate
    for _ in range(60):  # 1 second at 60 FPS
        sm.update(1/60)
    
    assert transform.x > initial_x
    assert abs(transform.x - 100) < 5  # Should be around 100
    
    sm.cleanup()
    print("  ✓ PhysicsSystem tests passed")


def test_collision_system():
    """Test CollisionSystem."""
    print("Testing CollisionSystem...")
    
    em = EntityManager()
    bus = EventBus()
    sm = SystemManager(em, bus)
    sm.add_system(CollisionSystem(800, 600))
    
    # Create two colliding entities
    e1 = em.create_entity()
    em.add_component(e1, Transform(x=0, y=0))
    em.add_component(e1, Collider(
        radius=20,
        layer=CollisionMask.PLAYER,
        mask=CollisionMask.ENEMY
    ))
    
    e2 = em.create_entity()
    em.add_component(e2, Transform(x=10, y=0))  # Overlapping
    em.add_component(e2, Collider(
        radius=20,
        layer=CollisionMask.ENEMY,
        mask=CollisionMask.PLAYER
    ))
    
    # Track collision events
    collisions = []
    bus.subscribe(CollisionEvent, lambda e: collisions.append(e))
    
    sm.update(1/60)
    
    assert len(collisions) == 1
    
    sm.cleanup()
    print("  ✓ CollisionSystem tests passed")


def test_ai_system():
    """Test AISystem."""
    print("Testing AISystem...")
    
    em = EntityManager()
    bus = EventBus()
    sm = SystemManager(em, bus)
    sm.add_system(AISystem())
    
    # Create player
    player = em.create_entity(name="player")
    em.add_component(player, Transform(x=0, y=0))
    
    # Create chaser enemy
    enemy = em.create_entity()
    em.add_component(enemy, Transform(x=200, y=0))
    em.add_component(enemy, Velocity())
    em.add_component(enemy, Physics(acceleration=300))
    em.add_component(enemy, AIBrain(
        behavior=AIBehavior.CHASER,
        awareness_range=500
    ))
    
    # Simulate
    for _ in range(10):
        sm.update(1/60)
    
    brain = em.get_component(enemy, AIBrain)
    assert brain.state == AIBehavior.CHASER or brain.state.name == "CHASING"
    
    sm.cleanup()
    print("  ✓ AISystem tests passed")


def test_pathfinding():
    """Test PathfindingSystem."""
    print("Testing Pathfinding...")
    
    from engine.systems.pathfinding_system import PathfindingGrid
    
    grid = PathfindingGrid(800, 600, cell_size=30)
    
    # Simple path
    path = grid.find_path(-200, -200, 200, 200)
    assert path is not None
    
    # Path around obstacle
    grid.mark_obstacle(0, 0, 100)
    path = grid.find_path(-200, 0, 200, 0)
    assert path is not None and len(path) > 1
    
    print("  ✓ Pathfinding tests passed")


def test_wave_system():
    """Test WaveSystem enemy spawning configuration."""
    print("Testing WaveSystem...")
    
    em = EntityManager()
    bus = EventBus()
    sm = SystemManager(em, bus)
    
    wave_sys = WaveSystem(800, 600, start_budget=5, budget_per_wave=3)
    sm.add_system(wave_sys)
    
    assert len(wave_sys.enemy_configs) > 0
    assert "chaser" in wave_sys.enemy_configs
    assert "turret" in wave_sys.enemy_configs
    
    sm.cleanup()
    print("  ✓ WaveSystem tests passed")


def run_all_tests():
    """Run all tests."""
    print("=" * 50)
    print("  ROBO-ARENA ENGINE TEST SUITE")
    print("=" * 50)
    print()
    
    try:
        test_entity_manager()
        test_event_bus()
        test_components()
        test_physics_system()
        test_collision_system()
        test_ai_system()
        test_pathfinding()
        test_wave_system()
        
        print()
        print("=" * 50)
        print("  ALL TESTS PASSED! ✓")
        print("=" * 50)
        return True
    except AssertionError as e:
        print(f"\n  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
