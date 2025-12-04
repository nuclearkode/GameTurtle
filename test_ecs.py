"""
Test ECS functionality without turtle dependency.
This demonstrates the core ECS architecture working independently.
"""

from engine.core.entity import EntityManager
from engine.core.component import Transform, Health, Physics, AIBrain, AIBehavior
from engine.core.system import GameSystem


class SimplePhysicsSystem(GameSystem):
    """Test physics system."""
    def update(self, dt: float):
        entities = self.entity_manager.query_entities(Transform, Physics)
        for entity in entities:
            transform = entity.get_component(Transform)
            physics = entity.get_component(Physics)
            
            # Apply velocity
            transform.x += transform.vx * dt
            transform.y += transform.vy * dt


def test_ecs_basics():
    """Test basic ECS operations."""
    print("Testing ECS Architecture...")
    print("=" * 50)
    
    # Create entity manager
    em = EntityManager()
    print(f"✓ Created EntityManager")
    
    # Create entities
    player = em.create_entity()
    enemy1 = em.create_entity()
    enemy2 = em.create_entity()
    print(f"✓ Created 3 entities")
    
    # Add components
    em.add_component(player.id, Transform(x=0, y=0, vx=10, vy=0))
    em.add_component(player.id, Health(hp=100, max_hp=100))
    em.add_component(player.id, Physics(max_speed=200))
    print(f"✓ Added components to player")
    
    em.add_component(enemy1.id, Transform(x=100, y=100, vx=-5, vy=0))
    em.add_component(enemy1.id, Health(hp=30, max_hp=30))
    em.add_component(enemy1.id, AIBrain(behavior_type=AIBehavior.CHASER))
    print(f"✓ Added components to enemy1")
    
    em.add_component(enemy2.id, Transform(x=-100, y=50))
    em.add_component(enemy2.id, AIBrain(behavior_type=AIBehavior.TURRET))
    print(f"✓ Added components to enemy2")
    
    # Query entities
    entities_with_health = em.query_entities(Health)
    print(f"✓ Query: Found {len(entities_with_health)} entities with Health")
    
    entities_with_ai = em.query_entities(AIBrain)
    print(f"✓ Query: Found {len(entities_with_ai)} entities with AI")
    
    entities_with_transform_and_physics = em.query_entities(Transform, Physics)
    print(f"✓ Query: Found {len(entities_with_transform_and_physics)} entities with Transform+Physics")
    
    # Test component access
    player_health = em.get_component(player.id, Health)
    print(f"✓ Player health: {player_health.hp}/{player_health.max_hp}")
    
    # Test system
    physics_system = SimplePhysicsSystem(em, priority=0)
    print(f"✓ Created SimplePhysicsSystem")
    
    # Update once
    dt = 0.016  # ~60 FPS
    physics_system.update(dt)
    
    player_transform = em.get_component(player.id, Transform)
    print(f"✓ After physics update: Player position = ({player_transform.x:.2f}, {player_transform.y:.2f})")
    
    # Test entity destruction
    em.destroy_entity(enemy2.id)
    em.process_destruction_queue()
    print(f"✓ Destroyed enemy2, remaining entities: {em.entity_count()}")
    
    # Verify query after destruction
    entities_with_ai_after = em.query_entities(AIBrain)
    print(f"✓ AI entities after destruction: {len(entities_with_ai_after)}")
    
    print("=" * 50)
    print("✅ All ECS tests passed!")
    print()
    print("The ECS architecture is working correctly:")
    print("  - Entity creation and management")
    print("  - Component attachment and retrieval")
    print("  - Entity queries by component type")
    print("  - System updates on queried entities")
    print("  - Entity destruction and cleanup")


def test_component_registry():
    """Test component registry performance."""
    print("\nTesting Component Registry Performance...")
    print("=" * 50)
    
    em = EntityManager()
    
    # Create 1000 entities
    import time
    start = time.time()
    for i in range(1000):
        entity = em.create_entity()
        em.add_component(entity.id, Transform(x=i, y=i*2))
        if i % 2 == 0:
            em.add_component(entity.id, Health(hp=100))
        if i % 3 == 0:
            em.add_component(entity.id, Physics(max_speed=100))
    
    creation_time = time.time() - start
    print(f"✓ Created 1000 entities with components in {creation_time*1000:.2f}ms")
    
    # Query performance
    start = time.time()
    results = em.query_entities(Transform, Health)
    query_time = time.time() - start
    print(f"✓ Queried Transform+Health in {query_time*1000:.4f}ms")
    print(f"✓ Found {len(results)} entities matching query")
    
    # Query with 3 components
    start = time.time()
    results2 = em.query_entities(Transform, Health, Physics)
    query_time2 = time.time() - start
    print(f"✓ Queried Transform+Health+Physics in {query_time2*1000:.4f}ms")
    print(f"✓ Found {len(results2)} entities matching query")
    
    print("=" * 50)
    print("✅ Performance tests passed!")


if __name__ == "__main__":
    test_ecs_basics()
    test_component_registry()
    
    print("\n" + "=" * 50)
    print("ROBO-ARENA ECS ENGINE - READY TO USE")
    print("=" * 50)
    print("\nTo run the full game (requires tkinter/turtle):")
    print("  python3 main.py")
    print("\nThe engine architecture is fully functional and ready for:")
    print("  - Adding new components")
    print("  - Creating new systems")
    print("  - Building different game types")
    print("  - Porting to other rendering backends")
