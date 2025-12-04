#!/usr/bin/env python3
"""
Test script to verify ECS core functionality without requiring turtle/tkinter.
"""

def test_ecs_core():
    """Test core ECS components."""
    print("Testing ECS Core...")
    
    # Test imports
    from game_engine.core import (
        Entity, EntityManager, ComponentRegistry, SystemManager, GameSystem,
        Transform, Renderable, Collider, Physics, Health, Weapon
    )
    print("✓ Imports successful")
    
    # Test EntityManager
    em = EntityManager()
    entity_id = em.create_entity()
    assert em.has_entity(entity_id), "Entity should exist"
    print("✓ EntityManager: create_entity works")
    
    # Test Component addition
    transform = Transform(x=10.0, y=20.0)
    em.add_component(entity_id, transform)
    assert em.has_component(entity_id, "Transform"), "Component should be added"
    retrieved = em.get_component(entity_id, "Transform")
    assert retrieved.x == 10.0, "Component data should be preserved"
    print("✓ EntityManager: add/get component works")
    
    # Test ComponentRegistry
    cr = ComponentRegistry()
    cr.register_component(entity_id, "Transform")
    assert cr.has_component(entity_id, "Transform"), "Registry should track component"
    
    entities_with_transform = cr.get_entities_with("Transform")
    assert entity_id in entities_with_transform, "Query should return entity"
    print("✓ ComponentRegistry: registration and queries work")
    
    # Test multiple components
    health = Health(hp=100.0, max_hp=100.0)
    em.add_component(entity_id, health)
    cr.register_component(entity_id, "Health")
    
    entities_with_both = cr.get_entities_with("Transform", "Health")
    assert entity_id in entities_with_both, "Query should find entity with both components"
    print("✓ ComponentRegistry: multi-component queries work")
    
    # Test System
    class TestSystem(GameSystem):
        def update(self, dt):
            pass
    
    sm = SystemManager()
    test_system = TestSystem(em, cr)
    sm.register_system(test_system)
    sm.update_all(0.016)  # ~60 FPS dt
    print("✓ SystemManager: system registration and updates work")
    
    # Test entity destruction
    em.destroy_entity(entity_id)
    assert em.has_entity(entity_id), "Entity should still exist before flush"
    em.flush_destruction()
    assert not em.has_entity(entity_id), "Entity should be destroyed after flush"
    print("✓ EntityManager: deferred destruction works")
    
    print("\n✅ All ECS core tests passed!")


def test_components():
    """Test component functionality."""
    print("\nTesting Components...")
    
    from game_engine.core import Transform, Health, Collider
    
    # Test Transform
    t1 = Transform(x=0, y=0)
    t2 = Transform(x=3, y=4)
    distance = t1.distance_to(t2)
    assert abs(distance - 5.0) < 0.001, f"Distance should be 5.0, got {distance}"
    print("✓ Transform.distance_to works")
    
    angle = t1.angle_to(t2)
    assert abs(angle - 53.1301) < 1.0, f"Angle should be ~53 degrees, got {angle}"
    print("✓ Transform.angle_to works")
    
    # Test Health
    health = Health(hp=50.0, max_hp=100.0)
    assert health.is_alive(), "Health should be alive"
    health.hp = 0
    assert not health.is_alive(), "Health should be dead"
    print("✓ Health.is_alive works")
    
    # Test Collider
    c1 = Collider(radius=10.0, mask=0x0001)
    c2 = Collider(radius=10.0, mask=0x0002)
    c3 = Collider(radius=10.0, mask=0x0003)
    
    assert not c1.collides_with(c2), "Masks 0x0001 and 0x0002 should not collide"
    assert c1.collides_with(c3), "Masks 0x0001 and 0x0003 should collide"
    print("✓ Collider.collides_with works")
    
    print("\n✅ All component tests passed!")


if __name__ == "__main__":
    try:
        test_ecs_core()
        test_components()
        print("\n🎉 All tests passed! The ECS engine is working correctly.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
