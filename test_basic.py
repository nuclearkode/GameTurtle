#!/usr/bin/env python3
"""
Basic test to verify the game engine structure works.
Tests core ECS functionality without running the full game.
"""

from game_engine.core.entity import EntityManager
from game_engine.core.registry import ComponentRegistry
from game_engine.core.component import Transform, Renderable, Health


def test_ecs_basics():
    """Test basic ECS operations"""
    print("Testing ECS basics...")
    
    # Create managers
    entity_manager = EntityManager()
    registry = ComponentRegistry()
    
    # Create an entity
    entity_id = entity_manager.create_entity()
    print(f"Created entity: {entity_id[:8]}...")
    
    # Add components
    transform = Transform(x=10.0, y=20.0)
    entity_manager.add_component(entity_id, transform)
    registry.register(entity_id, transform)
    
    renderable = Renderable(color="blue", shape="circle")
    entity_manager.add_component(entity_id, renderable)
    registry.register(entity_id, renderable)
    
    health = Health(hp=100.0, max_hp=100.0)
    entity_manager.add_component(entity_id, health)
    registry.register(entity_id, health)
    
    # Verify components
    assert entity_manager.has_component(entity_id, Transform)
    assert entity_manager.has_component(entity_id, Renderable)
    assert entity_manager.has_component(entity_id, Health)
    
    retrieved_transform = entity_manager.get_component(entity_id, Transform)
    assert retrieved_transform.x == 10.0
    assert retrieved_transform.y == 20.0
    
    # Test registry queries
    entities_with_transform = registry.get_all(Transform)
    assert entity_id in entities_with_transform
    
    entities_with_both = registry.get_entities_with(Transform, Renderable)
    assert entity_id in entities_with_both
    
    print("✓ ECS basics test passed!")
    
    # Test entity destruction
    entity_manager.destroy_entity(entity_id)
    assert entity_id in entity_manager._pending_destruction
    
    entity_manager.flush_destruction(registry)
    assert entity_id not in entity_manager._entities
    
    print("✓ Entity destruction test passed!")
    print("\nAll basic tests passed! ✓")


if __name__ == "__main__":
    test_ecs_basics()
